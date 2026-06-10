# Command queue

## 架构精读

> 本节提炼命令队列的并发控制模式。跳过不影响阅读后续翻译。

### 核心问题

多个用户同时发消息给 Agent，每条都立刻触发 LLM 调用会怎样？资源竞争（同一个会话文件被并发读写）、上游限速（API 调用过密）、语义混乱（Agent 同时处理矛盾的指令）。

### 通路感知的 FIFO

解法是**两级串行化**，类似操作系统的线程调度：

1. **会话级**：每个会话同一时间只有一个 Agent 运行（`session:<key>` 通路），防止同一会话的并发冲突
2. **全局级**：所有会话运行再排进全局队列（`main` 通路），整体并行度受 `maxConcurrent` 限制

额外通路（`cron`、`subagent`）让后台任务独立排队，不阻塞用户的实时消息。

### 四种模式 = 四种中断处理策略

| 模式 | 类比 | 适用场景 |
|------|------|----------|
| `steer` | CPU 中断注入——正在执行的进程收到新信号 | 默认。用户补充信息给正在跑的 Agent |
| `followup` | 消息队列——先排队、后处理 | 每条消息需要独立完整处理 |
| `collect` | 批处理——攒一批再处理 | 多条消息合并成一个上下文更高效 |
| `interrupt` | kill -9——杀掉当前进程、跑新的 | 用户改主意了，之前的不要了 |

### 输入中状态的 UX 技巧

排队等待时立刻发"输入中"状态（typing indicator），让用户感觉 Agent 在处理。实际上 Agent 可能还在队列里等——但用户不需要知道这个实现细节。这是**感知延迟优化**的经典手法。

---

> We serialize inbound auto-reply runs (all channels) through a tiny in-process queue to prevent multiple agent runs from colliding, while still allowing safe parallelism across sessions.

我们用一个小型进程内队列把所有通道的接收自动回复运行串行化，避免多个 agent 运行打架，同时跨会话仍然能安全并行。

---

> ## Why

## 为什么

> * Auto-reply runs can be expensive (LLM calls) and can collide when multiple inbound messages arrive close together.
> * Serializing avoids competing for shared resources (session files, logs, CLI stdin) and reduces the chance of upstream rate limits.

- 自动回复运行可能贵（LLM 调用），多条接收消息靠近一起到达时会撞上。
- 串行化避免抢共享资源（会话文件、日志、CLI stdin），还能降低上游限速概率。

---

> ## How it works

## 工作原理

> * A lane-aware FIFO queue drains each lane with a configurable concurrency cap (default 1 for unconfigured lanes; main defaults to 4, subagent to 8).
> * `runEmbeddedAgent` enqueues by **session key** (lane `session:<key>`) to guarantee only one active run per session.
> * Each session run is then queued into a **global lane** (`main` by default) so overall parallelism is capped by `agents.defaults.maxConcurrent`.
> * When verbose logging is enabled, queued runs emit a short notice if they waited more than \~2s before starting.
> * Typing indicators still fire immediately on enqueue (when supported by the channel) so user experience is unchanged while we wait our turn.

- 一个按通路分组的 FIFO 队列，按可配置并发上限分别消费每条通路（未配置的通路默认 1；main 默认 4，subagent 默认 8）。
- `runEmbeddedAgent` 按**会话 key** 入队（通路 `session:<key>`），保证每会话同时只有一个活跃运行。
- 然后会话运行排进**全局队列**（默认 `main`），整体并行受 `agents.defaults.maxConcurrent` 限制。
- 启用 verbose 日志后，排队运行如果等了超过 \~2 秒才开始，会发一条简短通知。
- 入队时仍然立即发输入中状态（通道支持的话），等待时用户体验不变。

---

> ## Defaults

## 默认值

> When unset, all inbound channel surfaces use:
>
> * `mode: "steer"`
> * `debounceMs: 500`
> * `cap: 20`
> * `drop: "summarize"`

不设置时，所有接收通道入口用：

- `mode: "steer"`
- `debounceMs: 500`
- `cap: 20`
- `drop: "summarize"`

> Same-turn steering is the default. A prompt that arrives mid-run is injected into the active runtime when the run can accept steering, so no second session run is started. If the active run cannot accept steering, OpenClaw waits for the active run to finish before starting the prompt.

同轮转向（same-turn steering）是默认。运行中途到的 prompt，在运行能接受 steering 时被注入到活跃 runtime 里，不会启动第二次会话运行。活跃运行不能接受 steering 时，OpenClaw 等它结束才开始处理这个 prompt。

---

> ## Queue modes

## 队列模式

> `/queue` controls what normal inbound messages do while a session already has an active run:

`/queue` 控制会话已有活跃运行时常规接收消息怎么办：

> * `steer`: inject messages into the active runtime. OpenClaw delivers all pending steering messages **after the current assistant turn finishes executing its tool calls**, before the next LLM call; Codex app-server receives one batched `turn/steer`. If the run is not actively streaming or steering is unavailable, OpenClaw waits until the active run ends before starting the prompt.
> * `followup`: do not steer. Enqueue each message for a later agent turn after the current run ends.
> * `collect`: do not steer. Coalesce queued messages into a **single** followup turn after the quiet window. If messages target different channels/threads, they drain individually to preserve routing.
> * `interrupt`: abort the active run for that session, then run the newest message.

- `steer`：把消息注入到活跃 runtime。OpenClaw 在**当前 assistant 轮跑完它的工具调用之后**、下一次 LLM 调用之前投递所有待处理的 steering 消息；Codex app-server 收到一条合并的 `turn/steer`。运行没在流式或 steering 不可用时，OpenClaw 等到活跃运行结束再处理 prompt。
- `followup`：不 steer。每条消息排队进当前运行结束后的后续 agent 轮次。
- `collect`：不 steer。把排队消息合并成静默窗口结束后的**一个**后续轮次。消息目标不同通道 / thread 时分别消费，保持路由。
- `interrupt`：中止该会话的活跃运行，然后跑最新消息。

> For runtime-specific timing and dependency behavior, see [Steering queue](/concepts/queue-steering). For the explicit `/steer <message>` command, see [Steer](/tools/steer).

按 runtime 区分的时序和依赖行为见 [转向队列](/concepts/queue-steering)。显式 `/steer <message>` 命令见 [Steer](/tools/steer)。

> Configure globally or per channel via `messages.queue`:
>
> ```json5
> {
>   messages: {
>     queue: {
>       mode: "steer",
>       debounceMs: 500,
>       cap: 20,
>       drop: "summarize",
>       byChannel: { discord: "collect" },
>     },
>   },
> }
> ```

通过 `messages.queue` 全局或按通道配置：

```json5
{
  messages: {
    queue: {
      mode: "steer",
      debounceMs: 500,
      cap: 20,
      drop: "summarize",
      byChannel: { discord: "collect" },
    },
  },
}
```

---

> ## Queue options

## 队列选项

> Options apply to queued delivery. `debounceMs` also sets the Codex steering quiet window in `steer` mode:

选项作用于排队投递。`steer` 模式下 `debounceMs` 还设置 Codex steering 的静默窗口：

> * `debounceMs`: quiet window before draining queued followups or collect batches; in Codex `steer` mode, quiet window before sending batched `turn/steer`. Bare numbers are milliseconds; units `ms`, `s`, `m`, `h`, and `d` are accepted by `/queue` options.
> * `cap`: max queued messages per session. Values below `1` are ignored.
> * `drop: "summarize"`: default. Drop the oldest queued entries as needed, keep compact summaries, and inject them as a synthetic followup prompt.
> * `drop: "old"`: drop the oldest queued entries as needed, without preserving summaries.
> * `drop: "new"`: reject the newest message when the queue is already full.

- `debounceMs`：消费排队 followup 或 collect 批次前的静默窗口；Codex `steer` 模式下，发送合并 `turn/steer` 前的静默窗口。裸数字是毫秒；`/queue` 选项接受 `ms`、`s`、`m`、`h`、`d` 单位。
- `cap`：每会话排队消息数上限。小于 `1` 的值被忽略。
- `drop: "summarize"`：默认。按需丢最老的排队条目，保留紧凑摘要，把它们作为合成的 followup prompt 注入。
- `drop: "old"`：按需丢最老的排队条目，不保留摘要。
- `drop: "new"`：队列已满时拒绝最新消息。

> Defaults: `debounceMs: 500`, `cap: 20`, `drop: summarize`.

默认值：`debounceMs: 500`、`cap: 20`、`drop: summarize`。

---

> ## Steer and streaming

## 转向与流式

> When channel streaming is `partial` or `block`, steering can look like several short visible replies while the active run reaches runtime boundaries:
>
> * `partial`: the preview may finalize early, then a new preview starts after steering is accepted.
> * `block`: draft-sized blocks can create the same sequential appearance.
> * Without streaming, steering falls back to a followup after the active run when the runtime cannot accept same-turn steering.

通道流式为 `partial` 或 `block` 时，活跃运行到达 runtime 边界过程中 steering 可能看起来像连续几条短的可见回复：

- `partial`：预览可能提前定稿，steering 被接受后启动新的预览。
- `block`：草稿大小的 block 也能产生同样的逐条观感。
- 不开流式时，runtime 无法接受同轮 steering 就退化成活跃运行结束后的 followup。

> `steer` does not abort in-flight tools. Use `/queue interrupt` when the newest message should abort the current run.

`steer` 不会中止正在执行的工具。想让最新消息中止当前运行时用 `/queue interrupt`。

---

> ## Precedence

## 优先级

> For mode selection, OpenClaw resolves:
>
> 1. Inline or stored per-session `/queue` override.
> 2. `messages.queue.byChannel.<channel>`.
> 3. `messages.queue.mode`.
> 4. Default `steer`.

模式选择 OpenClaw 解析顺序：

1. 内联或存储的、按会话的 `/queue` 覆盖。
2. `messages.queue.byChannel.<channel>`。
3. `messages.queue.mode`。
4. 默认 `steer`。

> For options, inline or stored `/queue` options win over config. Then channel-specific debounce (`messages.queue.debounceMsByChannel`), plugin debounce defaults, global `messages.queue` options, and built-in defaults are applied. `cap` and `drop` are global/session options, not per-channel config keys.

选项方面，内联或存储的 `/queue` 选项优先于配置。之后依次应用按通道防抖（`messages.queue.debounceMsByChannel`）、插件防抖默认、全局 `messages.queue` 选项、内置默认。`cap` 和 `drop` 是全局 / 会话选项，不是按通道的配置 key。

---

> ## Per-session overrides

## 按会话覆盖

> * Send `/queue <steer|followup|collect|interrupt>` as a standalone command to store the queue mode for the current session.
> * Options can be combined: `/queue collect debounce:0.5s cap:25 drop:summarize`
> * `/queue default` or `/queue reset` clears the session override.

- 把 `/queue <steer|followup|collect|interrupt>` 作为独立命令发，存当前会话的队列模式。
- 选项可以组合：`/queue collect debounce:0.5s cap:25 drop:summarize`。
- `/queue default` 或 `/queue reset` 清掉会话覆盖。

---

> ## Scope and guarantees

## 范围和保证

> * Applies to auto-reply agent runs across all inbound channels that use the gateway reply pipeline (WhatsApp web, Telegram, Slack, Discord, Signal, iMessage, webchat, etc.).
> * Default lane (`main`) is process-wide for inbound + main heartbeats; set `agents.defaults.maxConcurrent` to allow multiple sessions in parallel.
> * Additional lanes may exist (e.g. `cron`, `cron-nested`, `nested`, `subagent`) so background jobs can run in parallel without blocking inbound replies. Isolated cron agent turns hold a `cron` slot while their inner agent execution uses `cron-nested`; both use `cron.maxConcurrentRuns`. Shared non-cron `nested` flows keep their own lane behavior. These detached runs are tracked as [background tasks](/automation/tasks).
> * Per-session lanes guarantee that only one agent run touches a given session at a time.
> * No external dependencies or background worker threads; pure TypeScript + promises.

- 适用于走 Gateway 回复流水线的所有接收通道（WhatsApp web、Telegram、Slack、Discord、Signal、iMessage、webchat 等）的自动回复 agent 运行。
- 默认队列（`main`）是进程级的，给接收 + 主心跳用；设 `agents.defaults.maxConcurrent` 允许多会话并行。
- 还可能有其他队列（`cron`、`cron-nested`、`nested`、`subagent`），让后台任务能并行跑而不挡住接收回复。隔离的 cron agent 轮次占一个 `cron` slot，它内部 agent 执行用 `cron-nested`；两者都用 `cron.maxConcurrentRuns`。共享的非 cron `nested` 流保持自己的队列行为。这些脱离的运行作为 [后台任务](/automation/tasks) 追踪。
- 按会话队列保证给定会话同时只有一个 agent 运行触碰它。
- 没有外部依赖或后台 worker 线程；纯 TypeScript + Promise。

---

> ## Troubleshooting

## 故障排查

> * If commands seem stuck, enable verbose logs and look for "queued for ...ms" lines to confirm the queue is draining.
> * If you need queue depth, enable verbose logs and watch for queue timing lines.
> * Codex app-server runs that accept a turn and then stop emitting progress are interrupted by the Codex adapter so the active session lane can release instead of waiting for the outer run timeout.
> * When diagnostics are enabled, sessions that remain in `processing` past `diagnostics.stuckSessionWarnMs` with no observed reply, tool, status, block, or ACP progress are classified by current activity. Active work logs as `session.long_running`; active work with no recent progress logs as `session.stalled`; `session.stuck` is reserved for recoverable stale session bookkeeping, including idle queued sessions with stale ownerless model/tool activity, and only that path can release the affected session lane so queued work drains. Repeated `session.stuck` diagnostics back off while the session remains unchanged.

- 命令好像卡住时，开 verbose 日志，看 "queued for ...ms" 行确认队列在消费。
- 想看队列深度，开 verbose 日志，留意队列时序行。
- Codex app-server 运行接受了一个 turn 然后停止发出进度时，Codex 适配器会中断它，让活跃会话队列能释放，而不是等外层运行超时。
- 启用诊断后，超过 `diagnostics.stuckSessionWarnMs` 仍处于 `processing` 且没观察到回复、工具、状态、block 或 ACP 进度的会话，按当前活动分类。活跃工作记 `session.long_running`；活跃但近期无进展的记 `session.stalled`；`session.stuck` 专门处理可恢复的过期会话记账，包括持有无主模型/工具活动的空闲排队会话；只有这条路径能释放受影响的会话通路让排队工作消费。会话没变时，重复出现的 `session.stuck` 诊断会逐步退避。

---

> ## Related

## 相关

> * [Session management](/concepts/session)
> * [Steering queue](/concepts/queue-steering)
> * [Steer](/tools/steer)
> * [Retry policy](/concepts/retry)

- [会话管理](/concepts/session)
- [转向队列](/concepts/queue-steering)
- [Steer](/tools/steer)
- [重试策略](/concepts/retry)
