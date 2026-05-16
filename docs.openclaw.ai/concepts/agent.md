# Agent runtime

> OpenClaw runs a **single embedded agent runtime** - one agent process per Gateway, with its own workspace, bootstrap files, and session store. This page covers that runtime contract: what the workspace must contain, which files get injected, and how sessions bootstrap against it.

OpenClaw 跑的是一个**内嵌的单 agent 运行时** —— 每个 Gateway 一个 agent 进程，带自己的工作区、引导文件和会话存储。本页讲这个运行时的契约：工作区必须包含哪些内容、哪些文件会被注入、会话怎么针对它做引导。

---

> ## Workspace (required)

## 工作区（必需）

> OpenClaw uses a single agent workspace directory (`agents.defaults.workspace`) as the agent's **only** working directory (`cwd`) for tools and context.

OpenClaw 用一个 agent 工作区目录（`agents.defaults.workspace`）作为 agent 的**唯一**工作目录（`cwd`），工具和上下文都基于它。

> Recommended: use `openclaw setup` to create `~/.openclaw/openclaw.json` if missing and initialize the workspace files.

推荐：用 `openclaw setup` 在 `~/.openclaw/openclaw.json` 不存在时创建它，并初始化工作区文件。

> Full workspace layout + backup guide: [Agent workspace](/concepts/agent-workspace)

完整的工作区布局和备份指南：[Agent 工作区](/concepts/agent-workspace)

> If `agents.defaults.sandbox` is enabled, non-main sessions can override this with per-session workspaces under `agents.defaults.sandbox.workspaceRoot` (see [Gateway configuration](/gateway/configuration)).

启用 `agents.defaults.sandbox` 时，非 main 会话可以通过 `agents.defaults.sandbox.workspaceRoot` 下的每会话工作区覆盖这个默认值（见 [Gateway 配置](/gateway/configuration)）。

---

> ## Bootstrap files (injected)

## 引导文件（自动注入）

> Inside `agents.defaults.workspace`, OpenClaw expects these user-editable files:
>
> * `AGENTS.md` - operating instructions + "memory"
> * `SOUL.md` - persona, boundaries, tone
> * `TOOLS.md` - user-maintained tool notes (e.g. `imsg`, `sag`, conventions)
> * `BOOTSTRAP.md` - one-time first-run ritual (deleted after completion)
> * `IDENTITY.md` - agent name/vibe/emoji
> * `USER.md` - user profile + preferred address

`agents.defaults.workspace` 里 OpenClaw 预期这些用户可编辑的文件：

- `AGENTS.md`：操作说明 + "记忆"
- `SOUL.md`：人设、边界、语气
- `TOOLS.md`：用户维护的工具笔记（比如 `imsg`、`sag`、约定）
- `BOOTSTRAP.md`：一次性的首次运行仪式（完成后删掉）
- `IDENTITY.md`：agent 名字 / 气质 / emoji
- `USER.md`：用户画像 + 偏好的称呼方式

> On the first turn of a new session, OpenClaw injects the contents of these files into the system prompt's Project Context.

新会话的第一轮里，OpenClaw 把这些文件的内容注入到系统提示词的 Project Context 部分。

> Blank files are skipped. Large files are trimmed and truncated with a marker so prompts stay lean (read the file for full content).

空文件会跳过。大文件会被裁切并加截断标记，让提示词保持精简（要看完整内容直接读文件）。

> If a file is missing, OpenClaw injects a single "missing file" marker line (and `openclaw setup` will create a safe default template).

文件缺失时，OpenClaw 注入一行"缺失文件"标记（用 `openclaw setup` 可以生成一个安全的默认模板）。

> `BOOTSTRAP.md` is only created for a **brand new workspace** (no other bootstrap files present). While it is pending, OpenClaw keeps it in Project Context and adds system-prompt bootstrap guidance for the initial ritual instead of copying it into the user message. If you delete it after completing the ritual, it should not be recreated on later restarts.

`BOOTSTRAP.md` 只在**全新工作区**（没有其他引导文件）时创建。在它待处理期间，OpenClaw 把它保留在 Project Context 里，并在系统提示词里加初始仪式的引导，不把它复制到用户消息里。完成仪式后你把它删掉，之后重启时就不会再被创建。

> To disable bootstrap file creation entirely (for pre-seeded workspaces), set:
>
> ```json5
> { agents: { defaults: { skipBootstrap: true } } }
> ```

要彻底禁用引导文件创建（针对已预置好的工作区），设：

```json5
{ agents: { defaults: { skipBootstrap: true } } }
```

---

> ## Built-in tools

## 内置工具

> Core tools (read/exec/edit/write and related system tools) are always available, subject to tool policy. `apply_patch` is optional and gated by `tools.exec.applyPatch`. `TOOLS.md` does **not** control which tools exist; it's guidance for how *you* want them used.

核心工具（read / exec / edit / write 及相关系统工具）始终可用，受工具策略约束。`apply_patch` 是可选的，由 `tools.exec.applyPatch` 控制。`TOOLS.md` **不**决定哪些工具存在；它是给*你*用来表达"工具该怎么用"的指引。

---

> ## Skills

## Skill

> OpenClaw loads skills from these locations (highest precedence first):
>
> * Workspace: `<workspace>/skills`
> * Project agent skills: `<workspace>/.agents/skills`
> * Personal agent skills: `~/.agents/skills`
> * Managed/local: `~/.openclaw/skills`
> * Bundled (shipped with the install)
> * Extra skill folders: `skills.load.extraDirs`

OpenClaw 从下列位置加载 skill（优先级从高到低）：

- 工作区：`<workspace>/skills`
- 项目 agent skill：`<workspace>/.agents/skills`
- 个人 agent skill：`~/.agents/skills`
- managed / local：`~/.openclaw/skills`
- bundled（随安装包发布）
- 额外 skill 目录：`skills.load.extraDirs`

> Skills can be gated by config/env (see `skills` in [Gateway configuration](/gateway/configuration)).

skill 可以通过配置 / 环境变量限制（见 [Gateway 配置](/gateway/configuration) 里的 `skills`）。

---

> ## Runtime boundaries

## 运行时边界

> The embedded agent runtime is built on the Pi agent core (models, tools, and prompt pipeline). Session management, discovery, tool wiring, and channel delivery are OpenClaw-owned layers on top of that core.

内嵌 agent 运行时基于 Pi agent core（模型、工具、提示词管道）构建。会话管理、发现、工具接线、通道投递这些是 OpenClaw 自己在 Pi core 之上的封装层。

---

> ## Sessions

## 会话

> Session transcripts are stored as JSONL at:
>
> * `~/.openclaw/agents/<agentId>/sessions/<SessionId>.jsonl`

会话对话以 JSONL 形式存放在：

- `~/.openclaw/agents/<agentId>/sessions/<SessionId>.jsonl`

> The session ID is stable and chosen by OpenClaw.
> Legacy session folders from other tools are not read.

session ID 是稳定的，由 OpenClaw 自己分配。
其他工具留下的旧版会话目录不会被读取。

---

> ## Steering while streaming

## 流式过程中的转向（steering）

> Inbound prompts that arrive mid-run are steered into the current run by default.
> Steering is delivered **after the current assistant turn finishes executing its tool calls**, before the next LLM call, and no longer skips remaining tool calls from the current assistant message.

运行中途到达的 prompt 默认会被转向到当前运行中。
转向**在当前 assistant 轮次跑完它的工具调用之后**派发，赶在下一次 LLM 调用之前；不再跳过当前 assistant 消息里剩下的工具调用。

> `/queue steer` is the default active-run behavior. `/queue followup` and `/queue collect` make messages wait for a later turn instead of steering. `/queue interrupt` aborts the active run instead. See [Queue](/concepts/queue) and [Steering queue](/concepts/queue-steering) for queue and boundary behavior.

`/queue steer` 是活跃运行的默认行为。`/queue followup` 和 `/queue collect` 让消息等到后续轮次，不做转向。`/queue interrupt` 直接中止当前运行。队列和边界行为见 [队列](/concepts/queue) 和 [转向队列](/concepts/queue-steering)。

> Block streaming sends completed assistant blocks as soon as they finish; it is **off by default** (`agents.defaults.blockStreamingDefault: "off"`).
> Tune the boundary via `agents.defaults.blockStreamingBreak` (`text_end` vs `message_end`; defaults to text\_end).
> Control soft block chunking with `agents.defaults.blockStreamingChunk` (defaults to 800-1200 chars; prefers paragraph breaks, then newlines; sentences last).
> Coalesce streamed chunks with `agents.defaults.blockStreamingCoalesce` to reduce single-line spam (idle-based merging before send). Non-Telegram channels require explicit `*.blockStreaming: true` to enable block replies.
> Verbose tool summaries are emitted at tool start (no debounce); Control UI streams tool output via agent events when available.
> More details: [Streaming + chunking](/concepts/streaming).

block 流式在 assistant block 完成时立刻发出去；它**默认关闭**（`agents.defaults.blockStreamingDefault: "off"`）。
通过 `agents.defaults.blockStreamingBreak` 调边界（`text_end` 还是 `message_end`；默认 `text_end`）。
通过 `agents.defaults.blockStreamingChunk` 控制软切块（默认 800-1200 字符；优先按段落分，再按换行分，最后才按句子分）。
通过 `agents.defaults.blockStreamingCoalesce` 合并流式分片，减少单行刷屏（发送前按空闲合并）。非 Telegram 通道需要显式设 `*.blockStreaming: true` 才会启用 block 回复。
工具开始时立刻发出详细工具摘要（不做防抖）；Control UI 在可用时通过 agent 事件流式接收工具输出。
更多细节：[流式 + 分片](/concepts/streaming)。

---

> ## Model refs

## 模型引用

> Model refs in config (for example `agents.defaults.model` and `agents.defaults.models`) are parsed by splitting on the **first** `/`.

配置里的模型引用（比如 `agents.defaults.model` 和 `agents.defaults.models`）按**第一个** `/` 切分。

> * Use `provider/model` when configuring models.
> * If the model ID itself contains `/` (OpenRouter-style), include the provider prefix (example: `openrouter/moonshotai/kimi-k2`).
> * If you omit the provider, OpenClaw tries an alias first, then a unique configured-provider match for that exact model id, and only then falls back to the configured default provider. If that provider no longer exposes the configured default model, OpenClaw falls back to the first configured provider/model instead of surfacing a stale removed-provider default.

- 配置模型时用 `provider/model`。
- 如果模型 ID 本身含 `/`（OpenRouter 风格），把 provider 前缀写上（例如 `openrouter/moonshotai/kimi-k2`）。
- 省略 provider 时，OpenClaw 先试 alias，然后试该 model id 在已配置 provider 里的唯一匹配，最后才回退到配置的默认 provider。如果那个 provider 已经不再暴露配置的默认 model，OpenClaw 会回退到第一个已配置的 provider/model，而不是把过期的、provider 已被删的默认值暴露出来。

---

> ## Configuration (minimal)

## 配置（最小集）

> At minimum, set:
>
> * `agents.defaults.workspace`
> * `channels.whatsapp.allowFrom` (strongly recommended)

至少设：

- `agents.defaults.workspace`
- `channels.whatsapp.allowFrom`（强烈推荐）

---

> *Next: [Group Chats](/channels/group-messages)* 🦞

*下一步：[群聊](/channels/group-messages)* 🦞

---

> ## Related

## 相关

> * [Agent workspace](/concepts/agent-workspace)
> * [Multi-agent routing](/concepts/multi-agent)
> * [Session management](/concepts/session)

- [Agent 工作区](/concepts/agent-workspace)
- [多 agent 路由](/concepts/multi-agent)
- [会话管理](/concepts/session)
