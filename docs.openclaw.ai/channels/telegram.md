# Telegram

> Production-ready for bot DMs and groups via grammY. Long polling is the default mode; webhook mode is optional.

通过 grammY 接入，机器人私聊和群聊已生产可用。默认走 long polling，webhook 模式可选。

> <CardGroup cols={3}>
>   <Card title="Pairing" icon="link" href="/channels/pairing">
>     Default DM policy for Telegram is pairing.
>   </Card>
>
>   <Card title="Channel troubleshooting" icon="wrench" href="/channels/troubleshooting">
>     Cross-channel diagnostics and repair playbooks.
>   </Card>
>
>   <Card title="Gateway configuration" icon="settings" href="/gateway/configuration">
>     Full channel config patterns and examples.
>   </Card>
> </CardGroup>

- [配对](/channels/pairing)：Telegram 的默认 DM 策略就是 pairing。
- [通道故障排查](/channels/troubleshooting)：跨通道的诊断和修复手册。
- [Gateway 配置](/gateway/configuration)：完整的通道配置模式和示例。

---

> ## Quick setup

## 快速配置

> [步骤 1: Create the bot token in BotFather]
>
> Open Telegram and chat with **@BotFather** (confirm the handle is exactly `@BotFather`).
>
> Run `/newbot`, follow prompts, and save the token.

[步骤 1：在 BotFather 里建机器人 token]

打开 Telegram，找 **@BotFather** 聊天（确认 handle 是 `@BotFather` 一字不差）。

发 `/newbot`，按提示走完，保存好 token。

> [步骤 2: Configure token and DM policy]
>
> ```json5
> {
>   channels: {
>     telegram: {
>       enabled: true,
>       botToken: "123:abc",
>       dmPolicy: "pairing",
>       groups: { "*": { requireMention: true } },
>     },
>   },
> }
> ```
>
> Env fallback: `TELEGRAM_BOT_TOKEN=...` (default account only).
> Telegram does **not** use `openclaw channels login telegram`; configure token in config/env, then start gateway.

[步骤 2：配 token 和 DM 策略]

```json5
{
  channels: {
    telegram: {
      enabled: true,
      botToken: "123:abc",
      dmPolicy: "pairing",
      groups: { "*": { requireMention: true } },
    },
  },
}
```

环境变量回退：`TELEGRAM_BOT_TOKEN=...`（只对默认账号生效）。
Telegram **不走** `openclaw channels login telegram`；token 写到配置或环境变量里，然后启动 Gateway。

> [步骤 3: Start gateway and approve first DM]
>
> ```bash
> openclaw gateway
> openclaw pairing list telegram
> openclaw pairing approve telegram <CODE>
> ```
>
> Pairing codes expire after 1 hour.

[步骤 3：启动 Gateway，批准第一条私聊]

```bash
openclaw gateway
openclaw pairing list telegram
openclaw pairing approve telegram <CODE>
```

配对码 1 小时后过期。

> [步骤 4: Add the bot to a group]
>
> Add the bot to your group, then get both IDs that group access needs:
>
> * your Telegram user ID, used in `allowFrom` / `groupAllowFrom`
> * the Telegram group chat ID, used as the key under `channels.telegram.groups`
>
> For first-time setup, get the group chat ID from `openclaw logs --follow`, a forwarded-ID bot, or Bot API `getUpdates`. After the group is allowed, `/whoami@<bot_username>` can confirm the user and group IDs.
>
> Negative Telegram supergroup IDs that start with `-100` are group chat IDs. Put them under `channels.telegram.groups`, not under `groupAllowFrom`.

[步骤 4：把机器人加进群]

把机器人加进群，拿到群访问需要的两个 ID：

- 你自己的 Telegram user ID，用在 `allowFrom` / `groupAllowFrom`。
- Telegram 群的 chat ID，作为 `channels.telegram.groups` 下的 key。

第一次配置时，群 chat ID 从 `openclaw logs --follow`、转发 ID 的工具机器人、或 Bot API `getUpdates` 里拿。群放行之后，`/whoami@<bot_username>` 可以确认 user 和群 ID。

以 `-100` 开头的负数 Telegram supergroup ID 是群 chat ID。放到 `channels.telegram.groups` 下，**不要**放到 `groupAllowFrom` 下。

> <Note>
>   Token resolution order is account-aware. In practice, config values win over env fallback, and `TELEGRAM_BOT_TOKEN` only applies to the default account.
> </Note>

> **提示**：token 解析顺序按账号区分。实际上配置里的值优先于环境变量回退，且 `TELEGRAM_BOT_TOKEN` 只对默认账号生效。

---

> ## Telegram side settings

## Telegram 侧的设置

> [展开: Privacy mode and group visibility]
>
> Telegram bots default to **Privacy Mode**, which limits what group messages they receive.
>
> If the bot must see all group messages, either:
>
> * disable privacy mode via `/setprivacy`, or
> * make the bot a group admin.
>
> When toggling privacy mode, remove + re-add the bot in each group so Telegram applies the change.

[展开：Privacy mode 和群消息可见性]

Telegram 机器人默认开 **Privacy Mode**，限制它能收到哪些群消息。

要让机器人看到所有群消息，二选一：

- 通过 `/setprivacy` 关掉 privacy mode，或者
- 把机器人设为群管理员。

切换 privacy mode 后，在每个群里把机器人移除再加回来，Telegram 才会让改动生效。

> [展开: Group permissions]
>
> Admin status is controlled in Telegram group settings.
>
> Admin bots receive all group messages, which is useful for always-on group behavior.

[展开：群权限]

群管理员身份在 Telegram 群设置里控制。

管理员机器人会收到所有群消息，对 always-on 群行为有用。

> [展开: Helpful BotFather toggles]
>
> * `/setjoingroups` to allow/deny group adds
> * `/setprivacy` for group visibility behavior

[展开：BotFather 常用开关]

- `/setjoingroups`：允许 / 禁止机器人被加进群
- `/setprivacy`：群消息可见性行为

---

> ## Access control and activation

## 访问控制与激活

> [标签页: DM policy]
>
> `channels.telegram.dmPolicy` controls direct message access:
>
> * `pairing` (default)
> * `allowlist` (requires at least one sender ID in `allowFrom`)
> * `open` (requires `allowFrom` to include `"*"`)
> * `disabled`

[标签页：DM 策略]

`channels.telegram.dmPolicy` 控制私聊访问：

- `pairing`（默认）
- `allowlist`（要求 `allowFrom` 里至少有一个发件人 ID）
- `open`（要求 `allowFrom` 里含 `"*"`）
- `disabled`

> `dmPolicy: "open"` with `allowFrom: ["*"]` lets any Telegram account that finds or guesses the bot username command the bot. Use it only for intentionally public bots with tightly restricted tools; one-owner bots should use `allowlist` with numeric user IDs.

`dmPolicy: "open"` 加上 `allowFrom: ["*"]` 等于让任何一个找得到或猜得出机器人 username 的 Telegram 账号都能命令机器人。只在那种"刻意公开 + 工具严格受限"的机器人上用；单所有者机器人请用 `allowlist` 加数字 user ID。

> `channels.telegram.allowFrom` accepts numeric Telegram user IDs. `telegram:` / `tg:` prefixes are accepted and normalized.
> In multi-account configs, a restrictive top-level `channels.telegram.allowFrom` is treated as a safety boundary: account-level `allowFrom: ["*"]` entries do not make that account public unless the effective account allowlist still contains an explicit wildcard after merging.
> `dmPolicy: "allowlist"` with empty `allowFrom` blocks all DMs and is rejected by config validation.
> Setup asks for numeric user IDs only.
> If you upgraded and your config contains `@username` allowlist entries, run `openclaw doctor --fix` to resolve them (best-effort; requires a Telegram bot token).
> If you previously relied on pairing-store allowlist files, `openclaw doctor --fix` can recover entries into `channels.telegram.allowFrom` in allowlist flows (for example when `dmPolicy: "allowlist"` has no explicit IDs yet).

`channels.telegram.allowFrom` 接受数字 Telegram user ID。`telegram:` / `tg:` 前缀也认，会归一化掉。
多账号配置里，顶层的 `channels.telegram.allowFrom` 若是严格白名单，会被当作安全边界：账号级的 `allowFrom: ["*"]` 条目并不会让该账号变成公开 —— 除非合并后的有效白名单里仍然显式带通配。
`dmPolicy: "allowlist"` 配空的 `allowFrom` 会拦下所有私聊，且配置校验时会拒绝。
配置向导只问数字 user ID。
升级后配置里如果还有 `@username` 形式的白名单条目，跑 `openclaw doctor --fix` 把它们解析掉（best-effort，需要 Telegram bot token）。
之前依赖 pairing 存储里的白名单文件的话，`openclaw doctor --fix` 可以把它们恢复进 `channels.telegram.allowFrom`（比如当 `dmPolicy: "allowlist"` 还没显式 ID 时）。

> For one-owner bots, prefer `dmPolicy: "allowlist"` with explicit numeric `allowFrom` IDs to keep access policy durable in config (instead of depending on previous pairing approvals).

单所有者机器人优先用 `dmPolicy: "allowlist"` + 显式的数字 `allowFrom` ID，把访问策略持久写在配置里（而不是依赖之前的配对批准）。

> Common confusion: DM pairing approval does not mean "this sender is authorized everywhere".
> Pairing grants DM access. If no command owner exists yet, the first approved pairing also sets `commands.ownerAllowFrom` so owner-only commands and exec approvals have an explicit operator account.
> Group sender authorization still comes from explicit config allowlists.
> If you want "I am authorized once and both DMs and group commands work", put your numeric Telegram user ID in `channels.telegram.allowFrom`; for owner-only commands, make sure `commands.ownerAllowFrom` contains `telegram:<your user id>`.

常见混淆：DM 配对批准不等于"这个发件人在所有地方都获授权"。
配对只给私聊访问。当还没有命令所有者时，第一条被批准的配对会同时写 `commands.ownerAllowFrom`，让 owner-only 命令和执行批准有一个明确的操作者账号。
群发件人授权仍然只来自配置里的显式白名单。
想要"授权一次，私聊和群命令都能用"，把你的数字 Telegram user ID 放进 `channels.telegram.allowFrom`；owner-only 命令则要确认 `commands.ownerAllowFrom` 里含 `telegram:<你的 user id>`。

> ### Finding your Telegram user ID

### 怎么找到自己的 Telegram user ID

> Safer (no third-party bot):
>
> 1. DM your bot.
> 2. Run `openclaw logs --follow`.
> 3. Read `from.id`.

更安全的做法（不用第三方机器人）：

1. 给你的机器人发私聊。
2. 跑 `openclaw logs --follow`。
3. 看 `from.id`。

> Official Bot API method:
>
> ```bash
> curl "https://api.telegram.org/bot<bot_token>/getUpdates"
> ```

官方 Bot API 方法：

```bash
curl "https://api.telegram.org/bot<bot_token>/getUpdates"
```

> Third-party method (less private): `@userinfobot` or `@getidsbot`.

第三方方法（隐私性差一些）：`@userinfobot` 或 `@getidsbot`。

> [标签页: Group policy and allowlists]
>
> Two controls apply together:
>
> 1. **Which groups are allowed** (`channels.telegram.groups`)
>    * no `groups` config:
>      * with `groupPolicy: "open"`: any group can pass group-ID checks
>      * with `groupPolicy: "allowlist"` (default): groups are blocked until you add `groups` entries (or `"*"`)
>    * `groups` configured: acts as allowlist (explicit IDs or `"*"`)
>
> 2. **Which senders are allowed in groups** (`channels.telegram.groupPolicy`)
>    * `open`
>    * `allowlist` (default)
>    * `disabled`

[标签页：群策略和白名单]

两套控制一起生效：

1. **哪些群被放行**（`channels.telegram.groups`）：
   - 没配 `groups`：
     - `groupPolicy: "open"`：任何群都能过群 ID 检查。
     - `groupPolicy: "allowlist"`（默认）：群被拦着，直到你加 `groups` 条目（或 `"*"`）。
   - 配了 `groups`：它就是白名单（显式 ID 或 `"*"`）。

2. **哪些发件人在群里被放行**（`channels.telegram.groupPolicy`）：
   - `open`
   - `allowlist`（默认）
   - `disabled`

> `groupAllowFrom` is used for group sender filtering. If not set, Telegram falls back to `allowFrom`.
> `groupAllowFrom` entries should be numeric Telegram user IDs (`telegram:` / `tg:` prefixes are normalized).
> Do not put Telegram group or supergroup chat IDs in `groupAllowFrom`. Negative chat IDs belong under `channels.telegram.groups`.
> Non-numeric entries are ignored for sender authorization.
> Security boundary (`2026.2.25+`): group sender auth does **not** inherit DM pairing-store approvals.
> Pairing stays DM-only. For groups, set `groupAllowFrom` or per-group/per-topic `allowFrom`.
> If `groupAllowFrom` is unset, Telegram falls back to config `allowFrom`, not the pairing store.
> Practical pattern for one-owner bots: set your user ID in `channels.telegram.allowFrom`, leave `groupAllowFrom` unset, and allow the target groups under `channels.telegram.groups`.
> Runtime note: if `channels.telegram` is completely missing, runtime defaults to fail-closed `groupPolicy="allowlist"` unless `channels.defaults.groupPolicy` is explicitly set.

`groupAllowFrom` 用于群发件人过滤。没设的话 Telegram 回退到 `allowFrom`。
`groupAllowFrom` 里的条目应该是数字 Telegram user ID（`telegram:` / `tg:` 前缀会归一化掉）。
**不要**把 Telegram 群或 supergroup chat ID 放进 `groupAllowFrom`。负数 chat ID 属于 `channels.telegram.groups`。
非数字条目在做发件人授权时会被忽略。
安全边界（`2026.2.25+`）：群发件人授权**不**继承 DM 配对存储里的批准。
配对只管私聊。群里要么设 `groupAllowFrom`，要么按群 / 按话题设 `allowFrom`。
`groupAllowFrom` 没设时 Telegram 回退到配置里的 `allowFrom`，不是配对存储。
单所有者机器人的实用模式：把你的 user ID 写在 `channels.telegram.allowFrom`，`groupAllowFrom` 留空，目标群在 `channels.telegram.groups` 下放行。
运行时注意：`channels.telegram` 整段缺失时，运行时回退到默认拒绝的 `groupPolicy="allowlist"`，除非显式设了 `channels.defaults.groupPolicy`。

> Owner-only group setup:
>
> ```json5
> {
>   channels: {
>     telegram: {
>       enabled: true,
>       dmPolicy: "pairing",
>       allowFrom: ["<YOUR_TELEGRAM_USER_ID>"],
>       groupPolicy: "allowlist",
>       groups: {
>         "<GROUP_CHAT_ID>": {
>           requireMention: true,
>         },
>       },
>     },
>   },
> }
> ```

只放行所有者的群配置：

```json5
{
  channels: {
    telegram: {
      enabled: true,
      dmPolicy: "pairing",
      allowFrom: ["<YOUR_TELEGRAM_USER_ID>"],
      groupPolicy: "allowlist",
      groups: {
        "<GROUP_CHAT_ID>": {
          requireMention: true,
        },
      },
    },
  },
}
```

> Test it from the group with `@<bot_username> ping`. Plain group messages do not trigger the bot while `requireMention: true`.

在群里发 `@<bot_username> ping` 测试。`requireMention: true` 时普通群消息不会触发机器人。

> Example: allow any member in one specific group:
>
> ```json5
> {
>   channels: {
>     telegram: {
>       groups: {
>         "-1001234567890": {
>           groupPolicy: "open",
>           requireMention: false,
>         },
>       },
>     },
>   },
> }
> ```

例子：在某个具体群里允许任何成员触发：

```json5
{
  channels: {
    telegram: {
      groups: {
        "-1001234567890": {
          groupPolicy: "open",
          requireMention: false,
        },
      },
    },
  },
}
```

> Example: allow only specific users inside one specific group:
>
> ```json5
> {
>   channels: {
>     telegram: {
>       groups: {
>         "-1001234567890": {
>           requireMention: true,
>           allowFrom: ["8734062810", "745123456"],
>         },
>       },
>     },
>   },
> }
> ```

例子：某个具体群里只允许特定用户触发：

```json5
{
  channels: {
    telegram: {
      groups: {
        "-1001234567890": {
          requireMention: true,
          allowFrom: ["8734062810", "745123456"],
        },
      },
    },
  },
}
```

> <Warning>
>   Common mistake: `groupAllowFrom` is not a Telegram group allowlist.
>
>   * Put negative Telegram group or supergroup chat IDs like `-1001234567890` under `channels.telegram.groups`.
>   * Put Telegram user IDs like `8734062810` under `groupAllowFrom` when you want to limit which people inside an allowed group can trigger the bot.
>   * Use `groupAllowFrom: ["*"]` only when you want any member of an allowed group to be able to talk to the bot.
> </Warning>

> **警告**：常见错误 —— `groupAllowFrom` 不是 Telegram 群白名单。
>
> - 像 `-1001234567890` 这种负数 Telegram 群 / supergroup chat ID 放到 `channels.telegram.groups` 下。
> - 像 `8734062810` 这种 Telegram user ID 放到 `groupAllowFrom` 下，用来限制已放行群内哪些人能触发机器人。
> - 只在你想让已放行群里任何成员都能跟机器人对话时，才用 `groupAllowFrom: ["*"]`。

> [标签页: Mention behavior]
>
> Group replies require mention by default.
>
> Mention can come from:
>
> * native `@botusername` mention, or
> * mention patterns in:
>   * `agents.list[].groupChat.mentionPatterns`
>   * `messages.groupChat.mentionPatterns`

[标签页：@ 行为]

群里回复默认要求 @ 触发。

@ 可以来自：

- 原生的 `@botusername` 提及，或者
- 下列位置的 mention 模式：
  - `agents.list[].groupChat.mentionPatterns`
  - `messages.groupChat.mentionPatterns`

> Session-level command toggles:
>
> * `/activation always`
> * `/activation mention`
>
> These update session state only. Use config for persistence.

会话级别的命令开关：

- `/activation always`
- `/activation mention`

这两个只改会话状态。要持久化，写到配置里。

> Persistent config example:
>
> ```json5
> {
>   channels: {
>     telegram: {
>       groups: {
>         "*": { requireMention: false },
>       },
>     },
>   },
> }
> ```

持久化配置示例：

```json5
{
  channels: {
    telegram: {
      groups: {
        "*": { requireMention: false },
      },
    },
  },
}
```

> Getting the group chat ID:
>
> * forward a group message to `@userinfobot` / `@getidsbot`
> * or read `chat.id` from `openclaw logs --follow`
> * or inspect Bot API `getUpdates`
> * after the group is allowed, run `/whoami@<bot_username>` if native commands are enabled

获取群 chat ID：

- 把群消息转发给 `@userinfobot` / `@getidsbot`；
- 或者在 `openclaw logs --follow` 输出里读 `chat.id`；
- 或者看 Bot API 的 `getUpdates`；
- 群放行后，原生命令开着的话跑 `/whoami@<bot_username>`。

---

> ## Runtime behavior

## 运行时行为

> * Telegram is owned by the gateway process.
> * Routing is deterministic: Telegram inbound replies back to Telegram (the model does not pick channels).
> * Inbound messages normalize into the shared channel envelope with reply metadata, media placeholders, and persisted reply-chain context for Telegram replies the gateway has observed.
> * Group sessions are isolated by group ID. Forum topics append `:topic:<threadId>` to keep topics isolated.
> * DM messages can carry `message_thread_id`; OpenClaw preserves the thread ID for replies but keeps DMs on the flat session by default. Configure `channels.telegram.dm.threadReplies: "inbound"`, `channels.telegram.direct.<chatId>.threadReplies: "inbound"`, `requireTopic: true`, or a matching topic config when you intentionally want DM topic session isolation.
> * Long polling uses grammY runner with per-chat/per-thread sequencing. Overall runner sink concurrency uses `agents.defaults.maxConcurrent`.
> * Multi-account startup bounds concurrent Telegram `getMe` probes so large bot fleets do not fan out every account probe at once.
> * Long polling is guarded inside each gateway process so only one active poller can use a bot token at a time. If you still see `getUpdates` 409 conflicts, another OpenClaw gateway, script, or external poller is likely using the same token.
> * Long-polling watchdog restarts trigger after 120 seconds without completed `getUpdates` liveness by default. Increase `channels.telegram.pollingStallThresholdMs` only if your deployment still sees false polling-stall restarts during long-running work. The value is in milliseconds and is allowed from `30000` to `600000`; per-account overrides are supported.
> * Telegram Bot API has no read-receipt support (`sendReadReceipts` does not apply).

- Telegram 由 Gateway 进程持有。
- 路由是确定性的：Telegram 进来的消息回包也回 Telegram（模型不挑通道）。
- 接收消息会归一化到共用的 channel envelope，带 reply 元数据、媒体占位符，以及 Gateway 观察到的 Telegram 回复的持久化回复链上下文。
- 群会话按群 ID 隔离。Forum topic 会在群 ID 后追加 `:topic:<threadId>`，让每个 topic 互相隔离。
- 私聊消息可能带 `message_thread_id`；OpenClaw 在回复时保留这个 thread ID，但默认让私聊走扁平会话。要刻意让私聊也按 topic 隔离会话，就配 `channels.telegram.dm.threadReplies: "inbound"`、`channels.telegram.direct.<chatId>.threadReplies: "inbound"`、`requireTopic: true`，或者一条匹配的 topic 配置。
- Long polling 用 grammY runner，按 chat / thread 顺序处理。runner 的整体 sink 并发用 `agents.defaults.maxConcurrent`。
- 多账号启动时会限制并发的 `getMe` 探测，避免大量机器人启动时一起向 Telegram 发探测。
- 每个 Gateway 进程内部对 long polling 做了护栏，一个 bot token 同时只允许一个 poller 在跑。如果还看到 `getUpdates` 409 冲突，多半是另一个 OpenClaw Gateway、脚本或外部 poller 在用同一个 token。
- Long polling 看门狗在默认 120 秒内没有完成 `getUpdates` liveness 时会重启。只有部署里在长任务期间还出现假阳性的 polling stall 重启时，才调高 `channels.telegram.pollingStallThresholdMs`。值的单位是毫秒，允许范围 `30000` 到 `600000`；可以按账号覆盖。
- Telegram Bot API 不支持已读回执（`sendReadReceipts` 不生效）。

---

> ## Feature reference

## 功能参考

> [展开: Live stream preview (message edits)]
>
> OpenClaw can stream partial replies in real time:
>
> * direct chats: preview message + `editMessageText`
> * groups/topics: preview message + `editMessageText`

[展开：实时流式预览（消息编辑）]

OpenClaw 可以实时流式发回复：

- 私聊：预览消息 + `editMessageText`
- 群 / topic：预览消息 + `editMessageText`

> Requirement:
>
> * `channels.telegram.streaming` is `off | partial | block | progress` (default: `partial`)
> * `progress` keeps one editable status draft for tool progress, clears it at completion, and sends the final answer as a normal message
> * `streaming.preview.toolProgress` controls whether tool/progress updates reuse the same edited preview message (default: `true` when preview streaming is active)
> * `streaming.preview.commandText` controls command/exec detail inside those tool-progress lines: `raw` (default, preserves released behavior) or `status` (tool label only)
> * legacy `channels.telegram.streamMode` and boolean `streaming` values are detected; run `openclaw doctor --fix` to migrate them to `channels.telegram.streaming.mode`

要求：

- `channels.telegram.streaming` 是 `off | partial | block | progress`（默认 `partial`）。
- `progress` 给工具进度留一条可编辑的状态草稿，完成时清空，最终答案以普通消息发出。
- `streaming.preview.toolProgress` 控制工具 / 进度更新是否复用同一条被编辑的预览消息（预览流式开启时默认 `true`）。
- `streaming.preview.commandText` 控制工具进度行里命令 / exec 细节的呈现：`raw`（默认，保留已发布行为）或 `status`（只显示工具标签）。
- 老的 `channels.telegram.streamMode` 和布尔型 `streaming` 值会被识别；跑 `openclaw doctor --fix` 把它们迁移到 `channels.telegram.streaming.mode`。

> Tool-progress preview updates are the short status lines shown while tools run, for example command execution, file reads, planning updates, patch summaries, or Codex preamble/commentary text in Codex app-server mode. Telegram keeps these enabled by default to match released OpenClaw behavior from `v2026.4.22` and later. To keep the edited preview for answer text but hide tool-progress lines, set:

工具进度预览更新就是工具运行期间显示的那些短状态行，比如命令执行、文件读取、计划更新、补丁摘要，或 Codex app-server 模式里的 preamble / 注释文本。Telegram 默认开着，与 `v2026.4.22` 及之后的 OpenClaw 行为保持一致。如果想保留"答案预览"的编辑、但隐藏工具进度行：

> ```json
> {
>   "channels": {
>     "telegram": {
>       "streaming": {
>         "mode": "partial",
>         "preview": {
>           "toolProgress": false
>         }
>       }
>     }
>   }
> }
> ```

```json
{
  "channels": {
    "telegram": {
      "streaming": {
        "mode": "partial",
        "preview": {
          "toolProgress": false
        }
      }
    }
  }
}
```

> To keep tool-progress visible but hide command/exec text, set:

要保留工具进度但隐藏命令 / exec 文本：

> ```json
> {
>   "channels": {
>     "telegram": {
>       "streaming": {
>         "mode": "partial",
>         "preview": {
>           "commandText": "status"
>         }
>       }
>     }
>   }
> }
> ```

```json
{
  "channels": {
    "telegram": {
      "streaming": {
        "mode": "partial",
        "preview": {
          "commandText": "status"
        }
      }
    }
  }
}
```

> Use `progress` mode when you want visible tool progress without editing the final answer into that same message. Put the command-text policy under `streaming.progress`:

如果想看到工具进度、但不希望最终答案被编辑进同一条消息，用 `progress` 模式。命令文本策略放在 `streaming.progress` 下：

> ```json
> {
>   "channels": {
>     "telegram": {
>       "streaming": {
>         "mode": "progress",
>         "progress": {
>           "toolProgress": true,
>           "commandText": "status"
>         }
>       }
>     }
>   }
> }
> ```

```json
{
  "channels": {
    "telegram": {
      "streaming": {
        "mode": "progress",
        "progress": {
          "toolProgress": true,
          "commandText": "status"
        }
      }
    }
  }
}
```

> Use `streaming.mode: "off"` only when you want final-only delivery: Telegram preview edits are disabled and generic tool/progress chatter is suppressed instead of being sent as standalone status messages. Approval prompts, media payloads, and errors still route through normal final delivery. Use `streaming.preview.toolProgress: false` when you only want to keep answer preview edits while hiding the tool-progress status lines.

只在你想"只发最终结果"时才用 `streaming.mode: "off"`：关掉 Telegram 预览编辑，通用的工具 / 进度闲聊也不再作为独立状态消息发出。批准提示、媒体载荷、错误仍然走正常的最终投递。只想保留答案预览编辑、但隐藏工具进度行，用 `streaming.preview.toolProgress: false`。

> <Note>
>   Telegram selected quote replies are the exception. When `replyToMode` is `"first"`, `"all"`, or `"batched"` and the inbound message includes selected quote text, OpenClaw sends the final answer through Telegram's native quote-reply path instead of editing the answer preview, so `streaming.preview.toolProgress` cannot show the short status lines for that turn. Current-message replies without selected quote text still keep preview streaming. Set `replyToMode: "off"` when tool-progress visibility matters more than native quote replies, or set `streaming.preview.toolProgress: false` to acknowledge the trade-off.
> </Note>

> **提示**：Telegram 的 selected quote 回复是个例外。当 `replyToMode` 是 `"first"`、`"all"` 或 `"batched"`，并且收到的消息带 selected quote 文本时，OpenClaw 通过 Telegram 原生的引用回复路径发最终答案，而不是编辑答案预览，因此那一轮 `streaming.preview.toolProgress` 显示不出短状态行。当前消息没有 selected quote 时，仍走预览流式。如果工具进度可见性比原生引用回复更重要，把 `replyToMode` 设成 `"off"`；或者把 `streaming.preview.toolProgress` 设成 `false`，明确接受这个权衡。

> For text-only replies:
>
> * short DM/group/topic previews: OpenClaw keeps the same preview message and performs the final edit in place
> * long text finals that split into multiple Telegram messages reuse the existing preview as the first final chunk when possible, then send only the remaining chunks
> * progress-mode finals clear the status draft and use normal final delivery instead of editing the draft into the answer
> * if the final edit fails before the completed text is confirmed, OpenClaw uses normal final delivery and cleans up the stale preview

纯文本回复时：

- 短的 DM / 群 / topic 预览：OpenClaw 沿用同一条预览消息，原地做最终编辑。
- 长文本最终回复被拆成多条 Telegram 消息时，会尽量把已有预览复用为第一段，再发剩下的几段。
- `progress` 模式的最终回复会清掉状态草稿，走正常的最终投递，不会把草稿改成答案。
- 已完成文本确认之前，最终编辑失败时，OpenClaw 改走正常的最终投递，并清理掉那条过期的预览。

> For complex replies (for example media payloads), OpenClaw falls back to normal final delivery and then cleans up the preview message.

复杂回复（比如带媒体载荷）时，OpenClaw 回退到正常最终投递，然后清理预览消息。

> Preview streaming is separate from block streaming. When block streaming is explicitly enabled for Telegram, OpenClaw skips the preview stream to avoid double-streaming.

预览流式和 block 流式是分开的两件事。Telegram 显式开了 block 流式时，OpenClaw 跳过预览流式，避免双重流式。

> Telegram-only reasoning stream:
>
> * `/reasoning stream` sends reasoning to the live preview while generating
> * the reasoning preview is deleted after final delivery; use `/reasoning on` when reasoning should remain visible
> * final answer is sent without reasoning text

Telegram 专属的推理流式：

- `/reasoning stream`：生成过程中把推理内容发到实时预览里。
- 最终投递完成后，推理预览会被删除；想让推理保留可见，用 `/reasoning on`。
- 最终答案不会附带推理文本。

> [展开: Formatting and HTML fallback]
>
> Outbound text uses Telegram `parse_mode: "HTML"`.
>
> * Markdown-ish text is rendered to Telegram-safe HTML.
> * Supported Telegram HTML tags are preserved; unsupported HTML is escaped.
> * If Telegram rejects parsed HTML, OpenClaw retries as plain text.
>
> Link previews are enabled by default and can be disabled with `channels.telegram.linkPreview: false`.

[展开：格式化和 HTML 回退]

发出的文本用 Telegram `parse_mode: "HTML"`。

- Markdown 风格的文本会渲染成 Telegram 安全的 HTML。
- 支持的 Telegram HTML 标签保留；不支持的 HTML 会被转义。
- Telegram 拒绝解析后的 HTML 时，OpenClaw 用纯文本重试。

链接预览默认开着，可以用 `channels.telegram.linkPreview: false` 关掉。

> [展开: Native commands and custom commands]
>
> Telegram command menu registration is handled at startup with `setMyCommands`.

[展开：原生命令和自定义命令]

Telegram 命令菜单的注册在启动时通过 `setMyCommands` 完成。

> Native command defaults:
>
> * `commands.native: "auto"` enables native commands for Telegram

原生命令默认值：

- `commands.native: "auto"` 给 Telegram 开启原生命令。

> Add custom command menu entries:
>
> ```json5
> {
>   channels: {
>     telegram: {
>       customCommands: [
>         { command: "backup", description: "Git backup" },
>         { command: "generate", description: "Create an image" },
>       ],
>     },
>   },
> }
> ```

加自定义菜单条目：

```json5
{
  channels: {
    telegram: {
      customCommands: [
        { command: "backup", description: "Git backup" },
        { command: "generate", description: "Create an image" },
      ],
    },
  },
}
```

> Rules:
>
> * names are normalized (strip leading `/`, lowercase)
> * valid pattern: `a-z`, `0-9`, `_`, length `1..32`
> * custom commands cannot override native commands
> * conflicts/duplicates are skipped and logged

规则：

- 命令名会归一化（去掉前导 `/`、转小写）。
- 合法格式：`a-z`、`0-9`、`_`，长度 1 到 32。
- 自定义命令不能覆盖原生命令。
- 冲突 / 重复会被跳过并记日志。

> Notes:
>
> * custom commands are menu entries only; they do not auto-implement behavior
> * plugin/skill commands can still work when typed even if not shown in Telegram menu

说明：

- 自定义命令只是菜单条目，不会自动实现行为。
- 插件 / skill 命令即便不出现在 Telegram 菜单里，手打仍然能用。

> If native commands are disabled, built-ins are removed. Custom/plugin commands may still register if configured.

关掉原生命令时，内置命令会从菜单里移除。自定义 / 插件命令如果配了，仍可能继续注册。

> Common setup failures:
>
> * `setMyCommands failed` with `BOT_COMMANDS_TOO_MUCH` means the Telegram menu still overflowed after trimming; reduce plugin/skill/custom commands or disable `channels.telegram.commands.native`.
> * `deleteWebhook`, `deleteMyCommands`, or `setMyCommands` failing with `404: Not Found` while direct Bot API curl commands work can mean `channels.telegram.apiRoot` was set to the full `/bot<TOKEN>` endpoint. `apiRoot` must be only the Bot API root, and `openclaw doctor --fix` removes an accidental trailing `/bot<TOKEN>`.
> * `getMe returned 401` means Telegram rejected the configured bot token. Update `botToken`, `tokenFile`, or `TELEGRAM_BOT_TOKEN` with the current BotFather token; OpenClaw stops before polling so this is not reported as a webhook cleanup failure.
> * `setMyCommands failed` with network/fetch errors usually means outbound DNS/HTTPS to `api.telegram.org` is blocked.

常见配置错误：

- `setMyCommands failed` 报 `BOT_COMMANDS_TOO_MUCH`：裁剪后 Telegram 菜单还是溢出。减少插件 / skill / 自定义命令，或者把 `channels.telegram.commands.native` 关掉。
- `deleteWebhook`、`deleteMyCommands`、`setMyCommands` 报 `404: Not Found`，但直接用 curl 调 Bot API 又能通：可能 `channels.telegram.apiRoot` 被写成了完整的 `/bot<TOKEN>` 端点。`apiRoot` 只能是 Bot API 根路径；`openclaw doctor --fix` 会把意外加上的 `/bot<TOKEN>` 后缀去掉。
- `getMe returned 401`：Telegram 拒绝了当前 bot token。用 BotFather 里的最新 token 更新 `botToken`、`tokenFile` 或 `TELEGRAM_BOT_TOKEN`；OpenClaw 在 polling 之前就停了，所以这条不会被报为 webhook 清理失败。
- `setMyCommands failed` 报网络 / fetch 错误：通常是发往 `api.telegram.org` 的 DNS / HTTPS 被拦了。

> ### Device pairing commands (`device-pair` plugin)

### 设备配对命令（`device-pair` 插件）

> When the `device-pair` plugin is installed:
>
> 1. `/pair` generates setup code
> 2. paste code in iOS app
> 3. `/pair pending` lists pending requests (including role/scopes)
> 4. approve the request:
>    * `/pair approve <requestId>` for explicit approval
>    * `/pair approve` when there is only one pending request
>    * `/pair approve latest` for most recent

装了 `device-pair` 插件之后：

1. `/pair` 生成配置码。
2. 把配置码粘进 iOS App。
3. `/pair pending` 列出待处理请求（含 role / 作用域）。
4. 批准请求：
   - `/pair approve <requestId>` 显式批准；
   - 只有一条待处理时直接 `/pair approve`；
   - `/pair approve latest` 批准最近一条。

> The setup code carries a short-lived bootstrap token. Built-in setup-code bootstrap is node-only: the first connect creates a pending node request, and after approval the Gateway returns a durable node token with `scopes: []`. It does not return a handed-off operator token; operator access requires a separate approved operator pairing or token flow.

配置码里带一个短期引导 token。内置的配置码引导只覆盖 node 角色：第一次连接会生成一条待处理的 node 请求，批准后 Gateway 返回一个长期 node token，`scopes: []`。它不会下发 operator token；要拿到 operator 权限，需要另一条专门批准过的 operator 配对或 token 流程。

> If a device retries with changed auth details (for example role/scopes/public key), the previous pending request is superseded and the new request uses a different `requestId`. Re-run `/pair pending` before approving.

同一设备如果换了认证细节（比如改 role / 作用域 / 公钥）再来一次，之前那条待处理请求会被替换，新请求用一个不同的 `requestId`。批准前重新跑 `/pair pending` 看一下。

> More details: [Pairing](/channels/pairing#pair-via-telegram-recommended-for-ios).

更多细节：[配对](/channels/pairing#pair-via-telegram-recommended-for-ios)。

> [展开: Inline buttons]
>
> Configure inline keyboard scope:
>
> ```json5
> {
>   channels: {
>     telegram: {
>       capabilities: {
>         inlineButtons: "allowlist",
>       },
>     },
>   },
> }
> ```

[展开：行内按钮]

配置 inline keyboard 的作用范围：

```json5
{
  channels: {
    telegram: {
      capabilities: {
        inlineButtons: "allowlist",
      },
    },
  },
}
```

> Per-account override:
>
> ```json5
> {
>   channels: {
>     telegram: {
>       accounts: {
>         main: {
>           capabilities: {
>             inlineButtons: "allowlist",
>           },
>         },
>       },
>     },
>   },
> }
> ```

按账号覆盖：

```json5
{
  channels: {
    telegram: {
      accounts: {
        main: {
          capabilities: {
            inlineButtons: "allowlist",
          },
        },
      },
    },
  },
}
```

> Scopes:
>
> * `off`
> * `dm`
> * `group`
> * `all`
> * `allowlist` (default)

可选作用域：

- `off`
- `dm`
- `group`
- `all`
- `allowlist`（默认）

> Legacy `capabilities: ["inlineButtons"]` maps to `inlineButtons: "all"`.

老格式 `capabilities: ["inlineButtons"]` 映射为 `inlineButtons: "all"`。

> Message action example:
>
> ```json5
> {
>   action: "send",
>   channel: "telegram",
>   to: "123456789",
>   message: "Choose an option:",
>   buttons: [
>     [
>       { text: "Yes", callback_data: "yes" },
>       { text: "No", callback_data: "no" },
>     ],
>     [{ text: "Cancel", callback_data: "cancel" }],
>   ],
> }
> ```

消息动作示例：

```json5
{
  action: "send",
  channel: "telegram",
  to: "123456789",
  message: "Choose an option:",
  buttons: [
    [
      { text: "Yes", callback_data: "yes" },
      { text: "No", callback_data: "no" },
    ],
    [{ text: "Cancel", callback_data: "cancel" }],
  ],
}
```

> Mini App button example:
>
> ```json5
> {
>   action: "send",
>   channel: "telegram",
>   to: "123456789",
>   message: "Open app:",
>   presentation: {
>     blocks: [
>       {
>         type: "buttons",
>         buttons: [{ label: "Launch", web_app: { url: "https://example.com/app" } }],
>       },
>     ],
>   },
> }
> ```

Mini App 按钮示例：

```json5
{
  action: "send",
  channel: "telegram",
  to: "123456789",
  message: "Open app:",
  presentation: {
    blocks: [
      {
        type: "buttons",
        buttons: [{ label: "Launch", web_app: { url: "https://example.com/app" } }],
      },
    ],
  },
}
```

> Telegram `web_app` buttons work only in private chats between a user and the bot.

Telegram `web_app` 按钮只在用户与机器人的私聊里起作用。

> Callback clicks are passed to the agent as text:
> `callback_data: <value>`

回调点击作为文本传给 agent：`callback_data: <value>`。

> [展开: Telegram message actions for agents and automation]
>
> Telegram tool actions include:
>
> * `sendMessage` (`to`, `content`, optional `mediaUrl`, `replyToMessageId`, `messageThreadId`)
> * `react` (`chatId`, `messageId`, `emoji`)
> * `deleteMessage` (`chatId`, `messageId`)
> * `editMessage` (`chatId`, `messageId`, `content`)
> * `createForumTopic` (`chatId`, `name`, optional `iconColor`, `iconCustomEmojiId`)

[展开：Telegram 给 agent 和自动化用的消息动作]

Telegram 工具动作包括：

- `sendMessage`（`to`、`content`，可选 `mediaUrl`、`replyToMessageId`、`messageThreadId`）
- `react`（`chatId`、`messageId`、`emoji`）
- `deleteMessage`（`chatId`、`messageId`）
- `editMessage`（`chatId`、`messageId`、`content`）
- `createForumTopic`（`chatId`、`name`，可选 `iconColor`、`iconCustomEmojiId`）

> Channel message actions expose ergonomic aliases (`send`, `react`, `delete`, `edit`, `sticker`, `sticker-search`, `topic-create`).

通道消息动作还提供了顺手的别名（`send`、`react`、`delete`、`edit`、`sticker`、`sticker-search`、`topic-create`）。

> Gating controls:
>
> * `channels.telegram.actions.sendMessage`
> * `channels.telegram.actions.deleteMessage`
> * `channels.telegram.actions.reactions`
> * `channels.telegram.actions.sticker` (default: disabled)

开关控制：

- `channels.telegram.actions.sendMessage`
- `channels.telegram.actions.deleteMessage`
- `channels.telegram.actions.reactions`
- `channels.telegram.actions.sticker`（默认关）

> Note: `edit` and `topic-create` are currently enabled by default and do not have separate `channels.telegram.actions.*` toggles.
> Runtime sends use the active config/secrets snapshot (startup/reload), so action paths do not perform ad-hoc SecretRef re-resolution per send.

注意：`edit` 和 `topic-create` 当前默认开着，没有单独的 `channels.telegram.actions.*` 开关。
运行时的发送动作用启动 / 重载时的配置 / 密钥快照，所以发送链路不会每次单独重新解析 SecretRef。

> Reaction removal semantics: [/tools/reactions](/tools/reactions)

表情移除的语义：[/tools/reactions](/tools/reactions)。

> [展开: Reply threading tags]
>
> Telegram supports explicit reply threading tags in generated output:
>
> * `[[reply_to_current]]` replies to the triggering message
> * `[[reply_to:<id>]]` replies to a specific Telegram message ID

[展开：回复线程标签]

Telegram 支持在生成的输出里写显式的回复线程标签：

- `[[reply_to_current]]`：回复触发当前轮的那条消息。
- `[[reply_to:<id>]]`：回复指定的 Telegram 消息 ID。

> `channels.telegram.replyToMode` controls handling:
>
> * `off` (default)
> * `first`
> * `all`

`channels.telegram.replyToMode` 控制处理方式：

- `off`（默认）
- `first`
- `all`

> When reply threading is enabled and the original Telegram text or caption is available, OpenClaw includes a native Telegram quote excerpt automatically. Telegram caps native quote text at 1024 UTF-16 code units, so longer messages are quoted from the start and fall back to a plain reply if Telegram rejects the quote.

开启回复线程且能拿到原 Telegram 文本或 caption 时，OpenClaw 会自动带上一段 Telegram 原生引用摘录。Telegram 把原生引用文本上限设为 1024 个 UTF-16 code unit，更长的消息从开头开始引用；Telegram 拒绝引用时回退到普通回复。

> Note: `off` disables implicit reply threading. Explicit `[[reply_to_*]]` tags are still honored.

说明：`off` 关掉隐式回复线程。显式的 `[[reply_to_*]]` 标签仍然有效。

> [展开: Forum topics and thread behavior]
>
> Forum supergroups:
>
> * topic session keys append `:topic:<threadId>`
> * replies and typing target the topic thread
> * topic config path:
>   `channels.telegram.groups.<chatId>.topics.<threadId>`

[展开：Forum topic 和线程行为]

Forum supergroup：

- topic 会话 key 追加 `:topic:<threadId>`。
- 回复和输入中状态都打到 topic 线程。
- topic 配置路径：`channels.telegram.groups.<chatId>.topics.<threadId>`。

> General topic (`threadId=1`) special-case:
>
> * message sends omit `message_thread_id` (Telegram rejects `sendMessage(...thread_id=1)`)
> * typing actions still include `message_thread_id`

General topic（`threadId=1`）特例：

- 发消息时不带 `message_thread_id`（Telegram 拒绝 `sendMessage(...thread_id=1)`）。
- 输入中状态仍然带 `message_thread_id`。

> Topic inheritance: topic entries inherit group settings unless overridden (`requireMention`, `allowFrom`, `skills`, `systemPrompt`, `enabled`, `groupPolicy`).
> `agentId` is topic-only and does not inherit from group defaults.

topic 继承：topic 条目继承群设置，除非显式覆盖（`requireMention`、`allowFrom`、`skills`、`systemPrompt`、`enabled`、`groupPolicy`）。
`agentId` 是 topic 独有字段，不会从群默认值继承。

> **Per-topic agent routing**: Each topic can route to a different agent by setting `agentId` in the topic config. This gives each topic its own isolated workspace, memory, and session. Example:

**按 topic 路由到不同 agent**：在 topic 配置里写 `agentId`，每个 topic 可以路由到不同的 agent。这样每个 topic 都有独立的工作区、记忆和会话。例子：

> ```json5
> {
>   channels: {
>     telegram: {
>       groups: {
>         "-1001234567890": {
>           topics: {
>             "1": { agentId: "main" },      // General topic → main agent
>             "3": { agentId: "zu" },        // Dev topic → zu agent
>             "5": { agentId: "coder" }      // Code review → coder agent
>           }
>         }
>       }
>     }
>   }
> }
> ```

```json5
{
  channels: {
    telegram: {
      groups: {
        "-1001234567890": {
          topics: {
            "1": { agentId: "main" },      // General topic → main agent
            "3": { agentId: "zu" },        // Dev topic → zu agent
            "5": { agentId: "coder" }      // Code review → coder agent
          }
        }
      }
    }
  }
}
```

> Each topic then has its own session key: `agent:zu:telegram:group:-1001234567890:topic:3`

这样每个 topic 都有自己的会话 key，例如 `agent:zu:telegram:group:-1001234567890:topic:3`。

> **Persistent ACP topic binding**: Forum topics can pin ACP harness sessions through top-level typed ACP bindings (`bindings[]` with `type: "acp"` and `match.channel: "telegram"`, `peer.kind: "group"`, and a topic-qualified id like `-1001234567890:topic:42`). Currently scoped to forum topics in groups/supergroups. See [ACP Agents](/tools/acp-agents).

**持久化 ACP topic 绑定**：通过顶层带类型的 ACP 绑定（`bindings[]` 里 `type: "acp"`、`match.channel: "telegram"`、`peer.kind: "group"`、id 带 topic 限定如 `-1001234567890:topic:42`），Forum topic 可以钉住 ACP harness 会话。当前只对群 / supergroup 里的 forum topic 生效。见 [ACP Agents](/tools/acp-agents)。

> **Thread-bound ACP spawn from chat**: `/acp spawn <agent> --thread here|auto` binds the current topic to a new ACP session; follow-ups route there directly. OpenClaw pins the spawn confirmation in-topic. Requires `channels.telegram.threadBindings.spawnSessions` to remain enabled (default: `true`).

**在聊天里启动线程绑定的 ACP**：`/acp spawn <agent> --thread here|auto` 把当前 topic 绑到一个新建的 ACP 会话；后续消息直接路由过去。OpenClaw 在 topic 里钉住派生确认消息。要求 `channels.telegram.threadBindings.spawnSessions` 保持开启（默认 `true`）。

> Template context exposes `MessageThreadId` and `IsForum`. DM chats with `message_thread_id` keep DM routing and reply metadata on flat sessions by default; they only use thread-aware session keys when configured with `threadReplies: "inbound"`, `threadReplies: "always"`, `requireTopic: true`, or a matching topic config. Use top-level `channels.telegram.dm.threadReplies` for the account default, or `direct.<chatId>.threadReplies` for one DM.

模板上下文里暴露 `MessageThreadId` 和 `IsForum`。带 `message_thread_id` 的私聊默认沿用扁平会话的 DM 路由和回复元数据；只有在配了 `threadReplies: "inbound"`、`threadReplies: "always"`、`requireTopic: true`，或一条匹配的 topic 配置时，才用 thread 感知的会话 key。账号默认值用顶层 `channels.telegram.dm.threadReplies`；单个私聊用 `direct.<chatId>.threadReplies`。

> [展开: Audio, video, and stickers]
>
> ### Audio messages

[展开：音频、视频、贴纸]

### 音频消息

> Telegram distinguishes voice notes vs audio files.
>
> * default: audio file behavior
> * tag `[[audio_as_voice]]` in agent reply to force voice-note send
> * inbound voice-note transcripts are framed as machine-generated, untrusted text in the agent context; mention detection still uses the raw transcript so mention-gated voice messages continue to work.

Telegram 区分语音笔记和音频文件。

- 默认走音频文件行为。
- 在 agent 回复里写 `[[audio_as_voice]]` 标签，强制以语音笔记发出。
- 收到的语音笔记转写在 agent 上下文里被标注为机器生成的不受信文本；@ 检测仍然走原始转写，所以靠 @ 触发的语音消息仍可工作。

> Message action example:
>
> ```json5
> {
>   action: "send",
>   channel: "telegram",
>   to: "123456789",
>   media: "https://example.com/voice.ogg",
>   asVoice: true,
> }
> ```

消息动作示例：

```json5
{
  action: "send",
  channel: "telegram",
  to: "123456789",
  media: "https://example.com/voice.ogg",
  asVoice: true,
}
```

> ### Video messages

### 视频消息

> Telegram distinguishes video files vs video notes.

Telegram 区分视频文件和 video note。

> Message action example:
>
> ```json5
> {
>   action: "send",
>   channel: "telegram",
>   to: "123456789",
>   media: "https://example.com/video.mp4",
>   asVideoNote: true,
> }
> ```

消息动作示例：

```json5
{
  action: "send",
  channel: "telegram",
  to: "123456789",
  media: "https://example.com/video.mp4",
  asVideoNote: true,
}
```

> Video notes do not support captions; provided message text is sent separately.

video note 不支持 caption；带的消息文本会另外发一条。

> ### Stickers

### 贴纸

> Inbound sticker handling:
>
> * static WEBP: downloaded and processed (placeholder `<media:sticker>`)
> * animated TGS: skipped
> * video WEBM: skipped

收到贴纸的处理：

- 静态 WEBP：下载并处理（占位符 `<media:sticker>`）。
- 动态 TGS：跳过。
- 视频 WEBM：跳过。

> Sticker context fields:
>
> * `Sticker.emoji`
> * `Sticker.setName`
> * `Sticker.fileId`
> * `Sticker.fileUniqueId`
> * `Sticker.cachedDescription`

贴纸上下文字段：

- `Sticker.emoji`
- `Sticker.setName`
- `Sticker.fileId`
- `Sticker.fileUniqueId`
- `Sticker.cachedDescription`

> Sticker cache file:
>
> * `~/.openclaw/telegram/sticker-cache.json`

贴纸缓存文件：

- `~/.openclaw/telegram/sticker-cache.json`

> Stickers are described once (when possible) and cached to reduce repeated vision calls.

贴纸尽量只描述一次然后缓存，减少重复的 vision 调用。

> Enable sticker actions:
>
> ```json5
> {
>   channels: {
>     telegram: {
>       actions: {
>         sticker: true,
>       },
>     },
>   },
> }
> ```

打开贴纸动作：

```json5
{
  channels: {
    telegram: {
      actions: {
        sticker: true,
      },
    },
  },
}
```

> Send sticker action:
>
> ```json5
> {
>   action: "sticker",
>   channel: "telegram",
>   to: "123456789",
>   fileId: "CAACAgIAAxkBAAI...",
> }
> ```

发送贴纸的动作：

```json5
{
  action: "sticker",
  channel: "telegram",
  to: "123456789",
  fileId: "CAACAgIAAxkBAAI...",
}
```

> Search cached stickers:
>
> ```json5
> {
>   action: "sticker-search",
>   channel: "telegram",
>   query: "cat waving",
>   limit: 5,
> }
> ```

搜索已缓存的贴纸：

```json5
{
  action: "sticker-search",
  channel: "telegram",
  query: "cat waving",
  limit: 5,
}
```

> [展开: Reaction notifications]
>
> Telegram reactions arrive as `message_reaction` updates (separate from message payloads).

[展开：表情通知]

Telegram 表情以 `message_reaction` 更新到达（和消息载荷是分开的）。

> When enabled, OpenClaw enqueues system events like:
>
> * `Telegram reaction added: 👍 by Alice (@alice) on msg 42`

打开后，OpenClaw 会入队类似这样的系统事件：

- `Telegram reaction added: 👍 by Alice (@alice) on msg 42`

> Config:
>
> * `channels.telegram.reactionNotifications`: `off | own | all` (default: `own`)
> * `channels.telegram.reactionLevel`: `off | ack | minimal | extensive` (default: `minimal`)

配置：

- `channels.telegram.reactionNotifications`：`off | own | all`（默认 `own`）
- `channels.telegram.reactionLevel`：`off | ack | minimal | extensive`（默认 `minimal`）

> Notes:
>
> * `own` means user reactions to bot-sent messages only (best-effort via sent-message cache).
> * Reaction events still respect Telegram access controls (`dmPolicy`, `allowFrom`, `groupPolicy`, `groupAllowFrom`); unauthorized senders are dropped.
> * Telegram does not provide thread IDs in reaction updates.
>   * non-forum groups route to group chat session
>   * forum groups route to the group general-topic session (`:topic:1`), not the exact originating topic

说明：

- `own` 只指用户对机器人发出的消息加的表情（通过发送消息缓存 best-effort 判断）。
- 表情事件仍然受 Telegram 访问控制（`dmPolicy`、`allowFrom`、`groupPolicy`、`groupAllowFrom`）约束；未授权的发件人会被丢掉。
- Telegram 不会在表情更新里给 thread ID。
  - 非 forum 群路由到群聊会话。
  - forum 群路由到群的 general-topic 会话（`:topic:1`），不是原始 topic。

> `allowed_updates` for polling/webhook include `message_reaction` automatically.

polling / webhook 的 `allowed_updates` 自动包含 `message_reaction`。

> [展开: Ack reactions]
>
> `ackReaction` sends an acknowledgement emoji while OpenClaw is processing an inbound message.

[展开：Ack 表情]

`ackReaction` 在 OpenClaw 处理收到的消息期间发一个确认 emoji。

> Resolution order:
>
> * `channels.telegram.accounts.<accountId>.ackReaction`
> * `channels.telegram.ackReaction`
> * `messages.ackReaction`
> * agent identity emoji fallback (`agents.list[].identity.emoji`, else "👀")

解析顺序：

- `channels.telegram.accounts.<accountId>.ackReaction`
- `channels.telegram.ackReaction`
- `messages.ackReaction`
- agent 身份 emoji 回退（`agents.list[].identity.emoji`，否则 "👀"）

> Notes:
>
> * Telegram expects unicode emoji (for example "👀").
> * Use `""` to disable the reaction for a channel or account.

说明：

- Telegram 要求 unicode emoji（比如 "👀"）。
- 用 `""` 关掉某个通道或账号的确认表情。

> [展开: Config writes from Telegram events and commands]
>
> Channel config writes are enabled by default (`configWrites !== false`).

[展开：从 Telegram 事件和命令写回配置]

通道写配置默认开启（`configWrites !== false`）。

> Telegram-triggered writes include:
>
> * group migration events (`migrate_to_chat_id`) to update `channels.telegram.groups`
> * `/config set` and `/config unset` (requires command enablement)

Telegram 触发的写动作包括：

- 群迁移事件（`migrate_to_chat_id`）—— 更新 `channels.telegram.groups`。
- `/config set` 和 `/config unset`（需要开启命令）。

> Disable:
>
> ```json5
> {
>   channels: {
>     telegram: {
>       configWrites: false,
>     },
>   },
> }
> ```

关掉：

```json5
{
  channels: {
    telegram: {
      configWrites: false,
    },
  },
}
```

> [展开: Long polling vs webhook]
>
> Default is long polling. For webhook mode set `channels.telegram.webhookUrl` and `channels.telegram.webhookSecret`; optional `webhookPath`, `webhookHost`, `webhookPort` (defaults `/telegram-webhook`, `127.0.0.1`, `8787`).

[展开：long polling 对比 webhook]

默认是 long polling。要走 webhook 模式，设 `channels.telegram.webhookUrl` 和 `channels.telegram.webhookSecret`；可选 `webhookPath`、`webhookHost`、`webhookPort`（默认 `/telegram-webhook`、`127.0.0.1`、`8787`）。

> In long-polling mode OpenClaw persists its restart watermark only after an update dispatches successfully. If a handler fails, that update remains retryable in the same process and is not written as completed for restart dedupe.

long polling 模式下，OpenClaw 只在 update 派发成功后才持久化重启水位。handler 失败时，那条 update 在当前进程内仍可重试，不会被写入重启去重的"已完成"状态。

> The local listener binds to `127.0.0.1:8787`. For public ingress, either put a reverse proxy in front of the local port or set `webhookHost: "0.0.0.0"` intentionally.

本地监听器绑在 `127.0.0.1:8787`。要对外暴露，要么在本地端口前面加反向代理，要么刻意把 `webhookHost` 设为 `"0.0.0.0"`。

> Webhook mode validates request guards, the Telegram secret token, and the JSON body before returning `200` to Telegram.
> OpenClaw then processes the update asynchronously through the same per-chat/per-topic bot lanes used by long polling, so slow agent turns do not hold Telegram's delivery ACK.

webhook 模式会校验请求护栏、Telegram secret token 和 JSON body，然后才给 Telegram 返回 `200`。
之后 OpenClaw 异步处理 update，走和 long polling 一样的按 chat / topic 区分的 bot 队列，所以慢的 agent 轮次不会卡住 Telegram 的投递 ACK。

> [展开: Limits, retry, and CLI targets]
>
> * `channels.telegram.textChunkLimit` default is 4000.
> * `channels.telegram.chunkMode="newline"` prefers paragraph boundaries (blank lines) before length splitting.
> * `channels.telegram.mediaMaxMb` (default 100) caps inbound and outbound Telegram media size.
> * `channels.telegram.mediaGroupFlushMs` (default 500) controls how long Telegram albums/media groups are buffered before OpenClaw dispatches them as one inbound message. Increase it if album parts arrive late; decrease it to reduce album reply latency.
> * `channels.telegram.timeoutSeconds` overrides Telegram API client timeout (if unset, grammY default applies). Bot clients clamp configured values below the 60-second outbound text/typing request guard so grammY does not abort visible reply delivery before OpenClaw's transport guard and fallback can run. Long polling still uses a 45-second `getUpdates` request guard so idle polls are not abandoned indefinitely.
> * `channels.telegram.pollingStallThresholdMs` defaults to `120000`; tune between `30000` and `600000` only for false-positive polling-stall restarts.
> * group context history uses `channels.telegram.historyLimit` or `messages.groupChat.historyLimit` (default 50); `0` disables.
> * reply/quote/forward supplemental context is normalized into one selected conversation context window when the gateway has observed the parent messages; the observed-message cache is persisted beside the session store. Telegram only includes one shallow `reply_to_message` in updates, so chains older than the cache are limited to Telegram's current update payload.
> * Telegram allowlists primarily gate who can trigger the agent, not a full supplemental-context redaction boundary.
> * DM history controls:
>   * `channels.telegram.dmHistoryLimit`
>   * `channels.telegram.dms["<user_id>"].historyLimit`
> * `channels.telegram.retry` config applies to Telegram send helpers (CLI/tools/actions) for recoverable outbound API errors. Inbound final-reply delivery also uses a bounded safe-send retry for Telegram pre-connect failures, but it does not retry ambiguous post-send network envelopes that could duplicate visible messages.

[展开：上限、重试、CLI 目标]

- `channels.telegram.textChunkLimit` 默认 4000。
- `channels.telegram.chunkMode="newline"` 优先按段落边界（空行）切分，再按长度切。
- `channels.telegram.mediaMaxMb`（默认 100）控制 Telegram 收发媒体的大小上限。
- `channels.telegram.mediaGroupFlushMs`（默认 500）控制 Telegram 相册 / media group 在 OpenClaw 把它们作为一条消息派发之前缓冲多久。相册分片到得晚就调高；想降低相册回复延迟就调低。
- `channels.telegram.timeoutSeconds` 覆盖 Telegram API 客户端超时（没设的话走 grammY 默认）。bot 客户端会把配置值压在 60 秒的发送文本 / typing 请求护栏之下，避免 grammY 在 OpenClaw 自己的传输护栏和回退之前就放弃可见回复的投递。long polling 仍然用 45 秒的 `getUpdates` 请求护栏，让空闲轮询不至于无限挂着。
- `channels.telegram.pollingStallThresholdMs` 默认 `120000`；只在出现假阳性的 polling-stall 重启时，在 `30000` 到 `600000` 之间调。
- 群上下文历史用 `channels.telegram.historyLimit` 或 `messages.groupChat.historyLimit`（默认 50）；`0` 关闭。
- 回复 / 引用 / 转发的补充上下文，在 Gateway 观察过父消息时会归一化到同一个选定的会话上下文窗口；observed-message 缓存和会话存储放在一起。Telegram 在 update 里只带一层浅 `reply_to_message`，所以早于缓存的回复链只能拿到 Telegram 当前 update 载荷里的内容。
- Telegram 白名单主要控制谁能触发 agent，并非对每一段补充上下文做统一脱敏边界。
- 私聊历史控制：
  - `channels.telegram.dmHistoryLimit`
  - `channels.telegram.dms["<user_id>"].historyLimit`
- `channels.telegram.retry` 配置作用于 Telegram 发送辅助流程（CLI / 工具 / 动作），针对可恢复的发送 API 错误。接收侧的最终回复投递在 Telegram pre-connect 失败时也用带边界的安全重试，但不会重试那些可能造成消息重复的"post-send 网络模糊"。

> CLI and message-tool send targets can be numeric chat ID, username, or a forum topic target:
>
> ```bash
> openclaw message send --channel telegram --target 123456789 --message "hi"
> openclaw message send --channel telegram --target @name --message "hi"
> openclaw message send --channel telegram --target -1001234567890:topic:42 --message "hi topic"
> ```

CLI 和消息工具的发送目标可以是数字 chat ID、username 或 forum topic 目标：

```bash
openclaw message send --channel telegram --target 123456789 --message "hi"
openclaw message send --channel telegram --target @name --message "hi"
openclaw message send --channel telegram --target -1001234567890:topic:42 --message "hi topic"
```

> Telegram polls use `openclaw message poll` and support forum topics:
>
> ```bash
> openclaw message poll --channel telegram --target 123456789 \
>   --poll-question "Ship it?" --poll-option "Yes" --poll-option "No"
> openclaw message poll --channel telegram --target -1001234567890:topic:42 \
>   --poll-question "Pick a time" --poll-option "10am" --poll-option "2pm" \
>   --poll-duration-seconds 300 --poll-public
> ```

Telegram 投票用 `openclaw message poll`，支持 forum topic：

```bash
openclaw message poll --channel telegram --target 123456789 \
  --poll-question "Ship it?" --poll-option "Yes" --poll-option "No"
openclaw message poll --channel telegram --target -1001234567890:topic:42 \
  --poll-question "Pick a time" --poll-option "10am" --poll-option "2pm" \
  --poll-duration-seconds 300 --poll-public
```

> Telegram-only poll flags:
>
> * `--poll-duration-seconds` (5-600)
> * `--poll-anonymous`
> * `--poll-public`
> * `--thread-id` for forum topics (or use a `:topic:` target)

Telegram 专属投票参数：

- `--poll-duration-seconds`（5-600）
- `--poll-anonymous`
- `--poll-public`
- `--thread-id` 用于 forum topic（或者用 `:topic:` 形式的目标）

> Telegram send also supports:
>
> * `--presentation` with `buttons` blocks for inline keyboards when `channels.telegram.capabilities.inlineButtons` allows it
> * `--pin` or `--delivery '{"pin":true}'` to request pinned delivery when the bot can pin in that chat
> * `--force-document` to send outbound images, GIFs, and videos as documents instead of compressed photo, animated-media, or video uploads

Telegram 发送还支持：

- `channels.telegram.capabilities.inlineButtons` 允许时，`--presentation` 带 `buttons` 块来发 inline keyboard。
- 机器人在该聊天里有 pin 权限时，`--pin` 或 `--delivery '{"pin":true}'` 请求"投递时置顶"。
- `--force-document` 把发出的图片、GIF、视频作为文档发，不走压缩照片 / 动图 / 视频上传。

> Action gating:
>
> * `channels.telegram.actions.sendMessage=false` disables outbound Telegram messages, including polls
> * `channels.telegram.actions.poll=false` disables Telegram poll creation while leaving regular sends enabled

动作开关：

- `channels.telegram.actions.sendMessage=false` 关闭所有 Telegram 发送，包括投票。
- `channels.telegram.actions.poll=false` 只关闭投票，普通发送保留。

> [展开: Exec approvals in Telegram]
>
> Telegram supports exec approvals in approver DMs and can optionally post prompts in the originating chat or topic. Approvers must be numeric Telegram user IDs.

[展开：Telegram 里的执行批准]

Telegram 支持在审批人的私聊里走执行批准，也可以选择性地把提示发到原始聊天或 topic 里。审批人必须是数字 Telegram user ID。

> Config path:
>
> * `channels.telegram.execApprovals.enabled` (auto-enables when at least one approver is resolvable)
> * `channels.telegram.execApprovals.approvers` (falls back to numeric owner IDs from `commands.ownerAllowFrom`)
> * `channels.telegram.execApprovals.target`: `dm` (default) | `channel` | `both`
> * `agentFilter`, `sessionFilter`

配置路径：

- `channels.telegram.execApprovals.enabled`（至少有一个审批人能解析时自动开启）
- `channels.telegram.execApprovals.approvers`（没设时回退到 `commands.ownerAllowFrom` 里的数字 owner ID）
- `channels.telegram.execApprovals.target`：`dm`（默认）| `channel` | `both`
- `agentFilter`、`sessionFilter`

> `channels.telegram.allowFrom`, `groupAllowFrom`, and `defaultTo` control who can talk to the bot and where it sends normal replies. They do not make someone an exec approver. The first approved DM pairing bootstraps `commands.ownerAllowFrom` when no command owner exists yet, so the one-owner setup still works without duplicating IDs under `execApprovals.approvers`.

`channels.telegram.allowFrom`、`groupAllowFrom`、`defaultTo` 控制谁能和机器人对话、它把普通回复发到哪里。它们不会让谁变成执行批准人。还没有命令所有者时，第一条被批准的 DM 配对会初始化 `commands.ownerAllowFrom`，单所有者部署因此不必在 `execApprovals.approvers` 下重复写 ID。

> Channel delivery shows the command text in the chat; only enable `channel` or `both` in trusted groups/topics. When the prompt lands in a forum topic, OpenClaw preserves the topic for the approval prompt and the follow-up. Exec approvals expire after 30 minutes by default.

Channel 投递会把命令文本显示在聊天里；只在受信群 / topic 里启用 `channel` 或 `both`。提示落在 forum topic 时，OpenClaw 把 topic 保留下来给批准提示和后续。执行批准默认 30 分钟后过期。

> Inline approval buttons also require `channels.telegram.capabilities.inlineButtons` to allow the target surface (`dm`, `group`, or `all`). Approval IDs prefixed with `plugin:` resolve through plugin approvals; others resolve through exec approvals first.

行内批准按钮还要求 `channels.telegram.capabilities.inlineButtons` 在目标 surface（`dm`、`group` 或 `all`）上允许。带 `plugin:` 前缀的批准 ID 走插件批准；其他的先走执行批准。

> See [Exec approvals](/tools/exec-approvals).

见 [执行批准](/tools/exec-approvals)。

---

> ## Error reply controls

## 错误回复控制

> When the agent encounters a delivery or provider error, Telegram can either reply with the error text or suppress it. Two config keys control this behavior:

agent 碰到投递或 provider 错误时，Telegram 可以回一条错误文本，也可以静默。两个配置 key 控制这个行为：

> | Key                                 | Values            | Default | Description                                                                                     |
> | ----------------------------------- | ----------------- | ------- | ----------------------------------------------------------------------------------------------- |
> | `channels.telegram.errorPolicy`     | `reply`, `silent` | `reply` | `reply` sends a friendly error message to the chat. `silent` suppresses error replies entirely. |
> | `channels.telegram.errorCooldownMs` | number (ms)       | `60000` | Minimum time between error replies to the same chat. Prevents error spam during outages.        |

| Key                                 | 取值              | 默认    | 说明                                                                                       |
| ----------------------------------- | ----------------- | ------- | ------------------------------------------------------------------------------------------ |
| `channels.telegram.errorPolicy`     | `reply`、`silent` | `reply` | `reply` 给聊天发一条友好的错误消息。`silent` 完全静默掉错误回复。                          |
| `channels.telegram.errorCooldownMs` | 数字（毫秒）      | `60000` | 同一个聊天里两次错误回复之间的最短间隔，防止故障时被错误消息刷屏。                         |

> Per-account, per-group, and per-topic overrides are supported (same inheritance as other Telegram config keys).

支持按账号、按群、按 topic 覆盖（继承规则跟其他 Telegram 配置 key 一致）。

> ```json5
> {
>   channels: {
>     telegram: {
>       errorPolicy: "reply",
>       errorCooldownMs: 120000,
>       groups: {
>         "-1001234567890": {
>           errorPolicy: "silent", // suppress errors in this group
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
      errorPolicy: "reply",
      errorCooldownMs: 120000,
      groups: {
        "-1001234567890": {
          errorPolicy: "silent", // 在这个群里静默错误
        },
      },
    },
  },
}
```

---

> ## Troubleshooting

## 故障排查

> [展开: Bot does not respond to non mention group messages]
>
> * If `requireMention=false`, Telegram privacy mode must allow full visibility.
>   * BotFather: `/setprivacy` -> Disable
>   * then remove + re-add bot to group
> * `openclaw channels status` warns when config expects unmentioned group messages.
> * `openclaw channels status --probe` can check explicit numeric group IDs; wildcard `"*"` cannot be membership-probed.
> * quick session test: `/activation always`.

[展开：机器人对没 @ 的群消息不回]

- 如果 `requireMention=false`，Telegram privacy mode 必须允许完全可见。
  - BotFather：`/setprivacy` -> Disable。
  - 然后在每个群里把机器人移除再加回来。
- 配置里期望接收无 @ 群消息时，`openclaw channels status` 会发警告。
- `openclaw channels status --probe` 可以检查具体的数字群 ID；通配 `"*"` 没法探测群成员关系。
- 快速会话级测试：`/activation always`。

> [展开: Bot not seeing group messages at all]
>
> * when `channels.telegram.groups` exists, group must be listed (or include `"*"`)
> * verify bot membership in group
> * review logs: `openclaw logs --follow` for skip reasons

[展开：机器人根本看不到群消息]

- 一旦 `channels.telegram.groups` 存在，群必须列在里面（或者带 `"*"`）。
- 确认机器人在群里。
- 翻日志：`openclaw logs --follow` 看跳过原因。

> [展开: Commands work partially or not at all]
>
> * authorize your sender identity (pairing and/or numeric `allowFrom`)
> * command authorization still applies even when group policy is `open`
> * `setMyCommands failed` with `BOT_COMMANDS_TOO_MUCH` means the native menu has too many entries; reduce plugin/skill/custom commands or disable native menus
> * `deleteMyCommands` / `setMyCommands` startup calls and `sendChatAction` typing calls are bounded and retry once through Telegram's transport fallback on request timeout. Persistent network/fetch errors usually indicate DNS/HTTPS reachability issues to `api.telegram.org`

[展开：命令部分或完全不工作]

- 给你的发件人身份授权（pairing 和 / 或数字 `allowFrom`）。
- 即使群策略是 `open`，命令授权仍然要走。
- `setMyCommands failed` 报 `BOT_COMMANDS_TOO_MUCH`：原生菜单条目太多了；减少插件 / skill / 自定义命令，或者关掉原生菜单。
- `deleteMyCommands` / `setMyCommands` 启动调用、`sendChatAction` typing 调用都有边界，请求超时时通过 Telegram 传输回退重试一次。持续的网络 / fetch 错误一般是到 `api.telegram.org` 的 DNS / HTTPS 不可达。

> [展开: Startup reports unauthorized token]
>
> * `getMe returned 401` is a Telegram authentication failure for the configured bot token.
> * Re-copy or regenerate the bot token in BotFather, then update `channels.telegram.botToken`, `channels.telegram.tokenFile`, `channels.telegram.accounts.<id>.botToken`, or `TELEGRAM_BOT_TOKEN` for the default account.
> * `deleteWebhook 401 Unauthorized` during startup is also an auth failure; treating it as "no webhook exists" would only defer the same bad-token failure to later API calls.

[展开：启动报 token 未授权]

- `getMe returned 401` 是当前 bot token 的 Telegram 认证失败。
- 在 BotFather 里重新复制或重新生成 bot token，然后更新 `channels.telegram.botToken`、`channels.telegram.tokenFile`、`channels.telegram.accounts.<id>.botToken`，或默认账号的 `TELEGRAM_BOT_TOKEN`。
- 启动期 `deleteWebhook 401 Unauthorized` 也是认证失败；把它当作"没有 webhook 存在"只会把同样的坏 token 错误推迟到后续 API 调用。

> [展开: Polling or network instability]
>
> * Node 22+ + custom fetch/proxy can trigger immediate abort behavior if AbortSignal types mismatch.
> * Some hosts resolve `api.telegram.org` to IPv6 first; broken IPv6 egress can cause intermittent Telegram API failures.
> * If logs include `TypeError: fetch failed` or `Network request for 'getUpdates' failed!`, OpenClaw now retries these as recoverable network errors.
> * During polling startup, OpenClaw reuses the successful startup `getMe` probe for grammY so the runner does not need a second `getMe` before the first `getUpdates`.
> * If `deleteWebhook` fails with a transient network error during polling startup, OpenClaw continues into long polling instead of making another pre-poll control-plane call. A still-active webhook surfaces as a `getUpdates` conflict; OpenClaw then rebuilds the Telegram transport and retries webhook cleanup.
> * If Telegram sockets recycle on a short fixed cadence, check for a low `channels.telegram.timeoutSeconds`; bot clients clamp configured values below the outbound and `getUpdates` request guards, but older releases could abort every poll or reply when this was set below those guards.
> * If logs include `Polling stall detected`, OpenClaw restarts polling and rebuilds the Telegram transport after 120 seconds without completed long-poll liveness by default.
> * `openclaw channels status --probe` and `openclaw doctor` warn when a running polling account has not completed `getUpdates` after startup grace, when a running webhook account has not completed `setWebhook` after startup grace, or when the last successful polling transport activity is stale.
> * Increase `channels.telegram.pollingStallThresholdMs` only when long-running `getUpdates` calls are healthy but your host still reports false polling-stall restarts. Persistent stalls usually point to proxy, DNS, IPv6, or TLS egress issues between the host and `api.telegram.org`.
> * Telegram also honors process proxy env for Bot API transport, including `HTTP_PROXY`, `HTTPS_PROXY`, `ALL_PROXY`, and their lowercase variants. `NO_PROXY` / `no_proxy` can still bypass `api.telegram.org`.
> * If the OpenClaw managed proxy is configured through `OPENCLAW_PROXY_URL` for a service environment and no standard proxy env is present, Telegram uses that URL for Bot API transport too.
> * On VPS hosts with unstable direct egress/TLS, route Telegram API calls through `channels.telegram.proxy`:

[展开：Polling 或网络不稳]

- Node 22+ 配自定义 fetch / 代理时，AbortSignal 类型对不上可能导致立即 abort 的行为。
- 有些主机把 `api.telegram.org` 优先解析到 IPv6；IPv6 出网坏了会造成 Telegram API 间歇性失败。
- 日志里有 `TypeError: fetch failed` 或 `Network request for 'getUpdates' failed!`，OpenClaw 现在会把这些当作可恢复的网络错误重试。
- polling 启动期，OpenClaw 复用启动成功的 `getMe` 探测给 grammY 用，所以 runner 在第一次 `getUpdates` 之前不必再做一次 `getMe`。
- polling 启动期 `deleteWebhook` 因为短暂网络错误失败时，OpenClaw 继续进入 long polling，不再多发一次 pre-poll 控制面调用。还存活的 webhook 会以 `getUpdates` 冲突的形式暴露出来；这时 OpenClaw 会重建 Telegram 传输并重试 webhook 清理。
- Telegram 套接字按短而固定的周期重建时，检查 `channels.telegram.timeoutSeconds` 是不是太小；bot 客户端会把配置值压在 outbound 和 `getUpdates` 请求护栏之下，但更老的版本会因为这个值低于护栏而每次 poll 或回复都被中断。
- 日志里出现 `Polling stall detected` 时，OpenClaw 默认在 120 秒没有完成长轮询 liveness 后重启 polling 并重建 Telegram 传输。
- `openclaw channels status --probe` 和 `openclaw doctor` 会发出警告：跑着的 polling 账号过了启动宽限期还没完成 `getUpdates`；跑着的 webhook 账号过了启动宽限期还没完成 `setWebhook`；最后一次成功的 polling 传输活动已经过期。
- 只在长任务 `getUpdates` 调用本身没问题、但宿主还是报假阳性 polling stall 重启时，才调高 `channels.telegram.pollingStallThresholdMs`。持续卡住通常说明宿主到 `api.telegram.org` 之间有代理、DNS、IPv6 或 TLS 出网问题。
- Telegram 也尊重进程级代理环境变量（用于 Bot API 传输）：`HTTP_PROXY`、`HTTPS_PROXY`、`ALL_PROXY` 及它们的小写变体。`NO_PROXY` / `no_proxy` 仍然可以绕开 `api.telegram.org`。
- 如果 OpenClaw 托管代理通过 `OPENCLAW_PROXY_URL` 配给某个 service 环境，且没有标准代理环境变量时，Telegram 的 Bot API 传输也走这个 URL。
- VPS 上直连出网 / TLS 不稳时，让 Telegram API 调用走 `channels.telegram.proxy`：

> ```yaml
> channels:
>   telegram:
>     proxy: socks5://<user>:<password>@proxy-host:1080
> ```

```yaml
channels:
  telegram:
    proxy: socks5://<user>:<password>@proxy-host:1080
```

> * Node 22+ defaults to `autoSelectFamily=true` (except WSL2). Telegram DNS result order honors `OPENCLAW_TELEGRAM_DNS_RESULT_ORDER`, then `channels.telegram.network.dnsResultOrder`, then the process default such as `NODE_OPTIONS=--dns-result-order=ipv4first`; if none applies, Node 22+ falls back to `ipv4first`.
> * If your host is WSL2 or explicitly works better with IPv4-only behavior, force family selection:

- Node 22+ 默认 `autoSelectFamily=true`（WSL2 例外）。Telegram 的 DNS 结果顺序按 `OPENCLAW_TELEGRAM_DNS_RESULT_ORDER`、然后 `channels.telegram.network.dnsResultOrder`、然后进程默认值（如 `NODE_OPTIONS=--dns-result-order=ipv4first`）依次生效；都没设时，Node 22+ 回退到 `ipv4first`。
- 宿主是 WSL2，或者明显更适合纯 IPv4 时，强制 family 选择：

> ```yaml
> channels:
>   telegram:
>     network:
>       autoSelectFamily: false
> ```

```yaml
channels:
  telegram:
    network:
      autoSelectFamily: false
```

> * RFC 2544 benchmark-range answers (`198.18.0.0/15`) are already allowed for Telegram media downloads by default. If a trusted fake-IP or transparent proxy rewrites `api.telegram.org` to some other private/internal/special-use address during media downloads, you can opt in to the Telegram-only bypass:

- Telegram 媒体下载默认已经允许 RFC 2544 基准范围（`198.18.0.0/15`）的响应。如果受信的 fake-IP 或透明代理在媒体下载时把 `api.telegram.org` 重写到其他私有 / 内部 / 特殊用途地址，可以选择性开启 Telegram 专属的旁路：

> ```yaml
> channels:
>   telegram:
>     network:
>       dangerouslyAllowPrivateNetwork: true
> ```

```yaml
channels:
  telegram:
    network:
      dangerouslyAllowPrivateNetwork: true
```

> * The same opt-in is available per account at `channels.telegram.accounts.<accountId>.network.dangerouslyAllowPrivateNetwork`.
> * If your proxy resolves Telegram media hosts into `198.18.x.x`, leave the dangerous flag off first. Telegram media already allows the RFC 2544 benchmark range by default.

- 同样的开关在账号粒度也有：`channels.telegram.accounts.<accountId>.network.dangerouslyAllowPrivateNetwork`。
- 如果你的代理把 Telegram 媒体主机解析成 `198.18.x.x`，先不要打开危险开关 —— Telegram 媒体默认已经允许 RFC 2544 基准范围。

> <Warning>
>   `channels.telegram.network.dangerouslyAllowPrivateNetwork` weakens Telegram media SSRF protections. Use it only for trusted operator-controlled proxy environments such as Clash, Mihomo, or Surge fake-IP routing when they synthesize private or special-use answers outside the RFC 2544 benchmark range. Leave it off for normal public internet Telegram access.
> </Warning>

> **警告**：`channels.telegram.network.dangerouslyAllowPrivateNetwork` 会削弱 Telegram 媒体的 SSRF 防护。只在受信、由运维控制的代理环境下用（比如 Clash、Mihomo、Surge 的 fake-IP 路由），并且它们合成的私有 / 特殊地址不在 RFC 2544 基准范围里。普通公网 Telegram 访问保持关闭。

> * Environment overrides (temporary):
>   * `OPENCLAW_TELEGRAM_DISABLE_AUTO_SELECT_FAMILY=1`
>   * `OPENCLAW_TELEGRAM_ENABLE_AUTO_SELECT_FAMILY=1`
>   * `OPENCLAW_TELEGRAM_DNS_RESULT_ORDER=ipv4first`
> * Validate DNS answers:

- 环境变量临时覆盖：
  - `OPENCLAW_TELEGRAM_DISABLE_AUTO_SELECT_FAMILY=1`
  - `OPENCLAW_TELEGRAM_ENABLE_AUTO_SELECT_FAMILY=1`
  - `OPENCLAW_TELEGRAM_DNS_RESULT_ORDER=ipv4first`
- 校验 DNS 响应：

> ```bash
> dig +short api.telegram.org A
> dig +short api.telegram.org AAAA
> ```

```bash
dig +short api.telegram.org A
dig +short api.telegram.org AAAA
```

> More help: [Channel troubleshooting](/channels/troubleshooting).

更多帮助：[通道故障排查](/channels/troubleshooting)。

---

> ## Configuration reference

## 配置项参考

> Primary reference: [Configuration reference - Telegram](/gateway/config-channels#telegram).

主参考：[配置参考 - Telegram](/gateway/config-channels#telegram)。

> [展开: High-signal Telegram fields]
>
> * startup/auth: `enabled`, `botToken`, `tokenFile`, `accounts.*` (`tokenFile` must point to a regular file; symlinks are rejected)
> * access control: `dmPolicy`, `allowFrom`, `groupPolicy`, `groupAllowFrom`, `groups`, `groups.*.topics.*`, top-level `bindings[]` (`type: "acp"`)
> * exec approvals: `execApprovals`, `accounts.*.execApprovals`
> * command/menu: `commands.native`, `commands.nativeSkills`, `customCommands`
> * threading/replies: `replyToMode`, `dm.threadReplies`, `direct.*.threadReplies`
> * streaming: `streaming` (preview), `streaming.preview.toolProgress`, `blockStreaming`
> * formatting/delivery: `textChunkLimit`, `chunkMode`, `linkPreview`, `responsePrefix`
> * media/network: `mediaMaxMb`, `mediaGroupFlushMs`, `timeoutSeconds`, `pollingStallThresholdMs`, `retry`, `network.autoSelectFamily`, `network.dangerouslyAllowPrivateNetwork`, `proxy`
> * custom API root: `apiRoot` (Bot API root only; do not include `/bot<TOKEN>`)
> * webhook: `webhookUrl`, `webhookSecret`, `webhookPath`, `webhookHost`
> * actions/capabilities: `capabilities.inlineButtons`, `actions.sendMessage|editMessage|deleteMessage|reactions|sticker`
> * reactions: `reactionNotifications`, `reactionLevel`
> * errors: `errorPolicy`, `errorCooldownMs`
> * writes/history: `configWrites`, `historyLimit`, `dmHistoryLimit`, `dms.*.historyLimit`

[展开：高信号量的 Telegram 字段]

- 启动 / 认证：`enabled`、`botToken`、`tokenFile`、`accounts.*`（`tokenFile` 必须指向普通文件；符号链接会被拒绝）
- 访问控制：`dmPolicy`、`allowFrom`、`groupPolicy`、`groupAllowFrom`、`groups`、`groups.*.topics.*`、顶层 `bindings[]`（`type: "acp"`）
- 执行批准：`execApprovals`、`accounts.*.execApprovals`
- 命令 / 菜单：`commands.native`、`commands.nativeSkills`、`customCommands`
- 线程 / 回复：`replyToMode`、`dm.threadReplies`、`direct.*.threadReplies`
- 流式：`streaming`（预览）、`streaming.preview.toolProgress`、`blockStreaming`
- 格式化 / 投递：`textChunkLimit`、`chunkMode`、`linkPreview`、`responsePrefix`
- 媒体 / 网络：`mediaMaxMb`、`mediaGroupFlushMs`、`timeoutSeconds`、`pollingStallThresholdMs`、`retry`、`network.autoSelectFamily`、`network.dangerouslyAllowPrivateNetwork`、`proxy`
- 自定义 API 根：`apiRoot`（只能写 Bot API 根，不要带 `/bot<TOKEN>`）
- webhook：`webhookUrl`、`webhookSecret`、`webhookPath`、`webhookHost`
- 动作 / 能力：`capabilities.inlineButtons`、`actions.sendMessage|editMessage|deleteMessage|reactions|sticker`
- 表情：`reactionNotifications`、`reactionLevel`
- 错误：`errorPolicy`、`errorCooldownMs`
- 写入 / 历史：`configWrites`、`historyLimit`、`dmHistoryLimit`、`dms.*.historyLimit`

> <Note>
>   Multi-account precedence: when two or more account IDs are configured, set `channels.telegram.defaultAccount` (or include `channels.telegram.accounts.default`) to make default routing explicit. Otherwise OpenClaw falls back to the first normalized account ID and `openclaw doctor` warns. Named accounts inherit `channels.telegram.allowFrom` / `groupAllowFrom`, but not `accounts.default.*` values.
> </Note>

> **提示**：多账号优先级 —— 配置了两个或更多账号 ID 时，设 `channels.telegram.defaultAccount`（或带上 `channels.telegram.accounts.default`），让默认路由明确下来。否则 OpenClaw 回退到第一个归一化后的账号 ID，`openclaw doctor` 会发警告。命名账号会继承 `channels.telegram.allowFrom` / `groupAllowFrom`，但不会继承 `accounts.default.*` 的值。

---

> ## Related

## 相关

> <CardGroup cols={2}>
>   <Card title="Pairing" icon="link" href="/channels/pairing">
>     Pair a Telegram user to the gateway.
>   </Card>
>
>   <Card title="Groups" icon="users" href="/channels/groups">
>     Group and topic allowlist behavior.
>   </Card>
>
>   <Card title="Channel routing" icon="route" href="/channels/channel-routing">
>     Route inbound messages to agents.
>   </Card>
>
>   <Card title="Security" icon="shield" href="/gateway/security">
>     Threat model and hardening.
>   </Card>
>
>   <Card title="Multi-agent routing" icon="sitemap" href="/concepts/multi-agent">
>     Map groups and topics to agents.
>   </Card>
>
>   <Card title="Troubleshooting" icon="wrench" href="/channels/troubleshooting">
>     Cross-channel diagnostics.
>   </Card>
> </CardGroup>

- [配对](/channels/pairing)：把一个 Telegram 用户配对到 Gateway。
- [群组](/channels/groups)：群和 topic 的白名单行为。
- [通道路由](/channels/channel-routing)：把接收消息路由到 agent。
- [安全](/gateway/security)：威胁模型与加固。
- [多 agent 路由](/concepts/multi-agent)：把群和 topic 映射到 agent。
- [故障排查](/channels/troubleshooting)：跨通道诊断。
