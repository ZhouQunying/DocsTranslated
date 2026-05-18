# Channel routing

> # Channels & routing

# 通道与路由

> OpenClaw routes replies **back to the channel where a message came from**. The model does not choose a channel; routing is deterministic and controlled by the host configuration.

OpenClaw 把回复送**回消息进来的那个通道**。模型不挑通道；路由是确定性的，由宿主配置决定。

---

> ## Key terms

## 关键术语

> * **Channel**: `telegram`, `whatsapp`, `discord`, `irc`, `googlechat`, `slack`, `signal`, `imessage`, `line`, plus plugin channels. `webchat` is the internal WebChat UI channel and is not a configurable outbound channel.
> * **AccountId**: per-channel account instance (when supported).
> * Optional channel default account: `channels.<channel>.defaultAccount` chooses which account is used when an outbound path does not specify `accountId`.
>   * In multi-account setups, set an explicit default (`defaultAccount` or `accounts.default`) when two or more accounts are configured. Without it, fallback routing may pick the first normalized account ID.
> * **AgentId**: an isolated workspace + session store ("brain").
> * **SessionKey**: the bucket key used to store context and control concurrency.

- **Channel（通道）**：`telegram`、`whatsapp`、`discord`、`irc`、`googlechat`、`slack`、`signal`、`imessage`、`line`，以及各种插件通道。`webchat` 是 OpenClaw 内置的 WebChat UI 通道，不是可配置的出向通道。
- **AccountId（账号 ID）**：每个通道下的账号实例（通道支持的话）。
- 通道级可选的默认账号：`channels.<channel>.defaultAccount` 决定发送链路没指定 `accountId` 时走哪个账号。
  - 多账号场景下，配置了两个或更多账号时，要显式设默认账号（`defaultAccount` 或 `accounts.default`）。不设的话，回退路由可能会挑到第一个归一化后的账号 ID。
- **AgentId**：一个独立的工作区 + 会话存储（"大脑"）。
- **SessionKey**：保存上下文、控制并发的桶 key。

---

> ## Outbound target prefixes

## 发送目标前缀

> Explicit outbound targets may include a provider prefix, such as `telegram:123` or `tg:123`. Core treats that prefix as a channel-selection hint only when the selected channel is `last` or otherwise unresolved, and only when the loaded plugin advertises that prefix. If the caller already selected an explicit channel, the provider prefix must match that channel; cross-channel combinations such as WhatsApp delivery to `telegram:123` fail before plugin-specific target normalization.

显式的发送目标可以带 provider 前缀，比如 `telegram:123` 或 `tg:123`。核心只在所选通道是 `last` 或还没解析时，才把这个前缀当作通道选择提示，并且要求加载的插件声明了这个前缀。调用方已经选定了具体通道时，provider 前缀必须和那个通道一致；跨通道组合比如用 WhatsApp 发到 `telegram:123` 会在插件级目标归一化之前就失败。

> Target-kind and service prefixes such as `channel:<id>`, `user:<id>`, `room:<id>`, `thread:<id>`, `imessage:<handle>`, and `sms:<number>` stay inside the selected channel's grammar. They do not select the provider by themselves.

目标类型和服务前缀（如 `channel:<id>`、`user:<id>`、`room:<id>`、`thread:<id>`、`imessage:<handle>`、`sms:<number>`）只在所选通道的语法范围内有效，本身不参与选 provider。

---

> ## Session key shapes (examples)

## Session key 的格式（示例）

> Direct messages collapse to the agent's **main** session by default:
>
> * `agent:<agentId>:<mainKey>` (default: `agent:main:main`)

私聊默认收敛到 agent 的 **main** 会话：

- `agent:<agentId>:<mainKey>`（默认 `agent:main:main`）

> Even when direct-message conversation history is shared with main, sandbox and tool policy use a derived per-account direct-chat runtime key for external DMs so channel-originated messages are not treated like local main-session runs.

即便私聊对话历史和 main 共享，沙盒和工具策略对外部私聊用的是一个派生出的、按账号区分的私聊运行时 key，这样从通道进来的消息不会被当成本地 main 会话的运行。

> Groups and channels remain isolated per channel:
>
> * Groups: `agent:<agentId>:<channel>:group:<id>`
> * Channels/rooms: `agent:<agentId>:<channel>:channel:<id>`

群和频道按通道隔离：

- 群：`agent:<agentId>:<channel>:group:<id>`
- 频道 / 房间：`agent:<agentId>:<channel>:channel:<id>`

> Threads:
>
> * Slack/Discord threads append `:thread:<threadId>` to the base key.
> * Telegram forum topics embed `:topic:<topicId>` in the group key.

话题：

- Slack / Discord 的 thread 在基础 key 后追加 `:thread:<threadId>`。
- Telegram 的 forum topic 把 `:topic:<topicId>` 嵌进群 key。

> Examples:
>
> * `agent:main:telegram:group:-1001234567890:topic:42`
> * `agent:main:discord:channel:123456:thread:987654`

例子：

- `agent:main:telegram:group:-1001234567890:topic:42`
- `agent:main:discord:channel:123456:thread:987654`

---

> ## Main DM route pinning

## main 会话的私聊路由钉定

> When `session.dmScope` is `main`, direct messages may share one main session. To prevent the session's `lastRoute` from being overwritten by non-owner DMs, OpenClaw infers a pinned owner from `allowFrom` when all of these are true:
>
> * `allowFrom` has exactly one non-wildcard entry.
> * The entry can be normalized to a concrete sender ID for that channel.
> * The inbound DM sender does not match that pinned owner.

`session.dmScope` 是 `main` 时，私聊可能共享同一个 main 会话。为了防止非所有者的私聊覆盖会话的 `lastRoute`，OpenClaw 在以下三条都成立时，从 `allowFrom` 推断出一个钉定的所有者：

- `allowFrom` 里只有一条非通配条目。
- 这条条目能归一为该通道的具体发件人 ID。
- 进来的私聊发件人和这个钉定的所有者不一致。

> In that mismatch case, OpenClaw still records inbound session metadata, but it skips updating the main session `lastRoute`.

不一致的情况下，OpenClaw 仍然记录接收侧会话元数据，但跳过更新 main 会话的 `lastRoute`。

---

> ## Guarded inbound recording

## 受保护的接收记录

> Channel plugins can mark an inbound session record as `createIfMissing: false` when a guarded path must not create a new OpenClaw session. In that mode, OpenClaw may update metadata and `lastRoute` for an existing session, but it does not create a route-only session entry just because a message was observed.

通道插件可以把接收侧会话记录标记成 `createIfMissing: false`，告诉受保护链路不要创建新的 OpenClaw 会话。这种模式下，OpenClaw 仍可以更新已有会话的元数据和 `lastRoute`，但不会因为单纯观察到一条消息就创建一条只为路由用的会话记录。

---

> ## Routing rules (how an agent is chosen)

## 路由规则（怎么选 agent）

> Routing picks **one agent** for each inbound message:

每条收到的消息，路由会挑出**一个 agent**：

> 1. **Exact peer match** (`bindings` with `peer.kind` + `peer.id`).
> 2. **Parent peer match** (thread inheritance).
> 3. **Guild + roles match** (Discord) via `guildId` + `roles`.
> 4. **Guild match** (Discord) via `guildId`.
> 5. **Team match** (Slack) via `teamId`.
> 6. **Account match** (`accountId` on the channel).
> 7. **Channel match** (any account on that channel, `accountId: "*"`).
> 8. **Default agent** (`agents.list[].default`, else first list entry, fallback to `main`).

1. **精确 peer 匹配**（`bindings` 里带 `peer.kind` + `peer.id`）。
2. **父 peer 匹配**（thread 继承）。
3. **Guild + roles 匹配**（Discord，通过 `guildId` + `roles`）。
4. **Guild 匹配**（Discord，只用 `guildId`）。
5. **Team 匹配**（Slack，通过 `teamId`）。
6. **账号匹配**（按通道下的 `accountId`）。
7. **通道匹配**（该通道下任意账号，`accountId: "*"`）。
8. **默认 agent**（`agents.list[].default`，没有就用列表第一个，再不行回退到 `main`）。

> When a binding includes multiple match fields (`peer`, `guildId`, `teamId`, `roles`), **all provided fields must match** for that binding to apply.

一条绑定同时写了多个匹配字段（`peer`、`guildId`、`teamId`、`roles`）时，**所有提供的字段都必须匹配**，这条绑定才生效。

> The matched agent determines which workspace and session store are used.

匹配到的 agent 决定走哪个工作区和会话存储。

---

> ## Broadcast groups (run multiple agents)

## 广播组（同时跑多个 agent）

> Broadcast groups let you run **multiple agents** for the same peer **when OpenClaw would normally reply** (for example: in WhatsApp groups, after mention/activation gating).

广播组让你在**原本 OpenClaw 会回复的时机**（比如 WhatsApp 群里通过了 @ 触发、激活规则之后），对同一个 peer 跑**多个 agent**。

> Config:

配置：

> ```json5
> {
>   broadcast: {
>     strategy: "parallel",
>     "120363403215116621@g.us": ["alfred", "baerbel"],
>     "+15555550123": ["support", "logger"],
>   },
> }
> ```

```json5
{
  broadcast: {
    strategy: "parallel",
    "120363403215116621@g.us": ["alfred", "baerbel"],
    "+15555550123": ["support", "logger"],
  },
}
```

> See: [Broadcast Groups](/channels/broadcast-groups).

详见：[广播组](/channels/broadcast-groups)。

---

> ## Config overview

## 配置概览

> * `agents.list`: named agent definitions (workspace, model, etc.).
> * `bindings`: map inbound channels/accounts/peers to agents.

- `agents.list`：命名的 agent 定义（工作区、模型等）。
- `bindings`：把进来的通道 / 账号 / peer 映射到 agent。

> Example:

例子：

> ```json5
> {
>   agents: {
>     list: [{ id: "support", name: "Support", workspace: "~/.openclaw/workspace-support" }],
>   },
>   bindings: [
>     { match: { channel: "slack", teamId: "T123" }, agentId: "support" },
>     { match: { channel: "telegram", peer: { kind: "group", id: "-100123" } }, agentId: "support" },
>   ],
> }
> ```

```json5
{
  agents: {
    list: [{ id: "support", name: "Support", workspace: "~/.openclaw/workspace-support" }],
  },
  bindings: [
    { match: { channel: "slack", teamId: "T123" }, agentId: "support" },
    { match: { channel: "telegram", peer: { kind: "group", id: "-100123" } }, agentId: "support" },
  ],
}
```

---

> ## Session storage

## 会话存储

> Session stores live under the state directory (default `~/.openclaw`):
>
> * `~/.openclaw/agents/<agentId>/sessions/sessions.json`
> * JSONL transcripts live alongside the store

会话存储放在状态目录下（默认 `~/.openclaw`）：

- `~/.openclaw/agents/<agentId>/sessions/sessions.json`
- JSONL 格式的对话记录就放在它旁边

> You can override the store path via `session.store` and `{agentId}` templating.

可以通过 `session.store` 加 `{agentId}` 模板覆盖存储路径。

> Gateway and ACP session discovery also scans disk-backed agent stores under the default `agents/` root and under templated `session.store` roots. Discovered stores must stay inside that resolved agent root and use a regular `sessions.json` file. Symlinks and out-of-root paths are ignored.

Gateway 和 ACP 在做会话发现时，也会扫默认的 `agents/` 根目录和模板化的 `session.store` 根目录下的磁盘 agent 存储。发现到的存储必须落在解析出来的 agent 根目录范围内，且是普通文件 `sessions.json`。符号链接和根目录之外的路径会被忽略。

---

> ## WebChat behavior

## WebChat 行为

> WebChat attaches to the **selected agent** and defaults to the agent's main session. Because of this, WebChat lets you see cross-channel context for that agent in one place.

WebChat 挂到**选中的 agent** 上，默认进 agent 的 main 会话。所以在 WebChat 里能在一处看到这个 agent 跨通道的上下文。

---

> ## Reply context

## 回复上下文

> Inbound replies include:
>
> * `ReplyToId`, `ReplyToBody`, and `ReplyToSender` when available.
> * Quoted context is appended to `Body` as a `[Replying to ...]` block.

进来的回复消息包含：

- `ReplyToId`、`ReplyToBody`、`ReplyToSender`（有的话）。
- 引用上下文以 `[Replying to ...]` 块形式追加到 `Body`。

> This is consistent across channels.

所有通道在这一点上保持一致。

---

> ## Related

## 相关

> * [Groups](/channels/groups)
> * [Broadcast groups](/channels/broadcast-groups)
> * [Pairing](/channels/pairing)

- [群组](/channels/groups)
- [广播组](/channels/broadcast-groups)
- [配对](/channels/pairing)
