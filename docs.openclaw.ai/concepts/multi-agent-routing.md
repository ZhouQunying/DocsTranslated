# Multi-agent routing

> Run multiple *isolated* agents — each with its own workspace, state directory (`agentDir`), and session history — plus multiple channel accounts (e.g. two WhatsApps) in one running Gateway. Inbound messages are routed to the right agent through bindings.

在一个 Gateway 里跑多个*隔离的* agent —— 每个有自己的工作区、状态目录（`agentDir`）和会话历史 —— 并支持多个通道账号（比如两个 WhatsApp）。接收消息通过绑定路由到对应的 agent。

> An **agent** here is the full per-persona scope: workspace files, auth profiles, model registry, and session store. `agentDir` is the on-disk state directory that holds this per-agent config at `~/.openclaw/agents/<agentId>/`. A **binding** maps a channel account (e.g. a Slack workspace or a WhatsApp number) to one of those agents.

这里的 **agent** 是按 persona 划分的完整范围：工作区文件、认证 profile、模型注册表、会话存储。`agentDir` 是磁盘上保存这份 per-agent 配置的状态目录，在 `~/.openclaw/agents/<agentId>/`。**绑定** 把一个通道账号（比如 Slack 工作区或 WhatsApp 号）映射到其中一个 agent。

---

> ## What is "one agent"?

## 什么是"一个 agent"

> An **agent** is a fully scoped brain with its own:
>
> * **Workspace** (files, AGENTS.md/SOUL.md/USER.md, local notes, persona rules).
> * **State directory** (`agentDir`) for auth profiles, model registry, and per-agent config.
> * **Session store** (chat history + routing state) under `~/.openclaw/agents/<agentId>/sessions`.

**agent** 是一个完整范围的"大脑"，自带：

- **工作区**（文件、AGENTS.md / SOUL.md / USER.md、本地笔记、persona 规则）。
- **状态目录**（`agentDir`）：认证 profile、模型注册表、per-agent 配置。
- **会话存储**（聊天历史 + 路由状态），在 `~/.openclaw/agents/<agentId>/sessions` 下。

> Auth profiles are **per-agent**. Each agent reads from its own:
>
> ```text
> ~/.openclaw/agents/<agentId>/agent/auth-profiles.json
> ```

认证 profile 是 **per-agent** 的。每个 agent 读自己的：

```text
~/.openclaw/agents/<agentId>/agent/auth-profiles.json
```

> <Note>
>   `sessions_history` is the safer cross-session recall path here too: it returns a bounded, sanitized view, not a raw transcript dump. Assistant recall strips thinking tags, `<relevant-memories>` scaffolding, plain-text tool-call XML payloads (including `<tool_call>...</tool_call>`, `<function_call>...</function_call>`, `<tool_calls>...</tool_calls>`, `<function_calls>...</function_calls>`, and truncated tool-call blocks), downgraded tool-call scaffolding, leaked ASCII/full-width model control tokens, and malformed MiniMax tool-call XML before redaction/truncation.
> </Note>

> **提示**：这里跨会话召回也优先用 `sessions_history`：它返回一个有界、经过 sanitize 的视图，不是原始 transcript dump。assistant 召回在脱敏 / 截断之前会先剥掉 thinking 标签、`<relevant-memories>` 脚手架、纯文本工具调用 XML 载荷（含 `<tool_call>...</tool_call>`、`<function_call>...</function_call>`、`<tool_calls>...</tool_calls>`、`<function_calls>...</function_calls>` 和被截断的工具调用块）、降级的工具调用脚手架、泄漏的 ASCII / 全角模型控制 token、以及畸形的 MiniMax 工具调用 XML。

> <Warning>
>   Never reuse `agentDir` across agents (it causes auth/session collisions). Agents can read through to the default/main agent's auth profiles when they do not have a local profile, but OpenClaw does not clone OAuth refresh tokens into the secondary agent store. If you want an independent OAuth account, sign in from that agent; if you copy credentials manually, copy only portable static `api_key` or `token` profiles.
> </Warning>

> **警告**：不要在多个 agent 间复用 `agentDir`（会造成认证 / 会话冲突）。agent 没有本地 profile 时可以 read-through 到默认 / 主 agent 的认证 profile，但 OpenClaw 不会把 OAuth refresh token 克隆进二级 agent 存储。要独立的 OAuth 账号，就从那个 agent 登录；手动复制凭证时，只复制可移植的静态 `api_key` 或 `token` profile。

> Skills are loaded from each agent workspace plus shared roots such as `~/.openclaw/skills`, then filtered by the effective agent skill allowlist when configured. Use `agents.defaults.skills` for a shared baseline and `agents.list[].skills` for per-agent replacement. See [Skills: per-agent vs shared](/tools/skills#per-agent-vs-shared-skills) and [Skills: agent skill allowlists](/tools/skills#agent-skill-allowlists).

skill 从每个 agent 工作区加 `~/.openclaw/skills` 这种共享根加载，然后按配置的有效 agent skill 白名单过滤。共享基线用 `agents.defaults.skills`，per-agent 替换用 `agents.list[].skills`。见 [Skill：per-agent vs 共享](/tools/skills#per-agent-vs-shared-skills) 和 [Skill：agent skill 白名单](/tools/skills#agent-skill-allowlists)。

> The Gateway can host **one agent** (default) or **many agents** side-by-side.

Gateway 可以承载**一个 agent**（默认）或**多个 agent** 并存。

> <Note>
>   **Workspace note:** each agent's workspace is the **default cwd**, not a hard sandbox. Relative paths resolve inside the workspace, but absolute paths can reach other host locations unless sandboxing is enabled. See [Sandboxing](/gateway/sandboxing).
> </Note>

> **提示 — 工作区说明**：每个 agent 的工作区是**默认 cwd**，不是硬沙盒。相对路径在工作区内解析，但绝对路径仍可触达宿主机其他位置 —— 除非启用沙盒。见 [沙盒](/gateway/sandboxing)。

---

> ## Paths (quick map)

## 路径速查

> * Config: `~/.openclaw/openclaw.json` (or `OPENCLAW_CONFIG_PATH`)
> * State dir: `~/.openclaw` (or `OPENCLAW_STATE_DIR`)
> * Workspace: `~/.openclaw/workspace` (or `~/.openclaw/workspace-<agentId>`)
> * Agent dir: `~/.openclaw/agents/<agentId>/agent` (or `agents.list[].agentDir`)
> * Sessions: `~/.openclaw/agents/<agentId>/sessions`

- 配置：`~/.openclaw/openclaw.json`（或 `OPENCLAW_CONFIG_PATH`）
- 状态目录：`~/.openclaw`（或 `OPENCLAW_STATE_DIR`）
- 工作区：`~/.openclaw/workspace`（或 `~/.openclaw/workspace-<agentId>`）
- agent 目录：`~/.openclaw/agents/<agentId>/agent`（或 `agents.list[].agentDir`）
- 会话：`~/.openclaw/agents/<agentId>/sessions`

> ### Single-agent mode (default)

### 单 agent 模式（默认）

> If you do nothing, OpenClaw runs a single agent:
>
> * `agentId` defaults to **`main`**.
> * Sessions are keyed as `agent:main:<mainKey>`.
> * Workspace defaults to `~/.openclaw/workspace` (or `~/.openclaw/workspace-<profile>` when `OPENCLAW_PROFILE` is set).
> * State defaults to `~/.openclaw/agents/main/agent`.

什么都不动时，OpenClaw 跑一个单 agent：

- `agentId` 默认 **`main`**。
- 会话 key 是 `agent:main:<mainKey>`。
- 工作区默认 `~/.openclaw/workspace`（设了 `OPENCLAW_PROFILE` 时是 `~/.openclaw/workspace-<profile>`）。
- 状态默认 `~/.openclaw/agents/main/agent`。

---

> ## Agent helper

## Agent 辅助命令

> Use the agent wizard to add a new isolated agent:
>
> ```bash
> openclaw agents add work
> ```

用 agent 向导加一个新的隔离 agent：

```bash
openclaw agents add work
```

> Then add `bindings` (or let the wizard do it) to route inbound messages.

然后加 `bindings`（或让向导帮你做）把接收消息路由过去。

> Verify with:
>
> ```bash
> openclaw agents list --bindings
> ```

验证：

```bash
openclaw agents list --bindings
```

---

> ## Quick start

## 快速上手

> [步骤 1: Create each agent workspace]
>
> Use the wizard or create workspaces manually:
>
> ```bash
> openclaw agents add coding
> openclaw agents add social
> ```
>
> Each agent gets its own workspace with `SOUL.md`, `AGENTS.md`, and optional `USER.md`, plus a dedicated `agentDir` and session store under `~/.openclaw/agents/<agentId>`.

[步骤 1：给每个 agent 建工作区]

用向导或手工创建工作区：

```bash
openclaw agents add coding
openclaw agents add social
```

每个 agent 拿到自己的工作区，含 `SOUL.md`、`AGENTS.md`，可选 `USER.md`，外加 `~/.openclaw/agents/<agentId>` 下专属的 `agentDir` 和会话存储。

> [步骤 2: Create channel accounts]
>
> Create one account per agent on your preferred channels:
>
> * Discord: one bot per agent, enable Message Content Intent, copy each token.
> * Telegram: one bot per agent via BotFather, copy each token.
> * WhatsApp: link each phone number per account.
>
> ```bash
> openclaw channels login --channel whatsapp --account work
> ```
>
> See channel guides: [Discord](/channels/discord), [Telegram](/channels/telegram), [WhatsApp](/channels/whatsapp).

[步骤 2：建通道账号]

在你选用的通道上每个 agent 建一个账号：

- Discord：每个 agent 一个 bot，启用 Message Content Intent，复制每个 token。
- Telegram：每个 agent 通过 BotFather 建一个 bot，复制每个 token。
- WhatsApp：每个账号链接一个手机号。

```bash
openclaw channels login --channel whatsapp --account work
```

通道指南：[Discord](/channels/discord)、[Telegram](/channels/telegram)、[WhatsApp](/channels/whatsapp)。

> [步骤 3: Add agents, accounts, and bindings]
>
> Add agents under `agents.list`, channel accounts under `channels.<channel>.accounts`, and connect them with `bindings` (examples below).

[步骤 3：添加 agent、账号和绑定]

agent 加到 `agents.list` 下，通道账号加到 `channels.<channel>.accounts` 下，用 `bindings` 把它们连起来（下面有例子）。

> [步骤 4: Restart and verify]
>
> ```bash
> openclaw gateway restart
> openclaw agents list --bindings
> openclaw channels status --probe
> ```

[步骤 4：重启并验证]

```bash
openclaw gateway restart
openclaw agents list --bindings
openclaw channels status --probe
```

---

> ## Multiple agents = multiple people, multiple personalities

## 多 agent = 多人、多人格

> With **multiple agents**, each `agentId` becomes a **fully isolated persona**:
>
> * **Different phone numbers/accounts** (per channel `accountId`).
> * **Different personalities** (per-agent workspace files like `AGENTS.md` and `SOUL.md`).
> * **Separate auth + sessions** (no cross-talk unless explicitly enabled).

**多 agent** 时，每个 `agentId` 是一个**完全隔离的 persona**：

- **不同的电话 / 账号**（按通道的 `accountId`）。
- **不同的人格**（per-agent 工作区文件，比如 `AGENTS.md` 和 `SOUL.md`）。
- **认证 + 会话独立**（除非显式启用，否则不会互通）。

> This lets **multiple people** share one Gateway server while keeping their AI "brains" and data isolated.

这样**多人**可以共享一台 Gateway 服务器，同时各自的 AI "大脑"和数据保持隔离。

---

> ## Cross-agent QMD memory search

## 跨 agent 的 QMD 记忆搜索

> If one agent should search another agent's QMD session transcripts, add extra collections under `agents.list[].memorySearch.qmd.extraCollections`. Use `agents.defaults.memorySearch.qmd.extraCollections` only when every agent should inherit the same shared transcript collections.

某个 agent 要搜索另一个 agent 的 QMD 会话 transcript 时，在 `agents.list[].memorySearch.qmd.extraCollections` 下加额外的 collection。只有所有 agent 都要继承同一组共享 transcript collection 时，才用 `agents.defaults.memorySearch.qmd.extraCollections`。

> ```json5
> {
>   agents: {
>     defaults: {
>       workspace: "~/workspaces/main",
>       memorySearch: {
>         qmd: {
>           extraCollections: [{ path: "~/agents/family/sessions", name: "family-sessions" }],
>         },
>       },
>     },
>     list: [
>       {
>         id: "main",
>         workspace: "~/workspaces/main",
>         memorySearch: {
>           qmd: {
>             extraCollections: [{ path: "notes" }], // resolves inside workspace -> collection named "notes-main"
>           },
>         },
>       },
>       { id: "family", workspace: "~/workspaces/family" },
>     ],
>   },
>   memory: {
>     backend: "qmd",
>     qmd: { includeDefaultMemory: false },
>   },
> }
> ```

```json5
{
  agents: {
    defaults: {
      workspace: "~/workspaces/main",
      memorySearch: {
        qmd: {
          extraCollections: [{ path: "~/agents/family/sessions", name: "family-sessions" }],
        },
      },
    },
    list: [
      {
        id: "main",
        workspace: "~/workspaces/main",
        memorySearch: {
          qmd: {
            extraCollections: [{ path: "notes" }], // 在工作区内解析 -> collection 名 "notes-main"
          },
        },
      },
      { id: "family", workspace: "~/workspaces/family" },
    ],
  },
  memory: {
    backend: "qmd",
    qmd: { includeDefaultMemory: false },
  },
}
```

> The extra collection path can be shared across agents, but the collection name stays explicit when the path is outside the agent workspace. Paths inside the workspace remain agent-scoped so each agent keeps its own transcript search set.

额外 collection 路径可以跨 agent 共享，但路径在 agent 工作区外时 collection 名要保持显式。工作区内的路径仍按 agent 作用域，每个 agent 保留自己的 transcript 搜索集合。

---

> ## One WhatsApp number, multiple people (DM split)

## 一个 WhatsApp 号、多个人（私聊分流）

> You can route **different WhatsApp DMs** to different agents while staying on **one WhatsApp account**. Match on sender E.164 (like `+15551234567`) with `peer.kind: "direct"`. Replies still come from the same WhatsApp number (no per-agent sender identity).

可以把**不同的 WhatsApp 私聊**路由到不同 agent，同时只用**一个 WhatsApp 账号**。按发件人 E.164（比如 `+15551234567`）配 `peer.kind: "direct"` 匹配。回复仍来自同一个 WhatsApp 号（没有 per-agent 的发件人身份）。

> <Note>
>   Direct chats collapse to the agent's **main session key**, so true isolation requires **one agent per person**.
> </Note>

> **提示**：私聊会收敛到 agent 的 **main 会话 key**，所以真正隔离需要**每人一个 agent**。

> Example:
>
> ```json5
> {
>   agents: {
>     list: [
>       { id: "alex", workspace: "~/.openclaw/workspace-alex" },
>       { id: "mia", workspace: "~/.openclaw/workspace-mia" },
>     ],
>   },
>   bindings: [
>     {
>       agentId: "alex",
>       match: { channel: "whatsapp", peer: { kind: "direct", id: "+15551230001" } },
>     },
>     {
>       agentId: "mia",
>       match: { channel: "whatsapp", peer: { kind: "direct", id: "+15551230002" } },
>     },
>   ],
>   channels: {
>     whatsapp: {
>       dmPolicy: "allowlist",
>       allowFrom: ["+15551230001", "+15551230002"],
>     },
>   },
> }
> ```

例子：

```json5
{
  agents: {
    list: [
      { id: "alex", workspace: "~/.openclaw/workspace-alex" },
      { id: "mia", workspace: "~/.openclaw/workspace-mia" },
    ],
  },
  bindings: [
    {
      agentId: "alex",
      match: { channel: "whatsapp", peer: { kind: "direct", id: "+15551230001" } },
    },
    {
      agentId: "mia",
      match: { channel: "whatsapp", peer: { kind: "direct", id: "+15551230002" } },
    },
  ],
  channels: {
    whatsapp: {
      dmPolicy: "allowlist",
      allowFrom: ["+15551230001", "+15551230002"],
    },
  },
}
```

> Notes:
>
> * DM access control is **global per WhatsApp account** (pairing/allowlist), not per agent.
> * For shared groups, bind the group to one agent or use [Broadcast groups](/channels/broadcast-groups).

说明：

- 私聊访问控制按 **WhatsApp 账号全局**（pairing / 白名单），不是按 agent。
- 对共享群，把群绑定到一个 agent，或者用 [广播组](/channels/broadcast-groups)。

---

> ## Routing rules (how messages pick an agent)

## 路由规则（消息怎么挑 agent）

> Bindings are **deterministic** and **most-specific wins**:

绑定是**确定性**的，**越具体越优先**：

> [步骤 1: peer match] Exact DM/group/channel id.

[步骤 1：peer 匹配] 精确的 DM / 群 / 频道 id。

> [步骤 2: parentPeer match] Thread inheritance.

[步骤 2：parentPeer 匹配] thread 继承。

> [步骤 3: guildId + roles] Discord role routing.

[步骤 3：guildId + roles] Discord 角色路由。

> [步骤 4: guildId] Discord.

[步骤 4：guildId] Discord。

> [步骤 5: teamId] Slack.

[步骤 5：teamId] Slack。

> [步骤 6: accountId match for a channel] Per-account fallback.

[步骤 6：通道下 accountId 匹配] 按账号回退。

> [步骤 7: Channel-level match] `accountId: "*"`.

[步骤 7：通道级匹配] `accountId: "*"`。

> [步骤 8: Default agent] Fallback to `agents.list[].default`, else first list entry, default: `main`.

[步骤 8：默认 agent] 回退到 `agents.list[].default`，不行就用列表第一个，再不行回退到 `main`。

> [展开: Tie-breaking and AND semantics]
>
> * If multiple bindings match in the same tier, the first one in config order wins.
> * If a binding sets multiple match fields (for example `peer` + `guildId`), all specified fields are required (`AND` semantics).

[展开：平局规则和 AND 语义]

- 同一层有多条绑定命中时，配置顺序里的第一条胜出。
- 绑定设了多个 match 字段时（比如 `peer` + `guildId`），所有指定字段都必须命中（`AND` 语义）。

> [展开: Account-scope detail]
>
> * A binding that omits `accountId` matches the default account only.
> * Use `accountId: "*"` for a channel-wide fallback across all accounts.
> * If you later add the same binding for the same agent with an explicit account id, OpenClaw upgrades the existing channel-only binding to account-scoped instead of duplicating it.

[展开：账号作用域细节]

- 没设 `accountId` 的绑定只匹配默认账号。
- 通道范围、跨所有账号的回退用 `accountId: "*"`。
- 之后给同一 agent 加同样绑定但带显式 account id 时，OpenClaw 把现有的"只通道级" 绑定升级成"账号级"，不重复。

---

> ## Multiple accounts / phone numbers

## 多账号 / 多电话号

> Channels that support **multiple accounts** (e.g. WhatsApp) use `accountId` to identify each login. Each `accountId` can be routed to a different agent, so one server can host multiple phone numbers without mixing sessions.

支持**多账号**的通道（比如 WhatsApp）用 `accountId` 标识每次登录。每个 `accountId` 可以路由到不同 agent，所以一台服务器能承载多个电话号而不混会话。

> If you want a channel-wide default account when `accountId` is omitted, set `channels.<channel>.defaultAccount` (optional). When unset, OpenClaw falls back to `default` if present, otherwise the first configured account id (sorted).

`accountId` 省略时想要一个通道级默认账号，设 `channels.<channel>.defaultAccount`（可选）。不设时，OpenClaw 先回退到 `default`（有的话），否则用第一个配置的账号 id（按排序）。

> Common channels supporting this pattern include:
>
> * `whatsapp`, `telegram`, `discord`, `slack`, `signal`, `imessage`
> * `irc`, `line`, `googlechat`, `mattermost`, `matrix`, `nextcloud-talk`
> * `zalo`, `zalouser`, `nostr`, `feishu`

支持这种模式的常见通道：

- `whatsapp`、`telegram`、`discord`、`slack`、`signal`、`imessage`
- `irc`、`line`、`googlechat`、`mattermost`、`matrix`、`nextcloud-talk`
- `zalo`、`zalouser`、`nostr`、`feishu`

---

> ## Concepts

## 概念

> * `agentId`: one "brain" (workspace, per-agent auth, per-agent session store).
> * `accountId`: one channel account instance (e.g. WhatsApp account `"personal"` vs `"biz"`).
> * `binding`: routes inbound messages to an `agentId` by `(channel, accountId, peer)` and optionally guild/team ids.
> * Direct chats collapse to `agent:<agentId>:<mainKey>` (per-agent "main"; `session.mainKey`).

- `agentId`：一个"大脑"（工作区、per-agent 认证、per-agent 会话存储）。
- `accountId`：一个通道账号实例（比如 WhatsApp `"personal"` 和 `"biz"`）。
- `binding`：按 `(通道、accountId、peer)` 加可选的 guild / team id，把接收消息路由到某个 `agentId`。
- 私聊会收敛到 `agent:<agentId>:<mainKey>`（per-agent 的 "main"；`session.mainKey`）。

---

> ## Platform examples

## 平台示例

> [展开: Discord bots per agent]
>
> Each Discord bot account maps to a unique `accountId`. Bind each account to an agent and keep allowlists per bot.

[展开：每个 agent 一个 Discord bot]

每个 Discord bot 账号对应一个唯一 `accountId`。把每个账号绑到一个 agent，按 bot 维护白名单。

> ```json5
> {
>   agents: {
>     list: [
>       { id: "main", workspace: "~/.openclaw/workspace-main" },
>       { id: "coding", workspace: "~/.openclaw/workspace-coding" },
>     ],
>   },
>   bindings: [
>     { agentId: "main", match: { channel: "discord", accountId: "default" } },
>     { agentId: "coding", match: { channel: "discord", accountId: "coding" } },
>   ],
>   channels: {
>     discord: {
>       groupPolicy: "allowlist",
>       accounts: {
>         default: {
>           token: "DISCORD_BOT_TOKEN_MAIN",
>           guilds: {
>             "123456789012345678": {
>               channels: {
>                 "222222222222222222": { allow: true, requireMention: false },
>               },
>             },
>           },
>         },
>         coding: {
>           token: "DISCORD_BOT_TOKEN_CODING",
>           guilds: {
>             "123456789012345678": {
>               channels: {
>                 "333333333333333333": { allow: true, requireMention: false },
>               },
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
  agents: {
    list: [
      { id: "main", workspace: "~/.openclaw/workspace-main" },
      { id: "coding", workspace: "~/.openclaw/workspace-coding" },
    ],
  },
  bindings: [
    { agentId: "main", match: { channel: "discord", accountId: "default" } },
    { agentId: "coding", match: { channel: "discord", accountId: "coding" } },
  ],
  channels: {
    discord: {
      groupPolicy: "allowlist",
      accounts: {
        default: {
          token: "DISCORD_BOT_TOKEN_MAIN",
          guilds: {
            "123456789012345678": {
              channels: {
                "222222222222222222": { allow: true, requireMention: false },
              },
            },
          },
        },
        coding: {
          token: "DISCORD_BOT_TOKEN_CODING",
          guilds: {
            "123456789012345678": {
              channels: {
                "333333333333333333": { allow: true, requireMention: false },
              },
            },
          },
        },
      },
    },
  },
}
```

> * Invite each bot to the guild and enable Message Content Intent.
> * Tokens live in `channels.discord.accounts.<id>.token` (default account can use `DISCORD_BOT_TOKEN`).

- 把每个 bot 邀请到 guild 里，启用 Message Content Intent。
- token 放在 `channels.discord.accounts.<id>.token`（默认账号可以用 `DISCORD_BOT_TOKEN`）。

> [展开: Telegram bots per agent]
>
> ```json5
> {
>   agents: {
>     list: [
>       { id: "main", workspace: "~/.openclaw/workspace-main" },
>       { id: "alerts", workspace: "~/.openclaw/workspace-alerts" },
>     ],
>   },
>   bindings: [
>     { agentId: "main", match: { channel: "telegram", accountId: "default" } },
>     { agentId: "alerts", match: { channel: "telegram", accountId: "alerts" } },
>   ],
>   channels: {
>     telegram: {
>       accounts: {
>         default: {
>           botToken: "123456:ABC...",
>           dmPolicy: "pairing",
>         },
>         alerts: {
>           botToken: "987654:XYZ...",
>           dmPolicy: "allowlist",
>           allowFrom: ["tg:123456789"],
>         },
>       },
>     },
>   },
> }
> ```

[展开：每个 agent 一个 Telegram bot]

```json5
{
  agents: {
    list: [
      { id: "main", workspace: "~/.openclaw/workspace-main" },
      { id: "alerts", workspace: "~/.openclaw/workspace-alerts" },
    ],
  },
  bindings: [
    { agentId: "main", match: { channel: "telegram", accountId: "default" } },
    { agentId: "alerts", match: { channel: "telegram", accountId: "alerts" } },
  ],
  channels: {
    telegram: {
      accounts: {
        default: {
          botToken: "123456:ABC...",
          dmPolicy: "pairing",
        },
        alerts: {
          botToken: "987654:XYZ...",
          dmPolicy: "allowlist",
          allowFrom: ["tg:123456789"],
        },
      },
    },
  },
}
```

> * Create one bot per agent with BotFather and copy each token.
> * Tokens live in `channels.telegram.accounts.<id>.botToken` (default account can use `TELEGRAM_BOT_TOKEN`).

- 每个 agent 用 BotFather 建一个 bot，复制每个 token。
- token 放在 `channels.telegram.accounts.<id>.botToken`（默认账号可以用 `TELEGRAM_BOT_TOKEN`）。

> [展开: WhatsApp numbers per agent]
>
> Link each account before starting the gateway:
>
> ```bash
> openclaw channels login --channel whatsapp --account personal
> openclaw channels login --channel whatsapp --account biz
> ```

[展开：每个 agent 一个 WhatsApp 号]

启动 Gateway 之前先链接每个账号：

```bash
openclaw channels login --channel whatsapp --account personal
openclaw channels login --channel whatsapp --account biz
```

> `~/.openclaw/openclaw.json` (JSON5):
>
> ```js
> {
>   agents: {
>     list: [
>       {
>         id: "home",
>         default: true,
>         name: "Home",
>         workspace: "~/.openclaw/workspace-home",
>         agentDir: "~/.openclaw/agents/home/agent",
>       },
>       {
>         id: "work",
>         name: "Work",
>         workspace: "~/.openclaw/workspace-work",
>         agentDir: "~/.openclaw/agents/work/agent",
>       },
>     ],
>   },
>
>   // Deterministic routing: first match wins (most-specific first).
>   bindings: [
>     { agentId: "home", match: { channel: "whatsapp", accountId: "personal" } },
>     { agentId: "work", match: { channel: "whatsapp", accountId: "biz" } },
>
>     // Optional per-peer override (example: send a specific group to work agent).
>     {
>       agentId: "work",
>       match: {
>         channel: "whatsapp",
>         accountId: "personal",
>         peer: { kind: "group", id: "1203630...@g.us" },
>       },
>     },
>   ],
>
>   // Off by default: agent-to-agent messaging must be explicitly enabled + allowlisted.
>   tools: {
>     agentToAgent: {
>       enabled: false,
>       allow: ["home", "work"],
>     },
>   },
>
>   channels: {
>     whatsapp: {
>       accounts: {
>         personal: {
>           // Optional override. Default: ~/.openclaw/credentials/whatsapp/personal
>           // authDir: "~/.openclaw/credentials/whatsapp/personal",
>         },
>         biz: {
>           // Optional override. Default: ~/.openclaw/credentials/whatsapp/biz
>           // authDir: "~/.openclaw/credentials/whatsapp/biz",
>         },
>       },
>     },
>   },
> }
> ```

`~/.openclaw/openclaw.json`（JSON5）：

```js
{
  agents: {
    list: [
      {
        id: "home",
        default: true,
        name: "Home",
        workspace: "~/.openclaw/workspace-home",
        agentDir: "~/.openclaw/agents/home/agent",
      },
      {
        id: "work",
        name: "Work",
        workspace: "~/.openclaw/workspace-work",
        agentDir: "~/.openclaw/agents/work/agent",
      },
    ],
  },

  // 确定性路由：第一个命中胜出（按从最具体到最一般写）。
  bindings: [
    { agentId: "home", match: { channel: "whatsapp", accountId: "personal" } },
    { agentId: "work", match: { channel: "whatsapp", accountId: "biz" } },

    // 可选的按 peer 覆盖（比如把某个具体群发给 work agent）。
    {
      agentId: "work",
      match: {
        channel: "whatsapp",
        accountId: "personal",
        peer: { kind: "group", id: "1203630...@g.us" },
      },
    },
  ],

  // 默认关：agent-to-agent 消息要显式启用 + 加白名单。
  tools: {
    agentToAgent: {
      enabled: false,
      allow: ["home", "work"],
    },
  },

  channels: {
    whatsapp: {
      accounts: {
        personal: {
          // 可选覆盖。默认：~/.openclaw/credentials/whatsapp/personal
          // authDir: "~/.openclaw/credentials/whatsapp/personal",
        },
        biz: {
          // 可选覆盖。默认：~/.openclaw/credentials/whatsapp/biz
          // authDir: "~/.openclaw/credentials/whatsapp/biz",
        },
      },
    },
  },
}
```

---

> ## Common patterns

## 常见模式

> [标签页: WhatsApp daily + Telegram deep work]
>
> Split by channel: route WhatsApp to a fast everyday agent and Telegram to an Opus agent.

[标签页：WhatsApp 日常 + Telegram 深度工作]

按通道拆：WhatsApp 路由到快速日常 agent，Telegram 路由到 Opus agent。

> ```json5
> {
>   agents: {
>     list: [
>       {
>         id: "chat",
>         name: "Everyday",
>         workspace: "~/.openclaw/workspace-chat",
>         model: "anthropic/claude-sonnet-4-6",
>       },
>       {
>         id: "opus",
>         name: "Deep Work",
>         workspace: "~/.openclaw/workspace-opus",
>         model: "anthropic/claude-opus-4-6",
>       },
>     ],
>   },
>   bindings: [
>     { agentId: "chat", match: { channel: "whatsapp" } },
>     { agentId: "opus", match: { channel: "telegram" } },
>   ],
> }
> ```

```json5
{
  agents: {
    list: [
      {
        id: "chat",
        name: "Everyday",
        workspace: "~/.openclaw/workspace-chat",
        model: "anthropic/claude-sonnet-4-6",
      },
      {
        id: "opus",
        name: "Deep Work",
        workspace: "~/.openclaw/workspace-opus",
        model: "anthropic/claude-opus-4-6",
      },
    ],
  },
  bindings: [
    { agentId: "chat", match: { channel: "whatsapp" } },
    { agentId: "opus", match: { channel: "telegram" } },
  ],
}
```

> Notes:
>
> * If you have multiple accounts for a channel, add `accountId` to the binding (for example `{ channel: "whatsapp", accountId: "personal" }`).
> * To route a single DM/group to Opus while keeping the rest on chat, add a `match.peer` binding for that peer; peer matches always win over channel-wide rules.

说明：

- 一个通道有多个账号时，绑定里加 `accountId`（比如 `{ channel: "whatsapp", accountId: "personal" }`）。
- 想把某一个 DM / 群路由到 Opus、其他还留在 chat 上，给那个 peer 加一条 `match.peer` 绑定；peer 匹配始终优先于通道级规则。

> [标签页: Same channel, one peer to Opus]
>
> Keep WhatsApp on the fast agent, but route one DM to Opus:

[标签页：同通道、单一 peer 路由到 Opus]

WhatsApp 留在快速 agent 上，但把某一个 DM 路由到 Opus：

> ```json5
> {
>   agents: {
>     list: [
>       {
>         id: "chat",
>         name: "Everyday",
>         workspace: "~/.openclaw/workspace-chat",
>         model: "anthropic/claude-sonnet-4-6",
>       },
>       {
>         id: "opus",
>         name: "Deep Work",
>         workspace: "~/.openclaw/workspace-opus",
>         model: "anthropic/claude-opus-4-6",
>       },
>     ],
>   },
>   bindings: [
>     {
>       agentId: "opus",
>       match: { channel: "whatsapp", peer: { kind: "direct", id: "+15551234567" } },
>     },
>     { agentId: "chat", match: { channel: "whatsapp" } },
>   ],
> }
> ```

```json5
{
  agents: {
    list: [
      {
        id: "chat",
        name: "Everyday",
        workspace: "~/.openclaw/workspace-chat",
        model: "anthropic/claude-sonnet-4-6",
      },
      {
        id: "opus",
        name: "Deep Work",
        workspace: "~/.openclaw/workspace-opus",
        model: "anthropic/claude-opus-4-6",
      },
    ],
  },
  bindings: [
    {
      agentId: "opus",
      match: { channel: "whatsapp", peer: { kind: "direct", id: "+15551234567" } },
    },
    { agentId: "chat", match: { channel: "whatsapp" } },
  ],
}
```

> Peer bindings always win, so keep them above the channel-wide rule.

peer 绑定一定胜出，所以放在通道级规则上面。

> [标签页: Family agent bound to a WhatsApp group]
>
> Bind a dedicated family agent to a single WhatsApp group, with mention gating and a tighter tool policy:

[标签页：把家庭 agent 绑到一个 WhatsApp 群]

把一个专属的家庭 agent 绑到一个 WhatsApp 群上，开 @ 触发和更紧的工具策略：

> ```json5
> {
>   agents: {
>     list: [
>       {
>         id: "family",
>         name: "Family",
>         workspace: "~/.openclaw/workspace-family",
>         identity: { name: "Family Bot" },
>         groupChat: {
>           mentionPatterns: ["@family", "@familybot", "@Family Bot"],
>         },
>         sandbox: {
>           mode: "all",
>           scope: "agent",
>         },
>         tools: {
>           allow: [
>             "exec",
>             "read",
>             "sessions_list",
>             "sessions_history",
>             "sessions_send",
>             "sessions_spawn",
>             "session_status",
>           ],
>           deny: ["write", "edit", "apply_patch", "browser", "canvas", "nodes", "cron"],
>         },
>       },
>     ],
>   },
>   bindings: [
>     {
>       agentId: "family",
>       match: {
>         channel: "whatsapp",
>         peer: { kind: "group", id: "120363999999999999@g.us" },
>       },
>     },
>   ],
> }
> ```

```json5
{
  agents: {
    list: [
      {
        id: "family",
        name: "Family",
        workspace: "~/.openclaw/workspace-family",
        identity: { name: "Family Bot" },
        groupChat: {
          mentionPatterns: ["@family", "@familybot", "@Family Bot"],
        },
        sandbox: {
          mode: "all",
          scope: "agent",
        },
        tools: {
          allow: [
            "exec",
            "read",
            "sessions_list",
            "sessions_history",
            "sessions_send",
            "sessions_spawn",
            "session_status",
          ],
          deny: ["write", "edit", "apply_patch", "browser", "canvas", "nodes", "cron"],
        },
      },
    ],
  },
  bindings: [
    {
      agentId: "family",
      match: {
        channel: "whatsapp",
        peer: { kind: "group", id: "120363999999999999@g.us" },
      },
    },
  ],
}
```

> Notes:
>
> * Tool allow/deny lists are **tools**, not skills. If a skill needs to run a binary, ensure `exec` is allowed and the binary exists in the sandbox.
> * For stricter gating, set `agents.list[].groupChat.mentionPatterns` and keep group allowlists enabled for the channel.

说明：

- 工具 allow/deny 列表是**工具**，不是 skill。skill 要跑二进制时，确保允许 `exec` 且二进制在沙盒里存在。
- 想要更严格的触发，就设 `agents.list[].groupChat.mentionPatterns`，并保持该通道的群白名单开着。

---

> ## Per-agent sandbox and tool configuration

## 按 agent 的沙盒与工具配置

> Each agent can have its own sandbox and tool restrictions:

每个 agent 可以有自己的沙盒和工具限制：

> ```js
> {
>   agents: {
>     list: [
>       {
>         id: "personal",
>         workspace: "~/.openclaw/workspace-personal",
>         sandbox: {
>           mode: "off",  // No sandbox for personal agent
>         },
>         // No tool restrictions - all tools available
>       },
>       {
>         id: "family",
>         workspace: "~/.openclaw/workspace-family",
>         sandbox: {
>           mode: "all",     // Always sandboxed
>           scope: "agent",  // One container per agent
>           docker: {
>             // Optional one-time setup after container creation
>             setupCommand: "apt-get update && apt-get install -y git curl",
>           },
>         },
>         tools: {
>           allow: ["read"],                    // Only read tool
>           deny: ["exec", "write", "edit", "apply_patch"],    // Deny others
>         },
>       },
>     ],
>   },
> }
> ```

```js
{
  agents: {
    list: [
      {
        id: "personal",
        workspace: "~/.openclaw/workspace-personal",
        sandbox: {
          mode: "off",  // 个人 agent 不进沙盒
        },
        // 没有工具限制 —— 所有工具可用
      },
      {
        id: "family",
        workspace: "~/.openclaw/workspace-family",
        sandbox: {
          mode: "all",     // 始终沙盒化
          scope: "agent",  // 每个 agent 一个容器
          docker: {
            // 可选的、容器创建后的一次性 setup
            setupCommand: "apt-get update && apt-get install -y git curl",
          },
        },
        tools: {
          allow: ["read"],                    // 只允许 read 工具
          deny: ["exec", "write", "edit", "apply_patch"],    // 其他禁用
        },
      },
    ],
  },
}
```

> <Note>
>   `setupCommand` lives under `sandbox.docker` and runs once on container creation. Per-agent `sandbox.docker.*` overrides are ignored when the resolved scope is `"shared"`.
> </Note>

> **提示**：`setupCommand` 在 `sandbox.docker` 下，容器创建时跑一次。解析出的 scope 是 `"shared"` 时，per-agent 的 `sandbox.docker.*` 覆盖会被忽略。

> **Benefits:**
>
> * **Security isolation**: restrict tools for untrusted agents.
> * **Resource control**: sandbox specific agents while keeping others on host.
> * **Flexible policies**: different permissions per agent.

**好处**：

- **安全隔离**：给不受信的 agent 限制工具。
- **资源控制**：让特定 agent 进沙盒，其他留在宿主机。
- **灵活策略**：每个 agent 不同权限。

> <Note>
>   `tools.elevated` is **global** and sender-based; it is not configurable per agent. If you need per-agent boundaries, use `agents.list[].tools` to deny `exec`. For group targeting, use `agents.list[].groupChat.mentionPatterns` so @mentions map cleanly to the intended agent.
> </Note>

> **提示**：`tools.elevated` 是**全局**且基于发件人的，不能按 agent 配。需要按 agent 设边界时，用 `agents.list[].tools` 把 `exec` 设成 deny。要按群定位，用 `agents.list[].groupChat.mentionPatterns`，让 @ 干净地映射到目标 agent。

> See [Multi-agent sandbox and tools](/tools/multi-agent-sandbox-tools) for detailed examples.

详细例子见 [多 agent 沙盒与工具](/tools/multi-agent-sandbox-tools)。

---

> ## Related

## 相关

> * [ACP agents](/tools/acp-agents) — running external coding harnesses
> * [Channel routing](/channels/channel-routing) — how messages route to agents
> * [Presence](/concepts/presence) — agent presence and availability
> * [Session](/concepts/session) — session isolation and routing
> * [Sub-agents](/tools/subagents) — spawning background agent runs

- [ACP agents](/tools/acp-agents)：跑外部编码 harness
- [通道路由](/channels/channel-routing)：消息怎么路由到 agent
- [Presence](/concepts/presence)：agent 在线 / 可用状态
- [会话](/concepts/session)：会话隔离与路由
- [Sub-agents](/tools/subagents)：派生后台 agent 运行
