# Local Model Services

## 架构精读

> 跳过不影响阅读翻译正文。

### 进程管理策略——为什么不用 system daemon？

OpenClaw 直接管理子进程而不是安装系统守护进程（如 launchd、systemd、Docker），这是一种"最小权限"的设计选择。系统守护进程需要超级用户（root）权限或系统级配置，增加了部署复杂度和安全风险。子进程管理让 OpenClaw 具备完整的生命周期控制——通过 `healthUrl` 探测服务是否健康，失败时自动用 `command` + `args`（参数）重启——但不需要系统级权限。这种设计部署更简单，也避免了与已有系统服务管理器的生命周期冲突。每个 OpenClaw 进程只管理它直接启动的子进程，如果另一个实例已经在响应同一个 health URL，则复用但不接管。

### 空闲停止机制——为什么 `idleStopMs` 要等待 response body 完成？

进程租约机制确保正在处理流式响应的进程不会被提前终止。只有当 response body 处理完成后，idle 计时器才开始计时。可以类比 HTTP server 的 graceful shutdown：不是立即终止（kill）进程，而是等待当前请求完成。模型推理服务冷启动可能需要数十秒甚至数分钟，意外终止后重启的代价远大于多等几秒。

### 并发启动串行化——为什么需要防止重复启动？

多个模型请求同时到达且指向同一个 backend 配置时，没有串行化控制就会重复启动多个 server 进程，浪费 GPU 资源并导致端口冲突。系统按 provider command + args 组合创建互斥锁，确保同一配置只启动一个 server。这类似于单例模式的进程级实现——第一次请求创建实例，后续请求共享。串行化只影响启动操作，不影响已启动 server 的并发请求处理。

### 就绪超时设计——为什么 `readyTimeoutMs` 默认 120 秒？

本地模型服务器的冷启动通常需要数十秒甚至更长时间——模型文件加载到 GPU 内存、初始化计算图、预分配 KV-cache 都需要时间。相比之下，数据库连接池创建新连接只需毫秒级。120 秒的默认值是基于实际模型加载时间的经验值，覆盖大多数本地推理服务器的启动场景。对于特别大的模型或较慢的硬件，可以通过配置调高此值。过短的超时会导致启动失败，过长则让真正的启动错误需要等待太久才被发现。

---

OpenClaw supports on-demand launching of local model servers through the `localService` configuration at the provider level. When a model request targets a provider with this configuration, OpenClaw checks whether the service is already running and starts it automatically if needed. This is ideal for resource-intensive local inference servers that cannot run continuously, or for workflows that should automatically activate backend infrastructure when a model is selected.

OpenClaw 支持通过 provider 级的 `localService` 配置按需启动本地 model server。当 model request 目标是有此配置的 provider 时，OpenClaw 检查服务是否已在运行，必要时自动启动再发送请求。适合资源密集不能持续运行的本地推理服务器，或选择模型时自动激活后端基础设施的工作流。

## 工作流程

Workflow

七步：

Seven steps:

1. Model request 解析到特定配置的 provider
2. 如果配置了 `localService`，OpenClaw 探测 `healthUrl`
3. 探测成功 → 使用已有 server
4. 探测失败 → OpenClaw 用 `command` + `args` 启动进程
5. 轮询就绪状态直到 `readyTimeoutMs` 过期
6. Model request 经正常 provider 传输执行
7. 如果 OpenClaw 启动了进程且 `idleStopMs` 为正，进程在该时间空闲后停止

1. Model request is resolved to a specific configured provider
2. If `localService` is configured, OpenClaw probes `healthUrl`
3. Probe succeeds → use existing server
4. Probe fails → OpenClaw starts the process with `command` + `args`
5. Polls readiness until `readyTimeoutMs` expires
6. Model request executes through the normal provider channel
7. If OpenClaw started the process and `idleStopMs` is positive, the process stops after being idle for that duration

## 配置结构

Configuration Structure

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

Field Reference

- **`command`**：可执行文件绝对路径。系统不执行 shell lookup
- **`args`**：进程参数数组。不应用 shell 展开、管道、globbing、引号规则
- **`cwd`**：可选工作目录
- **`env`**：可选环境变量，合并到父 OpenClaw 进程环境之上
- **`healthUrl`**：就绪检查 URL。省略时 OpenClaw 在 `baseUrl` 后追加 `/models`
- **`readyTimeoutMs`**：启动就绪最大等待时间。默认 120000ms
- **`idleStopMs`**：OpenClaw 启动的进程空闲多久后停止。`0` 或省略 = 保持运行直到 OpenClaw 退出

- **`command`**: Absolute path to the executable. The system does not perform shell lookup
- **`args`**: Process argument array. No shell expansion, pipes, globbing, or quoting rules are applied
- **`cwd`**: Optional working directory
- **`env`**: Optional environment variables, merged on top of the parent OpenClaw process environment
- **`healthUrl`**: Readiness check URL. When omitted, OpenClaw appends `/models` to the `baseUrl`
- **`readyTimeoutMs`**: Maximum wait time for startup readiness. Defaults to 120000ms
- **`idleStopMs`**: How long an OpenClaw-started process must be idle before stopping. `0` or omitted = keep running until OpenClaw exits

## Provider 示例

Provider Examples

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

Operational Considerations

**进程管理**：每个 OpenClaw 进程只管理它直接启动的子进程。如果另一个 OpenClaw 实例检测到同一 health URL 已在响应，它复用该 server 但不接管所有权。

**Process management**: Each OpenClaw process only manages the child processes it directly starts. If another OpenClaw instance detects the same health URL is already responding, it reuses that server but does not take ownership.

**并发控制**：启动操作按 provider command + args 组合串行化，防止针对相同配置的并发请求产生重复 server 启动。

**Concurrency control**: Startup operations are serialized by the provider command + args combination, preventing concurrent requests targeting the same configuration from spawning duplicate server launches.

**Streaming 和 idle shutdown**：Active streaming responses 维持进程租约。Idle shutdown 等待 response body handling 完成后再执行。

**Streaming and idle shutdown**: Active streaming responses maintain the process lease. Idle shutdown waits for response body handling to complete before executing.

**超时配置**：对较慢的本地 provider 配置合适的 `timeoutSeconds`，防止 cold start 和长时间生成触发默认请求超时。

**Timeout configuration**: Configure appropriate `timeoutSeconds` for slower local providers to prevent cold starts and long generations from triggering the default request timeout.
