# Streaming and chunking

> OpenClaw has two separate streaming layers:
>
> * **Block streaming (channels):** emit completed **blocks** as the assistant writes. These are normal channel messages (not token deltas).
> * **Preview streaming (Telegram/Discord/Slack):** update a temporary **preview message** while generating.

OpenClaw 有两层独立的流式机制：

- **块流式（通道）**：assistant 写出完整**块**就发出去。这些是常规通道消息（不是 token 增量）。
- **预览流式（Telegram / Discord / Slack）**：生成过程中更新一条临时的**预览消息**。

> There is **no true token-delta streaming** to channel messages today. Preview streaming is message-based (send + edits/appends).

目前**没有**真正的 token 增量流式发到通道消息。预览流式是基于消息的（发送 + 编辑 / 追加）。

---

> ## Block streaming (channel messages)

## 块流式（通道消息）

> Block streaming sends assistant output in coarse chunks as it becomes available.

块流式把 assistant 的输出拆成大块，写好一块就发一块。

> ```
> Model output
>   └─ text_delta/events
>        ├─ (blockStreamingBreak=text_end)
>        │    └─ chunker emits blocks as buffer grows
>        └─ (blockStreamingBreak=message_end)
>             └─ chunker flushes at message_end
>                    └─ channel send (block replies)
> ```

```
模型输出
  └─ text_delta / events
       ├─ (blockStreamingBreak=text_end)
       │    └─ chunker 在缓冲增长时发出块
       └─ (blockStreamingBreak=message_end)
            └─ chunker 在 message_end 时一次性 flush
                   └─ 通道发送（块回复）
```

> Legend:
>
> * `text_delta/events`: model stream events (may be sparse for non-streaming models).
> * `chunker`: `EmbeddedBlockChunker` applying min/max bounds + break preference.
> * `channel send`: actual outbound messages (block replies).

图例：

- `text_delta / events`：模型流事件（非流式模型可能稀疏）。
- `chunker`：`EmbeddedBlockChunker`，应用 min / max 边界和切分偏好。
- `channel send`：实际发出的消息（块回复）。

> **Controls:**
>
> * `agents.defaults.blockStreamingDefault`: `"on"`/`"off"` (default off).
> * Channel overrides: `*.blockStreaming` (and per-account variants) to force `"on"`/`"off"` per channel.
> * `agents.defaults.blockStreamingBreak`: `"text_end"` or `"message_end"`.
> * `agents.defaults.blockStreamingChunk`: `{ minChars, maxChars, breakPreference? }`.
> * `agents.defaults.blockStreamingCoalesce`: `{ minChars?, maxChars?, idleMs? }` (merge streamed blocks before send).
> * Channel hard cap: `*.textChunkLimit` (e.g., `channels.whatsapp.textChunkLimit`).
> * Channel chunk mode: `*.chunkMode` (`length` default, `newline` splits on blank lines (paragraph boundaries) before length chunking).
> * Discord soft cap: `channels.discord.maxLinesPerMessage` (default 17) splits tall replies to avoid UI clipping.

**控制**：

- `agents.defaults.blockStreamingDefault`：`"on"` / `"off"`（默认关）。
- 通道覆盖：`*.blockStreaming`（及按账号变体），按通道强制 `"on"` / `"off"`。
- `agents.defaults.blockStreamingBreak`：`"text_end"` 或 `"message_end"`。
- `agents.defaults.blockStreamingChunk`：`{ minChars, maxChars, breakPreference? }`。
- `agents.defaults.blockStreamingCoalesce`：`{ minChars?, maxChars?, idleMs? }`（发送前合并流块）。
- 通道硬上限：`*.textChunkLimit`（如 `channels.whatsapp.textChunkLimit`）。
- 通道分片模式：`*.chunkMode`（默认 `length`；`newline` 优先按空行（段落边界）切，再按长度切）。
- Discord 软上限：`channels.discord.maxLinesPerMessage`（默认 17）切分高回复，避免 UI 截断。

> **Boundary semantics:**
>
> * `text_end`: stream blocks as soon as chunker emits; flush on each `text_end`.
> * `message_end`: wait until assistant message finishes, then flush buffered output.

**边界语义**：

- `text_end`：分块器一出块就立刻发；每次 `text_end` 时 flush。
- `message_end`：等 assistant 消息写完，再一次性 flush 缓冲输出。

> `message_end` still uses the chunker if the buffered text exceeds `maxChars`, so it can emit multiple chunks at the end.

`message_end` 时如果缓冲文本超过 `maxChars`，仍走分块器，结尾可能发多个块。

> ### Media delivery with block streaming

### 块流式下的媒体投递

> Streaming media must use structured payload fields such as `mediaUrl` or `mediaUrls`; streamed text is not parsed as an attachment command. When block streaming sends media early, OpenClaw remembers that delivery for the turn. If the final assistant payload repeats the same media URL, the final delivery strips the duplicate media instead of sending the attachment again.

流式媒体必须用 `mediaUrl` 或 `mediaUrls` 这类结构化载荷字段；流式文本不会被当作附件命令解析。块流式提前发了媒体，OpenClaw 就记下这一轮投了什么。最终 assistant 载荷里又出现同一个媒体 URL 时，最终投递会把重复媒体剥掉，不再发一次附件。

> Exact duplicate final payloads are suppressed. If the final payload adds distinct text around media that was already streamed, OpenClaw still sends the new text while keeping the media single-delivery. This prevents duplicate voice notes or files on channels such as Telegram.

完全重复的最终载荷直接丢弃。如果最终载荷只是在已发过的媒体周围加了新文本，OpenClaw 仍发新文本，但媒体只投递一次。这样在 Telegram 这类通道上就不会出现重复的语音笔记或文件。

---

> ## Chunking algorithm (low/high bounds)

## 分片算法（低 / 高边界）

> Block chunking is implemented by `EmbeddedBlockChunker`:
>
> * **Low bound:** don't emit until buffer >= `minChars` (unless forced).
> * **High bound:** prefer splits before `maxChars`; if forced, split at `maxChars`.
> * **Break preference:** `paragraph` → `newline` → `sentence` → `whitespace` → hard break.
> * **Code fences:** never split inside fences; when forced at `maxChars`, close + reopen the fence to keep Markdown valid.

块分片由 `EmbeddedBlockChunker` 实现：

- **低边界**：缓冲 < `minChars` 时不发（除非强制）。
- **高边界**：优先在 `maxChars` 之前切；强制时在 `maxChars` 处切。
- **切分偏好**：`paragraph` → `newline` → `sentence` → `whitespace` → 硬切。
- **代码围栏**：永远不在围栏内切；在 `maxChars` 强制切时，关上再开围栏保持 Markdown 合法。

> `maxChars` is clamped to the channel `textChunkLimit`, so you can't exceed per-channel caps.

`maxChars` 不会超过通道的 `textChunkLimit`，所以单通道的上限是硬上限。

---

> ## Coalescing (merge streamed blocks)

## 合并流块

> When block streaming is enabled, OpenClaw can **merge consecutive block chunks** before sending them out. This reduces "single-line spam" while still providing progressive output.

块流式开启时，OpenClaw 可以在发送前**合并连续块**。这能减少单行刷屏，同时仍保持进度感。

> * Coalescing waits for **idle gaps** (`idleMs`) before flushing.
> * Buffers are capped by `maxChars` and will flush if they exceed it.
> * `minChars` prevents tiny fragments from sending until enough text accumulates (final flush always sends remaining text).
> * Joiner is derived from `blockStreamingChunk.breakPreference` (`paragraph` → `\n\n`, `newline` → `\n`, `sentence` → space).
> * Channel overrides are available via `*.blockStreamingCoalesce` (including per-account configs).
> * Default coalesce `minChars` is bumped to 1500 for Signal/Slack/Discord unless overridden.

- 合并等**空闲间隙**（`idleMs`）才推出。
- 缓冲上限 `maxChars`，超了就推出。
- `minChars` 防止小碎片在文本积够之前发出（最终推出总会把剩下的文本发掉）。
- 连接符从 `blockStreamingChunk.breakPreference` 派生（`paragraph` → `\n\n`、`newline` → `\n`、`sentence` → 空格）。
- 通道覆盖：`*.blockStreamingCoalesce`（含按账号配置）。
- Signal / Slack / Discord 的默认 `minChars` 升到 1500，除非显式覆盖。

---

> ## Human-like pacing between blocks

## 块之间的拟人节奏

> When block streaming is enabled, you can add a **randomized pause** between block replies (after the first block). This makes multi-bubble responses feel more natural.

块流式开启时，可以在块回复之间（第一块之后）加一个**随机停顿**，让多气泡回复看起来更自然。

> * Config: `agents.defaults.humanDelay` (override per agent via `agents.list[].humanDelay`).
> * Modes: `off` (default), `natural` (800-2500ms), `custom` (`minMs`/`maxMs`).
> * Applies only to **block replies**, not final replies or tool summaries.

- 配置：`agents.defaults.humanDelay`（按 agent 覆盖用 `agents.list[].humanDelay`）。
- 模式：`off`（默认）、`natural`（800-2500ms）、`custom`（`minMs` / `maxMs`）。
- 只对 **块回复**生效，不影响最终回复或工具摘要。

---

> ## "Stream chunks or everything"

## "按块流"还是"全部流"

> This maps to:
>
> * **Stream chunks:** `blockStreamingDefault: "on"` + `blockStreamingBreak: "text_end"` (emit as you go). Non-Telegram channels also need `*.blockStreaming: true`.
> * **Stream everything at end:** `blockStreamingBreak: "message_end"` (flush once, possibly multiple chunks if very long).
> * **No block streaming:** `blockStreamingDefault: "off"` (only final reply).

对应到：

- **按块流**：`blockStreamingDefault: "on"` + `blockStreamingBreak: "text_end"`（边写边发）。非 Telegram 通道还要 `*.blockStreaming: true`。
- **末尾流出全部**：`blockStreamingBreak: "message_end"`（一次性推出，超长时可能分多块）。
- **不开块流式**：`blockStreamingDefault: "off"`（只发最终回复）。

> **Channel note:** Block streaming is **off unless** `*.blockStreaming` is explicitly set to `true`. Channels can stream a live preview (`channels.<channel>.streaming`) without block replies.

**通道说明**：除非 `*.blockStreaming` 显式设成 `true`，否则块流式**关**。通道可以只开实时预览流式（`channels.<channel>.streaming`），不开块回复。

> Config location reminder: the `blockStreaming*` defaults live under `agents.defaults`, not the root config.

配置位置提醒：`blockStreaming*` 默认值在 `agents.defaults` 下，不是根配置。

---

> ## Preview streaming modes

## 预览流式模式

> Canonical key: `channels.<channel>.streaming`

权威 key：`channels.<channel>.streaming`

> Modes:
>
> * `off`: disable preview streaming.
> * `partial`: single preview that is replaced with latest text.
> * `block`: preview updates in chunked/appended steps.
> * `progress`: progress/status preview during generation, final answer at completion.

模式：

- `off`：关闭预览流式。
- `partial`：单条预览，用最新文本不断覆盖。
- `block`：预览按分片 / 追加步骤更新。
- `progress`：生成期间的进度 / 状态预览，完成时发最终答案。

> `streaming.mode: "block"` is a preview-streaming mode for edit-capable channels such as Discord and Telegram. It does not enable channel block delivery there. Use `streaming.block.enabled` or the legacy `blockStreaming` channel key when you want normal block replies. Microsoft Teams is the exception: it has no draft-preview block transport, so `streaming.mode: "block"` maps to Teams block delivery instead of native partial/progress streaming.

`streaming.mode: "block"` 是一种预览流式模式，用于 Discord、Telegram 这类支持编辑的通道。它**不会**启用这些通道的块投递。要开常规块回复，用 `streaming.block.enabled` 或旧版 `blockStreaming` 通道 key。Microsoft Teams 是例外：Teams 没有草稿预览的块传输，所以 `streaming.mode: "block"` 在 Teams 上映射到块投递，而非原生 partial / progress 流式。

> ### Channel mapping

### 通道映射

> | Channel    | `off` | `partial` | `block` | `progress`              |
> | ---------- | ----- | --------- | ------- | ----------------------- |
> | Telegram   | ✅     | ✅         | ✅       | editable progress draft |
> | Discord    | ✅     | ✅         | ✅       | editable progress draft |
> | Slack      | ✅     | ✅         | ✅       | ✅                       |
> | Mattermost | ✅     | ✅         | ✅       | ✅                       |
> | MS Teams   | ✅     | ✅         | ✅       | native progress stream  |

| 通道       | `off` | `partial` | `block` | `progress`            |
| ---------- | ----- | --------- | ------- | --------------------- |
| Telegram   | ✅     | ✅         | ✅       | 可编辑的进度草稿      |
| Discord    | ✅     | ✅         | ✅       | 可编辑的进度草稿      |
| Slack      | ✅     | ✅         | ✅       | ✅                     |
| Mattermost | ✅     | ✅         | ✅       | ✅                     |
| MS Teams   | ✅     | ✅         | ✅       | 原生 progress 流      |

> Slack-only:
>
> * `channels.slack.streaming.nativeTransport` toggles Slack native streaming API calls when `channels.slack.streaming.mode="partial"` (default: `true`).
> * Slack native streaming and Slack assistant thread status require a reply thread target. Top-level DMs do not show that thread-style preview, but they can still use Slack draft preview posts and edits.

Slack 专属：

- `channels.slack.streaming.mode="partial"` 时，`channels.slack.streaming.nativeTransport` 切换 Slack 原生流式 API 调用（默认 `true`）。
- Slack 原生流式和 Slack assistant thread 状态需要一个 reply thread 目标。顶层 DM 没有 thread 风格的预览，但仍能用 Slack 草稿预览消息和编辑。

> Legacy key migration:
>
> * Telegram: legacy `streamMode` and scalar/boolean `streaming` values are detected and migrated by doctor/config compatibility paths to `streaming.mode`.
> * Discord: `streamMode` + boolean `streaming` remain runtime aliases for the `streaming` enum; run `openclaw doctor --fix` to rewrite persisted config.
> * Slack: `streamMode` remains a runtime alias for `streaming.mode`; boolean `streaming` remains a runtime alias for `streaming.mode` plus `streaming.nativeTransport`; legacy `nativeStreaming` remains a runtime alias for `streaming.nativeTransport`. Run `openclaw doctor --fix` to rewrite persisted config.

旧 key 迁移：

- Telegram：doctor / 配置兼容路径能识别旧的 `streamMode` 和标量 / 布尔 `streaming` 值，并迁到 `streaming.mode`。
- Discord：`streamMode` + 布尔 `streaming` 仍作 `streaming` 枚举的运行时别名；跑 `openclaw doctor --fix` 改写持久化配置。
- Slack：`streamMode` 仍是 `streaming.mode` 的运行时别名；布尔 `streaming` 仍是 `streaming.mode` 加 `streaming.nativeTransport` 的运行时别名；旧 `nativeStreaming` 仍是 `streaming.nativeTransport` 的运行时别名。跑 `openclaw doctor --fix` 改写持久化配置。

> ### Runtime behavior

### 运行时行为

> Telegram:
>
> * Uses `sendMessage` + `editMessageText` preview updates across DMs and group/topics.
> * Final text edits the active preview in place; long finals reuse that message for the first chunk and send only the remaining chunks.
> * `progress` mode keeps tool progress in an editable status draft, clears that draft at completion, and sends the final answer through normal delivery.
> * If the final edit fails before the completed text is confirmed, OpenClaw uses normal final delivery and cleans up the stale preview.
> * Preview streaming is skipped when Telegram block streaming is explicitly enabled (to avoid double-streaming).
> * `/reasoning stream` can write reasoning to a transient preview that is deleted after final delivery.

Telegram：

- 在 DM 和群 / topic 上用 `sendMessage` + `editMessageText` 更新预览。
- 最终文本原地编辑当前预览消息；文本过长时，复用这条消息装第一段，多出来的另发。
- `progress` 模式把工具进度放进一个可编辑的状态草稿，完成时清掉草稿，最终答案走正常投递。
- 最终编辑在文本确认前失败时，OpenClaw 走正常最终投递并清理过期预览。
- Telegram 块流式显式开启时，预览流式跳过（避免双流）。
- `/reasoning stream` 可以把推理写到临时预览里，最终投递后删除。

> Discord:
>
> * Uses send + edit preview messages.
> * `block` mode uses draft chunking (`draftChunk`).
> * Preview streaming is skipped when Discord block streaming is explicitly enabled.
> * Final media, error, and explicit-reply payloads cancel pending previews without flushing a new draft, then use normal delivery.

Discord：

- 用发送 + 编辑预览消息。
- `block` 模式用草稿分片（`draftChunk`）。
- Discord 块流式显式开启时跳过预览流式。
- 最终的媒体、错误、显式 reply payload 取消挂起预览（不再推出新草稿），走正常投递。

> Slack:
>
> * `partial` can use Slack native streaming (`chat.startStream`/`append`/`stop`) when available.
> * `block` uses append-style draft previews.
> * `progress` uses status preview text, then final answer.
> * Top-level DMs without a reply thread use draft preview posts and edits instead of Slack native streaming.
> * Native and draft preview streaming suppress block replies for that turn, so a Slack reply is streamed by one delivery path only.
> * Final media/error payloads and progress finals do not create throwaway draft messages; only text/block finals that can edit the preview flush pending draft text.

Slack：

- `partial` 在可用时用 Slack 原生流式（`chat.startStream` / `append` / `stop`）。
- `block` 用追加风格的草稿预览。
- `progress` 用状态预览文本，最后给最终答案。
- 没有 reply thread 的顶层 DM 用草稿预览消息和 edit，而不是 Slack 原生流式。
- 这一轮如果走了原生流式或草稿预览流式，块回复就会被抑制——每条 Slack 回复只走一条投递路径。
- 最终的媒体/错误载荷和 progress 最终消息不会创建临时草稿；只有文本/块类型的最终消息（能编辑预览的那种）才会推出挂起的草稿文本。

> Mattermost:
>
> * Streams thinking, tool activity, and partial reply text into a single draft preview post that finalizes in place when the final answer is safe to send.
> * Falls back to sending a fresh final post if the preview post was deleted or is otherwise unavailable at finalize time.
> * Final media/error payloads cancel pending preview updates before normal delivery instead of flushing a temporary preview post.

Mattermost：

- 把思考、工具活动、部分回复文本流到一条草稿预览消息里；最终答案能安全发送时原地收尾。
- 收尾时如果预览消息已删或不可用，回退到发一条新的最终消息。
- 最终媒体 / 错误 payload 在正常投递前取消挂起预览更新，不再推出临时预览消息。

> Matrix:
>
> * Draft previews finalize in place when the final text can reuse the preview event.
> * Media-only, error, and reply-target-mismatch finals cancel pending preview updates before normal delivery; an already-visible stale preview is redacted.

Matrix：

- 最终文本能复用预览 event 时，草稿预览原地收尾。
- 仅媒体、错误、reply 目标不匹配的最终消息在正常投递前会取消挂起预览更新；已经可见的过期预览会被抹除。

> ### Tool-progress preview updates

### 工具进度预览更新

> Preview streaming can also include **tool-progress** updates - short status lines like "searching the web", "reading file", or "calling tool" - that appear in the same preview message while tools are running, ahead of the final reply. In Codex app-server mode, Codex preamble/commentary messages use this same preview path, so short "I am checking..." progress notes can stream into the editable draft without becoming part of the final answer. This keeps multi-step tool turns visually alive rather than silent between the first thinking preview and the final answer.

预览流式还可以包含**工具进度**更新——像"searching the web"、"reading file"、"calling tool"这种短状态行——工具运行期间出现在同一条预览消息里，先于最终回复。在 Codex app-server 模式下，Codex preamble/注释消息走同一条预览路径，"I am checking..."这种简短进度备注会流进可编辑草稿，但不会成为最终答案的一部分。这让多步工具轮次始终有视觉反馈，不会在第一次思考预览和最终答案之间陷入沉默。

> Long-running tools may emit typed progress before they return. For example, `web_fetch` arms a five-second timer when it starts: if the fetch is still pending, the preview can show `Fetching page content...`; if the fetch finishes or is canceled before then, no progress line is emitted. The later final tool result is still delivered normally to the model.

耗时较长的工具可能在返回之前就发出带类型的进度信息。比如 `web_fetch` 启动时会设一个五秒计时器：如果请求还没完成，预览可以显示 `Fetching page content...`；如果请求在五秒内完成或被取消，就不发进度行。后续的最终工具结果仍正常交给模型。

> Supported surfaces:
>
> * **Discord**, **Slack**, **Telegram**, and **Matrix** stream tool-progress and Codex preamble updates into the live preview edit by default when preview streaming is active. Microsoft Teams uses its native progress stream in personal chats.
> * Telegram has shipped with tool-progress preview updates enabled since `v2026.4.22`; keeping them enabled preserves that released behavior.
> * **Mattermost** already folds tool activity into its single draft preview post (see above).
> * Tool-progress edits follow the active preview streaming mode; they are skipped when preview streaming is `off` or when block streaming has taken over the message. On Telegram, `streaming.mode: "off"` is final-only: generic progress chatter is also suppressed instead of being delivered as standalone status messages, while approval prompts, media payloads, and errors still route normally.
> * To keep preview streaming but hide tool-progress lines, set `streaming.preview.toolProgress` to `false` for that channel. To keep tool-progress lines visible while hiding command/exec text, set `streaming.preview.commandText` to `"status"` or `streaming.progress.commandText` to `"status"`; the default is `"raw"` to preserve released behavior. This policy is shared by draft/progress channels that use OpenClaw's compact progress renderer, including Discord, Matrix, Microsoft Teams, Mattermost, Slack draft previews, and Telegram. To disable preview edits entirely, set `streaming.mode` to `off`.
> * Telegram selected quote replies are an exception: when `replyToMode` is not `"off"` and selected quote text is present, OpenClaw skips the answer preview stream for that turn so tool-progress preview lines cannot render. Current-message replies without selected quote text still keep preview streaming. See [Telegram channel docs](/channels/telegram) for details.

支持的平台：

- **Discord**、**Slack**、**Telegram**、**Matrix** 在预览流式开启时默认把工具进度和 Codex preamble 更新流到实时预览编辑里。Microsoft Teams 在个人聊天里用它的原生 progress 流。
- Telegram 自 `v2026.4.22` 起默认带工具进度预览更新；保持开启就是保留发布行为。
- **Mattermost** 已经把工具活动折进它的单一草稿预览消息（见上面）。
- 工具进度编辑跟随当前预览流式模式；预览流式是 `off` 或块流式已接管该消息时，工具进度就不发了。Telegram 上 `streaming.mode: "off"` 表示"只发最终"：通用进度信息也会被压住，不会作为独立状态消息投递；但批准提示、媒体载荷、错误仍正常路由。
- 要保留预览流式但隐藏工具进度行，把通道的 `streaming.preview.toolProgress` 设成 `false`。要保留工具进度行但隐藏命令/exec 文本，把 `streaming.preview.commandText` 设成 `"status"`，或 `streaming.progress.commandText` 设成 `"status"`；默认 `"raw"`，保留发布行为。这条策略适用于所有使用 OpenClaw 紧凑进度渲染器的通道，包括 Discord、Matrix、Microsoft Teams、Mattermost、Slack 草稿预览和 Telegram。要完全关闭预览编辑，把 `streaming.mode` 设成 `off`。
- Telegram selected quote 回复是例外：`replyToMode` 不是 `"off"` 且消息带 selected quote 文本时，OpenClaw 这一轮跳过答案预览流，工具进度预览行不会显示。没有 selected quote 文本的当前消息回复仍走预览流式。细节见 [Telegram 通道文档](/channels/telegram)。

> Keep progress lines visible but hide raw command/exec text:
>
> ```json
> {
>   "channels": {
>     "telegram": {
>       "streaming": {
>         "mode": "partial",
>         "preview": {
>           "toolProgress": true,
>           "commandText": "status"
>         }
>       }
>     }
>   }
> }
> ```

保留进度行但隐藏原始命令 / exec 文本：

```json
{
  "channels": {
    "telegram": {
      "streaming": {
        "mode": "partial",
        "preview": {
          "toolProgress": true,
          "commandText": "status"
        }
      }
    }
  }
}
```

> Use the same shape under another compact progress channel key, for example `channels.discord`, `channels.matrix`, `channels.msteams`, `channels.mattermost`, or Slack draft previews. For progress-draft mode, put the same policy under `streaming.progress`:

在其他紧凑进度通道 key 下用同样形状，如 `channels.discord`、`channels.matrix`、`channels.msteams`、`channels.mattermost` 或 Slack 草稿预览。`progress-draft` 模式下把同样策略放在 `streaming.progress` 下：

> ```json
> {
>   "channels": {
>     "telegram": {
>       "streaming": {
>         "mode": "progress",
>         "progress": {
>           "toolProgress": true,
>           "commandText": "status"
>         }
>       }
>     }
>   }
> }
> ```

```json
{
  "channels": {
    "telegram": {
      "streaming": {
        "mode": "progress",
        "progress": {
          "toolProgress": true,
          "commandText": "status"
        }
      }
    }
  }
}
```

---

> ## Related

## 相关

> * [Message lifecycle refactor](/concepts/message-lifecycle-refactor) - target shared preview, edit, stream, and finalization design
> * [Progress drafts](/concepts/progress-drafts) - visible work-in-progress messages that update during long turns
> * [Messages](/concepts/messages) - message lifecycle and delivery
> * [Retry](/concepts/retry) - retry behavior on delivery failure
> * [Channels](/channels) - per-channel streaming support

- [消息生命周期重构](/concepts/message-lifecycle-refactor)：目标共享预览、编辑、流式、收尾设计
- [进度草稿](/concepts/progress-drafts)：长轮次期间可见的、会更新的"工作中"消息
- [消息](/concepts/messages)：消息生命周期和投递
- [重试](/concepts/retry)：投递失败时的重试行为
- [通道](/channels)：按通道的流式支持
