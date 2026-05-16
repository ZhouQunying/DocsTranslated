# Parallel specialist lanes

> Parallel specialist lanes let one Gateway route different chats or rooms to different agents, while keeping the user experience fast. The trick is to treat parallelism as a scarce-resource design problem, not just as "more agents".

并行专家 lane 让一个 Gateway 把不同的聊天或房间路由到不同 agent，同时保持用户体验快速。诀窍是把并行当作"稀缺资源设计问题"来处理，而不是简单地"加更多 agent"。

---

> ## First principles

## 第一性原理

> A specialist lane only improves throughput when it reduces contention for the real bottlenecks:
>
> * **Session locks**: only one run should mutate a given session at a time.
> * **Global model capacity**: all visible chat runs still share provider limits.
> * **Tool capacity**: shell, browser, network, and repository work can be slower than the model turn itself.
> * **Context budget**: long transcripts make every future turn slower and less focused.
> * **Ownership ambiguity**: duplicate agents doing the same job waste capacity.

专家 lane 只有在减少了真正瓶颈上的争用时才能提升吞吐：

- **会话锁**：同一时刻只有一个运行能改某个具体会话。
- **全局模型容量**：所有可见的聊天运行仍共享 provider 上限。
- **工具容量**：shell、浏览器、网络、仓库操作可能比模型轮次本身还慢。
- **上下文预算**：长 transcript 让之后每一轮都更慢、更难聚焦。
- **归属模糊**：多个 agent 干同一件事浪费容量。

> OpenClaw already serializes runs per session and caps global parallelism through the [command queue](/concepts/queue). Specialist lanes add policy on top: which agent owns which work, what stays in chat, and what becomes background work.

OpenClaw 已经按会话串行运行，并通过 [命令队列](/concepts/queue) 限制全局并行。专家 lane 在这之上加策略：哪个 agent 拥有哪份工作、什么留在聊天里、什么变成后台工作。

---

> ## Recommended rollout

## 推荐的推广步骤

> ### Phase 1: lane contracts + background heavy work

### 阶段 1：lane 契约 + 重活后台化

> Give every lane a written contract in its workspace and system prompt:
>
> * **Purpose**: the work this lane owns.
> * **Non-goals**: work it should hand off instead of attempting.
> * **Chat budget**: quick answers stay in chat; long tasks should acknowledge briefly, then run in a background sub-agent or task.
> * **Handoff rule**: when another lane owns the work, say where it should go and provide a compact handoff summary.
> * **Tool-risk rule**: prefer the smallest tool surface that can do the job.

给每条 lane 在它的工作区和系统提示词里写一份契约：

- **职责**：这条 lane 拥有的工作。
- **非目标**：它应该转交、不应自己做的工作。
- **聊天预算**：快速答复留在聊天里；长任务先简短确认，然后丢到后台 sub-agent 或任务里跑。
- **转交规则**：工作归别的 lane 时，说清楚该去哪里，并给一份紧凑的转交摘要。
- **工具风险规则**：优先用能完成工作的最小工具面。

> This is the cheapest phase and fixes most clogging: one coding job no longer turns the research lane into molasses, and each chat keeps its own context clean.

这是成本最低的阶段，能解决大部分堵塞：一项编码任务不再把研究 lane 拖成泥潭，每个聊天保持自己的上下文干净。

> ### Phase 2: priority and concurrency controls

### 阶段 2：优先级与并发控制

> Tune queue and model capacity around the business value of each lane:

围绕每条 lane 的业务价值调队列和模型容量：

> ```json5
> {
>   agents: {
>     defaults: {
>       maxConcurrent: 4,
>       subagents: { maxConcurrent: 8, delegationMode: "prefer" },
>     },
>   },
>   messages: {
>     queue: {
>       mode: "collect",
>       debounceMs: 1000,
>       cap: 20,
>       drop: "summarize",
>     },
>   },
> }
> ```

```json5
{
  agents: {
    defaults: {
      maxConcurrent: 4,
      subagents: { maxConcurrent: 8, delegationMode: "prefer" },
    },
  },
  messages: {
    queue: {
      mode: "collect",
      debounceMs: 1000,
      cap: 20,
      drop: "summarize",
    },
  },
}
```

> Use direct/personal chats and production-ops agents for high-priority work. Let research, drafting, and batch coding move to background tasks when the system is busy.

把私聊 / 个人聊天和生产运维 agent 留给高优先级工作。系统忙时，让研究、起草、批量编码这类工作转到后台任务里。

> ### Phase 3: coordinator / traffic controller

### 阶段 3：协调员 / 流量管理

> Add a small coordinator pattern once multiple lanes are active:
>
> * Track active lane tasks and owners.
> * Detect duplicate requests across groups.
> * Route handoff summaries between lanes.
> * Surface only blockers, completed results, and decisions the human must make.

多条 lane 都活跃后，加一个小型协调员模式：

- 追踪活跃 lane 的任务和负责人。
- 跨群检测重复请求。
- 在 lane 之间路由转交摘要。
- 只把阻塞、完成结果和需要人类拍板的决策露给人。

> Do not start here. A coordinator without lane contracts just coordinates chaos.

不要从这里开始。没有 lane 契约的协调员，只是在协调一团乱。

---

> ## Minimal lane contract template

## 最小 lane 契约模板

> ```md
> # Lane contract
>
> ## Owns
>
> - <job this lane is responsible for>
>
> ## Does not own
>
> - <work to hand off>
>
> ## Chat budget
>
> - Answer quick questions directly.
> - For multi-step, slow, or tool-heavy work: acknowledge briefly, spawn/background
>   the work, then return the result when complete.
>
> ## Handoff
>
> If another lane owns the request, reply with:
>
> - target lane
> - objective
> - relevant context
> - exact next action
>
> ## Tool posture
>
> Use the smallest tool surface that can complete the task. Avoid broad shell or
> network work unless this lane explicitly owns it.
> ```

```md
# Lane contract

## Owns

- <这条 lane 负责的工作>

## Does not own

- <要转交出去的工作>

## Chat budget

- 快速问题直接答。
- 多步、慢或工具密集的工作：先简短确认，然后 spawn / 进入后台跑，
  完成时再把结果返回。

## Handoff

请求归别的 lane 时，回复里写：

- 目标 lane
- 目标动作
- 相关上下文
- 下一步要做的具体动作

## Tool posture

用能完成任务的最小工具面。除非本 lane 显式拥有，否则避免大范围 shell 或网络操作。
```

---

> ## Related

## 相关

> * [Multi-agent routing](/concepts/multi-agent)
> * [Command queue](/concepts/queue)
> * [Sub-agents](/tools/subagents)

- [多 agent 路由](/concepts/multi-agent)
- [命令队列](/concepts/queue)
- [Sub-agents](/tools/subagents)
