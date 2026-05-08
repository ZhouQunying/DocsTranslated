# WhatsApp

> Status: production-ready via WhatsApp Web (Baileys). Gateway owns linked session(s).

状态：通过 WhatsApp Web（Baileys）已生产就绪。Gateway 拥有已链接会话的控制权。

---

> ## Install (on demand)

## 安装（按需）

> - Onboarding (`openclaw onboard`) and `openclaw channels add --channel whatsapp` prompt to install the WhatsApp plugin the first time you select it.
> - `openclaw channels login --channel whatsapp` also offers the install flow when the plugin is not present yet.
> - Dev channel + git checkout: defaults to the local plugin path.
> - Stable/Beta: uses the npm package `@openclaw/whatsapp` on the current official release tag.

- 初始化引导（`openclaw onboard`）和 `openclaw channels add --channel whatsapp` 会在你首次选择 WhatsApp 时提示安装插件。
- 当插件尚未安装时，`openclaw channels login --channel whatsapp` 也会引导安装流程。
- 开发频道 + git checkout：默认使用本地插件路径。
- Stable/Beta 版本：使用当前官方发布标签对应的 npm 包 `@openclaw/whatsapp`。

> Manual install stays available:
>
> ```bash
> openclaw plugins install @openclaw/whatsapp
> ```

手动安装方式始终可用：

```bash
openclaw plugins install @openclaw/whatsapp
```

> Use the bare package to follow the current official release tag. Pin an exact version only when you need a reproducible install.

使用裸包名会跟随当前官方发布标签。仅在需要可复现安装时才锁定具体版本。

> On Windows, the WhatsApp plugin needs Git on `PATH` during npm install because one of its Baileys/libsignal dependencies is fetched from a git URL. Install Git for Windows, then restart the shell and rerun the install. Portable Git also works if its `bin` directory is on `PATH`.

在 Windows 上，WhatsApp 插件在 npm 安装时需要 Git 在 `PATH` 中，因为其 Baileys/libsignal 依赖之一是从 git URL 拉取的。先安装 Git for Windows，再重启 Shell 后重新运行安装。Portable Git 也可以，只要它的 `bin` 目录在 `PATH` 中。

---

> ### Configure WhatsApp access policy

### 配置 WhatsApp 访问策略

> ```json5
> {
>   channels: {
>     whatsapp: {
>       dmPolicy: "pairing",
>       allowFrom: ["+15551234567"],
>       groupPolicy: "allowlist",
>       groupAllowFrom: ["+15551234567"],
>     },
>   },
> }
> ```

（配置代码保持不变）

> ### Link WhatsApp (QR)

### 链接 WhatsApp（扫码）

> ```bash
> openclaw channels login --channel whatsapp
> ```
>
> For a specific account:
>
> ```bash
> openclaw channels login --channel whatsapp --account work
> ```
>
> To attach an existing/custom WhatsApp Web auth directory before login:
>
> ```bash
> openclaw channels add --channel whatsapp --account work --auth-dir /path/to/wa-auth
> openclaw channels login --channel whatsapp --account work
> ```

```bash
openclaw channels login --channel whatsapp
```

指定账号：

```bash
openclaw channels login --channel whatsapp --account work
```

登录前绑定已有的/自定义 WhatsApp Web 认证目录：

```bash
openclaw channels add --channel whatsapp --account work --auth-dir /path/to/wa-auth
openclaw channels login --channel whatsapp --account work
```

> ### Start the gateway

### 启动 Gateway

> ```bash
> openclaw gateway
> ```

```bash
openclaw gateway
```

> ### Approve first pairing request (if using pairing mode)
>
> ```bash
> openclaw pairing list whatsapp
> openclaw pairing approve whatsapp <CODE>
> ```
>
> Pairing requests expire after 1 hour. Pending requests are capped at 3 per channel.

### 批准首次配对请求（如果使用配对模式）

```bash
openclaw pairing list whatsapp
openclaw pairing approve whatsapp <CODE>
```

配对请求 1 小时后过期。每个频道最多等待 3 个请求。

> OpenClaw recommends running WhatsApp on a separate number when possible. (The channel metadata and setup flow are optimized for that setup, but personal-number setups are also supported.)

OpenClaw 建议尽可能使用独立号码运行 WhatsApp。（频道元数据和设置流程针对此场景优化，但也支持个人号码设置。）

---

> ## [展开] Deployment patterns / 部署模式

## [展开] Deployment patterns / 部署模式

> ### Dedicated number (recommended)
>
> This is the cleanest operational mode:
> - separate WhatsApp identity for OpenClaw
> - clearer DM allowlists and routing boundaries
> - lower chance of self-chat confusion
>
> Minimal policy pattern:
> ```json5
> { channels: { whatsapp: { dmPolicy: "allowlist", allowFrom: ["+15551234567"] } } }
> ```

### 独立号码（推荐）

这是最干净的运行模式：
- OpenClaw 拥有独立的 WhatsApp 身份
- 更清晰的私聊白名单和路由边界
- 降低自我对话混淆的概率

最小策略配置：
```json5
{ channels: { whatsapp: { dmPolicy: "allowlist", allowFrom: ["+15551234567"] } } }
```

> ### Personal-number fallback
>
> Onboarding supports personal-number mode and writes a self-chat-friendly baseline:
> - `dmPolicy: "allowlist"`
> - `allowFrom` includes your personal number
> - `selfChatMode: true`
>
> In runtime, self-chat protections key off the linked self number and `allowFrom`.

### 个人号码备选

初始化引导支持个人号码模式，并写入对自我对话友好的基础配置：
- `dmPolicy: "allowlist"`
- `allowFrom` 包含你的个人号码
- `selfChatMode: true`

运行时，自我对话保护基于已链接的自身号码和 `allowFrom` 生效。

> ### WhatsApp Web-only channel scope
>
> The messaging platform channel is WhatsApp Web-based (`Baileys`) in current OpenClaw channel architecture. There is no separate Twilio WhatsApp messaging channel in the built-in chat-channel registry.

### 仅限 WhatsApp Web 的频道范围

当前 OpenClaw 频道架构中，消息平台频道基于 WhatsApp Web（`Baileys`）。内置聊天频道注册表中没有独立的 Twilio WhatsApp 消息频道。

---

> ## Runtime model / 运行时模型

## Runtime model / 运行时模型

> Gateway owns the WhatsApp socket and reconnect loop.

Gateway 拥有 WhatsApp 套接字和重连循环的控制权。

> The reconnect watchdog uses WhatsApp Web transport activity, not only inbound app-message volume, so a quiet linked-device session is not restarted solely because nobody has sent a message recently. A longer application-silence cap still forces a reconnect if transport frames keep arriving but no application messages are handled for the watchdog window; after a transient reconnect for a recently active session, that application-silence check uses the normal message timeout for the first recovery window.

重连看门狗基于 WhatsApp Web 传输活动（而非仅入站应用消息量）来判断，因此不会因为近期没人发消息就重启安静的已链接设备会话。如果传输帧持续到达但窗口期内没有应用消息被处理，较长的应用静默上限仍会强制重连；在对近期活跃会话的短暂重连后，该静默检查使用正常消息超时作为首个恢复窗口。

> Baileys socket timings are explicit under `web.whatsapp.*`: `keepAliveIntervalMs` controls WhatsApp Web application pings, `connectTimeoutMs` controls the opening handshake timeout, and `defaultQueryTimeoutMs` controls Baileys query timeouts.

Baileys 套接字计时参数在 `web.whatsapp.*` 下显式配置：`keepAliveIntervalMs` 控制应用心跳，`connectTimeoutMs` 控制握手超时，`defaultQueryTimeoutMs` 控制 Baileys 查询超时。

> Outbound sends require an active WhatsApp listener for the target account.

出站发送需要目标账号有活跃的 WhatsApp 监听器。

> Group sends attach native mention metadata for `@+<digits>` and `@<digits>` tokens in text and media captions when the token matches current WhatsApp participant metadata, including LID-backed groups.

群组发送时，当文本和媒体说明中的 `@+<数字>` 和 `@<数字>` 标记匹配当前 WhatsApp 参与者元数据（包括基于 LID 的群组）时，会附加原生 @提及 元数据。

> Status and broadcast chats are ignored (`@status`, `@broadcast`).

状态和广播聊天会被忽略（`@status`、`@broadcast`）。

> The reconnect watchdog follows WhatsApp Web transport activity, not only inbound app-message volume: quiet linked-device sessions stay up while transport frames continue, but a transport stall forces reconnect well before the later remote disconnect path.

重连看门狗跟踪传输活动（而非仅消息量）：只要传输帧持续到达，安静的会话就保持在线；但传输停滞会在远端断开之前强制重连。

> Direct chats use DM session rules (`session.dmScope`; default `main` collapses DMs to the agent main session).

私聊使用 DM 会话规则（`session.dmScope`；默认 `main` 将所有私聊合并到 agent 主会话）。

> Group sessions are isolated (`agent:<agentId>:whatsapp:group:<jid>`).

群组会话相互隔离（`agent:<agentId>:whatsapp:group:<jid>`）。

> WhatsApp Channels/Newsletters can be explicit outbound targets with their native `@newsletter` JID. Outbound newsletter sends use channel session metadata (`agent:<agentId>:whatsapp:channel:<jid>`) rather than DM session semantics.

WhatsApp 频道/通讯可以使用原生 `@newsletter` JID 作为明确的出站目标。出站通讯发送使用频道会话元数据而非私聊会话语义。

> WhatsApp Web transport honors standard proxy environment variables on the gateway host (`HTTPS_PROXY`, `HTTP_PROXY`, `NO_PROXY` / lowercase variants). Prefer host-level proxy config over channel-specific WhatsApp proxy settings.

WhatsApp Web 传输遵循 Gateway 主机上的标准代理环境变量（`HTTPS_PROXY`、`HTTP_PROXY`、`NO_PROXY` 或其小写变体）。优先使用主机级代理配置而非频道特定的 WhatsApp 代理设置。

> When `messages.removeAckAfterReply` is enabled, OpenClaw clears the WhatsApp ack reaction after a visible reply is delivered.

启用 `messages.removeAckAfterReply` 后，OpenClaw 在可见回复送达后清除 WhatsApp 的确认反应（ack reaction）。

---

> ## Plugin hooks and privacy / 插件钩子与隐私

## Plugin hooks and privacy / 插件钩子与隐私

> WhatsApp inbound messages can contain personal message content, phone numbers, group identifiers, sender names, and session correlation fields. For that reason, WhatsApp does not broadcast inbound `message_received` hook payloads to plugins unless you explicitly opt in.

WhatsApp 入站消息可能包含个人消息内容、电话号码、群组标识、发送者名称和会话关联字段。因此，除非你明确启用，WhatsApp 不会向插件广播入站 `message_received` 钩子载荷。

> You can scope the opt-in to one account.

你可以将启用范围限定到单个账号。

> Only enable this for plugins you trust to receive inbound WhatsApp message content and identifiers.

仅对你信任能接收 WhatsApp 入站消息内容和标识的插件启用此功能。

---

> ## [标签页] Access control and activation / 访问控制与激活

## [标签页] Access control and activation / 访问控制与激活

> ### [标签页: DM policy] 私聊策略
>
> `channels.whatsapp.dmPolicy` controls direct chat access:
> - `pairing` (default)
> - `allowlist`
> - `open` (requires `allowFrom` to include `"*"`)
> - `disabled`
>
> `allowFrom` accepts E.164-style numbers (normalized internally).
>
> `allowFrom` is a DM sender access-control list. It does not gate explicit outbound sends to WhatsApp group JIDs or `@newsletter` channel JIDs.
>
> Multi-account override: `channels.whatsapp.accounts.<id>.dmPolicy` (and `allowFrom`) take precedence over channel-level defaults for that account.
>
> Runtime behavior details:
> - pairings are persisted in channel allow-store and merged with configured `allowFrom`
> - scheduled automation and heartbeat recipient fallback use explicit delivery targets or configured `allowFrom`; DM pairing approvals are not implicit cron or heartbeat recipients
> - if no allowlist is configured, the linked self number is allowed by default
> - OpenClaw never auto-pairs outbound `fromMe` DMs (messages you send to yourself from the linked device)

### [标签页: DM policy] 私聊策略

`channels.whatsapp.dmPolicy` 控制私聊访问：
- `pairing`（默认，配对模式）
- `allowlist`（白名单）
- `open`（开放，需要 `allowFrom` 包含 `"*"`）
- `disabled`（禁用）

`allowFrom` 接受 E.164 格式的号码（内部自动规范化）。

`allowFrom` 是私聊发送者访问控制列表。它不限制向 WhatsApp 群组 JID 或 `@newsletter` 频道 JID 的明确出站发送。

多账号覆盖：`channels.whatsapp.accounts.<id>.dmPolicy`（和 `allowFrom`）优先于频道级默认值。

运行时行为细节：
- 配对持久化在频道 allow-store 中并与配置的 `allowFrom` 合并
- 定时自动化和心跳接收者回退使用明确的投递目标或配置的 `allowFrom`；私聊配对批准不会隐式成为定时任务或心跳接收者
- 如果未配置白名单，默认允许已链接的自身号码
- OpenClaw 永远不会自动配对出站 `fromMe` 私聊（你从已链接设备发给自己的消息）

> ### [标签页: Group policy + allowlists] 群组策略与白名单
>
> Group access has two layers:
> 1. **Group membership allowlist** (`channels.whatsapp.groups`) — if `groups` is omitted, all groups are eligible; if `groups` is present, it acts as a group allowlist (`"*"` allowed).
> 2. **Group sender policy** (`channels.whatsapp.groupPolicy` + `groupAllowFrom`) — `open`: sender allowlist bypassed; `allowlist`: sender must match `groupAllowFrom` (or `*`); `disabled`: block all group inbound.
>
> Sender allowlist fallback:
> - if `groupAllowFrom` is unset, runtime falls back to `allowFrom` when available
> - sender allowlists are evaluated before mention/reply activation
>
> Note: if no `channels.whatsapp` block exists at all, runtime group-policy fallback is `allowlist` (with a warning log), even if `channels.defaults.groupPolicy` is set.

### [标签页: Group policy + allowlists] 群组策略与白名单

群组访问有两层控制：
1. **群组成员白名单** — 如果省略 `groups`，所有群组都可访问；如果设置了 `groups`，它作为群组白名单（允许 `"*"`）。
2. **群组发送者策略** — `open`：绕过发送者白名单；`allowlist`：发送者必须匹配 `groupAllowFrom`（或 `*`）；`disabled`：阻止所有群组入站。

发送者白名单回退：
- 如果 `groupAllowFrom` 未设置，运行时回退到 `allowFrom`
- 发送者白名单在 @提及/回复激活之前评估

注意：如果完全没有 `channels.whatsapp` 配置块，运行时群组策略回退为 `allowlist`（并产生警告日志），即使设置了 `channels.defaults.groupPolicy`。

> ### [标签页: Mentions + /activation] @提及与 / 激活
>
> Group replies require mention by default.
>
> Mention detection includes:
> - explicit WhatsApp mentions of the bot identity
> - configured mention regex patterns (`agents.list[].groupChat.mentionPatterns`, fallback `messages.groupChat.mentionPatterns`)
> - inbound voice-note transcripts for authorized group messages
> - implicit reply-to-bot detection (reply sender matches bot identity)
>
> Activation syntax in groups: `/` prefix triggers the agent.

### [标签页: Mentions + /activation] @提及与 / 激活

默认情况下，群组回复需要被 @提及。

@提及检测包括：
- 明确的 WhatsApp @提及机器人身份
- 配置的 @提及正则表达式模式（`agents.list[].groupChat.mentionPatterns`，回退到 `messages.groupChat.mentionPatterns`）
- 已授权群组消息的入站语音笔记转录
- 隐式回复机器人检测（回复发送者匹配机器人身份）

群组中的激活语法：`/` 前缀触发 agent。

---

> ## [展开] Message format and media / 消息格式与媒体

## [展开] Message format and media / 消息格式与媒体

> Outbound messages convert Markdown to WhatsApp formatting. WhatsApp supports bold, italic, strikethrough, monospace, and inline code. Lists, tables, and headings are converted to plain text.

出站消息将 Markdown 转换为 WhatsApp 格式。WhatsApp 支持粗体、斜体、删除线、等宽字体和行内代码。列表、表格和标题转换为纯文本。

> Media limits:
> - inbound media save cap: `channels.whatsapp.mediaMaxMb` (default `50`)
> - outbound media send cap: `channels.whatsapp.mediaMaxMb` (default `50`)
> - per-account overrides use `channels.whatsapp.accounts.<accountId>.mediaMaxMb`
> - images are auto-optimized (resize/quality sweep) to fit limits
> - on media send failure, first-item fallback sends text warning instead of dropping the response silently

媒体限制：
- 入站媒体保存上限：`channels.whatsapp.mediaMaxMb`（默认 50MB）
- 出站媒体发送上限：`channels.whatsapp.mediaMaxMb`（默认 50MB）
- 每个账号的覆盖使用 `channels.whatsapp.accounts.<accountId>.mediaMaxMb`
- 图片会自动优化（调整大小/质量扫描）以适应限制
- 媒体发送失败时，第一条回退消息会发送文本警告，而不是静默丢弃回复

---

> ## [展开] Message streaming and chunking / 消息流式传输与分块

## [展开] Message streaming and chunking / 消息流式传输与分块

> WhatsApp does not support native streaming. OpenClaw chunks agent replies into sequential messages. Chunk boundaries are at sentence breaks when possible. Chunk size and interval are configurable. A trailing chunk is sent when the stream ends if it has content.

WhatsApp 不支持原生流式传输。OpenClaw 将 agent 回复分块为顺序消息。分块边界尽可能落在句子断点处。分块大小和间隔可配置。流结束时如果有内容会发送尾部分块。

---

> ## [展开] Typing indicators / 输入指示器

## [展开] Typing indicators / 输入指示器

> `channels.whatsapp.typingIndicator` controls whether the agent shows a typing indicator before replying.

`channels.whatsapp.typingIndicator` 控制 agent 回复前是否显示输入中指示器。

> | Value | Behavior |
> |---|---|
> | `"off"` | No typing indicator |
> | `"auto"` | Show during generation, hide before sending |
> | `"always"` | Show continuously until the reply is fully sent |
>
> Default: `"auto"`.

| 值 | 行为 |
|---|---|
| `"off"` | 不显示输入指示器 |
| `"auto"` | 生成期间显示，发送前隐藏 |
| `"always"` | 持续显示直到回复完全发送 |

默认：`"auto"`。

---

> ## Reply quoting / 回复引用

## Reply quoting / 回复引用

> WhatsApp supports native reply quoting, where outbound replies visibly quote the inbound message. Control it with `channels.whatsapp.replyToMode`.

WhatsApp 支持原生回复引用，出站回复会 visibly 引用入站消息。通过 `channels.whatsapp.replyToMode` 控制。

> | Value | Behavior |
> |---|---|
> | `"off"` | Never quote; send as a plain message |
> | `"first"` | Quote only the first outbound reply chunk |
> | `"all"` | Quote every outbound reply chunk |
> | `"batched"` | Quote queued batched replies while leaving immediate replies unquoted |
>
> Default is `"off"`. Per-account overrides use `channels.whatsapp.accounts.<id>.replyToMode`.

| 值 | 行为 |
|---|---|
| `"off"` | 从不引用，作为普通消息发送 |
| `"first"` | 仅引用第一个出站回复分块 |
| `"all"` | 引用每个出站回复分块 |
| `"batched"` | 引用排队的批量回复，即时回复不被引用 |

默认 `"off"`。每个账号的覆盖使用 `channels.whatsapp.accounts.<id>.replyToMode`。

---

> ## Reaction level / 反应级别

## Reaction level / 反应级别

> `channels.whatsapp.reactionLevel` controls how broadly the agent uses emoji reactions on WhatsApp.

`channels.whatsapp.reactionLevel` 控制 agent 在 WhatsApp 上使用 emoji 反应的广泛程度。

> | Level | Ack reactions | Agent-initiated reactions | Description |
> |---|---|---|---|
> | `"off"` | No | No | No reactions at all |
> | `"ack"` | Yes | No | Ack reactions only (pre-reply receipt) |
> | `"minimal"` | Yes | Yes (conservative) | Ack + agent reactions with conservative guidance |
> | `"extensive"` | Yes | Yes (encouraged) | Ack + agent reactions with encouraged guidance |
>
> Default: `"minimal"`.

| 级别 | 确认反应 | Agent 主动反应 | 说明 |
|---|---|---|---|
| `"off"` | 否 | 否 | 完全不使用反应 |
| `"ack"` | 是 | 否 | 仅确认反应（回复前收据） |
| `"minimal"` | 是 | 是（保守） | 确认 + agent 反应，保守引导 |
| `"extensive"` | 是 | 是（鼓励） | 确认 + agent 反应，鼓励引导 |

默认：`"minimal"`。

---

> ## Acknowledgment reactions / 确认反应

## Acknowledgment reactions / 确认反应

> WhatsApp supports immediate ack reactions on inbound receipt via `channels.whatsapp.ackReaction`. Ack reactions are gated by `reactionLevel` — they are suppressed when `reactionLevel` is `"off"`.

WhatsApp 支持通过 `channels.whatsapp.ackReaction` 在入站接收时立即发送确认反应。确认反应受 `reactionLevel` 限制 — 当 `reactionLevel` 为 `"off"` 时被抑制。

> Behavior notes:
> - sent immediately after inbound is accepted (pre-reply)
> - failures are logged but do not block normal reply delivery
> - group mode `mentions` reacts on mention-triggered turns; group activation `always` acts as bypass for this check
> - WhatsApp uses `channels.whatsapp.ackReaction` (legacy `messages.ackReaction` is not used here)

行为说明：
- 入站接受后立即发送（回复前）
- 失败会记录日志但不阻塞正常回复发送
- 群组模式 `mentions` 在 @提及触发的回合中反应；群组激活 `always` 作为此检查的绕过
- WhatsApp 使用 `channels.whatsapp.ackReaction`（旧版 `messages.ackReaction` 在此不使用）

---

> ## [展开] Multi-account and credentials / 多账号与凭证

## [展开] Multi-account and credentials / 多账号与凭证

> ### Account selection and defaults
>
> Account ids come from `channels.whatsapp.accounts`. Default account selection: `default` if present, otherwise first configured account id (sorted). Account ids are normalized internally for lookup.

### 账号选择与默认

账号 ID 来自 `channels.whatsapp.accounts`。默认账号选择：如果存在 `default` 则使用，否则使用第一个配置的账号 ID（排序后）。账号 ID 在内部规范化用于查找。

> ### Credential paths and legacy compatibility
>
> Current auth path: `~/.openclaw/credentials/whatsapp/<accountId>/creds.json`. Backup file: `creds.json.bak`. Legacy default credentials may still be imported from older paths.

### 凭证路径与旧版兼容

当前认证路径：`~/.openclaw/credentials/whatsapp/<accountId>/creds.json`。备份文件：`creds.json.bak`。旧版默认凭证仍可能从旧路径导入。

---

> ## [展开] Message streaming and chunking / 消息流式传输与分块

## [展开] Message streaming and chunking / 消息流式传输与分块

> WhatsApp does not support native streaming. OpenClaw chunks agent replies into sequential messages. Chunk boundaries are at sentence breaks when possible. Chunk size and interval are configurable. A trailing chunk is sent when the stream ends if it has content.

WhatsApp 不支持原生流式传输。OpenClaw 将 agent 回复分块为顺序消息。分块边界尽可能落在句子断点处。分块大小和间隔可配置。流结束时如果有内容会发送尾部分块。

> `channels.whatsapp.chunkChars` — outbound text chunk size in characters. `channels.whatsapp.chunkIntervalMs` — time interval between chunks in milliseconds.

`channels.whatsapp.chunkChars` — 出站文本分块大小（字符数）。`channels.whatsapp.chunkIntervalMs` — 分块间隔时间（毫秒）。

---

> ## [展开] Typing indicators / 输入指示器

## [展开] Typing indicators / 输入指示器

> `channels.whatsapp.typingIndicator` controls whether the agent shows a typing indicator before replying.

`channels.whatsapp.typingIndicator` 控制 agent 回复前是否显示输入中指示器。

> | Value | Behavior |
> |---|---|
> | `"off"` | No typing indicator |
> | `"auto"` | Show during generation, hide before sending |
> | `"always"` | Show continuously until the reply is fully sent |
>
> Default: `"auto"`.

| 值 | 行为 |
|---|---|
| `"off"` | 不显示输入指示器 |
| `"auto"` | 生成期间显示，发送前隐藏 |
| `"always"` | 持续显示直到回复完全发送 |

默认：`"auto"`。

---

> ## [展开] Reaction level / 反应级别

## [展开] Reaction level / 反应级别

> `channels.whatsapp.reactionLevel` controls how broadly the agent uses emoji reactions on WhatsApp.

`channels.whatsapp.reactionLevel` 控制 agent 在 WhatsApp 上使用 emoji 反应的广泛程度。

> | Level | Ack reactions | Agent-initiated reactions | Description |
> |---|---|---|---|
> | `"off"` | No | No | No reactions at all |
> | `"ack"` | Yes | No | Ack reactions only (pre-reply receipt) |
> | `"minimal"` | Yes | Yes (conservative) | Ack + agent reactions with conservative guidance |
> | `"extensive"` | Yes | Yes (encouraged) | Ack + agent reactions with encouraged guidance |
>
> Default: `"minimal"`. Per-account overrides use `channels.whatsapp.accounts.<id>.reactionLevel`.

| 级别 | 确认反应 | Agent 主动反应 | 说明 |
|---|---|---|---|
| `"off"` | 否 | 否 | 完全不使用反应 |
| `"ack"` | 是 | 否 | 仅确认反应（回复前收据） |
| `"minimal"` | 是 | 是（保守） | 确认 + agent 反应，保守引导 |
| `"extensive"` | 是 | 是（鼓励） | 确认 + agent 反应，鼓励引导 |

默认：`"minimal"`。每个账号的覆盖使用 `channels.whatsapp.accounts.<id>.reactionLevel`。

---

> ## [展开] Acknowledgment reactions / 确认反应

## [展开] Acknowledgment reactions / 确认反应

> WhatsApp supports immediate ack reactions on inbound receipt via `channels.whatsapp.ackReaction`. Ack reactions are gated by `reactionLevel` — they are suppressed when `reactionLevel` is `"off"`.

WhatsApp 支持通过 `channels.whatsapp.ackReaction` 在入站接收时立即发送确认反应。确认反应受 `reactionLevel` 限制 — 当 `reactionLevel` 为 `"off"` 时被抑制。

> ```json5
> {
>   channels: {
>     whatsapp: {
>       ackReaction: {
>         emoji: "👀",
>         direct: true,
>         group: "mentions",
>       },
>     },
>   },
> }
> ```
>
> Behavior notes:
> - sent immediately after inbound is accepted (pre-reply)
> - failures are logged but do not block normal reply delivery
> - group mode `mentions` reacts on mention-triggered turns; group activation `always` acts as bypass for this check
> - WhatsApp uses `channels.whatsapp.ackReaction` (legacy `messages.ackReaction` is not used here)

```json5
{
  channels: {
    whatsapp: {
      ackReaction: {
        emoji: "👀",
        direct: true,
        group: "mentions", // always | mentions | never
      },
    },
  },
}
```

行为说明：
- 入站接受后立即发送（回复前）
- 失败会记录日志但不阻塞正常回复发送
- 群组模式 `mentions` 在 @提及触发的回合中反应；群组激活 `always` 作为此检查的绕过
- WhatsApp 使用 `channels.whatsapp.ackReaction`（旧版 `messages.ackReaction` 在此不使用）

---

> ## [展开] Multi-account and credentials / 多账号与凭证

## [展开] Multi-account and credentials / 多账号与凭证

> ### Account selection and defaults
> - account ids come from `channels.whatsapp.accounts`
> - default account selection: `default` if present, otherwise first configured account id (sorted)
> - account ids are normalized internally for lookup

### 账号选择与默认

- 账号 ID 来自 `channels.whatsapp.accounts`
- 默认账号选择：如果存在 `default` 则使用，否则使用第一个配置的账号 ID（排序后）
- 账号 ID 在内部规范化用于查找

> ### Credential paths and legacy compatibility
> - current auth path: `~/.openclaw/credentials/whatsapp/<accountId>/creds.json`
> - backup file: `creds.json.bak`
> - legacy default credentials stored in `~/.openclaw/credentials/whatsapp/creds.json` (no account id segment)
> - if both exist, the account-scoped file wins

### 凭证路径与旧版兼容

- 当前认证路径：`~/.openclaw/credentials/whatsapp/<accountId>/creds.json`
- 备份文件：`creds.json.bak`
- 旧版默认凭证存储在 `~/.openclaw/credentials/whatsapp/creds.json`（无账号 ID 分段）
- 如果两者都存在，以账号级别的文件为准

---

> ## [展开] Troubleshooting / 故障排除

## [展开] Troubleshooting / 故障排除

> ### WhatsApp Web connection lost
> If WhatsApp disconnects with "logged in elsewhere", you need to re-scan the QR code.
> Run `openclaw channels login --channel whatsapp` to restart the QR flow.
> After a successful scan, the new credentials are saved.

### WhatsApp Web 连接丢失

如果 WhatsApp 提示"已在其他地方登录"，需要重新扫码。运行 `openclaw channels login --channel whatsapp` 重新扫码流程。扫码成功后，新凭证会被保存。

> ### QR code not showing in terminal
> If your terminal does not support QR code rendering, the login command falls back to printing the QR code as text.
> Scan the text QR code from your terminal or open the Control UI to see a rendered QR code.

### 终端不显示二维码

如果你的终端不支持二维码渲染，登录命令会回退为打印文本形式的二维码。可以从终端扫描文

本二维码，或在 Control UI 中查看渲染后的二维码。

> ### WhatsApp plugin not loading after install
> Confirm the plugin is enabled: `openclaw config get plugins.entries.openclaw-weixin.enabled`
> If false: `openclaw config set plugins.entries.openclaw-weixin.enabled true`
> Then restart the Gateway: `openclaw gateway restart`

### WhatsApp 插件安装后未加载

确认插件已启用：`openclaw config get plugins.entries.openclaw-weixin.enabled`
如果为 false：`openclaw config set plugins.entries.openclaw-weixin.enabled true`
然后重启 Gateway：`openclaw gateway restart`

---

> ## [展开] Configuration reference / 配置参考

## [展开] Configuration reference / 配置参考

> | Setting | Description | Default |
> |---|---|---|
> | `channels.whatsapp.dmPolicy` | Direct message policy | `"pairing"` |
> | `channels.whatsapp.allowFrom` | DM sender allowlist (phone numbers) | `[]` |
> | `channels.whatsapp.groupPolicy` | Group message policy | `"allowlist"` |
> | `channels.whatsapp.groupAllowFrom` | Group sender allowlist | `[]` |
> | `channels.whatsapp.groups` | Per-group overrides | `{}` |
> | `channels.whatsapp.chunkChars` | Outbound text chunk size | `1000` |
> | `channels.whatsapp.chunkIntervalMs` | Time between chunks | `3000` |
> | `channels.whatsapp.typingIndicator` | Show typing indicator | `"auto"` |
> | `channels.whatsapp.replyToMode` | Reply quoting mode | `"off"` |
> | `channels.whatsapp.reactionLevel` | Emoji reaction breadth | `"minimal"` |
> | `channels.whatsapp.ackReaction` | Ack reaction config | `null` |
> | `channels.whatsapp.mediaMaxMb` | Media size limit | `50` |
> | `channels.whatsapp.selfChatMode` | Enable self-chat protections | `false` |
> | `channels.whatsapp.web.*` | WebSocket timing settings | see docs |

| 设置 | 说明 | 默认值 |
|---|---|---|
| `channels.whatsapp.dmPolicy` | 私聊策略 | `"pairing"` |
| `channels.whatsapp.allowFrom` | 私聊发送者白名单（电话号码） | `[]` |
| `channels.whatsapp.groupPolicy` | 群聊策略 | `"allowlist"` |
| `channels.whatsapp.groupAllowFrom` | 群聊发送者白名单 | `[]` |
| `channels.whatsapp.groups` | 每群覆盖 | `{}` |
| `channels.whatsapp.chunkChars` | 出站文本分块大小 | `1000` |
| `channels.whatsapp.chunkIntervalMs` | 分块间隔 | `3000` |
| `channels.whatsapp.typingIndicator` | 显示输入中指示器 | `"auto"` |
| `channels.whatsapp.replyToMode` | 回复引用模式 | `"off"` |
| `channels.whatsapp.reactionLevel` | emoji 反应范围 | `"minimal"` |
| `channels.whatsapp.ackReaction` | 确认反应配置 | `null` |
| `channels.whatsapp.mediaMaxMb` | 媒体大小限制 | `50` |
| `channels.whatsapp.selfChatMode` | 启用自我对话保护 | `false` |
| `channels.whatsapp.web.*` | WebSocket 计时设置 | 见文档 |

---

> ## [展开] Tools, actions, and config writes / 工具、操作与配置写入

## [展开] Tools, actions, and config writes / 工具、操作与配置写入

> * Agent tool support includes WhatsApp reaction action (`react`).
> * Action gates:
>   * `channels.whatsapp.actions.reactions`
>   *channels.whatsapp.actions.polls`
> * Channel-initiated config writes are enabled by default (disable via `channels.whatsapp.configWrites=false`).

* Agent 工具支持包含 WhatsApp 表情反应操作（`react`）。
* 操作权限门：
  * `channels.whatsapp.actions.reactions`
  * `channels.whatsapp.actions.polls`
* 频道发起的配置写入默认启用（通过 `channels.whatsapp.configWrites=false` 禁用）。

---

> ## [展开] Troubleshooting / 故障排除（补充）

## [展开] Troubleshooting / 故障排除（补充）

> ### Not linked (QR required)
> Symptom: channel status reports not linked.
> Fix: `openclaw channels login --channel whatsapp` then `openclaw channels status`

### 未链接（需要扫码）
症状：频道状态显示未链接。
修复：运行 `openclaw channels login --channel whatsapp` 然后 `openclaw channels status`

> ### Linked but disconnected / reconnect loop
> Symptom: linked account with repeated disconnects or reconnect attempts.
> Quiet accounts can stay connected past the normal message timeout; the watchdog restarts when WhatsApp Web transport activity stops, the socket closes, or application-level activity stays silent beyond the longer safety window.
> If logs show repeated `status=408 Request Time-out Connection was lost`, tune Baileys socket timings under `web.whatsapp`.

### 已链接但断开/重连循环
症状：已链接的账号反复断开或尝试重连。
安静的账号可以超过正常消息超时保持连接；看门狗在 WhatsApp Web 传输活动停止、套接字关闭或应用级活动超过更长安全窗口保持静默时重启。
如果日志显示重复的 `status=408 Request Time-out Connection was lost`，调整 `web.whatsapp` 下的 Baileys 套接字计时。

> ### QR login times out behind a proxy
> Symptom: `openclaw channels login --channel whatsapp` fails before showing a usable QR code with `status=408 Request Time-out` or a TLS socket disconnect.
> WhatsApp Web login uses the gateway host's standard proxy environment (`HTTPS_PROXY`, `HTTP_PROXY`, lowercase variants, and `NO_PROXY`). Verify the gateway process inherits the proxy env and that `NO_PROXY` does not match `mmg.whatsapp.net`.

### 代理后 QR 登录超时
症状：`openclaw channels login --channel whatsapp` 在显示可用二维码之前因 `status=408 Request Time-out` 或 TLS 套接字断开而失败。
WhatsApp Web 登录使用网关主机的标准代理环境变量。确认网关进程继承了代理环境变量，且 `NO_PROXY` 不匹配 `mmg.whatsapp.net`。

> ### No active listener when sending
> Outbound sends fail fast when no active gateway listener exists for the target account.

### 发送时无活跃监听器
当目标账号没有活跃的网关监听器时，出站发送会快速失败。

> ### Reply appears in transcript but not in WhatsApp
> Transcript rows record what the agent generated. WhatsApp delivery is checked separately: OpenClaw only treats an auto-reply as sent after Baileys returns an outbound message id for at least one visible text or media send.

### 回复出现在转录中但不在 WhatsApp 中
转录行记录 agent 生成的内容。WhatsApp 投递单独检查：OpenClaw 仅在 Baileys 返回至少一个可见文本或媒体发送的出站消息 ID 后才将自动回复视为已发送。

> ### Group messages unexpectedly ignored
> Check in this order: `groupPolicy` → `groupAllowFrom` / `allowFrom` → `groups` allowlist entries → mention gating → duplicate keys in `openclaw.json`

### 群消息被意外忽略
按此顺序检查：`groupPolicy` → `groupAllowFrom` / `allowFrom` → `groups` 白名单条目 → @提及门控 → `openclaw.json` 中的重复键

> ### Bun runtime warning
> WhatsApp gateway runtime should use Node. Bun is flagged as incompatible for stable WhatsApp/Telegram gateway operation.

### Bun 运行时警告
WhatsApp 网关运行时应该使用 Node。Bun 被标记为不兼容稳定的 WhatsApp/Telegram 网关操作。

---

> ## System prompts / 系统提示词

## System prompts / 系统提示词

> WhatsApp supports Telegram-style system prompts for groups and direct chats via the `groups` and `direct` maps.

WhatsApp 支持通过 `groups` 和 `direct` 映射为群聊和私聊设置 Telegram 风格的系统提示词。

> ### Resolution hierarchy for group messages:
> 1. **Group-specific system prompt** (`groups["<groupId>"].systemPrompt`): used when the specific group entry exists in the map **and** its `systemPrompt` key is defined. If `systemPrompt` is an empty string (`""`), the wildcard is suppressed and no system prompt is applied.
> 2. **Group wildcard system prompt** (`groups["*"].systemPrompt`): used when the specific group entry is absent from the map entirely, or when it exists but defines no `systemPrompt` key.

### 群聊消息的解析层级：
1. **群特定系统提示词**（`groups["<groupId>"].systemPrompt`）：当映射中存在该群的条目**且**其 `systemPrompt` 键已定义时使用。如果 `systemPrompt` 为空字符串（`""`），则通配符被抑制，不应用系统提示词。
2. **群通配符系统提示词**（`groups["*"].systemPrompt`）：当映射中完全不存在该群的条目，或存在但未定义 `systemPrompt` 键时使用。

> ### Resolution hierarchy for direct messages:
> 1. **Direct-specific system prompt** (`direct["<peerId>"].systemPrompt`): used when the specific peer entry exists in the map **and** its `systemPrompt` key is defined. If `systemPrompt` is an empty string (`""`), the wildcard is suppressed and no system prompt is applied.
> 2. **Direct wildcard system prompt** (`direct["*"].systemPrompt`): used when the specific peer entry is absent from the map entirely, or when it exists but defines no `systemPrompt` key.

### 私聊消息的解析层级：
1. **私聊特定系统提示词**（`direct["<peerId>"].systemPrompt`）：当映射中存在该对等方的条目**且**其 `systemPrompt` 键已定义时使用。如果 `systemPrompt` 为空字符串（`""`），则通配符被抑制，不应用系统提示词。
2. **私聊通配符系统提示词**（`direct["*"].systemPrompt`）：当映射中完全不存在该对等方的条目，或存在但未定义 `systemPrompt` 键时使用。

> **Difference from Telegram multi-account behavior:** In Telegram, root `groups` is intentionally suppressed for all accounts in a multi-account setup. WhatsApp does not apply this guard: root `groups` and root `direct` are always inherited by accounts that define no account-level override.

> **与 Telegram 多账号行为的区别：** 在 Telegram 中，多账号设置下根 `groups` 会被有意抑制。WhatsApp 不应用此防护：根 `groups` 和根 `direct` 始终被没有账号级别覆盖的账号继承。

> Important behavior:
> * `channels.whatsapp.groups` is both a per-group config map and the chat-level group allowlist. At either the root or account scope, `groups["*"]` means "all groups are admitted" for that scope.
> * Only add a wildcard group `systemPrompt` when you already want that scope to admit all groups.
> * `channels.whatsapp.direct` does not have the same side effect for DMs. `direct["*"]` only provides a default direct-chat config after a DM is already admitted by `dmPolicy` plus `allowFrom` or pairing-store rules.

重要行为：
* `channels.whatsapp.groups` 既是每群配置映射，也是聊天级别的群白名单。在根或账号作用域下，`groups["*"]` 表示"该作用域下所有群都被允许"。
* 仅当你希望该作用域允许所有群时，才添加通配符群 `systemPrompt`。
* `channels.whatsapp.direct` 对私聊没有相同的副作用。`direct["*"]` 仅在私聊已被 `dmPolicy` 加上 `allowFrom` 或配对存储规则允许后，提供默认私聊配置。

---

> ## Configuration reference pointers / 配置参考指针

## Configuration reference pointers / 配置参考指针

> Primary reference: [Configuration reference - WhatsApp](/gateway/config-channels#whatsapp)

主要参考：[配置参考 - WhatsApp](/gateway/config-channels#whatsapp)

> High-signal WhatsApp fields:
> * access: `dmPolicy`, `allowFrom`, `groupPolicy`, `groupAllowFrom`, `groups`
> * delivery: `textChunkLimit`, `chunkMode`, `mediaMaxMb`, `sendReadReceipts`, `ackReaction`, `reactionLevel`
> * multi-account: `accounts.<id>.enabled`, `accounts.<id>.authDir`, account-level overrides
> * operations: `configWrites`, `debounceMs`, `web.enabled`, `web.heartbeatSeconds`, `web.reconnect.*`, `web.whatsapp.*`
> * session behavior: `session.dmScope`, `historyLimit`, `dmHistoryLimit`, `dms.<id>.historyLimit`
> * prompts: `groups.<id>.systemPrompt`, `groups["*"].systemPrompt`, `direct.<id>.systemPrompt`, `direct["*"].systemPrompt`

高信号 WhatsApp 字段：
* 访问控制：`dmPolicy`, `allowFrom`, `groupPolicy`, `groupAllowFrom`, `groups`
* 投递：`textChunkLimit`, `chunkMode`, `mediaMaxMb`, `sendReadReceipts`, `ackReaction`, `reactionLevel`
* 多账号：`accounts.<id>.enabled`, `accounts.<id>.authDir`, 账号级别覆盖
* 运营：`configWrites`, `debounceMs`, `web.enabled`, `web.heartbeatSeconds`, `web.reconnect.*`, `web.whatsapp.*`
* 会话行为：`session.dmScope`, `historyLimit`, `dmHistoryLimit`, `dms.<id>.historyLimit`
* 提示词：`groups.<id>.systemPrompt`, `groups["*"].systemPrompt`, `direct.<id>.systemPrompt`, `direct["*"].systemPrompt`

---

> ## Related / 相关

## Related / 相关

> * [Pairing](/channels/pairing)
> * [Groups](/channels/groups)
> * [Security](/gateway/security)
> * [Channel routing](/channels/channel-routing)
> * [Multi-agent routing](/concepts/multi-agent)
> * [Troubleshooting](/channels/troubleshooting)

* [配对](/channels/pairing)
* [群组](/channels/groups)
* [安全](/gateway/security)
* [频道路由](/channels/channel-routing)
* [多 Agent 路由](/concepts/multi-agent)
* [故障排除](/channels/troubleshooting)
