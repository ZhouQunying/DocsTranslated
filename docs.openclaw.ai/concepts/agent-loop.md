# Agent loop

> An agentic loop is the full "real" run of an agent: intake → context assembly → model inference → tool execution → streaming replies → persistence. It's the authoritative path that turns a message into actions and a final reply, while keeping session state consistent.

agent 循环（agentic loop）是 agent 的一次完整"真实"运行：接收 → 组装上下文 → 模型推理 → 执行工具 → 流式回复 → 持久化。它是把一条消息变成一连串动作和最终回复的权威路径，并且保持会话状态一致。

> In OpenClaw, a loop is a single, serialized run per session that emits lifecycle and stream events as the model thinks, calls tools, and streams output. This doc explains how that authentic loop is wired end-to-end.

OpenClaw 里，一个循环就是按会话串行的一次运行，模型在思考、调用工具、输出流式内容时会发出生命周期事件和流事件。本文讲清楚这个真实循环从端到端是怎么接起来的。

---

> ## Entry points

## 入口

> * Gateway RPC: `agent` and `agent.wait`.
> * CLI: `agent` command.

- Gateway RPC：`agent` 和 `agent.wait`。
- CLI：`agent` 命令。

---

> ## How it works (high-level)

## 工作原理（总体）

> 1. `agent` RPC validates params, resolves session (sessionKey/sessionId), persists session metadata, returns `{ runId, acceptedAt }` immediately.
> 2. `agentCommand` runs the agent:
>    * resolves model + thinking/verbose/trace defaults
>    * loads skills snapshot
>    * calls `runEmbeddedPiAgent` (pi-agent-core runtime)
>    * emits **lifecycle end/error** if the embedded loop does not emit one
> 3. `runEmbeddedPiAgent`:
>    * serializes runs via per-session + global queues
>    * resolves model + auth profile and builds the pi session
>    * subscribes to pi events and streams assistant/tool deltas
>    * enforces timeout -> aborts run if exceeded
>    * for Codex app-server turns, aborts an accepted turn that stops producing app-server progress before a terminal event
>    * returns payloads + usage metadata
> 4. `subscribeEmbeddedPiSession` bridges pi-agent-core events to OpenClaw `agent` stream:
>    * tool events => `stream: "tool"`
>    * assistant deltas => `stream: "assistant"`
>    * lifecycle events => `stream: "lifecycle"` (`phase: "start" | "end" | "error"`)
> 5. `agent.wait` uses `waitForAgentRun`:
>    * waits for **lifecycle end/error** for `runId`
>    * returns `{ status: ok|error|timeout, startedAt, endedAt, error? }`

1. `agent` RPC 校验参数、解析会话（sessionKey / sessionId）、持久化会话元数据，立刻返回 `{ runId, acceptedAt }`。
2. `agentCommand` 跑 agent：
   - 解析模型 + thinking / verbose / trace 默认值
   - 加载 skill 快照
   - 调 `runEmbeddedPiAgent`（pi-agent-core 运行时）
   - 嵌入循环没发出生命周期 end / error 时，由它兜底发一个
3. `runEmbeddedPiAgent`：
   - 通过每会话 + 全局队列把运行串行化
   - 解析模型 + auth profile，构建 pi 会话
   - 订阅 pi 事件，流式发送 assistant / tool delta
   - 强制超时 → 超时则中止运行
   - 对 Codex app-server 轮次，已接受的轮次在终止事件前停止产生 app-server 进度时中止
   - 返回 payload + 用量元数据
4. `subscribeEmbeddedPiSession` 把 pi-agent-core 事件桥接成 OpenClaw 的 `agent` 流：
   - 工具事件 => `stream: "tool"`
   - assistant delta => `stream: "assistant"`
   - 生命周期事件 => `stream: "lifecycle"`（`phase: "start" | "end" | "error"`）
5. `agent.wait` 用 `waitForAgentRun`：
   - 等 `runId` 的**生命周期 end / error**
   - 返回 `{ status: ok|error|timeout, startedAt, endedAt, error? }`

---

> ## Queueing + concurrency

## 排队 + 并发

> * Runs are serialized per session key (session lane) and optionally through a global lane.
> * This prevents tool/session races and keeps session history consistent.
> * Messaging channels can choose queue modes (steer/followup/collect/interrupt) that feed this lane system.
>   See [Command Queue](/concepts/queue).
> * Transcript writes are also protected by a session write lock on the session file. The lock is process-aware and file-based, so it catches writers that bypass the in-process queue or come from another process. Session transcript writers wait up to `session.writeLock.acquireTimeoutMs` before reporting the session as busy; the default is `60000` ms.
> * Session write locks are non-reentrant by default. If a helper intentionally nests acquisition of the same lock while preserving one logical writer, it must opt in explicitly with `allowReentrant: true`.

- 运行按 session key（session 队列）串行化，可选地再过一道全局队列。
- 这样能避免工具 / 会话竞态，保持会话历史一致。
- 消息通道可以选不同的队列模式（steer / followup / collect / interrupt），把消息喂给这套队列系统。
  见 [命令队列](/concepts/queue)。
- 写对话也有一把 session 写锁，加在会话文件上。这把锁感知进程、基于文件，所以能拦下那些绕过进程内队列、或者来自另一个进程的写入。会话对话写入方等 `session.writeLock.acquireTimeoutMs` 之内拿不到锁就报 busy；默认 `60000` 毫秒。
- session 写锁默认不可重入。某个 helper 出于设计要嵌套获取同一把锁，且保留单一逻辑写入方时，必须显式带 `allowReentrant: true` 才能拿到。

---

> ## Session + workspace preparation

## 会话 + 工作区准备

> * Workspace is resolved and created; sandboxed runs may redirect to a sandbox workspace root.
> * Skills are loaded (or reused from a snapshot) and injected into env and prompt.
> * Bootstrap/context files are resolved and injected into the system prompt report.
> * A session write lock is acquired; `SessionManager` is opened and prepared before streaming. Any later transcript rewrite, compaction, or truncation path must take the same lock before opening or mutating the transcript file.

- 解析并创建工作区；沙盒运行可能会重定向到 sandbox 工作区根目录。
- 加载 skill（或者从快照复用），注入到环境变量和提示词里。
- 解析引导 / 上下文文件，注入到系统提示词报告里。
- 拿到 session 写锁；流式开始前打开并准备好 `SessionManager`。后续任何对话重写、压缩、截断路径，在打开或改动对话文件前都得先拿同一把锁。

---

> ## Prompt assembly + system prompt

## 提示词组装 + 系统提示词

> * System prompt is built from OpenClaw's base prompt, skills prompt, bootstrap context, and per-run overrides.
> * Model-specific limits and compaction reserve tokens are enforced.
> * See [System prompt](/concepts/system-prompt) for what the model sees.

- 系统提示词由 OpenClaw 基础提示词、skill 提示词、引导上下文、每次运行的覆盖项组合而成。
- 模型自身上限和压缩预留 token 会被强制执行。
- 模型实际看到什么见 [系统提示词](/concepts/system-prompt)。

---

> ## Hook points (where you can intercept)

## 钩子点（你能在哪里拦截）

> OpenClaw has two hook systems:
>
> * **Internal hooks** (Gateway hooks): event-driven scripts for commands and lifecycle events.
> * **Plugin hooks**: extension points inside the agent/tool lifecycle and gateway pipeline.

OpenClaw 有两套钩子系统：

- **内置钩子**（Gateway hooks）：命令和生命周期事件的事件驱动脚本。
- **插件钩子**：agent / 工具生命周期和 Gateway 管道里的扩展点。

> ### Internal hooks (Gateway hooks)

### 内置钩子（Gateway hooks）

> * **`agent:bootstrap`**: runs while building bootstrap files before the system prompt is finalized. Use this to add/remove bootstrap context files.
> * **Command hooks**: `/new`, `/reset`, `/stop`, and other command events (see Hooks doc).

- **`agent:bootstrap`**：构建引导文件、系统提示词最终确定前运行。可以用它增删引导上下文文件。
- **命令钩子**：`/new`、`/reset`、`/stop` 及其他命令事件（见 Hooks 文档）。

> See [Hooks](/automation/hooks) for setup and examples.

配置和示例见 [钩子](/automation/hooks)。

> ### Plugin hooks (agent + gateway lifecycle)

### 插件钩子（agent + Gateway 生命周期）

> These run inside the agent loop or gateway pipeline:

这些跑在 agent 循环或 Gateway 管道内部：

> * **`before_model_resolve`**: runs pre-session (no `messages`) to deterministically override provider/model before model resolution.
> * **`before_prompt_build`**: runs after session load (with `messages`) to inject `prependContext`, `systemPrompt`, `prependSystemContext`, or `appendSystemContext` before prompt submission. Use `prependContext` for per-turn dynamic text and system-context fields for stable guidance that should sit in system prompt space.
> * **`before_agent_start`**: legacy compatibility hook that may run in either phase; prefer the explicit hooks above.
> * **`before_agent_reply`**: runs after inline actions and before the LLM call, letting a plugin claim the turn and return a synthetic reply or silence the turn entirely.
> * **`agent_end`**: inspect the final message list and run metadata after completion.
> * **`before_compaction` / `after_compaction`**: observe or annotate compaction cycles.
> * **`before_tool_call` / `after_tool_call`**: intercept tool params/results.
> * **`before_install`**: inspect built-in scan findings and optionally block skill or plugin installs.
> * **`tool_result_persist`**: synchronously transform tool results before they are written to an OpenClaw-owned session transcript.
> * **`message_received` / `message_sending` / `message_sent`**: inbound + outbound message hooks.
> * **`session_start` / `session_end`**: session lifecycle boundaries.
> * **`gateway_start` / `gateway_stop`**: gateway lifecycle events.

- **`before_model_resolve`**：在会话开始前（没有 `messages`）跑，可以在模型解析之前确定地覆盖 provider / model。
- **`before_prompt_build`**：在会话加载后（带 `messages`）跑，可以在提交提示词前注入 `prependContext`、`systemPrompt`、`prependSystemContext` 或 `appendSystemContext`。每轮动态文本用 `prependContext`；该放在系统提示词空间的稳定指引用 system-context 字段。
- **`before_agent_start`**：旧版兼容钩子，可能在任一阶段跑；优先用上面那些更明确的钩子。
- **`before_agent_reply`**：在内联动作之后、LLM 调用之前跑，让插件接管这一轮，返回一个合成的回复，或者让这一轮整个安静。
- **`agent_end`**：完成后查看最终消息列表和运行元数据。
- **`before_compaction` / `after_compaction`**:观察或标注压缩周期。
- **`before_tool_call` / `after_tool_call`**：拦截工具的参数 / 结果。
- **`before_install`**：检查内置扫描结果，可选地拦下 skill 或插件安装。
- **`tool_result_persist`**：在工具结果写到 OpenClaw 自己的会话对话之前同步转换它。
- **`message_received` / `message_sending` / `message_sent`**：接收 + 发送消息钩子。
- **`session_start` / `session_end`**：会话生命周期边界。
- **`gateway_start` / `gateway_stop`**：Gateway 生命周期事件。

> Hook decision rules for outbound/tool guards:
>
> * `before_tool_call`: `{ block: true }` is terminal and stops lower-priority handlers.
> * `before_tool_call`: `{ block: false }` is a no-op and does not clear a prior block.
> * `before_install`: `{ block: true }` is terminal and stops lower-priority handlers.
> * `before_install`: `{ block: false }` is a no-op and does not clear a prior block.
> * `message_sending`: `{ cancel: true }` is terminal and stops lower-priority handlers.
> * `message_sending`: `{ cancel: false }` is a no-op and does not clear a prior cancel.

发送 / 工具守卫的钩子决策规则：

- `before_tool_call`：`{ block: true }` 是终局，会终止低优先级处理器。
- `before_tool_call`：`{ block: false }` 是空操作，不会清掉之前的 block。
- `before_install`：`{ block: true }` 是终局，会终止低优先级处理器。
- `before_install`：`{ block: false }` 是空操作，不会清掉之前的 block。
- `message_sending`：`{ cancel: true }` 是终局，会终止低优先级处理器。
- `message_sending`：`{ cancel: false }` 是空操作，不会清掉之前的 cancel。

> See [Plugin hooks](/plugins/hooks) for the hook API and registration details.

钩子 API 和注册细节见 [插件钩子](/plugins/hooks)。

> Harnesses may adapt these hooks differently. The Codex app-server harness keeps OpenClaw plugin hooks as the compatibility contract for documented mirrored surfaces, while Codex native hooks remain a separate lower-level Codex mechanism.

不同的 harness 可能会用不一样的方式适配这些钩子。Codex app-server harness 把 OpenClaw 插件钩子当作有文档说明的镜像 surface 的兼容契约；Codex 原生钩子是另一套更底层的 Codex 机制。

---

> ## Streaming + partial replies

## 流式 + 局部回复

> * Assistant deltas are streamed from pi-agent-core and emitted as `assistant` events.
> * Block streaming can emit partial replies either on `text_end` or `message_end`.
> * Reasoning streaming can be emitted as a separate stream or as block replies.
> * See [Streaming](/concepts/streaming) for chunking and block reply behavior.

- assistant delta 从 pi-agent-core 流出来，以 `assistant` 事件形式发出。
- block 流式可以在 `text_end` 或 `message_end` 边界发出局部回复。
- 推理流式可以走单独的流，也可以作为 block 回复发。
- 切片和 block 回复行为见 [流式](/concepts/streaming)。

---

> ## Tool execution + messaging tools

## 工具执行 + 消息工具

> * Tool start/update/end events are emitted on the `tool` stream.
> * Tool results are sanitized for size and image payloads before logging/emitting.
> * Messaging tool sends are tracked to suppress duplicate assistant confirmations.

- 工具的 start / update / end 事件走 `tool` 流。
- 工具结果在记录 / 发出前先按大小和图像载荷做清洗。
- 消息工具的发送会被记录下来，用于压制重复的 assistant 确认。

---

> ## Reply shaping + suppression

## 回复整形 + 压制

> * Final payloads are assembled from:
>   * assistant text (and optional reasoning)
>   * inline tool summaries (when verbose + allowed)
>   * assistant error text when the model errors
> * The exact silent token `NO_REPLY` / `no_reply` is filtered from outgoing payloads.
> * Messaging tool duplicates are removed from the final payload list.
> * If no renderable payloads remain and a tool errored, a fallback tool error reply is emitted (unless a messaging tool already sent a user-visible reply).

- 最终 payload 由这些拼起来：
  - assistant 文本（可选带推理）
  - 内联工具摘要（verbose 开启且允许时）
  - 模型出错时的 assistant 错误文本
- 精确的静默 token `NO_REPLY` / `no_reply` 在发出 payload 前被过滤掉。
- 最终 payload 列表里会去掉消息工具的重复项。
- 没有可渲染 payload 且工具报错时，会发一条兜底的工具错误回复（除非消息工具已经发过用户可见回复）。

---

> ## Compaction + retries

## 压缩 + 重试

> * Auto-compaction emits `compaction` stream events and can trigger a retry.
> * On retry, in-memory buffers and tool summaries are reset to avoid duplicate output.
> * See [Compaction](/concepts/compaction) for the compaction pipeline.

- 自动压缩会发出 `compaction` 流事件，可能触发重试。
- 重试时，内存里的缓冲和工具摘要会重置，避免重复输出。
- 压缩流水线见 [压缩](/concepts/compaction)。

---

> ## Event streams (today)

## 事件流（当前）

> * `lifecycle`: emitted by `subscribeEmbeddedPiSession` (and as a fallback by `agentCommand`)
> * `assistant`: streamed deltas from pi-agent-core
> * `tool`: streamed tool events from pi-agent-core

- `lifecycle`：由 `subscribeEmbeddedPiSession` 发出（`agentCommand` 兜底也会发）。
- `assistant`：来自 pi-agent-core 的流式 delta。
- `tool`：来自 pi-agent-core 的工具事件流。

---

> ## Chat channel handling

## 聊天通道处理

> * Assistant deltas are buffered into chat `delta` messages.
> * A chat `final` is emitted on **lifecycle end/error**.

- assistant delta 缓冲为聊天 `delta` 消息。
- 收到**生命周期 end / error** 时发一条聊天 `final`。

---

> ## Timeouts

## 超时

> * `agent.wait` default: 30s (just the wait). `timeoutMs` param overrides.
> * Agent runtime: `agents.defaults.timeoutSeconds` default 172800s (48 hours); enforced in `runEmbeddedPiAgent` abort timer.
> * Cron runtime: isolated agent-turn `timeoutSeconds` is owned by cron. The scheduler starts that timer when execution begins, aborts the underlying run at the configured deadline, then runs bounded cleanup before recording the timeout so a stale child session cannot keep the lane stuck.
> * Session liveness diagnostics: with diagnostics enabled, `diagnostics.stuckSessionWarnMs` classifies long `processing` sessions that have no observed reply, tool, status, block, or ACP progress. Active embedded runs, model calls, and tool calls report as `session.long_running`; active work with no recent progress reports as `session.stalled`; `session.stuck` is reserved for stale session bookkeeping with no active work. Stale session bookkeeping releases the affected session lane immediately; stalled embedded runs are abort-drained only after `diagnostics.stuckSessionAbortMs` (default: at least 5 minutes and 3x the warning threshold) so queued work can resume without cutting off merely slow runs. Recovery emits structured requested/completed outcomes, and diagnostic state is marked idle only if the same processing generation is still current. Repeated `session.stuck` diagnostics back off while the session remains unchanged.
> * Model idle timeout: OpenClaw aborts a model request when no response chunks arrive before the idle window. `models.providers.<id>.timeoutSeconds` extends this idle watchdog for slow local/self-hosted providers, but it is still bounded by any lower `agents.defaults.timeoutSeconds` or run-specific timeout because those control the whole agent run. Otherwise OpenClaw uses `agents.defaults.timeoutSeconds` when configured, capped at 120s by default. Cron-triggered runs with no explicit model or agent timeout disable the idle watchdog and rely on the cron outer timeout.
> * Provider HTTP request timeout: `models.providers.<id>.timeoutSeconds` applies to that provider's model HTTP fetches, including connect, headers, body, SDK request timeout, total guarded-fetch abort handling, and model stream idle watchdog. Use this for slow local/self-hosted providers such as Ollama before raising the whole agent runtime timeout, and keep the agent/runtime timeout at least as high when the model request needs to run longer.

- `agent.wait` 默认 30 秒（只等待）。`timeoutMs` 参数覆盖。
- Agent 运行时：`agents.defaults.timeoutSeconds` 默认 172800 秒（48 小时）；由 `runEmbeddedPiAgent` 的中止定时器执行。
- Cron 运行时：与 agent 隔离的轮次 `timeoutSeconds` 由 cron 拥有。调度器在执行开始时启动这个定时器，到配置的截止时间中止底层运行，然后跑一段有界清理之后再记录超时，避免一个过期的子会话把队列卡住。
- 会话存活性诊断：开启诊断后，`diagnostics.stuckSessionWarnMs` 把那些一直 `processing` 但没观察到回复 / 工具 / 状态 / block / ACP 进度的会话归类。活跃的嵌入运行、模型调用、工具调用算作 `session.long_running`；正在干活但最近没进展的算 `session.stalled`；`session.stuck` 保留给"没活在干、但记账上还在 processing"这种过期账目。过期账目会立刻释放会话队列；卡住的嵌入运行要等到 `diagnostics.stuckSessionAbortMs`（默认至少 5 分钟，且为告警阈值的 3 倍）才中止排空 —— 这样队列里其他活能继续，又不会误伤只是慢的运行。恢复时会发出结构化的请求 / 完成结果；只有当同一代 processing 仍然是当前代时，诊断状态才会被标为 idle。会话没变的情况下，反复出现的 `session.stuck` 诊断会逐步退避。
- 模型空闲超时：模型在空闲窗口内没回任何 chunk 时 OpenClaw 中止该请求。`models.providers.<id>.timeoutSeconds` 给慢的本地 / 自托管 provider 延长这个空闲看门狗，但仍受更低的 `agents.defaults.timeoutSeconds` 或运行级超时约束 —— 那两个控制整个 agent 运行。否则有配置时用 `agents.defaults.timeoutSeconds`，默认上限 120 秒。cron 触发、没显式模型或 agent 超时的运行会关闭空闲看门狗，依赖 cron 外层超时。
- Provider HTTP 请求超时：`models.providers.<id>.timeoutSeconds` 作用于该 provider 的模型 HTTP fetch，包括 connect、headers、body、SDK 请求超时、整体 guarded-fetch 中止处理和模型流空闲看门狗。慢的本地 / 自托管 provider（如 Ollama）应优先用这个，而不是直接抬高整个 agent 运行时超时；模型请求要跑久时，把 agent / 运行时超时也至少抬到同样高。

---

> ## Where things can end early

## 哪些情况会提前结束

> * Agent timeout (abort)
> * AbortSignal (cancel)
> * Gateway disconnect or RPC timeout
> * `agent.wait` timeout (wait-only, does not stop agent)

- Agent 超时（中止）
- AbortSignal（取消）
- Gateway 断开或 RPC 超时
- `agent.wait` 超时（只是结束等待，不会停掉 agent）

---

> ## Related

## 相关

> * [Tools](/tools) — available agent tools
> * [Hooks](/automation/hooks) — event-driven scripts triggered by agent lifecycle events
> * [Compaction](/concepts/compaction) — how long conversations are summarized
> * [Exec Approvals](/tools/exec-approvals) — approval gates for shell commands
> * [Thinking](/tools/thinking) — thinking/reasoning level configuration

- [工具](/tools) —— 可用的 agent 工具
- [钩子](/automation/hooks) —— agent 生命周期事件驱动的脚本
- [压缩](/concepts/compaction) —— 长对话怎么被概括
- [执行批准](/tools/exec-approvals) —— shell 命令的批准闸口
- [思考](/tools/thinking) —— 思考 / 推理等级配置
