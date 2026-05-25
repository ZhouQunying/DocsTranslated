# Inferred commitments

> Commitments are short-lived follow-up memories. When enabled, OpenClaw can
> notice that a conversation created a future check-in opportunity and remember
> to bring it back later.

跟进事项(commitment)是短期的"跟进备忘"。开启之后,OpenClaw 能察觉到一次对话里冒出了"将来值得回访一下"的机会,并把它记下,稍后再提起来。

> Examples:
>
> - You mention an interview tomorrow. OpenClaw may check in afterward.
> - You say you are exhausted. OpenClaw may ask later whether you slept.
> - The agent says it will follow up after something changes. OpenClaw may track
>   that open loop.

举几个例子:

- 你提到明天有面试,OpenClaw 事后可能会回头问一句。
- 你说自己累垮了,OpenClaw 过会儿可能问你睡了没。
- agent 说"等某件事变了我再来跟进",OpenClaw 可能就把这条没结掉的事跟住。

> Commitments are not durable facts like `MEMORY.md`, and they are not exact
> reminders. They sit between memory and automation: OpenClaw remembers a
> conversation-bound obligation, then heartbeat delivers it when it is due.

跟进事项不是 `MEMORY.md` 里那种长期事实,也不是按精确时间提醒。它夹在"记忆"和"自动化"中间:OpenClaw 记下这条绑在对话上的待办,等到点了由心跳投递。

## 开启跟进事项

> Commitments are off by default. Enable them in config:

跟进事项默认关闭。在配置里打开:

```bash
openclaw config set commitments.enabled true
openclaw config set commitments.maxPerDay 3
```

> Equivalent `openclaw.json`:

等价的 `openclaw.json`:

```json
{
  "commitments": {
    "enabled": true,
    "maxPerDay": 3
  }
}
```

> `commitments.maxPerDay` limits how many inferred follow-ups can be delivered
> per agent session in a rolling day. The default is `3`.

`commitments.maxPerDay` 限制一个 agent 会话在滚动 24 小时内能投递多少条推断式跟进。默认 `3`。

## 怎么工作的

> After an agent reply, OpenClaw may run a hidden background extraction pass in a
> separate context. That pass looks only for inferred follow-up commitments. It
> does not write into the visible conversation and it does not ask the main agent
> to reason about the extraction.

agent 回复完之后,OpenClaw 可能在一个独立上下文里悄悄跑一次后台抽取。这一次只找"值得后续跟进的事项",不会写到用户能看到的对话里,也不让主 agent 参与这次抽取的推理。

> When it finds a high-confidence candidate, OpenClaw stores a commitment with:
>
> - the agent id
> - the session key
> - the original channel and delivery target
> - a due window
> - a short suggested check-in
> - non-instructional metadata for heartbeat to decide whether to send it

抽到高置信度的候选时,OpenClaw 把这条跟进事项存起来,带上:

- agent id
- 会话 key
- 原通道和投递目标
- 到期窗口
- 一句简短的建议回访话
- 给心跳判断要不要发的非指令型元数据

> Delivery happens through heartbeat. When a commitment becomes due, heartbeat
> adds the commitment to the heartbeat turn for the same agent and channel scope.
> The model can send one natural check-in or reply `HEARTBEAT_OK` to dismiss it.
> If heartbeat is configured with `target: "none"`, due commitments remain
> internal and do not send external check-ins. Commitment delivery prompts do not
> replay the original conversation text, and due commitment heartbeat turns run
> without OpenClaw tools.

投递走心跳。一条跟进事项到期时,心跳会把它放进同一个 agent 和通道作用域下的心跳轮次。模型可以发一句自然的回访,也可以回 `HEARTBEAT_OK` 把它驳掉。心跳的 `target` 设成 `"none"` 时,到期的跟进事项只停留在内部,不会真的对外发回访。投递跟进事项的 prompt 不会回放原始对话文本,跟进的心跳轮次也不带 OpenClaw 工具。

> OpenClaw never delivers an inferred commitment immediately after writing it.
> The due time is clamped to at least one heartbeat interval after the commitment
> is created, so the follow-up cannot echo back in the same moment it was
> inferred.

OpenClaw 永远不会在写下一条推断跟进事项的同一刻就把它发出去。到期时间会被强制推到"创建之后至少一个心跳周期",所以你不会在刚被 OpenClaw 推断出之后立刻收到回声般的回访。

## 作用域

> Commitments are scoped to the exact agent and channel context where they were
> created. A follow-up inferred while talking to one agent in Discord is not
> delivered by another agent, another channel, or an unrelated session.

跟进事项严格绑在"创建它时的那个 agent 和通道上下文"。在 Discord 跟某个 agent 聊出来的跟进,不会换个 agent、换个通道,或者跑到无关的会话里去投递。

> This scope is part of the feature. Natural check-ins should feel like the same
> conversation continuing, not like a global reminder system.

这种作用域是特性的一部分,不是限制。自然的回访应该让你觉得"是刚才那段对话继续",而不是"一个全局提醒系统在弹"。

## 跟进事项 vs 提醒

> | Need                                            | Use                                      |
> | ----------------------------------------------- | ---------------------------------------- |
> | "Remind me at 3 PM"                             | [Scheduled tasks](/automation/cron-jobs) |
> | "Ping me in 20 minutes"                         | [Scheduled tasks](/automation/cron-jobs) |
> | "Run this report every weekday"                 | [Scheduled tasks](/automation/cron-jobs) |
> | "I have an interview tomorrow"                  | Commitments                              |
> | "I was up all night"                            | Commitments                              |
> | "Follow up if I do not answer this open thread" | Commitments                              |

| 需求                                  | 用什么                                 |
| ------------------------------------- | -------------------------------------- |
| "下午 3 点提醒我"                     | [定时任务](/automation/cron-jobs)      |
| "20 分钟后叫我"                       | [定时任务](/automation/cron-jobs)      |
| "每个工作日跑一遍这份报表"            | [定时任务](/automation/cron-jobs)      |
| "我明天有面试"                        | 跟进事项                               |
| "我熬了一晚上"                        | 跟进事项                               |
| "如果我没回这条开着的话题再跟我一下" | 跟进事项                               |

> Exact user requests already belong to the scheduler path. Commitments are only
> for inferred follow-ups: the moments where the user did not ask for a reminder,
> but the conversation clearly created a useful future check-in.

用户明确说出的请求走调度器那条路。跟进事项只管"推断出来的跟进":用户没主动让你提醒,但对话明显留下了一个值得将来回访的口子。

## 管理跟进事项

> Use the CLI to inspect and clear stored commitments:

用 CLI 看和清理已经存下的跟进事项:

```bash
openclaw commitments
openclaw commitments --all
openclaw commitments --agent main
openclaw commitments --status snoozed
openclaw commitments dismiss cm_abc123
```

> See [`openclaw commitments`](/cli/commitments) for the command reference.

命令参考见 [`openclaw commitments`](/cli/commitments)。

## 隐私和成本

> Commitment extraction uses an LLM pass, so enabling it adds background model
> usage after eligible turns. The pass is hidden from the user-visible
> conversation, but it can read the recent exchange needed to decide whether a
> follow-up exists.

跟进事项的抽取要跑一次 LLM,所以开启之后,符合条件的轮次后面会有额外的后台模型用量。这次跑对用户的可见对话是隐藏的,但它确实会读最近的一段对话以判断要不要写跟进。

> Stored commitments are local OpenClaw state. They are operational memory, not
> long-term memory. Disable the feature with:

已存的跟进事项是本地 OpenClaw 状态,属于运营记忆,不是长期记忆。关闭功能:

```bash
openclaw config set commitments.enabled false
```

## 排障

> If expected follow-ups are not appearing:
>
> - Confirm `commitments.enabled` is `true`.
> - Check `openclaw commitments --all` for pending, dismissed, snoozed, or expired
>   records.
> - Make sure heartbeat is running for the agent.
> - Check whether `commitments.maxPerDay` has already been reached for that
>   agent session.
> - Remember that exact reminders are skipped by commitment extraction and should
>   appear under [scheduled tasks](/automation/cron-jobs) instead.

预期的跟进没出现时:

- 确认 `commitments.enabled` 是 `true`。
- 用 `openclaw commitments --all` 看一下挂起、已驳回、已暂缓、已过期的记录。
- 确认那个 agent 的心跳在跑。
- 看那个 agent 会话的 `commitments.maxPerDay` 是不是已经满了。
- 记住:精确提醒会被跟进事项抽取直接跳过,应该走 [定时任务](/automation/cron-jobs)。

## 相关

> - [Memory overview](/concepts/memory)
> - [Active memory](/concepts/active-memory)
> - [Heartbeat](/gateway/heartbeat)
> - [Scheduled tasks](/automation/cron-jobs)
> - [`openclaw commitments`](/cli/commitments)
> - [Configuration reference](/gateway/configuration-reference#commitments)

- [记忆总览](/concepts/memory)
- [Active memory](/concepts/active-memory)
- [心跳](/gateway/heartbeat)
- [定时任务](/automation/cron-jobs)
- [`openclaw commitments`](/cli/commitments)
- [配置参考](/gateway/configuration-reference#commitments)
