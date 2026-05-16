# QQ Bot

> QQ Bot connects to OpenClaw via the official QQ Bot API (WebSocket gateway). The plugin supports C2C private chat, group @messages, and guild channel messages with rich media (images, voice, video, files).

QQ 机器人通过官方 QQ Bot API（WebSocket 网关）接入 OpenClaw。插件支持 C2C 私聊、群里 @ 机器人的消息、QQ 频道消息，带富媒体（图片、语音、视频、文件）。

> Status: downloadable plugin. Direct messages, group chats, guild channels, and media are supported. Reactions and threads are not supported.

状态：可下载插件。支持私聊、群聊、QQ 频道、媒体。不支持表情回复（reaction）和子话题（thread）。

---

> ## Install

## 安装

> Install QQ Bot before setup:

配置之前先装插件：

> ```bash
> openclaw plugins install @openclaw/qqbot
> ```

```bash
openclaw plugins install @openclaw/qqbot
```

---

> ## Setup

## 配置步骤

> 1. Go to the [QQ Open Platform](https://q.qq.com/) and scan the QR code with your phone QQ to register / log in.
> 2. Click **Create Bot** to create a new QQ bot.
> 3. Find **AppID** and **AppSecret** on the bot's settings page and copy them.

1. 打开 [QQ 开放平台](https://q.qq.com/)，用手机 QQ 扫码注册或登录。
2. 点击 **创建机器人**，新建一个 QQ 机器人。
3. 在机器人设置页找到 **AppID** 和 **AppSecret**，复制下来。

> > AppSecret is not stored in plaintext — if you leave the page without saving it, you'll have to regenerate a new one.

> AppSecret 不会明文保存。离开页面前没保存的话，得重新生成一个。

> 4. Add the channel:

4. 添加通道：

> ```bash
> openclaw channels add --channel qqbot --token "AppID:AppSecret"
> ```

```bash
openclaw channels add --channel qqbot --token "AppID:AppSecret"
```

> 5. Restart the Gateway.

5. 重启 Gateway。

> Interactive setup paths:

交互式配置入口：

> ```bash
> openclaw channels add
> openclaw configure --section channels
> ```

```bash
openclaw channels add
openclaw configure --section channels
```

---

> ## Configure

## 配置项

> Minimal config:

最简配置：

> ```json5
> {
>   channels: {
>     qqbot: {
>       enabled: true,
>       appId: "YOUR_APP_ID",
>       clientSecret: "YOUR_APP_SECRET",
>     },
>   },
> }
> ```

```json5
{
  channels: {
    qqbot: {
      enabled: true,
      appId: "YOUR_APP_ID",
      clientSecret: "YOUR_APP_SECRET",
    },
  },
}
```

> Default-account env vars:
>
> * `QQBOT_APP_ID`
> * `QQBOT_CLIENT_SECRET`

默认账号的环境变量：

- `QQBOT_APP_ID`
- `QQBOT_CLIENT_SECRET`

> File-backed AppSecret:

把 AppSecret 放在文件里：

> ```json5
> {
>   channels: {
>     qqbot: {
>       enabled: true,
>       appId: "YOUR_APP_ID",
>       clientSecretFile: "/path/to/qqbot-secret.txt",
>     },
>   },
> }
> ```

```json5
{
  channels: {
    qqbot: {
      enabled: true,
      appId: "YOUR_APP_ID",
      clientSecretFile: "/path/to/qqbot-secret.txt",
    },
  },
}
```

> Env SecretRef AppSecret:

通过 SecretRef 从环境变量读 AppSecret：

> ```json5
> {
>   channels: {
>     qqbot: {
>       enabled: true,
>       appId: "YOUR_APP_ID",
>       clientSecret: { source: "env", provider: "default", id: "QQBOT_CLIENT_SECRET" },
>     },
>   },
> }
> ```

```json5
{
  channels: {
    qqbot: {
      enabled: true,
      appId: "YOUR_APP_ID",
      clientSecret: { source: "env", provider: "default", id: "QQBOT_CLIENT_SECRET" },
    },
  },
}
```

> Notes:
>
> * Env fallback applies to the default QQ Bot account only.
> * `openclaw channels add --channel qqbot --token-file ...` provides the AppSecret only; the AppID must already be set in config or `QQBOT_APP_ID`.
> * `clientSecret` also accepts SecretRef input, not just a plaintext string.
> * Legacy `secretref:/...` marker strings are not valid `clientSecret` values; use structured SecretRef objects like the example above.

注意：

- 环境变量回退只对默认 QQ Bot 账号生效。
- `openclaw channels add --channel qqbot --token-file ...` 只设置 AppSecret，AppID 仍要从配置或 `QQBOT_APP_ID` 里来。
- `clientSecret` 既可以是明文字符串，也可以是 SecretRef 对象。
- 旧版那种 `secretref:/...` 标记串不是合法的 `clientSecret` 值，请用上面这种结构化 SecretRef 对象。

---

> ### Multi-account setup

### 多账号配置

> Run multiple QQ bots under a single OpenClaw instance:

在一个 OpenClaw 实例下跑多个 QQ 机器人：

> ```json5
> {
>   channels: {
>     qqbot: {
>       enabled: true,
>       appId: "111111111",
>       clientSecret: "secret-of-bot-1",
>       accounts: {
>         bot2: {
>           enabled: true,
>           appId: "222222222",
>           clientSecret: "secret-of-bot-2",
>         },
>       },
>     },
>   },
> }
> ```

```json5
{
  channels: {
    qqbot: {
      enabled: true,
      appId: "111111111",
      clientSecret: "secret-of-bot-1",
      accounts: {
        bot2: {
          enabled: true,
          appId: "222222222",
          clientSecret: "secret-of-bot-2",
        },
      },
    },
  },
}
```

> Each account launches its own WebSocket connection and maintains an independent token cache (isolated by `appId`).

每个账号会起独立的 WebSocket 连接，按 `appId` 隔离 token 缓存。

> Add a second bot via CLI:

用 CLI 添加第二个机器人：

> ```bash
> openclaw channels add --channel qqbot --account bot2 --token "222222222:secret-of-bot-2"
> ```

```bash
openclaw channels add --channel qqbot --account bot2 --token "222222222:secret-of-bot-2"
```

---

> ### Group chats

### 群聊

> QQ Bot group chat support uses QQ group OpenIDs, not display names. Add the bot to a group, then mention it or configure the group to run without a mention.

QQ Bot 的群聊用 QQ 群 OpenID，不是显示名。把机器人拉进群之后，要么 @ 它，要么改配置让它不用 @ 也回应。

> ```json5
> {
>   channels: {
>     qqbot: {
>       groupPolicy: "allowlist",
>       groupAllowFrom: ["member_openid"],
>       groups: {
>         "*": {
>           requireMention: true,
>           historyLimit: 50,
>           toolPolicy: "restricted",
>         },
>         GROUP_OPENID: {
>           name: "Release room",
>           requireMention: false,
>           ignoreOtherMentions: true,
>           historyLimit: 20,
>           prompt: "Keep replies short and operational.",
>         },
>       },
>     },
>   },
> }
> ```

```json5
{
  channels: {
    qqbot: {
      groupPolicy: "allowlist",
      groupAllowFrom: ["member_openid"],
      groups: {
        "*": {
          requireMention: true,
          historyLimit: 50,
          toolPolicy: "restricted",
        },
        GROUP_OPENID: {
          name: "Release room",
          requireMention: false,
          ignoreOtherMentions: true,
          historyLimit: 20,
          prompt: "Keep replies short and operational.",
        },
      },
    },
  },
}
```

> `groups["*"]` sets defaults for every group, and a concrete `groups.GROUP_OPENID` entry overrides those defaults for one group. Group settings include:
>
> * `requireMention`: require an @mention before the bot replies. Default: `true`.
> * `ignoreOtherMentions`: drop messages that mention someone else but not the bot.
> * `historyLimit`: keep recent non-mention group messages as context for the next mentioned turn. Set `0` to disable.
> * `toolPolicy`: `full`, `restricted`, or `none` for group-scoped tools.
> * `name`: friendly label used in logs and group context.
> * `prompt`: per-group behavior prompt appended to the agent context.

`groups["*"]` 是所有群共享的默认值，单独的 `groups.GROUP_OPENID` 配置会覆盖某一个群的默认值。每个群可设的字段：

- `requireMention`：要 @ 机器人才回复，默认 `true`。
- `ignoreOtherMentions`：群里 @ 别人但没 @ 机器人的消息，丢弃不处理。
- `historyLimit`：保留最近的非 @ 群消息，作为下次被 @ 时的上下文，设 `0` 关闭。
- `toolPolicy`：群里工具的可用范围，`full` / `restricted` / `none`。
- `name`：日志和群上下文里展示的友好名字。
- `prompt`：每个群独立的行为提示词，附加到 agent 上下文里。

> Activation modes are `mention` and `always`. `requireMention: true` maps to `mention`; `requireMention: false` maps to `always`. A session-level activation override, when present, wins over config.

激活模式有 `mention` 和 `always` 两种。`requireMention: true` 对应 `mention`，`requireMention: false` 对应 `always`。会话级别有激活模式覆盖时，它优先于配置。

> The inbound queue is per peer. Group peers get a larger queue cap, keep human messages ahead of bot-authored chatter when full, and merge bursts of normal group messages into one attributed turn. Slash commands still run one by one.

接收队列按对端独立维护。群对端的队列容量更大；队列满时优先保留真人消息，淘汰机器人写的内容；密集到来的普通群消息会合并成一个带署名的轮次。斜杠命令照旧一条一条跑。

---

> ### Voice (STT / TTS)

### 语音（STT / TTS）

> STT and TTS support two-level configuration with priority fallback:

STT 和 TTS 支持两级配置，按优先级回退：

> | Setting | Plugin-specific                                          | Framework fallback            |
> | ------- | -------------------------------------------------------- | ----------------------------- |
> | STT     | `channels.qqbot.stt`                                     | `tools.media.audio.models[0]` |
> | TTS     | `channels.qqbot.tts`, `channels.qqbot.accounts.<id>.tts` | `messages.tts`                |

| 配置项 | 插件级专属                                               | 框架级回退                    |
| ------ | -------------------------------------------------------- | ----------------------------- |
| STT    | `channels.qqbot.stt`                                     | `tools.media.audio.models[0]` |
| TTS    | `channels.qqbot.tts`、`channels.qqbot.accounts.<id>.tts` | `messages.tts`                |

> ```json5
> {
>   channels: {
>     qqbot: {
>       stt: {
>         provider: "your-provider",
>         model: "your-stt-model",
>       },
>       tts: {
>         provider: "your-provider",
>         model: "your-tts-model",
>         voice: "your-voice",
>       },
>       accounts: {
>         "qq-main": {
>           tts: {
>             providers: {
>               openai: { voice: "shimmer" },
>             },
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
    qqbot: {
      stt: {
        provider: "your-provider",
        model: "your-stt-model",
      },
      tts: {
        provider: "your-provider",
        model: "your-tts-model",
        voice: "your-voice",
      },
      accounts: {
        "qq-main": {
          tts: {
            providers: {
              openai: { voice: "shimmer" },
            },
          },
        },
      },
    },
  },
}
```

> Set `enabled: false` on either to disable.
> Account-level TTS overrides use the same shape as `messages.tts` and deep-merge over the channel/global TTS config.

把任一项设成 `enabled: false` 即可关闭。账号级的 TTS 覆盖配置结构和 `messages.tts` 一致，会跟通道级、全局级的 TTS 配置做深合并。

> Inbound QQ voice attachments are exposed to agents as audio media metadata while keeping raw voice files out of generic `MediaPaths`. `[[audio_as_voice]]` plain text replies synthesize TTS and send a native QQ voice message when TTS is configured.

收到的 QQ 语音消息以音频媒体元数据的形式给 agent，原始语音文件不出现在通用的 `MediaPaths` 里。回复内容里写 `[[audio_as_voice]]` 纯文本，且 TTS 已配置时，会合成语音并发出 QQ 原生语音消息。

> Outbound audio upload/transcode behavior can also be tuned with `channels.qqbot.audioFormatPolicy`:
>
> * `sttDirectFormats`
> * `uploadDirectFormats`
> * `transcodeEnabled`

发送音频时的上传和转码行为可以通过 `channels.qqbot.audioFormatPolicy` 调整：

- `sttDirectFormats`
- `uploadDirectFormats`
- `transcodeEnabled`

---

> ## Target formats

## 目标地址格式

> | Format                     | Description        |
> | -------------------------- | ------------------ |
> | `qqbot:c2c:OPENID`         | Private chat (C2C) |
> | `qqbot:group:GROUP_OPENID` | Group chat         |
> | `qqbot:channel:CHANNEL_ID` | Guild channel      |

| 格式                       | 说明        |
| -------------------------- | ----------- |
| `qqbot:c2c:OPENID`         | 私聊（C2C） |
| `qqbot:group:GROUP_OPENID` | 群聊        |
| `qqbot:channel:CHANNEL_ID` | QQ 频道     |

> > Each bot has its own set of user OpenIDs. An OpenID received by Bot A **cannot** be used to send messages via Bot B.

> 每个机器人有自己一套用户 OpenID。机器人 A 收到的 OpenID **不能**拿去通过机器人 B 发消息。

---

> ## Slash commands

## 斜杠命令

> Built-in commands intercepted before the AI queue:

进 AI 队列之前会被拦截的内置命令：

> | Command        | Description                                                                                              |
> | -------------- | -------------------------------------------------------------------------------------------------------- |
> | `/bot-ping`    | Latency test                                                                                             |
> | `/bot-version` | Show the OpenClaw framework version                                                                      |
> | `/bot-help`    | List all commands                                                                                        |
> | `/bot-me`      | Show the sender's QQ user ID (openid) for `allowFrom`/`groupAllowFrom` setup                             |
> | `/bot-upgrade` | Show the QQBot upgrade guide link                                                                        |
> | `/bot-logs`    | Export recent gateway logs as a file                                                                     |
> | `/bot-approve` | Approve a pending QQ Bot action (for example, confirming a C2C or group upload) through the native flow. |

| 命令           | 说明                                                                  |
| -------------- | --------------------------------------------------------------------- |
| `/bot-ping`    | 延迟测试                                                              |
| `/bot-version` | 显示 OpenClaw 框架版本                                                |
| `/bot-help`    | 列出所有命令                                                          |
| `/bot-me`      | 显示发送者的 QQ 用户 ID（openid），方便配 `allowFrom`/`groupAllowFrom` |
| `/bot-upgrade` | 显示 QQBot 升级指引链接                                               |
| `/bot-logs`    | 把最近的网关日志导出成文件                                            |
| `/bot-approve` | 通过原生流程批准一个待处理的 QQ Bot 操作（比如确认 C2C 或群里的上传） |

> Append `?` to any command for usage help (for example `/bot-upgrade ?`).

任意命令后面加 `?` 可以查用法（比如 `/bot-upgrade ?`）。

> Admin commands (`/bot-me`, `/bot-upgrade`, `/bot-logs`, `/bot-clear-storage`, `/bot-streaming`, `/bot-approve`) are direct-message-only and require the sender's openid in an explicit non-wildcard `allowFrom` list. A wildcard `allowFrom: ["*"]` permits chat but does not grant admin command access. Group messages match against `groupAllowFrom` first and fall back to `allowFrom`. Running an admin command in a group returns a hint rather than silently dropping.

管理命令（`/bot-me`、`/bot-upgrade`、`/bot-logs`、`/bot-clear-storage`、`/bot-streaming`、`/bot-approve`）只能在私聊里用，发送者的 openid 必须出现在一个显式的（非通配）`allowFrom` 列表里。通配 `allowFrom: ["*"]` 允许聊天，但不给管理命令权限。群消息先匹配 `groupAllowFrom`，匹配不到再回退到 `allowFrom`。在群里跑管理命令不会被静默丢掉，而是返回一条提示。

---

> ## Engine architecture

## 引擎架构

> QQ Bot ships as a self-contained engine inside the plugin:
>
> * Each account owns an isolated resource stack (WebSocket connection, API client, token cache, media storage root) keyed by `appId`. Accounts never share inbound/outbound state.
> * The multi-account logger tags log lines with the owning account so diagnostics stay separable when you run several bots under one gateway.
> * Inbound, outbound, and gateway bridge paths share a single media payload root under `~/.openclaw/media`, so uploads, downloads, and transcode caches land under one guarded directory instead of a per-subsystem tree.
> * Rich media delivery goes through one `sendMedia` path for C2C and group targets. Local files and buffers above the large-file threshold use QQ's chunked upload endpoints, while smaller payloads use the one-shot media API.
> * Credentials can be backed up and restored as part of standard OpenClaw credential snapshots; the engine re-attaches each account's resource stack on restore without requiring a fresh QR-code pair.

QQ Bot 在插件内部是个独立引擎：

- 每个账号有自己独立的资源栈（WebSocket 连接、API 客户端、token 缓存、媒体存储根目录），按 `appId` 隔离。账号之间不共享接收和发送状态。
- 多账号日志器会给每条日志打上所属账号的标签，一个网关下跑多个机器人时，诊断信息互相不会串。
- 接收链路、发送链路、网关桥接路径共用 `~/.openclaw/media` 下的同一个媒体根目录，所有上传、下载、转码缓存都落在这一个受控目录里，不是每个子系统一棵树。
- C2C 和群里的富媒体投递走同一条 `sendMedia` 链路。本地文件或缓冲区超过大文件阈值时走 QQ 的分块上传接口，小的走一次性媒体 API。
- 凭证可以走标准 OpenClaw 凭证快照流程备份和恢复。恢复时引擎会自动给每个账号挂回资源栈，不用重新扫码配对。

---

> ## QR-code onboarding

## 扫码引导

> As an alternative to pasting `AppID:AppSecret` manually, the engine supports a QR-code onboarding flow for linking a QQ Bot to OpenClaw:
>
> 1. Run the QQ Bot setup path (for example `openclaw channels add --channel qqbot`) and pick the QR-code flow when prompted.
> 2. Scan the generated QR code with the phone app tied to the target QQ Bot.
> 3. Approve the pairing on the phone. OpenClaw persists the returned credentials into `credentials/` under the right account scope.

除了手动粘 `AppID:AppSecret`，引擎也支持扫码绑定 QQ 机器人：

1. 跑 QQ Bot 配置入口（比如 `openclaw channels add --channel qqbot`），出现提示时选扫码流程。
2. 用绑定该 QQ 机器人的那个手机 App 扫生成出来的二维码。
3. 在手机上确认配对。OpenClaw 会把返回的凭证存到 `credentials/` 下对应的账号作用域里。

> Approval prompts generated by the bot itself (for example, "allow this action?" flows exposed by the QQ Bot API) surface as native OpenClaw prompts that you can accept with `/bot-approve` rather than replying through the raw QQ client.

机器人自身发出的批准提示（比如 QQ Bot API 里"允许这个操作吗？"这种流程），会以 OpenClaw 原生提示的形式弹出来，用 `/bot-approve` 接受即可，不必去原生 QQ 客户端回复。

---

> ## Troubleshooting

## 故障排查

> * **Bot replies "gone to Mars":** credentials not configured or Gateway not started.
> * **No inbound messages:** verify `appId` and `clientSecret` are correct, and the bot is enabled on the QQ Open Platform.
> * **Repeated self-replies:** OpenClaw records QQ outbound ref indexes as bot-authored and ignores inbound events whose current `msgIdx` matches that same bot account. This prevents platform echo loops while still allowing users to quote or reply to previous bot messages.
> * **Setup with `--token-file` still shows unconfigured:** `--token-file` only sets the AppSecret. You still need `appId` in config or `QQBOT_APP_ID`.
> * **Proactive messages not arriving:** QQ may intercept bot-initiated messages if the user hasn't interacted recently.
> * **Voice not transcribed:** ensure STT is configured and the provider is reachable.

- **机器人回复 "gone to Mars"**：凭证没配，或者 Gateway 没起。
- **收不到消息**：检查 `appId` 和 `clientSecret` 是否正确，以及机器人在 QQ 开放平台是否启用。
- **机器人反复回复自己**：OpenClaw 把发出消息的 ref index 记成机器人写的；新事件进来时，凡是 `msgIdx` 跟这个机器人账号对得上的都忽略掉。这样既阻断平台层面的回声循环，又不影响用户引用或回复机器人之前的消息。
- **用了 `--token-file` 还是显示未配置**：`--token-file` 只设置 AppSecret，`appId` 还是要从配置或 `QQBOT_APP_ID` 里来。
- **主动消息发不到**：用户最近没和机器人互动时，QQ 可能拦截机器人主动发起的消息。
- **语音没被转写**：确认 STT 已配置，且 provider 网络可达。

---

> ## Related

## 相关

> * [Pairing](/channels/pairing)
> * [Groups](/channels/groups)
> * [Channel troubleshooting](/channels/troubleshooting)

- [配对](/channels/pairing)
- [群组](/channels/groups)
- [通道故障排查](/channels/troubleshooting)
