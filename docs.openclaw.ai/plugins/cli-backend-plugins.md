# CLI 后端插件

## 架构精读

> 跳过不影响阅读翻译正文。

### 为什么不让 provider 插件直接调 CLI？

Provider 插件面向 HTTP API——发请求、读响应、处理流。但有些 AI 工具只暴露本地 CLI（带本地登录态、stdin/stdout 管道、会话状态）。如果硬用 provider 插件包 CLI，就像用 JDBC 驱动连 SQLite 文件——协议层完全不对。CLI 后端插件是另一种契约：声明"我知道怎么跟这个 CLI 对话"，OpenClaw 用这个驱动路由推理请求。就像 JDBC 有三层——驱动 JAR（分发）、META-INF/services（发现）、驱动注册调用（运行时注册）——CLI 后端也有三层契约：package.json（分发）、openclaw.plugin.json（冷发现）、api.registerCliBackend()（热注册）。好处是每个 CLI 方言独立封装，坏处是比 provider 插件多一层 manifest 要维护。

第二个关键设计：ownsNativeCompaction。有些 CLI 自己管理上下文压缩（比如 Claude Code 内部压缩，没有外部压缩端点）。告诉 OpenClaw"别插手，我自己处理"，OpenClaw 的保护性摘要器就不对这个会话生效。就像某些数据库自己管理 WAL checkpoint——你告诉编排器"别干扰，我自己来"。但声明这个的前提是 CLI 真的能可靠压缩，否则超预算会话就永远超预算——OpenClaw 不再兜底。

第三个边界：MCP 工具桥是 FFI（外部函数接口）。CLI 默认收不到 OpenClaw 工具——两个独立的工具生态。bundleMcp 启用桥接，就像 JNI 让 Java 调用 C 代码，MCP 桥让 CLI 消费 OpenClaw 的工具配置。三种桥模式对应三种 CLI 接收方式：配置文件（claude-config-file）、argv 参数（codex-config-overrides）、系统设置目录（gemini-system-settings）。

---

CLI 后端插件让 OpenClaw 把本地 AI CLI 当作文本推理后端调用。后端以 model ref 中的 provider 前缀出现：

```text
acme-cli/acme-large
```

在上游集成已经暴露为本地命令、CLI 持有本地登录态、或 CLI 作为 API provider 不可用时的后备时使用 CLI 后端。

> **信息**
>
> 如果上游服务暴露标准 HTTP 模型 API，写 [provider 插件](/plugins/sdk-provider-plugins)。如果上游运行时持有完整 agent 会话、工具事件、压缩或后台任务状态，使用 [agent harness](/plugins/sdk-agent-harness)。

## 插件持有的契约

CLI 后端插件有三个契约：

| 契约 | 文件 | 用途 |
| --- | --- | --- |
| 包入口 | `package.json` | 告诉 OpenClaw 插件运行时模块位置 |
| Manifest 所有权 | `openclaw.plugin.json` | 在运行时加载前声明后端 id |
| 运行时注册 | `index.ts` | 调用 `api.registerCliBackend(...)` 传入命令默认值 |

Manifest 是发现元数据。它不执行 CLI，也不注册运行时行为。运行时行为在插件入口调用 `api.registerCliBackend(...)` 时开始。

## 最简后端插件

步骤：

创建包元数据

```json package.json
{
  "name": "@acme/openclaw-acme-cli",
  "version": "1.0.0",
  "type": "module",
  "openclaw": {
    "extensions": ["./index.ts"],
    "compat": {
      "pluginApi": ">=2026.3.24-beta.2",
      "minGatewayVersion": "2026.3.24-beta.2"
    },
    "build": {
      "openclawVersion": "2026.3.24-beta.2",
      "pluginSdkVersion": "2026.3.24-beta.2"
    }
  },
  "dependencies": {
    "openclaw": "^2026.3.24"
  },
  "devDependencies": {
    "typescript": "^5.9.0"
  }
}
```

发布的包必须附带已构建的 JavaScript 运行时文件。如果源入口是 `./src/index.ts`，添加 `openclaw.runtimeExtensions` 指向对应的已构建 JavaScript。参见 [Entry points](/plugins/sdk-entrypoints)。

声明后端所有权

```json openclaw.plugin.json
{
  "id": "acme-cli",
  "name": "Acme CLI",
  "description": "Run Acme's local AI CLI through OpenClaw",
  "cliBackends": ["acme-cli"],
  "setup": {
    "cliBackends": ["acme-cli"],
    "requiresRuntime": false
  },
  "activation": {
    "onStartup": false
  },
  "configSchema": {
    "type": "object",
    "additionalProperties": false
  }
}
```

`cliBackends` 是运行时所有权列表。当配置或模型选择提到 `acme-cli/...` 时，OpenClaw 自动加载该插件。

`setup.cliBackends` 是描述符优先的 setup 表面。当模型发现、引导或状态页无需加载插件运行时即可识别后端时添加它。`requiresRuntime: false` 仅在静态描述符足以满足 setup 时使用。

注册后端

```typescript index.ts
import { definePluginEntry } from "openclaw/plugin-sdk/plugin-entry";
import {
  CLI_FRESH_WATCHDOG_DEFAULTS,
  CLI_RESUME_WATCHDOG_DEFAULTS,
  type CliBackendPlugin,
} from "openclaw/plugin-sdk/cli-backend";

function buildAcmeCliBackend(): CliBackendPlugin {
  return {
    id: "acme-cli",
    liveTest: {
      defaultModelRef: "acme-cli/acme-large",
      defaultImageProbe: false,
      defaultMcpProbe: false,
      docker: {
        npmPackage: "@acme/acme-cli",
        binaryName: "acme",
      },
    },
    config: {
      command: "acme",
      args: ["chat", "--json"],
      output: "json",
      input: "stdin",
      modelArg: "--model",
      sessionArg: "--session",
      sessionMode: "existing",
      sessionIdFields: ["session_id", "conversation_id"],
      systemPromptFileArg: "--system-file",
      systemPromptWhen: "first",
      imageArg: "--image",
      imageMode: "repeat",
      reliability: {
        watchdog: {
          fresh: { ...CLI_FRESH_WATCHDOG_DEFAULTS },
          resume: { ...CLI_RESUME_WATCHDOG_DEFAULTS },
        },
      },
      serialize: true,
    },
  };
}

export default definePluginEntry({
  id: "acme-cli",
  name: "Acme CLI",
  description: "Run Acme's local AI CLI through OpenClaw",
  register(api) {
    api.registerCliBackend(buildAcmeCliBackend());
  },
});
```

后端 id 必须与 manifest 的 `cliBackends` 条目匹配。注册的 `config` 只是默认值；用户在 `agents.defaults.cliBackends.acme-cli` 下的配置会在运行时合并覆盖。

## 配置形态

`CliBackendConfig` 描述 OpenClaw 如何启动和解析 CLI：

| 字段 | 用途 |
| --- | --- |
| `command` | 二进制名或绝对命令路径 |
| `args` | 新会话的基础 argv |
| `resumeArgs` | 恢复会话的替代 argv；支持 `{sessionId}` |
| `output` / `resumeOutput` | 解析器：`json`、`jsonl` 或 `text` |
| `input` | 提示传输方式：`arg` 或 `stdin` |
| `modelArg` | 模型 id 前的标志 |
| `modelAliases` | 将 OpenClaw 模型 id 映射到 CLI 原生 id |
| `sessionArg` / `sessionArgs` | 如何传递会话 id |
| `sessionMode` | `always`、`existing` 或 `none` |
| `sessionIdFields` | OpenClaw 从 CLI 输出读取的 JSON 字段 |
| `systemPromptArg` / `systemPromptFileArg` | 系统提示传输 |
| `systemPromptWhen` | `first`、`always` 或 `never` |
| `imageArg` / `imageMode` | 图片路径支持 |
| `serialize` | 保持同后端运行有序 |
| `reliability.watchdog` | 无输出超时调优 |

优先使用与 CLI 匹配的最小静态配置。仅在行为真正属于后端时才添加插件回调。

## 高级后端钩子

`CliBackendPlugin` 还可以定义：

| 钩子 | 用途 |
| --- | --- |
| `normalizeConfig(config, context)` | 合并后重写遗留用户配置 |
| `resolveExecutionArgs(ctx)` | 添加请求级标志如思考强度 |
| `prepareExecution(ctx)` | 在启动前创建临时认证或配置桥接 |
| `transformSystemPrompt(ctx)` | 应用最终的 CLI 特定系统提示变换 |
| `textTransforms` | 双向提示/输出替换 |
| `defaultAuthProfileId` | 优先使用特定 OpenClaw 认证配置 |
| `authEpochMode` | 决定认证变更如何使已存储 CLI 会话失效 |
| `nativeToolMode` | 声明 CLI 是否持有始终开启的原生工具 |
| `bundleMcp` / `bundleMcpMode` | 启用 OpenClaw 的环回 MCP 工具桥 |
| `ownsNativeCompaction` | 后端自己管理压缩——OpenClaw 推迟 |

保持这些钩子归后端所有。当后端钩子能表达行为时，不要在核心中添加 CLI 特定分支。

### `ownsNativeCompaction`：退出 OpenClaw 压缩

如果你的后端运行的 agent 自己压缩会话记录，设置 `ownsNativeCompaction: true`，OpenClaw 的保护性摘要器就不对它生效——CLI 压缩生命周期返回空操作，回合继续。`claude-cli` 声明了它，因为 Claude Code 内部压缩且没有 harness 端点。Codex 等原生 harness 会话仍路由到各自的 harness 压缩端点。

**仅在以下条件全部满足时声明**，否则超预算的延迟会话可能持续超预算或过期（OpenClaw 不再兜底）：

- 后端在接近窗口限制时可靠地压缩或限制自己的会话记录
- 它持久化可恢复的会话，使压缩后的状态跨回合存活（例如 `--resume` / `--session-id`）
- 它不是原生 harness 压缩会话——匹配 `agentHarnessId` 的会话路由到 harness 端点

## MCP 工具桥

CLI 后端默认不接收 OpenClaw 工具。如果 CLI 能消费 MCP 配置，显式启用：

```typescript
return {
  id: "acme-cli",
  bundleMcp: true,
  bundleMcpMode: "codex-config-overrides",
  config: {
    command: "acme",
    args: ["chat", "--json"],
    output: "json",
  },
};
```

支持的桥模式：

| 模式 | 用途 |
| --- | --- |
| `claude-config-file` | 接受 MCP 配置文件的 CLI |
| `codex-config-overrides` | 在 argv 上接受配置覆盖的 CLI |
| `gemini-system-settings` | 从系统设置目录读取 MCP 设置的 CLI |

仅在 CLI 真正能消费时才启用桥。如果 CLI 有自己的内置工具层且无法禁用，设置 `nativeToolMode: "always-on"`，OpenClaw 在调用者要求无原生工具时可以做 fail closed。

## 用户配置

用户可覆盖任何后端默认值：

```json5
{
  agents: {
    defaults: {
      cliBackends: {
        "acme-cli": {
          command: "/opt/acme/bin/acme",
          args: ["chat", "--json", "--profile", "work"],
          modelAliases: {
            large: "acme-large-2026",
          },
        },
      },
      model: {
        primary: "openai/gpt-5.5",
        fallbacks: ["acme-cli/large"],
      },
    },
  },
}
```

只文档化用户最可能需要的最小覆盖。通常只有 `command`（当二进制不在 `PATH` 中时）。

## 验证

对捆绑插件，围绕 builder 和 setup 注册添加聚焦测试，然后运行插件的目标测试通道：

```bash
pnpm test extensions/acme-cli
```

对本地或已安装插件，验证发现和一次真实模型运行：

```bash
openclaw plugins inspect acme-cli --runtime --json
openclaw agent --message "reply exactly: backend ok" --model acme-cli/acme-large
```

如果后端支持图片或 MCP，添加证明这些路径的真实 CLI 冒烟测试。不要依赖静态检查来验证提示、图片、MCP 或会话恢复行为。

## 检查清单

检查 `package.json` 对已发布包持有 `openclaw.extensions` 和已构建运行时入口

检查 `openclaw.plugin.json` 声明了 `cliBackends` 和有意的 `activation.onStartup`

检查 当 setup/模型发现需要冷看到后端时存在 `setup.cliBackends`

检查 `api.registerCliBackend(...)` 使用与 manifest 相同的后端 id

检查 `agents.defaults.cliBackends.<id>` 下的用户覆盖仍然生效

检查 会话、系统提示、图片和输出解析器设置匹配真实 CLI 契约

检查 目标测试和至少一次真实 CLI 冒烟证明后端路径

## 相关

- [CLI backends](/gateway/cli-backends)——用户配置和运行时行为
- [Building plugins](/plugins/building-plugins)——包和 manifest 基础
- [Plugin SDK overview](/plugins/sdk-overview)——注册 API 参考
- [Plugin manifest](/plugins/manifest)——`cliBackends` 和 setup 描述符
- [Agent harness](/plugins/sdk-agent-harness)——完整外部 agent 运行时
