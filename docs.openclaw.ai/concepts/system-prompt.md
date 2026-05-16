# System prompt

> OpenClaw builds a custom system prompt for every agent run. The prompt is **OpenClaw-owned** and does not use the pi-coding-agent default prompt.

OpenClaw 给每次 agent 运行单独构建一份系统提示词。这份提示词**由 OpenClaw 自己掌控**，不用 pi-coding-agent 的默认提示词。

> The prompt is assembled by OpenClaw and injected into each agent run.

提示词由 OpenClaw 拼装，注入到每次 agent 运行里。

> Prompt assembly has three layers:
>
> * `buildAgentSystemPrompt` renders the prompt from explicit inputs. It should stay a pure renderer and should not read global config directly.
> * `resolveAgentSystemPromptConfig` resolves config-backed prompt knobs such as owner display, TTS hints, model aliases, memory citation mode, and sub-agent delegation mode for a specific agent.
> * Runtime adapters (embedded, CLI, command/export previews, compaction) gather live facts such as tools, sandbox state, channel capabilities, context files, and provider prompt contributions, then call the configured prompt facade.

提示词组装分三层：

- `buildAgentSystemPrompt` 从显式输入渲染提示词。它应该保持为纯渲染器，不直接读全局配置。
- `resolveAgentSystemPromptConfig` 解析配置里的提示词调参，比如 owner 显示、TTS 提示、model 别名、memory 引用模式、某个 agent 的 sub-agent 委派模式。
- 运行时适配器（嵌入式、CLI、命令 / export 预览、压缩）收集实时信息：工具、沙盒状态、通道能力、上下文文件、provider 的提示词贡献，然后调配置好的提示词 facade。

> This keeps exported/debug prompt surfaces aligned with live runs without turning every runtime-specific detail into one monolithic builder.

这样能保证导出 / 调试用的提示词面与实际运行保持一致，而不用把每个运行时特有的细节都塞进一个大单体 builder。

> Provider plugins can contribute cache-aware prompt guidance without replacing the full OpenClaw-owned prompt. The provider runtime can:
>
> * replace a small set of named core sections (`interaction_style`, `tool_call_style`, `execution_bias`)
> * inject a **stable prefix** above the prompt cache boundary
> * inject a **dynamic suffix** below the prompt cache boundary

provider 插件可以贡献缓存感知的提示词指引，不必整段替换 OpenClaw 自己的提示词。provider runtime 可以：

- 替换一小组命名的核心段（`interaction_style`、`tool_call_style`、`execution_bias`）
- 在提示词缓存边界**之上**注入**稳定前缀**
- 在提示词缓存边界**之下**注入**动态后缀**

> Use provider-owned contributions for model-family-specific tuning. Keep legacy `before_prompt_build` prompt mutation for compatibility or truly global prompt changes, not normal provider behavior.

针对某个模型家族的调优用 provider 自己的贡献。旧版 `before_prompt_build` 的提示词改写留给兼容性或真正全局的提示词变更，不要用在常规 provider 行为上。

> The OpenAI GPT-5 family overlay keeps the core execution rule small and adds model-specific guidance for persona latching, concise output, tool discipline, parallel lookup, deliverable coverage, verification, missing context, and terminal-tool hygiene.

OpenAI GPT-5 系列的 overlay 把核心执行规则保持得很小，再针对该模型加指引：persona 锁定、简洁输出、工具纪律、并行查询、交付覆盖、校验、上下文缺失处理、terminal 工具卫生。

---

> ## Structure

## 结构

> The prompt is intentionally compact and uses fixed sections:

提示词刻意紧凑，用固定的段落：

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

- **Tooling**：结构化工具的"权威源"提醒 + 运行时工具使用指引。
- **Execution Bias**：紧凑的执行风格指引：能当轮做的事就当轮做、做到完成或受阻为止、工具结果差时要恢复、可变状态要实时检查、定稿之前要核验。
- **Safety**：简短的护栏提醒，避免追逐权力或绕过监督。
- **Skills**（有 skill 时）：告诉模型怎么按需加载 skill 指令。
- **OpenClaw Control**：告诉模型做配置 / 重启相关工作时优先用 `gateway` 工具，不要编造 CLI 命令。
- **OpenClaw Self-Update**：怎么用 `config.schema.lookup` 安全查看配置、用 `config.patch` 打补丁、用 `config.apply` 整段替换、只有用户明确要求时才跑 `update.run`。owner-only 的 `gateway` 工具也拒绝改写 `tools.exec.ask` / `tools.exec.security`，包括会归一化到这些受保护 exec 路径的旧版 `tools.bash.*` 别名。
- **Workspace**：工作目录（`agents.defaults.workspace`）。
- **Documentation**：本地 OpenClaw 文档 / 源代码路径，以及何时该读。
- **Workspace Files (injected)**：表明引导文件已包含在下面。
- **Sandbox**（启用时）：表明这是沙盒运行时、沙盒路径、是否有 elevated exec。
- **Current Date & Time**：只放时区（缓存稳定；实时时钟来自 `session_status`）。
- **Assistant Output Directives**：紧凑的附件、语音笔记、回复标签语法。
- **Heartbeats**：默认 agent 启用心跳时，心跳提示词和应答行为。
- **Runtime**：主机、OS、Node、模型、仓库根（检测到时）、thinking 等级（一行）。
- **Reasoning**：当前可见性等级 + /reasoning 切换提示。

> OpenClaw keeps large stable content, including **Project Context**, above the internal prompt cache boundary. Volatile channel/session sections such as Control UI embed guidance, **Messaging**, **Voice**, **Group Chat Context**, **Reactions**, **Heartbeats**, and **Runtime** are appended below that boundary so local backends with prefix caches can reuse the stable workspace prefix across channel turns. Tool descriptions should likewise avoid embedding current channel names when the accepted schema already carries that runtime detail.

OpenClaw 把稳定的大块内容（包括 **Project Context**）放在内部提示词缓存边界**之上**。易变的通道 / 会话相关段，比如 Control UI 嵌入指引、**Messaging**、**Voice**、**Group Chat Context**、**Reactions**、**Heartbeats**、**Runtime**，追加到边界**之下**；这样带前缀缓存的本地后端可以跨通道轮次复用稳定的工作区前缀。工具描述同理：如果已接受的 schema 里已经带了运行时细节（如当前通道名），就不要再把它嵌进描述。

> The Tooling section also includes runtime guidance for long-running work:
>
> * use cron for future follow-up (`check back later`, reminders, recurring work) instead of `exec` sleep loops, `yieldMs` delay tricks, or repeated `process` polling
> * use `exec` / `process` only for commands that start now and continue running in the background
> * when automatic completion wake is enabled, start the command once and rely on the push-based wake path when it emits output or fails
> * use `process` for logs, status, input, or intervention when you need to inspect a running command
> * if the task is larger, prefer `sessions_spawn`; sub-agent completion is push-based and auto-announces back to the requester
> * do not poll `subagents list` / `sessions_list` in a loop just to wait for completion

Tooling 段还包括长时任务的运行时指引：

- 未来要跟进的（"晚点再看"、提醒、定时任务）用 cron，不要用 `exec` sleep 循环、`yieldMs` 延时小技巧或者反复 `process` 轮询。
- `exec` / `process` 只用在那些"现在启动、然后在后台继续跑"的命令上。
- 启用了自动完成唤醒时，命令只起一次，等命令产生输出或失败时通过基于推送的唤醒路径接通。
- 要查看一个还在跑的命令的日志、状态、输入或干预时用 `process`。
- 任务更大时优先用 `sessions_spawn`；sub-agent 完成会基于推送自动通知回请求方。
- 不要循环轮询 `subagents list` / `sessions_list` 只为了等完成。

> `agents.defaults.subagents.delegationMode` can strengthen this guidance. The default `suggest` mode keeps the baseline nudge. `prefer` adds a dedicated **Sub-Agent Delegation** section telling the main agent to act as a responsive coordinator and push anything more involved than a direct reply through `sessions_spawn`. This is prompt-only; tool policy still controls whether `sessions_spawn` is available.

`agents.defaults.subagents.delegationMode` 可以加强这条指引。默认 `suggest` 保留基线提示。`prefer` 会加一段专门的 **Sub-Agent Delegation**，告诉主 agent 充当一个响应式协调者，凡是超出直接回复的工作都通过 `sessions_spawn` 推下去。这只是提示词层面；`sessions_spawn` 是否可用仍由工具策略决定。

> When the experimental `update_plan` tool is enabled, Tooling also tells the model to use it only for non-trivial multi-step work, keep exactly one `in_progress` step, and avoid repeating the whole plan after each update.

启用实验性 `update_plan` 工具时，Tooling 还会告诉模型：只在非平凡的多步任务里用它，保持恰好一个 `in_progress` 步骤，每次更新后别把整份计划重复一遍。

> Safety guardrails in the system prompt are advisory. They guide model behavior but do not enforce policy. Use tool policy, exec approvals, sandboxing, and channel allowlists for hard enforcement; operators can disable these by design.

系统提示词里的安全护栏是建议性的，引导模型行为但不强制策略。硬性约束用工具策略、执行批准、沙盒、通道白名单；这些按设计是允许运维关掉的。

> On channels with native approval cards/buttons, the runtime prompt now tells the agent to rely on that native approval UI first. It should only include a manual `/approve` command when the tool result says chat approvals are unavailable or manual approval is the only path.

在带原生批准卡片 / 按钮的通道上，运行时提示词会让 agent 优先靠原生批准 UI。只有工具结果说聊天批准不可用、或人工批准是唯一路径时，才提供手动 `/approve` 命令。

---

> ## Prompt modes

## 提示词模式

> OpenClaw can render smaller system prompts for sub-agents. The runtime sets a `promptMode` for each run (not a user-facing config):

OpenClaw 可以给 sub-agent 渲染更小的系统提示词。运行时给每次运行设一个 `promptMode`（不是面向用户的配置）：

> * `full` (default): includes all sections above.
> * `minimal`: used for sub-agents; omits **Memory Recall**, **OpenClaw Self-Update**, **Model Aliases**, **User Identity**, **Assistant Output Directives**, **Messaging**, **Silent Replies**, and **Heartbeats**. Tooling, **Safety**, **Skills** when supplied, Workspace, Sandbox, Current Date & Time (when known), Runtime, and injected context stay available.
> * `none`: returns only the base identity line.

- `full`（默认）：包含上面所有段。
- `minimal`：sub-agent 用；省略 **Memory Recall**、**OpenClaw Self-Update**、**Model Aliases**、**User Identity**、**Assistant Output Directives**、**Messaging**、**Silent Replies** 和 **Heartbeats**。Tooling、**Safety**、**Skills**（如有）、Workspace、Sandbox、Current Date & Time（已知时）、Runtime 和注入上下文仍然可用。
- `none`：只返回基础身份那一行。

> When `promptMode=minimal`, extra injected prompts are labeled **Subagent Context** instead of **Group Chat Context**.

`promptMode=minimal` 时，额外注入的提示词被标为 **Subagent Context**，不是 **Group Chat Context**。

> For channel auto-reply runs, OpenClaw omits the generic **Silent Replies** section when direct, group, or message-tool-only context owns the visible-reply contract. Only old automatic group/channel mode should show `NO_REPLY`; direct chats and message-tool-only replies do not receive silent-token guidance.

通道自动回复运行下，当私聊、群、message-tool-only 上下文已经掌握可见回复契约时，OpenClaw 会省略通用的 **Silent Replies** 段。只有旧的自动群 / 频道模式才显示 `NO_REPLY`；私聊和 message-tool-only 回复不会收到静默 token 指引。

---

> ## Prompt snapshots

## 提示词快照

> OpenClaw keeps committed prompt snapshots for the Codex runtime happy path under `test/fixtures/agents/prompt-snapshots/codex-runtime-happy-path/`. They render selected app-server thread/turn params plus a reconstructed model-bound prompt layer stack for Telegram direct, Discord group, and heartbeat turns. That stack includes a pinned Codex `gpt-5.5` model prompt fixture generated from Codex's model catalog/cache shape, the Codex happy-path permission developer text, OpenClaw developer instructions, turn-scoped collaboration-mode instructions when OpenClaw provides them, user turn input, and references to the dynamic tool specs.

OpenClaw 把 Codex runtime happy path 的提示词快照提交在 `test/fixtures/agents/prompt-snapshots/codex-runtime-happy-path/` 下。这些快照渲染了选定的 app-server thread/turn 参数加上重建出的模型绑定提示词层栈，覆盖 Telegram 私聊、Discord 群、heartbeat 这三类轮次。栈里包含：从 Codex 模型目录 / 缓存结构生成的 Codex `gpt-5.5` 模型提示词 fixture、Codex happy-path 权限开发者文本、OpenClaw 开发者指令、OpenClaw 提供时按轮作用域的协作模式指令、用户轮输入、以及动态工具规约的引用。

> Refresh the pinned Codex model prompt fixture with `pnpm prompt:snapshots:sync-codex-model`. By default, the script looks for Codex's runtime cache at `$CODEX_HOME/models_cache.json`, then `~/.codex/models_cache.json`, and only then falls back to the maintainer Codex checkout convention at `~/code/codex/codex-rs/models-manager/models.json`. If none of those sources exist, the command exits without changing the committed fixture. Pass `--catalog <path>` to refresh from a specific `models_cache.json` or `models.json` file.

用 `pnpm prompt:snapshots:sync-codex-model` 刷新固定的 Codex 模型提示词 fixture。脚本默认依次找 Codex 运行时缓存：`$CODEX_HOME/models_cache.json`、`~/.codex/models_cache.json`，最后回退到维护者 Codex checkout 约定路径 `~/code/codex/codex-rs/models-manager/models.json`。这些都不存在时，命令直接退出不会改提交进去的 fixture。要从指定的 `models_cache.json` 或 `models.json` 刷新就传 `--catalog <path>`。

> These snapshots are still not a byte-for-byte raw OpenAI request capture. Codex can add runtime-owned workspace context such as `AGENTS.md`, environment context, memories, app/plugin instructions, and built-in Default collaboration-mode instructions inside the Codex runtime after OpenClaw sends thread and turn params.

这些快照不是字节级的原始 OpenAI 请求抓包。OpenClaw 把 thread / turn 参数发出去之后，Codex runtime 内部还会加它自己拥有的工作区上下文 —— `AGENTS.md`、环境上下文、记忆、App / 插件指令、内置的默认协作模式指令。

> Regenerate them with `pnpm prompt:snapshots:gen` and verify drift with `pnpm prompt:snapshots:check`. CI runs the drift check in the additional boundary shard so prompt changes and snapshot updates stay attached to the same PR.

用 `pnpm prompt:snapshots:gen` 重生成，用 `pnpm prompt:snapshots:check` 校验偏移。CI 在额外的 boundary shard 里跑偏移检查，让提示词改动和快照更新绑在同一个 PR 上。

---

> ## Workspace bootstrap injection

## 工作区引导注入

> Bootstrap files are trimmed and appended under **Project Context** so the model sees identity and profile context without needing explicit reads:

引导文件会被裁剪后追加到 **Project Context** 下，让模型能直接看到身份和画像上下文，不必显式去读：

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
- `BOOTSTRAP.md`（只在全新工作区里有）
- `MEMORY.md`（如果存在）

> All of these files are **injected into the context window** on every turn unless a file-specific gate applies. `HEARTBEAT.md` is omitted on normal runs when heartbeats are disabled for the default agent or `agents.defaults.heartbeat.includeSystemPromptSection` is false. Keep injected files concise, especially `MEMORY.md`. `MEMORY.md` is intended to stay a curated long-term summary; detailed daily notes belong in `memory/*.md` where `memory_search` and `memory_get` can retrieve them on demand. Oversized `MEMORY.md` files increase prompt usage and can be partially injected because of the bootstrap file limits below.

每一轮上面这些文件都会**注入到上下文窗口**里，除非有文件专属门禁。当默认 agent 关掉了心跳，或 `agents.defaults.heartbeat.includeSystemPromptSection` 为 false 时，常规运行会跳过 `HEARTBEAT.md`。注入文件要保持简短，尤其是 `MEMORY.md`。`MEMORY.md` 应保持为精选的长期总结；详细的日常笔记放在 `memory/*.md`，由 `memory_search` 和 `memory_get` 按需检索。`MEMORY.md` 过大会增加提示词消耗，且可能因为下面的引导文件上限而被部分注入。

> When a session runs on the native Codex harness, Codex loads `AGENTS.md` through its own project-doc discovery. OpenClaw still resolves the remaining bootstrap files and forwards them as Codex config instructions, so `SOUL.md`, `TOOLS.md`, `IDENTITY.md`, `USER.md`, `HEARTBEAT.md`, `BOOTSTRAP.md`, and `MEMORY.md` keep the same workspace-context role without duplicating `AGENTS.md`.

会话跑在原生 Codex harness 上时，Codex 通过它自己的项目文档发现机制加载 `AGENTS.md`。OpenClaw 仍然解析其他引导文件，作为 Codex 配置指令传过去，所以 `SOUL.md`、`TOOLS.md`、`IDENTITY.md`、`USER.md`、`HEARTBEAT.md`、`BOOTSTRAP.md` 和 `MEMORY.md` 保留同样的工作区上下文角色，不会重复 `AGENTS.md`。

> <Note>
>   `memory/*.md` daily files are **not** part of the normal bootstrap Project Context. On ordinary turns they are accessed on demand via the `memory_search` and `memory_get` tools, so they do not count against the context window unless the model explicitly reads them. Bare `/new` and `/reset` turns are the exception: the runtime can prepend recent daily memory as a one-shot startup-context block for that first turn.
> </Note>

> **提示**：`memory/*.md` 日常文件**不是**常规引导 Project Context 的一部分。普通轮次下它们通过 `memory_search` 和 `memory_get` 工具按需访问，所以除非模型显式读，否则不占上下文窗口。光秃秃的 `/new` 和 `/reset` 轮次是例外：运行时可以为这第一轮把最近的日常记忆作为一次性启动上下文块前置进去。

> Large files are truncated with a marker. The max per-file size is controlled by `agents.defaults.bootstrapMaxChars` (default: 12000). Total injected bootstrap content across files is capped by `agents.defaults.bootstrapTotalMaxChars` (default: 60000). Missing files inject a short missing-file marker. When truncation occurs, OpenClaw can inject a concise system-prompt warning notice; control this with `agents.defaults.bootstrapPromptTruncationWarning` (`off`, `once`, `always`; default: `once`). Detailed raw/injected counts stay in diagnostics such as `/context`, `/status`, doctor, and logs.

大文件会被截断并加标记。每个文件的最大大小由 `agents.defaults.bootstrapMaxChars`（默认 12000）控制。所有引导文件注入的总量上限由 `agents.defaults.bootstrapTotalMaxChars`（默认 60000）控制。缺失文件会注入一个简短的"缺失文件"标记。截断发生时，OpenClaw 可以在系统提示词里注入一条简洁的警告通知；用 `agents.defaults.bootstrapPromptTruncationWarning` 控制（`off`、`once`、`always`；默认 `once`）。详细的原始 / 注入字数在 `/context`、`/status`、doctor、日志这些诊断里。

> For memory files, truncation is not data loss: the file remains intact on disk, but the model only sees the shortened injected copy until it reads or searches memory directly. If `MEMORY.md` is repeatedly truncated, distill it into a shorter durable summary and move detailed history into `memory/*.md`, or intentionally raise the bootstrap limits.

对记忆文件，截断不是数据丢失：磁盘上文件完好无损，只是模型直接读 / 搜索 memory 之前只看到截短的注入副本。`MEMORY.md` 反复被截断时，就把它精炼成一份更短的长期总结，把详细历史挪到 `memory/*.md`；或者刻意提高引导上限。

> Sub-agent sessions only inject `AGENTS.md` and `TOOLS.md` (other bootstrap files are filtered out to keep the sub-agent context small).

sub-agent 会话只注入 `AGENTS.md` 和 `TOOLS.md`（其他引导文件被过滤掉，让 sub-agent 上下文保持小巧）。

> Internal hooks can intercept this step via `agent:bootstrap` to mutate or replace the injected bootstrap files (for example swapping `SOUL.md` for an alternate persona).

内置钩子可以通过 `agent:bootstrap` 拦截这一步，改动或替换注入的引导文件（比如把 `SOUL.md` 换成另一种 persona）。

> If you want to make the agent sound less generic, start with [SOUL.md Personality Guide](/concepts/soul).

想让 agent 别那么"千篇一律"，从 [SOUL.md 人设指南](/concepts/soul) 入手。

> To inspect how much each injected file contributes (raw vs injected, truncation, plus tool schema overhead), use `/context list` or `/context detail`. See [Context](/concepts/context).

查看每个注入文件占多少（原始 vs 注入、截断、加上工具 schema 开销）用 `/context list` 或 `/context detail`。见 [Context](/concepts/context)。

---

> ## Time handling

## 时间处理

> The system prompt includes a dedicated **Current Date & Time** section when the user timezone is known. To keep the prompt cache-stable, it now only includes the **time zone** (no dynamic clock or time format).

用户时区已知时，系统提示词里有专门的 **Current Date & Time** 段。为了保持提示词缓存稳定，现在只放**时区**（不放动态时钟或时间格式）。

> Use `session_status` when the agent needs the current time; the status card includes a timestamp line. The same tool can optionally set a per-session model override (`model=default` clears it).

agent 需要当前时间时用 `session_status`；状态卡片里有一行时间戳。这个工具还可以可选地设一个按会话的 model 覆盖（`model=default` 清掉）。

> Configure with:
>
> * `agents.defaults.userTimezone`
> * `agents.defaults.timeFormat` (`auto` | `12` | `24`)

配置：

- `agents.defaults.userTimezone`
- `agents.defaults.timeFormat`（`auto` | `12` | `24`）

> See [Date & Time](/date-time) for full behavior details.

完整行为见 [日期与时间](/date-time)。

---

> ## Skills

## Skill

> When eligible skills exist, OpenClaw injects a compact **available skills list** (`formatSkillsForPrompt`) that includes the **file path** for each skill. The prompt instructs the model to use `read` to load the SKILL.md at the listed location (workspace, managed, or bundled). If no skills are eligible, the Skills section is omitted.

存在可用 skill 时，OpenClaw 注入一份紧凑的**可用 skill 列表**（`formatSkillsForPrompt`），每个 skill 带**文件路径**。提示词告诉模型用 `read` 去列出位置（workspace、managed、bundled）加载 SKILL.md。一个可用 skill 都没有时，Skills 段省略。

> Eligibility includes skill metadata gates, runtime environment/config checks, and the effective agent skill allowlist when `agents.defaults.skills` or `agents.list[].skills` is configured.

是否可用要看：skill 元数据门禁、运行时环境 / 配置检查、以及 `agents.defaults.skills` 或 `agents.list[].skills` 配置时生效的 agent skill 白名单。

> Plugin-bundled skills are eligible only when their owning plugin is enabled. This lets tool plugins expose deeper operating guides without embedding all of that guidance directly in every tool description.

插件捆绑的 skill 只在其所属插件启用时才可用。这让工具插件可以暴露更深入的操作指南，而不必把所有指引塞进每个工具描述里。

> ```
> <available_skills>
>   <skill>
>     <name>...</name>
>     <description>...</description>
>     <location>...</location>
>   </skill>
> </available_skills>
> ```

```
<available_skills>
  <skill>
    <name>...</name>
    <description>...</description>
    <location>...</location>
  </skill>
</available_skills>
```

> This keeps the base prompt small while still enabling targeted skill usage.

这样基础提示词保持精简，仍然支持有针对性地调用 skill。

> The skills list budget is owned by the skills subsystem:
>
> * Global default: `skills.limits.maxSkillsPromptChars`
> * Per-agent override: `agents.list[].skillsLimits.maxSkillsPromptChars`

skill 列表的预算由 skills 子系统管理：

- 全局默认：`skills.limits.maxSkillsPromptChars`
- 按 agent 覆盖：`agents.list[].skillsLimits.maxSkillsPromptChars`

> Generic bounded runtime excerpts use a different surface:
>
> * `agents.defaults.contextLimits.*`
> * `agents.list[].contextLimits.*`

通用的有界运行时摘录用另一组面：

- `agents.defaults.contextLimits.*`
- `agents.list[].contextLimits.*`

> That split keeps skills sizing separate from runtime read/injection sizing such as `memory_get`, live tool results, and post-compaction AGENTS.md refreshes.

这种划分把 skill 大小与运行时 read / 注入大小分开 —— 后者包括 `memory_get`、实时工具结果、压缩后的 AGENTS.md 刷新。

---

> ## Documentation

## 文档段

> The system prompt includes a **Documentation** section. When local docs are available, it points to the local OpenClaw docs directory (`docs/` in a Git checkout or the bundled npm package docs). If local docs are unavailable, it falls back to [https://docs.openclaw.ai](https://docs.openclaw.ai).

系统提示词里有 **Documentation** 段。本地文档可用时指向本地 OpenClaw docs 目录（git checkout 里的 `docs/` 或 bundled npm 包的 docs）。本地文档不可用时回退到 [https://docs.openclaw.ai](https://docs.openclaw.ai)。

> The same section also includes the OpenClaw source location. Git checkouts expose the local source root so the agent can inspect code directly. Package installs include the GitHub source URL and tell the agent to review source there whenever the docs are incomplete or stale. The prompt also notes the public docs mirror, community Discord, and ClawHub ([https://clawhub.ai](https://clawhub.ai)) for skills discovery. It tells the model to consult docs first for OpenClaw behavior, commands, configuration, or architecture, and to run `openclaw status` itself when possible (asking the user only when it lacks access). For configuration specifically, it points agents to the `gateway` tool action `config.schema.lookup` for exact field-level docs and constraints, then to `docs/gateway/configuration.md` and `docs/gateway/configuration-reference.md` for broader guidance.

同一段还包含 OpenClaw 源代码位置。git checkout 暴露本地源代码根目录，让 agent 直接看代码。npm 包安装则带上 GitHub 源 URL，告诉 agent 文档不完整或过期时去那里查源代码。提示词里还指出公开文档镜像、社区 Discord、以及发现 skill 用的 ClawHub（[https://clawhub.ai](https://clawhub.ai)）。它告诉模型查 OpenClaw 行为、命令、配置或架构时先查文档，可能时自己跑 `openclaw status`（只在没访问权限时问用户）。配置方面，特别指引 agent 用 `gateway` 工具的 `config.schema.lookup` 动作拿到字段级精确文档和约束，然后再去 `docs/gateway/configuration.md` 和 `docs/gateway/configuration-reference.md` 看更宽的指引。

---

> ## Related

## 相关

> * [Agent runtime](/concepts/agent)
> * [Agent workspace](/concepts/agent-workspace)
> * [Context engine](/concepts/context-engine)

- [Agent 运行时](/concepts/agent)
- [Agent 工作区](/concepts/agent-workspace)
- [Context 引擎](/concepts/context-engine)
