# Session tools

> OpenClaw gives agents tools to work across sessions, inspect status, and orchestrate sub-agents.

OpenClaw 给 agent 提供跨会话工作、查看状态、调度 sub-agent 的工具。

---

> ## Available tools

## 可用工具

> | Tool               | What it does                                                                |
> | ------------------ | --------------------------------------------------------------------------- |
> | `sessions_list`    | List sessions with optional filters (kind, label, agent, recency, preview)  |
> | `sessions_history` | Read the transcript of a specific session                                   |
> | `sessions_send`    | Send a message to another session and optionally wait                       |
> | `sessions_spawn`   | Spawn an isolated sub-agent session for background work                     |
> | `sessions_yield`   | End the current turn and wait for follow-up sub-agent results               |
> | `subagents`        | List, steer, or kill spawned sub-agents for this session                    |
> | `session_status`   | Show a `/status`-style card and optionally set a per-session model override |

| 工具               | 作用                                                                          |
| ------------------ | ----------------------------------------------------------------------------- |
| `sessions_list`    | 列出会话，可按 kind、label、agent、近期程度、预览过滤                         |
| `sessions_history` | 读某个会话的 transcript                                                       |
| `sessions_send`    | 给另一个会话发消息，可选等待                                                  |
| `sessions_spawn`   | 为后台工作 spawn 一个隔离的 sub-agent 会话                                    |
| `sessions_yield`   | 结束当前轮次，等 sub-agent 后续结果                                           |
| `subagents`        | 列出、引导或杀掉本会话 spawn 出的 sub-agent                                   |
| `session_status`   | 显示一张 `/status` 风格的卡片，可选设置按会话的模型覆盖                       |

> These tools are still subject to the active tool profile and allow/deny policy. `tools.profile: "coding"` includes the full session orchestration set, including `sessions_spawn`, `sessions_yield`, and `subagents`. `tools.profile: "messaging"` includes cross-session messaging tools (`sessions_list`, `sessions_history`, `sessions_send`, `session_status`) but does not include sub-agent spawning. To keep a messaging profile and still allow native delegation, add:

这些工具仍受当前工具 profile 和 allow/deny 策略约束。`tools.profile: "coding"` 包含完整的会话编排集，含 `sessions_spawn`、`sessions_yield`、`subagents`。`tools.profile: "messaging"` 包含跨会话消息工具（`sessions_list`、`sessions_history`、`sessions_send`、`session_status`），但不含 sub-agent spawn。要保留 messaging profile 同时允许原生委派：

> ```json5
> {
>   tools: {
>     profile: "messaging",
>     alsoAllow: ["sessions_spawn", "sessions_yield", "subagents"],
>   },
> }
> ```

```json5
{
  tools: {
    profile: "messaging",
    alsoAllow: ["sessions_spawn", "sessions_yield", "subagents"],
  },
}
```

> Group, provider, sandbox, and per-agent policies can still remove those tools after the profile stage. Use `/tools` from the affected session to inspect the effective tool list.

群、provider、沙盒、按 agent 的策略仍能在 profile 阶段之后把这些工具去掉。在受影响的会话里发 `/tools` 查看有效工具列表。

---

> ## Listing and reading sessions

## 列出与读取会话

> `sessions_list` returns sessions with their key, agentId, kind, channel, model, token counts, and timestamps. Filter by kind (`main`, `group`, `cron`, `hook`, `node`), exact `label`, exact `agentId`, search text, or recency (`activeMinutes`). When you need mailbox-style triage, it can also ask for a visibility-scoped derived title, a last-message preview snippet, or bounded recent messages on each row. Derived titles and previews are produced only for sessions the caller can already see under the configured session tool visibility policy, so unrelated sessions stay hidden.

`sessions_list` 返回会话的 key、agentId、kind、channel、model、token 数和时间戳。按 kind（`main`、`group`、`cron`、`hook`、`node`）、精确 `label`、精确 `agentId`、搜索文本或近期程度（`activeMinutes`）过滤。需要类似邮箱的归类时，还可以让它给每一行带上一个可见性范围内的派生标题、最近一条消息的预览片段或有界的最近消息。派生标题和预览只对调用方在配置的会话工具可见性策略下能看到的会话产生 —— 不相关的会话仍然藏着。

> `sessions_history` fetches the conversation transcript for a specific session. By default, tool results are excluded -- pass `includeTools: true` to see them. The returned view is intentionally bounded and safety-filtered:

`sessions_history` 抓取某个会话的对话 transcript。默认排除工具结果 —— 传 `includeTools: true` 才看得到。返回的视图刻意有界并经过安全过滤：

> * assistant text is normalized before recall:
>   * thinking tags are stripped
>   * `<relevant-memories>` / `<relevant_memories>` scaffolding blocks are stripped
>   * plain-text tool-call XML payload blocks such as `<tool_call>...</tool_call>`, `<function_call>...</function_call>`, `<tool_calls>...</tool_calls>`, and `<function_calls>...</function_calls>` are stripped, including truncated payloads that never close cleanly
>   * downgraded tool-call/result scaffolding such as `[Tool Call: ...]`, `[Tool Result ...]`, and `[Historical context ...]` is stripped
>   * leaked model control tokens such as `<|assistant|>`, other ASCII `<|...|>` tokens, and full-width `<｜...｜>` variants are stripped
>   * malformed MiniMax tool-call XML such as `<invoke ...>` / `</minimax:tool_call>` is stripped
> * credential/token-like text is redacted before it is returned
> * long text blocks are truncated
> * very large histories can drop older rows or replace an oversized row with `[sessions_history omitted: message too large]`
> * the tool reports summary flags such as `truncated`, `droppedMessages`, `contentTruncated`, `contentRedacted`, and `bytes`

- 召回前对 assistant 文本做归一化：
  - 剥掉 thinking 标签
  - 剥掉 `<relevant-memories>` / `<relevant_memories>` 脚手架块
  - 剥掉纯文本的工具调用 XML 载荷块，如 `<tool_call>...</tool_call>`、`<function_call>...</function_call>`、`<tool_calls>...</tool_calls>`、`<function_calls>...</function_calls>`，以及那些没干净闭合的截断载荷
  - 剥掉降级的工具调用 / 结果脚手架，如 `[Tool Call: ...]`、`[Tool Result ...]`、`[Historical context ...]`
  - 剥掉泄漏的模型控制 token，如 `<|assistant|>`、其他 ASCII `<|...|>` token，以及全角 `<｜...｜>` 变体
  - 剥掉畸形的 MiniMax 工具调用 XML，如 `<invoke ...>` / `</minimax:tool_call>`
- 返回前对类似凭证 / token 的文本做脱敏。
- 长文本块会被截断。
- 超大历史可能丢掉旧行，或用 `[sessions_history omitted: message too large]` 替换超大行。
- 工具会汇报 `truncated`、`droppedMessages`、`contentTruncated`、`contentRedacted`、`bytes` 这些汇总标志。

> Both tools accept either a **session key** (like `"main"`) or a **session ID** from a previous list call.

两个工具都接受**会话 key**（比如 `"main"`）或之前 list 调用返回的**会话 ID**。

> If you need the exact byte-for-byte transcript, inspect the transcript file on disk instead of treating `sessions_history` as a raw dump.

需要逐字节精确的 transcript 时，直接看磁盘上的 transcript 文件，不要把 `sessions_history` 当原始 dump。

---

> ## Sending cross-session messages

## 跨会话发消息

> `sessions_send` delivers a message to another session and optionally waits for the response:
>
> * **Fire-and-forget:** set `timeoutSeconds: 0` to enqueue and return immediately.
> * **Wait for reply:** set a timeout and get the response inline.

`sessions_send` 给另一个会话送消息，可选等待响应：

- **fire-and-forget**：`timeoutSeconds: 0`，入队后立刻返回。
- **等回复**：设个超时，内联拿到响应。

> Thread-scoped chat sessions, such as Slack or Discord keys ending in `:thread:<id>`, are not valid `sessions_send` targets. Use the parent channel session key for inter-agent coordination so tool-routed messages do not appear inside an active human-facing thread.

按 thread 作用域的聊天会话（比如以 `:thread:<id>` 结尾的 Slack 或 Discord key）不是合法的 `sessions_send` 目标。agent 之间协调要用父通道会话 key，避免工具路由的消息出现在面向人的活跃 thread 里。

> Messages and A2A follow-up replies are marked as inter-session data in the receiving prompt (`[Inter-session message ... isUser=false]`) and in transcript provenance. The receiving agent should treat them as tool-routed data, not as a direct end-user-authored instruction.

消息和 A2A 跟进回复在接收侧 prompt 里被标记为跨会话数据（`[Inter-session message ... isUser=false]`），在 transcript 来源标注里也是。接收方 agent 应当把它们当作工具路由的数据，不是用户直接发的指令。

> After the target responds, OpenClaw can run a **reply-back loop** where the agents alternate messages (up to `session.agentToAgent.maxPingPongTurns`, range 0-20, default 5). The target agent can reply `REPLY_SKIP` to stop early.

目标响应后，OpenClaw 可以跑一个**回包循环**，agent 交替发消息（最多 `session.agentToAgent.maxPingPongTurns` 轮，范围 0-20，默认 5）。目标 agent 可以回 `REPLY_SKIP` 提前停止。

---

> ## Status and orchestration helpers

## 状态和编排辅助

> `session_status` is the lightweight `/status`-equivalent tool for the current or another visible session. It reports usage, time, model/runtime state, and linked background-task context when present. Like `/status`, it can backfill sparse token/cache counters from the latest transcript usage entry, and `model=default` clears a per-session override. Use `sessionKey="current"` for the caller's current session; visible client labels such as `openclaw-tui` are not session keys.

`session_status` 是 `/status` 的轻量工具版，用于当前会话或另一个可见会话。它报告用量、时间、模型 / 运行时状态，以及（存在时）关联的后台任务上下文。和 `/status` 一样，它能从最新的 transcript usage 条目回填稀疏的 token / 缓存计数；`model=default` 清掉按会话的覆盖。当前会话用 `sessionKey="current"`；可见的客户端标签（如 `openclaw-tui`）不是会话 key。

> `sessions_yield` intentionally ends the current turn so the next message can be the follow-up event you are waiting for. Use it after spawning sub-agents when you want completion results to arrive as the next message instead of building poll loops.

`sessions_yield` 刻意结束当前轮次，让下一条消息成为你等的那个后续事件。spawn 完 sub-agent 后，想让完成结果作为下一条消息送达、不用搭轮询循环时用它。

> `subagents` is the control-plane helper for already spawned OpenClaw sub-agents. It supports:
>
> * `action: "list"` to inspect active/recent runs
> * `action: "steer"` to send follow-up guidance to a running child
> * `action: "kill"` to stop one child or `all`

`subagents` 是已经 spawn 出的 OpenClaw sub-agent 的控制面助手。支持：

- `action: "list"`：查看活跃 / 近期运行
- `action: "steer"`：给运行中的子 agent 发后续指引
- `action: "kill"`：停掉一个子 agent，或者 `all` 全停

---

> ## Spawning sub-agents

## Spawn sub-agent

> `sessions_spawn` creates an isolated session for a background task by default. It is always non-blocking -- it returns immediately with a `runId` and `childSessionKey`. Native sub-agent runs receive the delegated task in the child session's first visible `[Subagent Task]` message, while the system prompt carries only sub-agent runtime rules and routing context.

`sessions_spawn` 默认为后台任务建一个隔离会话。始终非阻塞 —— 立刻返回 `runId` 和 `childSessionKey`。原生 sub-agent 运行在子会话的第一条可见 `[Subagent Task]` 消息里收到委派的任务；系统提示词只承载 sub-agent 运行时规则和路由上下文。

> Key options:
>
> * `runtime: "subagent"` (default) or `"acp"` for external harness agents.
> * `model` and `thinking` overrides for the child session.
> * `thread: true` to bind the spawn to a chat thread (Discord, Slack, etc.).
> * `sandbox: "require"` to enforce sandboxing on the child.
> * `context: "fork"` for native sub-agents when the child needs the current requester transcript; omit it or use `context: "isolated"` for a clean child. Thread-bound native sub-agents default to `context: "fork"` unless `threadBindings.defaultSpawnContext` says otherwise.

关键选项：

- `runtime: "subagent"`（默认）或 `"acp"`（外部 harness agent）。
- 子会话的 `model` 和 `thinking` 覆盖。
- `thread: true` 把 spawn 绑到聊天 thread（Discord、Slack 等）。
- `sandbox: "require"` 强制子会话进沙盒。
- 原生 sub-agent 时，子需要当前请求者的 transcript 就用 `context: "fork"`；省略或写 `context: "isolated"` 让子会话干净。绑定 thread 的原生 sub-agent 默认 `context: "fork"`，除非 `threadBindings.defaultSpawnContext` 改了。

> Default leaf sub-agents do not get session tools. When `maxSpawnDepth >= 2`, depth-1 orchestrator sub-agents additionally receive `sessions_spawn`, `subagents`, `sessions_list`, and `sessions_history` so they can manage their own children. Leaf runs still do not get recursive orchestration tools.

默认叶子 sub-agent 不拿会话工具。`maxSpawnDepth >= 2` 时，深度 1 的 orchestrator sub-agent 会额外拿到 `sessions_spawn`、`subagents`、`sessions_list`、`sessions_history`，让它们管理自己的子。叶子运行仍然拿不到递归编排工具。

> After completion, an announce step posts the result to the requester's channel. Completion delivery preserves bound thread/topic routing when available, and if the completion origin only identifies a channel OpenClaw can still reuse the requester session's stored route (`lastChannel` / `lastTo`) for direct delivery.

完成后会有个 announce 步骤把结果发到请求方的通道。完成投递在可用时保留绑定的 thread / topic 路由；完成来源只能定位到通道时，OpenClaw 仍能复用请求方会话已存的路由（`lastChannel` / `lastTo`）做直接投递。

> For ACP-specific behavior, see [ACP Agents](/tools/acp-agents).

ACP 专属行为见 [ACP Agents](/tools/acp-agents)。

---

> ## Visibility

## 可见性

> Session tools are scoped to limit what the agent can see:

会话工具按作用域限制 agent 能看到什么：

> | Level   | Scope                                    |
> | ------- | ---------------------------------------- |
> | `self`  | Only the current session                 |
> | `tree`  | Current session + spawned sub-agents     |
> | `agent` | All sessions for this agent              |
> | `all`   | All sessions (cross-agent if configured) |

| 等级    | 作用域                                  |
| ------- | --------------------------------------- |
| `self`  | 仅当前会话                              |
| `tree`  | 当前会话 + spawn 出的 sub-agent         |
| `agent` | 该 agent 的所有会话                     |
| `all`   | 所有会话（如配置允许跨 agent）          |

> Default is `tree`. Sandboxed sessions are clamped to `tree` regardless of config.

默认 `tree`。沙盒会话不论配置如何都钳到 `tree`。

---

> ## Further reading

## 进一步阅读

> * [Session Management](/concepts/session) -- routing, lifecycle, maintenance
> * [ACP Agents](/tools/acp-agents) -- external harness spawning
> * [Multi-agent](/concepts/multi-agent) -- multi-agent architecture
> * [Gateway Configuration](/gateway/configuration) -- session tool config knobs

- [会话管理](/concepts/session)：路由、生命周期、维护
- [ACP Agents](/tools/acp-agents)：外部 harness spawn
- [多 agent](/concepts/multi-agent)：多 agent 架构
- [Gateway 配置](/gateway/configuration)：会话工具配置开关

---

> ## Related

## 相关

> * [Session management](/concepts/session)
> * [Session pruning](/concepts/session-pruning)

- [会话管理](/concepts/session)
- [会话裁剪](/concepts/session-pruning)
