# Messages

> OpenClaw handles inbound messages through a pipeline of session resolution, queueing, streaming, tool execution, and reasoning visibility. This page maps the path from inbound message to reply.

OpenClaw 用一条流水线处理接收消息：会话解析、排队、流式、工具执行、推理可见性。本页讲清楚从接收消息到回复的路径。

---

> ## Message flow (high level)

## 消息流（总体）

> ```
> Inbound message
>   -> routing/bindings -> session key
>   -> queue (if a run is active)
>   -> agent run (streaming + tools)
>   -> outbound replies (channel limits + chunking)
> ```

```
接收消息
  -> 路由 / bindings -> 会话 key
  -> 队列（有活跃运行时）
  -> agent 运行（流式 + 工具）
  -> 发送回复（通道上限 + 分片）
```

> Key knobs live in configuration:
>
> * `messages.*` for prefixes, queueing, and group behavior.
> * `agents.defaults.*` for block streaming and chunking defaults.
> * Channel overrides (`channels.whatsapp.*`, `channels.telegram.*`, etc.) for caps and streaming toggles.

关键开关都在配置里：

- `messages.*`：前缀、排队、群行为。
- `agents.defaults.*`：block 流式和分片默认值。
- 通道覆盖（`channels.whatsapp.*`、`channels.telegram.*` 等）：上限和流式开关。

> See [Configuration](/gateway/configuration) for full schema.

完整 schema 见 [配置](/gateway/configuration)。

---

> ## Inbound dedupe

## 接收去重

> Channels can redeliver the same message after reconnects. OpenClaw keeps a short-lived cache keyed by channel/account/peer/session/message id so duplicate deliveries do not trigger another agent run.

通道在重连后可能重投同一条消息。OpenClaw 维护一个短期缓存，按 channel / account / peer / session / message id 索引，让重复投递不会再触发一次 agent 运行。

---

> ## Inbound debouncing

## 接收防抖

> Rapid consecutive messages from the **same sender** can be batched into a single agent turn via `messages.inbound`. Debouncing is scoped per channel + conversation and uses the most recent message for reply threading/IDs.

**同一发件人**连续快速发的消息可以通过 `messages.inbound` 合并成一个 agent 轮次。防抖按 channel + 对话作用域，回复 threading / ID 用的是最新一条消息。

> Config (global default + per-channel overrides):
>
> ```json5
> {
>   messages: {
>     inbound: {
>       debounceMs: 2000,
>       byChannel: {
>         whatsapp: 5000,
>         slack: 1500,
>         discord: 1500,
>       },
>     },
>   },
> }
> ```

配置（全局默认 + 按通道覆盖）：

```json5
{
  messages: {
    inbound: {
      debounceMs: 2000,
      byChannel: {
        whatsapp: 5000,
        slack: 1500,
        discord: 1500,
      },
    },
  },
}
```

> Notes:
>
> * Debounce applies to **text-only** messages; media/attachments flush immediately.
> * Control commands bypass debouncing so they remain standalone. Channels that explicitly opt in to same-sender DM coalescing can keep DM commands inside the debounce window so a split-send payload can join the same agent turn.

说明：

- 防抖只对**纯文本**消息生效；媒体 / 附件立即 flush。
- 控制命令绕过防抖，保持独立。显式启用同发件人 DM 合并的通道可以把 DM 命令留在防抖窗口里，让拆分发送的载荷加入同一个 agent 轮次。

---

> ## Sessions and devices

## 会话与设备

> Sessions are owned by the gateway, not by clients.

会话由 Gateway 持有，不是客户端。

> * Direct chats collapse into the agent main session key.
> * Groups/channels get their own session keys.
> * The session store and transcripts live on the gateway host.

- 私聊收敛到 agent 的 main 会话 key。
- 群 / 频道有自己的会话 key。
- 会话存储和 transcript 都在 Gateway 宿主机上。

> Multiple devices/channels can map to the same session, but history is not fully synced back to every client. Recommendation: use one primary device for long conversations to avoid divergent context. The Control UI and TUI always show the gateway-backed session transcript, so they are the source of truth.

多个设备 / 通道可以映射到同一个会话，但历史不会全量同步回每个客户端。建议：长对话用一个主设备，避免上下文分叉。Control UI 和 TUI 始终显示 Gateway 后端的会话 transcript，所以它们是权威源。

> Details: [Session management](/concepts/session).

细节：[会话管理](/concepts/session)。

---

> ## Tool result metadata

## 工具结果元数据

> Tool result `content` is the model-visible result. Tool result `details` is runtime metadata for UI rendering, diagnostics, media delivery, and plugins.

工具结果的 `content` 是模型可见的结果。工具结果的 `details` 是运行时元数据，用于 UI 渲染、诊断、媒体投递、插件。

> OpenClaw keeps that boundary explicit:
>
> * `toolResult.details` is stripped before provider replay and compaction input.
> * Persisted session transcripts keep only bounded `details`; oversized metadata is replaced with a compact summary marked `persistedDetailsTruncated: true`.
> * Plugins and tools should put text the model must read in `content`, not only in `details`.

OpenClaw 把这条边界保持显式：

- `toolResult.details` 在 provider 重放和压缩输入前被剥掉。
- 持久化的会话 transcript 只保留有界的 `details`；超大元数据替换成一份紧凑摘要，并标 `persistedDetailsTruncated: true`。
- 插件和工具：模型必须读到的文本要放 `content`，不能只放在 `details` 里。

---

> ## Inbound bodies and history context

## 接收正文和历史上下文

> OpenClaw separates the **prompt body** from the **command body**:
>
> * `BodyForAgent`: primary model-facing text for the current message. Channel plugins should keep this focused on the sender's current prompt-bearing text.
> * `Body`: legacy prompt fallback. This may include channel envelopes and optional history wrappers, but current channels should not rely on it as the primary model input when `BodyForAgent` is available.
> * `CommandBody`: raw user text for directive/command parsing.
> * `RawBody`: legacy alias for `CommandBody` (kept for compatibility).

OpenClaw 把 **prompt 正文**和**命令正文**分开：

- `BodyForAgent`：当前消息给模型看的主文本。通道插件应当保持它聚焦在发件人当前承载 prompt 的文本上。
- `Body`：旧版 prompt 回退。可能包含通道信封和可选的历史封装；当 `BodyForAgent` 可用时，新通道不应再把它当主模型输入。
- `CommandBody`：原始用户文本，用于指令 / 命令解析。
- `RawBody`：`CommandBody` 的旧版别名（保留兼容）。

> When a channel supplies history, it uses a shared wrapper:
>
> * `[Chat messages since your last reply - for context]`
> * `[Current message - respond to this]`

通道带历史时使用共享的封装：

- `[Chat messages since your last reply - for context]`
- `[Current message - respond to this]`

> For **non-direct chats** (groups/channels/rooms), the **current message body** is prefixed with the sender label (same style used for history entries). This keeps real-time and queued/history messages consistent in the agent prompt.

**非私聊**（群 / 频道 / 房间）里，**当前消息正文**前面会加上发件人标签（跟历史条目同一风格）。这样实时消息和排队 / 历史消息在 agent prompt 里保持一致。

> History buffers are **pending-only**: they include group messages that did *not* trigger a run (for example, mention-gated messages) and **exclude** messages already in the session transcript.

历史缓冲是**仅 pending 的**：包含没触发运行的群消息（例如 @ 触发拦下的），**排除**已经在会话 transcript 里的消息。

> Directive stripping only applies to the **current message** section so history remains intact. Channels that wrap history should set `CommandBody` (or `RawBody`) to the original message text and keep `Body` as the combined prompt. Structured history, reply, forwarded, and channel metadata are rendered as user-role untrusted context blocks during prompt assembly. History buffers are configurable via `messages.groupChat.historyLimit` (global default) and per-channel overrides like `channels.slack.historyLimit` or `channels.telegram.accounts.<id>.historyLimit` (set `0` to disable).

指令剥离只对**当前消息**段生效，历史保持完整。封装历史的通道应当把 `CommandBody`（或 `RawBody`）设为原始消息文本，让 `Body` 保持为组合后的 prompt。结构化历史、回复、转发、通道元数据在 prompt 组装期间作为 user 角色的不受信上下文块渲染。历史缓冲通过 `messages.groupChat.historyLimit`（全局默认）和按通道覆盖（如 `channels.slack.historyLimit` 或 `channels.telegram.accounts.<id>.historyLimit`）配置（设 `0` 关闭）。

---

> ## Queueing and followups

## 排队与后续

> If a run is already active, inbound messages are steered into the current run by default. `messages.queue` selects whether active-run messages steer, queue for later, collect into one later turn, or interrupt the active run.

已经有活跃运行时，新接收消息默认转向到当前运行。`messages.queue` 决定：活跃运行期间的消息是 steer、排队等之后、collect 到一轮后续，还是 interrupt 掉当前运行。

> * Configure via `messages.queue` (and `messages.queue.byChannel`).
> * Default mode is `steer`, with a 500ms debounce for Codex steering batches and followup/collect queues.
> * Modes: `steer`, `followup`, `collect`, and `interrupt`.

- 配置在 `messages.queue`（和 `messages.queue.byChannel`）。
- 默认模式 `steer`，对 Codex steering 批次和 followup / collect 队列有 500ms 防抖。
- 模式：`steer`、`followup`、`collect`、`interrupt`。

> Details: [Command queue](/concepts/queue) and [Steering queue](/concepts/queue-steering).

细节：[命令队列](/concepts/queue) 和 [转向队列](/concepts/queue-steering)。

---

> ## Channel run ownership

## 通道运行归属

> Channel plugins may preserve ordering, debounce input, and apply transport backpressure before a message enters the session queue. They should not impose a separate timeout around the agent turn itself. Once a message is routed to a session, long-running work is governed by the session, tool, and runtime lifecycle so all channels report and recover from slow turns consistently.

通道插件可以在消息进入会话队列之前保持顺序、防抖输入、施加传输反压。它们**不应**在 agent 轮次本身之上再加一层独立超时。消息一旦路由到会话，长时工作就由会话、工具、运行时生命周期管，让所有通道一致地报告慢轮次并从中恢复。

---

> ## Streaming, chunking, and batching

## 流式、分片、批量

> Block streaming sends partial replies as the model produces text blocks. Chunking respects channel text limits and avoids splitting fenced code.

block 流式在模型生成文本块时发部分回复。分片尊重通道文本上限，避免切开围栏代码块。

> Key settings:
>
> * `agents.defaults.blockStreamingDefault` (`on|off`, default off)
> * `agents.defaults.blockStreamingBreak` (`text_end|message_end`)
> * `agents.defaults.blockStreamingChunk` (`minChars|maxChars|breakPreference`)
> * `agents.defaults.blockStreamingCoalesce` (idle-based batching)
> * `agents.defaults.humanDelay` (human-like pause between block replies)
> * Channel overrides: `*.blockStreaming` and `*.blockStreamingCoalesce` (non-Telegram channels require explicit `*.blockStreaming: true`)

关键配置：

- `agents.defaults.blockStreamingDefault`（`on|off`，默认 off）
- `agents.defaults.blockStreamingBreak`（`text_end|message_end`）
- `agents.defaults.blockStreamingChunk`（`minChars|maxChars|breakPreference`）
- `agents.defaults.blockStreamingCoalesce`（基于空闲的合并）
- `agents.defaults.humanDelay`（block 回复之间的拟人停顿）
- 通道覆盖：`*.blockStreaming` 和 `*.blockStreamingCoalesce`（非 Telegram 通道需要显式 `*.blockStreaming: true`）

> Details: [Streaming + chunking](/concepts/streaming).

细节：[流式 + 分片](/concepts/streaming)。

---

> ## Reasoning visibility and tokens

## 推理可见性与 token

> OpenClaw can expose or hide model reasoning:
>
> * `/reasoning on|off|stream` controls visibility.
> * Reasoning content still counts toward token usage when produced by the model.
> * Telegram supports reasoning stream into a transient draft bubble that is deleted after final delivery; use `/reasoning on` for persistent reasoning output.

OpenClaw 可以暴露或隐藏模型推理：

- `/reasoning on|off|stream` 控制可见性。
- 模型生成的推理内容仍然计入 token 用量。
- Telegram 支持把推理流到一个临时草稿气泡里，最终投递后删除；要持久化输出推理用 `/reasoning on`。

> Details: [Thinking + reasoning directives](/tools/thinking) and [Token use](/reference/token-use).

细节：[Thinking + reasoning 指令](/tools/thinking) 和 [Token 用量](/reference/token-use)。

---

> ## Prefixes, threading, and replies

## 前缀、线程、回复

> Outbound message formatting is centralized in `messages`:
>
> * `messages.responsePrefix`, `channels.<channel>.responsePrefix`, and `channels.<channel>.accounts.<id>.responsePrefix` (outbound prefix cascade), plus `channels.whatsapp.messagePrefix` (WhatsApp inbound prefix)
> * Reply threading via `replyToMode` and per-channel defaults

发送侧消息格式化集中在 `messages`：

- `messages.responsePrefix`、`channels.<channel>.responsePrefix`、`channels.<channel>.accounts.<id>.responsePrefix`（发送前缀级联），加 `channels.whatsapp.messagePrefix`（WhatsApp 接收前缀）。
- 回复线程通过 `replyToMode` 和按通道默认值。

> Details: [Configuration](/gateway/config-agents#messages) and channel docs.

细节：[配置](/gateway/config-agents#messages) 和各通道文档。

---

> ## Silent replies

## 静默回复

> The exact silent token `NO_REPLY` / `no_reply` means "do not deliver a user-visible reply".
> When a turn also has pending tool media, such as generated TTS audio, OpenClaw strips the silent text but still delivers the media attachment.
> OpenClaw resolves that behavior by conversation type:

精确的静默 token `NO_REPLY` / `no_reply` 意思是"不要发用户可见回复"。
轮次同时有待发送的工具媒体（比如生成的 TTS 音频）时，OpenClaw 剥掉静默文本，但仍然投递媒体附件。
OpenClaw 按对话类型决定行为：

> * Direct conversations never receive `NO_REPLY` prompt guidance. If a direct run accidentally returns a bare silent token, OpenClaw suppresses it instead of rewriting or delivering it.
> * Groups/channels allow silence by default only for automatic group replies. In `message_tool` visible-reply mode, silence means the model does not call `message(action=send)`.
> * Internal orchestration allows silence by default.

- 私聊永远不会收到 `NO_REPLY` 的 prompt 指引。私聊运行不小心返回了一个裸静默 token 时，OpenClaw 直接压制它，不改写也不投递。
- 群 / 频道默认只在自动群回复里允许静默。在 `message_tool` 可见回复模式下，静默意味着模型不调 `message(action=send)`。
- 内部编排默认允许静默。

> OpenClaw also uses silent replies for internal runner failures that happen before any assistant reply in non-direct chats, so groups/channels do not see gateway error boilerplate. Direct chats show compact failure copy by default; raw runner details are shown only when `/verbose` is `on` or `full`.

OpenClaw 在非私聊里、还没有任何 assistant 回复就发生的 runner 内部失败上也用静默回复，让群 / 频道看不到 Gateway 错误样板。私聊默认显示紧凑的失败文案；原始 runner 细节只在 `/verbose` 是 `on` 或 `full` 时显示。

> Defaults live under `agents.defaults.silentReply`; `surfaces.<id>.silentReply` can override group/internal policy per surface.

默认值在 `agents.defaults.silentReply` 下；`surfaces.<id>.silentReply` 可以按 surface 覆盖群 / 内部策略。

> Bare silent replies are dropped on all surfaces, so parent sessions stay quiet instead of rewriting sentinel text into fallback chatter.

裸的静默回复在所有 surface 都丢弃，让父会话保持安静，而不是把哨兵文本改写成回退闲聊。

---

> ## Related

## 相关

> * [Message lifecycle refactor](/concepts/message-lifecycle-refactor) - target durable send and receive design
> * [Streaming](/concepts/streaming) — real-time message delivery
> * [Retry](/concepts/retry) — message delivery retry behavior
> * [Queue](/concepts/queue) — message processing queue
> * [Channels](/channels) — messaging platform integrations

- [消息生命周期重构](/concepts/message-lifecycle-refactor)：目标持久化发送和接收设计
- [流式](/concepts/streaming)：实时消息投递
- [重试](/concepts/retry)：消息投递重试行为
- [队列](/concepts/queue)：消息处理队列
- [通道](/channels)：消息平台集成
