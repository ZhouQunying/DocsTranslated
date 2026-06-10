# Steer

## 架构精读

> 跳过不影响阅读翻译正文。

### Agent 正在跑,你突然想说"换个方向"——消息怎么注入？

正常消息是"排队等 agent 闲了再处理"。但有时候 agent 正在做的事你想实时纠正——比如它在写一个大 patch,你想说"别改测试文件"。

`/steer` 做的是"热注入"：把你的指导语在下一个运行时边界点塞给模型。不等 agent 跑完,不开新轮次,就是"往正在跑的这一轮里插一句话"。

跟副驾驶一个意思：司机在开,你说"前面右转"。不是让他停车重新规划路线,是在行驶中微调方向。

安全设计：注入不了(运行时不支持、会话空闲)就自动降级成普通消息。不会丢,也不会静默失败。

---

> `/steer` first tries to send guidance to an already-active run. It is for
> "adjust this run while it is still working" moments. If the current runtime
> cannot accept steering, OpenClaw sends the message as a normal prompt instead
> of dropping it.

`/steer` 先尝试把指导发给已经活跃的运行。它用在"这次运行还在跑时调整方向"的时刻。当前运行时不能接受 steering 时,OpenClaw 把消息当普通 prompt 发,而不是丢掉。

## 当前会话

> Use top-level `/steer` to target the active run for the current session:

用顶层 `/steer` 指向当前会话的活跃运行:

```text
/steer prefer the smaller patch and keep the tests focused
/tell summarize before making the next tool call
```

> Behavior:

行为:

> - Targets only the current session's active run.
> - Works independently of the session's `/queue` mode.
> - Starts a normal turn with the same message when the session is idle or the active run cannot accept steering.
> - Uses the active runtime's steering path, so the model sees the guidance at the next supported runtime boundary.

- 只针对当前会话的活跃运行。
- 不受会话的 `/queue` 模式影响。
- 会话空闲或活跃运行不能接受 steering 时,用同一消息启动普通轮次。
- 走活跃运行时的 steering 路径,模型在下一个支持的运行时边界看到指导。

## Steer vs queue

> `/queue steer` makes normal inbound messages try to steer the active run when they arrive while a run is active. `/steer <message>` is an explicit command that tries to inject that command's message into the active run at the next supported runtime boundary, regardless of the stored `/queue` setting.

`/queue steer` 让正常入站消息在运行活跃时尝试 steer。`/steer <消息>` 是显式命令,不管存储的 `/queue` 设置,都尝试在下一个支持的运行时边界注入。

> When that injection is not available, the command prefix is stripped and `<message>` continues as a normal prompt.

注入不可用时,命令前缀剥掉,`<消息>` 继续当普通 prompt。

> Use:

什么时候用什么:

> - `/steer <message>` when you want to guide the active run right now.
> - `/queue steer` when you want future normal messages to steer active runs by default.
> - `/queue collect` or `/queue followup` when future normal messages should wait for a later turn instead of steering the active run.
> - `/queue interrupt` when the newest message should replace the active run instead of steering it.

- `/steer <消息>` —— 你现在就想指导活跃运行。
- `/queue steer` —— 你想让未来的普通消息默认 steer 活跃运行。
- `/queue collect` 或 `/queue followup` —— 未来的普通消息应该等下一轮,而不是 steer 活跃运行。
- `/queue interrupt` —— 最新消息应该替换活跃运行,而不是 steer 它。

> For queue modes and steering boundaries, see Command queue and Steering queue.

队列模式和 steering 边界见[命令队列](/concepts/queue)和 [Steering 队列](/concepts/queue-steering)。

## Sub-agents

> Top-level `/steer` targets the current session's active run. Sub-agents report back to their parent/requester session; `/subagents` is for visibility only.

顶层 `/steer` 针对当前会话的活跃运行。子 agent 向父 / 请求者会话报告;`/subagents` 只用于查看。

## ACP 会话

> Use `/acp steer` when the target is an ACP harness session:

目标是 ACP harness 会话时用 `/acp steer`:

```text
/acp steer --session agent:main:acp:codex tighten the repro
```

> See ACP agents for ACP session selection and runtime behavior.

ACP 会话选择和运行时行为见 [ACP agents](/tools/acp-agents)。

## 相关

> - Slash commands
> - Command queue
> - Steering queue
> - Sub-agents

- [Slash 命令](/tools/slash-commands)
- [命令队列](/concepts/queue)
- [Steering 队列](/concepts/queue-steering)
- [Sub-agents](/tools/subagents)
