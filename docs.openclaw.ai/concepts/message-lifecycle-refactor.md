# Message lifecycle refactor（消息生命周期重构）

## 架构精读

> 跳过不影响阅读翻译正文。

### 一个问题：Agent 回复丢了怎么办？

想象这个场景：用户在 Telegram 问了一句话，Agent 花 10 秒跑完 LLM 生成了回复。就在调 Telegram API 发消息的前一瞬间——进程挂了。用户看到的是：消息已读，但永远没有回复。

更坑的是：Telegram 那边已经确认"OpenClaw 收到了这条消息"（轮询 offset 已推进），所以不会重发。回复就这么凭空消失了。

这不是 Telegram 特有的。任何"先确认收到、后才发送回复"的设计都有这个窗口。这就是整篇 RFC 要解决的核心问题。

### 解法的关键直觉：先写日志再干活

数据库怎么保证事务不丢？WAL——先写日志，再改数据。崩了就重放日志。

OpenClaw 搬了同一招：决定要发消息时，先把"发送意图"写到本地磁盘（DurableSendIntent）。然后再去调平台 API。API 成功了，把回执补上。进程重启时扫一遍未完成的意图——该重发重发，该对账对账。

说白了就是**把"想发但还没发出去"这个中间状态持久化了**。丢进程不怕，磁盘上有记录。

### 最难的坑："发了但我不知道发没发"

WAL 能兜住"还没发就挂了"。但还有个更恶心的场景：API 返回 200 了，进程在写回执之前挂了。你不知道这条消息到底到了没——盲目重发会重复，不重发可能丢。

跟支付系统的"掉单"一模一样：钱扣了但订单没更新。唯一的解法是**对账**——去平台查真实状态。所以设计里有个 `reconcileUnknownSend`，每个通道适配器按自己的能力声明怎么对账。

### 一个范式转换值得单独提

旧设计里 `reply()` 是一切外发的入口。新设计里 `send()` 才是入口，`reply` 降级成消息的一种**关系标签**，跟 `followup`、`broadcast`、`system` 平级。

为什么这很重要？因为 Agent 不是只会"回复用户"。它还要主动推送定时通知、发审批请求、转发子 Agent 的结果。旧模型里这些全是 hack。新模型里它们都是一等公民——走同一条管道、享受同样的持久化保证。

### 为什么不直接把所有通道做成一样的？

因为通道能力差异巨大。WhatsApp 支持编辑已发消息，Telegram 不支持；Discord 有 reactions，iMessage 没有。硬抹平差异 = 最低公约数，体验全打折。

所以设计用了**能力声明**：每个通道适配器声明"我能编辑/我能反应/我能流式"，核心根据声明走不同路由。跟 HTTP 的 Content-Type 协商一个思路——不是 if-else 分支判断，而是能力驱动的多态。

### 迁移怎么做才不会炸

这么大的重构不可能一刀切。设计用了 8 个阶段的灰度：

核心原则是"旧代码永远不变，新代码在旁边长"。每个通道可以独立开关持久化（`disabled` → `best_effort` → `required`）。开之前得满足 6 个前置条件。出问题随时关回去。

跟大型系统的 feature flag 灰度发布一回事——先 1% 流量跑，确认没问题再全量。

---

> This page is the target design for replacing scattered channel inbound, reply dispatch, preview streaming, and outbound delivery helpers with one durable message lifecycle.

本页是一份**目标设计文档**：用一套持久化的消息生命周期，替换掉目前散落在各处的通道接收、回复派发、预览流、外发投递等辅助逻辑。

> The short version:
>
> * The core primitives should be **receive** and **send**, not **reply**.
> * A reply is only a relation on an outbound message.
> * A turn is an inbound-processing convenience, not the owner of delivery.
> * Sending must be context based: `begin`, render, preview or stream, final send, commit, fail.
> * Receiving must be context based too: normalize, dedupe, route, record, dispatch, platform ack, fail.
> * The public plugin SDK should collapse to one small channel-outbound surface.

一句话概括：

- 核心原语应该是**接收**和**发送**，而不是**回复**。
- 回复只是发出消息上的一种关系。
- 轮次（turn）是处理接收消息时的便捷封装，不应该承担投递的责任。
- 发送必须走上下文：`begin`（开始）→ 渲染 → 预览或流式 → 最终发送 → 提交 → 失败。
- 接收也必须走上下文：标准化 → 去重 → 路由 → 记录 → 派发 → 平台确认 → 失败。
- 公共插件 SDK 应该收敛成一个小巧的通道发送接口。

---

> ## Problems

## 问题

> The current channel stack grew from several valid local needs:
>
> * Simple inbound adapters use `runtime.channel.inbound.run`.
> * Rich adapters use `runtime.channel.inbound.runPreparedReply`.
> * Legacy helpers use `dispatchInboundReplyWithBase`, `recordInboundSessionAndDispatchReply`, reply payload helpers, reply chunking, reply references, and outbound runtime helpers.
> * Preview streaming lives in channel-specific dispatchers.
> * Final delivery durability is being added around existing reply payload paths.

现有的通道栈是从几个合理的局部需求里逐步长出来的：

- 简单的接收适配器用 `runtime.channel.inbound.run`。
- 复杂的适配器用 `runtime.channel.inbound.runPreparedReply`。
- 旧版辅助函数用 `dispatchInboundReplyWithBase`、`recordInboundSessionAndDispatchReply`，还有回复载荷辅助、回复分片、回复引用，以及一堆外发运行时辅助。
- 预览流式逻辑分散在各通道自己的派发器里。
- 持久化最终投递是后期围绕已有的回复载荷路径打补丁加上去的。

> That shape fixes local bugs, but it leaves OpenClaw with too many public concepts and too many places where delivery semantics can drift.

这种形态确实能修局部 bug，但代价是 OpenClaw 暴露的公共概念太多，投递语义可能漂移的地方也太多。

> The reliability issue that exposed this is:
>
> ```text
> Telegram polling update acked
>   -> assistant final text exists
>   -> process restarts before sendMessage succeeds
>   -> final response is lost
> ```

暴露这个问题的可靠性故障：

```text
Telegram polling 已确认
  -> 助手最终文本已生成
  -> sendMessage 成功之前进程重启
  -> 最终响应丢失
```

> The target invariant is broader than Telegram: once core decides a visible outbound message should exist, the intent must be durable before the platform send is attempted, and the platform receipt must be committed after success. That gives OpenClaw at-least-once recovery. Exactly-once behavior exists only for adapters that can prove native idempotency or reconcile an unknown-after-send attempt against platform state before replay.

这条不变量不只适用于 Telegram。规则是：**核心一旦决定"应该发出一条可见消息"，就必须先把这条发送意图持久化，然后才调平台 API；平台确认成功后才提交回执**。这就给了 OpenClaw "至少一次"的恢复保证。只有两种适配器能做到"恰好一次"——要么原生幂等，要么在重放前能把"已发但结果未知"的尝试与平台真实状态做对账。

> That is the end state for this refactor, not a description of every current path. During migration, existing outbound helpers can still fall through to a direct send when best-effort queue writes fail. The refactor is complete only when durable final sends fail closed or explicitly opt out with a documented non-durable policy.

这是重构的**终态**，不是当前所有路径的描述。迁移期间，队列写入失败时旧辅助函数仍可降级到直接发送。什么时候算完成？**持久化最终发送在写不进意图时默认拒绝，或者由调用方显式选退、并有文档记录的非持久化策略**——两者满足其一。

---

> ## Goals

## 目标

> * One core lifecycle for all channel message receive and send paths.
> * Durable final sends by default in the new message lifecycle after an adapter declares replay-safe behavior.
> * Shared preview, edit, stream, finalization, retry, recovery, and receipt semantics.
> * A small plugin SDK surface that third-party plugins can learn and maintain.
> * Compatibility for existing inbound reply compatibility callers during migration.
> * Clear extension points for new channel capabilities.
> * No platform-specific branches in core.
> * No token-delta channel messages. Channel streaming remains message preview, edit, append, or completed block delivery.
> * Structured OpenClaw-origin metadata for operational/system output so visible gateway failures do not re-enter shared bot-enabled rooms as fresh prompts.

- 所有通道的接收和发送路径都走同一套核心生命周期。
- 适配器声明自己是"重放安全"的之后，新生命周期默认采用持久化最终发送。
- 预览、编辑、流式、收尾、重试、恢复、回执——这些语义全部共享一套。
- 公共插件 SDK 接口要小到第三方插件能学会、能维护得动。
- 迁移过程中保持对现有接收回复兼容调用方的兼容。
- 给新的通道能力留出清晰的扩展点。
- 核心层不写任何平台专属分支。
- 通道消息不再发 token 级别的增量。通道流式仍然限定为：消息预览、编辑、追加、或整块投递。
- 给运维/系统类输出加上结构化的"OpenClaw 来源"元数据——这样可见的 Gateway 失败消息不会作为新提示词重新进入已允许机器人发言的共享房间。

---

> ## Non goals

## 非目标

> * Do not force every existing channel onto durable message delivery in the first phase.
> * Do not force every channel into the same native transport behavior.
> * Do not teach core Telegram topics, Slack native streams, Matrix redactions, Feishu cards, QQ voice, or Teams activities.
> * Do not publish all internal migration helpers as stable SDK API.
> * Do not make retries replay completed non-idempotent platform operations.

- 第一阶段不要强制所有现有通道都上持久化消息投递。
- 不要强迫每个通道做同样的原生传输行为。
- 不要让核心知道 Telegram topic、Slack 原生流、Matrix 撤回、飞书卡片、QQ 语音、Teams activity。
- 不要把所有内部迁移辅助函数都当稳定 SDK API 发布。
- 不要让重试重放已经完成的、非幂等的平台操作。

---

> ## Reference model

## 参考模型

> Vercel Chat has a good public mental model:
>
> * `Chat`
> * `Thread`
> * `Channel`
> * `Message`
> * adapter methods such as `postMessage`, `editMessage`, `deleteMessage`, `stream`, `startTyping`, and history fetches
> * a state adapter for dedupe, locks, queues, and persistence

Vercel Chat 有一份不错的公开心智模型：

- `Chat`
- `Thread`
- `Channel`
- `Message`
- 适配器方法，如 `postMessage`、`editMessage`、`deleteMessage`、`stream`、`startTyping` 和历史拉取
- 一个状态适配器，负责去重、锁、队列、持久化

> OpenClaw should borrow the vocabulary, not copy the surface.

OpenClaw 借用这套术语，不照搬接口。

> What OpenClaw needs beyond that model:
>
> * Durable outbound send intents before direct transport calls.
> * Explicit send contexts with begin, commit, and fail.
> * Receive contexts that know platform ack policy.
> * Receipts that survive restart and can drive edits, deletes, recovery, and duplicate suppression.
> * A smaller public SDK. Bundled plugins can use internal runtime helpers, but third-party plugins should see one coherent message API.
> * Agent-specific behavior: sessions, transcripts, block streaming, tool progress, approvals, media directives, silent replies, and group mention history.

在那套模型之外，OpenClaw 还需要：

- 在直接传输调用之前就持久化的发送意图。
- 带开始、提交、失败阶段的显式发送上下文。
- 知道平台确认策略的接收上下文。
- 重启后仍然存活的回执，能驱动编辑、删除、恢复和重复抑制。
- 更小的公共 SDK。内置插件可以用内部运行时辅助，但第三方插件应该看到一套连贯的消息 API。
- Agent 专属行为：会话、对话记录、块流式、工具进度、批准、媒体指令、静默回复、群 @ 历史。

> `thread.post()` style promises are not enough for OpenClaw. They hide the transaction boundary that decides whether a send is recoverable.

`thread.post()` 风格的 Promise 不够 OpenClaw 用。它们隐藏了那条决定"发送是否可恢复"的事务边界。

---

> ## Core model

## 核心模型

> The new domain should live under an internal core namespace such as `src/channels/message/*`.

新领域应该放在内部核心命名空间下，比如 `src/channels/message/*`。

> It has four concepts:
>
> ```typescript
> core.messages.receive(...)
> core.messages.send(...)
> core.messages.live(...)
> core.messages.state(...)
> ```

四个概念：

```typescript
core.messages.receive(...)
core.messages.send(...)
core.messages.live(...)
core.messages.state(...)
```

> `receive` owns inbound lifecycle.
>
> `send` owns outbound lifecycle.
>
> `live` owns preview, edit, progress, and stream state.
>
> `state` owns durable intent storage, receipts, idempotency, recovery, locks, and dedupe.

`receive` 负责接收生命周期。

`send` 负责发送生命周期。

`live` 负责预览、编辑、进度、流式状态。

`state` 负责持久化意图存储、回执、幂等、恢复、锁、去重。

---

> ## Message terms

## 消息术语

> ### Message

### 消息

> A normalized message is platform-neutral:
>
> ```typescript
> type ChannelMessage = {
>   id: string;
>   channel: string;
>   accountId?: string;
>   direction: "inbound" | "outbound";
>   target: MessageTarget;
>   sender?: MessageActor;
>   body?: MessageBody;
>   attachments?: MessageAttachment[];
>   relation?: MessageRelation;
>   origin?: MessageOrigin;
>   timestamp?: number;
>   raw?: unknown;
> };
> ```

标准化后的消息是平台无关的：

```typescript
type ChannelMessage = {
  id: string;
  channel: string;
  accountId?: string;
  direction: "inbound" | "outbound";
  target: MessageTarget;
  sender?: MessageActor;
  body?: MessageBody;
  attachments?: MessageAttachment[];
  relation?: MessageRelation;
  origin?: MessageOrigin;
  timestamp?: number;
  raw?: unknown;
};
```

> ### Target

### 目标

> The target describes where the message lives:
>
> ```typescript
> type MessageTarget = {
>   kind: "direct" | "group" | "channel" | "thread";
>   id: string;
>   label?: string;
>   spaceId?: string;
>   parentId?: string;
>   threadId?: string;
>   nativeChannelId?: string;
> };
> ```

目标描述消息在哪里：

```typescript
type MessageTarget = {
  kind: "direct" | "group" | "channel" | "thread";
  id: string;
  label?: string;
  spaceId?: string;
  parentId?: string;
  threadId?: string;
  nativeChannelId?: string;
};
```

> ### Relation

### 关系

> Reply is a relation, not an API root:
>
> ```typescript
> type MessageRelation =
>   | {
>       kind: "reply";
>       inboundMessageId?: string;
>       replyToId?: string;
>       threadId?: string;
>       quote?: MessageQuote;
>     }
>   | {
>       kind: "followup";
>       sessionKey?: string;
>       previousMessageId?: string;
>     }
>   | {
>       kind: "broadcast";
>       reason?: string;
>     }
>   | {
>       kind: "system";
>       reason:
>         | "approval"
>         | "task"
>         | "hook"
>         | "cron"
>         | "subagent"
>         | "message_tool"
>         | "cli"
>         | "control_ui"
>         | "automation"
>         | "error";
>     };
> ```

回复是一种关系，不是 API 根：

```typescript
type MessageRelation =
  | {
      kind: "reply";
      inboundMessageId?: string;
      replyToId?: string;
      threadId?: string;
      quote?: MessageQuote;
    }
  | {
      kind: "followup";
      sessionKey?: string;
      previousMessageId?: string;
    }
  | {
      kind: "broadcast";
      reason?: string;
    }
  | {
      kind: "system";
      reason:
        | "approval"
        | "task"
        | "hook"
        | "cron"
        | "subagent"
        | "message_tool"
        | "cli"
        | "control_ui"
        | "automation"
        | "error";
    };
```

> This lets the same send path handle normal replies, cron notifications, approval prompts, task completions, message-tool sends, CLI or Control UI sends, subagent results, and automation sends.

这样同一条发送路径就能处理：常规回复、定时通知、审批提示、任务完成通知、消息工具发送、CLI / Control UI 发送、子 Agent 结果、自动化发送。

> ### Origin

### 来源（Origin）

> Origin describes who produced a message and how OpenClaw should treat echoes of that message. It is separate from relation: a message can be a reply to a user and still be OpenClaw-originated operational output.

来源字段描述"这条消息是谁产生的、OpenClaw 看到它的回声时该怎么处理"。它和关系是两个独立的概念——一条消息既可以是对用户的回复，同时又是 OpenClaw 自己产生的运维输出。

> ```typescript
> type MessageOrigin =
>   | {
>       source: "openclaw";
>       schemaVersion: 1;
>       kind: "gateway_failure";
>       code: "agent_failed_before_reply" | "missing_api_key" | "model_login_expired";
>       echoPolicy: "drop_bot_room_echo";
>     }
>   | {
>       source: "user" | "external_bot" | "platform" | "unknown";
>     };
> ```

```typescript
type MessageOrigin =
  | {
      source: "openclaw";
      schemaVersion: 1;
      kind: "gateway_failure";
      code: "agent_failed_before_reply" | "missing_api_key" | "model_login_expired";
      echoPolicy: "drop_bot_room_echo";
    }
  | {
      source: "user" | "external_bot" | "platform" | "unknown";
    };
```

> Core owns the meaning of OpenClaw-originated output. Channels own how that origin is encoded into their transport.

核心定义"OpenClaw 来源输出"的含义。通道决定怎么把这个来源编码进自己的传输协议里。

> The first required use is gateway failure output. Humans should still see messages such as "Agent failed before reply" or "Missing API key", but tagged OpenClaw operational output must not be accepted as bot-authored input in shared rooms when `allowBots` is enabled.

第一个必需的用例是 Gateway 失败输出。人类仍然应该看到 "Agent failed before reply" 或 "Missing API key" 这种消息。但是，共享房间开了 `allowBots` 时，打了 OpenClaw 运维标签的输出不能被当作机器人输入接受。

> ### Receipt

### 回执

> Receipts are first-class:

回执是一等公民：

> ```typescript
> type MessageReceipt = {
>   primaryPlatformMessageId?: string;
>   platformMessageIds: string[];
>   parts: MessageReceiptPart[];
>   threadId?: string;
>   replyToId?: string;
>   editToken?: string;
>   deleteToken?: string;
>   url?: string;
>   sentAt: number;
>   raw?: unknown;
> };
>
> type MessageReceiptPart = {
>   platformMessageId: string;
>   kind: "text" | "media" | "voice" | "card" | "preview" | "unknown";
>   index: number;
>   threadId?: string;
>   replyToId?: string;
>   editToken?: string;
>   deleteToken?: string;
>   url?: string;
>   raw?: unknown;
> };
> ```

```typescript
type MessageReceipt = {
  primaryPlatformMessageId?: string;
  platformMessageIds: string[];
  parts: MessageReceiptPart[];
  threadId?: string;
  replyToId?: string;
  editToken?: string;
  deleteToken?: string;
  url?: string;
  sentAt: number;
  raw?: unknown;
};

type MessageReceiptPart = {
  platformMessageId: string;
  kind: "text" | "media" | "voice" | "card" | "preview" | "unknown";
  index: number;
  threadId?: string;
  replyToId?: string;
  editToken?: string;
  deleteToken?: string;
  url?: string;
  raw?: unknown;
};
```

> Receipts are the bridge from durable intent to future edit, delete, preview finalization, duplicate suppression, and recovery.

回执是连接持久化意图与后续编辑、删除、预览收尾、重复抑制和恢复的桥梁。

> A receipt can describe one platform message or a multi-part delivery. Chunked text, media plus text, voice plus text, and card fallbacks must preserve all platform ids while still exposing a primary id for threading and later edits.

一份回执可以描述一条平台消息，也可以描述多部分投递。分片文本、媒体加文本、语音加文本、卡片降级——都必须保留所有平台 ID，同时提供一个主 ID 用于线程关联和后续编辑。

---

> ## Receive context

## 接收上下文

> Receiving should not be a bare helper call. The core needs a context that knows dedupe, routing, session recording, and platform ack policy.

接收不应该是一个裸函数调用。核心需要一个上下文，能处理去重、路由、会话记录和平台确认策略。

> ```typescript
> type MessageReceiveContext = {
>   id: string;
>   channel: string;
>   accountId?: string;
>   input: ChannelMessage;
>   ack: ReceiveAckController;
>   route: MessageRouteController;
>   session: MessageSessionController;
>   log: MessageLifecycleLogger;
>
>   dedupe(): Promise<ReceiveDedupeResult>;
>   resolve(): Promise<ResolvedInboundMessage>;
>   record(resolved: ResolvedInboundMessage): Promise<RecordResult>;
>   dispatch(recorded: RecordResult): Promise<DispatchResult>;
>   commit(result: DispatchResult): Promise<void>;
>   fail(error: unknown): Promise<void>;
> };
> ```

```typescript
type MessageReceiveContext = {
  id: string;
  channel: string;
  accountId?: string;
  input: ChannelMessage;
  ack: ReceiveAckController;
  route: MessageRouteController;
  session: MessageSessionController;
  log: MessageLifecycleLogger;

  dedupe(): Promise<ReceiveDedupeResult>;
  resolve(): Promise<ResolvedInboundMessage>;
  record(resolved: ResolvedInboundMessage): Promise<RecordResult>;
  dispatch(recorded: RecordResult): Promise<DispatchResult>;
  commit(result: DispatchResult): Promise<void>;
  fail(error: unknown): Promise<void>;
};
```

> Receive flow:
>
> ```text
> platform event
>   -> begin receive context
>   -> normalize
>   -> classify
>   -> dedupe and self-echo gate
>   -> route and authorize
>   -> record inbound session metadata
>   -> dispatch agent run
>   -> durable outbound sends happen through send context
>   -> commit receive
>   -> ack platform when policy allows
> ```

接收流程：

```text
平台事件
  -> 启动接收上下文
  -> 标准化
  -> 分类
  -> 去重和自回声闸口
  -> 路由和授权
  -> 记录接收会话元数据
  -> 派发 Agent 运行
  -> 走发送上下文做持久化发送
  -> 提交接收
  -> 策略允许时确认平台
```

> Ack is not one thing. The receive contract must keep these signals separate:
>
> * **Transport ack:** tells the platform webhook or socket that OpenClaw accepted the event envelope. Some platforms require this before dispatch.
> * **Polling offset ack:** advances a cursor so the same event is not fetched again. This must not advance past work that cannot be recovered.
> * **Inbound record ack:** confirms OpenClaw persisted enough inbound metadata to dedupe and route a redelivery.
> * **User-visible receipt:** optional read/status/typing behavior; never a durability boundary.

确认不止一种。接收契约必须把以下信号分开：

- **传输确认**：告诉平台的 webhook 或 socket，OpenClaw 接受了事件信封。有些平台要求在派发之前先完成这步。
- **轮询偏移确认**：往前推游标，让同一个事件不会被再拉一次。游标不能越过那些还没法恢复的工作。
- **接收记录确认**：确认 OpenClaw 已经持久化了足够的接收元数据，可以去重和路由重投。
- **用户可见回执**：可选的已读/状态/输入中行为，永远不是持久化边界。

> `ReceiveAckPolicy` controls transport or polling acknowledgement only. It must not be reused for read receipts or status reactions.

`ReceiveAckPolicy` 只控制传输或轮询的确认，不要复用到已读回执或状态反应上。

> Before bot authorization, receive must apply the shared OpenClaw echo policy when the channel can decode message origin metadata:

通道能解码消息来源元数据时，接收流程必须在机器人授权之前应用共享的 OpenClaw 回声策略：

> ```typescript
> function shouldDropOpenClawEcho(params: {
>   origin?: MessageOrigin;
>   isBotAuthor: boolean;
>   isRoomish: boolean;
> }): boolean {
>   return (
>     params.isBotAuthor &&
>     params.isRoomish &&
>     params.origin?.source === "openclaw" &&
>     params.origin.kind === "gateway_failure" &&
>     params.origin.echoPolicy === "drop_bot_room_echo"
>   );
> }
> ```

```typescript
function shouldDropOpenClawEcho(params: {
  origin?: MessageOrigin;
  isBotAuthor: boolean;
  isRoomish: boolean;
}): boolean {
  return (
    params.isBotAuthor &&
    params.isRoomish &&
    params.origin?.source === "openclaw" &&
    params.origin.kind === "gateway_failure" &&
    params.origin.echoPolicy === "drop_bot_room_echo"
  );
}
```

> This drop is tag-based, not text-based. A bot-authored room message with the same visible gateway-failure text but without OpenClaw origin metadata still goes through normal `allowBots` authorization.

这个丢弃动作基于标签，不基于文本。一条机器人发的房间消息，文本看起来一样是 Gateway 失败，但没带 OpenClaw 来源元数据，仍然走常规的 `allowBots` 授权。

> Ack policy is explicit:
>
> ```typescript
> type ReceiveAckPolicy =
>   | { kind: "immediate"; reason: "webhook-timeout" | "platform-contract" }
>   | { kind: "after-record" }
>   | { kind: "after-durable-send" }
>   | { kind: "manual" };
> ```

确认策略必须显式声明：

```typescript
type ReceiveAckPolicy =
  | { kind: "immediate"; reason: "webhook-timeout" | "platform-contract" }
  | { kind: "after-record" }
  | { kind: "after-durable-send" }
  | { kind: "manual" };
```

> Telegram polling now uses the receive-context ack policy for its persisted restart watermark. The tracker still observes grammY updates as they enter the middleware chain, but OpenClaw persists only the safe completed update id after successful dispatch, leaving failed or lower pending updates replayable after a restart. Telegram's upstream `getUpdates` fetch offset is still controlled by the polling library, so the remaining deeper cut is a fully durable polling source if we need platform-level redelivery beyond OpenClaw's restart watermark. Webhook platforms may need immediate HTTP ack, but they still need inbound dedupe and durable outbound send intents because webhooks can redeliver.

Telegram 轮询现在通过接收上下文的确认策略来维护持久化的重启水位。追踪器照常观察 grammY update 进入中间件链。区别在于：OpenClaw 只在派发成功后才持久化"安全已完成"的 update ID——失败的或编号更低的待处理 update 重启后仍可重放。

Telegram 上游的 `getUpdates` 拉取偏移仍由轮询库控制。更深层的改造是换成完全持久化的轮询源，等需要超越 OpenClaw 重启水位的平台级重投时再做。

webhook 平台可能需要立即 HTTP 确认，但仍需要接收去重和持久化发送意图——因为 webhook 本身也会重投。

---

> ## Send context

## 发送上下文

> Sending is also context based:

发送同样基于上下文：

> ```typescript
> type MessageSendContext = {
>   id: string;
>   channel: string;
>   accountId?: string;
>   message: ChannelMessage;
>   intent: DurableSendIntent;
>   attempt: number;
>   signal: AbortSignal;
>   previousReceipt?: MessageReceipt;
>   preview?: LiveMessageState;
>   log: MessageLifecycleLogger;
>
>   render(): Promise<RenderedMessageBatch>;
>   previewUpdate(rendered: RenderedMessageBatch): Promise<LiveMessageState>;
>   send(rendered: RenderedMessageBatch): Promise<MessageReceipt>;
>   edit(receipt: MessageReceipt, rendered: RenderedMessageBatch): Promise<MessageReceipt>;
>   delete(receipt: MessageReceipt): Promise<void>;
>   commit(receipt: MessageReceipt): Promise<void>;
>   fail(error: unknown): Promise<void>;
> };
> ```

```typescript
type MessageSendContext = {
  id: string;
  channel: string;
  accountId?: string;
  message: ChannelMessage;
  intent: DurableSendIntent;
  attempt: number;
  signal: AbortSignal;
  previousReceipt?: MessageReceipt;
  preview?: LiveMessageState;
  log: MessageLifecycleLogger;

  render(): Promise<RenderedMessageBatch>;
  previewUpdate(rendered: RenderedMessageBatch): Promise<LiveMessageState>;
  send(rendered: RenderedMessageBatch): Promise<MessageReceipt>;
  edit(receipt: MessageReceipt, rendered: RenderedMessageBatch): Promise<MessageReceipt>;
  delete(receipt: MessageReceipt): Promise<void>;
  commit(receipt: MessageReceipt): Promise<void>;
  fail(error: unknown): Promise<void>;
};
```

> Preferred orchestration:
>
> ```typescript
> await core.messages.withSendContext(message, async (ctx) => {
>   const rendered = await ctx.render();
>
>   if (ctx.preview?.canFinalizeInPlace) {
>     return await ctx.edit(ctx.preview.receipt, rendered);
>   }
>
>   return await ctx.send(rendered);
> });
> ```

推荐的编排方式：

```typescript
await core.messages.withSendContext(message, async (ctx) => {
  const rendered = await ctx.render();

  if (ctx.preview?.canFinalizeInPlace) {
    return await ctx.edit(ctx.preview.receipt, rendered);
  }

  return await ctx.send(rendered);
});
```

> The helper expands to:
>
> ```text
> begin durable intent
>   -> render
>   -> optional preview/edit/stream work
>   -> mark sending
>   -> final platform send or final edit
>   -> mark committing with raw receipt
>   -> commit receipt
>   -> ack durable intent
>   -> fail durable intent on classified failure
> ```

这个辅助函数展开后的流程：

```text
启动持久化意图
  -> 渲染
  -> 可选的预览/编辑/流式工作
  -> 标记"发送中"
  -> 平台最终发送或最终编辑
  -> 标记"提交中"，附带原始回执
  -> 提交回执
  -> 确认持久化意图完成
  -> 归类后的失败触发持久化意图失败
```

> The intent must exist before transport I/O. A restart after begin but before commit is recoverable.

持久化意图必须在传输 I/O 之前存在。开始之后、提交之前的重启是可恢复的。

> The dangerous boundary is after platform success and before receipt commit. If a process dies there, OpenClaw cannot know whether the platform message exists unless the adapter provides native idempotency or a receipt reconciliation path. Those attempts must resume in `unknown_after_send`, not blindly replay. Channels without reconciliation may choose at-least-once replay only if duplicate visible messages are an acceptable, documented tradeoff for that channel and relation. The current SDK reconciliation bridge requires the adapter to declare `reconcileUnknownSend`, then asks `durableFinal.reconcileUnknownSend` to classify an unknown entry as `sent`, `not_sent`, or `unresolved`; only `not_sent` permits replay, and unresolved entries stay terminal or retry only the reconciliation check.

危险边界在"平台成功之后、回执提交之前"。进程在这里挂掉，OpenClaw 不知道平台消息到底存不存在——除非适配器有原生幂等或回执对账。这类尝试恢复时必须标为 `unknown_after_send`，不能盲目重放。

没有对账机制的通道怎么办？只有当"发出重复可见消息"是该通道和该关系可接受的、且有文档记录的折中方案时，才能选择"至少一次"重放。

当前 SDK 的对账桥这么工作：适配器声明 `reconcileUnknownSend`，然后调 `durableFinal.reconcileUnknownSend` 把未知条目归为 `sent`、`not_sent` 或 `unresolved`。只有 `not_sent` 允许重放；`unresolved` 条目终止，或仅重试对账检查本身。

> Durability policy must be explicit:
>
> ```typescript
> type MessageDurabilityPolicy = "required" | "best_effort" | "disabled";
> ```

持久化策略必须显式声明：

```typescript
type MessageDurabilityPolicy = "required" | "best_effort" | "disabled";
```

> `required` means core must fail closed when it cannot write the durable intent. `best_effort` can fall through when persistence is unavailable. `disabled` keeps the old direct send behavior. During migration, legacy wrappers and public compatibility helpers default to `disabled`; they must not infer `required` from the fact that a channel has a generic outbound adapter.

三个档位：

- `required`：写不进持久化意图就默认拒绝。
- `best_effort`：持久化不可用时降级到直接发送。
- `disabled`：保持旧版直接发送行为。

迁移期间，旧版包装和公共兼容辅助默认 `disabled`。不能因为某个通道有通用外发适配器就推断成 `required`。

> Send contexts also own channel-local post-send effects. A migration is not safe if durable delivery bypasses local behavior that was previously attached to the channel's direct send path. Examples include self-echo suppression caches, thread participation markers, native edit anchors, model-signature rendering, and platform-specific duplicate guards. Those effects must either move into the send adapter, the render adapter, or a named send-context hook before that channel can enable durable generic final delivery.

发送上下文还管通道本地的发送后副作用。持久化投递如果绕开了原来挂在直接发送路径上的本地行为，迁移就不安全。哪些算本地行为？自回声抑制缓存、线程参与标记、原生编辑锚点、模型签名渲染、平台专属重复护栏。这些副作用必须先迁到发送适配器、渲染适配器或发送上下文钩子，通道才能启用持久化通用最终投递。

> Send helpers must return receipts all the way back to their caller. Durable wrappers cannot swallow message ids or replace a channel delivery result with `undefined`; buffered dispatchers use those ids for thread anchors, later edits, preview finalization, and duplicate suppression.

发送辅助函数必须把回执一路返回给调用方。持久化包装层不能吞消息 ID，也不能把投递结果换成 `undefined`——后面的带缓冲派发器要拿这些 ID 做线程锚点、后续编辑、预览收尾和重复抑制。

> Fallback sends operate on batches, not single payloads. Silent-reply rewrites, media fallback, card fallback, and chunk projection can all produce more than one deliverable message, so a send context must either deliver the whole projected batch or explicitly document why only one payload is valid.

降级发送的处理单位是批次，不是单条载荷。静默回复改写、媒体降级、卡片降级、分片投射——这几种情况都可能产生不止一条可投递消息。所以发送上下文要么把整批投射全部投递，要么必须明确写清楚"为什么只有一条载荷是合法的"。

> ```typescript
> type RenderedMessageBatch = {
>   units: RenderedMessageUnit[];
>   atomicity: "all_or_retry_remaining" | "best_effort_parts";
>   idempotencyKey: string;
> };
>
> type RenderedMessageUnit = {
>   index: number;
>   kind: "text" | "media" | "voice" | "card" | "preview" | "unknown";
>   payload: unknown;
>   required: boolean;
> };
> ```

```typescript
type RenderedMessageBatch = {
  units: RenderedMessageUnit[];
  atomicity: "all_or_retry_remaining" | "best_effort_parts";
  idempotencyKey: string;
};

type RenderedMessageUnit = {
  index: number;
  kind: "text" | "media" | "voice" | "card" | "preview" | "unknown";
  payload: unknown;
  required: boolean;
};
```

> When such a fallback is durable, the whole projected batch must be represented by one durable send intent or another atomic batch plan. Recording each payload one-by-one is not enough: a crash between payloads can leave a partial visible fallback with no durable record for the remaining payloads. Recovery must know which units already have receipts and either replay only missing units or mark the batch `unknown_after_send` until the adapter reconciles it.

降级如果要持久化，整批投射必须对应一份持久化发送意图或一个原子批次计划。逐条记录载荷是不够的——万一两条载荷之间崩溃，前面的已经发出去了，后面的却没有持久化记录。恢复时必须知道哪些单元已有回执：只重放缺失的，或者把整批标成 `unknown_after_send` 等适配器对账。

---

> ## Live context

## 实时上下文

> Preview, edit, progress, and stream behavior should be one opt-in lifecycle.

预览、编辑、进度、流式行为应该合并成一个可选启用的生命周期。

> ```typescript
> type MessageLiveAdapter = {
>   begin?(ctx: MessageSendContext): Promise<LiveMessageState>;
>   update?(
>     ctx: MessageSendContext,
>     state: LiveMessageState,
>     update: LiveMessageUpdate,
>   ): Promise<LiveMessageState>;
>   finalize?(
>     ctx: MessageSendContext,
>     state: LiveMessageState,
>     final: RenderedMessageBatch,
>   ): Promise<MessageReceipt>;
>   cancel?(
>     ctx: MessageSendContext,
>     state: LiveMessageState,
>     reason: LiveCancelReason,
>   ): Promise<void>;
> };
> ```

```typescript
type MessageLiveAdapter = {
  begin?(ctx: MessageSendContext): Promise<LiveMessageState>;
  update?(
    ctx: MessageSendContext,
    state: LiveMessageState,
    update: LiveMessageUpdate,
  ): Promise<LiveMessageState>;
  finalize?(
    ctx: MessageSendContext,
    state: LiveMessageState,
    final: RenderedMessageBatch,
  ): Promise<MessageReceipt>;
  cancel?(
    ctx: MessageSendContext,
    state: LiveMessageState,
    reason: LiveCancelReason,
  ): Promise<void>;
};
```

> Live state is durable enough to recover or suppress duplicates:
>
> ```typescript
> type LiveMessageState = {
>   mode: "partial" | "block" | "progress" | "native";
>   receipt?: MessageReceipt;
>   visibleSince?: number;
>   canFinalizeInPlace: boolean;
>   lastRenderedHash?: string;
>   staleAfterMs?: number;
> };
> ```

实时状态的持久度足够支撑恢复或抑制重复：

```typescript
type LiveMessageState = {
  mode: "partial" | "block" | "progress" | "native";
  receipt?: MessageReceipt;
  visibleSince?: number;
  canFinalizeInPlace: boolean;
  lastRenderedHash?: string;
  staleAfterMs?: number;
};
```

> This should cover current behavior:
>
> * Telegram send plus edit preview, with fresh final after stale preview age.
> * Discord send plus edit preview, cancel on media/error/explicit reply.
> * Slack native stream or draft preview depending on thread shape.
> * Mattermost draft post finalization.
> * Matrix draft event finalization or redaction on mismatch.
> * Teams native progress stream.
> * QQ Bot stream or accumulated fallback.

这套机制应当覆盖以下现有行为：

- **Telegram**：发一条预览消息后通过编辑更新；预览过期时发一条新的最终消息。
- **Discord**：发预览后通过编辑更新；遇到媒体/错误/显式回复时取消预览。
- **Slack**：根据线程形态选择原生流或草稿预览。
- **Mattermost**：草稿帖收尾。
- **Matrix**：草稿事件收尾；不匹配时撤回。
- **Microsoft Teams**：原生进度流。
- **QQ Bot**：流式输出或累积型降级。

---

> ## Adapter surface

## 适配器接口

> The public SDK target should be one subpath:
>
> ```typescript
> import { defineChannelMessageAdapter } from "openclaw/plugin-sdk/channel-outbound";
> ```

公共 SDK 的目标是收敛成一个子路径：

```typescript
import { defineChannelMessageAdapter } from "openclaw/plugin-sdk/channel-outbound";
```

> Target shape:
>
> ```typescript
> type ChannelMessageAdapter = {
>   receive?: MessageReceiveAdapter;
>   send: MessageSendAdapter;
>   live?: MessageLiveAdapter;
>   origin?: MessageOriginAdapter;
>   render?: MessageRenderAdapter;
>   capabilities: MessageCapabilities;
> };
> ```

目标形态：

```typescript
type ChannelMessageAdapter = {
  receive?: MessageReceiveAdapter;
  send: MessageSendAdapter;
  live?: MessageLiveAdapter;
  origin?: MessageOriginAdapter;
  render?: MessageRenderAdapter;
  capabilities: MessageCapabilities;
};
```

> Send adapter:
>
> ```typescript
> type MessageSendAdapter = {
>   send(ctx: MessageSendContext, rendered: RenderedMessageBatch): Promise<MessageReceipt>;
>   edit?(
>     ctx: MessageSendContext,
>     receipt: MessageReceipt,
>     rendered: RenderedMessageBatch,
>   ): Promise<MessageReceipt>;
>   delete?(ctx: MessageSendContext, receipt: MessageReceipt): Promise<void>;
>   classifyError?(ctx: MessageSendContext, error: unknown): DeliveryFailureKind;
>   reconcileUnknownSend?(ctx: MessageSendContext): Promise<MessageReceipt | null>;
>   afterSendSuccess?(ctx: MessageSendContext, receipt: MessageReceipt): Promise<void>;
>   afterCommit?(ctx: MessageSendContext, receipt: MessageReceipt): Promise<void>;
> };
> ```

发送适配器：

```typescript
type MessageSendAdapter = {
  send(ctx: MessageSendContext, rendered: RenderedMessageBatch): Promise<MessageReceipt>;
  edit?(
    ctx: MessageSendContext,
    receipt: MessageReceipt,
    rendered: RenderedMessageBatch,
  ): Promise<MessageReceipt>;
  delete?(ctx: MessageSendContext, receipt: MessageReceipt): Promise<void>;
  classifyError?(ctx: MessageSendContext, error: unknown): DeliveryFailureKind;
  reconcileUnknownSend?(ctx: MessageSendContext): Promise<MessageReceipt | null>;
  afterSendSuccess?(ctx: MessageSendContext, receipt: MessageReceipt): Promise<void>;
  afterCommit?(ctx: MessageSendContext, receipt: MessageReceipt): Promise<void>;
};
```

> Receive adapter:
>
> ```typescript
> type MessageReceiveAdapter<TRaw = unknown> = {
>   normalize(raw: TRaw, ctx: MessageNormalizeContext): Promise<ChannelMessage>;
>   classify?(message: ChannelMessage): Promise<MessageEventClass>;
>   preflight?(message: ChannelMessage, event: MessageEventClass): Promise<MessagePreflightResult>;
>   ackPolicy?(message: ChannelMessage, event: MessageEventClass): ReceiveAckPolicy;
> };
> ```

接收适配器：

```typescript
type MessageReceiveAdapter<TRaw = unknown> = {
  normalize(raw: TRaw, ctx: MessageNormalizeContext): Promise<ChannelMessage>;
  classify?(message: ChannelMessage): Promise<MessageEventClass>;
  preflight?(message: ChannelMessage, event: MessageEventClass): Promise<MessagePreflightResult>;
  ackPolicy?(message: ChannelMessage, event: MessageEventClass): ReceiveAckPolicy;
};
```

> Before preflight authorization, core must run the shared OpenClaw echo predicate whenever `origin.decode` returns OpenClaw-origin metadata. The receive adapter supplies platform facts such as bot author and room shape; core owns the drop decision and ordering so channels do not reimplement text filters.

预检授权之前，`origin.decode` 一旦返回 OpenClaw 来源元数据，核心就必须跑共享的回声断言。接收适配器只管提供平台事实——是不是机器人发的、房间是什么形态。核心来做丢弃决策，各通道不用自己实现文本过滤。

> Origin adapter:
>
> ```typescript
> type MessageOriginAdapter<TRaw = unknown, TNative = unknown> = {
>   encode?(origin: MessageOrigin): TNative | undefined;
>   decode?(raw: TRaw): MessageOrigin | undefined;
> };
> ```

来源适配器：

```typescript
type MessageOriginAdapter<TRaw = unknown, TNative = unknown> = {
  encode?(origin: MessageOrigin): TNative | undefined;
  decode?(raw: TRaw): MessageOrigin | undefined;
};
```

> Core sets `MessageOrigin`. Channels only translate it to and from native transport metadata. Slack maps this to `chat.postMessage({ metadata })` and inbound `message.metadata`; Matrix can map it to extra event content; channels without native metadata can use a receipt/outbound registry when that is the best available approximation.

核心设置 `MessageOrigin`，通道只负责跟原生传输元数据互相转换。举几个例子：Slack 映射到 `chat.postMessage({ metadata })` 和接收端的 `message.metadata`；Matrix 映射到额外事件内容；没有原生元数据的通道可以用回执/外发注册表做近似。

> Capabilities:
>
> ```typescript
> type MessageCapabilities = {
>   text: { maxLength?: number; chunking?: boolean };
>   attachments?: {
>     upload: boolean;
>     remoteUrl: boolean;
>     voice?: boolean;
>   };
>   threads?: {
>     reply: boolean;
>     topic?: boolean;
>     nativeThread?: boolean;
>   };
>   live?: {
>     edit: boolean;
>     delete: boolean;
>     nativeStream?: boolean;
>     progress?: boolean;
>   };
>   delivery?: {
>     idempotencyKey?: boolean;
>     retryAfter?: boolean;
>     receiptRequired?: boolean;
>   };
> };
> ```

能力声明：

```typescript
type MessageCapabilities = {
  text: { maxLength?: number; chunking?: boolean };
  attachments?: {
    upload: boolean;
    remoteUrl: boolean;
    voice?: boolean;
  };
  threads?: {
    reply: boolean;
    topic?: boolean;
    nativeThread?: boolean;
  };
  live?: {
    edit: boolean;
    delete: boolean;
    nativeStream?: boolean;
    progress?: boolean;
  };
  delivery?: {
    idempotencyKey?: boolean;
    retryAfter?: boolean;
    receiptRequired?: boolean;
  };
};
```

---

> ## Public SDK reduction

## 公共 SDK 收敛

> The new public surface should absorb or deprecate these conceptual areas:
>
> * `reply-runtime`
> * `reply-dispatch-runtime`
> * `reply-reference`
> * `reply-chunking`
> * `reply-payload`
> * `inbound-reply-dispatch`
> * `channel-reply-pipeline`
> * most public uses of `outbound-runtime`
> * ad hoc draft stream lifecycle helpers

新的公共接口应该吸收或废弃以下概念区域：

- `reply-runtime`
- `reply-dispatch-runtime`
- `reply-reference`
- `reply-chunking`
- `reply-payload`
- `inbound-reply-dispatch`
- `channel-reply-pipeline`
- `outbound-runtime` 的大部分公开用法
- 各种临时草稿流式生命周期辅助

> Compatibility subpaths can remain as wrappers, but new third-party plugins should not need them.

兼容子路径可以以包装器形式保留，但新的第三方插件不该再需要它们。

> Bundled plugins may keep internal helper imports through reserved runtime subpaths while migrating. Public docs should steer plugin authors to `plugin-sdk/channel-outbound` once it exists.

内置插件迁移期间可以通过保留的运行时子路径继续导入内部辅助。公共文档应当在 `plugin-sdk/channel-outbound` 出现后引导插件作者去用它。

---

> ## Relationship to channel inbound

## 与接收运行时的关系

> `runtime.channel.inbound.*` is the runtime bridge during migration.

`runtime.channel.inbound.*` 是迁移期间的运行时桥。

> It should become a compatibility adapter:
>
> ```text
> channel.inbound.run
>   -> messages.receive context
>   -> session dispatch
>   -> messages.send context for visible output
> ```

它应当变成一个兼容适配器：

```text
channel.inbound.run
  -> messages.receive 上下文
  -> 会话派发
  -> 用 messages.send 上下文发可见输出
```

> `channel.inbound.runPreparedReply` should also remain initially:
>
> ```text
> channel-owned dispatcher
>   -> messages.receive record/finalize bridge
>   -> messages.live for preview/progress
>   -> messages.send for final delivery
> ```

`channel.inbound.runPreparedReply` 也先保留：

```text
通道自有派发器
  -> messages.receive 的记录/收尾桥
  -> messages.live 用于预览/进度
  -> messages.send 用于最终投递
```

> The old `channel.turn` runtime surface was removed. Runtime callers use `channel.inbound.*`; channel docs and SDK subpaths use inbound/message nouns.

旧的 `channel.turn` 运行时接口已经移除。运行时调用方统一用 `channel.inbound.*`；通道文档和 SDK 子路径统一用接收/消息名词。

---

> ## Compatibility guardrails

## 兼容护栏

> During migration, generic durable delivery is opt-in for any channel whose existing delivery callback has side effects beyond "send this payload".

迁移期间，凡是现有投递回调有"发送这个载荷"之外副作用的通道，通用持久化投递都是可选启用的。

> Legacy entry points are non-durable by default:
>
> * `channel.inbound.run` and `dispatchChannelInboundReply` use the channel's delivery callback unless that channel explicitly supplies an audited durable policy/options object.
> * `channel.inbound.runPreparedReply` stays channel-owned until the prepared dispatcher explicitly calls the send context.
> * Public compatibility helpers such as `recordInboundSessionAndDispatchReply`, `dispatchInboundReplyWithBase`, and direct-DM helpers never inject generic durable delivery before the caller-provided `deliver` or `reply` callback.

旧入口默认非持久化：

- `channel.inbound.run` 和 `dispatchChannelInboundReply` 用通道自己的投递回调，除非通道显式提供经过审计的持久化策略/选项对象。
- `channel.inbound.runPreparedReply` 在预备派发器显式调发送上下文之前保持通道自有。
- 公共兼容辅助如 `recordInboundSessionAndDispatchReply`、`dispatchInboundReplyWithBase`、私聊辅助，从不在调用者提供的 `deliver` 或 `reply` 回调之前注入通用持久化投递。

> For migration bridge types, `durable: undefined` means "not durable". The durable path is enabled only by an explicit policy/options value. `durable: false` can remain as a compatibility spelling, but implementation should not require every unmigrated channel to add it.

迁移桥类型里，`durable: undefined` 就是"不持久化"。持久化路径只有显式传策略/选项值才启用。`durable: false` 可以保留当兼容写法，但别要求每个未迁移通道都手动加。

> Current bridge code must keep the durability decision explicit:
>
> * Durable final delivery returns a discriminated status. `handled_visible` and `handled_no_send` are terminal; `unsupported` and `not_applicable` may fall back to channel-owned delivery; `failed` propagates the send failure.
> * Generic durable final delivery is gated by adapter capabilities such as silent delivery, reply target preservation, native quote preservation, and message-sending hooks. Missing parity should choose channel-owned delivery, not a generic send that changes user-visible behavior.
> * Queue-backed durable sends expose a delivery intent reference. Existing `pendingFinalDelivery*` session fields can carry the intent id during the transition; the end state is a `MessageSendIntent` store instead of frozen reply text plus ad hoc context fields.

当前桥代码必须保持持久化决定的显式性：

- 持久化最终投递返回一个判别状态。`handled_visible` 和 `handled_no_send` 终结流程；`unsupported` 和 `not_applicable` 可以降级到通道自有投递；`failed` 把发送失败传出去。
- 通用持久化最终投递要过适配器能力闸门：静默投递、回复目标保留、原生引用保留、消息发送钩子——缺哪个就不能走通用发送，老老实实走通道自有投递，别改变用户看到的行为。
- 队列支持的持久化发送暴露投递意图引用。过渡期间，`pendingFinalDelivery*` 会话字段可以承载意图 ID；终态是换成 `MessageSendIntent` 存储，不再是冻结的回复文本加临时上下文字段。

> Do not enable the generic durable path for a channel until all of these are true:
>
> * The generic send adapter executes the same rendering and transport behavior as the old direct path.
> * Local post-send side effects are preserved through the send context.
> * The adapter returns receipts or delivery results with all platform message ids.
> * Prepared dispatcher paths either call the new send context or stay documented as outside the durable guarantee.
> * Fallback delivery handles every projected payload, not only the first one.
> * Durable fallback delivery records the whole projected payload array as one replayable intent or batch plan.

通道在以下条件全部满足之前不要启用通用持久化路径：

- 通用发送适配器跟旧直接路径执行同样的渲染和传输行为。
- 本地发送后副作用通过发送上下文保留。
- 适配器返回回执或投递结果，含所有平台消息 ID。
- 预备派发器路径要么调新发送上下文，要么文档明确说不在持久化保证范围内。
- 降级投递处理每个投射载荷，不只是第一个。
- 持久化降级投递把整个投射载荷数组记成一份可重放的意图或批次计划。

> Concrete migration hazards to preserve:
>
> * iMessage monitor delivery records sent messages in an echo cache after a successful send. Durable final sends must still populate that cache, otherwise OpenClaw can re-ingest its own final replies as inbound user messages.
> * Tlon appends an optional model signature and records participated threads after group replies. Generic durable delivery must not bypass those effects; either move them into Tlon render/send/finalize adapters or keep Tlon on the channel-owned path.
> * Discord and other prepared dispatchers already own direct delivery and preview behavior. They are not covered by an assembled-turn durable guarantee until their prepared dispatchers explicitly route finals through the send context.
> * Telegram silent fallback delivery must deliver the full projected payload array. A single-payload shortcut can drop additional fallback payloads after projection.
> * LINE, Zalo, Nostr, and other existing assembled/helper paths may have reply-token handling, media proxying, sent-message caches, loading/status cleanup, or callback-only targets. They stay on channel-owned delivery until those semantics are represented by the send adapter and verified by tests.
> * Direct-DM helpers can have a reply callback that is the only correct transport target. Generic outbound must not guess from `OriginatingTo` or `To` and skip that callback.
> * OpenClaw gateway failure output must stay visible to humans, but tagged bot-authored room echoes must be dropped before `allowBots` authorization. Channels must not implement this with visible-text prefix filters except as a short emergency stopgap; the durable contract is structured origin metadata.

具体的迁移风险：

- **iMessage 监听器投递**在发送成功后会把发出消息存进回声缓存。持久化最终发送仍要填这个缓存，否则 OpenClaw 可能把自己的最终回复又当作接收消息读回来。
- **Tlon** 在群回复后追加可选的模型签名并记录参与过的线程。通用持久化投递不能绕开这些副作用；要么把它们迁移到 Tlon 的渲染/发送/收尾适配器，要么让 Tlon 留在通道自有路径上。
- **Discord 和其他预备派发器**已经管理着直接投递和预览行为。在它们的预备派发器显式把最终消息路由到发送上下文之前，"已组装轮次的持久化保证"不覆盖它们。
- **Telegram 静默降级投递**必须投递完整的投射载荷数组。单载荷捷径会在投射后丢掉额外的降级载荷。
- **LINE、Zalo、Nostr 和其他现有已组装/辅助路径**可能有回复令牌处理、媒体代理、发送消息缓存、加载/状态清理或只能用回调的目标。它们留在通道自有投递上，直到这些语义由发送适配器表达且测试验证通过。
- **私聊辅助**可能有一个回复回调是唯一正确的传输目标。通用外发不能从 `OriginatingTo` 或 `To` 猜测并跳过这个回调。
- **OpenClaw Gateway 失败输出**必须对人类可见，但打了标签的、机器人发的房间回声必须在 `allowBots` 授权之前丢弃。通道不能用可见文本前缀过滤来实现——短期应急除外；持久契约是结构化的来源元数据。

---

> ## Internal storage

## 内部存储

> The durable queue should store message send intents, not reply payloads.

持久化队列应当存消息发送意图，不存回复载荷。

> ```typescript
> type DurableSendIntent = {
>   id: string;
>   idempotencyKey: string;
>   channel: string;
>   accountId?: string;
>   message: ChannelMessage;
>   batch?: RenderedMessageBatch;
>   liveState?: LiveMessageState;
>   status:
>     | "pending"
>     | "sending"
>     | "committing"
>     | "unknown_after_send"
>     | "sent"
>     | "failed"
>     | "cancelled";
>   attempt: number;
>   nextAttemptAt?: number;
>   receipt?: MessageReceipt;
>   partialReceipt?: MessageReceipt;
>   failure?: DeliveryFailure;
>   createdAt: number;
>   updatedAt: number;
> };
> ```

```typescript
type DurableSendIntent = {
  id: string;
  idempotencyKey: string;
  channel: string;
  accountId?: string;
  message: ChannelMessage;
  batch?: RenderedMessageBatch;
  liveState?: LiveMessageState;
  status:
    | "pending"
    | "sending"
    | "committing"
    | "unknown_after_send"
    | "sent"
    | "failed"
    | "cancelled";
  attempt: number;
  nextAttemptAt?: number;
  receipt?: MessageReceipt;
  partialReceipt?: MessageReceipt;
  failure?: DeliveryFailure;
  createdAt: number;
  updatedAt: number;
};
```

> Recovery loop:
>
> ```text
> load pending or sending intents
>   -> acquire idempotency lock
>   -> skip if receipt already committed
>   -> reconstruct send context
>   -> render if needed
>   -> reconcile unknown_after_send if needed
>   -> call adapter send/edit/finalize
>   -> commit receipt, mark unknown_after_send, or schedule retry
> ```

恢复循环：

```text
加载待处理或发送中的意图
  -> 拿幂等锁
  -> 回执已提交则跳过
  -> 重建发送上下文
  -> 必要时渲染
  -> 必要时对账"发送后未知"状态
  -> 调适配器的发送/编辑/收尾
  -> 提交回执、标记"发送后未知"、或排队重试
```

> The queue should keep enough identity to replay through the same account, thread, target, formatting policy, and media rules after restart.

队列要保留足够的身份信息，让重启后可以走同一个账号、线程、目标、格式化策略和媒体规则重放。

---

> ## Failure classes

## 失败分类

> Channel adapters classify transport failures into closed categories:
>
> ```typescript
> type DeliveryFailureKind =
>   | "transient"
>   | "rate_limit"
>   | "auth"
>   | "permission"
>   | "not_found"
>   | "invalid_payload"
>   | "conflict"
>   | "cancelled"
>   | "unknown";
> ```

通道适配器把传输失败归入封闭类别：

```typescript
type DeliveryFailureKind =
  | "transient"
  | "rate_limit"
  | "auth"
  | "permission"
  | "not_found"
  | "invalid_payload"
  | "conflict"
  | "cancelled"
  | "unknown";
```

> Core policy:
>
> * Retry `transient` and `rate_limit`.
> * Do not retry `invalid_payload` unless a render fallback exists.
> * Do not retry `auth` or `permission` until configuration changes.
> * For `not_found`, let live finalization fall back from edit to fresh send when the channel declares that safe.
> * For `conflict`, use receipt/idempotency rules to decide whether the message already exists.
> * Any error after the adapter may have completed platform I/O but before receipt commit becomes `unknown_after_send` unless the adapter can prove the platform operation did not happen.

核心策略：

- `transient` 和 `rate_limit` 重试。
- `invalid_payload` 不重试——除非有渲染降级。
- `auth` 或 `permission` 不重试，直到配置变更。
- `not_found` 时，通道声明安全的话，让实时收尾从编辑降级到新发送。
- `conflict` 时，用回执/幂等规则判断消息是否已存在。
- 适配器可能完成了平台 I/O 但回执提交之前发生的任何错误都成为 `unknown_after_send`，除非适配器能证明平台操作没发生。

---

> ## Channel mapping

## 通道映射

> | Channel | Target migration |
> | --- | --- |
> | Telegram | Receive ack policy plus durable final sends. Live adapter owns send plus edit preview, stale preview final send, topics, quote-reply preview skip, media fallback, and retry-after handling. |
> | Discord | Send adapter wraps existing durable payload delivery. Live adapter owns draft edit, progress draft, media/error preview cancel, reply target preservation, and message id receipts. Audit bot-authored gateway-failure echoes in shared rooms; use an outbound registry or other native equivalent if Discord cannot carry origin metadata on normal messages. |
> | Slack | Send adapter handles normal chat posts. Live adapter chooses native stream when thread shape supports it, otherwise draft preview. Receipts preserve thread timestamps. Origin adapter maps OpenClaw gateway failures to Slack `chat.postMessage.metadata` and drops tagged bot-room echoes before `allowBots` authorization. |
> | WhatsApp | Send adapter owns text/media send with durable final intents. Receive adapter handles group mention and sender identity. Live can stay absent until WhatsApp has an editable transport. |
> | Matrix | Live adapter owns draft event edits, finalization, redaction, encrypted media constraints, and reply-target mismatch fallback. Receive adapter owns encrypted event hydration and dedupe. Origin adapter should encode OpenClaw gateway-failure origin into Matrix event content and drop configured-bot room echoes before `allowBots` handling. |
> | Mattermost | Live adapter owns one draft post, progress/tool folding, finalization in place, and fresh-send fallback. |
> | Microsoft Teams | Live adapter owns native progress and block stream behavior. Send adapter owns activities and attachment/card receipts. |
> | Feishu | Render adapter owns text/card/raw rendering. Live adapter owns streaming cards and duplicate final suppression. Send adapter owns comments, topic sessions, media, and voice suppression. |
> | QQ Bot | Live adapter owns C2C streaming, accumulator timeout, and fallback final send. Render adapter owns media tags and text-as-voice. |
> | Signal | Simple receive plus send adapter. No live adapter unless signal-cli adds reliable edit support. |
> | iMessage | Simple receive plus send adapter. iMessage send must preserve monitor echo-cache population before durable finals can bypass monitor delivery. |
> | Google Chat | Simple receive plus send adapter with thread relation mapped to spaces and thread ids. Audit `allowBots=true` room behavior for tagged OpenClaw gateway-failure echoes. |
> | LINE | Simple receive plus send adapter with reply-token constraints modeled as target/relation capability. |
> | Nextcloud Talk | SDK receive bridge plus send adapter. |
> | IRC | Simple receive plus send adapter, no durable edit receipts. |
> | Nostr | Receive plus send adapter for encrypted DMs; receipts are event ids. |
> | QA Channel | Contract-test adapter for receive, send, live, retry, and recovery behavior. |
> | Synology Chat | Simple receive plus send adapter. |
> | Tlon | Send adapter must preserve model-signature rendering and participated-thread tracking before generic durable final delivery is enabled. |
> | Twitch | Simple receive plus send adapter with rate-limit classification. |
> | Zalo | Simple receive plus send adapter. |
> | Zalo Personal | Simple receive plus send adapter. |

| 通道 | 目标迁移 |
| --- | --- |
| Telegram | 接收确认策略 + 持久化最终发送。实时适配器负责发送加编辑预览、过期预览的新最终发送、topic、引用回复跳过预览、媒体降级、限速后重试处理。 |
| Discord | 发送适配器包装现有持久化载荷投递。实时适配器负责草稿编辑、进度草稿、媒体/错误时的预览取消、回复目标保留、消息 ID 回执。审计共享房间中机器人发的 Gateway 失败回声；Discord 不能在常规消息上承载来源元数据时用外发注册表或其他原生等价物。 |
| Slack | 发送适配器处理常规聊天消息。实时适配器在线程形态支持时选原生流，否则用草稿预览。回执保留线程时间戳。来源适配器把 OpenClaw Gateway 失败映射到 Slack `chat.postMessage.metadata`，在 `allowBots` 授权之前丢弃打标签的机器人房间回声。 |
| WhatsApp | 发送适配器负责文本/媒体发送，带持久化最终意图。接收适配器处理群 @ 和发件人身份。在 WhatsApp 有可编辑传输之前，实时适配器可以缺席。 |
| Matrix | 实时适配器负责草稿事件编辑、收尾、撤回、加密媒体约束、回复目标不匹配时的降级。接收适配器负责加密事件水合和去重。来源适配器应把 OpenClaw Gateway 失败来源编码进 Matrix 事件内容，在 `allowBots` 处理之前丢弃已配置机器人的房间回声。 |
| Mattermost | 实时适配器负责一个草稿帖、进度/工具折叠、原地收尾、新发送降级。 |
| Microsoft Teams | 实时适配器负责原生进度和块流式行为。发送适配器负责 activity 和附件/卡片回执。 |
| 飞书 | 渲染适配器负责文本/卡片/原始渲染。实时适配器负责流式卡片和重复最终消息抑制。发送适配器负责评论、topic 会话、媒体、语音抑制。 |
| QQ Bot | 实时适配器负责 C2C 流式、累加器超时、降级最终发送。渲染适配器负责媒体标签和文本转语音。 |
| Signal | 简单的接收加发送适配器。signal-cli 没有可靠编辑支持时不需要实时适配器。 |
| iMessage | 简单的接收加发送适配器。在持久化最终发送可以绕过监听器投递之前，iMessage 发送必须保留监听器回声缓存填充。 |
| Google Chat | 简单的接收加发送适配器，线程关系映射到空间和线程 ID。审计 `allowBots=true` 房间对打标签 OpenClaw Gateway 失败回声的行为。 |
| LINE | 简单的接收加发送适配器，回复令牌约束建模为目标/关系能力。 |
| Nextcloud Talk | SDK 接收桥加发送适配器。 |
| IRC | 简单的接收加发送适配器，没有持久化编辑回执。 |
| Nostr | 加密私聊的接收加发送适配器；回执是事件 ID。 |
| QA Channel | 给接收、发送、实时、重试、恢复行为做契约测试用的适配器。 |
| Synology Chat | 简单的接收加发送适配器。 |
| Tlon | 发送适配器在启用通用持久化最终投递之前必须保留模型签名渲染和参与线程追踪。 |
| Twitch | 简单的接收加发送适配器，带限速分类。 |
| Zalo | 简单的接收加发送适配器。 |
| Zalo Personal | 简单的接收加发送适配器。 |

---

> ## Migration plan

## 迁移计划

> ### Phase 1: Internal Message Domain

### 阶段 1：内部消息领域

> - Add `src/channels/message/*` types for messages, targets, relations, origins, receipts, capabilities, durable intents, receive context, send context, live context, and failure classes.
> - Add `origin?: MessageOrigin` to the migration bridge payload type used by current reply delivery, then move that field to `ChannelMessage` and rendered message types as the refactor replaces reply payloads.
> - Keep this internal until adapters and tests prove the shape.
> - Add pure unit tests for state transitions and serialization.

- 在 `src/channels/message/*` 新增类型：消息、目标、关系、来源、回执、能力、持久化意图、接收上下文、发送上下文、实时上下文、失败类。
- 给当前回复投递使用的迁移桥载荷类型加 `origin?: MessageOrigin`，等重构替换回复载荷时再迁移到 `ChannelMessage` 和渲染消息类型。
- 先内部使用，等适配器和测试证明形态可行。
- 给状态转换和序列化加纯单测。

> ### Phase 2: Durable Send Core

### 阶段 2：持久化发送核心

> - Move the existing outbound queue from reply-payload durability to durable message send intents.
> - Let a durable send intent carry a projected payload array or batch plan, not only one reply payload.
> - Preserve the current queue recovery behavior through compatibility conversion.
> - Make `deliverOutboundPayloads` call `messages.send`.
> - Make final-send durability the default and fail closed when the durable intent cannot be written in the new message lifecycle, after the adapter declares replay safety. Existing inbound runner and SDK compatibility paths remain direct-send by default during this phase.
> - Record receipts consistently.
> - Return receipts and delivery results to the original dispatcher caller instead of treating durable send as a terminal side effect.
> - Persist message origin through durable send intents so recovery, replay, and chunked sends preserve OpenClaw operational provenance.

- 把现有外发队列从回复载荷持久化迁移到持久化消息发送意图。
- 一份持久化发送意图要能承载投射载荷数组或批次计划，不只一条回复载荷。
- 通过兼容转换保留当前队列恢复行为。
- 让 `deliverOutboundPayloads` 调 `messages.send`。
- 适配器声明重放安全后，新消息生命周期里最终发送默认持久化，写不进意图就默认拒绝。注意：本阶段现有接收运行器和 SDK 兼容路径仍默认直接发送。
- 统一记录回执。
- 把回执和投递结果一路返回给原始派发调用方，不再把持久化发送当成终结的副作用。
- 通过持久化发送意图保留消息来源，让恢复、重放、分片发送都保留 OpenClaw 运维归属。

> ### Phase 3: Channel Inbound Bridge

### 阶段 3：通道接收桥

> - Reimplement `channel.inbound.run` and `dispatchChannelInboundReply` on top of `messages.receive` and `messages.send`.
> - Keep current fact types stable.
> - Keep legacy behavior by default. An assembled-turn channel becomes durable only when its adapter explicitly opts in with a replay-safe durability policy.
> - Keep `durable: false` as a compatibility escape hatch for paths that finalize native edits and cannot replay safely yet, but do not rely on `false` markers to protect unmigrated channels.
> - Default assembled-turn durability only in the new message lifecycle, after the channel mapping proves the generic send path preserves the old channel delivery semantics.

- 在 `messages.receive` 和 `messages.send` 之上重新实现 `channel.inbound.run` 和 `dispatchChannelInboundReply`。
- 保持当前 fact 类型稳定。
- 默认保留旧行为。已组装轮次的通道只有在适配器显式选择重放安全的持久化策略后才变成持久化的。
- `durable: false` 作为兼容逃生口保留，给那些收尾原生编辑、还不能安全重放的路径用，但不依靠 `false` 标记保护未迁移通道。
- 已组装轮次的持久化默认值只在新消息生命周期里启用，且需通道映射证明通用发送路径保留了旧投递语义。

> ### Phase 4: Prepared Dispatcher Bridge

### 阶段 4：预备派发器桥

> - Replace `deliverDurableInboundReplyPayload` with a send-context bridge.
> - Keep the old helper as a wrapper.
> - Port Telegram, WhatsApp, Slack, Signal, iMessage, and Discord first because they already have durable-final work or simpler send paths.
> - Treat every prepared dispatcher as uncovered until it explicitly opts in to the send context. Documentation and changelog entries must say "assembled channel turns" or name the migrated channel paths rather than claiming all automatic final replies.
> - Keep `recordInboundSessionAndDispatchReply`, direct-DM helpers, and similar public compatibility helpers behavior-preserving. They may expose an explicit send-context opt-in later, but must not automatically attempt generic durable delivery before the caller-owned delivery callback.

- 用发送上下文桥替换 `deliverDurableInboundReplyPayload`。
- 保留旧辅助函数作为包装。
- 优先迁移 Telegram、WhatsApp、Slack、Signal、iMessage、Discord——它们已有持久化最终发送的工作或更简单的发送路径。
- 预备派发器没显式加入发送上下文的，都视为未覆盖。文档和变更日志要说"已组装通道轮次"或点名迁移过的通道，别笼统宣称所有自动最终回复已覆盖。
- `recordInboundSessionAndDispatchReply`、私聊辅助等公共兼容辅助保持行为不变。以后可以加发送上下文选择入口，但不能在调用方的投递回调之前偷偷尝试通用持久化投递。

> ### Phase 5: Unified Live Lifecycle

### 阶段 5：统一实时生命周期

> - Build `messages.live` with two proof adapters:
>   - Telegram for send plus edit plus stale final send.
>   - Matrix for draft finalization plus redaction fallback.
> - Then migrate Discord, Slack, Mattermost, Teams, QQ Bot, and Feishu.
> - Delete duplicated preview finalization code only after each channel has parity tests.

- 用两个验证适配器搭建 `messages.live`：
  - Telegram：发送加编辑加过期最终发送。
  - Matrix：草稿收尾加撤回降级。
- 然后迁移 Discord、Slack、Mattermost、Teams、QQ Bot、飞书。
- 每个通道有等价测试之后才删重复的预览收尾代码。

> ### Phase 6: Public SDK

### 阶段 6：公共 SDK

> - Add `openclaw/plugin-sdk/channel-outbound`.
> - Document it as the preferred channel plugin API.
> - Update package exports, entrypoint inventory, generated API baselines, and plugin SDK docs.
> - Include `MessageOrigin`, origin encode/decode hooks, and the shared `shouldDropOpenClawEcho` predicate in the channel-outbound SDK surface.
> - Keep compatibility wrappers for old subpaths.
> - Mark reply-named SDK helpers as deprecated in docs after bundled plugins are migrated.

- 新增 `openclaw/plugin-sdk/channel-outbound`。
- 文档标注为通道插件 API 的首选。
- 更新包导出、入口清单、生成的 API 基线、插件 SDK 文档。
- 把 `MessageOrigin`、来源编码/解码钩子、共享的 `shouldDropOpenClawEcho` 断言放进通道发送 SDK 接口。
- 保留旧子路径的兼容包装。
- 内置插件迁移完成后，在文档里把以 reply 命名的 SDK 辅助标为已废弃。

> ### Phase 7: All Senders

### 阶段 7：所有发送者

> Move all non-reply outbound producers onto `messages.send`:
>
> - cron and heartbeat notifications
> - task completions
> - hook results
> - approval prompts and approval results
> - message tool sends
> - subagent completion announcements
> - explicit CLI or Control UI sends
> - automation/broadcast paths
>
> This is where the model stops being "agent replies" and becomes "OpenClaw sends messages".

把所有非回复的外发生产者搬到 `messages.send`：

- 定时任务和心跳通知
- 任务完成
- 钩子结果
- 批准提示和批准结果
- 消息工具发送
- 子 Agent 完成通告
- 显式 CLI 或 Control UI 发送
- 自动化/广播路径

这是模型从"Agent 回复"变成"OpenClaw 发消息"的转折点。

> ### Phase 8: Remove Turn-Named Compatibility

### 阶段 8：移除旧命名兼容

> - Keep inbound/message-named wrappers as the compatibility window.
> - Publish migration notes.
> - Run plugin SDK compatibility tests against old imports.
> - Remove or hide old internal helpers only after no bundled plugin needs them and third-party contracts have a stable replacement.

- 保留接收/消息命名的包装器作为兼容窗口期。
- 发布迁移说明。
- 用旧导入跑插件 SDK 兼容测试。
- 等没有内置插件再需要、且第三方契约已有稳定替代之后，才删或隐藏旧的内部辅助。

---

> ## Test plan

## 测试计划

> Unit tests:
>
> - Durable send intent serialization and recovery.
> - Idempotency key reuse and duplicate suppression.
> - Receipt commit and replay skip.
> - `unknown_after_send` recovery that reconciles before replay when an adapter supports reconciliation.
> - Failure classification policy.
> - Receive ack policy sequencing.
> - Relation mapping for reply, followup, system, and broadcast sends.
> - Gateway-failure origin factory and `shouldDropOpenClawEcho` predicate.
> - Origin preservation through payload normalization, chunking, durable queue serialization, and recovery.

单测：

- 持久化发送意图的序列化和恢复。
- 幂等键复用和重复抑制。
- 回执提交和重放跳过。
- 适配器支持对账时，`unknown_after_send` 恢复在重放前先对账。
- 失败分类策略。
- 接收确认策略的执行顺序。
- 回复、后续、系统、广播发送的关系映射。
- Gateway 失败来源工厂和 `shouldDropOpenClawEcho` 断言。
- 来源信息在载荷标准化、分片、持久队列序列化和恢复中的保留。

> Integration tests:
>
> - `channel.inbound.run` simple adapter still records and sends.
> - Legacy assembled-event delivery does not become durable unless the channel explicitly opts in.
> - `channel.inbound.runPreparedReply` bridge still records and finalizes.
> - Public compatibility helpers call caller-owned delivery callbacks by default and do not generic-send before those callbacks.
> - Durable fallback delivery replays the whole projected payload array after restart and cannot leave the later payloads unrecorded after an early crash.
> - Durable assembled-event delivery returns platform message ids to the buffered dispatcher.
> - Custom delivery hooks still return platform message ids when durable delivery is disabled or unavailable.
> - Final reply survives restart between assistant completion and platform send.
> - Preview draft finalizes in place when allowed.
> - Preview draft is cancelled or redacted when media/error/reply-target mismatch requires normal delivery.
> - Block streaming and preview streaming do not both deliver the same text.
> - Media streamed early is not duplicated in final delivery.

集成测试：

- `channel.inbound.run` 简单适配器仍能记录和发送。
- 旧版已组装事件投递不会自动变成持久化的，除非通道显式选择加入。
- `channel.inbound.runPreparedReply` 桥仍能记录和收尾。
- 公共兼容辅助默认调调用方自己的投递回调，不在这些回调之前做通用发送。
- 持久化降级投递在重启后重放整个投射载荷数组，不能在早期崩溃后遗漏后续载荷的记录。
- 持久化已组装事件投递把平台消息 ID 返回给带缓冲的派发器。
- 自定义投递钩子在持久化投递禁用或不可用时仍返回平台消息 ID。
- 最终回复在助手完成和平台发送之间的重启中存活。
- 允许时预览草稿原地收尾。
- 媒体/错误/回复目标不匹配需要常规投递时，预览草稿被取消或撤回。
- 块流式和预览流式不会把同一段文本投递两次。
- 提前流式输出的媒体不会在最终投递中重复。

> Channel tests:
>
> - Telegram topic reply with polling ack delayed until the receive context's safe completed watermark.
> - Telegram polling recovery for accepted-but-not-delivered updates covered by the persisted safe-completed offset model.
> - Telegram stale preview sends fresh final and cleans up preview.
> - Telegram silent fallback sends every projected fallback payload.
> - Telegram silent fallback durability records the full projected fallback array atomically, not one single-payload durable intent per loop iteration.
> - Discord preview cancel on media/error/explicit reply.
> - Discord prepared dispatcher finals route through the send context before docs or changelog claim Discord final-reply durability.
> - iMessage durable final sends populate the monitor sent-message echo cache.
> - LINE, Zalo, and Nostr legacy delivery paths are not bypassed by generic durable send until their adapter parity tests exist.
> - Direct-DM/Nostr callback delivery remains authoritative unless explicitly migrated to a complete message target and replay-safe send adapter.
> - Slack tagged OpenClaw gateway failure messages stay visible outbound, tagged bot-room echoes drop before `allowBots`, and untagged bot messages with the same visible text still follow normal bot authorization.
> - Slack native stream fallback to draft preview in top-level DMs.
> - Matrix preview finalization and redaction fallback.
> - Matrix tagged OpenClaw gateway-failure room echoes from configured bot accounts drop before `allowBots` handling.
> - Discord and Google Chat shared-room gateway-failure cascade audits cover `allowBots` modes before claiming generic protection there.
> - Mattermost draft finalization and fresh-send fallback.
> - Teams native progress finalization.
> - Feishu duplicate final suppression.
> - QQ Bot accumulator timeout fallback.
> - Tlon durable final sends preserve model-signature rendering and participated thread tracking.
> - WhatsApp, Signal, iMessage, Google Chat, LINE, IRC, Nostr, Nextcloud Talk, Synology Chat, Tlon, Twitch, Zalo, and Zalo Personal simple durable final sends.

通道测试：

- Telegram topic 回复，轮询确认延迟到接收上下文的安全完成水位。
- Telegram 轮询恢复：已接受但未投递的 update 由持久化的安全完成偏移模型覆盖。
- Telegram 过期预览发新的最终消息并清理预览。
- Telegram 静默降级发送每一个投射降级载荷。
- Telegram 静默降级持久化原子地记录完整的投射降级数组，而不是每次循环迭代一条单载荷持久化意图。
- Discord 预览在媒体/错误/显式回复时取消。
- Discord 预备派发器的最终消息在文档或变更日志宣称 Discord 最终回复持久化之前先路由到发送上下文。
- iMessage 持久化最终发送填充监听器的已发消息回声缓存。
- LINE、Zalo、Nostr 旧版投递路径在适配器等价测试出来之前不被通用持久化发送绕过。
- 私聊/Nostr 回调投递保持权威，除非显式迁移到完整消息目标和重放安全的发送适配器。
- Slack：打标签的 OpenClaw Gateway 失败消息保持外发可见；打标签的机器人房间回声在 `allowBots` 之前丢弃；未打标签但文本相同的机器人消息仍走常规授权。
- Slack 原生流在顶级私聊中降级到草稿预览。
- Matrix 预览收尾和撤回降级。
- Matrix 打标签的、来自已配置机器人账号的 OpenClaw Gateway 失败房间回声在 `allowBots` 处理之前丢弃。
- Discord 和 Google Chat 共享房间 Gateway 失败级联审计覆盖 `allowBots` 模式，然后才宣称通用保护。
- Mattermost 草稿收尾和新发送降级。
- Teams 原生进度收尾。
- 飞书重复最终消息抑制。
- QQ Bot 累加器超时降级。
- Tlon 持久化最终发送保留模型签名渲染和参与线程追踪。
- WhatsApp、Signal、iMessage、Google Chat、LINE、IRC、Nostr、Nextcloud Talk、Synology Chat、Tlon、Twitch、Zalo、Zalo Personal 的简单持久化最终发送。

> Validation:
>
> - Targeted Vitest files during development.
> - `pnpm check:changed` in Testbox for the full changed surface.
> - Broader `pnpm check` in Testbox before landing the complete refactor or after public SDK/export changes.
> - Live or qa-channel smoke for at least one edit-capable channel and one simple send-only channel before removing compatibility wrappers.

验证：

- 开发期间写针对性的 Vitest 文件。
- 在 Testbox 中用 `pnpm check:changed` 覆盖完整的变更范围。
- 在合并完整重构或公共 SDK/导出变更之前，在 Testbox 中跑更广的 `pnpm check`。
- 移除兼容包装之前，至少对一个支持编辑的通道和一个纯发送通道做线上或 qa-channel 冒烟测试。

---

> ## Open questions

## 开放问题

> - Whether Telegram should eventually replace the grammY runner source with a fully durable polling source that can control platform-level redelivery, not only OpenClaw's persisted restart watermark.
> - Whether durable live preview state should be stored in the same queue record as the final send intent or in a sibling live-state store.
> - How long compatibility wrappers stay documented after `plugin-sdk/channel-outbound` ships.
> - Whether third-party plugins should implement receive adapters directly or only provide normalize/send/live hooks through `defineChannelMessageAdapter`.
> - Which receipt fields are safe to expose in public SDK versus internal runtime state.
> - Whether side effects such as self-echo caches and participated-thread markers should be modeled as send-context hooks, adapter-owned finalize steps, or receipt subscribers.
> - Which channels have native origin metadata, which need persisted outbound registries, and which cannot offer reliable cross-bot echo suppression.

- Telegram 是否最终该把 grammY 运行器源替换成一个完全持久化的轮询源，能控制平台级重投，而不只是 OpenClaw 的持久化重启水位。
- 持久化的实时预览状态该和最终发送意图存在同一条队列记录里，还是放在并列的实时状态存储。
- `plugin-sdk/channel-outbound` 发布之后，兼容包装在文档里保留多久。
- 第三方插件应当直接实现接收适配器，还是只通过 `defineChannelMessageAdapter` 提供标准化/发送/实时钩子。
- 回执字段哪些能安全暴露到公共 SDK 里、哪些只能留在内部运行时状态里。
- 自回声缓存和参与线程标记这种副作用，应当建模为发送上下文钩子、适配器管理的收尾步骤、还是回执订阅者。
- 哪些通道有原生来源元数据、哪些需要持久化的外发注册表、哪些根本无法做可靠的跨机器人回声抑制。

---

> ## Acceptance criteria

## 验收标准

> - Every bundled message channel sends final visible output through `messages.send`.
> - Every inbound message channel enters through `messages.receive` or a documented compatibility wrapper.
> - Every preview/edit/stream channel uses `messages.live` for draft state and finalization.
> - `channel.inbound` is only a wrapper.
> - Reply-named SDK helpers are compatibility exports, not the recommended path.
> - Durable recovery can replay pending final sends after restart without losing the final response or duplicating already committed sends; sends whose platform outcome is unknown are reconciled before replay or documented as at-least-once for that adapter.
> - Durable final sends fail closed when the durable intent cannot be written, unless a caller explicitly selected a documented non-durable mode.
> - Legacy SDK compatibility helpers default to direct channel-owned delivery; generic durable send is explicit opt-in only.
> - Receipts preserve all platform message ids for multi-part deliveries and a primary id for threading/edit convenience.
> - Durable wrappers preserve channel-local side effects before replacing direct delivery callbacks.
> - Prepared dispatchers are not counted as durable until their final delivery path explicitly uses the send context.
> - Fallback delivery handles every projected payload.
> - Durable fallback delivery records every projected payload in one replayable intent or batch plan.
> - OpenClaw-originated gateway failure output is visible to humans but tagged bot-authored room echoes are dropped before bot authorization on channels that declare support for the origin contract.
> - The docs explain send, receive, live, state, receipts, relations, failure policy, migration, and test coverage.

- 每个内置消息通道都通过 `messages.send` 发最终可见输出。
- 每个接收消息通道都通过 `messages.receive` 或一个有文档的兼容包装进入。
- 每个预览/编辑/流式通道都用 `messages.live` 做草稿状态和收尾。
- `channel.inbound` 只是一个包装。
- 以 reply 命名的 SDK 辅助只是兼容导出，不是推荐路径。
- 持久化恢复能在重启后重放待处理的最终发送，不丢最终响应、不重复已提交的发送；平台结果未知的发送在重放前对账，或者文档化为该适配器的"至少一次"。
- 持久化最终发送在写不进意图时默认拒绝——除非调用者显式选了一个文档化的非持久模式。
- 旧版 SDK 兼容辅助默认直接走通道自有投递；通用持久化发送必须显式选择加入。
- 多部分投递的回执保留所有平台消息 ID，并提供一个主 ID 用于线程关联/编辑。
- 持久化包装在替换直接投递回调之前先保留通道本地副作用。
- 预备派发器在最终投递路径显式使用发送上下文之前都不算持久化。
- 降级投递处理每一个投射载荷。
- 持久化降级投递把每一个投射载荷记进一份可重放的意图或批次计划。
- OpenClaw 产生的 Gateway 失败输出对人类可见。但如果通道声明了来源契约支持，打了标签的机器人房间回声必须在机器人授权之前丢弃。
- 文档讲清楚发送、接收、实时、状态、回执、关系、失败策略、迁移、测试覆盖。

---

> ## Related

## 相关

> - [Messages](/concepts/messages)
> - [Streaming and chunking](/concepts/streaming)
> - [Progress drafts](/concepts/progress-drafts)
> - [Retry policy](/concepts/retry)
> - [Channel inbound API](/plugins/sdk-channel-inbound)

- [消息](/concepts/messages)
- [流式与分片](/concepts/streaming)
- [进度草稿](/concepts/progress-drafts)
- [重试策略](/concepts/retry)
- [通道接收 API](/plugins/sdk-channel-inbound)
