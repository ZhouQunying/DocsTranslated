# Context

> "Context" is **everything OpenClaw sends to the model for a run**. It is bounded by the model's **context window** (token limit).

"Context（上下文）"指的是**OpenClaw 在一次运行里送给模型的全部内容**。它的上限是模型的**上下文窗口**（token 上限）。

> Beginner mental model:
>
> * **System prompt** (OpenClaw-built): rules, tools, skills list, time/runtime, and injected workspace files.
> * **Conversation history**: your messages + the assistant's messages for this session.
> * **Tool calls/results + attachments**: command output, file reads, images/audio, etc.

入门心智模型：

- **系统提示词**（OpenClaw 构建）：规则、工具、skill 列表、时间 / 运行时信息、注入的工作区文件。
- **对话历史**：当前会话里你和 assistant 的消息。
- **工具调用 / 结果 + 附件**：命令输出、文件读取、图片 / 音频等。

> Context is *not the same thing* as "memory": memory can be stored on disk and reloaded later; context is what's inside the model's current window.

context *不等于* "memory"：memory 可以存到磁盘上、之后再加载；context 是当前在模型窗口里的内容。

---

> ## Quick start (inspect context)

## 快速上手（查看 context）

> * `/status` → quick "how full is my window?" view + session settings.
> * `/context list` → what's injected + rough sizes (per file + totals).
> * `/context detail` → deeper breakdown: per-file, per-tool schema sizes, per-skill entry sizes, and system prompt size.
> * `/context map` → WinDirStat-style treemap image of the current session's tracked context contributors.
> * `/usage tokens` → append per-reply usage footer to normal replies.
> * `/compact` → summarize older history into a compact entry to free window space.

- `/status` → 快速查看"窗口满了多少"+ 会话设置。
- `/context list` → 注入了什么 + 粗略大小（按文件 + 总计）。
- `/context detail` → 更深拆解：按文件、按工具 schema 大小、按 skill 条目大小、系统提示词大小。
- `/context map` → 当前会话里被追踪的 context 贡献者的 WinDirStat 风格 treemap 图。
- `/usage tokens` → 在普通回复后追加每条回复的用量页脚。
- `/compact` → 把较早的历史压缩成一条简洁条目，释放窗口空间。

> See also: [Slash commands](/tools/slash-commands), [Token use & costs](/reference/token-use), [Compaction](/concepts/compaction).

另见：[斜杠命令](/tools/slash-commands)、[Token 用量与成本](/reference/token-use)、[压缩](/concepts/compaction)。

---

> ## Example output

## 示例输出

> Values vary by model, provider, tool policy, and what's in your workspace.

数值会随模型、provider、工具策略和工作区内容而变化。

> ### `/context list`

### `/context list`

> ```
> 🧠 Context breakdown
> Workspace: <workspaceDir>
> Bootstrap max/file: 12,000 chars
> Sandbox: mode=non-main sandboxed=false
> System prompt (run): 38,412 chars (~9,603 tok) (Project Context 23,901 chars (~5,976 tok))
>
> Injected workspace files:
> - AGENTS.md: OK | raw 1,742 chars (~436 tok) | injected 1,742 chars (~436 tok)
> - SOUL.md: OK | raw 912 chars (~228 tok) | injected 912 chars (~228 tok)
> - TOOLS.md: TRUNCATED | raw 54,210 chars (~13,553 tok) | injected 20,962 chars (~5,241 tok)
> - IDENTITY.md: OK | raw 211 chars (~53 tok) | injected 211 chars (~53 tok)
> - USER.md: OK | raw 388 chars (~97 tok) | injected 388 chars (~97 tok)
> - HEARTBEAT.md: MISSING | raw 0 | injected 0
> - BOOTSTRAP.md: OK | raw 0 chars (~0 tok) | injected 0 chars (~0 tok)
>
> Skills list (system prompt text): 2,184 chars (~546 tok) (12 skills)
> Tools: read, edit, write, exec, process, browser, message, sessions_send, …
> Tool list (system prompt text): 1,032 chars (~258 tok)
> Tool schemas (JSON): 31,988 chars (~7,997 tok) (counts toward context; not shown as text)
> Tools: (same as above)
>
> Session tokens (cached): 14,250 total / ctx=32,000
> ```

```
🧠 Context breakdown
Workspace: <workspaceDir>
Bootstrap max/file: 12,000 chars
Sandbox: mode=non-main sandboxed=false
System prompt (run): 38,412 chars (~9,603 tok) (Project Context 23,901 chars (~5,976 tok))

Injected workspace files:
- AGENTS.md: OK | raw 1,742 chars (~436 tok) | injected 1,742 chars (~436 tok)
- SOUL.md: OK | raw 912 chars (~228 tok) | injected 912 chars (~228 tok)
- TOOLS.md: TRUNCATED | raw 54,210 chars (~13,553 tok) | injected 20,962 chars (~5,241 tok)
- IDENTITY.md: OK | raw 211 chars (~53 tok) | injected 211 chars (~53 tok)
- USER.md: OK | raw 388 chars (~97 tok) | injected 388 chars (~97 tok)
- HEARTBEAT.md: MISSING | raw 0 | injected 0
- BOOTSTRAP.md: OK | raw 0 chars (~0 tok) | injected 0 chars (~0 tok)

Skills list (system prompt text): 2,184 chars (~546 tok) (12 skills)
Tools: read, edit, write, exec, process, browser, message, sessions_send, …
Tool list (system prompt text): 1,032 chars (~258 tok)
Tool schemas (JSON): 31,988 chars (~7,997 tok) (counts toward context; not shown as text)
Tools: (same as above)

Session tokens (cached): 14,250 total / ctx=32,000
```

> ### `/context detail`

### `/context detail`

> ```
> 🧠 Context breakdown (detailed)
> …
> Top skills (prompt entry size):
> - frontend-design: 412 chars (~103 tok)
> - oracle: 401 chars (~101 tok)
> … (+10 more skills)
>
> Top tools (schema size):
> - browser: 9,812 chars (~2,453 tok)
> - exec: 6,240 chars (~1,560 tok)
> … (+N more tools)
> ```

```
🧠 Context breakdown (detailed)
…
Top skills (prompt entry size):
- frontend-design: 412 chars (~103 tok)
- oracle: 401 chars (~101 tok)
… (+10 more skills)

Top tools (schema size):
- browser: 9,812 chars (~2,453 tok)
- exec: 6,240 chars (~1,560 tok)
… (+N more tools)
```

> ### `/context map`

### `/context map`

> Sends an image generated from the latest cached run report. Before a normal message has produced a run report in the session, `/context map` returns an unavailable message instead of rendering an estimate. Rectangle area is proportional to tracked prompt characters:
>
> * injected workspace files
> * base system prompt text
> * skill prompt entries
> * tool JSON schemas

发送一张基于最近一次缓存运行报告生成的图。会话里普通消息还没产生过运行报告之前，`/context map` 会回一条"不可用"消息，不会按估算来渲染。矩形面积跟被追踪的提示词字符数成正比：

- 注入的工作区文件
- 基础系统提示词文本
- skill 提示词条目
- 工具 JSON schema

> `/context list`, `/context detail`, and `/context json` can still inspect an on-demand estimate when no run report is cached.

没有缓存运行报告时，`/context list`、`/context detail`、`/context json` 仍然可以按需查看估算值。

---

> ## What counts toward the context window

## 哪些算进上下文窗口

> Everything the model receives counts, including:
>
> * System prompt (all sections).
> * Conversation history.
> * Tool calls + tool results.
> * Attachments/transcripts (images/audio/files).
> * Compaction summaries and pruning artifacts.
> * Provider "wrappers" or hidden headers (not visible, still counted).

模型收到的全部内容都算进去，包括：

- 系统提示词（所有段）。
- 对话历史。
- 工具调用 + 工具结果。
- 附件 / 转写（图片 / 音频 / 文件）。
- 压缩摘要和裁剪产物。
- provider 的"包装"或隐藏头部（看不见，但照样计算）。

---

> ## How OpenClaw builds the system prompt

## OpenClaw 怎么构建系统提示词

> The system prompt is **OpenClaw-owned** and rebuilt each run. It includes:
>
> * Tool list + short descriptions.
> * Skills list (metadata only; see below).
> * Workspace location.
> * Time (UTC + converted user time if configured).
> * Runtime metadata (host/OS/model/thinking).
> * Injected workspace bootstrap files under **Project Context**.

系统提示词由 **OpenClaw 自己掌控**，每次运行重建。它包含：

- 工具列表 + 简短描述。
- skill 列表（只放元数据；见下）。
- 工作区位置。
- 时间（UTC + 配置后的用户时间）。
- 运行时元数据（host / OS / model / thinking）。
- 注入到 **Project Context** 下的工作区引导文件。

> Full breakdown: [System Prompt](/concepts/system-prompt).

完整拆解：[系统提示词](/concepts/system-prompt)。

---

> ## Injected workspace files (Project Context)

## 注入的工作区文件（Project Context）

> By default, OpenClaw injects a fixed set of workspace files (if present):
>
> * `AGENTS.md`
> * `SOUL.md`
> * `TOOLS.md`
> * `IDENTITY.md`
> * `USER.md`
> * `HEARTBEAT.md`
> * `BOOTSTRAP.md` (first-run only)

OpenClaw 默认注入一组固定的工作区文件（存在则注入）：

- `AGENTS.md`
- `SOUL.md`
- `TOOLS.md`
- `IDENTITY.md`
- `USER.md`
- `HEARTBEAT.md`
- `BOOTSTRAP.md`（仅首次运行）

> Large files are truncated per-file using `agents.defaults.bootstrapMaxChars` (default `12000` chars). OpenClaw also enforces a total bootstrap injection cap across files with `agents.defaults.bootstrapTotalMaxChars` (default `60000` chars). `/context` shows **raw vs injected** sizes and whether truncation happened.

大文件按 `agents.defaults.bootstrapMaxChars`（默认 `12000` 字符）按文件截断。OpenClaw 还跨文件总注入量上限 `agents.defaults.bootstrapTotalMaxChars`（默认 `60000` 字符）。`/context` 会显示**原始 vs 注入**的大小和是否截断。

> When truncation occurs, the runtime can inject an in-prompt warning block under Project Context. Configure this with `agents.defaults.bootstrapPromptTruncationWarning` (`off`, `once`, `always`; default `once`).

截断发生时，运行时可以在 Project Context 下注入一段提示词内警告块。用 `agents.defaults.bootstrapPromptTruncationWarning` 配置（`off`、`once`、`always`；默认 `once`）。

---

> ## Skills: injected vs loaded on-demand

## Skill：注入 vs 按需加载

> The system prompt includes a compact **skills list** (name + description + location). This list has real overhead.

系统提示词里有一份紧凑的 **skill 列表**（名字 + 描述 + 位置）。这份列表本身有实际开销。

> Skill instructions are *not* included by default. The model is expected to `read` the skill's `SKILL.md` **only when needed**.

skill 指令默认*不*包含。模型应该**只在需要时**通过 `read` 加载该 skill 的 `SKILL.md`。

---

> ## Tools: there are two costs

## 工具：有两种开销

> Tools affect context in two ways:
>
> 1. **Tool list text** in the system prompt (what you see as "Tooling").
> 2. **Tool schemas** (JSON). These are sent to the model so it can call tools. They count toward context even though you don't see them as plain text.

工具占用上下文的两种方式：

1. 系统提示词里的**工具列表文本**（你看到的 "Tooling"）。
2. **工具 schema**（JSON）。它们发给模型让它能调用工具。即使没作为纯文本显示，也照样算进上下文。

> `/context detail` breaks down the biggest tool schemas so you can see what dominates.

`/context detail` 会拆出最大的工具 schema，让你看到是哪些占主导。

---

> ## Commands, directives, and "inline shortcuts"

## 命令、指令和"内联快捷方式"

> Slash commands are handled by the Gateway. There are a few different behaviors:

斜杠命令由 Gateway 处理。有几种不同行为：

> * **Standalone commands**: a message that is only `/...` runs as a command.
> * **Directives**: `/think`, `/verbose`, `/trace`, `/reasoning`, `/elevated`, `/model`, `/queue` are stripped before the model sees the message.
>   * Directive-only messages persist session settings.
>   * Inline directives in a normal message act as per-message hints.
> * **Inline shortcuts** (allowlisted senders only): certain `/...` tokens inside a normal message can run immediately (example: "hey /status"), and are stripped before the model sees the remaining text.

- **独立命令**：消息只有 `/...` 时按命令执行。
- **指令（directive）**：`/think`、`/verbose`、`/trace`、`/reasoning`、`/elevated`、`/model`、`/queue` 在模型看到消息之前被剥掉。
  - 只含指令的消息会持久化会话设置。
  - 嵌在普通消息里的指令作为单条消息的临时提示。
- **内联快捷方式**（仅白名单发件人）：普通消息里某些 `/...` token 可以立即执行（例如 "hey /status"），剩余文本在交给模型前被剥掉。

> Details: [Slash commands](/tools/slash-commands).

细节：[斜杠命令](/tools/slash-commands)。

---

> ## Sessions, compaction, and pruning (what persists)

## 会话、压缩、裁剪（什么会持久化）

> What persists across messages depends on the mechanism:
>
> * **Normal history** persists in the session transcript until compacted/pruned by policy.
> * **Compaction** persists a summary into the transcript and keeps recent messages intact.
> * **Pruning** drops old tool results from the *in-memory* prompt to free context-window space, but does not rewrite the session transcript - the full history is still inspectable on disk.

跨消息的持久化看具体机制：

- **普通历史**保留在会话 transcript 里，直到按策略压缩 / 裁剪。
- **压缩**把摘要写进 transcript，保留最近的消息不动。
- **裁剪**把旧的工具结果从*内存*里的提示词中丢掉，释放上下文窗口空间，但不会改写会话 transcript —— 完整历史仍能在磁盘上查看。

> Docs: [Session](/concepts/session), [Compaction](/concepts/compaction), [Session pruning](/concepts/session-pruning).

文档：[会话](/concepts/session)、[压缩](/concepts/compaction)、[会话裁剪](/concepts/session-pruning)。

> By default, OpenClaw uses the built-in `legacy` context engine for assembly and compaction. If you install a plugin that provides `kind: "context-engine"` and select it with `plugins.slots.contextEngine`, OpenClaw delegates context assembly, `/compact`, and related subagent context lifecycle hooks to that engine instead. `ownsCompaction: false` does not auto-fallback to the legacy engine; the active engine must still implement `compact()` correctly. See [Context Engine](/concepts/context-engine) for the full pluggable interface, lifecycle hooks, and configuration.

OpenClaw 默认用内置的 `legacy` 上下文引擎做组装和压缩。如果你装了一个 `kind: "context-engine"` 的插件并通过 `plugins.slots.contextEngine` 选用它，OpenClaw 会把上下文组装、`/compact` 和相关 sub-agent 上下文生命周期钩子委托给那个引擎。`ownsCompaction: false` 不会自动回退到 legacy 引擎；当前生效的引擎仍然要正确实现 `compact()`。完整可插拔接口、生命周期钩子和配置见 [上下文引擎](/concepts/context-engine)。

---

> ## What `/context` actually reports

## `/context` 实际报告什么

> `/context` prefers the latest **run-built** system prompt report when available:
>
> * `System prompt (run)` = captured from the last embedded (tool-capable) run and persisted in the session store.
> * `System prompt (estimate)` = computed on the fly when no run report exists (or when running via a CLI backend that doesn't generate the report).

`/context` 在可用时优先用最近的**运行构建**系统提示词报告：

- `System prompt (run)` = 从最近一次嵌入式（带工具）运行里捕获，持久化在会话存储里。
- `System prompt (estimate)` = 没有运行报告时（或者通过不生成报告的 CLI 后端运行时）现场计算的估算。

> Either way, it reports sizes and top contributors; it does **not** dump the full system prompt or tool schemas.

无论哪种，它都报告大小和主要贡献者；**不会**把完整系统提示词或工具 schema 全部倒出来。

---

> ## Related

## 相关

> <CardGroup cols={2}>
>   <Card title="Context engine" href="/concepts/context-engine" icon="puzzle-piece">
>     Custom context injection via plugins.
>   </Card>
>
>   <Card title="Compaction" href="/concepts/compaction" icon="compress">
>     Summarizing long conversations to keep them inside the model window.
>   </Card>
>
>   <Card title="System prompt" href="/concepts/system-prompt" icon="message-lines">
>     How the system prompt is built and what it injects each turn.
>   </Card>
>
>   <Card title="Agent loop" href="/concepts/agent-loop" icon="arrows-rotate">
>     The full agent execution cycle from inbound message to final reply.
>   </Card>
> </CardGroup>

- [上下文引擎](/concepts/context-engine)：通过插件定制上下文注入。
- [压缩](/concepts/compaction)：长对话怎么被概括，从而塞进模型窗口。
- [系统提示词](/concepts/system-prompt)：系统提示词怎么构建、每轮注入什么。
- [Agent 循环](/concepts/agent-loop)：从消息进来到最终回复的完整 agent 执行周期。
