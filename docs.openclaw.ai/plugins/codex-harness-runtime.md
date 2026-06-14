# Codex Harness 运行时

## 架构精读

> 跳过不影响阅读翻译正文。

### Codex 模式和普通 OpenClaw 有什么区别？

普通 OpenClaw 模式下，OpenClaw 持有整个 agent 循环——提示构建、工具执行、上下文压缩、回复生成。Codex 模式下，Codex app-server 接管了原生模型循环——线程管理、工具延续、压缩。OpenClaw 适配自己的插件、工具、会话和诊断表面围绕这个边界。就像微服务架构中的 sidecar 模式——主服务（Codex）做核心业务，sidecar（OpenClaw）处理横切关注点：channel 路由、会话文件、消息交付、动态工具、审批、媒体交付和会话记录镜像。好处是 Codex 的全部原生能力都可用，坏处是两个系统之间的边界需要精确定义。

三层钩子边界：OpenClaw 插件钩子（产品和插件兼容）、Codex app-server 扩展中间件（每回合适配器行为）、Codex 原生钩子（底层生命周期和原生工具策略）。就像 OSI 模型的分层——每层只关心自己的职责，跨层通信通过定义好的接口。

V1 支持契约明确列出什么支持、什么不支持。原生工具参数修改不支持（Codex 原生钩子可阻止但不重写参数），可编辑 Codex 原生会话记录历史不支持（Codex 持有规范历史）。这些是显式边界——不是 bug，是有意的设计决策。

---

此页面记录 Codex harness 回合的运行时契约。关于设置和路由，从 [Codex harness](/plugins/codex-harness) 开始。关于配置字段，参见 [Codex harness reference](/plugins/codex-harness-reference)。

## 概述

Codex 模式不是 OpenClaw 底下换了个模型调用。Codex 持有更多原生模型循环，OpenClaw 围绕该边界适配其插件、工具、会话和诊断表面。

OpenClaw 仍持有 channel 路由、会话文件、可见消息交付、OpenClaw 动态工具、审批、媒体交付和会话记录镜像。Codex 持有规范的原生线程、原生模型循环、原生工具延续和原生压缩。

提示路由跟随选择的运行时，不仅是 provider 字符串。原生 Codex 回合接收 Codex app-server 开发者指令，而显式 OpenClaw 兼容路由保持普通 OpenClaw 系统提示，即使它使用 Codex 风格的 OpenAI 认证或传输。

原生 Codex 根据活动的 Codex 线程配置保持 Codex 持有的基础/模型指令和项目文档行为。OpenClaw 启动和恢复原生 Codex 线程时禁用 Codex 的内置人格，这样工作区人格文件和 OpenClaw agent 身份保持权威。轻量级 OpenClaw 运行仍保留其现有的项目文档抑制。OpenClaw 开发者指令覆盖 OpenClaw 运行时关注点如源 channel 交付、OpenClaw 动态工具、ACP 委托、适配器上下文和活动的 agent 工作区配置文件。OpenClaw 技能目录和工具路由的 `MEMORY.md` 指针被投射为原生 Codex 的回合级协作开发者指令。活动的 `BOOTSTRAP.md` 内容和完整 `MEMORY.md` 后备注入仍使用回合输入引用上下文。

## 线程绑定和模型变更

当 OpenClaw 会话附加到已有 Codex 线程时，下一回合再次向 app-server 发送当前选择的 OpenAI 模型、审批策略、沙箱和服务层。从 `openai/gpt-5.5` 切换到 `openai/gpt-5.2` 保持线程绑定但要求 Codex 以新选择的模型继续。

## 可见回复和心跳

当直接/源聊天回合通过 Codex harness 运行时，可见回复默认为内部 WebChat 表面的自动最终助手交付。这保持 Codex 与 Pi harness 提示契约对齐：agent 正常回复，OpenClaw 将最终文本发布到源对话。当直接/源聊天应故意将最终助手文本保持私密（除非 agent 调用 `message(action="send")`）时设置 `messages.visibleReplies: "message_tool"`。

Codex 心跳回合也默认在可搜索的 OpenClaw 工具目录中获得 `heartbeat_respond`，agent 可记录唤醒是否应保持安静或通知，而无需在最终文本中编码该控制流。

心跳特定的主动性指导作为 Codex 协作模式开发者指令在心跳回合本身上发送。普通聊天回合恢复 Codex Default 模式，而非在正常运行时提示中携带心跳哲学。当非空 `HEARTBEAT.md` 存在时，心跳协作模式指令将 Codex 指向文件而非内联其内容。

## 钩子边界

Codex harness 有三层钩子：

| 层 | 持有者 | 用途 |
| --- | --- | --- |
| OpenClaw 插件钩子 | OpenClaw | OpenClaw 和 Codex harness 之间的产品/插件兼容。 |
| Codex app-server 扩展中间件 | OpenClaw 捆绑插件 | OpenClaw 动态工具周围的每回合适配器行为。 |
| Codex 原生钩子 | Codex | 来自 Codex 配置的底层 Codex 生命周期和原生工具策略。 |

OpenClaw 不使用项目或全局 Codex `hooks.json` 文件路由 OpenClaw 插件行为。对支持的原生工具和权限桥，OpenClaw 为 `PreToolUse`、`PostToolUse`、`PermissionRequest` 和 `Stop` 注入每线程 Codex 配置。

当 Codex app-server 审批启用时（即 `approvalPolicy` 不是 `"never"`），默认注入的原生钩子配置省略 `PermissionRequest`，Codex 的 app-server 审查器和 OpenClaw 的审批桥在审查后处理真实升级。Operator 可在需要兼容中继时显式将 `permission_request` 添加到 `nativeHookRelay.events`。

其他 Codex 钩子如 `SessionStart` 和 `UserPromptSubmit` 仍是 Codex 级控制。它们在 v1 契约中不作为 OpenClaw 插件钩子暴露。

对 OpenClaw 动态工具，OpenClaw 在 Codex 请求调用后执行工具，OpenClaw 在 harness 适配器中触发它持有的插件和中间件行为。对 Codex 原生工具，Codex 持有规范的工具记录。OpenClaw 可镜像选定事件，但不能重写原生 Codex 线程，除非 Codex 通过 app-server 或原生钩子回调暴露该操作。

Codex app-server 报告模式 `PreToolUse` 事件将插件审批请求推迟到匹配的 app-server 审批。如果 OpenClaw `before_tool_call` 钩子返回 `requireApproval` 而原生负载设置报告审批模式（`openclaw_approval_mode` 是 `"report"`），原生钩子中继记录插件审批需求并返回无原生决策。当 Codex 为同一工具使用发送 app-server 审批请求时，OpenClaw 打开插件审批提示并将决策映射回 Codex。Codex `PermissionRequest` 事件是单独的审批路径，当运行时配置为该桥时仍可通过 OpenClaw 审批路由。

Codex app-server 项目通知还为原生 `PostToolUse` 中继未覆盖的原生工具完成提供异步 `after_tool_call` 观察。这些观察仅用于遥测和插件兼容；它们不能阻止、延迟或变更原生工具调用。

压缩和 LLM 生命周期投影来自 Codex app-server 通知和 OpenClaw 适配器状态，而非原生 Codex 钩子命令。OpenClaw 的 `before_compaction`、`after_compaction`、`llm_input` 和 `llm_output` 事件是适配器级观察，不是 Codex 内部请求或压缩负载的逐字节捕获。

Codex 原生 `hook/started` 和 `hook/completed` app-server 通知被投射为 `codex_app_server.hook` agent 事件，用于轨迹和调试。它们不调用 OpenClaw 插件钩子。

## V1 支持契约

Codex 运行时 v1 中支持的：

| 表面 | 支持 | 原因 |
| --- | --- | --- |
| 通过 Codex 的 OpenAI 模型循环 | 支持 | Codex app-server 持有 OpenAI 回合、原生线程恢复和原生工具延续。 |
| OpenClaw channel 路由和交付 | 支持 | Telegram、Discord、Slack、WhatsApp、iMessage 和其他 channel 保持在模型运行时之外。 |
| OpenClaw 动态工具 | 支持 | Codex 要求 OpenClaw 执行这些工具，OpenClaw 保持在执行路径中。 |
| 提示和上下文插件 | 支持 | OpenClaw 将 OpenClaw 特定的提示/上下文投射到 Codex 回合中，同时将 Codex 持有的基础、模型和配置的项目文档提示留在原生 Codex 通道。 |
| 上下文引擎生命周期 | 支持 | 组装、摄取和回合后维护在 Codex 回合周围运行。上下文引擎不替换原生 Codex 压缩。 |
| 动态工具钩子 | 支持 | `before_tool_call`、`after_tool_call` 和工具结果中间件在 OpenClaw 持有的动态工具周围运行。 |
| 生命周期钩子 | 作为适配器观察支持 | `llm_input`、`llm_output`、`agent_end`、`before_compaction` 和 `after_compaction` 以真实的 Codex 模式负载触发。 |
| 最终答案修订门控 | 通过原生钩子中继支持 | Codex `Stop` 中继到 `before_agent_finalize`；`revise` 要求 Codex 在最终化前再做一次模型通过。 |
| 原生 shell、patch 和 MCP 阻止或观察 | 通过原生钩子中继支持 | Codex `PreToolUse` 和 `PostToolUse` 为已提交的原生工具表面中继。支持阻止；不支持参数重写。 |
| 原生权限策略 | 通过 Codex app-server 审批和兼容原生钩子中继支持 | Codex app-server 审批请求在 Codex 审查后通过 OpenClaw 路由。`PermissionRequest` 原生钩子中继对原生审批模式是 opt-in 的。 |
| App-server 轨迹捕获 | 支持 | OpenClaw 记录它发送给 app-server 的请求和接收到的 app-server 通知。 |

Codex 运行时 v1 中不支持的：

| 表面 | V1 边界 | 未来路径 |
| --- | --- | --- |
| 原生工具参数变更 | Codex 原生工具前钩子可阻止，但 OpenClaw 不重写 Codex 原生工具参数。 | 需要 Codex 钩子/schema 支持替换工具输入。 |
| 可编辑 Codex 原生会话记录历史 | Codex 持有规范的原生线程历史。OpenClaw 持有镜像并可投射未来上下文，但不应变更不支持的内部。 | 如果需要原生线程手术则添加显式 Codex app-server API。 |
| Codex 原生工具记录的 `tool_result_persist` | 该钩子变换 OpenClaw 持有的会话记录写入，不是 Codex 原生工具记录。 | 可镜像变换的记录，但规范重写需要 Codex 支持。 |
| 丰富的原生压缩元数据 | OpenClaw 可请求原生压缩，但不接收稳定的保留/丢弃列表、token 变化、完成摘要或摘要负载。 | 需要更丰富的 Codex 压缩事件。 |
| 压缩干预 | OpenClaw 不让插件或上下文引擎否决、重写或替换原生 Codex 压缩。 | 如果插件需要否决或重写原生压缩则添加 Codex 前/后压缩钩子。 |
| 逐字节模型 API 请求捕获 | OpenClaw 可捕获 app-server 请求和通知，但 Codex 核心在内部构建最终的 OpenAI API 请求。 | 需要 Codex 模型请求追踪事件或调试 API。 |

## 原生权限和 MCP 引出

对 `PermissionRequest`，OpenClaw 仅在策略决定时返回显式允许或拒绝决策。无决策结果不是允许。Codex 将其视为无钩子决策并回退到自己的守护者或用户审批路径。

Codex app-server 审批模式默认省略此原生钩子。此行为在 `permission_request` 显式包含在 `nativeHookRelay.events` 中或兼容运行时安装它时适用。

当 operator 为 Codex 原生权限请求选择 `allow-always` 时，OpenClaw 在有界会话窗口内记住该精确的 provider/会话/工具输入/cwd 指纹。记住的决策故意仅精确匹配：更改的命令、参数、工具负载或 cwd 创建新的审批。

当 Codex 将 `_meta.codex_approval_kind` 标记为 `"mcp_tool_call"` 时，Codex MCP 工具审批引出通过 OpenClaw 的插件审批流程路由。Codex `request_user_input` 提示发送回源聊天，下一个排队的后续消息回答该原生服务器请求，而非被引导为额外上下文。其他 MCP 引出请求做默认拒绝。

关于承载这些提示的通用插件审批流程，参见 [Plugin permission requests](/plugins/plugin-permission-requests)。

## 队列引导

活跃运行队列引导映射到 Codex app-server `turn/steer`。使用默认 `messages.queue.mode: "steer"`，OpenClaw 为配置的安静窗口批量处理引导模式聊天消息，并按到达顺序将它们作为一个 `turn/steer` 请求发送。

Codex 审查和手动压缩回合可拒绝同回合引导。此时 OpenClaw 等待活跃运行完成后再启动提示。当消息应默认排队而非引导时使用 `/queue followup` 或 `/queue collect`。参见 [Steering queue](/concepts/queue-steering)。

## Codex 反馈上传

当 `/diagnostics [note]` 在使用原生 Codex harness 的会话中被批准时，OpenClaw 也为相关 Codex 线程调用 Codex app-server `feedback/upload`。上传要求 app-server 为每个列出的线程和生成的 Codex 子线程包含日志。

上传通过 Codex 的正常反馈路径到达 OpenAI 服务器。如果该 app-server 中禁用了 Codex 反馈，命令返回 app-server 错误。完成的诊断回复列出已发送线程的 channel、OpenClaw 会话 id、Codex 线程 id 和本地 `codex resume <thread-id>` 命令。

如果拒绝或忽略审批，OpenClaw 不打印那些 Codex id 也不发送 Codex 反馈。上传不替换本地 Gateway 诊断导出。参见 [Diagnostics export](/gateway/diagnostics) 了解审批、隐私、本地捆绑和群聊行为。

仅在特别想要当前附加线程的 Codex 反馈上传而不需要完整 Gateway 诊断捆绑时使用 `/codex diagnostics [note]`。

## 压缩和会话记录镜像

当选择的模型使用 Codex harness 时，原生线程压缩归 Codex app-server 管理。OpenClaw 不为 Codex 回合运行预检压缩，不用上下文引擎压缩替换 Codex 压缩，当原生 Codex 压缩无法启动时不回退到 OpenClaw 或公共 OpenAI 摘要。OpenClaw 为 channel 历史、搜索、`/new`、`/reset` 和未来模型或 harness 切换保持会话记录镜像。

显式压缩请求如 `/compact` 或插件请求的手动压缩操作通过 `thread/compact/start` 启动原生 Codex 压缩。OpenClaw 在启动该原生操作后返回。它不等待完成，不施加单独的 OpenClaw 超时，不重启共享 Codex app-server，也不将操作记录为 OpenClaw 已完成的压缩。

当上下文引擎请求 Codex 线程引导投影时，OpenClaw 将工具调用名称和 id、输入形态和脱敏的工具结果内容投射到新的 Codex 线程。它不将原始工具调用参数值复制到该投影中。

镜像包括用户提示、最终助手文本和 app-server 发出时的轻量级 Codex 推理或计划记录。目前 OpenClaw 仅在请求压缩时记录显式原生压缩启动信号。它不暴露人类可读的压缩摘要或 Codex 压缩后保留条目的可审计列表。

因为 Codex 持有规范的原生线程，`tool_result_persist` 当前不重写 Codex 原生工具结果记录。它仅在 OpenClaw 写入 OpenClaw 持有的会话记录工具结果时适用。

## 媒体和交付

OpenClaw 继续持有媒体交付和媒体 provider 选择。图片、视频、音乐、PDF、TTS 和媒体理解使用匹配的 provider/模型设置如 `agents.defaults.imageGenerationModel`、`videoGenerationModel`、`pdfModel` 和 `messages.tts`。

文本、图片、视频、音乐、TTS、审批和消息工具输出继续通过普通 OpenClaw 交付路径。媒体生成不需要遗留运行时。当 Codex 发出带有 `savedPath` 的原生图片生成项目时，OpenClaw 通过普通回复媒体路径转发该精确文件，即使 Codex 回合没有助手文本。

## 相关

- [Codex harness](/plugins/codex-harness)
- [Codex harness reference](/plugins/codex-harness-reference)
- [Native Codex plugins](/plugins/codex-native-plugins)
- [Plugin hooks](/plugins/hooks)
- [Agent harness plugins](/plugins/sdk-agent-harness)
- [Diagnostics export](/gateway/diagnostics)
- [Trajectory export](/tools/trajectory)
