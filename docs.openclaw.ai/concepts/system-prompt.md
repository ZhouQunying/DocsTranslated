# System prompt（系统提示词）

> OpenClaw builds a custom system prompt for every agent run. The prompt is **OpenClaw-owned** and does not use the pi-coding-agent default prompt.

OpenClaw 会为每次 Agent 运行单独构建一份系统提示词（system prompt）。这份提示词**由 OpenClaw 全权掌控**，不使用 pi-coding-agent 的默认提示词。

> The prompt is assembled by OpenClaw and injected into each agent run.

提示词由 OpenClaw 拼装好后，注入到每次 Agent 运行中。

> Prompt assembly has three layers:
>
> * `buildAgentSystemPrompt` renders the prompt from explicit inputs. It should stay a pure renderer and should not read global config directly.
> * `resolveAgentSystemPromptConfig` resolves config-backed prompt knobs such as owner display, TTS hints, model aliases, memory citation mode, and sub-agent delegation mode for a specific agent.
> * Runtime adapters (embedded, CLI, command/export previews, compaction) gather live facts such as tools, sandbox state, channel capabilities, context files, and provider prompt contributions, then call the configured prompt facade.

提示词的组装分为三层：

- `buildAgentSystemPrompt`：根据明确传入的参数来生成提示词。它只负责"渲染"，不应该自己去读全局配置。
- `resolveAgentSystemPromptConfig`：从配置中解析出各种可调节项——比如是否显示 owner 信息、TTS（语音合成）提示、模型别名、记忆引用方式、以及某个 Agent 的子 Agent 委派模式。
- 运行时适配器（嵌入式、CLI、命令/导出预览、上下文压缩等场景）：负责收集实时信息——可用工具、沙盒状态、通道能力、上下文文件、以及 Provider 提供的提示词片段——然后调用统一的提示词生成入口。

> This keeps exported/debug prompt surfaces aligned with live runs without turning every runtime-specific detail into one monolithic builder.

这种分层设计保证了导出/调试时看到的提示词与实际运行时一致，又不必把所有运行时细节都塞进一个庞大的构建器里。

> Provider plugins can contribute cache-aware prompt guidance without replacing the full OpenClaw-owned prompt. The provider runtime can:
>
> * replace a small set of named core sections (`interaction_style`, `tool_call_style`, `execution_bias`)
> * inject a **stable prefix** above the prompt cache boundary
> * inject a **dynamic suffix** below the prompt cache boundary

Provider 插件可以提供自己的提示词片段（且能配合提示词缓存机制），而不必整段替换 OpenClaw 的提示词。Provider 运行时可以：

- 替换少量命名的核心段落（`interaction_style`、`tool_call_style`、`execution_bias`）
- 在提示词缓存边界**之上**注入**稳定前缀**（不常变化的内容）
- 在提示词缓存边界**之下**注入**动态后缀**（随运行变化的内容）

> Use provider-owned contributions for model-family-specific tuning. Keep legacy `before_prompt_build` prompt mutation for compatibility or truly global prompt changes, not normal provider behavior.

如果要针对特定模型系列做调优，用 Provider 自己的提示词片段。旧版的 `before_prompt_build` 提示词改写机制应该只用于兼容性需求或真正全局性的提示词变更，不要在日常 Provider 行为中使用。

> The OpenAI GPT-5 family overlay keeps the core execution rule small and adds model-specific guidance for persona latching, concise output, tool discipline, parallel lookup, deliverable coverage, verification, missing context, and terminal-tool hygiene.

OpenAI GPT-5 系列的覆盖层（overlay）将核心执行规则保持精简，另外针对该模型补充了专项指引：角色设定的持续维持、输出简洁性、工具调用规范、并行查询、交付物完整性、结果校验、上下文缺失处理、终端工具的规范使用等。

---

> ## Structure

## 结构

> The prompt is intentionally compact and uses fixed sections:

提示词刻意保持紧凑，采用固定的段落结构：

> * **Tooling**: structured-tool source-of-truth reminder plus runtime tool-use guidance.
> * **Execution Bias**: compact follow-through guidance: act in-turn on actionable requests, continue until done or blocked, recover from weak tool results, check mutable state live, and verify before finalizing.
> * **Safety**: short guardrail reminder to avoid power-seeking behavior or bypassing oversight.
> * **Skills** (when available): tells the model how to load skill instructions on demand.
> * **OpenClaw Control**: tells the model to prefer the `gateway` tool for config/restart work and to avoid inventing CLI commands.
> * **OpenClaw Self-Update**: how to inspect config safely with `config.schema.lookup`, patch config with `config.patch`, replace the full config with `config.apply`, and run `update.run` only on explicit user request. The owner-only `gateway` tool also refuses to rewrite `tools.exec.ask` / `tools.exec.security`, including legacy `tools.bash.*` aliases that normalize to those protected exec paths.
> * **Workspace**: working directory (`agents.defaults.workspace`).
> * **Documentation**: local path to OpenClaw docs/source and when to read them.
> * **Workspace Files (injected)**: indicates bootstrap files are included below.
> * **Sandbox** (when enabled): indicates sandboxed runtime, sandbox paths, and whether elevated exec is available.
> * **Current Date & Time**: time zone only (cache-stable; the live clock comes from `session_status`).
> * **Assistant Output Directives**: compact attachment, voice-note, and reply tag syntax.
> * **Heartbeats**: heartbeat prompt and ack behavior, when heartbeats are enabled for the default agent.
> * **Runtime**: host, OS, node, model, repo root (when detected), thinking level (one line).
> * **Reasoning**: current visibility level + /reasoning toggle hint.

- **Tooling（工具）**：提醒模型以结构化工具描述为唯一可信来源，并给出运行时工具使用指引。
- **Execution Bias（执行倾向）**：简短的行动风格指引——能在当轮完成的事就当轮做、持续执行直到完成或遇阻、工具返回结果不理想时要设法补救、对可能变化的状态要实时核查、在最终提交前要做校验。
- **Safety（安全）**：简短的安全红线提醒，避免模型出现追求权力或绕过监督的行为。
- **Skills（技能）**（如有可用技能）：告诉模型如何按需加载技能指令。
- **OpenClaw Control（OpenClaw 控制）**：告诉模型在做配置/重启等管理工作时优先使用 `gateway` 工具，不要自行编造 CLI 命令。
- **OpenClaw Self-Update（OpenClaw 自更新）**：说明如何用 `config.schema.lookup` 安全查看配置、用 `config.patch` 局部修改配置、用 `config.apply` 整体替换配置、以及只有用户明确要求时才执行 `update.run`。此外，仅限 owner 使用的 `gateway` 工具会拒绝改写 `tools.exec.ask` / `tools.exec.security`，包括会自动映射到这些受保护路径的旧版别名 `tools.bash.*`。
- **Workspace（工作区）**：当前工作目录（`agents.defaults.workspace`）。
- **Documentation（文档）**：本地 OpenClaw 文档/源码的路径，以及何时应该去查阅。
- **Workspace Files (injected)（注入的工作区文件）**：标识引导文件已包含在下方。
- **Sandbox（沙盒）**（启用时）：标识当前处于沙盒运行时、沙盒路径、以及是否支持提权执行。
- **Current Date & Time（当前日期与时间）**：只包含时区信息（保持缓存稳定；实时时钟通过 `session_status` 获取）。
- **Assistant Output Directives（助手输出指令）**：附件、语音消息、回复标签等的简洁语法说明。
- **Heartbeats（心跳）**：当默认 Agent 启用心跳功能时，包含心跳提示词和应答行为说明。
- **Runtime（运行时信息）**：主机、操作系统、Node 版本、模型、仓库根路径（如检测到）、思考等级（一行信息）。
- **Reasoning（推理）**：当前推理可见性等级 + `/reasoning` 切换提示。

> OpenClaw keeps large stable content, including **Project Context**, above the internal prompt cache boundary. Volatile channel/session sections such as Control UI embed guidance, **Messaging**, **Voice**, **Group Chat Context**, **Reactions**, **Heartbeats**, and **Runtime** are appended below that boundary so local backends with prefix caches can reuse the stable workspace prefix across channel turns. Tool descriptions should likewise avoid embedding current channel names when the accepted schema already carries that runtime detail.

OpenClaw 将大块稳定内容（包括 **Project Context / 项目上下文**）放在内部提示词缓存边界**之上**。而容易变化的通道/会话相关段落——如 Control UI 嵌入指引、**Messaging（消息）**、**Voice（语音）**、**Group Chat Context（群聊上下文）**、**Reactions（表情回应）**、**Heartbeats（心跳）**、**Runtime（运行时）**——则追加到缓存边界**之下**。这样，支持前缀缓存的本地后端就可以跨不同通道的轮次复用稳定的工作区前缀。同理，工具描述也不应嵌入当前通道名等运行时细节——这些信息已经由 schema 传入了。

> The Tooling section also includes runtime guidance for long-running work:
>
> * use cron for future follow-up (`check back later`, reminders, recurring work) instead of `exec` sleep loops, `yieldMs` delay tricks, or repeated `process` polling
> * use `exec` / `process` only for commands that start now and continue running in the background
> * when automatic completion wake is enabled, start the command once and rely on the push-based wake path when it emits output or fails
> * use `process` for logs, status, input, or intervention when you need to inspect a running command
> * if the task is larger, prefer `sessions_spawn`; sub-agent completion is push-based and auto-announces back to the requester
> * do not poll `subagents list` / `sessions_list` in a loop just to wait for completion

Tooling 段还包含关于长时间运行任务的指引：

- 需要未来跟进的工作（"晚点再看"、提醒、定时任务）应使用 cron，不要用 `exec` 配合 sleep 循环、`yieldMs` 延时技巧或反复调用 `process` 轮询。
- `exec` / `process` 只用于"现在启动、然后在后台持续运行"的命令。
- 启用了自动完成唤醒（automatic completion wake）时，命令只需启动一次，等它产生输出或失败时会通过推送机制自动唤醒 Agent。
- 需要查看正在运行的命令的日志、状态、输入或对其进行干预时，使用 `process`。
- 任务规模更大时，优先使用 `sessions_spawn`（生成子 Agent 会话）；子 Agent 完成后会通过推送机制自动通知发起者。
- 不要为了等待完成而循环轮询 `subagents list` / `sessions_list`。

> `agents.defaults.subagents.delegationMode` can strengthen this guidance. The default `suggest` mode keeps the baseline nudge. `prefer` adds a dedicated **Sub-Agent Delegation** section telling the main agent to act as a responsive coordinator and push anything more involved than a direct reply through `sessions_spawn`. This is prompt-only; tool policy still controls whether `sessions_spawn` is available.

`agents.defaults.subagents.delegationMode` 可以加强上述指引。默认的 `suggest` 模式只做温和的提示。设为 `prefer` 时会额外增加一段 **Sub-Agent Delegation（子 Agent 委派）** 指引，告诉主 Agent 充当响应式协调者——凡是超出简单直接回复的工作，都通过 `sessions_spawn` 交给子 Agent 处理。这只是提示词层面的引导，`sessions_spawn` 是否真正可用仍由工具策略（tool policy）决定。

> When the experimental `update_plan` tool is enabled, Tooling also tells the model to use it only for non-trivial multi-step work, keep exactly one `in_progress` step, and avoid repeating the whole plan after each update.

当实验性的 `update_plan` 工具启用时，Tooling 段还会告诉模型：只在较复杂的多步骤任务中使用它，始终只保持一个 `in_progress`（进行中）步骤，且每次更新后不要重复输出整个计划。

> Safety guardrails in the system prompt are advisory. They guide model behavior but do not enforce policy. Use tool policy, exec approvals, sandboxing, and channel allowlists for hard enforcement; operators can disable these by design.

系统提示词中的安全护栏属于"建议性"的——它们引导模型行为，但不具备强制约束力。如需硬性约束，应使用工具策略（tool policy）、执行审批（exec approvals）、沙盒（sandboxing）和通道白名单（channel allowlists）。运维人员可以按需关闭这些安全护栏，这是设计上允许的。

> On channels with native approval cards/buttons, the runtime prompt now tells the agent to rely on that native approval UI first. It should only include a manual `/approve` command when the tool result says chat approvals are unavailable or manual approval is the only path.

在支持原生审批卡片/按钮的通道上，运行时提示词会让 Agent 优先使用原生的审批 UI。只有当工具返回结果表明"聊天审批不可用"或"手动审批是唯一途径"时，才提供手动 `/approve` 命令。

---

> ## Prompt modes

## 提示词模式

> OpenClaw can render smaller system prompts for sub-agents. The runtime sets a `promptMode` for each run (not a user-facing config):

OpenClaw 可以为子 Agent 生成更精简的系统提示词。运行时会为每次运行设置一个 `promptMode`（这不是用户可配置的选项）：

> * `full` (default): includes all sections above.
> * `minimal`: used for sub-agents; omits **Memory Recall**, **OpenClaw Self-Update**, **Model Aliases**, **User Identity**, **Assistant Output Directives**, **Messaging**, **Silent Replies**, and **Heartbeats**. Tooling, **Safety**, **Skills** when supplied, Workspace, Sandbox, Current Date & Time (when known), Runtime, and injected context stay available.
> * `none`: returns only the base identity line.

- `full`（默认）：包含上面所有段落。
- `minimal`：用于子 Agent；会省略 **Memory Recall（记忆召回）**、**OpenClaw Self-Update（自更新）**、**Model Aliases（模型别名）**、**User Identity（用户身份）**、**Assistant Output Directives（助手输出指令）**、**Messaging（消息）**、**Silent Replies（静默回复）** 和 **Heartbeats（心跳）**。但 Tooling（工具）、**Safety（安全）**、**Skills（技能）**（如有）、Workspace（工作区）、Sandbox（沙盒）、Current Date & Time（当前日期与时间，已知时）、Runtime（运行时）以及注入的上下文仍然可用。
- `none`：只返回最基本的身份标识那一行。

> When `promptMode=minimal`, extra injected prompts are labeled **Subagent Context** instead of **Group Chat Context**.

当 `promptMode=minimal` 时，额外注入的提示词会被标记为 **Subagent Context（子 Agent 上下文）**，而不是 **Group Chat Context（群聊上下文）**。

> For channel auto-reply runs, OpenClaw omits the generic **Silent Replies** section when direct, group, or message-tool-only context owns the visible-reply contract. Only old automatic group/channel mode should show `NO_REPLY`; direct chats and message-tool-only replies do not receive silent-token guidance.

在通道自动回复场景下，当私聊、群聊或仅通过消息工具回复的上下文已经约定了"可见回复"的规则时，OpenClaw 会省略通用的 **Silent Replies（静默回复）** 段。只有旧版的自动群/频道模式才会显示 `NO_REPLY` 标记；私聊和仅通过消息工具的回复不会收到静默令牌（silent-token）指引。

---

> ## Prompt snapshots

## 提示词快照

> OpenClaw keeps committed prompt snapshots for the Codex runtime happy path under `test/fixtures/agents/prompt-snapshots/codex-runtime-happy-path/`. They render selected app-server thread/turn params plus a reconstructed model-bound prompt layer stack for Telegram direct, Discord group, and heartbeat turns. That stack includes a pinned Codex `gpt-5.5` model prompt fixture generated from Codex's model catalog/cache shape, the Codex happy-path permission developer text, OpenClaw developer instructions, turn-scoped collaboration-mode instructions when OpenClaw provides them, user turn input, and references to the dynamic tool specs.

OpenClaw 在代码库中保存了 Codex 运行时正常流程（happy path）的提示词快照，位于 `test/fixtures/agents/prompt-snapshots/codex-runtime-happy-path/` 目录下。这些快照包含了选定的 app-server 线程/轮次参数，以及为 Telegram 私聊、Discord 群组、心跳这三类轮次重建的模型绑定提示词层级栈。该层级栈包含：从 Codex 模型目录/缓存结构生成的固定版本 Codex `gpt-5.5` 模型提示词测试数据（fixture）、Codex 正常流程的权限开发者文本、OpenClaw 开发者指令、OpenClaw 提供时的按轮次生效的协作模式指令、用户轮次输入、以及对动态工具规格的引用。

> Refresh the pinned Codex model prompt fixture with `pnpm prompt:snapshots:sync-codex-model`. By default, the script looks for Codex's runtime cache at `$CODEX_HOME/models_cache.json`, then `~/.codex/models_cache.json`, and only then falls back to the maintainer Codex checkout convention at `~/code/codex/codex-rs/models-manager/models.json`. If none of those sources exist, the command exits without changing the committed fixture. Pass `--catalog <path>` to refresh from a specific `models_cache.json` or `models.json` file.

运行 `pnpm prompt:snapshots:sync-codex-model` 可以刷新固定版本的 Codex 模型提示词 fixture。脚本默认按以下顺序查找 Codex 运行时缓存：`$CODEX_HOME/models_cache.json` → `~/.codex/models_cache.json` → 最后回退到维护者的 Codex 代码检出路径 `~/code/codex/codex-rs/models-manager/models.json`。如果这些文件都不存在，命令会直接退出且不修改已提交的 fixture。传 `--catalog <path>` 参数可以从指定的 `models_cache.json` 或 `models.json` 文件刷新。

> These snapshots are still not a byte-for-byte raw OpenAI request capture. Codex can add runtime-owned workspace context such as `AGENTS.md`, environment context, memories, app/plugin instructions, and built-in Default collaboration-mode instructions inside the Codex runtime after OpenClaw sends thread and turn params.

这些快照并非逐字节的原始 OpenAI 请求抓包。在 OpenClaw 发出线程/轮次参数之后，Codex 运行时还会在内部添加它自己管理的工作区上下文——包括 `AGENTS.md`、环境上下文、记忆、应用/插件指令，以及内置的默认协作模式指令。

> Regenerate them with `pnpm prompt:snapshots:gen` and verify drift with `pnpm prompt:snapshots:check`. CI runs the drift check in the additional boundary shard so prompt changes and snapshot updates stay attached to the same PR.

用 `pnpm prompt:snapshots:gen` 重新生成快照，用 `pnpm prompt:snapshots:check` 检查是否存在偏差。CI 在额外的边界分片（boundary shard）中运行偏差检查，确保提示词改动和快照更新始终出现在同一个 PR 中。

---

> ## Workspace bootstrap injection

## 工作区引导文件注入

> Bootstrap files are trimmed and appended under **Project Context** so the model sees identity and profile context without needing explicit reads:

引导文件（bootstrap files）会被裁剪后追加到 **Project Context（项目上下文）** 中，这样模型可以直接看到身份和配置信息，无需手动读取文件：

> * `AGENTS.md`
> * `SOUL.md`
> * `TOOLS.md`
> * `IDENTITY.md`
> * `USER.md`
> * `HEARTBEAT.md`
> * `BOOTSTRAP.md` (only on brand-new workspaces)
> * `MEMORY.md` when present

- `AGENTS.md`
- `SOUL.md`
- `TOOLS.md`
- `IDENTITY.md`
- `USER.md`
- `HEARTBEAT.md`
- `BOOTSTRAP.md`（仅在全新工作区中存在）
- `MEMORY.md`（如果存在）

> All of these files are **injected into the context window** on every turn unless a file-specific gate applies. `HEARTBEAT.md` is omitted on normal runs when heartbeats are disabled for the default agent or `agents.defaults.heartbeat.includeSystemPromptSection` is false. Keep injected files concise, especially `MEMORY.md`. `MEMORY.md` is intended to stay a curated long-term summary; detailed daily notes belong in `memory/*.md` where `memory_search` and `memory_get` can retrieve them on demand. Oversized `MEMORY.md` files increase prompt usage and can be partially injected because of the bootstrap file limits below.

以上所有文件在每一轮对话中都会**被注入到上下文窗口**，除非该文件有特定的过滤条件。当默认 Agent 关闭了心跳功能，或 `agents.defaults.heartbeat.includeSystemPromptSection` 设为 false 时，普通运行会跳过 `HEARTBEAT.md`。注入的文件应尽量简短，尤其是 `MEMORY.md`。`MEMORY.md` 应该保持为一份精心整理的长期摘要；详细的日常笔记应放在 `memory/*.md` 中，由 `memory_search` 和 `memory_get` 工具按需检索。`MEMORY.md` 过大会增加提示词开销，还可能因为下面提到的引导文件大小限制而只被部分注入。

> When a session runs on the native Codex harness, Codex loads `AGENTS.md` through its own project-doc discovery. OpenClaw still resolves the remaining bootstrap files and forwards them as Codex config instructions, so `SOUL.md`, `TOOLS.md`, `IDENTITY.md`, `USER.md`, `HEARTBEAT.md`, `BOOTSTRAP.md`, and `MEMORY.md` keep the same workspace-context role without duplicating `AGENTS.md`.

当会话运行在原生 Codex 运行环境上时，Codex 会通过自己的项目文档发现机制加载 `AGENTS.md`。OpenClaw 仍会解析其余的引导文件，并将它们作为 Codex 配置指令传递过去。因此 `SOUL.md`、`TOOLS.md`、`IDENTITY.md`、`USER.md`、`HEARTBEAT.md`、`BOOTSTRAP.md` 和 `MEMORY.md` 保持同样的工作区上下文角色，同时不会重复注入 `AGENTS.md`。

> **提示**：`memory/*.md` 日常文件**不是**常规引导 Project Context 的一部分。普通轮次下它们通过 `memory_search` 和 `memory_get` 工具按需访问，所以除非模型显式读取，否则不占用上下文窗口。仅 `/new` 和 `/reset` 轮次例外：运行时可以为这第一轮把最近的日常记忆作为一次性启动上下文预先注入。

> Large files are truncated with a marker. The max per-file size is controlled by `agents.defaults.bootstrapMaxChars` (default: 12000). Total injected bootstrap content across files is capped by `agents.defaults.bootstrapTotalMaxChars` (default: 60000). Missing files inject a short missing-file marker. When truncation occurs, OpenClaw can inject a concise system-prompt warning notice; control this with `agents.defaults.bootstrapPromptTruncationWarning` (`off`, `once`, `always`; default: `once`). Detailed raw/injected counts stay in diagnostics such as `/context`, `/status`, doctor, and logs.

过大的文件会被截断并附加截断标记。每个文件的最大字符数由 `agents.defaults.bootstrapMaxChars` 控制（默认 12000）。所有引导文件注入的总字符数上限由 `agents.defaults.bootstrapTotalMaxChars` 控制（默认 60000）。缺失的文件会注入一个简短的"文件缺失"标记。发生截断时，OpenClaw 可以在系统提示词中插入一条简短的警告通知；通过 `agents.defaults.bootstrapPromptTruncationWarning` 控制（可选值：`off`——关闭、`once`——仅一次、`always`——始终显示；默认 `once`）。详细的原始/注入字符数统计可在 `/context`、`/status`、doctor 诊断和日志中查看。

> For memory files, truncation is not data loss: the file remains intact on disk, but the model only sees the shortened injected copy until it reads or searches memory directly. If `MEMORY.md` is repeatedly truncated, distill it into a shorter durable summary and move detailed history into `memory/*.md`, or intentionally raise the bootstrap limits.

对于记忆文件，截断并不意味着数据丢失：文件在磁盘上仍然完好无损，只是模型在主动读取或搜索记忆之前只能看到截短后的注入版本。如果 `MEMORY.md` 反复被截断，建议将其精炼为更短的长期摘要，把详细历史移到 `memory/*.md` 中；或者刻意提高引导文件的大小限制。

> Sub-agent sessions only inject `AGENTS.md` and `TOOLS.md` (other bootstrap files are filtered out to keep the sub-agent context small).

子 Agent 会话只注入 `AGENTS.md` 和 `TOOLS.md`（其他引导文件会被过滤掉，以保持子 Agent 的上下文精简）。

> Internal hooks can intercept this step via `agent:bootstrap` to mutate or replace the injected bootstrap files (for example swapping `SOUL.md` for an alternate persona).

内部钩子（hooks）可以通过 `agent:bootstrap` 事件拦截这一步骤，对注入的引导文件进行修改或替换（例如将 `SOUL.md` 替换为另一个人设）。

> If you want to make the agent sound less generic, start with [SOUL.md Personality Guide](/concepts/soul).

想让 Agent 不那么"千篇一律"？从 [SOUL.md 人设指南](/concepts/soul) 开始。

> To inspect how much each injected file contributes (raw vs injected, truncation, plus tool schema overhead), use `/context list` or `/context detail`. See [Context](/concepts/context).

要查看每个注入文件占用了多少上下文（原始大小 vs 注入大小、截断情况、以及工具 schema 的额外开销），可使用 `/context list` 或 `/context detail` 命令。详见 [Context（上下文）](/concepts/context)。

---

> ## Time handling

## 时间处理

> The system prompt includes a dedicated **Current Date & Time** section when the user timezone is known. To keep the prompt cache-stable, it now only includes the **time zone** (no dynamic clock or time format).

当用户时区已知时，系统提示词中会包含一个专门的 **Current Date & Time（当前日期与时间）** 段。为了保持提示词缓存的稳定性，该段现在只包含**时区信息**（不包含动态时钟或时间格式）。

> Use `session_status` when the agent needs the current time; the status card includes a timestamp line. The same tool can optionally set a per-session model override (`model=default` clears it).

Agent 需要获取当前时间时，应使用 `session_status` 工具——返回的状态卡片中包含时间戳。该工具还可以为当前会话设置模型覆盖（传 `model=default` 可清除覆盖）。

> Configure with:
>
> * `agents.defaults.userTimezone`
> * `agents.defaults.timeFormat` (`auto` | `12` | `24`)

相关配置项：

- `agents.defaults.userTimezone`
- `agents.defaults.timeFormat`（可选值：`auto` | `12` | `24`）

> See [Date & Time](/date-time) for full behavior details.

完整的行为说明请参阅 [日期与时间](/date-time)。

---

> ## Skills

## 技能（Skills）

> When eligible skills exist, OpenClaw injects a compact **available skills list** (`formatSkillsForPrompt`) that includes the **file path** for each skill. The prompt instructs the model to use `read` to load the SKILL.md at the listed location (workspace, managed, or bundled). If no skills are eligible, the Skills section is omitted.

当存在可用的技能时，OpenClaw 会注入一份精简的**可用技能列表**（通过 `formatSkillsForPrompt` 生成），每个技能附带**文件路径**。提示词会指示模型使用 `read` 工具去加载对应路径（工作区内、托管目录或内置目录）的 SKILL.md 文件。如果没有可用技能，则省略 Skills 段。

> Eligibility includes skill metadata gates, runtime environment/config checks, and the effective agent skill allowlist when `agents.defaults.skills` or `agents.list[].skills` is configured.

技能是否"可用"取决于：技能元数据中的准入条件、运行时环境/配置检查，以及当配置了 `agents.defaults.skills` 或 `agents.list[].skills` 时生效的 Agent 技能白名单。

> Plugin-bundled skills are eligible only when their owning plugin is enabled. This lets tool plugins expose deeper operating guides without embedding all of that guidance directly in every tool description.

插件自带的技能只在其所属插件启用时才可用。这使得工具插件可以提供更深入的操作指南，而不必把所有指引都直接塞进每一条工具描述里。

> ```
> <available_skills>
>   <skill>
>     <name>...</name>
>     <description>...</description>
>     <location>...</location>
>   </skill>
> </available_skills>
> ```

```xml
<available_skills>
  <skill>
    <name>...</name>
    <description>...</description>
    <location>...</location>
  </skill>
</available_skills>
```

> This keeps the base prompt small while still enabling targeted skill usage.

这种方式既保持了基础提示词的精简，又能支持有针对性的技能调用。

> The skills list budget is owned by the skills subsystem:
>
> * Global default: `skills.limits.maxSkillsPromptChars`
> * Per-agent override: `agents.list[].skillsLimits.maxSkillsPromptChars`

技能列表的字符预算由技能子系统管理：

- 全局默认值：`skills.limits.maxSkillsPromptChars`
- 按 Agent 覆盖：`agents.list[].skillsLimits.maxSkillsPromptChars`

> Generic bounded runtime excerpts use a different surface:
>
> * `agents.defaults.contextLimits.*`
> * `agents.list[].contextLimits.*`

通用的运行时内容摘录使用另一套配置：

- `agents.defaults.contextLimits.*`
- `agents.list[].contextLimits.*`

> That split keeps skills sizing separate from runtime read/injection sizing such as `memory_get`, live tool results, and post-compaction AGENTS.md refreshes.

这种拆分使得技能的大小预算与运行时读取/注入的大小预算互不干扰——后者包括 `memory_get` 返回的内容、实时工具调用结果、上下文压缩后 AGENTS.md 的刷新等。

---

> ## Documentation

## 文档（Documentation）

> The system prompt includes a **Documentation** section. When local docs are available, it points to the local OpenClaw docs directory (`docs/` in a Git checkout or the bundled npm package docs). If local docs are unavailable, it falls back to [https://docs.openclaw.ai](https://docs.openclaw.ai).

系统提示词中包含一个 **Documentation（文档）** 段。当本地文档可用时，它会指向本地的 OpenClaw 文档目录（Git 检出中的 `docs/` 或 npm 包内置的文档）。如果本地文档不可用，则回退到在线文档 [https://docs.openclaw.ai](https://docs.openclaw.ai)。

> The same section also includes the OpenClaw source location. Git checkouts expose the local source root so the agent can inspect code directly. Package installs include the GitHub source URL and tell the agent to review source there whenever the docs are incomplete or stale. The prompt also notes the public docs mirror, community Discord, and ClawHub ([https://clawhub.ai](https://clawhub.ai)) for skills discovery. It tells the model to consult docs first for OpenClaw behavior, commands, configuration, or architecture, and to run `openclaw status` itself when possible (asking the user only when it lacks access). For configuration specifically, it points agents to the `gateway` tool action `config.schema.lookup` for exact field-level docs and constraints, then to `docs/gateway/configuration.md` and `docs/gateway/configuration-reference.md` for broader guidance.

同一段还包含 OpenClaw 源代码位置。通过 Git 检出安装时，会暴露本地源码根目录，让 Agent 可以直接查看代码。通过 npm 包安装时，则提供 GitHub 上的源码 URL，告诉 Agent 在文档不完整或过时时去那里查阅源码。提示词中还提到了公开文档镜像、社区 Discord，以及用于发现技能的 ClawHub（[https://clawhub.ai](https://clawhub.ai)）。它指示模型在查询 OpenClaw 行为、命令、配置或架构相关问题时**优先查阅文档**，并在可能时自行运行 `openclaw status`（仅在无法访问时才询问用户）。针对配置查询，它特别引导 Agent 使用 `gateway` 工具的 `config.schema.lookup` 操作来获取精确的字段级文档和约束条件，再参考 `docs/gateway/configuration.md` 和 `docs/gateway/configuration-reference.md` 获取更全面的指引。

---

> ## Related

## 相关文档

> * [Agent runtime](/concepts/agent)
> * [Agent workspace](/concepts/agent-workspace)
> * [Context engine](/concepts/context-engine)

- [Agent 运行时](/concepts/agent)
- [Agent 工作区](/concepts/agent-workspace)
- [上下文引擎](/concepts/context-engine)
