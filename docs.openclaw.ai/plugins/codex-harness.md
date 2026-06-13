# Codex 外部执行器

## 架构精读

> 跳过不影响阅读翻译正文。

### 为什么不让 Codex 直接替代 OpenClaw？

关键在于**职责切分**。Codex 擅长底层 agent 会话管理——原生线程恢复、工具续接、压缩、app-server 执行。OpenClaw 擅长上层——聊天频道、会话文件、模型选择、审批、媒体投递、可见记录镜像。两者各取所长,而非一个吞并另一个。

就像 Docker 的分层：容器引擎负责进程隔离和生命周期,编排器负责调度和网络。Codex 是"引擎",OpenClaw 是"编排器"。

认证隔离的设计特别精妙。用订阅认证时,OpenClaw 会从 Codex 子进程中**清除** `CODEX_API_KEY` 和 `OPENAI_API_KEY`。为什么？因为 Gateway 级的 API key 还要留给 embedding 或直接 OpenAI 模型用,不能让 Codex 原生执行意外走 API 计费。每个 agent 有独立的 `CODEX_HOME`,避免跨 agent 的线程状态污染。

工具桥接的 searchable 加载也值得注意。Codex 原生工具（shell、patch、MCP）自己处理,但消息、浏览器、cron 等 OpenClaw 集成工具通过 tool search 按需加载。初始工具上下文更小,提示缓存命中率更高。就像懒加载——用到才加载,而非启动时全塞进去。

---

> The bundled `codex` plugin lets OpenClaw run embedded OpenAI agent turns through Codex app-server instead of the built-in OpenClaw harness.

内置 `codex` 插件让 OpenClaw 通过 Codex app-server 而非内置 OpenClaw 执行器运行嵌入式 OpenAI agent 轮次。

> Use the Codex harness when you want Codex to own the low-level agent session...

想让 Codex 持有底层 agent 会话时用 Codex 执行器：原生线程恢复、原生工具续接、原生压缩和 app-server 执行。OpenClaw 仍持有聊天频道、会话文件、模型选择、OpenClaw 动态工具、审批、媒体投递和可见记录镜像。

> The normal setup uses canonical OpenAI model refs such as `openai/gpt-5.5`...

正常设置使用标准 OpenAI 模型引用如 `openai/gpt-5.5`。不要配置旧版 Codex GPT 引用。将 OpenAI agent 认证顺序放在 `auth.order.openai` 下；旧版 Codex 认证 profile id 和旧版 Codex 认证顺序条目是由 `openclaw doctor --fix` 修复的旧状态。

> When no OpenClaw sandbox is active...

无 OpenClaw 沙箱活跃时,OpenClaw 启动 Codex app-server 线程时启用 Codex 原生代码模式,默认关闭 code-mode-only。这让 Codex 原生工作区和代码能力保持可用,同时 OpenClaw 动态工具继续走 app-server `item/tool/call` 桥。活跃的 OpenClaw 沙箱和受限工具策略会完全禁用原生代码模式,除非你选择实验性沙箱 exec-server 路径。

> This Codex-native feature is separate from OpenClaw code mode...

此 Codex 原生功能不同于 [OpenClaw code mode](/reference/code-mode),后者是通用 OpenClaw 运行的可选 QuickJS-WASI 运行时,`exec` 输入形态不同。

模型/提供商/运行时简要划分：`openai/gpt-5.5` 是模型引用,`codex` 是运行时,Telegram/Discord/Slack 或其他频道仍是通信表面。完整划分见 [Agent runtimes](/concepts/agent-runtimes)。

## 要求

- OpenClaw 含可用内置 `codex` 插件。
- 配置使用 `plugins.allow` 时包含 `codex`。
- Codex app-server `0.125.0` 或更新。内置插件默认管理兼容的 Codex app-server 二进制,所以 `PATH` 上的本地 `codex` 命令不影响正常执行器启动。
- Codex 认证通过 `openclaw models auth login --provider openai`、agent Codex home 中的 app-server 账户、或显式 Codex API-key 认证 profile 可用。

认证优先级、环境隔离、自定义 app-server 命令、模型发现和所有配置字段见 [Codex harness reference](/plugins/codex-harness-reference)。

## 快速开始

> Most users who want Codex in OpenClaw want this path...

多数想在 OpenClaw 中用 Codex 的用户想要这条路径：用 ChatGPT/Codex 订阅登录、启用内置 `codex` 插件、使用标准 `openai/gpt-*` 模型引用。

Codex OAuth 登录：

```bash
openclaw models auth login --provider openai
```

启用内置 `codex` 插件并选择 OpenAI agent 模型：

```json5
{
  plugins: {
    entries: {
      codex: {
        enabled: true,
      },
    },
  },
  agents: {
    defaults: {
      model: "openai/gpt-5.5",
    },
  },
}
```

配置使用 `plugins.allow` 时也要加 `codex`：

```json5
{
  plugins: {
    allow: ["codex"],
    entries: {
      codex: {
        enabled: true,
      },
    },
  },
}
```

改插件配置后重启 gateway。已有聊天有会话时,测试运行时变更前用 `/new` 或 `/reset`,让下次轮次从当前配置解析执行器。

## 配置

快速开始配置是最小可行 Codex 执行器配置。在 OpenClaw 配置中设 Codex 执行器选项,CLI 仅用于 Codex 认证：

| 需求                                   | 设置                                                                              | 位置                              |
| -------------------------------------- | --------------------------------------------------------------------------------- | --------------------------------- |
| 启用执行器                             | `plugins.entries.codex.enabled: true`                                             | OpenClaw 配置                     |
| 保持白名单插件安装                     | `plugins.allow` 中包含 `codex`                                                    | OpenClaw 配置                     |
| OpenAI agent 轮次走 Codex 路由         | `agents.defaults.model` 或 `agents.list[].model` 为 `openai/gpt-*`                | OpenClaw agent 配置               |
| ChatGPT/Codex OAuth 登录               | `openclaw models auth login --provider openai`                                    | CLI 认证 profile                  |
| Codex 运行添加 API-key 备份            | `auth.order.openai` 中订阅认证后列出 `openai:*` API-key profile                    | CLI 认证 profile + OpenClaw 配置  |
| Codex 不可用时失败即拒绝               | 提供商或模型 `agentRuntime.id: "codex"`                                            | OpenClaw 模型/提供商配置          |
| 使用直接 OpenAI API 流量               | 提供商或模型 `agentRuntime.id: "openclaw"` 加正常 OpenAI 认证                      | OpenClaw 模型/提供商配置          |
| 调整 app-server 行为                   | `plugins.entries.codex.config.appServer.*`                                        | Codex 插件配置                    |
| 启用原生 Codex 插件应用                | `plugins.entries.codex.config.codexPlugins.*`                                     | Codex 插件配置                    |
| 启用 Codex Computer Use                | `plugins.entries.codex.config.computerUse.*`                                      | Codex 插件配置                    |

> Use `openai/gpt-*` model refs for Codex-backed OpenAI agent turns...

Codex 支持的 OpenAI agent 轮次用 `openai/gpt-*` 模型引用。认证排序优先用 `auth.order.openai`。已有旧版 Codex 认证 profile id 和旧版 Codex 认证顺序是 doctor-only 旧状态；不要写新的旧版 Codex GPT 引用。

> Do not set `compaction.model` or `compaction.provider` on Codex-backed agents...

不要在 Codex 支持的 agent 上设 `compaction.model` 或 `compaction.provider`。Codex 通过原生 app-server 线程状态压缩,所以 OpenClaw 运行时忽略那些本地摘要器覆盖,`openclaw doctor --fix` 在 agent 用 Codex 时移除它们。

> Lossless remains supported as a context engine for assembly, ingestion, and maintenance...

Lossless 作为上下文引擎仍受支持,用于 Codex 轮次周围的组装、摄取和维护。通过 `plugins.slots.contextEngine: "lossless-claw"` 和 `plugins.entries.lossless-claw.config.summaryModel` 配置,不通过 `agents.defaults.compaction.provider`。`openclaw doctor --fix` 在 Codex 为活跃运行时将旧的 `compaction.provider: "lossless-claw"` 形态迁移到 Lossless 上下文引擎槽位,但原生 Codex 仍持有压缩。

> The native Codex app-server harness supports context engines that require pre-prompt assembly...

原生 Codex app-server 执行器支持需要预提示组装的上下文引擎。通用 CLI 后端（含 `codex-cli`）不提供该宿主能力。

> For Codex-backed agents, `/compact` starts native Codex app-server compaction...

Codex 支持的 agent 用 `/compact` 在绑定线程上启动原生 Codex app-server 压缩。OpenClaw 不等待完成、不设 OpenClaw 超时、不重启共享 app-server、也不回退到上下文引擎或公共 OpenAI 摘要器。原生 Codex 线程绑定缺失或过期时,命令失败即拒绝,让运营者看到真实运行时边界而非静默切换压缩后端。

认证排序示例：

```json5
{
  auth: {
    order: {
      openai: ["openai:user@example.com", "openai:api-key-backup"],
    },
  },
}
```

该形态中两个 profile 对 `openai/gpt-*` agent 轮次仍走 Codex。API key 只是认证回退,不是切到 OpenClaw 或纯 OpenAI Responses 的请求。

本页其余覆盖用户必须选择的常见变体：部署形态、失败即拒绝路由、guardian 审批策略、原生 Codex 插件和 Computer Use。完整选项列表、默认值、枚举、发现、环境隔离、超时和 app-server 传输字段见 [Codex harness reference](/plugins/codex-harness-reference)。

## 验证 Codex 运行时

> Use `/status` in the chat where you expect Codex...

在期望 Codex 的聊天中用 `/status`。Codex 支持的 OpenAI agent 轮次显示：

```text
Runtime: OpenAI Codex
```

然后检查 Codex app-server 状态：

```text
/codex status
/codex models
```

`/codex status` 报告 app-server 连接性、账户、速率限制、MCP 服务器和 skill。`/codex models` 列出执行器和账户的实时 Codex app-server 目录。`/status` 异常时见 [故障排查](#故障排查)。

## 路由和模型选择

> Keep provider refs and runtime policy separate:

保持提供商引用和运行时策略分离：

- OpenAI agent 轮次走 Codex 时用 `openai/gpt-*`。
- 不要在配置中用旧版 Codex GPT 引用。运行 `openclaw doctor --fix` 修复旧版引用和过期会话路由钉定。
- 正常 OpenAI auto 模式下 `agentRuntime.id: "codex"` 可选,但部署应在 Codex 不可用时失败即拒绝时有用。
- `agentRuntime.id: "openclaw"` 有意时让提供商或模型选择 OpenClaw 嵌入式运行时。
- `/codex ...` 从聊天控制原生 Codex app-server 对话。
- ACP/acpx 是独立的外部执行器路径。仅在用户要求 ACP/acpx 或外部执行器适配器时使用。

常见命令路由：

| 用户意图                                            | 使用                                                                                                  |
| --------------------------------------------------- | ----------------------------------------------------------------------------------------------------- |
| 附加当前聊天                                        | `/codex bind [--cwd <path>]`                                                                          |
| 恢复已有 Codex 线程                                 | `/codex resume <thread-id>`                                                                           |
| 列出或过滤 Codex 线程                               | `/codex threads [filter]`                                                                             |
| 列出原生 Codex 插件                                 | `/codex plugins list`                                                                                 |
| 启用或禁用已配置的原生 Codex 插件                   | `/codex plugins enable <name>`、`/codex plugins disable <name>`                                       |
| 附加配对节点上的已有 Codex CLI 会话                 | `/codex sessions --host <node> [filter]`,然后 `/codex resume <session-id> --host <node> --bind here`  |
| 仅发送 Codex 反馈                                   | `/codex diagnostics [note]`                                                                           |
| 启动 ACP/acpx 任务                                  | ACP/acpx 会话命令,非 `/codex`                                                                         |

| 用例                                                | 配置                                                                | 验证                                  | 备注                                |
| --------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------- | ----------------------------------- |
| ChatGPT/Codex 订阅加原生 Codex 运行时               | `openai/gpt-*` 加启用的 `codex` 插件                                | `/status` 显示 `Runtime: OpenAI Codex` | 推荐路径                            |
| Codex 不可用时失败即拒绝                            | 提供商或模型 `agentRuntime.id: "codex"`                              | 轮次失败而非嵌入式回退                 | 用于 Codex-only 部署                |
| 直接 OpenAI API-key 流量走 OpenClaw                 | 提供商或模型 `agentRuntime.id: "openclaw"` 加正常 OpenAI 认证        | `/status` 显示 OpenClaw 运行时         | 仅在有意 OpenClaw 时使用            |
| 旧版配置                                            | 旧版 Codex GPT 引用                                                 | `openclaw doctor --fix` 重写           | 不要以这种方式写新配置              |
| ACP/acpx Codex 适配器                               | ACP `sessions_spawn({ runtime: "acp" })`                            | ACP 任务/会话状态                      | 与原生 Codex 执行器分离             |

`agents.defaults.imageModel` 遵循相同前缀分离。正常 OpenAI 路由用 `openai/gpt-*`,仅当图片理解应走有界 Codex app-server 轮次时用 `codex/gpt-*`。不要用旧版 Codex GPT 引用；doctor 将旧版前缀重写为 `openai/gpt-*`。

## 部署模式

### 基础 Codex 部署

所有 OpenAI agent 轮次默认走 Codex 时用快速开始配置。

```json5
{
  plugins: {
    entries: {
      codex: {
        enabled: true,
      },
    },
  },
  agents: {
    defaults: {
      model: "openai/gpt-5.5",
    },
  },
}
```

### 混合提供商部署

> This shape keeps Claude as the default agent and adds a named Codex agent:

此形态保持 Claude 为默认 agent 并添加命名 Codex agent：

```json5
{
  plugins: {
    entries: {
      codex: {
        enabled: true,
      },
    },
  },
  agents: {
    defaults: {
      model: "anthropic/claude-opus-4-6",
    },
    list: [
      {
        id: "main",
        default: true,
        model: "anthropic/claude-opus-4-6",
      },
      {
        id: "codex",
        name: "Codex",
        model: "openai/gpt-5.5",
      },
    ],
  },
}
```

此配置下 `main` agent 走正常提供商路径,`codex` agent 走 Codex app-server。

### 失败即拒绝 Codex 部署

> For OpenAI agent turns, `openai/gpt-*` already resolves to Codex...

OpenAI agent 轮次中 `openai/gpt-*` 在内置插件可用时已解析到 Codex。需要书面失败即拒绝规则时添加显式运行时策略：

```json5
{
  models: {
    providers: {
      openai: {
        agentRuntime: {
          id: "codex",
        },
      },
    },
  },
  agents: {
    defaults: {
      model: "openai/gpt-5.5",
    },
  },
  plugins: {
    entries: {
      codex: {
        enabled: true,
      },
    },
  },
}
```

强制 Codex 时,Codex 插件被禁用、app-server 太旧或 app-server 无法启动时 OpenClaw 提前失败。

## App-server 策略

> By default, the plugin starts OpenClaw's managed Codex binary locally with stdio transport...

默认插件用 stdio 传输本地启动 OpenClaw 受管的 Codex 二进制。仅有意运行不同可执行文件时设 `appServer.command`。仅当 app-server 已在别处运行时用 WebSocket 传输：

```json5
{
  plugins: {
    entries: {
      codex: {
        enabled: true,
        config: {
          appServer: {
            transport: "websocket",
            url: "ws://gateway-host:39175",
            authToken: "${CODEX_APP_SERVER_TOKEN}",
          },
        },
      },
    },
  },
}
```

> Local stdio app-server sessions default to the trusted local operator posture...

本地 stdio app-server 会话默认为受信本地运营者姿态：`approvalPolicy: "never"`、`approvalsReviewer: "user"` 和 `sandbox: "danger-full-access"`。本地 Codex 要求不允许该隐式 YOLO 姿态时,OpenClaw 选择允许的 guardian 权限。OpenClaw 沙箱对会话活跃时,OpenClaw 为该轮次禁用 Codex 原生 Code Mode、用户 MCP 服务器和 app-backed 插件执行,而非依赖 Codex 宿主侧沙箱。Shell 访问通过 OpenClaw 沙箱支持的动态工具如 `sandbox_exec` 和 `sandbox_process` 暴露（正常 exec/process 工具可用时）。

想让 Codex 原生 auto-review 在沙箱逃逸或额外权限之前运行用规范化 OpenClaw exec 模式：

```json5
{
  tools: {
    exec: {
      mode: "auto",
    },
  },
  plugins: {
    entries: {
      codex: {
        enabled: true,
      },
    },
  },
}
```

> For Codex app-server sessions, OpenClaw maps `tools.exec.mode: "auto"`...

Codex app-server 会话中 OpenClaw 将 `tools.exec.mode: "auto"` 映射为 Codex Guardian 审核审批,通常是 `approvalPolicy: "on-request"`、`approvalsReviewer: "auto_review"` 和 `sandbox: "workspace-write"`（本地要求允许时）。`tools.exec.mode: "auto"` 下 OpenClaw 不保留旧版不安全 Codex `approvalPolicy: "never"` 或 `sandbox: "danger-full-access"` 覆盖；有意无审批 Codex 姿态用 `tools.exec.mode: "full"`。旧版 `plugins.entries.codex.config.appServer.mode: "guardian"` 预设仍可用,但 `tools.exec.mode: "auto"` 是规范化的 OpenClaw 表面。

模式级与宿主 exec 审批和 ACPX 权限比较见 [Permission modes](/tools/permission-modes)。

所有 app-server 字段、认证顺序、环境隔离、发现和超时行为见 [Codex harness reference](/plugins/codex-harness-reference)。

## 命令和诊断

> The bundled plugin registers `/codex` as a slash command...

内置插件在支持 OpenClaw 文本命令的频道上注册 `/codex` 为斜杠命令。

常见形式：

- `/codex status` 检查 app-server 连接性、模型、账户、速率限制、MCP 服务器和 skill。
- `/codex models` 列出实时 Codex app-server 模型。
- `/codex threads [filter]` 列出近期 Codex app-server 线程。
- `/codex resume <thread-id>` 将当前 OpenClaw 会话附加到已有 Codex 线程。
- `/codex compact` 请求 Codex app-server 压缩附加线程。
- `/codex review` 启动附加线程的 Codex 原生审查。
- `/codex diagnostics [note]` 在发送附加线程的 Codex 反馈前请求确认。
- `/codex account` 显示账户和速率限制状态。
- `/codex mcp` 列出 Codex app-server MCP 服务器状态。
- `/codex skills` 列出 Codex app-server skill。

> For most support reports, start with `/diagnostics [note]`...

多数支持报告从出 bug 对话中的 `/diagnostics [note]` 开始。它创建一个 Gateway 诊断报告,对 Codex 执行器会话请求批准发送相关 Codex 反馈包。隐私模型和群聊行为见 [Diagnostics export](/gateway/diagnostics)。

仅想为当前附加线程上传 Codex 反馈而不要完整 Gateway 诊断包时用 `/codex diagnostics [note]`。

### 本地检查 Codex 线程

> The fastest way to inspect a bad Codex run...

检查糟糕 Codex 运行的最快方式通常是直接打开原生 Codex 线程：

```bash
codex resume <thread-id>
```

从已完成的 `/diagnostics` 回复、`/codex binding` 或 `/codex threads [filter]` 获取线程 id。

上传机制和运行时级诊断边界见 [Codex harness runtime](/plugins/codex-harness-runtime#codex-feedback-upload)。

认证按此顺序选择：

1. agent 的有序 OpenAI 认证 profile,优先在 `auth.order.openai` 下。运行 `openclaw doctor --fix` 迁移旧版 Codex 认证 profile id 和旧版 Codex 认证顺序。
2. app-server 在该 agent Codex home 中的已有账户。
3. 仅本地 stdio app-server 启动时,无 app-server 账户且仍需 OpenAI 认证时,`CODEX_API_KEY`,然后 `OPENAI_API_KEY`。

> When OpenClaw sees a ChatGPT subscription-style Codex auth profile...

OpenClaw 看到 ChatGPT 订阅式 Codex 认证 profile 时,从产生的 Codex 子进程中移除 `CODEX_API_KEY` 和 `OPENAI_API_KEY`。这让 Gateway 级 API key 可用于 embedding 或直接 OpenAI 模型,而不让原生 Codex app-server 轮次意外走 API 计费。显式 Codex API-key profile 和本地 stdio env-key 回退用 app-server 登录而非继承的子进程 env。WebSocket app-server 连接不接收 Gateway env API-key 回退；用显式认证 profile 或远程 app-server 自己的账户。

> If a subscription profile hits a Codex usage limit...

订阅 profile 触及 Codex 用量上限时,OpenClaw 在 Codex 报告重置时间时记录它,并为同一 Codex 运行尝试下一个有序认证 profile。重置时间过后,订阅 profile 再次可用,无需改选定的 `openai/gpt-*` 模型或 Codex 运行时。

> For local stdio app-server launches, OpenClaw sets `CODEX_HOME` to a per-agent directory...

本地 stdio app-server 启动时,OpenClaw 将 `CODEX_HOME` 设为按 agent 目录,这样 Codex 配置、认证/账户文件、插件缓存/数据和原生线程状态默认不读写运营者个人 `~/.codex`。OpenClaw 保留正常进程 `HOME`；Codex 运行子进程仍可找到用户主目录配置和令牌,Codex 可发现共享 `$HOME/.agents/skills` 和 `$HOME/.agents/plugins/marketplace.json` 条目。

需要额外环境隔离时将那些变量加到 `appServer.clearEnv`：

```json5
{
  plugins: {
    entries: {
      codex: {
        enabled: true,
        config: {
          appServer: {
            clearEnv: ["CODEX_API_KEY", "OPENAI_API_KEY"],
          },
        },
      },
    },
  },
}
```

`appServer.clearEnv` 仅影响产生的 Codex app-server 子进程。OpenClaw 在本地启动规范化期间从此列表移除 `CODEX_HOME` 和 `HOME`：`CODEX_HOME` 保持按 agent,`HOME` 保持继承以便子进程可用正常用户主目录状态。

> Codex dynamic tools default to `searchable` loading...

Codex 动态工具默认为 `searchable` 加载。OpenClaw 不暴露与 Codex 原生工作区操作重复的动态工具：`read`、`write`、`edit`、`apply_patch`、`exec`、`process` 和 `update_plan`。多数剩余 OpenClaw 集成工具如消息、媒体、cron、浏览器、节点、gateway、`heartbeat_respond` 和 `web_search` 通过 Codex tool search 在 `openclaw` 命名空间下可用,保持初始模型上下文更小。`sessions_yield` 和 message-tool-only 源回复保持直接因为它们是轮次控制契约。`sessions_spawn` 保持 searchable 让 Codex 原生 `spawn_agent` 仍为主要 Codex 子 agent 表面,同时显式 OpenClaw 或 ACP 委派仍可通过 `openclaw` 动态工具命名空间获得。Heartbeat 协作指令告诉 Codex 在结束 heartbeat 轮次前搜索 `heartbeat_respond`（工具未加载时）。

仅当连接无法搜索延迟动态工具的自定义 Codex app-server 或调试完整工具载荷时设 `codexDynamicToolsLoading: "direct"`。

支持的顶层 Codex 插件字段：

| 字段                       | 默认值         | 含义                                                                             |
| -------------------------- | -------------- | -------------------------------------------------------------------------------- |
| `codexDynamicToolsLoading` | `"searchable"` | 用 `"direct"` 将 OpenClaw 动态工具直接放入初始 Codex 工具上下文。                |
| `codexDynamicToolsExclude` | `[]`           | 从 Codex app-server 轮次中省略的额外 OpenClaw 动态工具名。                        |
| `codexPlugins`             | 禁用           | 原生 Codex 插件/应用支持,用于迁移的源安装精选插件。                               |

支持的 `appServer` 字段：

| 字段                                              | 默认值                                              | 含义                                                                                                                                                                                                                                                                                                                                                      |
| ------------------------------------------------- | --------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `transport`                                       | `"stdio"`                                           | `"stdio"` 产生 Codex；`"websocket"` 连接到 `url`。                                                                                                                                                                                                                                                                                                         |
| `command`                                         | 受管 Codex 二进制                                   | stdio 传输的可执行文件。不设则用受管二进制；仅显式覆盖时设。                                                                                                                                                                                                                                                                                               |
| `args`                                            | `["app-server", "--listen", "stdio://"]`            | stdio 传输的参数。                                                                                                                                                                                                                                                                                                                                        |
| `url`                                             | 未设                                                | WebSocket app-server URL。                                                                                                                                                                                                                                                                                                                                |
| `authToken`                                       | 未设                                                | WebSocket 传输的 Bearer 令牌。                                                                                                                                                                                                                                                                                                                            |
| `headers`                                         | `{}`                                                | 额外 WebSocket 头。                                                                                                                                                                                                                                                                                                                                       |
| `clearEnv`                                        | `[]`                                                | OpenClaw 构建继承环境后从产生的 stdio app-server 进程中移除的额外环境变量名。OpenClaw 为本地启动保留按 agent 的 `CODEX_HOME` 和继承的 `HOME`。                                                                                                                                                                                                             |
| `codeModeOnly`                                    | `false`                                             | 选择 Codex 的 code-mode-only 工具表面。OpenClaw 动态工具仍注册到 Codex 以便嵌套 `tools.*` 调用通过 app-server `item/tool/call` 桥返回。                                                                                                                                                                                                                   |
| `requestTimeoutMs`                                | `60000`                                             | app-server 控制面调用超时。                                                                                                                                                                                                                                                                                                                               |
| `turnCompletionIdleTimeoutMs`                     | `60000`                                             | Codex 接受轮次后或轮次范围 app-server 请求后,OpenClaw 等待 `turn/completed` 的静默窗口。                                                                                                                                                                                                                                                                  |
| `postToolRawAssistantCompletionIdleTimeoutMs`     | `300000`                                            | 工具交接后、原生工具完成后、post-tool 原始助手进度、原始推理完成或推理进度期间使用的完成-空闲和进度守卫,OpenClaw 等待 `turn/completed`。用于可信或重载荷工作负载,post-tool 合成可合法比最终助手发布预算更久。                                                                                                                                               |
| `mode`                                            | `"yolo"`（除非本地 Codex 要求不允许 YOLO）           | YOLO 或 guardian 审核执行的预设。省略 `danger-full-access`、`never` 审批或 `user` reviewer 的本地 stdio 要求使隐式默认 guardian 生效。                                                                                                                                                                                                                     |
| `approvalPolicy`                                  | `"never"` 或允许的 guardian 审批策略                 | 发送到线程启动/恢复/轮次的原生 Codex 审批策略。Guardian 默认在允许时优先用 `"on-request"`。                                                                                                                                                                                                                                                               |
| `sandbox`                                         | `"danger-full-access"` 或允许的 guardian 沙箱        | 发送到线程启动/恢复的原生 Codex 沙箱模式。Guardian 默认在允许时优先用 `"workspace-write"`,否则 `"read-only"`。OpenClaw 沙箱活跃时,`danger-full-access` 轮次用 Codex `workspace-write`,网络访问从 OpenClaw 沙箱出口设置推导。                                                                                                                              |
| `approvalsReviewer`                               | `"user"` 或允许的 guardian reviewer                  | 允许时用 `"auto_review"` 让 Codex 审查原生审批提示,否则 `guardian_subagent` 或 `user`。`guardian_subagent` 仍是旧版别名。                                                                                                                                                                                                                                 |
| `serviceTier`                                     | 未设                                                | 可选 Codex app-server 服务层。`"priority"` 启用快速模式路由,`"flex"` 请求弹性处理,`null` 清除覆盖,旧版 `"fast"` 作为 `"priority"` 接受。                                                                                                                                                                                                                 |
| `experimental.sandboxExecServer`                  | `false`                                             | 预览选择加入,向 Codex app-server 0.132.0+ 注册 OpenClaw 沙箱支持的 Codex 环境,让原生 Codex 执行可在活跃 OpenClaw 沙箱内运行。                                                                                                                                                                                                                             |

> OpenClaw-owned dynamic tool calls are bounded independently...

OpenClaw 持有的动态工具调用独立于 `appServer.requestTimeoutMs` 设限：Codex `item/tool/call` 请求默认用 90 秒 OpenClaw 看门狗。正数每次调用 `timeoutMs` 参数扩展或缩短该特定工具预算。`image_generate` 工具在工具调用未提供自己的超时时用 `agents.defaults.imageGenerationModel.timeoutMs`,否则用 120 秒图片生成默认。媒体理解 `image` 工具用 `tools.media.image.timeoutSeconds` 或其 60 秒媒体默认。动态工具预算上限 600000 ms。超时时 OpenClaw 在支持处中止工具信号并向 Codex 返回失败的动态工具响应,让轮次可继续而非让会话停在 `processing`。

> After Codex accepts a turn...

Codex 接受轮次后,OpenClaw 响应轮次范围 app-server 请求后,执行器期望 Codex 推进当前轮次并最终以 `turn/completed` 完成原生轮次。app-server 静默超过 `appServer.turnCompletionIdleTimeoutMs` 时,OpenClaw 尽力中断 Codex 轮次、记录诊断超时并释放 OpenClaw 会话通道,让后续聊天消息不排在过期原生轮次后。同一轮次的多数非终态通知解除该短看门狗,因为 Codex 已证明轮次仍活跃。工具交接使用更长的 post-tool 空闲预算：OpenClaw 返回 `item/tool/call` 响应后、`commandExecution` 等原生工具项完成后、原始 `custom_tool_call_output` 完成后、post-tool 原始助手进度、原始推理完成或推理进度后。守卫用 `appServer.postToolRawAssistantCompletionIdleTimeoutMs`（配置时）,默认五分钟。该 post-tool 预算也扩展 Codex 发出下个当前轮次事件前的静默合成窗口进度看门狗。全局 app-server 通知（如速率限制更新）不重置轮次空闲进度。推理完成、评论性 `agentMessage` 完成和 pre-tool 原始推理或助手进度后可跟自动最终回复,所以用 post-progress 回复守卫而非立即释放会话通道。仅最终/非评论性完成的 `agentMessage` 项和 pre-tool 原始助手完成启用助手输出释放：Codex 随后静默无 `turn/completed` 时,OpenClaw 尽力中断原生轮次并释放会话通道。重放安全 stdio app-server 失败（含无助手、工具、活跃项或副作用证据的轮次完成空闲超时）在全新 app-server 尝试上重试一次。不安全超时仍退役卡住的 app-server 客户端并释放 OpenClaw 会话通道。它们还清过期原生线程绑定而非自动重放。完成监视超时显示 Codex 特定超时文本：重放安全情况说响应可能不完整,不安全情况告诉用户重试前验证当前状态。公开超时诊断包含结构字段如最后 app-server 通知方法、原始助手响应项 id/类型/角色、活跃请求/项计数和设防监视状态。最后通知是原始助手响应项时还包含有界助手文本预览。不含原始提示或工具内容。

本地测试仍可用环境覆盖：

- `OPENCLAW_CODEX_APP_SERVER_BIN`
- `OPENCLAW_CODEX_APP_SERVER_ARGS`
- `OPENCLAW_CODEX_APP_SERVER_MODE=yolo|guardian`
- `OPENCLAW_CODEX_APP_SERVER_APPROVAL_POLICY`
- `OPENCLAW_CODEX_APP_SERVER_SANDBOX`

`OPENCLAW_CODEX_APP_SERVER_BIN` 在 `appServer.command` 未设时绕过受管二进制。

`OPENCLAW_CODEX_APP_SERVER_GUARDIAN=1` 已移除。用 `plugins.entries.codex.config.appServer.mode: "guardian"` 替代,或 `OPENCLAW_CODEX_APP_SERVER_MODE=guardian` 用于一次性本地测试。配置更适合可重复部署,因为插件行为与其他 Codex 执行器设置在同一审查文件中。

## 原生 Codex 插件

> Native Codex plugin support uses Codex app-server's own app and plugin capabilities...

原生 Codex 插件支持在与 OpenClaw 执行器轮次相同的 Codex 线程中使用 Codex app-server 自己的应用和插件能力。OpenClaw 不将 Codex 插件翻译为合成 `codex_plugin_*` OpenClaw 动态工具。

`codexPlugins` 仅影响选择原生 Codex 执行器的会话。对内置执行器运行、正常 OpenAI 提供商运行、ACP 对话绑定或其他执行器无效。

最小迁移配置：

```json5
{
  plugins: {
    entries: {
      codex: {
        enabled: true,
        config: {
          codexPlugins: {
            enabled: true,
            allow_destructive_actions: true,
            plugins: {
              "google-calendar": {
                enabled: true,
                marketplaceName: "openai-curated",
                pluginName: "google-calendar",
              },
            },
          },
        },
      },
    },
  },
}
```

> Thread app config is computed when OpenClaw establishes a Codex harness session...

线程应用配置在 OpenClaw 建立 Codex 执行器会话或替换过期 Codex 线程绑定时计算。不在每轮次重算。改 `codexPlugins` 后用 `/new`、`/reset` 或重启 gateway,让未来 Codex 执行器会话用更新后的应用集启动。

迁移资格、应用清单、破坏性操作策略、elicitation 和原生插件诊断见 [Native Codex plugins](/plugins/codex-native-plugins)。

OpenAI 侧应用和插件访问由登录的 Codex 账户控制,Business 和 Enterprise/Edu 工作区还有工作区应用控制。OpenAI 账户和工作区控制概述见 [Using Codex with your ChatGPT plan](https://help.openai.com/en/articles/11369540-using-codex-with-your-chatgpt-plan)。

## Computer Use

> Computer Use is covered in its own setup guide...

Computer Use 在自己的设置指南中：[Codex Computer Use](/plugins/codex-computer-use)。

简要说明：OpenClaw 不供应桌面控制应用或自己执行桌面操作。它准备 Codex app-server、验证 `computer-use` MCP 服务器可用,然后让 Codex 在 Codex 模式轮次中持有原生 MCP 工具调用。

## 运行时边界

> The Codex harness changes the low-level embedded agent executor only.

Codex 执行器仅改底层嵌入式 agent 执行器。

- OpenClaw 动态工具受支持。Codex 让 OpenClaw 执行那些工具,所以 OpenClaw 仍在执行路径中。
- Codex 原生 shell、patch、MCP 和原生应用工具由 Codex 持有。OpenClaw 可通过支持的中继观察或阻止选定的原生事件,但不重写原生工具参数。
- Codex 持有原生压缩。OpenClaw 为频道历史、搜索、`/new`、`/reset` 和未来模型或执行器切换保留记录镜像,但不用 OpenClaw 或上下文引擎摘要器替代 Codex 压缩。
- 媒体生成、媒体理解、TTS、审批和消息工具输出继续走匹配的 OpenClaw 提供商/模型设置。
- `tool_result_persist` 应用于 OpenClaw 持有的记录工具结果,非 Codex 原生工具结果记录。

钩子层、支持的 V1 表面、原生权限处理、队列引导、Codex 反馈上传机制和压缩细节见 [Codex harness runtime](/plugins/codex-harness-runtime)。

## 故障排查

**Codex 不出现在正常 `/model` 提供商中：** 新配置预期如此。选择 `openai/gpt-*` 模型、启用 `plugins.entries.codex.enabled`、检查 `plugins.allow` 是否排除了 `codex`。

**OpenClaw 用内置执行器而非 Codex：** 确保模型引用是官方 OpenAI 提供商上的 `openai/gpt-*` 且 Codex 插件已安装并启用。测试需严格证明时设提供商或模型 `agentRuntime.id: "codex"`。强制 Codex 运行时会失败而非回退到 OpenClaw。

**OpenAI Codex 运行时回退到 API-key 路径：** 收集脱敏 gateway 摘录显示模型、运行时、选定提供商和失败。让受影响的协作者在其 OpenClaw 主机上运行此只读命令（脚本同上,此处省略）。有用摘录通常含 `openai/gpt-5.5` 或 `openai/gpt-5.4`、`Runtime: OpenAI Codex`、`agentRuntime.id` 或 `harnessRuntime`、`candidateProvider: "openai"` 和 `401`/`Incorrect API key`/`No API key` 结果。修正运行应显示 OpenAI OAuth 路径而非纯 OpenAI API-key 失败。

**旧版 Codex 模型引用配置仍在：** 运行 `openclaw doctor --fix`。Doctor 将旧版模型引用重写为 `openai/*`,移除过期会话和整 agent 运行时钉定,保留已有认证 profile 覆盖。

**app-server 被拒绝：** 用 Codex app-server `0.125.0` 或更新。同版本预发布或构建后缀版本如 `0.125.0-alpha.2` 或 `0.125.0+custom` 被拒绝,因为 OpenClaw 测试稳定的 `0.125.0` 协议底线。

**`/codex status` 无法连接：** 检查内置 `codex` 插件是否启用、`plugins.allow` 是否包含它（配了白名单时）、自定义 `appServer.command`/`url`/`authToken` 或头是否有效。

**模型发现慢：** 降低 `plugins.entries.codex.config.discovery.timeoutMs` 或禁用发现。见 [Codex harness reference](/plugins/codex-harness-reference#model-discovery)。

**WebSocket 传输立即失败：** 检查 `appServer.url`、`authToken`、头和远程 app-server 是否说相同 Codex app-server 协议版本。

**原生 shell 或 patch 工具被阻止,报 `Native hook relay unavailable`：** Codex 线程仍尝试用 OpenClaw 不再注册的原生钩子中继 id。这是原生 Codex 钩子传输问题,非 ACP 后端、提供商、GitHub 或 shell 命令失败。在受影响聊天中用 `/new` 或 `/reset` 开始新会话,然后重试无害命令。如果成功一次但下次原生工具调用又失败,将 `/new` 仅作临时规避：重启 Codex app-server 或 OpenClaw Gateway 后将提示复制到新会话,让旧线程被丢弃并重建原生钩子注册。

**非 Codex 模型用内置执行器：** 预期如此,除非提供商或模型运行时策略路由到其他执行器。`auto` 模式下纯非 OpenAI 提供商引用走正常提供商路径。

**Computer Use 已安装但工具不运行：** 从新会话检查 `/codex computer-use status`。工具报 `Native hook relay unavailable` 时用上面的原生钩子中继恢复。见 [Codex Computer Use](/plugins/codex-computer-use#troubleshooting)。

## 相关

- [Codex harness reference](/plugins/codex-harness-reference)
- [Codex harness runtime](/plugins/codex-harness-runtime)
- [Native Codex plugins](/plugins/codex-native-plugins)
- [Codex Computer Use](/plugins/codex-computer-use)
- [Agent runtimes](/concepts/agent-runtimes)
- [Model providers](/concepts/model-providers)
- [OpenAI provider](/providers/openai)
- [OpenAI Codex help](https://help.openai.com/en/collections/14937394-codex)
- [Agent harness plugins](/plugins/sdk-agent-harness)
- [Plugin hooks](/plugins/hooks)
- [Diagnostics export](/gateway/diagnostics)
- [Status](/cli/status)
- [Testing](/help/testing-live#live-codex-app-server-harness-smoke)
