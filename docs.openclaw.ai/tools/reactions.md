# Reactions

> The agent can add and remove emoji reactions on messages using the `message`
> tool with the `react` action. Reaction behavior varies by channel and transport.

agent 用 `message` 工具的 `react` 动作给消息加或撤掉表情反应。反应行为各通道、各传输不同。

## 怎么工作的

```json
{
  "action": "react",
  "messageId": "msg-123",
  "emoji": "thumbsup"
}
```

> - `emoji` is required when adding a reaction.
> - Set `emoji` to an empty string (`""`) to remove the bot's reaction(s).
> - Set `remove: true` to remove a specific emoji (requires non-empty `emoji`).
> - On channels that support status reactions, `trackToolCalls: true` on a
>   reaction lets the runtime use that reacted message for subsequent tool
>   progress reactions during the same turn.

- 加反应时 `emoji` 必填。
- `emoji` 设成空字符串(`""`)撤掉 bot 自己的反应。
- 设 `remove: true` 撤掉某个具体的 emoji(此时 `emoji` 仍要非空)。
- 在支持状态反应的通道上,反应里设 `trackToolCalls: true`,运行时会把这条被反应的消息作为同一轮里后续工具进度反应的载体。

## 各通道行为

> <Accordion title="Discord and Slack">
>     - Empty `emoji` removes all of the bot's reactions on the message.
>     - `remove: true` removes just the specified emoji.

[展开: Discord 和 Slack]

- 空 `emoji` 撤掉 bot 在该消息上的所有反应。
- `remove: true` 只撤掉指定的 emoji。

> <Accordion title="Google Chat">
>     - Empty `emoji` removes the app's reactions on the message.
>     - `remove: true` removes just the specified emoji.

[展开: Google Chat]

- 空 `emoji` 撤掉 app 在该消息上的反应。
- `remove: true` 只撤掉指定的 emoji。

> <Accordion title="Nextcloud Talk">
>     - Adding reactions only: `emoji` is required and must be non-empty.
>     - Reaction removal is not supported yet; calls with `remove: true` (or empty `emoji`) are rejected with a clear error rather than silently no-oping.
>     - Requires the Talk bot to be registered with the `reaction` feature (see [Nextcloud Talk channel docs](/channels/nextcloud-talk)).

[展开: Nextcloud Talk]

- 只支持加反应:`emoji` 必填且非空。
- 撤反应暂不支持;带 `remove: true`(或空 `emoji`)的调用会被明确拒绝并报错,而不是默默不执行。
- Talk bot 必须注册了 `reaction` 特性(见 [Nextcloud Talk 通道文档](/channels/nextcloud-talk))。

> <Accordion title="Telegram">
>     - Empty `emoji` removes the bot's reactions.
>     - `remove: true` also removes reactions but still requires a non-empty `emoji` for tool validation.

[展开: Telegram]

- 空 `emoji` 撤掉 bot 的反应。
- `remove: true` 也撤反应,但工具校验仍要求 `emoji` 非空。

> <Accordion title="WhatsApp">
>     - Empty `emoji` removes the bot reaction.
>     - `remove: true` maps to empty emoji internally (still requires `emoji` in the tool call).
>     - WhatsApp has one bot reaction slot per message; status reaction updates replace that slot rather than stacking multiple emoji.

[展开: WhatsApp]

- 空 `emoji` 撤掉 bot 反应。
- `remove: true` 内部映射成空 emoji(工具调用里仍要给 `emoji`)。
- WhatsApp 每条消息只有一个 bot 反应槽;状态反应更新会替换这个槽,不会堆多个 emoji。

> <Accordion title="Zalo Personal (zalouser)">
>     - Requires non-empty `emoji`.
>     - `remove: true` removes that specific emoji reaction.

[展开: Zalo Personal (zalouser)]

- 要求 `emoji` 非空。
- `remove: true` 撤掉这个具体 emoji 的反应。

> <Accordion title="Feishu/Lark">
>     - Use the `feishu_reaction` tool with actions `add`, `remove`, and `list`.
>     - Add/remove requires `emoji_type`; remove also requires `reaction_id`.

[展开: 飞书 / Lark]

- 用 `feishu_reaction` 工具,动作为 `add`、`remove`、`list`。
- 加 / 撤都要 `emoji_type`;撤还要 `reaction_id`。

> <Accordion title="Signal">
>     - Inbound reaction notifications are controlled by `channels.signal.reactionNotifications`: `"off"` disables them, `"own"` (default) emits events when users react to bot messages, and `"all"` emits events for all reactions.

[展开: Signal]

- 入站反应通知由 `channels.signal.reactionNotifications` 控制:`"off"` 关掉;`"own"`(默认)只在用户对 bot 消息反应时发事件;`"all"` 所有反应都发事件。

> <Accordion title="iMessage">
>     - Outbound reactions are iMessage tapbacks (`love`, `like`, `dislike`, `laugh`, `emphasize`, and `question`).
>     - Inbound tapback notifications are controlled by `channels.imessage.reactionNotifications`: `"off"` disables them, `"own"` (default) emits events when users react to bot-authored messages, and `"all"` emits events for all tapbacks from authorized senders.

[展开: iMessage]

- 出站反应是 iMessage 的 tapback(`love`、`like`、`dislike`、`laugh`、`emphasize`、`question`)。
- 入站 tapback 通知由 `channels.imessage.reactionNotifications` 控制:`"off"` 关掉;`"own"`(默认)只在用户对 bot 发的消息做 tapback 时发事件;`"all"` 来自授权发送者的所有 tapback 都发事件。

## 反应级别

> Per-channel `reactionLevel` config controls how broadly the agent uses reactions. Values are typically `off`, `ack`, `minimal`, or `extensive`.

按通道的 `reactionLevel` 配置控制 agent 多大程度用反应。取值通常是 `off`、`ack`、`minimal`、`extensive`。

> - [Telegram reactionLevel](/channels/telegram#reaction-notifications) — `channels.telegram.reactionLevel`
> - [WhatsApp reactionLevel](/channels/whatsapp#reaction-level) — `channels.whatsapp.reactionLevel`

- [Telegram reactionLevel](/channels/telegram#reaction-notifications) — `channels.telegram.reactionLevel`
- [WhatsApp reactionLevel](/channels/whatsapp#reaction-level) — `channels.whatsapp.reactionLevel`

> Set `reactionLevel` on individual channels to tune how actively the agent reacts to messages on each platform.

在各个通道上设 `reactionLevel`,调每个平台上 agent 反应的活跃度。

## 相关

> - [Agent Send](/tools/agent-send) — the `message` tool that includes `react`
> - [Channels](/channels) — channel-specific configuration

- [Agent Send](/tools/agent-send) —— 含 `react` 的 `message` 工具
- [通道](/channels) —— 各通道的配置
