# WhatsApp group messages

> For the cross-channel groups model (Discord, iMessage, Matrix, Microsoft Teams, Signal, Slack, Telegram, WhatsApp, Zalo), see [Groups](/channels/groups). This page covers the WhatsApp-specific behavior on top of that model: activation, group allowlists, per-group session keys, and pending-message context injection.

跨通道的群模型（Discord、iMessage、Matrix、Microsoft Teams、Signal、Slack、Telegram、WhatsApp、Zalo）见 [Groups](/channels/groups)。本页讲 WhatsApp 在那个通用模型之上的特有行为：激活模式、群白名单、每个群独立的会话 key、待处理消息的上下文注入。

> Goal: let OpenClaw sit in WhatsApp groups, wake up only when pinged, and keep that thread separate from the personal DM session.

目标：让 OpenClaw 待在 WhatsApp 群里，只有被点名时才回应，且这条群对话和个人私聊会话各走各的。

> <Note>
>   `agents.list[].groupChat.mentionPatterns` is also used by Telegram, Discord, Slack, and iMessage. For multi-agent setups, set it per agent, or use `messages.groupChat.mentionPatterns` as a global fallback.
> </Note>

> **提示**：`agents.list[].groupChat.mentionPatterns` 这个字段在 Telegram、Discord、Slack、iMessage 也用。多 agent 部署时，按 agent 单独配；或者用 `messages.groupChat.mentionPatterns` 作为全局回退。

---

> ## Behavior

## 行为

> * Activation modes: `mention` (default) or `always`. `mention` requires a ping (real WhatsApp @-mentions via `mentionedJids`, safe regex patterns, or the bot's E.164 anywhere in the text). `always` wakes the agent on every message but it should reply only when it can add meaningful value; otherwise it returns the exact silent token `NO_REPLY` / `no_reply`. Defaults can be set in config (`channels.whatsapp.groups`) and overridden per group via `/activation`. When `channels.whatsapp.groups` is set, it also acts as a group allowlist (include `"*"` to allow all).

- **激活模式**：`mention`（默认）或 `always`。`mention` 必须被点名才回（真正的 WhatsApp `mentionedJids` @ 提及、安全的正则匹配、或者文本里出现机器人 E.164 号码）。`always` 每条消息都唤醒 agent，但 agent 只在确实能补充有价值的内容时才回；否则要返回精确的静默 token `NO_REPLY` / `no_reply`。默认值在配置里设（`channels.whatsapp.groups`），单个群可以用 `/activation` 覆盖。`channels.whatsapp.groups` 配置后，它同时充当群白名单（写 `"*"` 表示允许所有群）。

> * Group policy: `channels.whatsapp.groupPolicy` controls whether group messages are accepted (`open|disabled|allowlist`). `allowlist` uses `channels.whatsapp.groupAllowFrom` (fallback: explicit `channels.whatsapp.allowFrom`). Default is `allowlist` (blocked until you add senders).

- **群策略**：`channels.whatsapp.groupPolicy` 控制群消息收不收（`open|disabled|allowlist`）。`allowlist` 模式下查 `channels.whatsapp.groupAllowFrom`（没设的话回退到显式的 `channels.whatsapp.allowFrom`）。默认值是 `allowlist`（你不加发件人就一直拦着）。

> * Per-group sessions: session keys look like `agent:<agentId>:whatsapp:group:<jid>` so commands such as `/verbose on`, `/trace on`, or `/think high` (sent as standalone messages) are scoped to that group; personal DM state is untouched. Heartbeats are skipped for group threads.

- **每个群独立会话**：会话 key 形如 `agent:<agentId>:whatsapp:group:<jid>`。所以 `/verbose on`、`/trace on`、`/think high` 这种命令（独立消息发出）只作用于那个群；个人私聊状态不受影响。群对话不发心跳。

> * Context injection: **pending-only** group messages (default 50) that *did not* trigger a run are prefixed under `[Chat messages since your last reply - for context]`, with the triggering line under `[Current message - respond to this]`. Messages already in the session are not re-injected.

- **上下文注入**：那些**没有触发运行**的群消息（默认最多 50 条）会带 `[Chat messages since your last reply - for context]` 前缀注入，触发的那条挂在 `[Current message - respond to this]` 下面。会话里已经有的消息不会再次注入。

> * Sender surfacing: every group batch now ends with `[from: Sender Name (+E164)]` so Pi knows who is speaking.

- **发件人露出**：每个群消息批次末尾会附上 `[from: 发件人名字 (+E164)]`，让 Pi 知道是谁在说话。

> * Ephemeral/view-once: we unwrap those before extracting text/mentions, so pings inside them still trigger.

- **限时消息 / 阅后即焚**：在提取文本和 @ 提及之前会先解包，里面的点名仍然能触发。

> * Group system prompt: on the first turn of a group session (and whenever `/activation` changes the mode) we inject a short blurb into the system prompt like `You are replying inside the WhatsApp group "<subject>". Group members: Alice (+44...), Bob (+43...), ... Activation: trigger-only ... Address the specific sender noted in the message context.` If metadata isn't available we still tell the agent it's a group chat.

- **群专属系统提示词**：群会话的第一轮（以及每次 `/activation` 切换激活模式时），系统提示词里会注入一小段，类似 `You are replying inside the WhatsApp group "<subject>". Group members: Alice (+44...), Bob (+43...), ... Activation: trigger-only ... Address the specific sender noted in the message context.`。即便拿不到群元数据，也会告诉 agent 当前是群聊。

---

> ## Config example (WhatsApp)

## 配置示例（WhatsApp）

> Add a `groupChat` block to `~/.openclaw/openclaw.json` so display-name pings work even when WhatsApp strips the visual `@` in the text body:

在 `~/.openclaw/openclaw.json` 里加一个 `groupChat` 块，这样即便 WhatsApp 把文本里可见的 `@` 去掉，按显示名 / 号码点名也能识别：

> ```json5
> {
>   channels: {
>     whatsapp: {
>       groups: {
>         "*": { requireMention: true },
>       },
>     },
>   },
>   agents: {
>     list: [
>       {
>         id: "main",
>         groupChat: {
>           historyLimit: 50,
>           mentionPatterns: ["@?openclaw", "\\+?15555550123"],
>         },
>       },
>     ],
>   },
> }
> ```

```json5
{
  channels: {
    whatsapp: {
      groups: {
        "*": { requireMention: true },
      },
    },
  },
  agents: {
    list: [
      {
        id: "main",
        groupChat: {
          historyLimit: 50,
          mentionPatterns: ["@?openclaw", "\\+?15555550123"],
        },
      },
    ],
  },
}
```

> Notes:
>
> * The regexes are case-insensitive and use the same safe-regex guardrails as other config regex surfaces; invalid patterns and unsafe nested repetition are ignored.
> * WhatsApp still sends canonical mentions via `mentionedJids` when someone taps the contact, so the number fallback is rarely needed but is a useful safety net.

注意：

- 正则不区分大小写，用的安全护栏跟其他配置里的正则一致；非法模式和不安全的嵌套重复会被忽略。
- 用户点联系人 @ 时，WhatsApp 仍然走 `mentionedJids` 字段发标准的 @ 提及，所以基于号码的回退很少用得到，但留着兜底。

---

> ### Activation command (owner-only)

### 切换激活模式的命令（只有所有者能用）

> Use the group chat command:
>
> * `/activation mention`
> * `/activation always`

群聊里发：

- `/activation mention`
- `/activation always`

> Only the owner number (from `channels.whatsapp.allowFrom`, or the bot's own E.164 when unset) can change this. Send `/status` as a standalone message in the group to see the current activation mode.

只有所有者号码（来自 `channels.whatsapp.allowFrom`，没设就用机器人自己的 E.164）能切换激活模式。在群里独立发一条 `/status`，可以看到当前激活模式。

---

> ## How to use

## 用法

> 1. Add your WhatsApp account (the one running OpenClaw) to the group.
> 2. Say `@openclaw …` (or include the number). Only allowlisted senders can trigger it unless you set `groupPolicy: "open"`.
> 3. The agent prompt will include recent group context plus the trailing `[from: …]` marker so it can address the right person.
> 4. Session-level directives (`/verbose on`, `/trace on`, `/think high`, `/new` or `/reset`, `/compact`) apply only to that group's session; send them as standalone messages so they register. Your personal DM session remains independent.

1. 把跑 OpenClaw 的那个 WhatsApp 账号加进群。
2. 在群里说 `@openclaw ……`（或者把号码写进去）。除非把 `groupPolicy` 设成 `"open"`，否则只有白名单里的发件人能触发。
3. agent 的提示词里会带上最近的群上下文，外加末尾的 `[from: …]` 标记，方便它对应到具体的人。
4. 会话级别的指令（`/verbose on`、`/trace on`、`/think high`、`/new` 或 `/reset`、`/compact`）只作用于这个群的会话；要让它们生效，必须独立发一条消息。你的个人私聊会话不会被影响。

---

> ## Testing / verification

## 测试与验证

> * Manual smoke:
>   * Send an `@openclaw` ping in the group and confirm a reply that references the sender name.
>   * Send a second ping and verify the history block is included then cleared on the next turn.
> * Check gateway logs (run with `--verbose`) to see `inbound web message` entries showing `from: <groupJid>` and the `[from: …]` suffix.

- 手工冒烟：
  - 在群里发一条 `@openclaw` 点名，确认回复里提到了发件人名字。
  - 再发一次点名，确认历史块被注入了，且在下一轮被清空。
- 看 Gateway 日志（用 `--verbose` 启动），里面 `inbound web message` 条目会显示 `from: <groupJid>` 和 `[from: …]` 后缀。

---

> ## Known considerations

## 已知注意事项

> * Heartbeats are intentionally skipped for groups to avoid noisy broadcasts.
> * Echo suppression uses the combined batch string; if you send identical text twice without mentions, only the first will get a response.
> * Session store entries will appear as `agent:<agentId>:whatsapp:group:<jid>` in the session store (`~/.openclaw/agents/<agentId>/sessions/sessions.json` by default); a missing entry just means the group hasn't triggered a run yet.
> * Typing indicators in groups follow `agents.defaults.typingMode`. When visible replies use the default message-tool-only mode, typing starts immediately by default so group members can see the agent is working even if no automatic final reply is posted. Explicit typing-mode config still wins.

- 群里有意不发心跳，避免群聊被噪音刷屏。
- 回声抑制用的是合并后的批次字符串；连续两次发同样的文本且都没 @，只有第一次会回。
- 会话存储里的条目格式是 `agent:<agentId>:whatsapp:group:<jid>`（默认存在 `~/.openclaw/agents/<agentId>/sessions/sessions.json`）。看不到对应条目，只是说明这个群还没触发过运行。
- 群里的"输入中"状态跟随 `agents.defaults.typingMode`。在默认的 message-tool-only 可见回复模式下，输入中状态会立即开始，让群成员看见 agent 正在工作 —— 哪怕这一轮没有自动发出最终回复。显式的 typing-mode 配置优先级仍然更高。

---

> ## Related

## 相关

> * [Groups](/channels/groups)
> * [Channel routing](/channels/channel-routing)
> * [Broadcast groups](/channels/broadcast-groups)

- [群组](/channels/groups)
- [通道路由](/channels/channel-routing)
- [广播组](/channels/broadcast-groups)
