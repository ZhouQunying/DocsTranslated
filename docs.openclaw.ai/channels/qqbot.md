# QQ Bot / QQ机器人

## 状态

**英文原文**: QQ Bot connects to OpenClaw via the official QQ Bot API (WebSocket gateway). The plugin supports C2C private chat, group @messages, and guild channel messages with rich media (images, voice, video, files). Status: downloadable plugin. Direct messages, group chats, guild channels, and media are supported. Reactions and threads are not supported.

**中文翻译**: QQ Bot 通过官方 QQ Bot API（WebSocket 网关）连接到 OpenClaw。插件支持 C2C 私聊、群组 @消息和频道消息，支持丰富媒体（图片、语音、视频、文件）。状态：可下载的插件。支持私聊、群聊、频道和媒体。不支持表情回应和线程。

---

## 安装

**英文原文**: Install QQ Bot before setup: `openclaw plugins install @openclaw/qqbot`

**中文翻译**: 安装 QQ Bot 插件：`openclaw plugins install @openclaw/qqbot`

---

## 设置

**英文原文**:
1. Go to the [QQ Open Platform](https://q.qq.com/) and scan the QR code with your phone QQ to register / log in.
2. Click **Create Bot** to create a new QQ bot.
3. Find **AppID** and **AppSecret** on the bot's settings page and copy them. AppSecret is not stored in plaintext — if you leave the page without saving it, you'll have to regenerate a new one.
4. Add the channel: `openclaw channels add --channel qqbot --token "AppID:AppSecret"`
5. Restart the Gateway.

Interactive setup paths: `openclaw channels add` / `openclaw configure --section channels`

**中文翻译**:
1. 前往 [QQ 开放平台](https://q.qq.com/)，用手机 QQ 扫码注册/登录。
2. 点击**创建机器人**创建新 QQ 机器人。
3. 在机器人设置页面找到 **AppID** 和 **AppSecret** 并复制。AppSecret 不以明文存储——如果离开页面时未保存，需要重新生成新的。
4. 添加频道：`openclaw channels add --channel qqbot --token "AppID:AppSecret"`
5. 重启 Gateway。

交互式设置：`openclaw channels add` 或 `openclaw configure --section channels`

---

## 配置

### 最小配置

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

默认账号环境变量：`QQBOT_APP_ID`、`QQBOT_CLIENT_SECRET`

### 文件存储 AppSecret

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

### 环境变量 SecretRef

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

说明：
- `clientSecret` 接受 SecretRef 对象，不仅是明文字符串
- 旧版 `secretref:/...` 标记字符串不是有效的 `clientSecret` 值

### [展开] 多账号设置

**英文原文**: Run multiple QQ bots under a single OpenClaw instance:

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

Each account launches its own WebSocket connection and maintains an independent token cache (isolated by `appId`).

Add a second bot via CLI: `openclaw channels add --channel qqbot --account bot2 --token "222222222:secret-of-bot-2"`

**中文翻译**: 在单个 OpenClaw 实例下运行多个 QQ 机器人：

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

每个账号启动独立的 WebSocket 连接并维护独立的令牌缓存（按 `appId` 隔离）。

通过 CLI 添加第二个机器人：`openclaw channels add --channel qqbot --account bot2 --token "222222222:secret-of-bot-2"`

### [展开] 群聊

**英文原文**: QQ Bot group chat support uses QQ group OpenIDs, not display names. Add the bot to a group, then mention it or configure the group to run without a mention.

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

`groups["*"]` sets defaults for every group, and a concrete `groups.GROUP_OPENID` entry overrides those defaults for one group. Group settings include:

- `requireMention`: require an @mention before the bot replies. Default: `true`.
- `ignoreOtherMentions`: drop messages that mention someone else but not the bot.
- `historyLimit`: keep recent non-mention group messages as context for the next mentioned turn. Set `0` to disable.
- `toolPolicy`: `full`, `restricted`, or `none` for group-scoped tools.
- `name`: friendly label used in logs and group context.
- `prompt`: per-group behavior prompt appended to the agent context.

Activation modes are `mention` and `always`. `requireMention: true` maps to `mention`; `requireMention: false` maps to `always`. A session-level activation override, when present, wins over config.

The inbound queue is per peer. Group peers get a larger queue cap, keep human messages ahead of bot-authored chatter when full, and merge bursts of normal group messages into one attributed turn. Slash commands still run one by one.

**中文翻译**: QQ Bot 群聊使用 QQ 群 OpenID，不使用群名称。将机器人添加到群后，@它或配置群为无需 @ 即可运行。

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
          name: "发布群",
          requireMention: false,
          ignoreOtherMentions: true,
          historyLimit: 20,
          prompt: "保持回复简短且操作性强。",
        },
      },
    },
  },
}
```

`groups["*"]` 为所有群设置默认值，具体的 `groups.GROUP_OPENID` 条目覆盖单个群的默认值。群设置包括：

- `requireMention`：机器人回复前是否需要 @提及。默认 `true`。
- `ignoreOtherMentions`：丢弃只 @了别人但没 @机器人的消息。
- `historyLimit`：保留近期未 @的群消息作为下一次被 @时的上下文。设为 `0` 禁用。
- `toolPolicy`：`full`、`restricted` 或 `none`，控制群作用域的工具。
- `name`：日志和群上下文中使用的友好标签。
- `prompt`：每个群的行为提示词，附加到 agent 上下文中。

激活模式为 `mention` 和 `always`。`requireMention: true` 对应 `mention`；`requireMention: false` 对应 `always`。会话级激活覆盖（如果存在）优先于配置。

入站队列按 peer 隔离。群 peer 有更大的队列上限，队列满时保持人类消息优先于机器人自产聊天，并将普通群消息突发合并为一次归属回合。斜杠命令仍然逐个执行。

### [展开] 语音（STT / TTS）

**英文原文**: STT and TTS support two-level configuration with priority fallback:

| Setting | Plugin-specific | Framework fallback |
|---|---|---|
| STT | `channels.qqbot.stt` | `tools.media.audio.models[0]` |
| TTS | `channels.qqbot.tts`, `channels.qqbot.accounts.<id>.tts` | `messages.tts` |

Inbound QQ voice attachments are exposed to agents as audio media metadata while keeping raw voice files out of generic `MediaPaths`. `[[audio_as_voice]]` plain text replies synthesize TTS and send a native QQ voice message when TTS is configured.

**中文翻译**: STT（语音转文字）和 TTS（文字转语音）支持两层配置，带优先级回退：

| 设置 | 插件专用 | 框架回退 |
|---|---|---|
| STT | `channels.qqbot.stt` | `tools.media.audio.models[0]` |
| TTS | `channels.qqbot.tts`、`channels.qqbot.accounts.<id>.tts` | `messages.tts` |

入站 QQ 语音附件以音频媒体元数据形式暴露给 agent，同时将原始语音文件排除在通用 `MediaPaths` 之外。`[[audio_as_voice]]` 纯文本回复会合成 TTS 并在 TTS 配置时发送原生 QQ 语音消息。

---

## 目标格式

**英文原文**:
| Format | Description |
|---|---|
| `qqbot:c2c:OPENID` | Private chat (C2C) |
| `qqbot:group:GROUP_OPENID` | Group chat |
| `qqbot:channel:CHANNEL_ID` | Guild channel |

> Each bot has its own set of user OpenIDs. An OpenID received by Bot A **cannot** be used to send messages via Bot B.

**中文翻译**:
| 格式 | 说明 |
|---|---|
| `qqbot:c2c:OPENID` | 私聊（C2C） |
| `qqbot:group:GROUP_OPENID` | 群聊 |
| `qqbot:channel:CHANNEL_ID` | 频道 |

> 每个机器人有自己的一套用户 OpenID。机器人 A 收到的 OpenID **不能**用于通过机器人 B 发送消息。

---

## 斜杠命令

**英文原文**: Built-in commands intercepted before the AI queue:

| Command | Description |
|---|---|
| `/bot-ping` | Latency test |
| `/bot-version` | Show the OpenClaw framework version |
| `/bot-help` | List all commands |
| `/bot-me` | Show the sender's QQ user ID (openid) for `allowFrom`/`groupAllowFrom` setup |
| `/bot-upgrade` | Show the QQBot upgrade guide link |
| `/bot-logs` | Export recent gateway logs as a file |
| `/bot-approve` | Approve a pending QQ Bot action (for example, confirming a C2C or group upload) through the native flow. |

Append `?` to any command for usage help (for example `/bot-upgrade ?`).

Admin commands (`/bot-me`, `/bot-upgrade`, `/bot-logs`, `/bot-clear-storage`, `/bot-streaming`, `/bot-approve`) are direct-message-only and require the sender's openid in an explicit non-wildcard `allowFrom` list. A wildcard `allowFrom: ["*"]` permits chat but does not grant admin command access. Group messages match against `groupAllowFrom` first and fall back to `allowFrom`. Running an admin command in a group returns a hint rather than silently dropping.

**中文翻译**: 在进入 AI 队列之前拦截的内置命令：

| 命令 | 说明 |
|---|---|
| `/bot-ping` | 延迟测试 |
| `/bot-version` | 显示 OpenClaw 框架版本 |
| `/bot-help` | 列出所有命令 |
| `/bot-me` | 显示发送者的 QQ 用户 ID（openid），用于配置 `allowFrom`/`groupAllowFrom` |
| `/bot-upgrade` | 显示 QQBot 升级指南链接 |
| `/bot-logs` | 导出近期 Gateway 日志为文件 |
| `/bot-approve` | 通过原生流程批准待处理的 QQ Bot 操作（例如确认 C2C 或群上传） |

在任何命令后加 `?` 获取用法帮助（例如 `/bot-upgrade ?`）。

管理命令（`/bot-me`、`/bot-upgrade`、`/bot-logs`、`/bot-clear-storage`、`/bot-streaming`、`/bot-approve`）仅限私聊使用，且要求发送者的 openid 在明确的非通配符 `allowFrom` 列表中。通配符 `allowFrom: ["*"]` 允许聊天但不授予管理命令权限。群消息先匹配 `groupAllowFrom`，再回退到 `allowFrom`。在群中执行管理命令会返回提示而非静默丢弃。

---

## [展开] 引擎架构

**英文原文**: QQ Bot ships as a self-contained engine inside the plugin:

- Each account owns an isolated resource stack (WebSocket connection, API client, token cache, media storage root) keyed by `appId`. Accounts never share inbound/outbound state.
- The multi-account logger tags log lines with the owning account so diagnostics stay separable when you run several bots under one gateway.
- Inbound, outbound, and gateway bridge paths share a single media payload root under `~/.openclaw/media`, so uploads, downloads, and transcode caches land under one guarded directory instead of a per-subsystem tree.
- Rich media delivery goes through one `sendMedia` path for C2C and group targets. Local files and buffers above the large-file threshold use QQ's chunked upload endpoints, while smaller payloads use the one-shot media API.
- Credentials can be backed up and restored as part of standard OpenClaw credential snapshots; the engine re-attaches each account's resource stack on restore without requiring a fresh QR-code pair.

**中文翻译**: QQ Bot 在插件内作为独立引擎运行：

- 每个账号拥有隔离的资源栈（WebSocket 连接、API 客户端、令牌缓存、媒体存储根目录），以 `appId` 为键。账号之间从不共享入站/出站状态。
- 多账号日志记录器为每行日志打上所属账号标签，因此在一个 Gateway 下运行多个机器人时诊断信息仍可分离。
- 入站、出站和 Gateway 桥接路径共享 `~/.openclaw/media` 下的单一媒体载荷根目录，因此上传、下载和转码缓存在一个受保护的目录下，而不是每个子系统一棵树。
- 丰富媒体发送通过单一的 `sendMedia` 路径处理 C2C 和群目标。超过大文件阈值的本地文件和缓冲区使用 QQ 的分片上传端点，较小的载荷使用一次性媒体 API。
- 凭证可以作为标准 OpenClaw 凭证快照的一部分进行备份和恢复；引擎在恢复时为每个账号重新挂载资源栈，无需重新扫码配对。

---

## [展开] 扫码入驻

**英文原文**: As an alternative to pasting `AppID:AppSecret` manually, the engine supports a QR-code onboarding flow for linking a QQ Bot to OpenClaw:

1. Run the QQ Bot setup path (for example `openclaw channels add --channel qqbot`) and pick the QR-code flow when prompted.
2. Scan the generated QR code with the phone app tied to the target QQ Bot.
3. Approve the pairing on the phone. OpenClaw persists the returned credentials into `credentials/` under the right account scope.

**中文翻译**: 作为手动粘贴 `AppID:AppSecret` 的替代方案，引擎支持扫码入驻流程将 QQ Bot 连接到 OpenClaw：

1. 运行 QQ Bot 设置路径（例如 `openclaw channels add --channel qqbot`），在提示时选择扫码流程。
2. 用目标 QQ Bot 绑定的手机 App 扫描生成的二维码。
3. 在手机上批准配对。OpenClaw 将返回的凭证持久化到 `credentials/` 下正确的账号作用域中。

---

## 故障排除

| 问题 | 原因与解决 |
|---|---|
| 机器人回复 "gone to Mars" | 未配置凭证或 Gateway 未启动 |
| 无入站消息 | 确认 `appId` 和 `clientSecret` 正确，且机器人在 QQ 开放平台已启用 |
| 反复自我回复 | OpenClaw 记录 QQ 出站引用索引作为机器人自产内容，忽略当前 `msgIdx` 匹配的入站事件，防止平台回环 |
| `--token-file` 设置后仍显示未配置 | `--token-file` 仅设置 AppSecret，仍需在配置或 `QQBOT_APP_ID` 中设置 `appId` |
| 主动消息未到达 | 如果用户近期没有互动，QQ 可能拦截机器人主动发送的消息 |
| 语音未转写 | 确认 STT 已配置且提供商可访问 |
