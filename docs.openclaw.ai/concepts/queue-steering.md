# Steering queue

> When a normal prompt arrives while a session run is already streaming, OpenClaw tries to send that prompt into the active runtime by default when the queue mode is `steer`. No config entry and no queue directive are required for that default behavior. OpenClaw and the native Codex app-server harness implement the delivery details differently.

会话运行已经在流式时常规 prompt 到达，队列模式是 `steer` 时 OpenClaw 默认尝试把这个 prompt 送进活跃 runtime。这个默认行为不需要配置或队列指令。OpenClaw 和原生 Codex app-server harness 在投递细节上各不相同。

---

> ## Runtime boundary

## 运行时边界

> Steering does not interrupt a tool call that is already running. OpenClaw checks for queued steering messages at model boundaries:

steering 不会中断已经在跑的工具调用。OpenClaw 在模型边界检查排队的 steering 消息：

> 1. The assistant asks for tool calls.
> 2. OpenClaw executes the current assistant message's tool-call batch.
> 3. OpenClaw emits the turn end event.
> 4. OpenClaw drains queued steering messages.
> 5. OpenClaw appends those messages as user messages before the next LLM call.

1. assistant 请求工具调用。
2. OpenClaw 执行当前 assistant 消息的工具调用批次。
3. OpenClaw 发出 turn end 事件。
4. OpenClaw 消费排队的 steering 消息。
5. 在下一次 LLM 调用之前，OpenClaw 把这些消息作为 user 消息追加上去。

> This keeps tool results paired with the assistant message that requested them, then lets the next model call see the latest user input.

这样工具结果跟请求它们的 assistant 消息保持成对，下一次模型调用看到最新的用户输入。

> The native Codex app-server harness exposes `turn/steer` instead of OpenClaw runtime's internal steering queue. OpenClaw batches queued prompts for the configured quiet window, then sends a single `turn/steer` request with all collected user input in arrival order.

原生 Codex app-server harness 暴露的是 `turn/steer`，而不是 OpenClaw runtime 内部的 steering 队列。OpenClaw 在配置的静默窗口内合并排队 prompt，然后按到达顺序把所有收集到的用户输入打包成一次 `turn/steer` 请求。

> Codex review and manual compaction turns reject same-turn steering. When a runtime cannot accept steering in `steer` mode, OpenClaw waits for the active run to finish before starting the prompt.

Codex review 和手动压缩轮次拒绝同轮 steering。`steer` 模式下 runtime 不能接受 steering 时，OpenClaw 等活跃运行结束才开始处理 prompt。

> This page explains queue-mode steering for normal inbound messages when the mode is `steer`. If the mode is `followup` or `collect`, normal messages do not enter this steering path; they wait until the active run finishes. For the explicit `/steer <message>` command, see [Steer](/tools/steer).

本页讲模式为 `steer` 时常规接收消息的队列模式 steering。模式是 `followup` 或 `collect` 时，常规消息不进这条 steering 路径；它们等活跃运行结束。显式 `/steer <message>` 命令见 [Steer](/tools/steer)。

---

> ## Modes

## 模式

> | Mode        | Active-run behavior                                    | Later behavior                                                                      |
> | ----------- | ------------------------------------------------------ | ----------------------------------------------------------------------------------- |
> | `steer`     | Steers the prompt into the active runtime when it can. | Waits for the active run to finish if steering is unavailable.                      |
> | `followup`  | Does not steer.                                        | Runs queued messages later after the active run ends.                               |
> | `collect`   | Does not steer.                                        | Coalesces compatible queued messages into one later turn after the debounce window. |
> | `interrupt` | Aborts the active run instead of steering it.          | Starts the newest message after aborting.                                           |

| 模式        | 活跃运行期间行为                              | 之后行为                                                              |
| ----------- | --------------------------------------------- | --------------------------------------------------------------------- |
| `steer`     | 能时把 prompt steer 进活跃 runtime。          | steering 不可用时等活跃运行结束。                                     |
| `followup`  | 不 steer。                                    | 活跃运行结束后跑排队消息。                                            |
| `collect`   | 不 steer。                                    | 防抖窗口结束后，把兼容的排队消息合并成一个后续轮次。                  |
| `interrupt` | 中止活跃运行，不 steer。                      | 中止后跑最新消息。                                                    |

---

> ## Burst example

## 爆发场景例子

> If four users send messages while the agent is executing a tool call:
>
> * With default behavior, the active runtime receives all four messages in arrival order before its next model decision. OpenClaw drains them at the next model boundary; Codex receives them as one batched `turn/steer`.
> * With `/queue collect`, OpenClaw does not steer. It waits until the active run ends, then creates a followup turn with compatible queued messages after the debounce window.
> * With `/queue interrupt`, OpenClaw aborts the active run and starts the newest message instead of steering.

agent 正在执行一个工具调用时，四个用户发消息：

- 默认行为：活跃 runtime 在它下一次模型决策之前按到达顺序收到四条消息。OpenClaw 在下一个模型边界消费；Codex 把它们作为一条合并的 `turn/steer` 收到。
- `/queue collect`：OpenClaw 不 steer。等活跃运行结束，再在防抖窗口后用兼容的排队消息建一个后续轮次。
- `/queue interrupt`：OpenClaw 中止活跃运行，跑最新消息，不 steer。

---

> ## Scope

## 范围

> Steering always targets the current active session run. It does not create a new session, change the active run's tool policy, or split messages by sender. In multi-user channels, inbound prompts already include sender and route context, so the next model call can see who sent each message.

steering 总是针对当前活跃的会话运行。它不会建新会话、不改活跃运行的工具策略、不按发件人拆分消息。多用户通道里，接收 prompt 已经带了发件人和路由上下文，下一次模型调用能看到每条消息是谁发的。

> Use `followup` or `collect` when you want messages to queue by default instead of steering the active run. Use `interrupt` when the newest prompt should replace the active run.

想让消息默认排队而不是 steer 活跃运行时用 `followup` 或 `collect`。想让最新 prompt 替换活跃运行时用 `interrupt`。

---

> ## Debounce

## 防抖

> `messages.queue.debounceMs` applies to queued `followup` and `collect` delivery. In `steer` mode with the native Codex harness, it also sets the quiet window before sending batched `turn/steer`. For OpenClaw, active steering itself does not use the debounce timer because OpenClaw naturally batches messages until the next model boundary.

`messages.queue.debounceMs` 作用于 `followup` 和 `collect` 的排队投递。在原生 Codex harness 的 `steer` 模式下，它还设置发送合并 `turn/steer` 前的静默窗口。OpenClaw 的活跃 steering 本身不用防抖定时器——OpenClaw 自然地把消息缓冲到下一个模型边界。

---

> ## Related

## 相关

> * [Command queue](/concepts/queue)
> * [Steer](/tools/steer)
> * [Messages](/concepts/messages)
> * [Agent loop](/concepts/agent-loop)

- [命令队列](/concepts/queue)
- [Steer](/tools/steer)
- [消息](/concepts/messages)
- [Agent 循环](/concepts/agent-loop)
