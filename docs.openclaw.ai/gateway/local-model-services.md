# Local Model Services

OpenClaw 支持通过 provider 级的 `localService` 配置按需启动本地 model server。当 model request 目标是有此配置的 provider 时,OpenClaw 检查服务是否已在运行,必要时自动启动再发送请求。适合资源密集不能持续运行的本地推理服务器,或选择模型时自动激活后端基础设施的工作流。

> **类比:K8s 的 liveness probe + auto-start。** K8s 用 liveness probe 检测 container 是否健康,失败时重启。OpenClaw 的 `localService` 类似: 用 `healthUrl` 探测服务是否运行,失败时自动 `command` + `args` 启动。但 OpenClaw 管理的是 child process 而非 container,不安装 system daemon (launchd、systemd、Docker)。
>
> **类比:数据库连接池的 auto-provision。** 连接池在需要时自动创建新连接,空闲时回收。`localService` 在需要时自动启动 model server,空闲 `idleStopMs` 后停止。关键区别: model server 启动慢(cold start 可能需要分钟级),连接创建快(毫秒级),所以 `readyTimeoutMs` 默认 120s。
>
> **架构要点:** OpenClaw 直接管理 child process,不安装 system daemon;`healthUrl` 探测 + 自动启动;`idleStopMs` 控制空闲停止;启动操作按 provider command + args 串行化防止重复 spawn;active streaming 维持 process lease,idle shutdown 等待 response body 完成。

## 工作流程

七步:

1. Model request 解析到特定配置的 provider
2. 如果配置了 `localService`,OpenClaw 探测 `healthUrl`
3. 探测成功 → 使用已有 server
4. 探测失败 → OpenClaw 用 `command` + `args` 启动进程
5. 轮询就绪状态直到 `readyTimeoutMs` 过期
6. Model request 经正常 provider 传输执行
7. 如果 OpenClaw 启动了进程且 `idleStopMs` 为正,进程在该时间空闲后停止

## 配置结构

```json5
{
  models: {
    providers: {
      local: {
        baseUrl: "http://127.0.0.1:8000/v1",
        apiKey: "local-model",
        api: "openai-completions",
        timeoutSeconds: 300,
        localService: {
          command: "/absolute/path/to/server",
          args: ["--host", "127.0.0.1", "--port", "8000"],
          cwd: "/absolute/path/to/working-dir",
          env: { LOCAL_MODEL_CACHE: "/absolute/path/to/cache" },
          healthUrl: "http://127.0.0.1:8000/v1/models",
          readyTimeoutMs: 180000,
          idleStopMs: 0
        },
        models: [{ id: "my-local-model", /* ... */ }]
      }
    }
  }
}
```

### 字段参考

- **`command`**: 可执行文件绝对路径。系统不执行 shell lookup
- **`args`**: 进程参数数组。不应用 shell 展开、管道、globbing、引号规则
- **`cwd`**: 可选工作目录
- **`env`**: 可选环境变量,合并到父 OpenClaw 进程环境之上
- **`healthUrl`**: 就绪检查 URL。省略时 OpenClaw 在 `baseUrl` 后追加 `/models`
- **`readyTimeoutMs`**: 启动就绪最大等待时间。默认 120000ms
- **`idleStopMs`**: OpenClaw 启动的进程空闲多久后停止。`0` 或省略 = 保持运行直到 OpenClaw 退出

## Provider 示例

### Inferrs

```json5
{
  models: {
    providers: {
      inferrs: {
        baseUrl: "http://127.0.0.1:8080/v1",
        apiKey: "inferrs-local",
        api: "openai-completions",
        localService: {
          command: "/opt/homebrew/bin/inferrs",
          args: ["serve", "google/gemma-4-E2B-it", "--host", "127.0.0.1", "--port", "8080", "--device", "metal"],
          healthUrl: "http://127.0.0.1:8080/v1/models",
          readyTimeoutMs: 180000,
          idleStopMs: 0
        }
      }
    }
  }
}
```

### ds4

```json5
{
  models: {
    providers: {
      ds4: {
        baseUrl: "http://127.0.0.1:18000/v1",
        localService: {
          command: "<DS4_DIR>/ds4-server",
          args: ["--model", "<DS4_DIR>/ds4flash.gguf", "--host", "127.0.0.1", "--port", "18000", "--ctx", "32768"],
          cwd: "<DS4_DIR>",
          readyTimeoutMs: 300000,
          idleStopMs: 0
        }
      }
    }
  }
}
```

## 运维考虑

**进程管理**: 每个 OpenClaw 进程只管理它直接启动的 child。如果另一个 OpenClaw 实例检测到同一 health URL 已在响应,它复用该 server 但不接管所有权。

**并发控制**: 启动操作按 provider command + args 组合串行化,防止针对相同配置的并发请求产生重复 server 启动。

**Streaming 和 idle shutdown**: Active streaming responses 维持进程租约。Idle shutdown 等待 response body handling 完成后再执行。

**超时配置**: 对较慢的本地 provider 配置合适的 `timeoutSeconds`,防止 cold start 和长时间生成触发默认请求超时。
