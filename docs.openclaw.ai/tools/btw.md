# BTW side questions

## 架构精读

> 跳过不影响阅读翻译正文。

### Agent 正在写代码，你想问一句"这啥意思"——怎么不打断它？

场景：Agent 跑了一个 10 分钟的任务，你中途想问一句"这个变量是什么意思"。如果正常发消息，这条问答就进了会话历史，后续 Agent 调模型时带着它当上下文——上下文被污染了。如果等 Agent 跑完再问，你可能忘了。

核心直觉：**临时的 fork**。拍个快照、跑个独立查询、答完就扔。主历史线完全不受影响。

### 怎么做到"看得见但不存在"？

关键在 Gateway 的事件类型分离。普通回复走 `chat` 事件，客户端看到了会存进历史。BTW 的回复走 `chat.side_result`——客户端照样显示给你，但不往 `chat.history` 里写。重新加载后它就消失了。

跟数据库里的 dirty read 是一个思路：你能看到还没提交的数据，但它不会被持久化。

### Codex 场景的更复杂变体

普通会话直接跑一次独立 LLM 调用就行。但 Codex 有 OAuth、线程上下文、原生工具这些状态。直接跑个裸调用会丢掉这些。

所以 Codex 场景的做法是**线程 fork**：从当前活跃线程派生一个临时子线程。子线程继承了权限和工具接口，但加了护栏——"不要把继承的父线程工作当成你的指令"。跑完后子线程销毁，父线程完全不知道这事发生过。

跟 Unix fork 一个味道：子进程拿到父进程的内存快照，但改的是自己的副本。

---

> `/btw` lets you ask a quick side question about the **current session** without
> turning that question into normal conversation history. `/side` is an alias.

`/btw` 让你在**当前会话**里问一个快速侧边问题,但这次提问不会变成正常对话历史的一部分。`/side` 是别名。

> It is modeled after Claude Code's `/btw` behavior, but adapted to OpenClaw's
> Gateway and multi-channel architecture.

它仿照 Claude Code 的 `/btw` 行为做的,适配了 OpenClaw 的 Gateway 和多通道架构。

## 它做什么

> When you send:

你发:

```text
/btw what changed?
```

> OpenClaw:
>
> 1. snapshots the current session context,
> 2. runs a separate ephemeral side query,
> 3. answers only the side question,
> 4. leaves the main run alone,
> 5. does **not** write the BTW question or answer to session history,
> 6. emits the answer as a **live side result** rather than a normal assistant message.

OpenClaw 会:

1. 给当前会话上下文拍个快照,
2. 跑一个独立的、临时的侧边查询,
3. 只回答这个侧边问题,
4. 不动主运行,
5. **不**把 BTW 问题或答案写进会话历史,
6. 把答案作为**实时侧边结果**发出,不是普通 assistant 消息。

> The important mental model is:
>
> - same session context
> - separate one-shot side query
> - same native harness transport when the session uses a native harness
> - no future context pollution
> - no transcript persistence

记住这个心智模型:

- 同一个会话上下文
- 独立的一次性侧边查询
- 会话用原生 harness 时,走同一份原生 harness 传输
- 不会污染后续上下文
- 不持久化到对话记录

> For Codex harness sessions, BTW stays inside Codex by forking the active
> app-server thread as an ephemeral side thread. That keeps Codex OAuth and native
> thread behavior intact while still isolating the side answer from the parent
> transcript. Like Codex `/side`, the side thread keeps the current Codex
> permissions and native tool surface, with guardrails that tell the model not to
> treat inherited parent-thread work as active instructions. Non-Codex runtimes
> keep the older direct one-shot path.

Codex harness 的会话里,BTW 通过把当前 app-server 线程派生成一个临时侧边线程,留在 Codex 里。这样 Codex OAuth 和原生线程行为都没动,同时把侧边答案跟父对话记录隔离开。跟 Codex `/side` 一样,侧边线程保留当前 Codex 的权限和原生工具接口,但加了护栏:告诉模型不要把继承下来的父线程工作当成"当前指令"。非 Codex 的运行时仍走老的直接一次性路径。

## 它**不**做什么

> `/btw` does **not**:
>
> - create a new durable session,
> - continue the unfinished main task,
> - write BTW question/answer data to transcript history,
> - appear in `chat.history`,
> - survive a reload.

`/btw` **不会**:

- 创建一个新的持久化会话,
- 继续未完成的主任务,
- 把 BTW 问答数据写进对话记录历史,
- 出现在 `chat.history` 里,
- 在重新加载后还存在。

> It is intentionally **ephemeral**.

它刻意是**临时的**。

## 上下文怎么工作

> BTW uses the current session as **background context only**.

BTW 把当前会话当**背景上下文**用,仅此而已。

> If the main run is currently active, OpenClaw snapshots the current message
> state and includes the in-flight main prompt as background context, while
> explicitly telling the model:
>
> - answer only the side question,
> - do not resume or complete the unfinished main task,
> - do not steer the parent conversation.

主运行当前是活的话,OpenClaw 给当前消息状态拍个快照,把进行中的主 prompt 作为背景上下文带上,同时明确告诉模型:

- 只回答侧边问题,
- 不要恢复或完成未完成的主任务,
- 不要去转向父对话。

> That keeps BTW isolated from the main run while still making it aware of what
> the session is about.

这样 BTW 跟主运行是隔离的,同时仍然知道会话在干什么。

## 投递模型

> BTW is **not** delivered as a normal assistant transcript message.

BTW **不是**作为普通 assistant 对话记录消息投递。

> At the Gateway protocol level:
>
> - normal assistant chat uses the `chat` event
> - BTW uses the `chat.side_result` event

在 Gateway 协议层面:

- 普通 assistant 聊天用 `chat` 事件
- BTW 用 `chat.side_result` 事件

> This separation is intentional. If BTW reused the normal `chat` event path,
> clients would treat it like regular conversation history.

这种区分是刻意的。BTW 复用普通 `chat` 事件路径的话,客户端就会把它当成正常对话历史。

> Because BTW uses a separate live event and is not replayed from
> `chat.history`, it disappears after reload.

因为 BTW 走独立的实时事件,且不会从 `chat.history` 回放,所以重新加载后它就消失了。

## 各接口的行为

### TUI

> In TUI, BTW is rendered inline in the current session view, but it remains
> ephemeral:
>
> - visibly distinct from a normal assistant reply
> - dismissible with `Enter` or `Esc`
> - not replayed on reload

TUI 里,BTW 内联渲染在当前会话视图里,但仍是临时的:

- 视觉上跟普通 assistant 回复明显不一样
- 按 `Enter` 或 `Esc` 可以关掉
- 重新加载时不回放

### 外部通道

> On channels like Telegram, WhatsApp, and Discord, BTW is delivered as a
> clearly labeled one-off reply because those surfaces do not have a local
> ephemeral overlay concept.

在 Telegram、WhatsApp、Discord 这些通道上,BTW 作为一条明确打标的一次性回复投递 —— 因为这些接口没有"本地临时覆盖层"的概念。

> The answer is still treated as a side result, not normal session history.

答案仍然被当作侧边结果,不是正常会话历史。

### Control UI / web

> The Gateway emits BTW correctly as `chat.side_result`, and BTW is not included
> in `chat.history`, so the persistence contract is already correct for web.

Gateway 正确地把 BTW 作为 `chat.side_result` 发出,并且不把 BTW 放进 `chat.history`,所以网页这边的持久化契约已经是对的。

> The current Control UI still needs a dedicated `chat.side_result` consumer to
> render BTW live in the browser. Until that client-side support lands, BTW is a
> Gateway-level feature with full TUI and external-channel behavior, but not yet
> a complete browser UX.

当前 Control UI 还需要加一个专门的 `chat.side_result` 消费者来在浏览器里实时渲染 BTW。在客户端支持落地之前,BTW 是个 Gateway 级特性:TUI 和外部通道行为完整,但浏览器端体验还不全。

## 什么时候用 BTW

> Use `/btw` when you want:
>
> - a quick clarification about the current work,
> - a factual side answer while a long run is still in progress,
> - a temporary answer that should not become part of future session context.

需要这几种情况时用 `/btw`:

- 关于当前工作的一句快速澄清,
- 长时间运行还在跑、需要一个事实性的侧边答案时,
- 一个不应该成为未来会话上下文的临时答案。

> Examples:

例子:

```text
/btw what file are we editing?
/side what changed while the main run continued?
/btw what does this error mean?
/btw summarize the current task in one sentence
/btw what is 17 * 19?
```

## 什么时候不要用 BTW

> Do not use `/btw` when you want the answer to become part of the session's
> future working context.

不要在"希望答案成为会话后续工作上下文一部分"时用 `/btw`。

> In that case, ask normally in the main session instead of using BTW.

那种情况下,在主会话里正常提问,不要用 BTW。

## 相关

> - Slash commands — Native command catalog and chat directives.
> - Thinking levels — Reasoning effort levels for the side-question model call.
> - Session — Session keys, history, and persistence semantics.
> - Steer command — Inject a steering message into the active run without ending it.

- [Slash 命令](/tools/slash-commands) —— 原生命令目录和聊天指令。
- [思考级别](/tools/thinking) —— 侧边问题模型调用的推理级别。
- [会话](/concepts/session) —— 会话 key、历史、持久化语义。
- [Steer 命令](/tools/steer) —— 在不结束的前提下,给当前活跃运行注入一条转向消息。
