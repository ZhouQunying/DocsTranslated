# Codex Harness 参考

## 架构精读

> 跳过不影响阅读翻译正文。

### app-server 传输：子进程 vs 远程连接

Codex app-server 有两种传输模式。stdio 模式：OpenClaw 把 Codex 二进制作为子进程启动，版本与捆绑插件绑定。websocket 模式：OpenClaw 连接已运行的远程 app-server 实例。这个设计本质上是 sidecar 模式的两种部署拓扑——stdio 是 colocated sidecar（同一进程树），websocket 是 remote sidecar（独立进程甚至独立机器）。好处是灵活：本地开发用 stdio 零配置，生产环境可部署独立的 app-server 集群。坏处是 websocket 模式下 loopback-only 的功能（如 sandbox exec server）不可用。

第二个设计：YOLO 与 guardian 双模。审批策略和沙箱模式是两个正交的安全维度。审批维度：`never`（无审批）→ `on-request`（按需审批）。沙箱维度：`danger-full-access`（全权限）→ `workspace-write`（仅工作区写入）。两个维度的默认值联动——YOLO 模式同时关闭审批和放宽沙箱，guardian 模式同时开启审批和收紧沙箱。就像防火墙的 zone 概念：你在 DMZ 和内网之间切换时，一整套规则同时变更，而不是逐条配置。

第三个边界：环境变量隔离。OpenClaw 为每个 agent 设置独立的 `CODEX_HOME`，Codex 的配置、账户、插件缓存和线程状态都限定在该 agent 目录下。`clearEnv` 机制在启动子进程前清除指定的环境变量，防止 Gateway 级的 API 密钥意外流入 Codex 子进程导致错误计费。这就像容器运行时的 namespace 隔离——每个容器看到自己的环境，不会泄露宿主机状态。

---

此页面覆盖捆绑 `codex` 插件的详细配置。关于设置和路由决策，从 [Codex harness](/plugins/codex-harness) 开始。

## 插件配置表面

所有 Codex harness 设置位于 `plugins.entries.codex.config` 下。

支持的顶层字段：

| 字段 | 默认值 | 含义 |
| --- | --- | --- |
| `discovery` | 启用 | Codex app-server `model/list` 的模型发现设置。 |
| `appServer` | 托管 stdio app-server | 传输、命令、认证、审批、沙箱和超时设置。 |
| `codexDynamicToolsLoading` | `"searchable"` | 使用 `"direct"` 将 OpenClaw 动态工具直接放入初始 Codex 工具上下文。 |
| `codexPlugins` | 禁用 | 原生 Codex 插件/应用支持。参见 [Native Codex plugins](/plugins/codex-native-plugins)。 |
| `computerUse` | 禁用 | Codex Computer Use 设置。参见 [Codex Computer Use](/plugins/codex-computer-use)。 |

## App-server 传输

默认情况下 OpenClaw 启动捆绑插件附带的托管 Codex 二进制：

```bash
codex app-server --listen stdio://
```

这使 app-server 版本与捆绑 `codex` 插件保持同步。仅在需要运行不同可执行文件时设置 `appServer.command`。

对已运行的 app-server，使用 WebSocket 传输：

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

关键 `appServer` 传输字段：

| 字段 | 默认值 | 含义 |
| --- | --- | --- |
| `transport` | `"stdio"` | `"stdio"` 启动 Codex；`"websocket"` 连接到 `url`。 |
| `command` | 托管 Codex 二进制 | stdio 传输的可执行文件。 |
| `url` | 未设置 | WebSocket app-server URL。 |
| `authToken` | 未设置 | WebSocket 传输的 Bearer token。 |
| `requestTimeoutMs` | `60000` | app-server 控制面调用超时。 |
| `turnCompletionIdleTimeoutMs` | `60000` | Codex 接受回合后 OpenClaw 等待 `turn/completed` 的安静窗口。 |
| `serviceTier` | 未设置 | `"priority"` 启用快速路由，`"flex"` 请求弹性处理。 |

插件阻止较旧或未版本化的 app-server 握手。Codex app-server 必须报告稳定版本 `0.125.0` 或更新。

## 审批和沙箱模式

本地 stdio app-server 会话默认为 YOLO 模式：`approvalPolicy: "never"`、`approvalsReviewer: "user"`、`sandbox: "danger-full-access"`。这个受信任的本地操作者姿态让无人值守的 OpenClaw 回合和心跳无需原生审批提示即可推进。

设置 `appServer.mode: "guardian"` 启用 Codex guardian 审查审批：

```json5
{
  plugins: {
    entries: {
      codex: {
        enabled: true,
        config: {
          appServer: {
            mode: "guardian",
            serviceTier: "priority",
          },
        },
      },
    },
  },
}
```

`guardian` 预设展开为 `approvalPolicy: "on-request"`、`approvalsReviewer: "auto_review"`、`sandbox: "workspace-write"`。单个策略字段可覆盖 `mode`。

当 OpenClaw 沙箱处于活跃状态时，本地 Codex app-server 进程仍在 Gateway 主机上运行。OpenClaw 禁用 Codex 原生 Code Mode、用户 MCP 服务器和应用插件执行。Shell 访问通过 OpenClaw 沙箱支持的动态工具（如 `sandbox_exec` 和 `sandbox_process`）暴露。

## 沙箱化原生执行

稳定默认值是默认拒绝：活跃的 OpenClaw 沙箱禁用从 Codex app-server 主机运行的原生 Codex 执行表面。使用 `appServer.experimental.sandboxExecServer: true` 尝试 Codex 的远程环境支持与 OpenClaw 沙箱后端集成。此预览路径需要 Codex app-server 0.132.0 或更新。

当该标志开启且当前 OpenClaw 会话被沙箱化时，OpenClaw 启动由活跃沙箱支持的本地 loopback exec-server，向 Codex app-server 注册它，并使用该 OpenClaw 持有的环境启动 Codex 线程和回合。如果 app-server 无法注册环境，运行默认拒绝而非静默回退到主机执行。

此预览路径仅限本地。远程 WebSocket app-server 无法访问 loopback exec-server，除非它们在同一主机上。OpenClaw 拒绝该组合。

## 认证和环境隔离

认证按以下顺序选择：

1. agent 的显式 OpenClaw Codex 认证配置文件
2. app-server 在该 agent 的 Codex home 中的现有账户
3. 仅限本地 stdio app-server 启动时，`CODEX_API_KEY`，然后 `OPENAI_API_KEY`

当 OpenClaw 检测到 ChatGPT 订阅式 Codex 认证配置文件时，它从启动的 Codex 子进程中移除 `CODEX_API_KEY` 和 `OPENAI_API_KEY`。这使 Gateway 级 API 密钥可用于嵌入或直接 OpenAI 模型，而不会让原生 Codex app-server 回合意外通过 API 计费。

stdio app-server 启动默认继承 OpenClaw 的进程环境。OpenClaw 持有 Codex app-server 账户桥接并将 `CODEX_HOME` 设置为该 agent 的 OpenClaw 状态下的逐 agent 目录。这使 Codex 配置、账户、插件缓存/数据和线程状态限定在 OpenClaw agent 范围内，而非从操作者个人 `~/.codex` home 泄露。

OpenClaw 不为普通本地 app-server 启动重写 `HOME`。Codex 运行的子进程（如 `openclaw`、`gh`、`git`、云 CLI 和 shell 命令）看到正常的进程 home，可以找到用户 home 配置和 token。

如果部署需要额外的环境隔离，将变量添加到 `appServer.clearEnv`：

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

`appServer.clearEnv` 仅影响启动的 Codex app-server 子进程。OpenClaw 在本地启动归一化期间从此列表中移除 `CODEX_HOME` 和 `HOME`：`CODEX_HOME` 保持逐 agent，`HOME` 保持继承以便子进程使用正常的用户 home 状态。

## 动态工具

Codex 动态工具默认为 `searchable` 加载。OpenClaw 不暴露与 Codex 原生工作区操作重复的动态工具：`read`、`write`、`edit`、`apply_patch`、`exec`、`process`、`update_plan`。

其余 OpenClaw 集成工具（如消息、媒体、cron、浏览器、节点、gateway、`heartbeat_respond` 和 `web_search`）通过 Codex 工具搜索在 `openclaw` 命名空间下可用。这使初始模型上下文更小。`sessions_yield` 和仅消息工具的源回复保持直接暴露，因为这些是回合控制契约。

仅在连接到无法搜索延迟动态工具的自定义 Codex app-server 或调试完整工具负载时设置 `codexDynamicToolsLoading: "direct"`。

## 超时

OpenClaw 持有的动态工具调用独立于 `appServer.requestTimeoutMs` 进行限制。每个 Codex `item/tool/call` 请求按以下顺序使用第一个可用超时：

- 正值的逐调用 `timeoutMs` 参数
- 对 `image_generate`，`agents.defaults.imageGenerationModel.timeoutMs`
- 对无配置超时的 `image_generate`，120 秒图片生成默认值
- 对媒体理解 `image` 工具，`tools.media.image.timeoutSeconds` 转为毫秒，或 60 秒媒体默认值
- 90 秒动态工具默认值

动态工具预算上限为 600000 毫秒。超时时 OpenClaw 中止工具信号并向 Codex 返回失败的动态工具响应，使回合可以继续而非让会话卡在 `processing`。

Codex 接受回合后，harness 期望 Codex 取得当前回合进展并最终用 `turn/completed` 完成原生回合。如果 app-server 在 `turnCompletionIdleTimeoutMs` 内保持安静，OpenClaw 尽力中断 Codex 回合、记录诊断超时并释放 OpenClaw 会话通道。

工具交接使用更长的工具后空闲预算：OpenClaw 返回 `item/tool/call` 响应后、原生工具项目完成后、原始助手/推理进展后，使用 `postToolRawAssistantCompletionIdleTimeoutMs`（默认五分钟）。回放安全的 stdio app-server 失败重试一次；不安全的超时使卡住的 app-server 客户端退役并清除过时的原生线程绑定。

## 模型发现

默认情况下 Codex 插件向 app-server 查询可用模型。模型可用性由 Codex app-server 持有，当 OpenClaw 升级捆绑 `@openai/codex` 版本或部署指向不同 Codex 二进制时列表可能变更。

如果发现失败或超时，OpenClaw 使用捆绑的回退目录：GPT-5.5、GPT-5.4 mini、GPT-5.2。

当前捆绑 harness 是 `@openai/codex` `0.135.0`。

在 `plugins.entries.codex.config.discovery` 下调优发现：

```json5
{
  plugins: {
    entries: {
      codex: {
        enabled: true,
        config: {
          discovery: {
            enabled: true,
            timeoutMs: 2500,
          },
        },
      },
    },
  },
}
```

禁用发现以让启动时跳过 Codex 探测并仅使用回退目录。

## 工作区引导文件

Codex 通过原生项目文档发现自行处理 `AGENTS.md`。OpenClaw 不写入合成的 Codex 项目文档文件，因为 Codex 回退仅在 `AGENTS.md` 缺失时适用。

对 OpenClaw 工作区一致性，Codex harness 解析其他引导文件。`SOUL.md`、`IDENTITY.md`、`TOOLS.md` 和 `USER.md` 作为 OpenClaw Codex 开发者指令转发。紧凑的 OpenClaw 技能列表作为回合范围协作开发者指令转发。`MEMORY.md` 内容在记忆工具可用时不粘贴到原生 Codex 回合输入中；harness 添加小型工作区记忆指针到回合范围协作开发者指令中。当工具被禁用、记忆搜索不可用或活跃工作区与 agent 记忆工作区不同时，`MEMORY.md` 使用正常的有界回合上下文路径。

## 环境覆盖

环境覆盖仍可用于本地测试：

- `OPENCLAW_CODEX_APP_SERVER_BIN`
- `OPENCLAW_CODEX_APP_SERVER_ARGS`
- `OPENCLAW_CODEX_APP_SERVER_MODE=yolo|guardian`
- `OPENCLAW_CODEX_APP_SERVER_APPROVAL_POLICY`
- `OPENCLAW_CODEX_APP_SERVER_SANDBOX`

## 相关

- [Codex harness](/plugins/codex-harness)
- [Codex harness runtime](/plugins/codex-harness-runtime)
- [Native Codex plugins](/plugins/codex-native-plugins)
- [Codex Computer Use](/plugins/codex-computer-use)
