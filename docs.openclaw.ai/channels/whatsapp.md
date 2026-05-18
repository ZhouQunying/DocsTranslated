# WhatsApp

> Status: production-ready via WhatsApp Web (Baileys). Gateway owns linked session(s).

状态：通过 WhatsApp Web（Baileys）已生产可用。Gateway 持有已链接的会话。

---

> ## Install (on demand)

## 按需安装

> * Onboarding (`openclaw onboard`) and `openclaw channels add --channel whatsapp` prompt to install the WhatsApp plugin the first time you select it.
> * `openclaw channels login --channel whatsapp` also offers the install flow when the plugin is not present yet.
> * Dev channel + git checkout: defaults to the local plugin path.
> * Stable/Beta: installs the official `@openclaw/whatsapp` plugin from ClawHub first, with npm as the fallback.
> * The WhatsApp runtime is distributed outside the core OpenClaw npm package so WhatsApp-specific runtime dependencies stay with the external plugin.

- 初次选择 WhatsApp 时，引导流程（`openclaw onboard`）和 `openclaw channels add --channel whatsapp` 会提示安装 WhatsApp 插件。
- 插件还没装时，`openclaw channels login --channel whatsapp` 也会提供安装流程。
- Dev 通道 + git checkout：默认走本地插件路径。
- Stable / Beta：优先从 ClawHub 装官方 `@openclaw/whatsapp` 插件，npm 作为回退。
- WhatsApp 运行时不放在 OpenClaw 核心 npm 包里，WhatsApp 特有的运行时依赖跟随外部插件一起走。

> Manual install stays available:
>
> ```bash
> openclaw plugins install clawhub:@openclaw/whatsapp
> ```

手动安装方式始终可用：

```bash
openclaw plugins install clawhub:@openclaw/whatsapp
```

> Use the bare npm package (`@openclaw/whatsapp`) only when you need the registry fallback. Pin an exact version only when you need a reproducible install.

只有在需要 npm registry 回退时才用裸 npm 包名（`@openclaw/whatsapp`）。需要可复现安装时才锁具体版本。

> <CardGroup cols={3}>
>   <Card title="Pairing" icon="link" href="/channels/pairing">
>     Default DM policy is pairing for unknown senders.
>   </Card>
>
>   <Card title="Channel troubleshooting" icon="wrench" href="/channels/troubleshooting">
>     Cross-channel diagnostics and repair playbooks.
>   </Card>
>
>   <Card title="Gateway configuration" icon="settings" href="/gateway/configuration">
>     Full channel config patterns and examples.
>   </Card>
> </CardGroup>

- [配对](/channels/pairing)：对陌生发件人的默认 DM 策略就是 pairing。
- [通道故障排查](/channels/troubleshooting)：跨通道的诊断和修复手册。
- [Gateway 配置](/gateway/configuration)：完整的通道配置模式和示例。

---

> ## Quick setup

## 快速配置

> [步骤 1: Configure WhatsApp access policy]
>
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

[步骤 1：配 WhatsApp 访问策略]

```json5
{
  channels: {
    whatsapp: {
      dmPolicy: "pairing",
      allowFrom: ["+15551234567"],
      groupPolicy: "allowlist",
      groupAllowFrom: ["+15551234567"],
    },
  },
}
```

> [步骤 2: Link WhatsApp (QR)]
>
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

[步骤 2：扫码链接 WhatsApp]

```bash
openclaw channels login --channel whatsapp
```

针对特定账号：

```bash
openclaw channels login --channel whatsapp --account work
```

登录前要挂上一个已有的 / 自定义的 WhatsApp Web 认证目录：

```bash
openclaw channels add --channel whatsapp --account work --auth-dir /path/to/wa-auth
openclaw channels login --channel whatsapp --account work
```

> [步骤 3: Start the gateway]
>
> ```bash
> openclaw gateway
> ```

[步骤 3：启动 Gateway]

```bash
openclaw gateway
```

> [步骤 4: Approve first pairing request (if using pairing mode)]
>
> ```bash
> openclaw pairing list whatsapp
> openclaw pairing approve whatsapp <CODE>
> ```
>
> Pairing requests expire after 1 hour. Pending requests are capped at 3 per channel.

[步骤 4：批准第一条配对请求（使用 pairing 模式时）]

```bash
openclaw pairing list whatsapp
openclaw pairing approve whatsapp <CODE>
```

配对请求 1 小时后过期。每个通道最多保留 3 条待处理请求。

> <Note>
>   OpenClaw recommends running WhatsApp on a separate number when possible. (The channel metadata and setup flow are optimized for that setup, but personal-number setups are also supported.)
> </Note>

> **提示**：OpenClaw 推荐 WhatsApp 尽量跑在独立号码上（通道元数据和配置流程都按这种部署优化，不过个人号码部署也支持）。

---

> ## Deployment patterns

## 部署模式

> [展开: Dedicated number (recommended)]
>
> This is the cleanest operational mode:
>
> * separate WhatsApp identity for OpenClaw
> * clearer DM allowlists and routing boundaries
> * lower chance of self-chat confusion

[展开：独立号码（推荐）]

这是运维最干净的模式：

- OpenClaw 用独立的 WhatsApp 身份。
- 私聊白名单和路由边界更清晰。
- 不容易被自己和自己的聊天搞混。

> Minimal policy pattern:
>
> ```json5
> {
>   channels: {
>     whatsapp: {
>       dmPolicy: "allowlist",
>       allowFrom: ["+15551234567"],
>     },
>   },
> }
> ```

最简策略模板：

```json5
{
  channels: {
    whatsapp: {
      dmPolicy: "allowlist",
      allowFrom: ["+15551234567"],
    },
  },
}
```

> [展开: Personal-number fallback]
>
> Onboarding supports personal-number mode and writes a self-chat-friendly baseline:
>
> * `dmPolicy: "allowlist"`
> * `allowFrom` includes your personal number
> * `selfChatMode: true`
>
> In runtime, self-chat protections key off the linked self number and `allowFrom`.

[展开：个人号码回退]

引导流程支持个人号码模式，写入一份对自聊友好的基线：

- `dmPolicy: "allowlist"`
- `allowFrom` 包含你的个人号码
- `selfChatMode: true`

运行时的自聊保护以已链接的自身号码和 `allowFrom` 为依据。

> [展开: WhatsApp Web-only channel scope]
>
> The messaging platform channel is WhatsApp Web-based (`Baileys`) in current OpenClaw channel architecture.
>
> There is no separate Twilio WhatsApp messaging channel in the built-in chat-channel registry.

[展开：仅 WhatsApp Web 范围]

当前 OpenClaw 的通道架构里，这个消息平台通道基于 WhatsApp Web（`Baileys`）。

内置的聊天通道注册表里没有单独的 Twilio WhatsApp 消息通道。

---

> ## Runtime model

## 运行时模型

> * Gateway owns the WhatsApp socket and reconnect loop.

- Gateway 持有 WhatsApp 套接字和重连循环。

> * The reconnect watchdog uses WhatsApp Web transport activity, not only inbound app-message volume, so a quiet linked-device session is not restarted solely because nobody has sent a message recently. A longer application-silence cap still forces a reconnect if transport frames keep arriving but no application messages are handled for the watchdog window; after a transient reconnect for a recently active session, that application-silence check uses the normal message timeout for the first recovery window.

- 重连看门狗看的是 WhatsApp Web 的传输活动，不只是收到的应用消息量。所以一段时间没人发消息的"安静"链接会话不会单凭这个就被重启。如果传输帧一直在到、但看门狗窗口内没有处理任何应用消息，更长的"应用静默"上限仍然会强制重连；最近活跃的会话经历了一次短暂重连之后，应用静默检查在第一次恢复窗口里走的是普通消息超时。

> * Baileys socket timings are explicit under `web.whatsapp.*`: `keepAliveIntervalMs` controls WhatsApp Web application pings, `connectTimeoutMs` controls the opening handshake timeout, and `defaultQueryTimeoutMs` controls Baileys query timeouts.

- Baileys 套接字时序明确放在 `web.whatsapp.*` 下：`keepAliveIntervalMs` 控制 WhatsApp Web 应用层 ping，`connectTimeoutMs` 控制握手超时，`defaultQueryTimeoutMs` 控制 Baileys 查询超时。

> * Outbound sends require an active WhatsApp listener for the target account.

- 要发消息，目标账号必须有一个活跃的 WhatsApp 监听器。

> * Group sends attach native mention metadata for `@+<digits>` and `@<digits>` tokens in text and media captions when the token matches current WhatsApp participant metadata, including LID-backed groups.

- 群消息发送时，文本和媒体说明中的 `@+<数字>` 和 `@<数字>` 标记若匹配当前 WhatsApp 群成员元数据（含基于 LID 的群），会自动附加原生 @ 提及元数据。

> * Status and broadcast chats are ignored (`@status`, `@broadcast`).

- 状态消息和广播聊天会忽略（`@status`、`@broadcast`）。

> * The reconnect watchdog follows WhatsApp Web transport activity, not only inbound app-message volume: quiet linked-device sessions stay up while transport frames continue, but a transport stall forces reconnect well before the later remote disconnect path.

- 重连看门狗跟随 WhatsApp Web 传输活动，不只是应用消息量：传输帧持续时，安静的链接会话保持在线；但传输停滞会在后面的"远端断开"路径触发之前就强制重连。

> * Direct chats use DM session rules (`session.dmScope`; default `main` collapses DMs to the agent main session).

- 私聊走 DM 会话规则（`session.dmScope`；默认 `main` 把私聊收敛到 agent 的 main 会话）。

> * Group sessions are isolated (`agent:<agentId>:whatsapp:group:<jid>`).

- 群会话隔离（`agent:<agentId>:whatsapp:group:<jid>`）。

> * WhatsApp Channels/Newsletters can be explicit outbound targets with their native `@newsletter` JID. Outbound newsletter sends use channel session metadata (`agent:<agentId>:whatsapp:channel:<jid>`) rather than DM session semantics.

- WhatsApp 频道 / Newsletter 可以作为显式发送目标，用它们的原生 `@newsletter` JID。发往 newsletter 的消息用频道会话元数据（`agent:<agentId>:whatsapp:channel:<jid>`），不走 DM 会话语义。

> * WhatsApp Web transport honors standard proxy environment variables on the gateway host (`HTTPS_PROXY`, `HTTP_PROXY`, `NO_PROXY` / lowercase variants). Prefer host-level proxy config over channel-specific WhatsApp proxy settings.

- WhatsApp Web 传输尊重 Gateway 宿主的标准代理环境变量（`HTTPS_PROXY`、`HTTP_PROXY`、`NO_PROXY` 及小写变体）。优先用宿主级代理配置，少用通道级的 WhatsApp 代理设置。

> * When `messages.removeAckAfterReply` is enabled, OpenClaw clears the WhatsApp ack reaction after a visible reply is delivered.

- 启用 `messages.removeAckAfterReply` 后，OpenClaw 在可见回复送达后会清掉 WhatsApp 的确认表情。

---

> ## Plugin hooks and privacy

## 插件钩子和隐私

> WhatsApp inbound messages can contain personal message content, phone numbers, group identifiers, sender names, and session correlation fields. For that reason, WhatsApp does not broadcast inbound `message_received` hook payloads to plugins unless you explicitly opt in:

WhatsApp 收到的消息可能包含个人消息内容、电话号码、群标识、发件人名字和会话关联字段。基于这个原因，WhatsApp 默认不把接收 `message_received` 钩子的载荷广播给插件，除非显式开启：

> ```json5
> {
>   channels: {
>     whatsapp: {
>       pluginHooks: {
>         messageReceived: true,
>       },
>     },
>   },
> }
> ```

```json5
{
  channels: {
    whatsapp: {
      pluginHooks: {
        messageReceived: true,
      },
    },
  },
}
```

> You can scope the opt-in to one account:
>
> ```json5
> {
>   channels: {
>     whatsapp: {
>       accounts: {
>         work: {
>           pluginHooks: {
>             messageReceived: true,
>           },
>         },
>       },
>     },
>   },
> }
> ```

可以把这个开关限定到一个账号：

```json5
{
  channels: {
    whatsapp: {
      accounts: {
        work: {
          pluginHooks: {
            messageReceived: true,
          },
        },
      },
    },
  },
}
```

> Only enable this for plugins you trust to receive inbound WhatsApp message content and identifiers.

只有当你信任某个插件可以收到 WhatsApp 接收消息的内容和标识时，才开启这个开关。

---

> ## Access control and activation

## 访问控制与激活

> [标签页: DM policy]
>
> `channels.whatsapp.dmPolicy` controls direct chat access:
>
> * `pairing` (default)
> * `allowlist`
> * `open` (requires `allowFrom` to include `"*"`)
> * `disabled`

[标签页：DM 策略]

`channels.whatsapp.dmPolicy` 控制私聊访问：

- `pairing`（默认）
- `allowlist`
- `open`（要求 `allowFrom` 含 `"*"`）
- `disabled`

> `allowFrom` accepts E.164-style numbers (normalized internally).

`allowFrom` 接受 E.164 风格的号码（内部会归一化）。

> `allowFrom` is a DM sender access-control list. It does not gate explicit outbound sends to WhatsApp group JIDs or `@newsletter` channel JIDs.

`allowFrom` 是私聊发件人访问控制列表，不会拦显式发往 WhatsApp 群 JID 或 `@newsletter` 频道 JID 的发送。

> Multi-account override: `channels.whatsapp.accounts.<id>.dmPolicy` (and `allowFrom`) take precedence over channel-level defaults for that account.

多账号覆盖：`channels.whatsapp.accounts.<id>.dmPolicy`（以及 `allowFrom`）对该账号优先于通道级默认值。

> Runtime behavior details:
>
> * pairings are persisted in channel allow-store and merged with configured `allowFrom`
> * scheduled automation and heartbeat recipient fallback use explicit delivery targets or configured `allowFrom`; DM pairing approvals are not implicit cron or heartbeat recipients
> * if no allowlist is configured, the linked self number is allowed by default
> * OpenClaw never auto-pairs outbound `fromMe` DMs (messages you send to yourself from the linked device)

运行时行为细节：

- 配对持久化在通道 allow-store 里，与配置的 `allowFrom` 合并。
- 定时自动化和心跳接收人的回退使用显式投递目标或配置的 `allowFrom`；DM 配对批准不会自动充当 cron 或心跳接收人。
- 没配白名单时，已链接的自身号码默认放行。
- OpenClaw 永远不会自动给发出的 `fromMe` 私聊（你从已链接设备发给自己的消息）做配对。

> [标签页: Group policy + allowlists]
>
> Group access has two layers:
>
> 1. **Group membership allowlist** (`channels.whatsapp.groups`)
>    * if `groups` is omitted, all groups are eligible
>    * if `groups` is present, it acts as a group allowlist (`"*"` allowed)
>
> 2. **Group sender policy** (`channels.whatsapp.groupPolicy` + `groupAllowFrom`)
>    * `open`: sender allowlist bypassed
>    * `allowlist`: sender must match `groupAllowFrom` (or `*`)
>    * `disabled`: block all group inbound

[标签页：群策略 + 白名单]

群访问分两层：

1. **群成员白名单**（`channels.whatsapp.groups`）
   - 没写 `groups`：所有群都符合资格。
   - 写了 `groups`：它就是群白名单（允许 `"*"`）。

2. **群发件人策略**（`channels.whatsapp.groupPolicy` + `groupAllowFrom`）
   - `open`：发件人白名单被绕过。
   - `allowlist`：发件人必须命中 `groupAllowFrom`（或 `*`）。
   - `disabled`：拦下所有群入消息。

> Sender allowlist fallback:
>
> * if `groupAllowFrom` is unset, runtime falls back to `allowFrom` when available
> * sender allowlists are evaluated before mention/reply activation

发件人白名单回退：

- `groupAllowFrom` 没设时，运行时回退到 `allowFrom`（有的话）。
- 发件人白名单在 @ / 回复激活之前判断。

> Note: if no `channels.whatsapp` block exists at all, runtime group-policy fallback is `allowlist` (with a warning log), even if `channels.defaults.groupPolicy` is set.

注意：如果 `channels.whatsapp` 块完全缺失，运行时群策略回退到 `allowlist`（并打警告日志），即使设了 `channels.defaults.groupPolicy` 也一样。

> [标签页: Mentions + /activation]
>
> Group replies require mention by default.
>
> Mention detection includes:
>
> * explicit WhatsApp mentions of the bot identity
> * configured mention regex patterns (`agents.list[].groupChat.mentionPatterns`, fallback `messages.groupChat.mentionPatterns`)
> * inbound voice-note transcripts for authorized group messages
> * implicit reply-to-bot detection (reply sender matches bot identity)

[标签页：@ + /activation]

群回复默认要求 @ 触发。

@ 检测包括：

- 对机器人身份的显式 WhatsApp @ 提及。
- 配置的 mention 正则（`agents.list[].groupChat.mentionPatterns`，回退到 `messages.groupChat.mentionPatterns`）。
- 已授权群消息里的语音笔记转写。
- 隐式"回复到机器人"检测（回复对象的发件人就是机器人身份）。

> Security note:
>
> * quote/reply only satisfies mention gating; it does **not** grant sender authorization
> * with `groupPolicy: "allowlist"`, non-allowlisted senders are still blocked even if they reply to an allowlisted user's message

安全说明：

- 引用 / 回复只满足 @ 触发条件，**不**授予发件人授权。
- 在 `groupPolicy: "allowlist"` 下，非白名单发件人即便回复白名单用户的消息，仍然会被拦。

> Session-level activation command:
>
> * `/activation mention`
> * `/activation always`
>
> `activation` updates session state (not global config). It is owner-gated.

会话级别的激活命令：

- `/activation mention`
- `/activation always`

`activation` 只改会话状态（不是全局配置），且只有所有者能用。

---

> ## Personal-number and self-chat behavior

## 个人号码和自聊行为

> When the linked self number is also present in `allowFrom`, WhatsApp self-chat safeguards activate:
>
> * skip read receipts for self-chat turns
> * ignore mention-JID auto-trigger behavior that would otherwise ping yourself
> * if `messages.responsePrefix` is unset, self-chat replies default to `[{identity.name}]` or `[openclaw]`

当已链接的自身号码也在 `allowFrom` 里时，WhatsApp 自聊保护会激活：

- 自聊轮次跳过已读回执。
- 忽略那些会 @ 到自己的 mention-JID 自动触发行为。
- 没设 `messages.responsePrefix` 时，自聊回复默认前缀是 `[{identity.name}]` 或 `[openclaw]`。

---

> ## Message normalization and context

## 消息归一化和上下文

> [展开: Inbound envelope + reply context]
>
> Incoming WhatsApp messages are wrapped in the shared inbound envelope.

[展开：接收信封 + 回复上下文]

收到的 WhatsApp 消息被包装在共用的接收信封里。

> If a quoted reply exists, context is appended in this form:
>
> ```text
> [Replying to <sender> id:<stanzaId>]
> <quoted body or media placeholder>
> [/Replying]
> ```

有引用回复时，上下文以这种形式附加：

```text
[Replying to <sender> id:<stanzaId>]
<quoted body or media placeholder>
[/Replying]
```

> Reply metadata fields are also populated when available (`ReplyToId`, `ReplyToBody`, `ReplyToSender`, sender JID/E.164).
> When the quoted reply target is downloadable media, OpenClaw saves it through the normal inbound media store and exposes it as `MediaPath`/`MediaType` so the agent can inspect the referenced image instead of only seeing `<media:image>`.

可用时回复元数据字段也会填上（`ReplyToId`、`ReplyToBody`、`ReplyToSender`、发件人 JID / E.164）。
当被引用的回复目标是可下载媒体时，OpenClaw 通过常规接收媒体存储把它存下来，并暴露 `MediaPath` / `MediaType`，让 agent 能查看被引用的图片，而不只是看到 `<media:image>`。

> [展开: Media placeholders and location/contact extraction]
>
> Media-only inbound messages are normalized with placeholders such as:
>
> * `<media:image>`
> * `<media:video>`
> * `<media:audio>`
> * `<media:document>`
> * `<media:sticker>`

[展开：媒体占位符与位置 / 联系人提取]

仅媒体的接收消息归一化为占位符，例如：

- `<media:image>`
- `<media:video>`
- `<media:audio>`
- `<media:document>`
- `<media:sticker>`

> Authorized group voice notes are transcribed before mention gating when the body is only `<media:audio>`, so saying the bot mention in the voice note can trigger the reply. If the transcript still does not mention the bot, the transcript is kept in pending group history instead of the raw placeholder.

授权群里的语音笔记，当 body 只有 `<media:audio>` 时，在 @ 触发判断之前会先转写，所以在语音笔记里说出机器人 @ 也能触发回复。如果转写后仍然没 @ 机器人，转写文本会保留在待处理群历史里，而不是原始占位符。

> Location bodies use terse coordinate text. Location labels/comments and contact/vCard details are rendered as fenced untrusted metadata, not inline prompt text.

位置消息正文用简短的坐标文本。位置标签 / 备注和联系人 / vCard 细节渲染为围栏内的不受信元数据，不作为行内提示词文本。

> [展开: Pending group history injection]
>
> For groups, unprocessed messages can be buffered and injected as context when the bot is finally triggered.

[展开：待处理群历史注入]

群里没处理的消息可以缓冲下来，等机器人最终被触发时作为上下文注入。

> * default limit: `50`
> * config: `channels.whatsapp.historyLimit`
> * fallback: `messages.groupChat.historyLimit`
> * `0` disables

- 默认上限：`50`
- 配置：`channels.whatsapp.historyLimit`
- 回退：`messages.groupChat.historyLimit`
- `0` 关闭

> Injection markers:
>
> * `[Chat messages since your last reply - for context]`
> * `[Current message - respond to this]`

注入标记：

- `[Chat messages since your last reply - for context]`
- `[Current message - respond to this]`

> [展开: Read receipts]
>
> Read receipts are enabled by default for accepted inbound WhatsApp messages.

[展开：已读回执]

接受的 WhatsApp 接收消息默认会发已读回执。

> Disable globally:
>
> ```json5
> {
>   channels: {
>     whatsapp: {
>       sendReadReceipts: false,
>     },
>   },
> }
> ```

全局关闭：

```json5
{
  channels: {
    whatsapp: {
      sendReadReceipts: false,
    },
  },
}
```

> Per-account override:
>
> ```json5
> {
>   channels: {
>     whatsapp: {
>       accounts: {
>         work: {
>           sendReadReceipts: false,
>         },
>       },
>     },
>   },
> }
> ```

按账号覆盖：

```json5
{
  channels: {
    whatsapp: {
      accounts: {
        work: {
          sendReadReceipts: false,
        },
      },
    },
  },
}
```

> Self-chat turns skip read receipts even when globally enabled.

即便全局开了，自聊轮次也会跳过已读回执。

---

> ## Delivery, chunking, and media

## 投递、分片和媒体

> [展开: Text chunking]
>
> * default chunk limit: `channels.whatsapp.textChunkLimit = 4000`
> * `channels.whatsapp.chunkMode = "length" | "newline"`
> * `newline` mode prefers paragraph boundaries (blank lines), then falls back to length-safe chunking

[展开：文本分片]

- 默认分片上限：`channels.whatsapp.textChunkLimit = 4000`
- `channels.whatsapp.chunkMode = "length" | "newline"`
- `newline` 模式优先按段落边界（空行）切，然后回退到按长度安全切分。

> [展开: Outbound media behavior]
>
> * supports image, video, audio (PTT voice-note), and document payloads
> * audio media is sent through the Baileys `audio` payload with `ptt: true`, so WhatsApp clients render it as a push-to-talk voice note
> * reply payloads preserve `audioAsVoice`; TTS voice-note output for WhatsApp stays on this PTT path even when the provider returns MP3 or WebM
> * native Ogg/Opus audio is sent as `audio/ogg; codecs=opus` for voice-note compatibility
> * non-Ogg audio, including Microsoft Edge TTS MP3/WebM output, is transcoded with `ffmpeg` to 48 kHz mono Ogg/Opus before PTT delivery
> * `/tts latest` sends the latest assistant reply as one voice note and suppresses repeat sends for the same reply; `/tts chat on|off|default` controls auto-TTS for the current WhatsApp chat
> * animated GIF playback is supported via `gifPlayback: true` on video sends
> * captions are applied to the first media item when sending multi-media reply payloads, except PTT voice notes send the audio first and visible text separately because WhatsApp clients do not render voice-note captions consistently
> * media source can be HTTP(S), `file://`, or local paths

[展开：发送媒体的行为]

- 支持图片、视频、音频（PTT 语音笔记）和文档载荷。
- 音频媒体通过 Baileys 的 `audio` 载荷加 `ptt: true` 发出，WhatsApp 客户端把它渲染成一条按住说话的语音笔记。
- 回复载荷保留 `audioAsVoice`；即便 provider 返回 MP3 或 WebM，WhatsApp 的 TTS 语音笔记输出仍然走这条 PTT 路径。
- 原生 Ogg/Opus 音频按 `audio/ogg; codecs=opus` 发出，兼容语音笔记。
- 非 Ogg 音频（包括 Microsoft Edge TTS 的 MP3 / WebM 输出）在 PTT 投递前用 `ffmpeg` 转码到 48 kHz 单声道 Ogg/Opus。
- `/tts latest` 把最近一条 assistant 回复作为一条语音笔记发出，同一条回复不会重复发；`/tts chat on|off|default` 控制当前 WhatsApp 聊天的自动 TTS。
- 视频发送时设 `gifPlayback: true` 支持动图 GIF 播放。
- 发多媒体回复载荷时，caption 加在第一项媒体上 —— 除了 PTT 语音笔记：音频先发，可见文本另发一条，因为 WhatsApp 客户端对语音笔记的 caption 渲染不一致。
- 媒体源可以是 HTTP(S)、`file://` 或本地路径。

> [展开: Media size limits and fallback behavior]
>
> * inbound media save cap: `channels.whatsapp.mediaMaxMb` (default `50`)
> * outbound media send cap: `channels.whatsapp.mediaMaxMb` (default `50`)
> * per-account overrides use `channels.whatsapp.accounts.<accountId>.mediaMaxMb`
> * images are auto-optimized (resize/quality sweep) to fit limits
> * on media send failure, first-item fallback sends text warning instead of dropping the response silently

[展开：媒体大小上限与回退行为]

- 接收媒体保存上限：`channels.whatsapp.mediaMaxMb`（默认 `50`）
- 发送媒体上限：`channels.whatsapp.mediaMaxMb`（默认 `50`）
- 按账号覆盖用 `channels.whatsapp.accounts.<accountId>.mediaMaxMb`
- 图片会自动优化（按尺寸 / 质量扫一遍）以贴合上限。
- 媒体发送失败时，对第一项的回退会发一条文本警告，而不是静默丢掉响应。

---

> ## Reply quoting

## 回复引用

> WhatsApp supports native reply quoting, where outbound replies visibly quote the inbound message. Control it with `channels.whatsapp.replyToMode`.

WhatsApp 支持原生回复引用：发出的回复可视化地引用收到的消息。用 `channels.whatsapp.replyToMode` 控制。

> | Value       | Behavior                                                              |
> | ----------- | --------------------------------------------------------------------- |
> | `"off"`     | Never quote; send as a plain message                                  |
> | `"first"`   | Quote only the first outbound reply chunk                             |
> | `"all"`     | Quote every outbound reply chunk                                      |
> | `"batched"` | Quote queued batched replies while leaving immediate replies unquoted |

| 取值        | 行为                                                            |
| ----------- | --------------------------------------------------------------- |
| `"off"`     | 永不引用；按普通消息发                                          |
| `"first"`   | 只在发出的第一段回复上引用                                      |
| `"all"`     | 每一段发出的回复都引用                                          |
| `"batched"` | 引用排队批量回复，对即时回复不引用                              |

> Default is `"off"`. Per-account overrides use `channels.whatsapp.accounts.<id>.replyToMode`.

默认 `"off"`。按账号覆盖用 `channels.whatsapp.accounts.<id>.replyToMode`。

> ```json5
> {
>   channels: {
>     whatsapp: {
>       replyToMode: "first",
>     },
>   },
> }
> ```

```json5
{
  channels: {
    whatsapp: {
      replyToMode: "first",
    },
  },
}
```

---

> ## Reaction level

## 表情等级

> `channels.whatsapp.reactionLevel` controls how broadly the agent uses emoji reactions on WhatsApp:

`channels.whatsapp.reactionLevel` 控制 agent 在 WhatsApp 上使用 emoji 表情的范围：

> | Level         | Ack reactions | Agent-initiated reactions | Description                                      |
> | ------------- | ------------- | ------------------------- | ------------------------------------------------ |
> | `"off"`       | No            | No                        | No reactions at all                              |
> | `"ack"`       | Yes           | No                        | Ack reactions only (pre-reply receipt)           |
> | `"minimal"`   | Yes           | Yes (conservative)        | Ack + agent reactions with conservative guidance |
> | `"extensive"` | Yes           | Yes (encouraged)          | Ack + agent reactions with encouraged guidance   |

| 等级          | Ack 表情 | Agent 主动表情 | 说明                                          |
| ------------- | -------- | -------------- | --------------------------------------------- |
| `"off"`       | 无       | 无             | 完全不发表情                                  |
| `"ack"`       | 有       | 无             | 只发确认表情（回复前回执）                   |
| `"minimal"`   | 有       | 有（保守）     | Ack + agent 表情，引导偏保守                  |
| `"extensive"` | 有       | 有（鼓励）     | Ack + agent 表情，引导偏鼓励                  |

> Default: `"minimal"`.

默认：`"minimal"`。

> Per-account overrides use `channels.whatsapp.accounts.<id>.reactionLevel`.

按账号覆盖用 `channels.whatsapp.accounts.<id>.reactionLevel`。

> ```json5
> {
>   channels: {
>     whatsapp: {
>       reactionLevel: "ack",
>     },
>   },
> }
> ```

```json5
{
  channels: {
    whatsapp: {
      reactionLevel: "ack",
    },
  },
}
```

---

> ## Acknowledgment reactions

## 确认表情

> WhatsApp supports immediate ack reactions on inbound receipt via `channels.whatsapp.ackReaction`.
> Ack reactions are gated by `reactionLevel` — they are suppressed when `reactionLevel` is `"off"`.

WhatsApp 支持在收到消息时立即发确认表情，配置在 `channels.whatsapp.ackReaction`。
确认表情受 `reactionLevel` 限制 —— `reactionLevel` 为 `"off"` 时会被静默掉。

> ```json5
> {
>   channels: {
>     whatsapp: {
>       ackReaction: {
>         emoji: "👀",
>         direct: true,
>         group: "mentions", // always | mentions | never
>       },
>     },
>   },
> }
> ```

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

> Behavior notes:
>
> * sent immediately after inbound is accepted (pre-reply)
> * failures are logged but do not block normal reply delivery
> * group mode `mentions` reacts on mention-triggered turns; group activation `always` acts as bypass for this check
> * WhatsApp uses `channels.whatsapp.ackReaction` (legacy `messages.ackReaction` is not used here)

行为说明：

- 接收被接受后立即发（回复之前）。
- 失败会记日志，但不会阻塞正常的回复投递。
- 群模式 `mentions` 在 @ 触发的轮次上发表情；群激活 `always` 模式对这个检查起绕过作用。
- WhatsApp 用的是 `channels.whatsapp.ackReaction`（这里不走旧版 `messages.ackReaction`）。

---

> ## Lifecycle status reactions

## 生命周期状态表情

> Set `messages.statusReactions.enabled: true` to let WhatsApp replace the ack reaction during a turn instead of leaving a static receipt emoji. When enabled, OpenClaw uses the same inbound message reaction slot for lifecycle states such as queued, thinking, tool activity, compaction, done, and error.

把 `messages.statusReactions.enabled` 设成 `true`，WhatsApp 在一轮里就会替换掉确认表情，而不是留一个静态的回执 emoji。开启后，OpenClaw 复用同一条接收消息的表情槽，承载生命周期状态：排队、思考、工具活动、压缩、完成、错误。

> ```json5
> {
>   messages: {
>     statusReactions: {
>       enabled: true,
>       emojis: {
>         deploy: "🛫",
>         build: "🏗️",
>         concierge: "💁",
>       },
>     },
>   },
> }
> ```

```json5
{
  messages: {
    statusReactions: {
      enabled: true,
      emojis: {
        deploy: "🛫",
        build: "🏗️",
        concierge: "💁",
      },
    },
  },
}
```

> Behavior notes:
>
> * `channels.whatsapp.ackReaction` still controls whether status reactions are eligible for direct messages and groups.
> * WhatsApp has one bot reaction slot per message, so lifecycle updates replace the current reaction in place.
> * `messages.removeAckAfterReply: true` clears the final status reaction after the configured done/error hold.
> * Tool emoji categories include `tool`, `coding`, `web`, `deploy`, `build`, and `concierge`.

行为说明：

- `channels.whatsapp.ackReaction` 仍然控制状态表情在私聊和群里是否可用。
- WhatsApp 每条消息只有一个机器人表情槽，所以生命周期更新会原地替换当前表情。
- `messages.removeAckAfterReply: true` 在配置的 done / error 停留时长后清掉最终状态表情。
- 工具 emoji 类别包括 `tool`、`coding`、`web`、`deploy`、`build`、`concierge`。

---

> ## Multi-account and credentials

## 多账号与凭证

> [展开: Account selection and defaults]
>
> * account ids come from `channels.whatsapp.accounts`
> * default account selection: `default` if present, otherwise first configured account id (sorted)
> * account ids are normalized internally for lookup

[展开：账号选择与默认值]

- 账号 ID 来自 `channels.whatsapp.accounts`。
- 默认账号选择：有 `default` 用 `default`，否则用配置里第一个账号 ID（按排序）。
- 账号 ID 内部会归一化以便查找。

> [展开: Credential paths and legacy compatibility]
>
> * current auth path: `~/.openclaw/credentials/whatsapp/<accountId>/creds.json`
> * backup file: `creds.json.bak`
> * legacy default auth in `~/.openclaw/credentials/` is still recognized/migrated for default-account flows

[展开：凭证路径与旧版兼容]

- 当前认证路径：`~/.openclaw/credentials/whatsapp/<accountId>/creds.json`
- 备份文件：`creds.json.bak`
- 旧版 `~/.openclaw/credentials/` 下的默认认证仍然能识别，默认账号流程会自动迁移。

> [展开: Logout behavior]
>
> `openclaw channels logout --channel whatsapp [--account <id>]` clears WhatsApp auth state for that account.

[展开：登出行为]

`openclaw channels logout --channel whatsapp [--account <id>]` 清理该账号的 WhatsApp 认证状态。

> When a Gateway is reachable, logout first stops the live WhatsApp listener for the selected account so the linked session does not keep receiving messages until the next restart. `openclaw channels remove --channel whatsapp` also stops the live listener before disabling or deleting account config.

Gateway 可达时，登出会先停掉所选账号的实时 WhatsApp 监听器，避免链接会话一直收消息到下次重启。`openclaw channels remove --channel whatsapp` 在禁用或删除账号配置之前也会先停实时监听器。

> In legacy auth directories, `oauth.json` is preserved while Baileys auth files are removed.

在旧版认证目录里，`oauth.json` 会保留，Baileys 认证文件会被删掉。

---

> ## Tools, actions, and config writes

## 工具、动作和写配置

> * Agent tool support includes WhatsApp reaction action (`react`).
> * Action gates:
>   * `channels.whatsapp.actions.reactions`
>   * `channels.whatsapp.actions.polls`
> * Channel-initiated config writes are enabled by default (disable via `channels.whatsapp.configWrites=false`).

- agent 工具支持 WhatsApp 表情动作（`react`）。
- 动作开关：
  - `channels.whatsapp.actions.reactions`
  - `channels.whatsapp.actions.polls`
- 通道发起的写配置默认开启（用 `channels.whatsapp.configWrites=false` 关掉）。

---

> ## Troubleshooting

## 故障排查

> [展开: Not linked (QR required)]
>
> Symptom: channel status reports not linked.

[展开：未链接（需要扫码）]

现象：通道状态报告未链接。

> Fix:
>
> ```bash
> openclaw channels login --channel whatsapp
> openclaw channels status
> ```

修法：

```bash
openclaw channels login --channel whatsapp
openclaw channels status
```

> [展开: Linked but disconnected / reconnect loop]
>
> Symptom: linked account with repeated disconnects or reconnect attempts.

[展开：已链接但断开 / 反复重连]

现象：账号已链接，但反复断开或反复尝试重连。

> Quiet accounts can stay connected past the normal message timeout; the watchdog restarts when WhatsApp Web transport activity stops, the socket closes, or application-level activity stays silent beyond the longer safety window.

安静的账号可以在普通消息超时之后仍然保持连接；看门狗在 WhatsApp Web 传输活动停了、套接字关掉了，或应用层活动安静过了更长的安全窗口之后才重启。

> If logs show repeated `status=408 Request Time-out Connection was lost`, tune Baileys socket timings under `web.whatsapp`. Start by shortening `keepAliveIntervalMs` below your network's idle timeout and increasing `connectTimeoutMs` on slow or lossy links:

日志里反复出现 `status=408 Request Time-out Connection was lost` 时，调一下 `web.whatsapp` 下的 Baileys 套接字时序。先把 `keepAliveIntervalMs` 调到比网络空闲超时更短，慢链路或丢包链路上把 `connectTimeoutMs` 调大：

> ```json5
> {
>   web: {
>     whatsapp: {
>       keepAliveIntervalMs: 15000,
>       connectTimeoutMs: 60000,
>       defaultQueryTimeoutMs: 60000,
>     },
>   },
> }
> ```

```json5
{
  web: {
    whatsapp: {
      keepAliveIntervalMs: 15000,
      connectTimeoutMs: 60000,
      defaultQueryTimeoutMs: 60000,
    },
  },
}
```

> Fix:
>
> ```bash
> openclaw doctor
> openclaw logs --follow
> ```

修法：

```bash
openclaw doctor
openclaw logs --follow
```

> If `~/.openclaw/logs/whatsapp-health.log` says `Gateway inactive` but `openclaw gateway status` and `openclaw channels status --probe` show the gateway and WhatsApp are healthy, run `openclaw doctor`. On Linux, doctor warns about legacy crontab entries that still invoke `~/.openclaw/bin/ensure-whatsapp.sh`; remove those stale entries with `crontab -e` because cron can lack the systemd user-bus environment and make that old script misreport gateway health.

如果 `~/.openclaw/logs/whatsapp-health.log` 显示 `Gateway inactive`，但 `openclaw gateway status` 和 `openclaw channels status --probe` 都显示 Gateway 和 WhatsApp 健康，跑 `openclaw doctor`。Linux 上 doctor 会就那些仍在调 `~/.openclaw/bin/ensure-whatsapp.sh` 的旧 crontab 条目发警告；用 `crontab -e` 把这些过期条目去掉 —— cron 可能缺少 systemd 用户总线环境，让那个老脚本误报 Gateway 健康状态。

> If needed, re-link with `channels login`.

需要的话用 `channels login` 重新链接。

> [展开: QR login times out behind a proxy]
>
> Symptom: `openclaw channels login --channel whatsapp` fails before showing a usable QR code with `status=408 Request Time-out` or a TLS socket disconnect.

[展开：代理后面 QR 登录超时]

现象：`openclaw channels login --channel whatsapp` 在显示可用二维码之前就以 `status=408 Request Time-out` 或 TLS 套接字断开失败。

> WhatsApp Web login uses the gateway host's standard proxy environment (`HTTPS_PROXY`, `HTTP_PROXY`, lowercase variants, and `NO_PROXY`). Verify the gateway process inherits the proxy env and that `NO_PROXY` does not match `mmg.whatsapp.net`.

WhatsApp Web 登录走 Gateway 宿主的标准代理环境（`HTTPS_PROXY`、`HTTP_PROXY`，及它们的小写变体和 `NO_PROXY`）。确认 Gateway 进程继承了代理环境变量，并且 `NO_PROXY` 没匹配到 `mmg.whatsapp.net`。

> [展开: No active listener when sending]
>
> Outbound sends fail fast when no active gateway listener exists for the target account.
>
> Make sure gateway is running and the account is linked.

[展开：发送时没有活跃监听器]

目标账号没有活跃的 Gateway 监听器时，发送会快速失败。

确认 Gateway 在跑、账号已链接。

> [展开: Reply appears in transcript but not in WhatsApp]
>
> Transcript rows record what the agent generated. WhatsApp delivery is checked separately: OpenClaw only treats an auto-reply as sent after Baileys returns an outbound message id for at least one visible text or media send.

[展开：回复出现在 transcript 但没到 WhatsApp]

transcript 行记录 agent 生成了什么。WhatsApp 投递独立判断：只有当 Baileys 给至少一条可见文本或媒体发送返回了发送消息 id，OpenClaw 才把自动回复视为已发送。

> Ack reactions are independent pre-reply receipts. A successful reaction does not prove that the later text or media reply was accepted by WhatsApp.

Ack 表情是独立的"回复前回执"。表情成功并不能证明后续的文本或媒体回复被 WhatsApp 接受了。

> Check gateway logs for `auto-reply delivery failed` or `auto-reply was not accepted by WhatsApp provider`.

看 Gateway 日志里有没有 `auto-reply delivery failed` 或 `auto-reply was not accepted by WhatsApp provider`。

> [展开: Group messages unexpectedly ignored]
>
> Check in this order:
>
> * `groupPolicy`
> * `groupAllowFrom` / `allowFrom`
> * `groups` allowlist entries
> * mention gating (`requireMention` + mention patterns)
> * duplicate keys in `openclaw.json` (JSON5): later entries override earlier ones, so keep a single `groupPolicy` per scope

[展开：群消息莫名被忽略]

按这个顺序排查：

- `groupPolicy`
- `groupAllowFrom` / `allowFrom`
- `groups` 白名单条目
- @ 触发（`requireMention` + mention 模式）
- `openclaw.json`（JSON5）里的重复 key：后写的会覆盖先写的，每个作用域只保留一个 `groupPolicy`。

> [展开: Bun runtime warning]
>
> WhatsApp gateway runtime should use Node. Bun is flagged as incompatible for stable WhatsApp/Telegram gateway operation.

[展开：Bun 运行时警告]

WhatsApp Gateway 运行时应该用 Node。Bun 在稳定的 WhatsApp / Telegram Gateway 运行上被标记为不兼容。

---

> ## System prompts

## 系统提示词

> WhatsApp supports Telegram-style system prompts for groups and direct chats via the `groups` and `direct` maps.

WhatsApp 通过 `groups` 和 `direct` 映射，为群和私聊支持 Telegram 风格的系统提示词。

> Resolution hierarchy for group messages:

群消息的解析层级：

> The effective `groups` map is determined first: if the account defines its own `groups`, it fully replaces the root `groups` map (no deep merge). Prompt lookup then runs on the resulting single map:

先确定有效的 `groups` 映射：账号自己定义了 `groups` 时，它完全替换根 `groups`（不做深合并）。提示词查找在最终这一份单一映射上做：

> 1. **Group-specific system prompt** (`groups["<groupId>"].systemPrompt`): used when the specific group entry exists in the map **and** its `systemPrompt` key is defined. If `systemPrompt` is an empty string (`""`), the wildcard is suppressed and no system prompt is applied.
> 2. **Group wildcard system prompt** (`groups["*"].systemPrompt`): used when the specific group entry is absent from the map entirely, or when it exists but defines no `systemPrompt` key.

1. **群专属系统提示词**（`groups["<groupId>"].systemPrompt`）：映射里**有**该群条目且其 `systemPrompt` key **已定义**时使用。`systemPrompt` 写空字符串（`""`）时，通配会被压制，不应用任何系统提示词。
2. **群通配系统提示词**（`groups["*"].systemPrompt`）：映射里完全没这个具体群条目，或者条目在但没定义 `systemPrompt` key 时使用。

> Resolution hierarchy for direct messages:

私聊的解析层级：

> The effective `direct` map is determined first: if the account defines its own `direct`, it fully replaces the root `direct` map (no deep merge). Prompt lookup then runs on the resulting single map:

先确定有效的 `direct` 映射：账号自己定义了 `direct` 时，它完全替换根 `direct`（不做深合并）。提示词查找在最终这一份单一映射上做：

> 1. **Direct-specific system prompt** (`direct["<peerId>"].systemPrompt`): used when the specific peer entry exists in the map **and** its `systemPrompt` key is defined. If `systemPrompt` is an empty string (`""`), the wildcard is suppressed and no system prompt is applied.
> 2. **Direct wildcard system prompt** (`direct["*"].systemPrompt`): used when the specific peer entry is absent from the map entirely, or when it exists but defines no `systemPrompt` key.

1. **私聊专属系统提示词**（`direct["<peerId>"].systemPrompt`）：映射里**有**该 peer 条目且其 `systemPrompt` key **已定义**时使用。`systemPrompt` 写空字符串（`""`）时，通配会被压制，不应用任何系统提示词。
2. **私聊通配系统提示词**（`direct["*"].systemPrompt`）：映射里完全没这个具体 peer 条目，或者条目在但没定义 `systemPrompt` key 时使用。

> <Note>
>   `dms` remains the lightweight per-DM history override bucket (`dms.<id>.historyLimit`). Prompt overrides live under `direct`.
> </Note>

> **提示**：`dms` 仍然是轻量级的每 DM 历史覆盖桶（`dms.<id>.historyLimit`）。提示词覆盖放在 `direct` 下。

> **Difference from Telegram multi-account behavior:** In Telegram, root `groups` is intentionally suppressed for all accounts in a multi-account setup — even accounts that define no `groups` of their own — to prevent a bot from receiving group messages for groups it does not belong to. WhatsApp does not apply this guard: root `groups` and root `direct` are always inherited by accounts that define no account-level override, regardless of how many accounts are configured. In a multi-account WhatsApp setup, if you want per-account group or direct prompts, define the full map under each account explicitly rather than relying on root-level defaults.

**与 Telegram 多账号行为的区别**：Telegram 在多账号部署里有意压制所有账号的根 `groups` —— 即便账号本身没定义 `groups` 也一样 —— 避免机器人为不属于它的群收消息。WhatsApp 不做这个守卫：根 `groups` 和根 `direct` 始终被那些没定义账号级覆盖的账号继承，跟配置了多少账号无关。WhatsApp 多账号部署里，如果想要按账号区分群或私聊提示词，请在每个账号下显式定义完整映射，不要依赖根级默认。

> Important behavior:
>
> * `channels.whatsapp.groups` is both a per-group config map and the chat-level group allowlist. At either the root or account scope, `groups["*"]` means "all groups are admitted" for that scope.
> * Only add a wildcard group `systemPrompt` when you already want that scope to admit all groups. If you still want only a fixed set of group IDs to be eligible, do not use `groups["*"]` for the prompt default. Instead, repeat the prompt on each explicitly allowlisted group entry.
> * Group admission and sender authorization are separate checks. `groups["*"]` widens the set of groups that can reach group handling, but it does not by itself authorize every sender in those groups. Sender access is still controlled separately by `channels.whatsapp.groupPolicy` and `channels.whatsapp.groupAllowFrom`.
> * `channels.whatsapp.direct` does not have the same side effect for DMs. `direct["*"]` only provides a default direct-chat config after a DM is already admitted by `dmPolicy` plus `allowFrom` or pairing-store rules.

重要行为：

- `channels.whatsapp.groups` 同时是按群的配置映射 + 聊天级别的群白名单。在根或账号作用域下，`groups["*"]` 意思是"该作用域下所有群都准入"。
- 只有你确实想让这个作用域准入所有群时，才加一个通配群的 `systemPrompt`。如果你只想让一组固定的群 ID 符合资格，不要用 `groups["*"]` 做提示词默认值 —— 把同样的提示词写到每个显式白名单群条目上。
- 群准入和发件人授权是两套检查。`groups["*"]` 扩大能进入群处理的群集合，但本身不给那些群里的每个发件人授权。发件人访问仍然由 `channels.whatsapp.groupPolicy` 和 `channels.whatsapp.groupAllowFrom` 单独控制。
- `channels.whatsapp.direct` 对私聊没有同样的副作用。`direct["*"]` 只是给已经被 `dmPolicy` + `allowFrom` 或配对存储规则准入的私聊提供一个默认配置。

> Example:
>
> ```json5
> {
>   channels: {
>     whatsapp: {
>       groups: {
>         // Use only if all groups should be admitted at the root scope.
>         // Applies to all accounts that do not define their own groups map.
>         "*": { systemPrompt: "Default prompt for all groups." },
>       },
>       direct: {
>         // Applies to all accounts that do not define their own direct map.
>         "*": { systemPrompt: "Default prompt for all direct chats." },
>       },
>       accounts: {
>         work: {
>           groups: {
>             // This account defines its own groups, so root groups are fully
>             // replaced. To keep a wildcard, define "*" explicitly here too.
>             "120363406415684625@g.us": {
>               requireMention: false,
>               systemPrompt: "Focus on project management.",
>             },
>             // Use only if all groups should be admitted in this account.
>             "*": { systemPrompt: "Default prompt for work groups." },
>           },
>           direct: {
>             // This account defines its own direct map, so root direct entries are
>             // fully replaced. To keep a wildcard, define "*" explicitly here too.
>             "+15551234567": { systemPrompt: "Prompt for a specific work direct chat." },
>             "*": { systemPrompt: "Default prompt for work direct chats." },
>           },
>         },
>       },
>     },
>   },
> }
> ```

例子：

```json5
{
  channels: {
    whatsapp: {
      groups: {
        // 只在你想让根作用域准入所有群时用。
        // 对所有没定义自己 groups 映射的账号生效。
        "*": { systemPrompt: "Default prompt for all groups." },
      },
      direct: {
        // 对所有没定义自己 direct 映射的账号生效。
        "*": { systemPrompt: "Default prompt for all direct chats." },
      },
      accounts: {
        work: {
          groups: {
            // 这个账号定义了自己的 groups，所以根 groups 被完全替换。
            // 想保留通配，这里也要显式定义 "*"。
            "120363406415684625@g.us": {
              requireMention: false,
              systemPrompt: "Focus on project management.",
            },
            // 只在你想让该账号准入所有群时用。
            "*": { systemPrompt: "Default prompt for work groups." },
          },
          direct: {
            // 这个账号定义了自己的 direct 映射，根 direct 条目被完全替换。
            // 想保留通配，这里也要显式定义 "*"。
            "+15551234567": { systemPrompt: "Prompt for a specific work direct chat." },
            "*": { systemPrompt: "Default prompt for work direct chats." },
          },
        },
      },
    },
  },
}
```

---

> ## Configuration reference pointers

## 配置项参考索引

> Primary reference:
>
> * [Configuration reference - WhatsApp](/gateway/config-channels#whatsapp)

主参考：

- [配置参考 - WhatsApp](/gateway/config-channels#whatsapp)

> High-signal WhatsApp fields:
>
> * access: `dmPolicy`, `allowFrom`, `groupPolicy`, `groupAllowFrom`, `groups`
> * delivery: `textChunkLimit`, `chunkMode`, `mediaMaxMb`, `sendReadReceipts`, `ackReaction`, `reactionLevel`
> * multi-account: `accounts.<id>.enabled`, `accounts.<id>.authDir`, account-level overrides
> * operations: `configWrites`, `debounceMs`, `web.enabled`, `web.heartbeatSeconds`, `web.reconnect.*`, `web.whatsapp.*`
> * session behavior: `session.dmScope`, `historyLimit`, `dmHistoryLimit`, `dms.<id>.historyLimit`
> * prompts: `groups.<id>.systemPrompt`, `groups["*"].systemPrompt`, `direct.<id>.systemPrompt`, `direct["*"].systemPrompt`

高信号量的 WhatsApp 字段：

- 访问：`dmPolicy`、`allowFrom`、`groupPolicy`、`groupAllowFrom`、`groups`
- 投递：`textChunkLimit`、`chunkMode`、`mediaMaxMb`、`sendReadReceipts`、`ackReaction`、`reactionLevel`
- 多账号：`accounts.<id>.enabled`、`accounts.<id>.authDir`、账号级覆盖
- 运维：`configWrites`、`debounceMs`、`web.enabled`、`web.heartbeatSeconds`、`web.reconnect.*`、`web.whatsapp.*`
- 会话行为：`session.dmScope`、`historyLimit`、`dmHistoryLimit`、`dms.<id>.historyLimit`
- 提示词：`groups.<id>.systemPrompt`、`groups["*"].systemPrompt`、`direct.<id>.systemPrompt`、`direct["*"].systemPrompt`

---

> ## Related

## 相关

> * [Pairing](/channels/pairing)
> * [Groups](/channels/groups)
> * [Security](/gateway/security)
> * [Channel routing](/channels/channel-routing)
> * [Multi-agent routing](/concepts/multi-agent)
> * [Troubleshooting](/channels/troubleshooting)

- [配对](/channels/pairing)
- [群组](/channels/groups)
- [安全](/gateway/security)
- [通道路由](/channels/channel-routing)
- [多 agent 路由](/concepts/multi-agent)
- [故障排查](/channels/troubleshooting)
