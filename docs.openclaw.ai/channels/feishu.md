# Feishu

> Feishu/Lark is an all-in-one collaboration platform where teams chat, share documents, manage calendars, and get work done together.

飞书/Lark 是一个一体化协作平台，团队在上面聊天、共享文档、管理日历、协同推进工作。

> **Status:** production-ready for bot DMs + group chats. WebSocket is the default mode; webhook mode is optional.

**状态：** 机器人私聊和群聊已生产可用。默认走 WebSocket，Webhook 模式可选。

---

> ## Quick start

## 快速开始

> <Note>
>   Requires OpenClaw 2026.4.25 or above. Run `openclaw --version` to check. Upgrade with `openclaw update`.
> </Note>

> **提示**：需要 OpenClaw 2026.4.25 或以上版本。跑 `openclaw --version` 查看版本，用 `openclaw update` 升级。

> [步骤 1: Run the channel setup wizard]
>
> ```bash
> openclaw channels login --channel feishu
> ```
>
> Choose manual setup to paste an App ID and App Secret from Feishu Open Platform, or choose QR setup to create a bot automatically. If the domestic Feishu mobile app does not react to the QR code, rerun setup and choose manual setup.

[步骤 1：跑通道配置向导]

```bash
openclaw channels login --channel feishu
```

可以选手动配置，把飞书开放平台拿到的 App ID 和 App Secret 粘进去；也可以选扫码配置，自动建一个机器人。如果国内飞书手机端对二维码没反应，重新跑一次配置，改用手动方式。

> [步骤 2: After setup completes, restart the gateway to apply the changes]
>
> ```bash
> openclaw gateway restart
> ```

[步骤 2：配置完成后重启 Gateway，让改动生效]

```bash
openclaw gateway restart
```

---

> ## Access control

## 访问控制

> ### Direct messages

### 私聊

> Configure `dmPolicy` to control who can DM the bot:
>
> * `"pairing"` - unknown users receive a pairing code; approve via CLI
> * `"allowlist"` - only users listed in `allowFrom` can chat (default: bot owner only)
> * `"open"` - allow public DMs only when `allowFrom` includes `"*"`; with restrictive entries, only matching users can chat
> * `"disabled"` - disable all DMs

通过 `dmPolicy` 控制谁可以私聊机器人：

- `"pairing"`：陌生人会收到配对码，通过 CLI 批准。
- `"allowlist"`：只有 `allowFrom` 列表里的用户能聊（默认只有机器人所有者）。
- `"open"`：当且仅当 `allowFrom` 包含 `"*"` 时允许任何人私聊；如果列表里写的是具体限制项，只有匹配上的用户能聊。
- `"disabled"`：关掉所有私聊。

> **Approve a pairing request:**

**批准配对请求：**

> ```bash
> openclaw pairing list feishu
> openclaw pairing approve feishu <CODE>
> ```

```bash
openclaw pairing list feishu
openclaw pairing approve feishu <CODE>
```

> ### Group chats

### 群聊

> **Group policy** (`channels.feishu.groupPolicy`):

**群策略**（`channels.feishu.groupPolicy`）：

> | Value         | Behavior                                                                                     |
> | ------------- | -------------------------------------------------------------------------------------------- |
> | `"open"`      | Respond to all messages in groups                                                            |
> | `"allowlist"` | Only respond to groups in `groupAllowFrom` or explicitly configured under `groups.<chat_id>` |
> | `"disabled"`  | Disable all group messages; explicit `groups.<chat_id>` entries do not override this         |

| 取值          | 行为                                                                          |
| ------------- | ----------------------------------------------------------------------------- |
| `"open"`      | 群里所有消息都回                                                              |
| `"allowlist"` | 只回 `groupAllowFrom` 列表里的群，或在 `groups.<chat_id>` 里显式配置过的群     |
| `"disabled"`  | 关掉所有群消息；`groups.<chat_id>` 里的显式条目也覆盖不了                      |

> Default: `allowlist`

默认值：`allowlist`。

> **Mention requirement** (`channels.feishu.requireMention`):
>
> * `true` - require @mention (default)
> * `false` - respond without @mention
> * Per-group override: `channels.feishu.groups.<chat_id>.requireMention`
> * Broadcast-only `@all` and `@_all` are not treated as bot mentions. A message that mentions both `@all` and the bot directly still counts as a bot mention.

**@ 要求**（`channels.feishu.requireMention`）：

- `true`：必须 @ 机器人才回（默认）。
- `false`：不 @ 也回。
- 单个群可以单独覆盖：`channels.feishu.groups.<chat_id>.requireMention`。
- 单纯的 `@all` 和 `@_all` 广播 @，不算 @ 到机器人。一条消息同时 @all 又直接 @ 了机器人，还是算 @ 到了机器人。

---

> ## Group configuration examples

## 群配置示例

> ### Allow all groups, no @mention required

### 所有群都放行，不需要 @ 机器人

> ```json5
> {
>   channels: {
>     feishu: {
>       groupPolicy: "open",
>     },
>   },
> }
> ```

```json5
{
  channels: {
    feishu: {
      groupPolicy: "open",
    },
  },
}
```

> ### Allow all groups, still require @mention

### 所有群都放行，但仍要求 @ 机器人

> ```json5
> {
>   channels: {
>     feishu: {
>       groupPolicy: "open",
>       requireMention: true,
>     },
>   },
> }
> ```

```json5
{
  channels: {
    feishu: {
      groupPolicy: "open",
      requireMention: true,
    },
  },
}
```

> ### Allow specific groups only

### 只放行特定的群

> ```json5
> {
>   channels: {
>     feishu: {
>       groupPolicy: "allowlist",
>       // Group IDs look like: oc_xxx
>       groupAllowFrom: ["oc_xxx", "oc_yyy"],
>     },
>   },
> }
> ```

```json5
{
  channels: {
    feishu: {
      groupPolicy: "allowlist",
      // 群 ID 形如 oc_xxx
      groupAllowFrom: ["oc_xxx", "oc_yyy"],
    },
  },
}
```

> In `allowlist` mode, you can also admit a group by adding an explicit `groups.<chat_id>` entry. Explicit entries do not override `groupPolicy: "disabled"`. Wildcard defaults under `groups.*` configure matching groups, but they do not admit groups by themselves.

在 `allowlist` 模式下，加一条显式的 `groups.<chat_id>` 条目也能放行某个群。但显式条目压不过 `groupPolicy: "disabled"`。`groups.*` 下的通配默认值只用来给匹配上的群配参数，本身不会放行任何群。

> ```json5
> {
>   channels: {
>     feishu: {
>       groupPolicy: "allowlist",
>       groups: {
>         oc_xxx: {
>           requireMention: false,
>         },
>       },
>     },
>   },
> }
> ```

```json5
{
  channels: {
    feishu: {
      groupPolicy: "allowlist",
      groups: {
        oc_xxx: {
          requireMention: false,
        },
      },
    },
  },
}
```

> ### Restrict senders within a group

### 限制群内的发件人

> ```json5
> {
>   channels: {
>     feishu: {
>       groupPolicy: "allowlist",
>       groupAllowFrom: ["oc_xxx"],
>       groups: {
>         oc_xxx: {
>           // User open_ids look like: ou_xxx
>           allowFrom: ["ou_user1", "ou_user2"],
>         },
>       },
>     },
>   },
> }
> ```

```json5
{
  channels: {
    feishu: {
      groupPolicy: "allowlist",
      groupAllowFrom: ["oc_xxx"],
      groups: {
        oc_xxx: {
          // 用户 open_id 形如 ou_xxx
          allowFrom: ["ou_user1", "ou_user2"],
        },
      },
    },
  },
}
```

---

<a id="get-groupuser-ids" />

> ## Get group/user IDs

## 获取群 ID 和用户 ID

> ### Group IDs (`chat_id`, format: `oc_xxx`)

### 群 ID（`chat_id`，格式 `oc_xxx`）

> Open the group in Feishu/Lark, click the menu icon in the top-right corner, and go to **Settings**. The group ID (`chat_id`) is listed on the settings page.

在飞书/Lark 里打开群，点右上角菜单图标，进 **设置**。群 ID（`chat_id`）就在设置页里列着。

> <img src="https://mintcdn.com/clawdhub/0NpU6wNaI7exeaOE/images/feishu-get-group-id.png?fit=max&auto=format&n=0NpU6wNaI7exeaOE&q=85&s=1c9b41e1f9743621dfdd3abf7e952405" alt="Get Group ID" width="1636" height="1764" data-path="images/feishu-get-group-id.png" />

<img src="https://mintcdn.com/clawdhub/0NpU6wNaI7exeaOE/images/feishu-get-group-id.png?fit=max&auto=format&n=0NpU6wNaI7exeaOE&q=85&s=1c9b41e1f9743621dfdd3abf7e952405" alt="获取群 ID" width="1636" height="1764" data-path="images/feishu-get-group-id.png" />

> ### User IDs (`open_id`, format: `ou_xxx`)

### 用户 ID（`open_id`，格式 `ou_xxx`）

> Start the gateway, send a DM to the bot, then check the logs:

启动 Gateway，给机器人发一条私聊，然后看日志：

> ```bash
> openclaw logs --follow
> ```

```bash
openclaw logs --follow
```

> Look for `open_id` in the log output. You can also check pending pairing requests:

在日志输出里找 `open_id`。也可以查看待处理的配对请求：

> ```bash
> openclaw pairing list feishu
> ```

```bash
openclaw pairing list feishu
```

---

> ## Common commands

## 常用命令

> | Command   | Description                 |
> | --------- | --------------------------- |
> | `/status` | Show bot status             |
> | `/reset`  | Reset the current session   |
> | `/model`  | Show or switch the AI model |

| 命令      | 说明                |
| --------- | ------------------- |
| `/status` | 查看机器人状态      |
| `/reset`  | 重置当前会话        |
| `/model`  | 查看或切换 AI 模型  |

> <Note>
>   Feishu/Lark does not support native slash-command menus, so send these as plain text messages.
> </Note>

> **提示**：飞书/Lark 不支持原生斜杠命令菜单，把这些当普通文本消息发出去就行。

---

> ## Troubleshooting

## 故障排查

> ### Bot does not respond in group chats

### 群里机器人不回复

> 1. Ensure the bot is added to the group
> 2. Ensure you @mention the bot (required by default)
> 3. Verify `groupPolicy` is not `"disabled"`
> 4. Check logs: `openclaw logs --follow`

1. 确认机器人已经被拉进了群。
2. 确认你 @ 了机器人（默认要 @）。
3. 确认 `groupPolicy` 不是 `"disabled"`。
4. 查日志：`openclaw logs --follow`。

> ### Bot does not receive messages

### 机器人收不到消息

> 1. Ensure the bot is published and approved in Feishu Open Platform / Lark Developer
> 2. Ensure event subscription includes `im.message.receive_v1`
> 3. Ensure **persistent connection** (WebSocket) is selected
> 4. Ensure all required permission scopes are granted
> 5. Ensure the gateway is running: `openclaw gateway status`
> 6. Check logs: `openclaw logs --follow`

1. 确认机器人在飞书开放平台 / Lark Developer 里已经发布并通过审核。
2. 确认事件订阅里包含 `im.message.receive_v1`。
3. 确认选的是 **长连接**（WebSocket）。
4. 确认所有需要的权限范围都已授权。
5. 确认 Gateway 在跑：`openclaw gateway status`。
6. 查日志：`openclaw logs --follow`。

> ### QR setup does not react in the Feishu mobile app

### 飞书手机端对扫码配置没反应

> 1. Rerun setup: `openclaw channels login --channel feishu`
> 2. Choose manual setup
> 3. In Feishu Open Platform, create a self-built app and copy its App ID and App Secret
> 4. Paste those credentials into the setup wizard

1. 重新跑配置：`openclaw channels login --channel feishu`。
2. 选手动配置。
3. 在飞书开放平台新建一个自建应用，复制它的 App ID 和 App Secret。
4. 把这两个凭证粘到配置向导里。

> ### App Secret leaked

### App Secret 泄漏了

> 1. Reset the App Secret in Feishu Open Platform / Lark Developer
> 2. Update the value in your config
> 3. Restart the gateway: `openclaw gateway restart`

1. 在飞书开放平台 / Lark Developer 里重置 App Secret。
2. 在配置里改成新值。
3. 重启 Gateway：`openclaw gateway restart`。

---

> ## Advanced configuration

## 高级配置

> ### Multiple accounts

### 多账号

> ```json5
> {
>   channels: {
>     feishu: {
>       defaultAccount: "main",
>       accounts: {
>         main: {
>           appId: "cli_xxx",
>           appSecret: "xxx",
>           name: "Primary bot",
>           tts: {
>             providers: {
>               openai: { voice: "shimmer" },
>             },
>           },
>         },
>         backup: {
>           appId: "cli_yyy",
>           appSecret: "yyy",
>           name: "Backup bot",
>           enabled: false,
>         },
>       },
>     },
>   },
> }
> ```

```json5
{
  channels: {
    feishu: {
      defaultAccount: "main",
      accounts: {
        main: {
          appId: "cli_xxx",
          appSecret: "xxx",
          name: "Primary bot",
          tts: {
            providers: {
              openai: { voice: "shimmer" },
            },
          },
        },
        backup: {
          appId: "cli_yyy",
          appSecret: "yyy",
          name: "Backup bot",
          enabled: false,
        },
      },
    },
  },
}
```

> `defaultAccount` controls which account is used when outbound APIs do not specify an `accountId`.
> `accounts.<id>.tts` uses the same shape as `messages.tts` and deep-merges over global TTS config, so multi-bot Feishu setups can keep shared provider credentials globally while overriding only voice, model, persona, or auto mode per account.

`defaultAccount` 决定发送 API 没指定 `accountId` 时走哪个账号。`accounts.<id>.tts` 的结构跟 `messages.tts` 一致，会与全局 TTS 配置深合并。这样多机器人飞书部署可以把 provider 凭证统一放在全局，每个账号只覆盖 voice、model、persona 或 auto 模式即可。

> ### Message limits

### 消息上限

> * `textChunkLimit` - outbound text chunk size (default: `2000` chars)
> * `mediaMaxMb` - media upload/download limit (default: `30` MB)

- `textChunkLimit`：发出去的文本分片大小（默认 `2000` 字符）。
- `mediaMaxMb`：媒体上传/下载上限（默认 `30` MB）。

> ### Streaming

### 流式输出

> Feishu/Lark supports streaming replies via interactive cards. When enabled, the bot updates the card in real time as it generates text.

飞书/Lark 通过交互卡片支持流式回复。开启后，机器人一边生成文本，一边实时更新卡片。

> ```json5
> {
>   channels: {
>     feishu: {
>       streaming: true, // enable streaming card output (default: true)
>       blockStreaming: true, // opt into completed-block streaming
>     },
>   },
> }
> ```

```json5
{
  channels: {
    feishu: {
      streaming: true, // 开启流式卡片输出（默认 true）
      blockStreaming: true, // 选择性开启已完成块的流式输出
    },
  },
}
```

> Set `streaming: false` to send the complete reply in one message. `blockStreaming` is off by default; enable it only when you want completed assistant blocks flushed before the final reply.

把 `streaming` 设成 `false`，机器人会一次性发完整回复。`blockStreaming` 默认关，需要让助手已完成的内容块在最终回复前先输出时再开。

> ### Quota optimization

### 配额优化

> Reduce the number of Feishu/Lark API calls with two optional flags:
>
> * `typingIndicator` (default `true`): set `false` to skip typing reaction calls
> * `resolveSenderNames` (default `true`): set `false` to skip sender profile lookups

两个可选开关可以减少飞书/Lark API 调用次数：

- `typingIndicator`（默认 `true`）：设成 `false` 跳过输入中状态的调用。
- `resolveSenderNames`（默认 `true`）：设成 `false` 跳过发件人资料查询。

> ```json5
> {
>   channels: {
>     feishu: {
>       typingIndicator: false,
>       resolveSenderNames: false,
>     },
>   },
> }
> ```

```json5
{
  channels: {
    feishu: {
      typingIndicator: false,
      resolveSenderNames: false,
    },
  },
}
```

> ### ACP sessions

### ACP 会话

> Feishu/Lark supports ACP for DMs and group thread messages. Feishu/Lark ACP is text-command driven - there are no native slash-command menus, so use `/acp ...` messages directly in the conversation.

飞书/Lark 在私聊和群话题里都支持 ACP。飞书/Lark 的 ACP 是文本命令驱动的，没有原生斜杠命令菜单，直接在对话里发 `/acp ...` 消息即可。

> #### Persistent ACP binding

#### 持久化 ACP 绑定

> ```json5
> {
>   agents: {
>     list: [
>       {
>         id: "codex",
>         runtime: {
>           type: "acp",
>           acp: {
>             agent: "codex",
>             backend: "acpx",
>             mode: "persistent",
>             cwd: "/workspace/openclaw",
>           },
>         },
>       },
>     ],
>   },
>   bindings: [
>     {
>       type: "acp",
>       agentId: "codex",
>       match: {
>         channel: "feishu",
>         accountId: "default",
>         peer: { kind: "direct", id: "ou_1234567890" },
>       },
>     },
>     {
>       type: "acp",
>       agentId: "codex",
>       match: {
>         channel: "feishu",
>         accountId: "default",
>         peer: { kind: "group", id: "oc_group_chat:topic:om_topic_root" },
>       },
>       acp: { label: "codex-feishu-topic" },
>     },
>   ],
> }
> ```

```json5
{
  agents: {
    list: [
      {
        id: "codex",
        runtime: {
          type: "acp",
          acp: {
            agent: "codex",
            backend: "acpx",
            mode: "persistent",
            cwd: "/workspace/openclaw",
          },
        },
      },
    ],
  },
  bindings: [
    {
      type: "acp",
      agentId: "codex",
      match: {
        channel: "feishu",
        accountId: "default",
        peer: { kind: "direct", id: "ou_1234567890" },
      },
    },
    {
      type: "acp",
      agentId: "codex",
      match: {
        channel: "feishu",
        accountId: "default",
        peer: { kind: "group", id: "oc_group_chat:topic:om_topic_root" },
      },
      acp: { label: "codex-feishu-topic" },
    },
  ],
}
```

> #### Spawn ACP from chat

#### 从聊天里启动 ACP

> In a Feishu/Lark DM or thread:

在飞书/Lark 的私聊或话题里：

> ```text
> /acp spawn codex --thread here
> ```

```text
/acp spawn codex --thread here
```

> `--thread here` works for DMs and Feishu/Lark thread messages. Follow-up messages in the bound conversation route directly to that ACP session.

`--thread here` 适用于私聊和飞书/Lark 话题消息。绑定会话里的后续消息会直接路由到这个 ACP 会话。

> ### Multi-agent routing

### 多 agent 路由

> Use `bindings` to route Feishu/Lark DMs or groups to different agents.

通过 `bindings` 把飞书/Lark 的私聊或群路由到不同的 agent：

> ```json5
> {
>   agents: {
>     list: [
>       { id: "main" },
>       { id: "agent-a", workspace: "/home/user/agent-a" },
>       { id: "agent-b", workspace: "/home/user/agent-b" },
>     ],
>   },
>   bindings: [
>     {
>       agentId: "agent-a",
>       match: {
>         channel: "feishu",
>         peer: { kind: "direct", id: "ou_xxx" },
>       },
>     },
>     {
>       agentId: "agent-b",
>       match: {
>         channel: "feishu",
>         peer: { kind: "group", id: "oc_zzz" },
>       },
>     },
>   ],
> }
> ```

```json5
{
  agents: {
    list: [
      { id: "main" },
      { id: "agent-a", workspace: "/home/user/agent-a" },
      { id: "agent-b", workspace: "/home/user/agent-b" },
    ],
  },
  bindings: [
    {
      agentId: "agent-a",
      match: {
        channel: "feishu",
        peer: { kind: "direct", id: "ou_xxx" },
      },
    },
    {
      agentId: "agent-b",
      match: {
        channel: "feishu",
        peer: { kind: "group", id: "oc_zzz" },
      },
    },
  ],
}
```

> Routing fields:
>
> * `match.channel`: `"feishu"`
> * `match.peer.kind`: `"direct"` (DM) or `"group"` (group chat)
> * `match.peer.id`: user Open ID (`ou_xxx`) or group ID (`oc_xxx`)

路由字段：

- `match.channel`：`"feishu"`。
- `match.peer.kind`：`"direct"`（私聊）或 `"group"`（群聊）。
- `match.peer.id`：用户 Open ID（`ou_xxx`）或群 ID（`oc_xxx`）。

> See [Get group/user IDs](#get-groupuser-ids) for lookup tips.

查询方法见 [获取群 ID 和用户 ID](#get-groupuser-ids)。

---

> ## Configuration reference

## 配置项参考

> Full configuration: [Gateway configuration](/gateway/configuration)

完整配置：[Gateway 配置](/gateway/configuration)

> | Setting                                           | Description                                                                      | Default          |
> | ------------------------------------------------- | -------------------------------------------------------------------------------- | ---------------- |
> | `channels.feishu.enabled`                         | Enable/disable the channel                                                       | `true`           |
> | `channels.feishu.domain`                          | API domain (`feishu` or `lark`)                                                  | `feishu`         |
> | `channels.feishu.connectionMode`                  | Event transport (`websocket` or `webhook`)                                       | `websocket`      |
> | `channels.feishu.defaultAccount`                  | Default account for outbound routing                                             | `default`        |
> | `channels.feishu.verificationToken`               | Required for webhook mode                                                        | -                |
> | `channels.feishu.encryptKey`                      | Required for webhook mode                                                        | -                |
> | `channels.feishu.webhookPath`                     | Webhook route path                                                               | `/feishu/events` |
> | `channels.feishu.webhookHost`                     | Webhook bind host                                                                | `127.0.0.1`      |
> | `channels.feishu.webhookPort`                     | Webhook bind port                                                                | `3000`           |
> | `channels.feishu.accounts.<id>.appId`             | App ID                                                                           | -                |
> | `channels.feishu.accounts.<id>.appSecret`         | App Secret                                                                       | -                |
> | `channels.feishu.accounts.<id>.domain`            | Per-account domain override                                                      | `feishu`         |
> | `channels.feishu.accounts.<id>.tts`               | Per-account TTS override                                                         | `messages.tts`   |
> | `channels.feishu.dmPolicy`                        | DM policy                                                                        | `allowlist`      |
> | `channels.feishu.allowFrom`                       | DM allowlist (open\_id list)                                                     | \[BotOwnerId]    |
> | `channels.feishu.groupPolicy`                     | Group policy                                                                     | `allowlist`      |
> | `channels.feishu.groupAllowFrom`                  | Group allowlist                                                                  | -                |
> | `channels.feishu.requireMention`                  | Require @mention in groups                                                       | `true`           |
> | `channels.feishu.groups.<chat_id>.requireMention` | Per-group @mention override; explicit IDs also admit the group in allowlist mode | inherited        |
> | `channels.feishu.groups.<chat_id>.enabled`        | Enable/disable a specific group                                                  | `true`           |
> | `channels.feishu.textChunkLimit`                  | Message chunk size                                                               | `2000`           |
> | `channels.feishu.mediaMaxMb`                      | Media size limit                                                                 | `30`             |
> | `channels.feishu.streaming`                       | Streaming card output                                                            | `true`           |
> | `channels.feishu.blockStreaming`                  | Completed-block reply streaming                                                  | `false`          |
> | `channels.feishu.typingIndicator`                 | Send typing reactions                                                            | `true`           |
> | `channels.feishu.resolveSenderNames`              | Resolve sender display names                                                     | `true`           |

| 配置项                                            | 说明                                                                          | 默认值           |
| ------------------------------------------------- | ----------------------------------------------------------------------------- | ---------------- |
| `channels.feishu.enabled`                         | 启用 / 关闭通道                                                               | `true`           |
| `channels.feishu.domain`                          | API 域（`feishu` 或 `lark`）                                                  | `feishu`         |
| `channels.feishu.connectionMode`                  | 事件传输（`websocket` 或 `webhook`）                                          | `websocket`      |
| `channels.feishu.defaultAccount`                  | 发送时默认走的账号                                                            | `default`        |
| `channels.feishu.verificationToken`               | Webhook 模式必填                                                              | -                |
| `channels.feishu.encryptKey`                      | Webhook 模式必填                                                              | -                |
| `channels.feishu.webhookPath`                     | Webhook 路径                                                                  | `/feishu/events` |
| `channels.feishu.webhookHost`                     | Webhook 监听主机                                                              | `127.0.0.1`      |
| `channels.feishu.webhookPort`                     | Webhook 监听端口                                                              | `3000`           |
| `channels.feishu.accounts.<id>.appId`             | App ID                                                                        | -                |
| `channels.feishu.accounts.<id>.appSecret`         | App Secret                                                                    | -                |
| `channels.feishu.accounts.<id>.domain`            | 每个账号单独覆盖域                                                            | `feishu`         |
| `channels.feishu.accounts.<id>.tts`               | 每个账号单独覆盖 TTS                                                          | `messages.tts`   |
| `channels.feishu.dmPolicy`                        | 私聊策略                                                                      | `allowlist`      |
| `channels.feishu.allowFrom`                       | 私聊白名单（open\_id 列表）                                                   | \[BotOwnerId]    |
| `channels.feishu.groupPolicy`                     | 群策略                                                                        | `allowlist`      |
| `channels.feishu.groupAllowFrom`                  | 群白名单                                                                      | -                |
| `channels.feishu.requireMention`                  | 群里要不要 @ 机器人                                                           | `true`           |
| `channels.feishu.groups.<chat_id>.requireMention` | 单个群的 @ 覆盖；写在 `allowlist` 模式下，显式 ID 同时也起到放行该群的作用     | 继承             |
| `channels.feishu.groups.<chat_id>.enabled`        | 启用 / 关闭某个具体的群                                                       | `true`           |
| `channels.feishu.textChunkLimit`                  | 消息分片大小                                                                  | `2000`           |
| `channels.feishu.mediaMaxMb`                      | 媒体大小上限                                                                  | `30`             |
| `channels.feishu.streaming`                       | 流式卡片输出                                                                  | `true`           |
| `channels.feishu.blockStreaming`                  | 已完成块的流式回复                                                            | `false`          |
| `channels.feishu.typingIndicator`                 | 发送输入中状态                                                                | `true`           |
| `channels.feishu.resolveSenderNames`              | 解析发件人显示名                                                              | `true`           |

---

> ## Supported message types

## 支持的消息类型

> ### Receive

### 接收

> * ✅ Text
> * ✅ Rich text (post)
> * ✅ Images
> * ✅ Files
> * ✅ Audio
> * ✅ Video/media
> * ✅ Stickers

- ✅ 文本
- ✅ 富文本（post）
- ✅ 图片
- ✅ 文件
- ✅ 音频
- ✅ 视频 / 媒体
- ✅ 表情贴图

> Inbound Feishu/Lark audio messages are normalized as media placeholders instead of raw `file_key` JSON. When `tools.media.audio` is configured, OpenClaw downloads the voice-note resource and runs shared audio transcription before the agent turn, so the agent receives the spoken transcript. If Feishu includes transcript text directly in the audio payload, that text is used without another ASR call. Without an audio transcription provider, the agent still receives a `<media:audio>` placeholder plus the saved attachment, not the raw Feishu resource payload.

收到的飞书/Lark 语音消息会标准化成媒体占位符，不会直接给 agent 原始的 `file_key` JSON。配了 `tools.media.audio` 的话，OpenClaw 会先把语音文件下载下来，跑共用的音频转写流程，然后把语音文字稿交给 agent。如果飞书在音频载荷里已经带了转写文本，直接用，不再调一次 ASR。没配音频转写 provider 时，agent 拿到的是一个 `<media:audio>` 占位符加上已保存的附件，而不是飞书原始的资源载荷。

> ### Send

### 发送

> * ✅ Text
> * ✅ Images
> * ✅ Files
> * ✅ Audio
> * ✅ Video/media
> * ✅ Interactive cards (including streaming updates)
> * ⚠️ Rich text (post-style formatting; doesn't support full Feishu/Lark authoring capabilities)

- ✅ 文本
- ✅ 图片
- ✅ 文件
- ✅ 音频
- ✅ 视频 / 媒体
- ✅ 交互卡片（含流式更新）
- ⚠️ 富文本（post 风格的排版，不覆盖飞书/Lark 全部创作能力）

> Native Feishu/Lark audio bubbles use the Feishu `audio` message type and require Ogg/Opus upload media (`file_type: "opus"`). Existing `.opus` and `.ogg` media is sent directly as native audio. MP3/WAV/M4A and other likely audio formats are transcoded to 48kHz Ogg/Opus with `ffmpeg` only when the reply requests voice delivery (`audioAsVoice` / message tool `asVoice`, including TTS voice-note replies). Ordinary MP3 attachments stay regular files. If `ffmpeg` is missing or conversion fails, OpenClaw falls back to a file attachment and logs the reason.

飞书/Lark 原生语音气泡走 `audio` 消息类型，要求上传的媒体是 Ogg/Opus（`file_type: "opus"`）。已有的 `.opus` 和 `.ogg` 文件直接作为原生音频发送。MP3/WAV/M4A 之类的音频格式只有在回复明确要求语音投递时（`audioAsVoice` / 消息工具的 `asVoice`，包括 TTS 语音回复），才会用 `ffmpeg` 转码到 48kHz Ogg/Opus。普通的 MP3 附件保持文件附件形态。如果 `ffmpeg` 不在或转码失败，OpenClaw 会退回用文件附件发送，日志里记原因。

> ### Threads and replies

### 话题和回复

> * ✅ Inline replies
> * ✅ Thread replies
> * ✅ Media replies stay thread-aware when replying to a thread message

- ✅ 行内回复
- ✅ 话题回复
- ✅ 在话题消息里回复媒体时，仍能识别话题归属

> For `groupSessionScope: "group_topic"` and `"group_topic_sender"`, native Feishu/Lark topic groups use the event `thread_id` (`omt_*`) as the canonical topic session key. If a native topic starter event omits `thread_id`, OpenClaw hydrates it from Feishu before routing the turn. Normal group replies that OpenClaw turns into threads keep using the reply root message ID (`om_*`) so the first turn and follow-up turn stay in the same session.

`groupSessionScope` 是 `"group_topic"` 或 `"group_topic_sender"` 时，飞书/Lark 原生话题群把事件里的 `thread_id`（`omt_*`）当作话题会话的标准 key。如果原生话题起始事件里没带 `thread_id`，OpenClaw 会先去飞书补全这个字段，再路由这一轮。OpenClaw 自己把普通群回复升级成话题时，仍然用回复根消息 ID（`om_*`），让第一轮和后续轮处于同一个会话。

---

> ## Related

## 相关

> * [Channels Overview](/channels) - all supported channels
> * [Pairing](/channels/pairing) - DM authentication and pairing flow
> * [Groups](/channels/groups) - group chat behavior and mention gating
> * [Channel Routing](/channels/channel-routing) - session routing for messages
> * [Security](/gateway/security) - access model and hardening

- [通道总览](/channels)：所有支持的通道
- [配对](/channels/pairing)：私聊认证和配对流程
- [群组](/channels/groups)：群聊行为和 @ 触发规则
- [通道路由](/channels/channel-routing)：消息的会话路由
- [安全](/gateway/security)：访问模型和加固
