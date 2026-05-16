# Access groups

> Access groups are named sender lists you define once and reference from channel allowlists with `accessGroup:<name>`.

访问组（Access groups）是命名的发件人列表：定义一次，在通道白名单里用 `accessGroup:<名字>` 引用。

> Use them when the same people should be allowed across several message channels, or when one trusted set should apply to both DMs and group sender authorization.

适合两种场景：同一批人要在多个消息通道放行；同一批受信发件人要同时用在私聊和群授权里。

> Access groups do not grant access by themselves. A group only matters when an allowlist field references it.

访问组本身不授予访问权限。只有被某个白名单字段引用时，它才起作用。

---

> ## Static message sender groups

## 静态消息发件人组

> Static sender groups use `type: "message.senders"`.

静态发件人组的 `type` 是 `"message.senders"`：

> ```json5
> {
>   accessGroups: {
>     operators: {
>       type: "message.senders",
>       members: {
>         "*": ["global-owner-id"],
>         discord: ["discord:123456789012345678"],
>         telegram: ["987654321"],
>         whatsapp: ["+15551234567"],
>       },
>     },
>   },
> }
> ```

```json5
{
  accessGroups: {
    operators: {
      type: "message.senders",
      members: {
        "*": ["global-owner-id"],
        discord: ["discord:123456789012345678"],
        telegram: ["987654321"],
        whatsapp: ["+15551234567"],
      },
    },
  },
}
```

> Member lists are keyed by message-channel id:

成员列表按消息通道 ID 分组：

> | Key        | Meaning                                                                 |
> | ---------- | ----------------------------------------------------------------------- |
> | `"*"`      | Shared entries checked for every message channel that references group. |
> | `discord`  | Entries checked only for Discord allowlist matching.                    |
> | `telegram` | Entries checked only for Telegram allowlist matching.                   |
> | `whatsapp` | Entries checked only for WhatsApp allowlist matching.                   |

| Key        | 含义                                                            |
| ---------- | --------------------------------------------------------------- |
| `"*"`      | 共享条目，引用这个组的所有消息通道都会查这一组。                |
| `discord`  | 只在 Discord 白名单匹配时查的条目。                             |
| `telegram` | 只在 Telegram 白名单匹配时查的条目。                            |
| `whatsapp` | 只在 WhatsApp 白名单匹配时查的条目。                            |

> Entries are matched with the destination channel's normal `allowFrom` rules. OpenClaw does not translate sender ids between channels. If Alice has a Telegram id and a Discord id, list both ids under the appropriate keys.

条目按目标通道自己的 `allowFrom` 规则匹配。OpenClaw 不会在通道之间互相转换发件人 ID。Alice 既有 Telegram ID 又有 Discord ID，那两个 ID 都要写到各自对应的 key 下。

---

> ## Reference groups from allowlists

## 在白名单里引用访问组

> Reference a group with `accessGroup:<name>` anywhere the message channel path supports sender allowlists.

支持发件人白名单的地方都可以用 `accessGroup:<名字>` 引用一个组。

> DM allowlist example:

私聊白名单的例子：

> ```json5
> {
>   accessGroups: {
>     operators: {
>       type: "message.senders",
>       members: {
>         discord: ["discord:123456789012345678"],
>         telegram: ["987654321"],
>       },
>     },
>   },
>   channels: {
>     discord: {
>       dmPolicy: "allowlist",
>       allowFrom: ["accessGroup:operators"],
>     },
>     telegram: {
>       dmPolicy: "allowlist",
>       allowFrom: ["accessGroup:operators"],
>     },
>   },
> }
> ```

```json5
{
  accessGroups: {
    operators: {
      type: "message.senders",
      members: {
        discord: ["discord:123456789012345678"],
        telegram: ["987654321"],
      },
    },
  },
  channels: {
    discord: {
      dmPolicy: "allowlist",
      allowFrom: ["accessGroup:operators"],
    },
    telegram: {
      dmPolicy: "allowlist",
      allowFrom: ["accessGroup:operators"],
    },
  },
}
```

> Group sender allowlist example:

群发件人白名单的例子：

> ```json5
> {
>   accessGroups: {
>     oncall: {
>       type: "message.senders",
>       members: {
>         whatsapp: ["+15551234567"],
>         googlechat: ["users/1234567890"],
>       },
>     },
>   },
>   channels: {
>     whatsapp: {
>       groupPolicy: "allowlist",
>       groupAllowFrom: ["accessGroup:oncall"],
>     },
>     googlechat: {
>       spaces: {
>         "spaces/AAA": {
>           users: ["accessGroup:oncall"],
>         },
>       },
>     },
>   },
> }
> ```

```json5
{
  accessGroups: {
    oncall: {
      type: "message.senders",
      members: {
        whatsapp: ["+15551234567"],
        googlechat: ["users/1234567890"],
      },
    },
  },
  channels: {
    whatsapp: {
      groupPolicy: "allowlist",
      groupAllowFrom: ["accessGroup:oncall"],
    },
    googlechat: {
      spaces: {
        "spaces/AAA": {
          users: ["accessGroup:oncall"],
        },
      },
    },
  },
}
```

> You can mix groups and direct entries:

可以把组引用和直接条目混着写：

> ```json5
> {
>   channels: {
>     discord: {
>       dmPolicy: "allowlist",
>       allowFrom: ["accessGroup:operators", "discord:123456789012345678"],
>     },
>   },
> }
> ```

```json5
{
  channels: {
    discord: {
      dmPolicy: "allowlist",
      allowFrom: ["accessGroup:operators", "discord:123456789012345678"],
    },
  },
}
```

---

> ## Supported message-channel paths

## 支持访问组的消息通道路径

> Access groups are available in shared message-channel authorization paths, including:
>
> * DM sender allowlists such as `channels.<channel>.allowFrom`
> * group sender allowlists such as `channels.<channel>.groupAllowFrom`
> * channel-specific per-room sender allowlists that use the same sender matching rules
> * command authorization paths that reuse message-channel sender allowlists

通用的消息通道授权路径都支持访问组：

- 私聊发件人白名单，如 `channels.<channel>.allowFrom`
- 群发件人白名单，如 `channels.<channel>.groupAllowFrom`
- 通道里的每个房间单独的发件人白名单（用相同的匹配规则）
- 复用消息通道发件人白名单的命令授权路径

> Channel support depends on whether that channel is wired through the shared OpenClaw sender-authorization helpers. Current bundled support includes Discord, Feishu, Google Chat, iMessage, LINE, Mattermost, Microsoft Teams, Nextcloud Talk, Nostr, QQBot, Signal, WhatsApp, Zalo, and Zalo Personal. Static `message.senders` groups are designed to be channel-agnostic, so new message channels should support them by using the shared plugin SDK helpers instead of custom allowlist expansion.

具体通道支不支持，看它有没有接进 OpenClaw 共用的发件人授权工具。当前内置支持：Discord、Feishu、Google Chat、iMessage、LINE、Mattermost、Microsoft Teams、Nextcloud Talk、Nostr、QQBot、Signal、WhatsApp、Zalo、Zalo Personal。静态 `message.senders` 组的设计就是与具体通道解耦，新增的消息通道接入时直接用共用插件 SDK 的工具就好，不要自己写白名单展开逻辑。

---

> ## Plugin diagnostics

## 插件侧的诊断接口

> Plugin authors can inspect structured access-group state without expanding it back into a flat allowlist:

插件作者可以查看结构化的访问组状态，不必再展开成扁平的白名单数组：

> ```typescript
> import { resolveAccessGroupAllowFromState } from "openclaw/plugin-sdk/security-runtime";
>
> const state = await resolveAccessGroupAllowFromState({
>   accessGroups: cfg.accessGroups,
>   allowFrom: channelConfig.allowFrom,
>   channel: "my-channel",
>   accountId: "default",
>   senderId,
>   isSenderAllowed,
> });
> ```

```typescript
import { resolveAccessGroupAllowFromState } from "openclaw/plugin-sdk/security-runtime";

const state = await resolveAccessGroupAllowFromState({
  accessGroups: cfg.accessGroups,
  allowFrom: channelConfig.allowFrom,
  channel: "my-channel",
  accountId: "default",
  senderId,
  isSenderAllowed,
});
```

> The result reports referenced, matched, missing, unsupported, and failed groups. Use this when you need diagnostics or conformance tests. Use `expandAllowFromWithAccessGroups(...)` only for compatibility paths that still expect a flat `allowFrom` array.

返回值会报告：引用了哪些组、命中了哪些、缺失的、不支持的、失败的。需要诊断或写一致性测试时用它。只有那些还指望拿到扁平 `allowFrom` 数组的兼容路径，才去用 `expandAllowFromWithAccessGroups(...)`。

---

> ## Discord channel audiences

## Discord 频道受众组

> Discord also supports a dynamic access group type:

Discord 还支持一种动态访问组：

> ```json5
> {
>   accessGroups: {
>     maintainers: {
>       type: "discord.channelAudience",
>       guildId: "1456350064065904867",
>       channelId: "1456744319972282449",
>       membership: "canViewChannel",
>     },
>   },
>   channels: {
>     discord: {
>       dmPolicy: "allowlist",
>       allowFrom: ["accessGroup:maintainers"],
>     },
>   },
> }
> ```

```json5
{
  accessGroups: {
    maintainers: {
      type: "discord.channelAudience",
      guildId: "1456350064065904867",
      channelId: "1456744319972282449",
      membership: "canViewChannel",
    },
  },
  channels: {
    discord: {
      dmPolicy: "allowlist",
      allowFrom: ["accessGroup:maintainers"],
    },
  },
}
```

> `discord.channelAudience` means "allow Discord DM senders who can currently view this guild channel." OpenClaw resolves the sender through Discord at authorization time and applies Discord `ViewChannel` permission rules.

`discord.channelAudience` 的含义是"放行那些当前能看到这个 guild 频道的 Discord 私聊发件人"。授权时 OpenClaw 通过 Discord 解析发件人，按 Discord 的 `ViewChannel` 权限规则判断。

> Use this when a Discord channel is already the source of truth for a team, such as `#maintainers` or `#on-call`.

适合 Discord 频道本身就是某个团队权威名单的情况，比如 `#maintainers` 或 `#on-call`。

> Requirements and failure behavior:
>
> * The bot needs access to the guild and channel.
> * The bot needs the Discord Developer Portal **Server Members Intent**.
> * The access group fails closed when Discord returns `Missing Access`, the sender cannot be resolved as a guild member, or the channel belongs to another guild.

要求和失败时的行为：

- 机器人要能访问这个 guild 和频道。
- 机器人在 Discord 开发者后台要打开 **Server Members Intent**。
- 出现以下情况时，访问组会"fail closed"（默认拒绝）：Discord 返回 `Missing Access`、发件人解析不出来不是 guild 成员、频道属于另一个 guild。

> More Discord-specific examples: [Discord access control](/channels/discord#access-control-and-routing)

更多 Discord 相关的例子：[Discord 访问控制](/channels/discord#access-control-and-routing)。

---

> ## Security notes

## 安全注意事项

> * Access groups are allowlist aliases, not roles. They do not create owners, approve pairing requests, or grant tool permissions by themselves.
> * `dmPolicy: "open"` still requires `"*"` in the effective DM allowlist. Referencing an access group is not the same as public access.
> * Missing group names fail closed. If `allowFrom` contains `accessGroup:operators` and `accessGroups.operators` is absent, that entry authorizes nobody.
> * Keep channel ids stable. Prefer numeric/user ids over display names when the channel supports both.

- 访问组只是白名单别名，不是 role。它本身不会创建所有者、不会批准配对请求、也不会授予工具权限。
- `dmPolicy: "open"` 仍然要求有效的 DM 白名单里写了 `"*"`。引用一个访问组并不等同于"对外开放"。
- 找不到的组名按"fail closed"处理。`allowFrom` 里写了 `accessGroup:operators` 但 `accessGroups.operators` 不存在时，这条条目谁也不放行。
- 通道 ID 要稳定。通道同时支持数字 ID 和显示名时，优先用数字 / 用户 ID。

---

> ## Troubleshooting

## 故障排查

> If a sender should match but is blocked:
>
> 1. Confirm the allowlist field contains the exact `accessGroup:<name>` reference.
> 2. Confirm `accessGroups.<name>.type` is correct.
> 3. Confirm the sender id is listed under the matching channel key, or under `"*"`.
> 4. Confirm the entry uses that channel's normal allowlist syntax.
> 5. For Discord channel audiences, confirm the bot can see the guild channel and has Server Members Intent enabled.

某个发件人按理应该匹配上，却被拦了：

1. 确认白名单字段里写的就是 `accessGroup:<名字>` 这种引用。
2. 确认 `accessGroups.<名字>.type` 写对了。
3. 确认发件人 ID 在对应通道的 key 下，或写在 `"*"` 下。
4. 确认条目格式符合该通道自己白名单的语法。
5. 用 Discord 频道受众组的话，确认机器人能看到这个 guild 频道，并且打开了 Server Members Intent。

> Run `openclaw doctor` after editing access-control config. It catches many invalid allowlist and policy combinations before runtime.

改完访问控制配置后跑一下 `openclaw doctor`。运行前它能捕获很多白名单和策略的非法组合。
