# Channel docking

> Channel docking is call forwarding for one OpenClaw session.

通道 dock 相当于给一个 OpenClaw 会话做"呼叫转移"。

> It keeps the same conversation context, but changes where future replies for that session are delivered.

它保留同一份对话上下文，但改变这个会话之后的回复送到哪里。

---

> ## Example

## 例子

> Alice can message OpenClaw on Telegram and Discord:

Alice 可以从 Telegram 和 Discord 给 OpenClaw 发消息：

> ```json5
> {
>   session: {
>     identityLinks: {
>       alice: ["telegram:123", "discord:456"],
>     },
>   },
> }
> ```

```json5
{
  session: {
    identityLinks: {
      alice: ["telegram:123", "discord:456"],
    },
  },
}
```

> If Alice sends this from Telegram:
>
> ```text
> /dock_discord
> ```

Alice 在 Telegram 里发：

```text
/dock_discord
```

> OpenClaw keeps the current session context and changes the reply route:

OpenClaw 保留当前会话上下文，把回复路由改了：

> | Before docking               | After `/dock_discord`       |
> | ---------------------------- | --------------------------- |
> | Replies go to Telegram `123` | Replies go to Discord `456` |

| dock 之前                    | `/dock_discord` 之后        |
| ---------------------------- | --------------------------- |
| 回复发到 Telegram `123`      | 回复发到 Discord `456`      |

> The session is not recreated. The transcript history stays attached to the same session.

会话不会被重建。transcript 历史仍挂在同一个会话上。

---

> ## Why use it

## 为什么用它

> Use docking when a task starts in one chat app but the next replies should land somewhere else.

某个任务在一个聊天 App 起头、之后的回复要落到另一个地方时，用 dock。

> Common flow:
>
> 1. Start an agent task from Telegram.
> 2. Move to Discord where you are coordinating work.
> 3. Send `/dock_discord` from the Telegram session.
> 4. Keep the same OpenClaw session, but receive future replies in Discord.

常见流程：

1. 在 Telegram 里给 agent 起一项任务。
2. 你转去 Discord 做协调。
3. 在 Telegram 那个会话里发 `/dock_discord`。
4. 保留同一个 OpenClaw 会话，之后的回复在 Discord 收。

---

> ## Required config

## 必需的配置

> Docking requires `session.identityLinks`. The source sender and target peer must be in the same identity group:

dock 需要 `session.identityLinks`。源发件人和目标 peer 必须在同一个身份组里：

> ```json5
> {
>   session: {
>     identityLinks: {
>       alice: ["telegram:123", "discord:456", "slack:U123"],
>     },
>   },
> }
> ```

```json5
{
  session: {
    identityLinks: {
      alice: ["telegram:123", "discord:456", "slack:U123"],
    },
  },
}
```

> The values are channel-prefixed peer ids:
>
> | Value          | Meaning                      |
> | -------------- | ---------------------------- |
> | `telegram:123` | Telegram sender id `123`     |
> | `discord:456`  | Discord direct peer id `456` |
> | `slack:U123`   | Slack user id `U123`         |

值是带通道前缀的 peer id：

| 值             | 含义                            |
| -------------- | ------------------------------- |
| `telegram:123` | Telegram 发件人 id `123`        |
| `discord:456`  | Discord 私聊 peer id `456`      |
| `slack:U123`   | Slack 用户 id `U123`            |

> The canonical key (`alice` above) is only the shared identity group name. Dock commands use the channel-prefixed values to prove that the source sender and target peer are the same person.

权威 key（上面是 `alice`）只是共享身份组的名字。dock 命令用带通道前缀的值来证明源发件人和目标 peer 是同一个人。

---

> ## Commands

## 命令

> Dock commands are generated from loaded channel plugins that support native commands. Current bundled commands:

dock 命令由已加载、支持原生命令的通道插件生成。当前内置命令：

> | Target channel | Command            | Alias              |
> | -------------- | ------------------ | ------------------ |
> | Discord        | `/dock-discord`    | `/dock_discord`    |
> | Mattermost     | `/dock-mattermost` | `/dock_mattermost` |
> | Slack          | `/dock-slack`      | `/dock_slack`      |
> | Telegram       | `/dock-telegram`   | `/dock_telegram`   |

| 目标通道       | 命令               | 别名               |
| -------------- | ------------------ | ------------------ |
| Discord        | `/dock-discord`    | `/dock_discord`    |
| Mattermost     | `/dock-mattermost` | `/dock_mattermost` |
| Slack          | `/dock-slack`      | `/dock_slack`      |
| Telegram       | `/dock-telegram`   | `/dock_telegram`   |

> The underscore aliases are useful on native command surfaces such as Telegram.

下划线别名在 Telegram 这种原生命令面上好用。

---

> ## What changes

## 改了什么

> Docking updates the active session delivery fields:

dock 更新当前会话的投递字段：

> | Session field   | Example after `/dock_discord`            |
> | --------------- | ---------------------------------------- |
> | `lastChannel`   | `discord`                                |
> | `lastTo`        | `456`                                    |
> | `lastAccountId` | the target channel account, or `default` |

| 会话字段         | `/dock_discord` 之后的例子              |
| ---------------- | --------------------------------------- |
| `lastChannel`    | `discord`                               |
| `lastTo`         | `456`                                   |
| `lastAccountId`  | 目标通道账号，或 `default`              |

> Those fields are persisted in the session store and used by later reply delivery for that session.

这些字段会持久化到会话存储里，该会话后续回复投递时使用。

---

> ## What does not change

## 没改什么

> Docking does not:
>
> * create channel accounts
> * connect a new Discord, Telegram, Slack, or Mattermost bot
> * grant access to a user
> * bypass channel allowlists or DM policies
> * move transcript history to another session
> * make unrelated users share a session

dock **不会**：

- 创建通道账号
- 接入新的 Discord、Telegram、Slack 或 Mattermost bot
- 给某个用户授权
- 绕过通道白名单或 DM 策略
- 把 transcript 历史挪到另一个会话
- 让不相关的用户共用一个会话

> It only changes the delivery route for the current session.

它只改当前会话的投递路由。

---

> ## Troubleshooting

## 故障排查

> **The command says the sender is not linked.**

**命令说发件人没链接。**

> Add both the current sender and the target peer to the same `session.identityLinks` group. For example, if Telegram sender `123` should dock to Discord peer `456`, include both `telegram:123` and `discord:456`.

把当前发件人和目标 peer 都加到同一个 `session.identityLinks` 组里。比如 Telegram 发件人 `123` 要 dock 到 Discord peer `456`，把 `telegram:123` 和 `discord:456` 都写进去。

> **The command says no active session exists.**

**命令说没有活动会话。**

> Dock from an existing direct-chat session. The command needs an active session entry so it can persist the new route.

从一个已有的私聊会话里发 dock。命令需要一个活动会话条目才能持久化新路由。

> **Replies still go to the old channel.**

**回复还是发到旧通道。**

> Check that the command replied with a success message, and confirm the target peer id matches the id used by that channel. Docking only changes the active session route; another session may still route elsewhere.

确认命令回了成功消息，确认目标 peer id 跟那个通道里用的 id 一致。dock 只改当前会话路由；另一个会话可能仍然路由到别处。

> **I need to switch back.**

**我要切回去。**

> Send the matching command for the original channel, such as `/dock_telegram` or `/dock-telegram`, from a linked sender.

从一个已链接的发件人那里发对应原通道的命令，比如 `/dock_telegram` 或 `/dock-telegram`。
