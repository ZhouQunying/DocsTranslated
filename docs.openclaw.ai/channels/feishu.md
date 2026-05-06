# Feishu / 飞书

## 状态

**英文原文**: Feishu/Lark is an all-in-one collaboration platform where teams chat, share documents, manage calendars, and get work done together. **Status:** production-ready for bot DMs + group chats. WebSocket is the default mode; webhook mode is optional.

**中文翻译**: 飞书/Lark 是一个一体化协作平台，团队可以在其中聊天、共享文档、管理日历和协同工作。**状态：** 机器人私聊和群聊已生产就绪。WebSocket 为默认模式；Webhook 模式为可选。

---

## 快速开始

**英文原文**: Requires OpenClaw 2026.4.25 or above. Run `openclaw --version` to check. Upgrade with `openclaw update`.

**中文翻译**: 需要 OpenClaw 2026.4.25 或以上版本。运行 `openclaw --version` 检查。通过 `openclaw update` 升级。

### Step 1 — Run the channel setup wizard

**英文原文**: `openclaw channels login --channel feishu` — Scan the QR code with your Feishu/Lark mobile app to create a Feishu/Lark bot automatically.

**中文翻译**: `openclaw channels login --channel feishu` — 用飞书/Lark 手机 App 扫码，自动创建飞书/Lark 机器人。

### Step 2 — Restart the gateway

**英文原文**: After setup completes, restart the gateway to apply the changes: `openclaw gateway restart`

**中文翻译**: 设置完成后，重启 Gateway 以应用更改：`openclaw gateway restart`

---

## 访问控制

### 私聊

**英文原文**: Configure `dmPolicy` to control who can DM the bot:

- `"pairing"` - unknown users receive a pairing code; approve via CLI
- `"allowlist"` - only users listed in `allowFrom` can chat (default: bot owner only)
- `"open"` - allow public DMs only when `allowFrom` includes `"*"`; with restrictive entries, only matching users can chat
- `"disabled"` - disable all DMs

Approve a pairing request:
```bash
openclaw pairing list feishu
openclaw pairing approve feishu <CODE>
```

**中文翻译**: 配置 `dmPolicy` 控制谁可以私聊机器人：

- `"pairing"` — 未知用户收到配对码；通过 CLI 批准
- `"allowlist"` — 仅 `allowFrom` 列表中的用户可聊天（默认：仅机器人所有者）
- `"open"` — 仅当 `allowFrom` 包含 `"*"` 时允许公开私聊；限制性条目下仅匹配用户可聊天
- `"disabled"` — 禁用所有私聊

批准配对请求：
```bash
openclaw pairing list feishu
openclaw pairing approve feishu <CODE>
```

### 群聊

**英文原文**: Group policy (`channels.feishu.groupPolicy`):

| Value | Behavior |
|---|---|
| `"open"` | Respond to all messages in groups |
| `"allowlist"` | Only respond to groups in `groupAllowFrom` or explicitly configured under `groups.<chat_id>` |
| `"disabled"` | Disable all group messages; explicit `groups.<chat_id>` entries do not override this |

Default: `allowlist`

Mention requirement (`channels.feishu.requireMention`):
- `true` - require @mention (default)
- `false` - respond without @mention
- Per-group override: `channels.feishu.groups.<chat_id>.requireMention`
- Broadcast-only `@all` and `@_all` are not treated as bot mentions. A message that mentions both `@all` and the bot directly still counts as a bot mention.

**中文翻译**: 群策略（`channels.feishu.groupPolicy`）：

| 值 | 行为 |
|---|---|
| `"open"` | 响应群内所有消息 |
| `"allowlist"` | 仅响应 `groupAllowFrom` 中或 `groups.<chat_id>` 下明确配置的群 |
| `"disabled"` | 禁用所有群消息；明确的 `groups.<chat_id>` 条目不覆盖此设置 |

默认：`allowlist`

@提及要求（`channels.feishu.requireMention`）：
- `true` — 需要 @提及（默认）
- `false` — 无需 @提及即可回复
- 每群覆盖：`channels.feishu.groups.<chat_id>.requireMention`
- 纯广播的 `@all` 和 `@_all` 不算作机器人 @提及。同时 @了 `@all` 和机器人的消息仍算作机器人 @提及。

---

## [展开] 群配置示例

### 允许所有群，无需 @提及

**英文原文**:
```json5
{ channels: { feishu: { groupPolicy: "open" } } }
```

**中文翻译**: （配置代码保持不变）

### 允许所有群，仍需 @提及

**英文原文**:
```json5
{ channels: { feishu: { groupPolicy: "open", requireMention: true } } }
```

**中文翻译**: （配置代码保持不变）

### 仅允许特定群

**英文原文**:
```json5
{
  channels: {
    feishu: {
      groupPolicy: "allowlist",
      groupAllowFrom: ["oc_xxx", "oc_yyy"],
    },
  },
}
```

In `allowlist` mode, you can also admit a group by adding an explicit `groups.<chat_id>` entry. Explicit entries do not override `groupPolicy: "disabled"`. Wildcard defaults under `groups.*` configure matching groups, but they do not admit groups by themselves.

```json5
{
  channels: {
    feishu: {
      groupPolicy: "allowlist",
      groups: { oc_xxx: { requireMention: false } },
    },
  },
}
```

**中文翻译**: 在 `allowlist` 模式下，你也可以通过添加明确的 `groups.<chat_id>` 条目来接纳一个群。明确条目不覆盖 `groupPolicy: "disabled"`。`groups.*` 下的通配符默认值配置匹配的群，但它们本身不接纳群。

### 限制群内发送者

**英文原文**:
```json5
{
  channels: {
    feishu: {
      groupPolicy: "allowlist",
      groupAllowFrom: ["oc_xxx"],
      groups: {
        oc_xxx: {
          allowFrom: ["ou_user1", "ou_user2"],
        },
      },
    },
  },
}
```

**中文翻译**: （配置代码保持不变。User open_ids 格式如：`ou_xxx`）

---

## 获取群/用户 ID

### 群 ID（`chat_id`，格式：`oc_xxx`）

**英文原文**: Open the group in Feishu/Lark, click the menu icon in the top-right corner, and go to **Settings**. The group ID (`chat_id`) is listed on the settings page.

**中文翻译**: 在飞书/Lark 中打开群，点击右上角菜单图标，进入**设置**。群 ID（`chat_id`）列在设置页面上。

### 用户 ID（`open_id`，格式：`ou_xxx`）

**英文原文**: Start the gateway, send a DM to the bot, then check the logs: `openclaw logs --follow`. Look for `open_id` in the log output. You can also check pending pairing requests: `openclaw pairing list feishu`

**中文翻译**: 启动 Gateway，给机器人发一条私聊，然后查看日志：`openclaw logs --follow`。在日志输出中查找 `open_id`。你也可以检查待处理的配对请求：`openclaw pairing list feishu`

---

## 常用命令

**英文原文**:
| Command | Description |
|---|---|
| `/status` | Show bot status |
| `/reset` | Reset the current session |
| `/model` | Show or switch the AI model |

Feishu/Lark does not support native slash-command menus, so send these as plain text messages.

**中文翻译**:
| 命令 | 说明 |
|---|---|
| `/status` | 显示机器人状态 |
| `/reset` | 重置当前会话 |
| `/model` | 显示或切换 AI 模型 |

飞书/Lark 不支持原生斜杠命令菜单，所以直接以纯文本消息发送这些命令。

---

## 故障排除

### 机器人在群聊中不回复

1. 确保机器人已被添加到群
2. 确保你 @了机器人（默认需要）
3. 验证 `groupPolicy` 不是 `"disabled"`
4. 检查日志：`openclaw logs --follow`

### 机器人收不到消息

1. 确保机器人在飞书开放平台已发布并审批通过
2. 确保事件订阅包含 `im.message.receive_v1`
3. 确保选择了**长连接**（WebSocket）模式
4. 确保已授予所有必需的权限范围
5. 确保 Gateway 正在运行：`openclaw gateway status`
6. 检查日志：`openclaw logs --follow`

### App Secret 泄露

1. 在飞书开放平台重置 App Secret
2. 更新配置中的值
3. 重启 Gateway：`openclaw gateway restart`

---

## [展开] 高级配置

### 多账号

**英文原文**:
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
          tts: { providers: { openai: { voice: "shimmer" } } },
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

`defaultAccount` controls which account is used when outbound APIs do not specify an `accountId`. `accounts.<id>.tts` uses the same shape as `messages.tts` and deep-merges over global TTS config.

**中文翻译**: （配置代码保持不变）

`defaultAccount` 控制在出站 API 未指定 `accountId` 时使用哪个账号。`accounts.<id>.tts` 使用与 `messages.tts` 相同的结构，并深度合并到全局 TTS 配置中，因此多机器人飞书设置可以在全局共享提供商凭证的同时，按账号覆盖语音、模型、角色或自动模式。

### 消息限制

- `textChunkLimit` — 出站文本分块大小（默认：2000 字符）
- `mediaMaxMb` — 媒体上传/下载限制（默认：30 MB）

### 流式输出

**英文原文**: Feishu/Lark supports streaming replies via interactive cards. When enabled, the bot updates the card in real time as it generates text.

```json5
{
  channels: {
    feishu: {
      streaming: true,
      blockStreaming: true,
    },
  },
}
```

Set `streaming: false` to send the complete reply in one message. `blockStreaming` is off by default; enable it only when you want completed assistant blocks flushed before the final reply.

**中文翻译**: 飞书/Lark 支持通过交互卡片流式回复。启用后，机器人生成文本时会实时更新卡片。

`streaming: false` 时一次性发送完整回复。`blockStreaming` 默认关闭；仅当你希望在最终回复之前刷新已完成的 agent 块时启用。

### 配额优化

**英文原文**: Reduce the number of Feishu/Lark API calls with two optional flags:
- `typingIndicator` (default `true`): set `false` to skip typing reaction calls
- `resolveSenderNames` (default `true`): set `false` to skip sender profile lookups

**中文翻译**: 通过两个可选标志减少飞书/Lark API 调用次数：
- `typingIndicator`（默认 `true`）：设为 `false` 跳过输入中反应调用
- `resolveSenderNames`（默认 `true`）：设为 `false` 跳过发送者资料查询

### [展开] ACP 会话

**英文原文**: Feishu/Lark supports ACP for DMs and group thread messages. Feishu/Lark ACP is text-command driven - there are no native slash-command menus, so use `/acp ...` messages directly in the conversation.

**中文翻译**: 飞书/Lark 支持私聊和群线程消息的 ACP。飞书/Lark ACP 由文本命令驱动——没有原生斜杠命令菜单，所以直接在对话中使用 `/acp ...` 消息。

#### 持久 ACP 绑定

（配置代码保持不变，无需翻译）

#### 从聊天中生成 ACP

**英文原文**: In a Feishu/Lark DM or thread: `/acp spawn codex --thread here`

`--thread here` works for DMs and Feishu/Lark thread messages. Follow-up messages in the bound conversation route directly to that ACP session.

**中文翻译**: 在飞书/Lark 私聊或线程中：`/acp spawn codex --thread here`

`--thread here` 适用于私聊和飞书/Lark 线程消息。绑定对话中的后续消息直接路由到该 ACP 会话。

### [展开] 多 Agent 路由

**英文原文**: Use `bindings` to route Feishu/Lark DMs or groups to different agents.

Routing fields:
- `match.channel`: `"feishu"`
- `match.peer.kind`: `"direct"` (DM) or `"group"` (group chat)
- `match.peer.id`: user Open ID (`ou_xxx`) or group ID (`oc_xxx`)

**中文翻译**: 使用 `bindings` 将飞书/Lark 私聊或群路由到不同的 agent。

路由字段：
- `match.channel`：`"feishu"`
- `match.peer.kind`：`"direct"`（私聊）或 `"group"`（群聊）
- `match.peer.id`：用户 Open ID（`ou_xxx`）或群 ID（`oc_xxx`）

---

## 配置参考

| 设置 | 说明 | 默认值 |
|---|---|---|
| `channels.feishu.enabled` | 启用/禁用频道 | `true` |
| `channels.feishu.domain` | API 域名（`feishu` 或 `lark`） | `feishu` |
| `channels.feishu.connectionMode` | 事件传输方式（`websocket` 或 `webhook`） | `websocket` |
| `channels.feishu.defaultAccount` | 出站路由的默认账号 | `default` |
| `channels.feishu.verificationToken` | Webhook 模式必需 | - |
| `channels.feishu.encryptKey` | Webhook 模式必需 | - |
| `channels.feishu.webhookPath` | Webhook 路由路径 | `/feishu/events` |
| `channels.feishu.webhookHost` | Webhook 绑定主机 | `127.0.0.1` |
| `channels.feishu.webhookPort` | Webhook 绑定端口 | `3000` |
| `channels.feishu.accounts.<id>.appId` | App ID | - |
| `channels.feishu.accounts.<id>.appSecret` | App Secret | - |
| `channels.feishu.accounts.<id>.domain` | 每账号域名覆盖 | `feishu` |
| `channels.feishu.dmPolicy` | 私聊策略 | `allowlist` |
| `channels.feishu.allowFrom` | 私聊白名单（open_id 列表） | [BotOwnerId] |
| `channels.feishu.groupPolicy` | 群策略 | `allowlist` |
| `channels.feishu.groupAllowFrom` | 群白名单 | - |
| `channels.feishu.requireMention` | 群中需要 @提及 | `true` |
| `channels.feishu.groups.<chat_id>.requireMention` | 每群 @提及覆盖；明确 ID 也在 allowlist 模式下接纳该群 | 继承 |
| `channels.feishu.groups.<chat_id>.enabled` | 启用/禁用特定群 | `true` |
| `channels.feishu.textChunkLimit` | 消息分块大小 | `2000` |
| `channels.feishu.mediaMaxMb` | 媒体大小限制 | `30` |
| `channels.feishu.streaming` | 流式卡片输出 | `true` |
| `channels.feishu.blockStreaming` | 已完成块的回复流式输出 | `false` |
| `channels.feishu.typingIndicator` | 发送输入中反应 | `true` |
| `channels.feishu.resolveSenderNames` | 解析发送者显示名称 | `true` |

---

## 支持的消息类型

### 接收

- ✅ 文本
- ✅ 富文本（post）
- ✅ 图片
- ✅ 文件
- ✅ 音频
- ✅ 视频/媒体
- ✅ 表情贴纸

入站飞书/Lark 音频消息被规范化为媒体占位符而非原始 `file_key` JSON。当配置了 `tools.media.audio` 时，OpenClaw 下载语音资源并在 agent 回合前运行共享音频转写，因此 agent 收到的是语音转录文本。如果飞书直接在音频载荷中包含转录文本，则该文本直接使用，不再进行额外的 ASR 调用。没有音频转写提供商时，agent 仍然收到 `<media:audio>` 占位符和已保存的附件，而非原始飞书资源载荷。

### 发送

- ✅ 文本
- ✅ 图片
- ✅ 文件
- ✅ 音频
- ✅ 视频/媒体
- ✅ 交互卡片（包括流式更新）
- ⚠️ 富文本（post 风格排版；不支持完整的飞书/Lark 创作能力）

原生飞书/Lark 音频气泡使用飞书 `audio` 消息类型，需要 Ogg/Opus 上传媒体（`file_type: "opus"`）。现有的 `.opus` 和 `.ogg` 媒体直接作为原生音频发送。MP3/WAV/M4A 等其他音频格式仅在回复请求语音投递时（`audioAsVoice` / 消息工具 `asVoice`，包括 TTS 语音笔记回复）通过 `ffmpeg` 转码为 48kHz Ogg/Opus。普通 MP3 附件保持为常规文件。如果缺少 `ffmpeg` 或转换失败，OpenClaw 回退为文件附件并记录原因。

### 线程和回复

- ✅ 内联回复
- ✅ 线程回复
- ✅ 媒体回复在线程中保持线程感知

对于 `groupSessionScope: "group_topic"` 和 `"group_topic_sender"`，原生飞书/Lark 话题群使用事件 `thread_id`（`omt_*`）作为规范的话题会话键。如果原生话题起始事件缺少 `thread_id`，OpenClaw 在路由回合之前从飞书补充它。OpenClaw 转为线程的普通群回复继续使用回复根消息 ID（`om_*`），因此首回合和后续回合保持在同一会话中。
