# Groups

> OpenClaw treats group chats consistently across surfaces: Discord, iMessage, Matrix, Microsoft Teams, Signal, Slack, Telegram, WhatsApp, Zalo.

OpenClaw 在所有支持群聊的通道上行为一致：Discord、iMessage、Matrix、Microsoft Teams、Signal、Slack、Telegram、WhatsApp、Zalo。

---

> ## Beginner intro (2 minutes)

## 新手入门（2 分钟）

> OpenClaw "lives" on your own messaging accounts. There is no separate WhatsApp bot user. If **you** are in a group, OpenClaw can see that group and respond there.

OpenClaw 是"挂"在你自己的消息账号上的。没有独立的 WhatsApp 机器人账号。**你**在哪个群里，OpenClaw 就能看到那个群、在那里回应。

> Default behavior:
>
> * Groups are restricted (`groupPolicy: "allowlist"`).
> * Replies require a mention unless you explicitly disable mention gating.
> * Normal final replies in groups/channels are private by default. Visible room output uses the `message` tool.

默认行为：

- 群是受限的（`groupPolicy: "allowlist"`）。
- 除非显式关掉 @ 触发，否则要回复必须先 @。
- 群 / 频道里的最终回复默认是私有的（agent 自己看得到，群里看不到）。要让群里看到内容，agent 得调 `message` 工具。

> Translation: allowlisted senders can trigger OpenClaw by mentioning it.

简单说：白名单里的发件人 @ 一下 OpenClaw 就能触发。

> <Note>
>   **TL;DR**
>
>   * **DM access** is controlled by `*.allowFrom`.
>   * **Group access** is controlled by `*.groupPolicy` + allowlists (`*.groups`, `*.groupAllowFrom`).
>   * **Reply triggering** is controlled by mention gating (`requireMention`, `/activation`).
> </Note>

> **提示 — 一句话总结**：
>
> - **私聊访问**由 `*.allowFrom` 控制。
> - **群访问**由 `*.groupPolicy` + 白名单（`*.groups`、`*.groupAllowFrom`）控制。
> - **触发回复**由 @ 门控（`requireMention`、`/activation`）控制。

> Quick flow (what happens to a group message):

群消息的处理流程：

> ```
> groupPolicy? disabled -> drop
> groupPolicy? allowlist -> group allowed? no -> drop
> requireMention? yes -> mentioned? no -> store for context only
> mention/reply/command/DM -> user request
> always-on group chatter -> user request, or room event when configured
> ```

```
groupPolicy 为 disabled？     -> 丢弃
groupPolicy 为 allowlist？    -> 群在白名单里？不是 -> 丢弃
requireMention？              -> @ 了机器人？没 @  -> 只存为上下文
@ / 回复 / 命令 / 私聊        -> 算用户请求
always-on 群里的普通发言       -> 算用户请求；配置后也可以走房间事件
```

---

> ## Visible replies

## 可见回复

> For group/channel rooms, OpenClaw defaults to `messages.groupChat.visibleReplies: "message_tool"`.
> `openclaw doctor --fix` writes this default into configured-channel configs that omit it.
> That means the agent still processes the turn and can update memory/session state, but its normal final answer is not automatically posted back into the room. To speak visibly, the agent uses `message(action=send)`.

群 / 频道里 OpenClaw 默认 `messages.groupChat.visibleReplies: "message_tool"`。已配置但漏写这个字段的通道，`openclaw doctor --fix` 会把默认值补上。意思是：agent 照样处理这一轮、更新记忆 / 会话状态，但它的最终回答不会自动发回群里。想让群里看见，agent 要调 `message(action=send)`。

> This default depends on a model/runtime that reliably calls tools. If logs show assistant text but `didSendViaMessagingTool: false`, the model answered privately instead of calling the message tool. That is not a Discord/Slack/Telegram send failure. Use a tool-call-reliable model for group/channel sessions, or set `messages.groupChat.visibleReplies: "automatic"` to restore legacy visible final replies for group requests.

这个默认值依赖能稳定调工具的模型 / 运行时。日志里看到 assistant 文本但 `didSendViaMessagingTool: false`，说明模型私下回复了，没调消息工具。这不是 Discord / Slack / Telegram 的发送失败。给群 / 频道会话换一个调工具靠谱的模型；或者把 `messages.groupChat.visibleReplies` 设回 `"automatic"`，恢复旧的"群请求自动可见回复"行为。

> If the message tool is unavailable under the active tool policy, OpenClaw falls back to automatic visible replies instead of silently suppressing the response. `openclaw doctor` warns about this mismatch.

当前工具策略下消息工具不可用时，OpenClaw 会回退到自动可见回复，而不是静默吞掉响应。`openclaw doctor` 会就这种不一致发出警告。

> For direct chats and any other source turn, use `messages.visibleReplies: "message_tool"` to apply the same tool-only visible-reply behavior globally. Harnesses can also choose this as their unset default; the Codex harness does this for Codex-mode direct chats. `messages.groupChat.visibleReplies` remains the more specific override for group/channel rooms.

要把"只通过工具发可见回复"的行为推广到私聊及其他所有来源，把 `messages.visibleReplies` 设成 `"message_tool"`。Harness 也可以把这个当作它的默认值；Codex harness 在 Codex-mode 私聊里就是这么做的。`messages.groupChat.visibleReplies` 是更具体的覆盖配置，针对群 / 频道。

> This replaces the old pattern of forcing the model to answer `NO_REPLY` for most lurk-mode turns. In tool-only mode, doing nothing visible simply means not calling the message tool.

这种模式取代了过去那种"潜伏模式下让模型每轮回 `NO_REPLY`"的做法。在 tool-only 模式下，不发可见内容只意味着不调消息工具。

> Typing indicators are still sent for direct group requests. Ambient always-on room events, when enabled, stay quiet unless the agent calls the message tool.

直接的群请求仍然会发"输入中"指示。开启的环境型 always-on 房间事件保持安静，除非 agent 主动调消息工具。

> To submit always-on ambient group chatter as quiet room context instead of legacy user requests:

要把 always-on 群里的环境闲聊以"安静的房间上下文"形式提交，而不是当作旧式用户请求：

> ```json5
> {
>   messages: {
>     groupChat: {
>       ambientTurns: "room_event",
>     },
>   },
> }
> ```

```json5
{
  messages: {
    groupChat: {
      ambientTurns: "room_event",
    },
  },
}
```

> The default is `ambientTurns: "user_request"` for compatibility.

兼容性考虑，默认值是 `ambientTurns: "user_request"`。

> To restore legacy automatic final replies for group/channel requests:

要恢复旧的"群 / 频道请求自动发最终回复"行为：

> ```json5
> {
>   messages: {
>     groupChat: {
>       visibleReplies: "automatic",
>     },
>   },
> }
> ```

```json5
{
  messages: {
    groupChat: {
      visibleReplies: "automatic",
    },
  },
}
```

> The gateway hot-reloads `messages` config after the file is saved. Restart only when file watching or config reload is disabled in the deployment.

`messages` 配置保存后，Gateway 会热加载。只有在部署里关掉文件监听或配置热加载时，才需要重启。

> To require visible output to go through the message tool for every source chat:

要求所有来源对话都通过消息工具发可见输出：

> ```json5
> {
>   messages: {
>     visibleReplies: "message_tool",
>   },
> }
> ```

```json5
{
  messages: {
    visibleReplies: "message_tool",
  },
}
```

> Native slash commands (Discord, Telegram, and other surfaces with native command support) bypass `visibleReplies: "message_tool"` and always reply visibly so the channel-native command UI gets the response it expects. This applies to validated native command turns only; text-typed `/...` commands and ordinary chat turns still follow the configured group default.

原生斜杠命令（Discord、Telegram 等支持原生命令的通道）会绕过 `visibleReplies: "message_tool"`，始终可见地回复，让通道原生命令 UI 拿到它预期的响应。这只对通过校验的原生命令轮次生效；纯文本输入的 `/...` 命令和普通聊天仍然按配置的群默认走。

---

> ## Context visibility and allowlists

## 上下文可见性和白名单

> Two different controls are involved in group safety:
>
> * **Trigger authorization**: who can trigger the agent (`groupPolicy`, `groups`, `groupAllowFrom`, channel-specific allowlists).
> * **Context visibility**: what supplemental context is injected into the model (reply text, quotes, thread history, forwarded metadata).

群的安全模型有两套控制：

- **触发授权**：谁能触发 agent（`groupPolicy`、`groups`、`groupAllowFrom`、各通道自己的白名单）。
- **上下文可见性**：哪些补充上下文会注入给模型（回复文本、引用、话题历史、转发的元数据）。

> By default, OpenClaw prioritizes normal chat behavior and keeps context mostly as received. This means allowlists primarily decide who can trigger actions, not a universal redaction boundary for every quoted or historical snippet.

OpenClaw 默认偏向"按正常聊天行为来"，上下文基本按接收时的样子保留。也就是说，白名单主要决定谁能触发动作，并不是对每一条引用 / 历史片段做统一脱敏的边界。

> <AccordionGroup>
>   <Accordion title="Current behavior is channel-specific">
>     * Some channels already apply sender-based filtering for supplemental context in specific paths (for example Slack thread seeding, Matrix reply/thread lookups).
>     * Other channels still pass quote/reply/forward context through as received.
>   </Accordion>
>
>   <Accordion title="Hardening direction (planned)">
>     * `contextVisibility: "all"` (default) keeps current as-received behavior.
>     * `contextVisibility: "allowlist"` filters supplemental context to allowlisted senders.
>     * `contextVisibility: "allowlist_quote"` is `allowlist` plus one explicit quote/reply exception.
>
>     Until this hardening model is implemented consistently across channels, expect differences by surface.
>   </Accordion>
> </AccordionGroup>

[展开：当前行为各通道不一]

- 有些通道已经在特定路径里按发件人过滤补充上下文（比如 Slack 的话题种子注入、Matrix 的回复 / 话题查询）。
- 另一些通道还是按收到时的原样把引用 / 回复 / 转发上下文带进去。

[展开：未来强化方向（规划中）]

- `contextVisibility: "all"`（默认）维持现有的"按收到时的原样"行为。
- `contextVisibility: "allowlist"` 把补充上下文过滤到白名单发件人的范围内。
- `contextVisibility: "allowlist_quote"` 等于 `allowlist` 加一条显式的引用 / 回复豁免。

在所有通道一致实现这个强化模型之前，各通道之间的行为还会有差异。

> <img src="https://mintcdn.com/clawdhub/dpADRo8IUoiDztzJ/images/groups-flow.svg?fit=max&auto=format&n=dpADRo8IUoiDztzJ&q=85&s=eeb387df91a967fbbe8bf8f80ae41dd7" alt="Group message flow" width="960" height="260" data-path="images/groups-flow.svg" />

<img src="https://mintcdn.com/clawdhub/dpADRo8IUoiDztzJ/images/groups-flow.svg?fit=max&auto=format&n=dpADRo8IUoiDztzJ&q=85&s=eeb387df91a967fbbe8bf8f80ae41dd7" alt="群消息流程" width="960" height="260" data-path="images/groups-flow.svg" />

> If you want...
>
> | Goal                                         | What to set                                                |
> | -------------------------------------------- | ---------------------------------------------------------- |
> | Allow all groups but only reply on @mentions | `groups: { "*": { requireMention: true } }`                |
> | Disable all group replies                    | `groupPolicy: "disabled"`                                  |
> | Only specific groups                         | `groups: { "<group-id>": { ... } }` (no `"*"` key)         |
> | Only you can trigger in groups               | `groupPolicy: "allowlist"`, `groupAllowFrom: ["+1555..."]` |
> | Reuse one trusted sender set across channels | `groupAllowFrom: ["accessGroup:operators"]`                |

要实现某个目标，对应的配置：

| 目标                                          | 配置                                                              |
| --------------------------------------------- | ----------------------------------------------------------------- |
| 所有群都允许，但只在被 @ 时回复               | `groups: { "*": { requireMention: true } }`                       |
| 关闭所有群回复                                | `groupPolicy: "disabled"`                                         |
| 只允许特定的群                                | `groups: { "<group-id>": { ... } }`（不要 `"*"` key）             |
| 只有你能在群里触发                            | `groupPolicy: "allowlist"`、`groupAllowFrom: ["+1555..."]`        |
| 一份受信发件人列表跨多个通道复用              | `groupAllowFrom: ["accessGroup:operators"]`                       |

> For reusable sender allowlists, see [Access groups](/channels/access-groups).

可复用发件人白名单的写法见 [访问组](/channels/access-groups)。

---

> ## Session keys

## 会话 key

> * Group sessions use `agent:<agentId>:<channel>:group:<id>` session keys (rooms/channels use `agent:<agentId>:<channel>:channel:<id>`).
> * Telegram forum topics add `:topic:<threadId>` to the group id so each topic has its own session.
> * Direct chats use the main session (or per-sender if configured).
> * Heartbeats are skipped for group sessions.

- 群会话的 key 形如 `agent:<agentId>:<channel>:group:<id>`（rooms / channels 用 `agent:<agentId>:<channel>:channel:<id>`）。
- Telegram 的 forum topic 会在群 id 后追加 `:topic:<threadId>`，每个 topic 有自己的会话。
- 私聊用主会话（或者按发件人独立，看配置）。
- 群会话不发心跳。

---

<a id="pattern-personal-dms-public-groups-single-agent" />

> ## Pattern: personal DMs + public groups (single agent)

## 模式：私人私聊 + 公共群（单 agent）

> Yes — this works well if your "personal" traffic is **DMs** and your "public" traffic is **groups**.

如果你的"私人"流量集中在**私聊**、"公共"流量集中在**群**，这个模式效果很好。

> Why: in single-agent mode, DMs typically land in the **main** session key (`agent:main:main`), while groups always use **non-main** session keys (`agent:main:<channel>:group:<id>`). If you enable sandboxing with `mode: "non-main"`, those group sessions run in the configured sandbox backend while your main DM session stays on-host. Docker is the default backend if you do not choose one.

原因：单 agent 模式下，私聊通常落在 **main** 会话 key（`agent:main:main`）；群一定用**非 main** 会话 key（`agent:main:<channel>:group:<id>`）。把 sandbox 配成 `mode: "non-main"`，群会话就跑在配好的 sandbox 后端里，私聊的 main 会话留在宿主机上。不指定的话，默认后端是 Docker。

> This gives you one agent "brain" (shared workspace + memory), but two execution postures:
>
> * **DMs**: full tools (host)
> * **Groups**: sandbox + restricted tools

这样就有一个 agent "大脑"（共享工作区 + 记忆），但两种执行姿态：

- **私聊**：全套工具（宿主机）
- **群**：沙盒 + 受限工具

> <Note>
>   If you need truly separate workspaces/personas ("personal" and "public" must never mix), use a second agent + bindings. See [Multi-Agent Routing](/concepts/multi-agent).
> </Note>

> **提示**：如果"私人"和"公共"必须完全隔离（工作区 / 人设都不能混），用第二个 agent 加 bindings。见 [多 Agent 路由](/concepts/multi-agent)。

> [标签页: DMs on host, groups sandboxed]
>
> ```json5
> {
>   agents: {
>     defaults: {
>       sandbox: {
>         mode: "non-main", // groups/channels are non-main -> sandboxed
>         scope: "session", // strongest isolation (one container per group/channel)
>         workspaceAccess: "none",
>       },
>     },
>   },
>   tools: {
>     sandbox: {
>       tools: {
>         // If allow is non-empty, everything else is blocked (deny still wins).
>         allow: ["group:messaging", "group:sessions"],
>         deny: ["group:runtime", "group:fs", "group:ui", "nodes", "cron", "gateway"],
>       },
>     },
>   },
> }
> ```

[标签页：私聊在宿主机、群在沙盒]

```json5
{
  agents: {
    defaults: {
      sandbox: {
        mode: "non-main", // 群 / 频道是 non-main -> 进沙盒
        scope: "session", // 最强隔离（每个群 / 频道一个容器）
        workspaceAccess: "none",
      },
    },
  },
  tools: {
    sandbox: {
      tools: {
        // allow 非空时，其他一律禁止（deny 优先级更高）
        allow: ["group:messaging", "group:sessions"],
        deny: ["group:runtime", "group:fs", "group:ui", "nodes", "cron", "gateway"],
      },
    },
  },
}
```

> [标签页: Groups see only an allowlisted folder]
>
> Want "groups can only see folder X" instead of "no host access"? Keep `workspaceAccess: "none"` and mount only allowlisted paths into the sandbox:
>
> ```json5
> {
>   agents: {
>     defaults: {
>       sandbox: {
>         mode: "non-main",
>         scope: "session",
>         workspaceAccess: "none",
>         docker: {
>           binds: [
>             // hostPath:containerPath:mode
>             "/home/user/FriendsShared:/data:ro",
>           ],
>         },
>       },
>     },
>   },
> }
> ```

[标签页：群里只能看到白名单内的目录]

想要"群只能看到目录 X"而不是"完全没有宿主机访问"？保持 `workspaceAccess: "none"`，把白名单路径挂进沙盒：

```json5
{
  agents: {
    defaults: {
      sandbox: {
        mode: "non-main",
        scope: "session",
        workspaceAccess: "none",
        docker: {
          binds: [
            // hostPath:containerPath:mode
            "/home/user/FriendsShared:/data:ro",
          ],
        },
      },
    },
  },
}
```

> Related:
>
> * Configuration keys and defaults: [Gateway configuration](/gateway/config-agents#agentsdefaultssandbox)
> * Debugging why a tool is blocked: [Sandbox vs Tool Policy vs Elevated](/gateway/sandbox-vs-tool-policy-vs-elevated)
> * Bind mounts details: [Sandboxing](/gateway/sandboxing#custom-bind-mounts)

相关：

- 配置项和默认值：[Gateway 配置](/gateway/config-agents#agentsdefaultssandbox)
- 调试某个工具被拦的原因：[Sandbox vs Tool Policy vs Elevated](/gateway/sandbox-vs-tool-policy-vs-elevated)
- bind 挂载详情：[沙盒](/gateway/sandboxing#custom-bind-mounts)

---

> ## Display labels

## 显示标签

> * UI labels use `displayName` when available, formatted as `<channel>:<token>`.
> * `#room` is reserved for rooms/channels; group chats use `g-<slug>` (lowercase, spaces -> `-`, keep `#@+._-`).

- UI 标签优先用 `displayName`，格式 `<channel>:<token>`。
- `#room` 保留给 rooms / channels；群聊用 `g-<slug>`（小写，空格变 `-`，保留 `#@+._-`）。

---

> ## Group policy

## 群策略

> Control how group/room messages are handled per channel:

按通道控制群 / 房间消息怎么处理：

> ```json5
> {
>   channels: {
>     whatsapp: {
>       groupPolicy: "disabled", // "open" | "disabled" | "allowlist"
>       groupAllowFrom: ["+15551234567"],
>     },
>     telegram: {
>       groupPolicy: "disabled",
>       groupAllowFrom: ["123456789"], // numeric Telegram user id (wizard can resolve @username)
>     },
>     signal: {
>       groupPolicy: "disabled",
>       groupAllowFrom: ["+15551234567"],
>     },
>     imessage: {
>       groupPolicy: "disabled",
>       groupAllowFrom: ["chat_id:123"],
>     },
>     msteams: {
>       groupPolicy: "disabled",
>       groupAllowFrom: ["user@org.com"],
>     },
>     discord: {
>       groupPolicy: "allowlist",
>       guilds: {
>         GUILD_ID: { channels: { help: { allow: true } } },
>       },
>     },
>     slack: {
>       groupPolicy: "allowlist",
>       channels: { "#general": { allow: true } },
>     },
>     matrix: {
>       groupPolicy: "allowlist",
>       groupAllowFrom: ["@owner:example.org"],
>       groups: {
>         "!roomId:example.org": { enabled: true },
>         "#alias:example.org": { enabled: true },
>       },
>     },
>   },
> }
> ```

```json5
{
  channels: {
    whatsapp: {
      groupPolicy: "disabled", // "open" | "disabled" | "allowlist"
      groupAllowFrom: ["+15551234567"],
    },
    telegram: {
      groupPolicy: "disabled",
      groupAllowFrom: ["123456789"], // 数字 Telegram user id（向导可以解析 @username）
    },
    signal: {
      groupPolicy: "disabled",
      groupAllowFrom: ["+15551234567"],
    },
    imessage: {
      groupPolicy: "disabled",
      groupAllowFrom: ["chat_id:123"],
    },
    msteams: {
      groupPolicy: "disabled",
      groupAllowFrom: ["user@org.com"],
    },
    discord: {
      groupPolicy: "allowlist",
      guilds: {
        GUILD_ID: { channels: { help: { allow: true } } },
      },
    },
    slack: {
      groupPolicy: "allowlist",
      channels: { "#general": { allow: true } },
    },
    matrix: {
      groupPolicy: "allowlist",
      groupAllowFrom: ["@owner:example.org"],
      groups: {
        "!roomId:example.org": { enabled: true },
        "#alias:example.org": { enabled: true },
      },
    },
  },
}
```

> | Policy        | Behavior                                                     |
> | ------------- | ------------------------------------------------------------ |
> | `"open"`      | Groups bypass allowlists; mention-gating still applies.      |
> | `"disabled"`  | Block all group messages entirely.                           |
> | `"allowlist"` | Only allow groups/rooms that match the configured allowlist. |

| 策略          | 行为                                                  |
| ------------- | ----------------------------------------------------- |
| `"open"`      | 群绕过白名单；@ 触发仍然生效。                        |
| `"disabled"`  | 全部群消息直接拦下。                                  |
| `"allowlist"` | 只允许命中白名单的群 / 房间。                         |

> [展开: Per-channel notes]
>
> * `groupPolicy` is separate from mention-gating (which requires @mentions).
> * WhatsApp/Telegram/Signal/iMessage/Microsoft Teams/Zalo: use `groupAllowFrom` (fallback: explicit `allowFrom`).
> * Signal: `groupAllowFrom` can match either the inbound Signal group id or the sender phone/UUID.
> * DM pairing approvals (`*-allowFrom` store entries) apply to DM access only; group sender authorization stays explicit to group allowlists.
> * Discord: allowlist uses `channels.discord.guilds.<id>.channels`.
> * Slack: allowlist uses `channels.slack.channels`.
> * Matrix: allowlist uses `channels.matrix.groups`. Prefer room IDs or aliases; joined-room name lookup is best-effort, and unresolved names are ignored at runtime. Use `channels.matrix.groupAllowFrom` to restrict senders; per-room `users` allowlists are also supported.
> * Group DMs are controlled separately (`channels.discord.dm.*`, `channels.slack.dm.*`).
> * Telegram allowlist can match user IDs (`"123456789"`, `"telegram:123456789"`, `"tg:123456789"`) or usernames (`"@alice"` or `"alice"`); prefixes are case-insensitive.
> * Default is `groupPolicy: "allowlist"`; if your group allowlist is empty, group messages are blocked.
> * Runtime safety: when a provider block is completely missing (`channels.<provider>` absent), group policy falls back to a fail-closed mode (typically `allowlist`) instead of inheriting `channels.defaults.groupPolicy`.

[展开：各通道说明]

- `groupPolicy` 跟 @ 触发是两件事（@ 触发要求消息里有 @）。
- WhatsApp / Telegram / Signal / iMessage / Microsoft Teams / Zalo：用 `groupAllowFrom`（没设回退到显式的 `allowFrom`）。
- Signal：`groupAllowFrom` 可以匹配 Signal 群 id，也可以匹配发件人的电话 / UUID。
- 私聊配对的批准（`*-allowFrom` 存储里的条目）只管私聊访问，群发件人授权一直要走群白名单。
- Discord：白名单用 `channels.discord.guilds.<id>.channels`。
- Slack：白名单用 `channels.slack.channels`。
- Matrix：白名单用 `channels.matrix.groups`。优先写 room IDs 或 alias；按已加入的房间名查找是 best-effort，运行时解析不出来的名字会忽略。用 `channels.matrix.groupAllowFrom` 限制发件人；每个房间也可以单独设 `users` 白名单。
- 群里的私聊另有控制（`channels.discord.dm.*`、`channels.slack.dm.*`）。
- Telegram 白名单可以匹配 user ID（`"123456789"`、`"telegram:123456789"`、`"tg:123456789"`）或 username（`"@alice"` 或 `"alice"`）；前缀不区分大小写。
- 默认 `groupPolicy: "allowlist"`；群白名单为空时，所有群消息都被拦。
- 运行时安全：某个 provider 块完全缺失时（`channels.<provider>` 不存在），群策略会回退到 fail-closed 模式（通常是 `allowlist`），不会去继承 `channels.defaults.groupPolicy`。

> Quick mental model (evaluation order for group messages):

群消息的判断顺序记忆图：

> [步骤 1: groupPolicy] `groupPolicy` (open/disabled/allowlist).

[步骤 1：groupPolicy] `groupPolicy`（open / disabled / allowlist）。

> [步骤 2: Group allowlists] Group allowlists (`*.groups`, `*.groupAllowFrom`, channel-specific allowlist).

[步骤 2：群白名单] 群白名单（`*.groups`、`*.groupAllowFrom`、各通道自己的白名单）。

> [步骤 3: Mention gating] Mention gating (`requireMention`, `/activation`).

[步骤 3：@ 触发] @ 触发（`requireMention`、`/activation`）。

---

> ## Mention gating (default)

## @ 触发（默认）

> Group messages require a mention unless overridden per group. Defaults live per subsystem under `*.groups."*"`.

群消息默认要 @，除非在某个群里覆盖了。各子系统的默认值放在 `*.groups."*"` 下。

> Replying to a bot message counts as an implicit mention when the channel supports reply metadata. Quoting a bot message can also count as an implicit mention on channels that expose quote metadata. Current built-in cases include Telegram, WhatsApp, Slack, Discord, Microsoft Teams, and ZaloUser.

通道支持 reply 元数据时，回复机器人的消息算隐式 @。通道暴露 quote 元数据时，引用机器人的消息也算隐式 @。当前内置支持这一点的通道有 Telegram、WhatsApp、Slack、Discord、Microsoft Teams、ZaloUser。

> ```json5
> {
>   channels: {
>     whatsapp: {
>       groups: {
>         "*": { requireMention: true },
>         "123@g.us": { requireMention: false },
>       },
>     },
>     telegram: {
>       groups: {
>         "*": { requireMention: true },
>         "123456789": { requireMention: false },
>       },
>     },
>     imessage: {
>       groups: {
>         "*": { requireMention: true },
>         "123": { requireMention: false },
>       },
>     },
>   },
>   agents: {
>     list: [
>       {
>         id: "main",
>         groupChat: {
>           mentionPatterns: ["@openclaw", "openclaw", "\\+15555550123"],
>           historyLimit: 50,
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
        "123@g.us": { requireMention: false },
      },
    },
    telegram: {
      groups: {
        "*": { requireMention: true },
        "123456789": { requireMention: false },
      },
    },
    imessage: {
      groups: {
        "*": { requireMention: true },
        "123": { requireMention: false },
      },
    },
  },
  agents: {
    list: [
      {
        id: "main",
        groupChat: {
          mentionPatterns: ["@openclaw", "openclaw", "\\+15555550123"],
          historyLimit: 50,
        },
      },
    ],
  },
}
```

> [展开: Mention gating notes]
>
> * `mentionPatterns` are case-insensitive safe regex patterns; invalid patterns and unsafe nested-repetition forms are ignored.
> * Surfaces that provide explicit mentions still pass; patterns are a fallback.
> * Per-agent override: `agents.list[].groupChat.mentionPatterns` (useful when multiple agents share a group).
> * Mention gating is only enforced when mention detection is possible (native mentions or `mentionPatterns` are configured).
> * Allowlisting a group or sender does not disable mention gating; set that group's `requireMention` to `false` when all messages should trigger.
> * Automatic group chat prompt context carries the resolved silent-reply instruction every turn; workspace files should not duplicate `NO_REPLY` mechanics.
> * Groups where automatic silent replies are allowed treat clean empty or reasoning-only model turns as silent, equivalent to `NO_REPLY`. Direct chats never receive `NO_REPLY` guidance, and message-tool-only group replies stay quiet by not calling `message(action=send)`.
> * Ambient always-on group chatter uses legacy user-request semantics by default. Set `messages.groupChat.ambientTurns: "room_event"` to submit it as quiet context instead.
> * Room events are not stored as fake user requests, and private assistant text from no-message-tool room events is not replayed as chat history.
> * Discord defaults live in `channels.discord.guilds."*"` (overridable per guild/channel).
> * Group history context is wrapped uniformly across channels. Mention-gated groups keep pending skipped messages; always-on groups may also retain recent processed room messages when the channel supports it. Use `messages.groupChat.historyLimit` for the global default and `channels.<channel>.historyLimit` (or `channels.<channel>.accounts.*.historyLimit`) for overrides. Set `0` to disable.

[展开：@ 触发的注意事项]

- `mentionPatterns` 是不区分大小写的安全正则；非法模式和不安全的嵌套重复会被忽略。
- 通道自带显式 @ 时直接通过；正则模式是兜底。
- 按 agent 覆盖：`agents.list[].groupChat.mentionPatterns`（多个 agent 共享一个群时有用）。
- 只有能检测 @ 时（通道支持原生 @ 或配了 `mentionPatterns`），@ 触发才会强制执行。
- 把一个群或发件人加进白名单不会关掉 @ 触发；想让所有消息都触发，把那个群的 `requireMention` 设成 `false`。
- 群聊自动提示词每一轮都会带上"安静回复"指令；工作区文件不要重复实现 `NO_REPLY` 那套机制。
- 允许自动安静回复的群里，模型给出空内容或仅有推理的轮次会被当作安静，等同于 `NO_REPLY`。私聊永远不会收到 `NO_REPLY` 指引；message-tool-only 模式的群回复通过不调 `message(action=send)` 来保持安静。
- 环境型 always-on 群闲聊默认走旧版用户请求语义。把 `messages.groupChat.ambientTurns` 设成 `"room_event"`，可以改为以安静上下文形式提交。
- 房间事件不会被记成"假用户请求"，无消息工具的房间事件里 assistant 的私下文本也不会作为聊天历史回放。
- Discord 默认值放在 `channels.discord.guilds."*"`（可按 guild / channel 覆盖）。
- 群历史上下文在所有通道里用同一种方式封装。@ 触发的群会保留被跳过的待处理消息；always-on 群在通道支持时也会保留最近处理过的房间消息。全局默认用 `messages.groupChat.historyLimit`，覆盖用 `channels.<channel>.historyLimit`（或 `channels.<channel>.accounts.*.historyLimit`）。设 `0` 关闭。

---

> ## Group/channel tool restrictions (optional)

## 群 / 频道工具限制（可选）

> Some channel configs support restricting which tools are available **inside a specific group/room/channel**.

部分通道配置支持限制**某个群 / 房间 / 频道里**能用哪些工具。

> * `tools`: allow/deny tools for the whole group.
> * `toolsBySender`: per-sender overrides within the group. Use explicit key prefixes: `channel:<channelId>:<senderId>`, `id:<senderId>`, `e164:<phone>`, `username:<handle>`, `name:<displayName>`, and `"*"` wildcard. Channel ids use canonical OpenClaw channel ids; aliases such as `teams` normalize to `msteams`. Legacy unprefixed keys are still accepted and matched as `id:` only.

- `tools`：整个群的工具 allow / deny。
- `toolsBySender`：群里按发件人覆盖。key 要带前缀：`channel:<channelId>:<senderId>`、`id:<senderId>`、`e164:<phone>`、`username:<handle>`、`name:<displayName>`，以及通配 `"*"`。channel id 用 OpenClaw 标准的 channel id；`teams` 这种别名会归一为 `msteams`。旧版不带前缀的 key 仍然接受，但只按 `id:` 匹配。

> Resolution order (most specific wins):

判断顺序（越具体越优先）：

> [步骤 1: Group toolsBySender] Group/channel `toolsBySender` match.

[步骤 1：群 toolsBySender] 群 / 频道的 `toolsBySender` 匹配。

> [步骤 2: Group tools] Group/channel `tools`.

[步骤 2：群 tools] 群 / 频道的 `tools`。

> [步骤 3: Default toolsBySender] Default (`"*"`) `toolsBySender` match.

[步骤 3：默认 toolsBySender] 默认（`"*"`）的 `toolsBySender` 匹配。

> [步骤 4: Default tools] Default (`"*"`) `tools`.

[步骤 4：默认 tools] 默认（`"*"`）的 `tools`。

> Example (Telegram):

例子（Telegram）：

> ```json5
> {
>   channels: {
>     telegram: {
>       groups: {
>         "*": { tools: { deny: ["exec"] } },
>         "-1001234567890": {
>           tools: { deny: ["exec", "read", "write"] },
>           toolsBySender: {
>             "id:123456789": { alsoAllow: ["exec"] },
>           },
>         },
>       },
>     },
>   },
> }
> ```

```json5
{
  channels: {
    telegram: {
      groups: {
        "*": { tools: { deny: ["exec"] } },
        "-1001234567890": {
          tools: { deny: ["exec", "read", "write"] },
          toolsBySender: {
            "id:123456789": { alsoAllow: ["exec"] },
          },
        },
      },
    },
  },
}
```

> <Note>
>   Group/channel tool restrictions are applied in addition to global/agent tool policy (deny still wins). Some channels use different nesting for rooms/channels (e.g., Discord `guilds.*.channels.*`, Slack `channels.*`, Microsoft Teams `teams.*.channels.*`).
> </Note>

> **提示**：群 / 频道的工具限制是在全局 / agent 工具策略之上叠加的（deny 仍然优先级最高）。部分通道用不同的嵌套结构表示 rooms / channels（比如 Discord 的 `guilds.*.channels.*`、Slack 的 `channels.*`、Microsoft Teams 的 `teams.*.channels.*`）。

---

> ## Group allowlists

## 群白名单

> When `channels.whatsapp.groups`, `channels.telegram.groups`, or `channels.imessage.groups` is configured, the keys act as a group allowlist. Use `"*"` to allow all groups while still setting default mention behavior.

`channels.whatsapp.groups`、`channels.telegram.groups`、`channels.imessage.groups` 配置后，里面的 key 同时充当群白名单。用 `"*"` 表示所有群都放行，同时还能设默认的 @ 行为。

> <Warning>
>   Common confusion: DM pairing approval is not the same as group authorization. For channels that support DM pairing, the pairing store unlocks DMs only. Group commands still require explicit group sender authorization from config allowlists such as `groupAllowFrom` or the documented config fallback for that channel.
> </Warning>

> **警告**：常见混淆 —— 私聊配对批准 ≠ 群授权。支持私聊配对的通道，配对存储只解锁私聊。群命令仍然要从配置白名单（比如 `groupAllowFrom`，或该通道文档里说明的回退配置）里拿到显式的群发件人授权。

> Common intents (copy/paste):

常见意图，复制即用：

> [标签页: Disable all group replies]
>
> ```json5
> {
>   channels: { whatsapp: { groupPolicy: "disabled" } },
> }
> ```

[标签页：关闭所有群回复]

```json5
{
  channels: { whatsapp: { groupPolicy: "disabled" } },
}
```

> [标签页: Allow only specific groups (WhatsApp)]
>
> ```json5
> {
>   channels: {
>     whatsapp: {
>       groups: {
>         "123@g.us": { requireMention: true },
>         "456@g.us": { requireMention: false },
>       },
>     },
>   },
> }
> ```

[标签页：只允许特定群（WhatsApp）]

```json5
{
  channels: {
    whatsapp: {
      groups: {
        "123@g.us": { requireMention: true },
        "456@g.us": { requireMention: false },
      },
    },
  },
}
```

> [标签页: Allow all groups but require mention]
>
> ```json5
> {
>   channels: {
>     whatsapp: {
>       groups: { "*": { requireMention: true } },
>     },
>   },
> }
> ```

[标签页：所有群放行，但要 @]

```json5
{
  channels: {
    whatsapp: {
      groups: { "*": { requireMention: true } },
    },
  },
}
```

> [标签页: Owner-only triggers (WhatsApp)]
>
> ```json5
> {
>   channels: {
>     whatsapp: {
>       groupPolicy: "allowlist",
>       groupAllowFrom: ["+15551234567"],
>       groups: { "*": { requireMention: true } },
>     },
>   },
> }
> ```

[标签页：只有所有者能触发（WhatsApp）]

```json5
{
  channels: {
    whatsapp: {
      groupPolicy: "allowlist",
      groupAllowFrom: ["+15551234567"],
      groups: { "*": { requireMention: true } },
    },
  },
}
```

---

> ## Activation (owner-only)

## 激活（只有所有者能切）

> Group owners can toggle per-group activation:
>
> * `/activation mention`
> * `/activation always`

群所有者可以按群切激活模式：

- `/activation mention`
- `/activation always`

> Owner is determined by `channels.whatsapp.allowFrom` (or the bot's self E.164 when unset). Send the command as a standalone message. Other surfaces currently ignore `/activation`.

所有者按 `channels.whatsapp.allowFrom` 决定（没设就用机器人自己的 E.164）。命令要独立发一条消息。目前其他通道会忽略 `/activation`。

---

> ## Context fields

## 上下文字段

> Group inbound payloads set:
>
> * `ChatType=group`
> * `GroupSubject` (if known)
> * `GroupMembers` (if known)
> * `WasMentioned` (mention gating result)
> * Telegram forum topics also include `MessageThreadId` and `IsForum`.

群消息进来时会带上：

- `ChatType=group`
- `GroupSubject`（已知时）
- `GroupMembers`（已知时）
- `WasMentioned`（@ 触发的结果）
- Telegram forum topic 还会附带 `MessageThreadId` 和 `IsForum`。

> The agent system prompt includes a group intro on the first turn of a new group session. It reminds the model to respond like a human, avoid Markdown tables, minimize empty lines and follow normal chat spacing, and avoid typing literal `\n` sequences. Channel-sourced group names and participant labels are rendered as fenced untrusted metadata, not inline system instructions.

新建群会话的第一轮里，agent 系统提示词会带一段群介绍，提醒模型像人一样回话、不要用 Markdown 表格、尽量少空行、按正常聊天节奏排版、不要直接打 `\n` 字面量。从通道拿到的群名和参与者标签会渲染成围栏内的不受信元数据，不是行内系统指令。

---

> ## iMessage specifics

## iMessage 专属

> * Prefer `chat_id:<id>` when routing or allowlisting.
> * List chats: `imsg chats --limit 20`.
> * Group replies always go back to the same `chat_id`.

- 路由或加白名单时优先用 `chat_id:<id>`。
- 列出聊天：`imsg chats --limit 20`。
- 群回复始终发回同一个 `chat_id`。

---

> ## WhatsApp system prompts

## WhatsApp 系统提示词

> See [WhatsApp](/channels/whatsapp#system-prompts) for the canonical WhatsApp system prompt rules, including group and direct prompt resolution, wildcard behavior, and account override semantics.

WhatsApp 系统提示词的标准规则见 [WhatsApp](/channels/whatsapp#system-prompts)，包括群与私聊提示词的解析、通配行为、账号覆盖语义。

---

> ## WhatsApp specifics

## WhatsApp 专属

> See [Group messages](/channels/group-messages) for WhatsApp-only behavior (history injection, mention handling details).

WhatsApp 专属行为（历史注入、@ 处理细节）见 [WhatsApp 群消息](/channels/group-messages)。

---

> ## Related

## 相关

> * [Broadcast groups](/channels/broadcast-groups)
> * [Channel routing](/channels/channel-routing)
> * [Group messages](/channels/group-messages)
> * [Pairing](/channels/pairing)

- [广播组](/channels/broadcast-groups)
- [通道路由](/channels/channel-routing)
- [WhatsApp 群消息](/channels/group-messages)
- [配对](/channels/pairing)
