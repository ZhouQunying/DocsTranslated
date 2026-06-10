# Goal

## 架构精读

> 跳过不影响阅读翻译正文。

### Agent 跑了 50 轮对话——它还记得自己在干嘛吗？

长会话最大的问题不是 token 限制,是"目标漂移"。Agent 回着回着就偏了,用户得反复提醒"别忘了我们在修那个 PR"。

Goal 的设计：给会话钉一个持久目标。它不是任务队列,不是 cron,不是后台进程——就是一个"北极星"。Agent 和用户都能看到,跨重启存活,TUI 底部一直显示。

关键约束：Agent **不能**自己清除、暂停、恢复或替换目标。它只能报告"做完了"或"卡住了"。清除权在人手里。这是一个信任边界设计：agent 执行,人类掌舵。

Token budget 是另一个巧妙设计：不是计费上限,是"这件事最多花多少 token"的护栏。超了自动停,不删目标,人类决定是继续还是换方向。

---

> A **goal** is one durable objective attached to the current OpenClaw session.
> It gives the agent and the operator a shared target for long-running work,
> without turning that target into a background task, reminder, cron job, or
> standing order.

**目标(goal)** 是附着在当前 OpenClaw 会话上的一个持久目标。它给 agent 和操作者一个共同的靶心,用于长期任务,但不会变成后台任务、提醒、cron 或常驻指令。

> Goals are session state. They move with the session key, survive process
> restarts, show up in `/goal`, are available to the model through the goal
> tools, and appear in the TUI footer when the active session has one.

Goal 是会话状态。它跟着 session key 走,进程重启后存活,出现在 `/goal` 里,模型通过 goal 工具能看到,活跃会话有 goal 时 TUI 底栏会显示。

## 快速开始

> Set a goal:

设一个目标:

```text
/goal start get CI green for PR 87469 and push the fix
```

> Check it:

检查:

```text
/goal
```

> Pause it when work is intentionally waiting:

工作主动等待时暂停:

```text
/goal pause waiting for CI
```

> Resume it:

恢复:

```text
/goal resume
```

> Mark it complete:

标记完成:

```text
/goal complete pushed and verified
```

> Clear it:

清除:

```text
/goal clear
```

## 什么时候用 Goal

> Use a goal when a session has a concrete outcome that should remain visible
> across many turns:

会话有一个需要跨多轮一直可见的具体结果时用 goal:

> - A PR closeout: fix, verify, autoreview, push, and open or update the PR.
> - A debug run: reproduce the bug, identify the owning surface, patch, and prove the fix.
> - A docs pass: read the relevant docs, write the new page, cross-link it, and verify the docs build.
> - A maintenance task: inspect current state, make bounded changes, run the right checks, and report what changed.

- PR 收尾:修、验、自动审查、推、开或更新 PR。
- 调试跑:复现 bug、定位归属面、打补丁、证明修复。
- 文档跑:读相关文档、写新页、交叉链接、验构建。
- 维护任务:检查当前状态、做有界修改、跑正确检查、报告改了什么。

> A goal is not a task queue. Use Task Flow, tasks, cron jobs, or standing orders
> when work should run detached, repeat on a schedule, fan out into managed
> sub-work, or persist as a policy.

Goal 不是任务队列。工作需要脱离运行、按计划重复、展开成受管子任务、或作为策略持久化时,用 [Task Flow](/automation/taskflow)、[任务](/automation/tasks)、[cron jobs](/automation/cron-jobs) 或[常驻指令](/automation/standing-orders)。

## 命令参考

> `/goal` without arguments prints the current goal summary:

不带参数的 `/goal` 打印当前目标摘要:

```text
Goal
Status: active
Objective: get CI green for PR 87469 and push the fix
Tokens used: 12k
Token budget: 12k/50k

Commands: /goal pause, /goal complete, /goal clear
```

> Commands:

命令:

> - `/goal` or `/goal status` shows the current goal.
> - `/goal start <objective>` creates a new goal for the current session.
> - `/goal set <objective>` and `/goal create <objective>` are aliases for `start`.
> - `/goal pause [note]` pauses an active goal.
> - `/goal resume [note]` resumes a paused, blocked, usage-limited, or budget-limited goal.
> - `/goal complete [note]` marks the goal achieved.
> - `/goal done [note]` is an alias for `complete`.
> - `/goal block [note]` marks the goal blocked.
> - `/goal blocked [note]` is an alias for `block`.
> - `/goal clear` removes the goal from the session.

- `/goal` 或 `/goal status` 查看当前目标。
- `/goal start <目标>` 为当前会话创建新目标。
- `/goal set <目标>` 和 `/goal create <目标>` 是 `start` 的别名。
- `/goal pause [备注]` 暂停活跃目标。
- `/goal resume [备注]` 恢复已暂停、已阻塞、受用量限制、或受预算限制的目标。
- `/goal complete [备注]` 标记目标已达成。
- `/goal done [备注]` 是 `complete` 的别名。
- `/goal block [备注]` 标记目标被阻塞。
- `/goal blocked [备注]` 是 `block` 的别名。
- `/goal clear` 从会话中移除目标。

> Only one goal can exist on a session at a time. Starting a second goal fails until the current one is cleared.

一个会话同时只能有一个目标。不清掉当前的就开不了第二个。

## 状态

> Goals use a small status set:

Goal 用一组小状态集:

> - `active`: the session is pursuing the goal.
> - `paused`: the operator paused the goal; `/goal resume` makes it active again.
> - `blocked`: the agent or operator reported a real blocker; `/goal resume` makes it active again when new information or state is available.
> - `budget_limited`: the configured token budget was reached; `/goal resume` restarts pursuit from the same objective.
> - `usage_limited`: reserved for usage-limit stop states; `/goal resume` restarts pursuit when allowed.
> - `complete`: the goal was achieved. Complete goals are terminal; use `/goal clear` before starting another goal.

- `active`:会话正在追求目标。
- `paused`:操作者暂停了;`/goal resume` 恢复。
- `blocked`:agent 或操作者报告了真实阻塞;有新信息或状态后 `/goal resume` 恢复。
- `budget_limited`:到了配置的 token 预算;`/goal resume` 从同一目标重新开始追求。
- `usage_limited`:保留给用量限制停止状态;允许后 `/goal resume` 重新开始。
- `complete`:目标已达成。完成的目标是终态;再开一个之前先 `/goal clear`。

> `/new` and `/reset` clear the current session goal because they intentionally start fresh session context.

`/new` 和 `/reset` 会清掉当前会话目标,因为它们本意就是从头开始。

## Token 预算

> Goals can have an optional positive token budget. The budget is stored with the goal and measured from the session's fresh token count at creation time.

Goal 可以有一个可选的正数 token 预算。预算随 goal 存储,从创建时会话的新鲜 token 计数开始计量。

> If the current session only has stale or unknown token usage when the goal starts, OpenClaw waits for the next fresh session token snapshot and uses that as the baseline, so tokens spent before the goal existed are not charged to the goal.

如果 goal 启动时会话只有过时或未知的 token 用量,OpenClaw 等下一次新鲜的会话 token 快照再把它作为基线——goal 存在之前花的 token 不算在 goal 头上。

> When token usage reaches the budget, the goal changes to `budget_limited`. This does not delete the goal or erase the objective. It tells the operator and the agent that the goal is no longer actively being pursued until it is resumed or cleared.

Token 用量到了预算时,goal 变成 `budget_limited`。这不会删目标也不会擦掉目标文字。它告诉操作者和 agent:在恢复或清除之前,不再主动追求这个目标了。

> Token budgets are a session-goal guardrail, not a billing cap. Provider quota, cost reporting, and context-window behavior still use the normal OpenClaw usage and model controls.

Token 预算是会话目标的护栏,不是计费上限。Provider 配额、费用报告、上下文窗口行为仍然走 OpenClaw 正常的用量和模型控制。

## 模型工具

> OpenClaw exposes three core goal tools to agent harnesses:

OpenClaw 给 agent harness 暴露三个核心 goal 工具:

> - `get_goal`: read the current session goal, including status, objective, token usage, and token budget.
> - `create_goal`: create a goal only when the user, system, or developer instructions explicitly request one. It fails if the session already has a goal.
> - `update_goal`: mark the goal `complete` or `blocked`.

- `get_goal`:读取当前会话目标,含状态、目标文字、token 用量和预算。
- `create_goal`:只有用户、系统或开发者指令显式要求时才创建目标。会话已有目标时失败。
- `update_goal`:把目标标为 `complete` 或 `blocked`。

> The model cannot silently pause, resume, clear, or replace a goal. Those are operator/session controls through `/goal` and reset commands. This keeps the agent from quietly moving the target while preserving a clean path for the agent to report achievement or a genuine blocker.

模型**不能**悄悄暂停、恢复、清除、替换目标。那些是操作者通过 `/goal` 和 reset 命令的会话控制。这防止 agent 偷偷挪靶心,同时保留 agent 报告达成或真实阻塞的干净路径。

> The `update_goal` tool should mark a goal `complete` only when the objective is actually achieved. It should mark a goal `blocked` only when the same blocking condition has repeated and the agent cannot make meaningful progress without new user input or an external-state change.

`update_goal` 只应在目标**确实**达成时标 `complete`。只应在同一阻塞条件反复出现、且没有新用户输入或外部状态变化就无法有意义推进时标 `blocked`。

## TUI

> The TUI keeps the active session's goal visible in the footer next to the agent, session, model, run controls, and token counts.

TUI 在底栏的 agent、会话、模型、运行控件、token 计数旁边一直显示活跃会话的目标。

> Footer examples:

底栏例子:

> - `Pursuing goal (12k/50k)` for an active goal with a token budget.
> - `Goal paused (/goal resume)` for a paused goal.
> - `Goal blocked (/goal resume)` for a blocked goal.
> - `Goal hit usage limits (/goal resume)` for a usage-limited goal.
> - `Goal unmet (50k/50k)` for a budget-limited goal.
> - `Goal achieved (42k)` for a completed goal.

- `Pursuing goal (12k/50k)` —— 有 token 预算的活跃目标。
- `Goal paused (/goal resume)` —— 已暂停的目标。
- `Goal blocked (/goal resume)` —— 已阻塞的目标。
- `Goal hit usage limits (/goal resume)` —— 受用量限制的目标。
- `Goal unmet (50k/50k)` —— 受预算限制的目标。
- `Goal achieved (42k)` —— 已完成的目标。

> The footer is intentionally compact. Use `/goal` for the full objective, note, token budget, and available commands.

底栏故意紧凑。用 `/goal` 看完整目标、备注、token 预算和可用命令。

## 通道行为

> The `/goal` command works in command-capable OpenClaw sessions, including the TUI and chat surfaces that permit text commands. Goal state is attached to the session key, not the transport. If two surfaces use the same session, they see the same goal.

`/goal` 命令在支持命令的 OpenClaw 会话里工作,包括 TUI 和允许文本命令的聊天面。Goal 状态挂在 session key 上,不在传输上。两个面用同一会话就看到同一目标。

> Goal state is not a delivery directive. It does not force replies through a channel, change queue behavior, approve tools, or schedule work.

Goal 状态不是投递指令。它不会强制回复走某个通道、改变队列行为、批准工具、或调度工作。

## 故障排查

> `Goal error: goal already exists` means the session already has a goal. Use `/goal` to inspect it, `/goal complete` if it is done, or `/goal clear` before starting a different objective.

`Goal error: goal already exists` —— 会话已有目标。用 `/goal` 检查,做完了 `/goal complete`,要换方向就 `/goal clear`。

> `Goal error: goal not found` means the session has no goal yet. Start one with `/goal start <objective>`.

`Goal error: goal not found` —— 还没目标。`/goal start <目标>` 开一个。

> `Goal error: goal is already complete` means the goal is terminal. Clear it before starting or resuming another objective.

`Goal error: goal is already complete` —— 目标已终态。再开或恢复之前先清掉。

> If token usage looks like `0` or stale, the active session may not have a fresh token snapshot yet. Usage refreshes as OpenClaw records session usage and transcript-derived totals.

Token 用量显示 `0` 或过时的话,活跃会话可能还没拿到新鲜 token 快照。随着 OpenClaw 记录会话用量和转录推导的总量,用量会刷新。

## 相关

> - Slash commands
> - TUI
> - Session tool
> - Compaction
> - Task Flow
> - Standing orders

- [Slash 命令](/tools/slash-commands)
- [TUI](/web/tui)
- [会话工具](/concepts/session-tool)
- [压缩](/concepts/compaction)
- [Task Flow](/automation/taskflow)
- [常驻指令](/automation/standing-orders)
