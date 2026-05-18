# Message lifecycle refactor

> This page is the target design for replacing scattered channel turn, reply dispatch, preview streaming, and outbound delivery helpers with one durable message lifecycle.

本页是一份目标设计：把散乱的 channel turn、reply dispatch、预览 streaming、outbound delivery helper 替换成一套持久化的消息生命周期。

> The short version:
>
> * The core primitives should be **receive** and **send**, not **reply**.
> * A reply is only a relation on an outbound message.
> * A turn is an inbound-processing convenience, not the owner of delivery.
> * Sending must be context based: `begin`, render, preview or stream, final send, commit, fail.
> * Receiving must be context based too: normalize, dedupe, route, record, dispatch, platform ack, fail.
> * The public plugin SDK should collapse to one small channel-message surface.

简短版：

- 核心原语应该是 **receive** 和 **send**，不是 **reply**。
- reply 只是发送消息上的一种关系。
- turn 是接收处理的便捷封装，不是投递的所有者。
- 发送必须基于上下文：`begin`、渲染、预览或 stream、final send、commit、fail。
- 接收也必须基于上下文：归一化、去重、route、record、dispatch、平台确认、fail。
- 公共插件 SDK 应该收敛到一个小的 channel-message 面。

---

> ## Problems

## 问题

> The current channel stack grew from several valid local needs:
>
> * Simple inbound adapters use `runtime.channel.turn.run`.
> * Rich adapters use `runtime.channel.turn.runPrepared`.
> * Legacy helpers use `dispatchInboundReplyWithBase`, `recordInboundSessionAndDispatchReply`, reply payload helpers, reply chunking, reply references, and outbound runtime helpers.
> * Preview streaming lives in channel-specific dispatchers.
> * Final delivery durability is being added around existing reply payload paths.

现有通道栈是从一些合理的局部需求里长出来的：

- 简单的接收适配器用 `runtime.channel.turn.run`。
- 富适配器用 `runtime.channel.turn.runPrepared`。
- 旧版助手用 `dispatchInboundReplyWithBase`、`recordInboundSessionAndDispatchReply`、reply payload 助手、reply chunking、reply reference 以及 outbound runtime 助手。
- 预览流式实现在通道专属的 dispatcher 里。
- 投递持久化是绕着现有 reply payload 路径加上去的。

> That shape fixes local bugs, but it leaves OpenClaw with too many public concepts and too many places where delivery semantics can drift.

这种形状能修局部 bug，但留给 OpenClaw 太多公共概念、太多投递语义可能漂移的地方。

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
Telegram polling 已 ack
  -> assistant 最终文本已生成
  -> sendMessage 成功之前进程重启
  -> 最终响应丢失
```

> The target invariant is broader than Telegram: once core decides a visible outbound message should exist, the intent must be durable before the platform send is attempted, and the platform receipt must be committed after success. That gives OpenClaw at-least-once recovery. Exactly-once behavior exists only for adapters that can prove native idempotency or reconcile an unknown-after-send attempt against platform state before replay.

目标不变量比 Telegram 更广：核心一旦决定要存在一条可见发送消息，意图必须在平台 send 之前就持久化，平台收据必须在成功后提交。这给 OpenClaw 提供"至少一次"恢复。"恰好一次"只有那些能证明原生幂等、或能在重放前把"send 后未知"尝试和平台状态对账的适配器才有。

> That is the end state for this refactor, not a description of every current path. During migration, existing outbound helpers can still fall through to a direct send when best-effort queue writes fail. The refactor is complete only when durable final sends fail closed or explicitly opt out with a documented non-durable policy.

这是这次重构的终态，不是现状每条路径的描述。迁移期间，现有 outbound 助手仍可以在 best-effort 队列写入失败时降级到直接 send。只有当持久化的最终 send 在失败时默认拒绝、或显式带有文档化的非持久策略时，重构才算完成。

---

> ## Goals

## 目标

> * One core lifecycle for all channel message receive and send paths.
> * Durable final sends by default in the new message lifecycle after an adapter declares replay-safe behavior.
> * Shared preview, edit, stream, finalization, retry, recovery, and receipt semantics.
> * A small plugin SDK surface that third-party plugins can learn and maintain.
> * Compatibility for existing `channel.turn` callers during migration.
> * Clear extension points for new channel capabilities.
> * No platform-specific branches in core.
> * No token-delta channel messages. Channel streaming remains message preview, edit, append, or completed block delivery.
> * Structured OpenClaw-origin metadata for operational/system output so visible gateway failures do not re-enter shared bot-enabled rooms as fresh prompts.

- 所有通道消息 receive 和 send 路径走一套核心生命周期。
- 在新消息生命周期里，适配器声明 replay-safe 后，默认走持久化的最终 send。
- 共享预览、edit、stream、finalization、retry、recovery、回执语义。
- 一个小的插件 SDK 面，第三方插件能学得会、维护得动。
- 迁移期间对现有 `channel.turn` 调用者保持兼容。
- 给新的通道能力留清晰的扩展点。
- 核心里不要平台专属分支。
- 不发 token-delta 的通道消息。通道流式保留为消息预览、edit、append、或完成块投递。
- 给运维 / 系统输出加上结构化的 OpenClaw 来源元数据，避免可见的 Gateway 失败作为新 prompt 重新进入开了 bot 的共享房间。

---

> ## Non goals

## 非目标

> * Do not remove `runtime.channel.turn.*` in the first phase.
> * Do not force every channel into the same native transport behavior.
> * Do not teach core Telegram topics, Slack native streams, Matrix redactions, Feishu cards, QQ voice, or Teams activities.
> * Do not publish all internal migration helpers as stable SDK API.
> * Do not make retries replay completed non-idempotent platform operations.

- 第一阶段不要删 `runtime.channel.turn.*`。
- 不要强迫每个通道做同样的原生传输行为。
- 不要让核心知道 Telegram topic、Slack 原生流、Matrix redaction、飞书 card、QQ 语音、Teams activity。
- 不要把所有内部迁移助手都当稳定 SDK API 发布。
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
- 一个 state 适配器，负责去重、锁、队列、持久化

> OpenClaw should borrow the vocabulary, not copy the surface.

OpenClaw 借用这套术语，不抄表面。

> What OpenClaw needs beyond that model:
>
> * Durable outbound send intents before direct transport calls.
> * Explicit send contexts with begin, commit, and fail.
> * Receive contexts that know platform ack policy.
> * Receipts that survive restart and can drive edits, deletes, recovery, and duplicate suppression.
> * A smaller public SDK. Bundled plugins can use internal runtime helpers, but third-party plugins should see one coherent message API.
> * Agent-specific behavior: sessions, transcripts, block streaming, tool progress, approvals, media directives, silent replies, and group mention history.

在那套模型之外 OpenClaw 还需要：

- 在直接传输调用之前持久化的发送意图。
- 带 begin / commit / fail 的显式 send 上下文。
- 知道平台确认策略的 receive 上下文。
- 重启后存活的回执，能驱动编辑、删除、恢复和重复抑制。
- 更小的公共 SDK。内置插件可以用内部 runtime 助手，但第三方插件应该看到一个连贯的 message API。
- agent 专属行为：会话、transcript、block streaming、工具进度、批准、媒体指令、静默回复、群 @ 历史。

> `thread.post()` style promises are not enough for OpenClaw. They hide the transaction boundary that decides whether a send is recoverable.

`thread.post()` 风格的 Promise 不够 OpenClaw 用。它们隐藏了那条决定"send 是否可恢复"的事务边界。

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

`receive` 拥有接收生命周期。

`send` 拥有发送生命周期。

`live` 拥有预览、编辑、进度、流式状态。

`state` 拥有持久化意图存储、回执、幂等、恢复、锁、去重。

---

> ## Message terms

## 消息术语

> ### Message

### Message

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

一条归一化消息是平台无关的：

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

### Target

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

target 描述消息在哪里：

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

### Relation

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

reply 是一种关系，不是 API 根：

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

让同一条 send 路径处理常规回复、cron 通知、批准提示、任务完成、message-tool 发送、CLI 或 Control UI 发送、sub-agent 结果、自动化发送。

> ### Origin

### Origin

> Origin describes who produced a message and how OpenClaw should treat echoes of that message. It is separate from relation: a message can be a reply to a user and still be OpenClaw-originated operational output.

origin 描述消息是谁产生的、OpenClaw 应该怎么对待它的回声。它和关系是两码事：一条消息可以既是对用户的回复，又是 OpenClaw 来源的运维输出。

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

核心拥有"OpenClaw 来源输出"的含义。通道决定怎么把这个 origin 编码进自己的传输里。

> The first required use is gateway failure output. Humans should still see messages such as "Agent failed before reply" or "Missing API key", but tagged OpenClaw operational output must not be accepted as bot-authored input in shared rooms when `allowBots` is enabled.

第一个必需用例是 Gateway 失败输出。人类仍然应该能看到 "Agent failed before reply" 或 "Missing API key" 这种消息，但带 OpenClaw 运维标签的输出在 `allowBots` 打开的共享房间里不能被当作 bot 作者的输入接受。

> ### Receipt

### Receipt

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

回执是从持久化意图到将来 edit、delete、预览 finalization、重复抑制、恢复之间的桥。

> A receipt can describe one platform message or a multi-part delivery. Chunked text, media plus text, voice plus text, and card fallbacks must preserve all platform ids while still exposing a primary id for threading and later edits.

一份回执可以描述一条平台消息，也可以描述多部分投递。分片文本、媒体加文本、语音加文本、card 降级都必须保留所有平台 id，同时提供一个主 id 给 threading 和后续 edit 用。

---

> ## Receive context

## Receive 上下文

> Receiving should not be a bare helper call. The core needs a context that knows dedupe, routing, session recording, and platform ack policy.

接收不该是一个裸的助手调用。核心需要一个上下文，懂去重、路由、会话记录和平台确认策略。

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
  -> 启动 receive 上下文
  -> 归一化
  -> 分类
  -> dedupe 和自回声闸口
  -> 路由和授权
  -> 记录接收会话元数据
  -> 派发 agent 运行
  -> 持久化发送通过 send 上下文进行
  -> 提交 receive
  -> 策略允许时 ack 平台
```

> Ack is not one thing. The receive contract must keep these signals separate:
>
> * **Transport ack:** tells the platform webhook or socket that OpenClaw accepted the event envelope. Some platforms require this before dispatch.
> * **Polling offset ack:** advances a cursor so the same event is not fetched again. This must not advance past work that cannot be recovered.
> * **Inbound record ack:** confirms OpenClaw persisted enough inbound metadata to dedupe and route a redelivery.
> * **User-visible receipt:** optional read/status/typing behavior; never a durability boundary.

确认不是一回事。receive 契约必须把这几种信号分开：

- **传输确认**：告诉平台 webhook 或 socket：OpenClaw 接受了事件信封。有些平台要求在派发之前先确认。
- **polling offset 确认**：往前推游标，让同一个事件不会被再拉一次。它不能越过那些还没法恢复的工作。
- **接收记录确认**：确认 OpenClaw 已经把够去重和路由重投的接收元数据持久化了。
- **用户可见回执**：可选的已读 / 状态 / 输入中行为；永远不是持久化边界。

> `ReceiveAckPolicy` controls transport or polling acknowledgement only. It must not be reused for read receipts or status reactions.

`ReceiveAckPolicy` 只控制传输或 polling 的确认。不要复用到已读回执或状态反应上。

> Before bot authorization, receive must apply the shared OpenClaw echo policy when the channel can decode message origin metadata:

通道能解码消息 origin 元数据时，receive 必须在 bot 授权之前应用共享的 OpenClaw 回声策略：

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

这个丢弃是基于标签、不是基于文本。一条 bot 作者的房间消息，文本看起来一样是 Gateway 失败、但没带 OpenClaw origin 元数据，仍然走常规的 `allowBots` 授权。

> Ack policy is explicit:
>
> ```typescript
> type ReceiveAckPolicy =
>   | { kind: "immediate"; reason: "webhook-timeout" | "platform-contract" }
>   | { kind: "after-record" }
>   | { kind: "after-durable-send" }
>   | { kind: "manual" };
> ```

确认策略是显式的：

```typescript
type ReceiveAckPolicy =
  | { kind: "immediate"; reason: "webhook-timeout" | "platform-contract" }
  | { kind: "after-record" }
  | { kind: "after-durable-send" }
  | { kind: "manual" };
```

> Telegram polling now uses the receive-context ack policy for its persisted restart watermark. The tracker still observes grammY updates as they enter the middleware chain, but OpenClaw persists only the safe completed update id after successful dispatch, leaving failed or lower pending updates replayable after a restart. Telegram's upstream `getUpdates` fetch offset is still controlled by the polling library, so the remaining deeper cut is a fully durable polling source if we need platform-level redelivery beyond OpenClaw's restart watermark. Webhook platforms may need immediate HTTP ack, but they still need inbound dedupe and durable outbound send intents because webhooks can redeliver.

Telegram polling 现在用 receive 上下文确认策略来维护其持久化的重启水位。tracker 仍然观察 grammY update 进入 middleware 链，但 OpenClaw 只在派发成功后持久化"安全已完成"的 update id，让失败或更低的 pending update 在重启后仍可重放。Telegram 上游的 `getUpdates` 拉取偏移仍由 polling 库控制，所以更深层的切口是一个完全持久化的 polling 源 —— 当我们需要超越 OpenClaw 重启水位的平台级重投时再做。webhook 平台可能需要立即 HTTP 确认，但仍然需要接收去重和持久化发送意图，因为 webhook 也会重投。

---

> ## Send context

## Send 上下文

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

推荐编排：

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

这个 helper 展开为：

```text
启动持久化意图
  -> 渲染
  -> 可选的 preview / edit / stream 工作
  -> 标记 sending
  -> 平台最终 send 或最终 edit
  -> 标记 committing，带原始 receipt
  -> 提交 receipt
  -> ack 持久化意图
  -> 分类失败时 fail 持久化意图
```

> The intent must exist before transport I/O. A restart after begin but before commit is recoverable.

意图必须在传输 I/O 之前存在。begin 之后、commit 之前的重启是可恢复的。

> The dangerous boundary is after platform success and before receipt commit. If a process dies there, OpenClaw cannot know whether the platform message exists unless the adapter provides native idempotency or a receipt reconciliation path. Those attempts must resume in `unknown_after_send`, not blindly replay. Channels without reconciliation may choose at-least-once replay only if duplicate visible messages are an acceptable, documented tradeoff for that channel and relation. The current SDK reconciliation bridge requires the adapter to declare `reconcileUnknownSend`, then asks `durableFinal.reconcileUnknownSend` to classify an unknown entry as `sent`, `not_sent`, or `unresolved`; only `not_sent` permits replay, and unresolved entries stay terminal or retry only the reconciliation check.

危险边界是平台成功之后、回执提交之前。进程在那里挂掉，OpenClaw 没法知道平台消息是否存在 —— 除非适配器提供原生幂等或回执对账路径。这些尝试必须以 `unknown_after_send` 状态恢复，而不是盲目重放。没有对账机制的通道，只有当"重复可见消息"是该通道和该关系可接受、有文档的取舍时，才能选择"至少一次"重放。当前 SDK 的对账桥要求适配器声明 `reconcileUnknownSend`，然后让 `durableFinal.reconcileUnknownSend` 把一条未知条目分成 `sent`、`not_sent` 或 `unresolved`；只有 `not_sent` 允许重放，`unresolved` 条目终止或仅重试对账检查。

> Durability policy must be explicit:
>
> ```typescript
> type MessageDurabilityPolicy = "required" | "best_effort" | "disabled";
> ```

持久化策略必须显式：

```typescript
type MessageDurabilityPolicy = "required" | "best_effort" | "disabled";
```

> `required` means core must fail closed when it cannot write the durable intent. `best_effort` can fall through when persistence is unavailable. `disabled` keeps the old direct send behavior. During migration, legacy wrappers and public compatibility helpers default to `disabled`; they must not infer `required` from the fact that a channel has a generic outbound adapter.

`required` 表示核心写不进持久化意图时必须默认拒绝。`best_effort` 在持久化不可用时可以降级直发。`disabled` 保持旧版直接 send 行为。迁移期间，旧版包装和公共兼容助手默认 `disabled`；它们不能因为某个通道有通用 outbound 适配器就推断成 `required`。

> Send contexts also own channel-local post-send effects. A migration is not safe if durable delivery bypasses local behavior that was previously attached to the channel's direct send path. Examples include self-echo suppression caches, thread participation markers, native edit anchors, model-signature rendering, and platform-specific duplicate guards. Those effects must either move into the send adapter, the render adapter, or a named send-context hook before that channel can enable durable generic final delivery.

send 上下文也拥有通道本地的 post-send 副作用。如果持久化投递绕开了之前附在通道直接 send 路径上的本地行为，迁移就不安全。例子包括：自回声抑制缓存、thread 参与标记、原生 edit 锚点、模型签名渲染、平台专属重复护栏。这些副作用必须先挪到 send 适配器、渲染适配器或一个命名的 send 上下文 hook 里，该通道才能启用持久化的通用最终投递。

> Send helpers must return receipts all the way back to their caller. Durable wrappers cannot swallow message ids or replace a channel delivery result with `undefined`; buffered dispatchers use those ids for thread anchors, later edits, preview finalization, and duplicate suppression.

send helper 必须把回执一路返回给调用方。持久化包装不能吞掉消息 id，也不能把通道投递结果替换成 `undefined`；缓冲 dispatcher 用这些 id 来做 thread 锚点、后续 edit、预览收尾和重复抑制。

> Fallback sends operate on batches, not single payloads. Silent-reply rewrites, media fallback, card fallback, and chunk projection can all produce more than one deliverable message, so a send context must either deliver the whole projected batch or explicitly document why only one payload is valid.

降级发送以批次为单位、不是单个 payload。静默回复改写、媒体降级、card 降级、chunk 投影都可能产生多于一条可投递消息，所以 send 上下文要么投递整批投影，要么显式文档化为什么只有一个 payload 是合法的。

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

这种降级如果是持久化的，整个投影批次必须由一份持久化 send 意图或另一种原子批次计划来表示。一条一条记 payload 不够：payload 之间的崩溃会让部分可见降级已经发出去、剩下的 payload 却没有持久化记录。恢复必须知道哪些 unit 已经有回执，然后要么只重放缺失的 unit、要么把这个批次标成 `unknown_after_send` 直到适配器对账。

---

> ## Live context

## Live 上下文

> Preview, edit, progress, and stream behavior should be one opt-in lifecycle.

预览、编辑、进度、流式行为应该是一个可选启用的生命周期。

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

实时状态有足够的持久度来恢复或抑制重复：

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

应当覆盖当前行为：

- Telegram：send + edit 预览，预览过旧后发新 final。
- Discord：send + edit 预览，遇到媒体 / 错误 / 显式回复时取消。
- Slack：根据 thread 形态选原生流或草稿预览。
- Mattermost：草稿 post 收尾。
- Matrix：草稿 event 收尾，不匹配时 redaction。
- Teams：原生 progress 流。
- QQ Bot：流式或累积降级。

---

> ## Adapter surface

## 适配器面

> The public SDK target should be one subpath:
>
> ```typescript
> import { defineChannelMessageAdapter } from "openclaw/plugin-sdk/channel-message";
> ```

公共 SDK 目标应该是一个子路径：

```typescript
import { defineChannelMessageAdapter } from "openclaw/plugin-sdk/channel-message";
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

send 适配器：

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

receive 适配器：

```typescript
type MessageReceiveAdapter<TRaw = unknown> = {
  normalize(raw: TRaw, ctx: MessageNormalizeContext): Promise<ChannelMessage>;
  classify?(message: ChannelMessage): Promise<MessageEventClass>;
  preflight?(message: ChannelMessage, event: MessageEventClass): Promise<MessagePreflightResult>;
  ackPolicy?(message: ChannelMessage, event: MessageEventClass): ReceiveAckPolicy;
};
```

> Before preflight authorization, core must run the shared OpenClaw echo predicate whenever `origin.decode` returns OpenClaw-origin metadata. The receive adapter supplies platform facts such as bot author and room shape; core owns the drop decision and ordering so channels do not reimplement text filters.

预检授权之前，只要 `origin.decode` 返回了 OpenClaw 来源元数据，核心就必须跑共享的 OpenClaw 回声断言。receive 适配器提供平台事实，比如是否 bot 作者、房间形态；核心拥有 drop 决策和顺序，让通道不必各自实现文本过滤。

> Origin adapter:
>
> ```typescript
> type MessageOriginAdapter<TRaw = unknown, TNative = unknown> = {
>   encode?(origin: MessageOrigin): TNative | undefined;
>   decode?(raw: TRaw): MessageOrigin | undefined;
> };
> ```

origin 适配器：

```typescript
type MessageOriginAdapter<TRaw = unknown, TNative = unknown> = {
  encode?(origin: MessageOrigin): TNative | undefined;
  decode?(raw: TRaw): MessageOrigin | undefined;
};
```

> Core sets `MessageOrigin`. Channels only translate it to and from native transport metadata. Slack maps this to `chat.postMessage({ metadata })` and inbound `message.metadata`; Matrix can map it to extra event content; channels without native metadata can use a receipt/outbound registry when that is the best available approximation.

核心设置 `MessageOrigin`。通道只负责把它和原生传输元数据互译。Slack 把它映射到 `chat.postMessage({ metadata })` 和接收的 `message.metadata`；Matrix 可以映射到额外 event content；没有原生元数据的通道可以用回执 / outbound 注册表作为现有最佳近似。

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

## 公共 SDK 收缩

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

新的公共面应该吸收或废弃这些概念区域：

- `reply-runtime`
- `reply-dispatch-runtime`
- `reply-reference`
- `reply-chunking`
- `reply-payload`
- `inbound-reply-dispatch`
- `channel-reply-pipeline`
- `outbound-runtime` 的大部分公开用法
- 各种临时草稿流式生命周期助手

> Compatibility subpaths can remain as wrappers, but new third-party plugins should not need them.

兼容子路径可以以包装器形式保留，但新的第三方插件不该再需要它们。

> Bundled plugins may keep internal helper imports through reserved runtime subpaths while migrating. Public docs should steer plugin authors to `plugin-sdk/channel-message` once it exists.

内置插件迁移期间可以通过保留的 runtime 子路径继续 import 内部 helper。公共文档应当在 `plugin-sdk/channel-message` 出现后引导插件作者去用它。

---

> ## Relationship to channel turn

## 与 channel turn 的关系

> `runtime.channel.turn.*` should stay during migration.

迁移期间 `runtime.channel.turn.*` 应当保留。

> It should become a compatibility adapter:
>
> ```text
> channel.turn.run
>   -> messages.receive context
>   -> session dispatch
>   -> messages.send context for visible output
> ```

它应当变成一个兼容适配器：

```text
channel.turn.run
  -> messages.receive 上下文
  -> 会话派发
  -> 用 messages.send 上下文发可见输出
```

> `channel.turn.runPrepared` should also remain initially:
>
> ```text
> channel-owned dispatcher
>   -> messages.receive record/finalize bridge
>   -> messages.live for preview/progress
>   -> messages.send for final delivery
> ```

`channel.turn.runPrepared` 也先保留：

```text
通道自有 dispatcher
  -> messages.receive 的 record / finalize 桥
  -> messages.live 用于 preview / 进度
  -> messages.send 用于最终投递
```

> After all bundled plugins and known third-party compatibility paths are bridged, `channel.turn` can be deprecated. It should not be removed until there is a published SDK migration path and contract tests proving old plugins still work or fail with a clear version error.

所有内置插件和已知第三方兼容路径都桥接好后，`channel.turn` 可以废弃。在 SDK 迁移路径发布、契约测试证明老插件仍然工作或带清晰版本错误失败之前，不要删它。

---

> ## Compatibility guardrails

## 兼容护栏

> During migration, generic durable delivery is opt-in for any channel whose existing delivery callback has side effects beyond "send this payload".

迁移期间，对那些"现有投递回调有'send 这个 payload' 之外副作用"的通道，通用持久化投递是 opt-in 的。

> Legacy entry points are non-durable by default:
>
> * `channel.turn.run` and `dispatchAssembledChannelTurn` use the channel's delivery callback unless that channel explicitly supplies an audited durable policy/options object.
> * `channel.turn.runPrepared` stays channel-owned until the prepared dispatcher explicitly calls the send context.
> * Public compatibility helpers such as `recordInboundSessionAndDispatchReply`, `dispatchInboundReplyWithBase`, and direct-DM helpers never inject generic durable delivery before the caller-provided `deliver` or `reply` callback.

旧入口默认非持久化：

- `channel.turn.run` 和 `dispatchAssembledChannelTurn` 用通道自己的投递回调，除非通道显式提供经过审计的持久化策略 / options 对象。
- `channel.turn.runPrepared` 在 prepared dispatcher 显式调 send 上下文之前保持通道自有。
- 公共兼容助手如 `recordInboundSessionAndDispatchReply`、`dispatchInboundReplyWithBase`、私聊助手，从不在调用者提供的 `deliver` 或 `reply` 回调之前注入通用持久化投递。

> For migration bridge types, `durable: undefined` means "not durable". The durable path is enabled only by an explicit policy/options value. `durable: false` can remain as a compatibility spelling, but implementation should not require every unmigrated channel to add it.

对迁移桥类型，`durable: undefined` 表示"不持久化"。持久化路径只能由显式策略 / options 值启用。`durable: false` 可以作为兼容写法保留，但实现不该要求每个未迁移通道都加上它。

> Current bridge code must keep the durability decision explicit:
>
> * Durable final delivery returns a discriminated status. `handled_visible` and `handled_no_send` are terminal; `unsupported` and `not_applicable` may fall back to channel-owned delivery; `failed` propagates the send failure.
> * Generic durable final delivery is gated by adapter capabilities such as silent delivery, reply target preservation, native quote preservation, and message-sending hooks. Missing parity should choose channel-owned delivery, not a generic send that changes user-visible behavior.
> * Queue-backed durable sends expose a delivery intent reference. Existing `pendingFinalDelivery*` session fields can carry the intent id during the transition; the end state is a `MessageSendIntent` store instead of frozen reply text plus ad hoc context fields.

当前桥代码必须保持持久化决定的显式性：

- 持久化最终投递返回一个判别状态。`handled_visible` 和 `handled_no_send` 终结；`unsupported` 和 `not_applicable` 可以降级到通道自有投递；`failed` 把 send 失败传出去。
- 通用持久化最终投递由适配器能力闸门控制 —— 静默投递、回复目标保留、原生引用保留、message-sending hook。缺失对等行为时应当选通道自有投递，不要选一个会改变用户可见行为的通用 send。
- 队列支持的持久化 send 暴露一个 delivery 意图引用。过渡期间，已有的 `pendingFinalDelivery*` 会话字段可以承载意图 id；终态是 `MessageSendIntent` 存储，不再是冻结的 reply 文本加临时上下文字段。

> Do not enable the generic durable path for a channel until all of these are true:
>
> * The generic send adapter executes the same rendering and transport behavior as the old direct path.
> * Local post-send side effects are preserved through the send context.
> * The adapter returns receipts or delivery results with all platform message ids.
> * Prepared dispatcher paths either call the new send context or stay documented as outside the durable guarantee.
> * Fallback delivery handles every projected payload, not only the first one.
> * Durable fallback delivery records the whole projected payload array as one replayable intent or batch plan.

通道在以下全部成立之前不要启用通用持久化路径：

- 通用 send 适配器跟旧直接路径执行同样的渲染和传输行为。
- 本地 post-send 副作用通过 send 上下文保留。
- 适配器返回回执或投递结果，含所有平台消息 id。
- prepared dispatcher 路径要么调新 send 上下文，要么文档明确说不在持久化保证范围内。
- 降级投递处理每个投影 payload，不只是第一个。
- 持久化降级投递把整个投影 payload 数组记成一份可重放的意图或 批次计划。

> Concrete migration hazards to preserve:
>
> * iMessage monitor delivery records sent messages in an echo cache after a successful send. Durable final sends must still populate that cache, otherwise OpenClaw can re-ingest its own final replies as inbound user messages.
> * Tlon appends an optional model signature and records participated threads after group replies. Generic durable delivery must not bypass those effects; either move them into Tlon render/send/finalize adapters or keep Tlon on the channel-owned path.
> * Discord and other prepared dispatchers already own direct delivery and preview behavior. They are not covered by an assembled-turn durable guarantee until their prepared dispatchers explicitly route finals through the send context.
> * Telegram silent fallback delivery must deliver the full projected payload array. A single-payload shortcut can drop additional fallback payloads after projection.
> * LINE, Zalo, Nostr, and other existing assembled/helper paths may have reply-token handling, media proxying, sent-message caches, loading/status cleanup, or callback-only targets. They stay on channel-owned delivery until those semantics are represented by the send adapter and verified by tests.
> * Direct-DM helpers can have a reply callback that is the only correct transport target. Generic outbound must not guess from `OriginatingTo` or `To` and skip that callback.
> * OpenClaw gateway failure output must stay visible to humans, but tagged bot-authored room echoes must be dropped before `allowBots` authorization. Channels must not implement this with visible-text prefix filters except as a short emergency stopgap; the durable contract is structured origin metadata.

具体的迁移风险，要保留：

- iMessage monitor 投递在 send 成功后会把发出消息存进 echo 缓存。持久化最终 send 仍要填这个缓存，否则 OpenClaw 可能把自己的最终回复又作为接收用户消息读回来。
- Tlon 在群回复后追加可选的 model 签名并记参与过的 thread。通用持久化投递不能绕开这些副作用；要么把它们挪到 Tlon 的渲染 / send / finalize 适配器，要么让 Tlon 留在通道自有路径上。
- Discord 和其他 prepared dispatcher 已经拥有直接投递和预览行为。在它们的 prepared dispatcher 显式把 final 路由到 send 上下文之前，"已组装轮次的持久化保证"不覆盖它们。
- Telegram 静默降级投递必须投递完整的投影 payload 数组。单 payload 捷径会在投影后丢掉额外的降级 payload。
- LINE、Zalo、Nostr 和其他现有 assembled / helper 路径可能有 reply-token 处理、媒体代理、发送消息缓存、loading / 状态清理或只能用回调的目标。它们留在通道自有投递上，直到这些语义由 send 适配器表达且测试验证通过。
- 私聊助手可能有一个 reply 回调是唯一正确的传输目标。通用 outbound 不能从 `OriginatingTo` 或 `To` 猜，跳过这个回调。
- OpenClaw Gateway 失败输出必须对人类可见，但带标签的、bot 作者的房间回声必须在 `allowBots` 授权之前 drop。通道不能用可见文本前缀过滤实现这件事 —— 短期应急除外；持久契约是结构化 origin 元数据。

---

> ## Internal storage

## 内部存储

> The durable queue should store message send intents, not reply payloads.

持久化队列应当存消息 send 意图，不是 reply payload。

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
加载 pending 或 sending 的 intent
  -> 拿幂等锁
  -> receipt 已提交则跳过
  -> 重建 send 上下文
  -> 必要时渲染
  -> 必要时对账 unknown_after_send
  -> 调适配器 send / edit / finalize
  -> 提交 receipt、标 unknown_after_send 或排队重试
```

> The queue should keep enough identity to replay through the same account, thread, target, formatting policy, and media rules after restart.

队列要保留足够身份，让重启后可以走同一个账号、thread、target、格式化策略和媒体规则重放。

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

通道适配器把传输失败分到封闭类别：

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
- `invalid_payload` 不重试 —— 除非有渲染降级。
- `auth` 或 `permission` 不重试，直到配置变更。
- `not_found` 时，让实时收尾在通道声明安全的情况下从 edit 降级到新 send。
- `conflict` 时，用回执 / 幂等规则判断消息是否已存在。
- 适配器可能完成了平台 I/O 但回执提交之前发生的任何错误都成为 `unknown_after_send`，除非适配器能证明平台操作没发生。

---

> ## Channel mapping

## 通道映射

> | Channel         | Target migration                                                                                                                                                                                                                                                                                                                                               |
> | --------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
> | Telegram        | Receive ack policy plus durable final sends. Live adapter owns send plus edit preview, stale preview final send, topics, quote-reply preview skip, media fallback, and retry-after handling.                                                                                                                                                                   |
> | Discord         | Send adapter wraps existing durable payload delivery. Live adapter owns draft edit, progress draft, media/error preview cancel, reply target preservation, and message id receipts. Audit bot-authored gateway-failure echoes in shared rooms; use an outbound registry or other native equivalent if Discord cannot carry origin metadata on normal messages. |
> | Slack           | Send adapter handles normal chat posts. Live adapter chooses native stream when thread shape supports it, otherwise draft preview. Receipts preserve thread timestamps. Origin adapter maps OpenClaw gateway failures to Slack `chat.postMessage.metadata` and drops tagged bot-room echoes before `allowBots` authorization.                                  |
> | WhatsApp        | Send adapter owns text/media send with durable final intents. Receive adapter handles group mention and sender identity. Live can stay absent until WhatsApp has an editable transport.                                                                                                                                                                        |
> | Matrix          | Live adapter owns draft event edits, finalization, redaction, encrypted media constraints, and reply-target mismatch fallback. Receive adapter owns encrypted event hydration and dedupe. Origin adapter should encode OpenClaw gateway-failure origin into Matrix event content and drop configured-bot room echoes before `allowBots` handling.              |
> | Mattermost      | Live adapter owns one draft post, progress/tool folding, finalization in place, and fresh-send fallback.                                                                                                                                                                                                                                                       |
> | Microsoft Teams | Live adapter owns native progress and block stream behavior. Send adapter owns activities and attachment/card receipts.                                                                                                                                                                                                                                        |
> | Feishu          | Render adapter owns text/card/raw rendering. Live adapter owns streaming cards and duplicate final suppression. Send adapter owns comments, topic sessions, media, and voice suppression.                                                                                                                                                                      |
> | QQ Bot          | Live adapter owns C2C streaming, accumulator timeout, and fallback final send. Render adapter owns media tags and text-as-voice.                                                                                                                                                                                                                               |
> | Signal          | Simple receive plus send adapter. No live adapter unless signal-cli adds reliable edit support.                                                                                                                                                                                                                                                                |
> | iMessage        | Simple receive plus send adapter. iMessage send must preserve monitor echo-cache population before durable finals can bypass monitor delivery.                                                                                                                                                                                                                 |
> | Google Chat     | Simple receive plus send adapter with thread relation mapped to spaces and thread ids. Audit `allowBots=true` room behavior for tagged OpenClaw gateway-failure echoes.                                                                                                                                                                                        |
> | LINE            | Simple receive plus send adapter with reply-token constraints modeled as target/relation capability.                                                                                                                                                                                                                                                           |
> | Nextcloud Talk  | SDK receive bridge plus send adapter.                                                                                                                                                                                                                                                                                                                          |
> | IRC             | Simple receive plus send adapter, no durable edit receipts.                                                                                                                                                                                                                                                                                                    |
> | Nostr           | Receive plus send adapter for encrypted DMs; receipts are event ids.                                                                                                                                                                                                                                                                                           |
> | QA Channel      | Contract-test adapter for receive, send, live, retry, and recovery behavior.                                                                                                                                                                                                                                                                                   |
> | Synology Chat   | Simple receive plus send adapter.                                                                                                                                                                                                                                                                                                                              |
> | Tlon            | Send adapter must preserve model-signature rendering and participated-thread tracking before generic durable final delivery is enabled.                                                                                                                                                                                                                        |
> | Twitch          | Simple receive plus send adapter with rate-limit classification.                                                                                                                                                                                                                                                                                               |
> | Zalo            | Simple receive plus send adapter.                                                                                                                                                                                                                                                                                                                              |
> | Zalo Personal   | Simple receive plus send adapter.                                                                                                                                                                                                                                                                                                                              |

| 通道               | 目标迁移                                                                                                                                                                                                                                                                                                       |
| ------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Telegram           | receive 确认策略 + 持久化 final send。实时适配器拥有 send + edit 预览、过期预览的新 final send、topic、quote-reply 跳过预览、媒体降级、retry-after 处理。                                                                                                                                                  |
| Discord            | send 适配器包装现有持久化 payload 投递。实时适配器拥有草稿 edit、progress 草稿、媒体 / 错误时的预览 cancel、回复目标保留、消息 id 回执。审计 bot 作者的 Gateway 失败回声在共享房间里的行为；Discord 不能在常规消息上承载 origin 元数据时用 outbound 注册表或其他原生等价物。                              |
| Slack              | send 适配器处理常规 chat post。实时适配器在 thread 形态支持时选原生流，否则用草稿预览。回执保留 thread 时间戳。origin 适配器把 OpenClaw Gateway 失败映射到 Slack `chat.postMessage.metadata`，在 `allowBots` 授权之前 drop 带标签的 bot-room 回声。                                                       |
| WhatsApp           | send 适配器拥有文本 / 媒体 send，带持久化 final 意图。receive 适配器处理群 @ 和发件人身份。在 WhatsApp 有可编辑传输之前，实时可以缺席。                                                                                                                                                                  |
| Matrix             | 实时适配器拥有草稿 event edit、收尾、redaction、加密媒体约束、回复目标不匹配时的降级。receive 适配器拥有加密 event 的 hydrate 和去重。origin 适配器应把 OpenClaw Gateway 失败 origin 编码进 Matrix event content，在 `allowBots` 处理之前 drop 已配置 bot 的房间回声。                                       |
| Mattermost         | 实时适配器拥有一个草稿 post、进度 / 工具折叠、原地收尾、新 send 降级。                                                                                                                                                                                                                                          |
| Microsoft Teams    | 实时适配器拥有原生 progress 和 block 流式行为。send 适配器拥有 activity 和附件 / card 回执。                                                                                                                                                                                                                |
| 飞书               | 渲染适配器拥有 text / card / raw 渲染。实时适配器拥有流式 card 和重复 final 抑制。send 适配器拥有评论、topic 会话、媒体、语音抑制。                                                                                                                                                                            |
| QQ Bot             | 实时适配器拥有 C2C 流式、累加器超时、降级 final send。渲染适配器拥有媒体标签和文本作语音。                                                                                                                                                                                                                  |
| Signal             | 简单的 receive 加 send 适配器。signal-cli 没有可靠 edit 支持时不需要实时适配器。                                                                                                                                                                                                                              |
| iMessage           | 简单的 receive 加 send 适配器。在持久化 final 可以绕过 monitor 投递之前，iMessage send 必须保留 monitor echo 缓存填充。                                                                                                                                                                                          |
| Google Chat        | 简单的 receive 加 send 适配器，thread 关系映射到 space 和 thread id。审计 `allowBots=true` 房间对带标签 OpenClaw Gateway 失败回声的行为。                                                                                                                                                                          |
| LINE               | 简单的 receive 加 send 适配器，reply-token 约束建模为 target / 关系能力。                                                                                                                                                                                                                                  |
| Nextcloud Talk     | SDK receive 桥 + send 适配器。                                                                                                                                                                                                                                                                                  |
| IRC                | 简单的 receive 加 send 适配器，没有持久 edit 回执。                                                                                                                                                                                                                                                          |
| Nostr              | 加密 DM 的 receive + send 适配器；回执是 event id。                                                                                                                                                                                                                                                          |
| QA Channel         | 给 receive、send、实时、retry、recovery 行为做契约测试用的适配器。                                                                                                                                                                                                                                                  |
| Synology Chat      | 简单的 receive 加 send 适配器。                                                                                                                                                                                                                                                                                  |
| Tlon               | send 适配器在启用通用持久化 final 投递之前必须保留 model 签名渲染和参与 thread 追踪。                                                                                                                                                                                                                            |
| Twitch             | 简单的 receive 加 send 适配器，带限速分类。                                                                                                                                                                                                                                                                      |
| Zalo               | 简单的 receive 加 send 适配器。                                                                                                                                                                                                                                                                                  |
| Zalo Personal      | 简单的 receive 加 send 适配器。                                                                                                                                                                                                                                                                                  |

---

> ## Migration plan

## 迁移计划

> ### Phase 1: Internal Message Domain
> ### Phase 2: Durable Send Core
> ### Phase 3: Channel Turn Bridge
> ### Phase 4: Prepared Dispatcher Bridge
> ### Phase 5: Unified Live Lifecycle
> ### Phase 6: Public SDK
> ### Phase 7: All Senders
> ### Phase 8: Deprecate Turn

### 阶段 1：内部 Message 领域
### 阶段 2：持久化 Send 核心
### 阶段 3：Channel Turn 桥
### 阶段 4：Prepared Dispatcher 桥
### 阶段 5：统一 Live 生命周期
### 阶段 6：公共 SDK
### 阶段 7：所有发送者
### 阶段 8：废弃 Turn

> 阶段 1：在 `src/channels/message/*` 加 message、target、relation、origin、receipt、capability、durable intent、receive 上下文、send 上下文、live 上下文、failure 类型。在迁移桥的 reply payload 里加可选 `origin: MessageOrigin`，等重构替换 reply payload 时再把它挪到 `ChannelMessage` 和渲染消息类型。先内部用，等适配器和测试证明形态可行。加状态转换和序列化的单测。

> 阶段 2：把现有 outbound 队列从 reply payload 持久化迁到持久化 message send 意图。让一份持久化 send 意图带投影 payload 数组或 batch 计划，不只一条 reply payload。通过兼容转换保留当前队列恢复行为。让 `deliverOutboundPayloads` 调 `messages.send`。把"final send 持久化"做成新消息生命周期里的默认行为，写不进意图时 fail-closed —— 适配器声明 replay-safe 之后。现有 channel-turn 和 SDK 兼容路径在本阶段仍然默认直接 send。一致地记录 receipt。把 receipt 和投递结果一路返回原 dispatcher 调用方，不再把持久化 send 当成一种终结的副作用。让 origin 通过持久化 send 意图保留下来，恢复、重放、分片 send 都保留 OpenClaw 运维归属。

> 阶段 3：在 `messages.receive` 和 `messages.send` 之上重新实现 `channel.turn.run` 和 `dispatchAssembledChannelTurn`。保持当前 fact 类型稳定。默认保留旧行为。已组装轮次的通道在适配器显式 opt-in replay-safe 持久化策略后才变成持久化。`durable: false` 作为兼容逃生口保留，给那些 finalize 原生 edit、还不能安全重放的路径用，但不要靠 `false` 标记保护未迁移通道。已组装轮次的持久化默认值只在新消息生命周期里启用，且需通道映射证明通用 send 路径保留旧投递语义。

> 阶段 4：用 send 上下文桥替换 `deliverDurableInboundReplyPayload`。保留旧 helper 作为包装。优先迁 Telegram、WhatsApp、Slack、Signal、iMessage、Discord —— 它们已有持久化 final 的工作或更简单的 send 路径。除非 prepared dispatcher 显式 opt-in send 上下文，否则视它为未覆盖。文档和 changelog 必须说"已组装通道轮次"或具名迁移过的通道路径，不能宣称所有自动 final reply 都覆盖了。`recordInboundSessionAndDispatchReply`、私聊 helper 等公共兼容 helper 保持行为不变。它们之后可能暴露显式的 send 上下文 opt-in，但不能在调用者拥有的投递回调之前自动尝试通用持久化投递。

> 阶段 5：用两个 proof 适配器搭 `messages.live`：Telegram（send + edit + 过期 final send）和 Matrix（草稿收尾 + redaction 降级）。然后迁 Discord、Slack、Mattermost、Teams、QQ Bot、飞书。每个通道有等价测试之后才删重复的 preview 收尾代码。

> 阶段 6：加 `openclaw/plugin-sdk/channel-message`。文档化为通道插件 API 的优先选择。更新包导出、入口清单、生成的 API 基线、插件 SDK 文档。把 `MessageOrigin`、origin encode/decode hook、共享的 `shouldDropOpenClawEcho` 断言放进 channel-message SDK 面。保留旧子路径的兼容包装。内置插件迁移完成后，把以 reply 命名的 SDK helper 在文档里标为 deprecated。

> 阶段 7：把所有非 reply outbound 生产者搬到 `messages.send`：cron 和心跳通知；任务完成；hook 结果；批准提示和批准结果；message tool 发送；sub-agent 完成 announce；显式 CLI 或 Control UI send；自动化 / 广播路径。这是模型从"agent reply"变成"OpenClaw 发消息"的地方。

> 阶段 8：让 `channel.turn` 至少在一个兼容窗口期里保持为包装。发布迁移说明。用旧 import 跑插件 SDK 兼容测试。等没有内置插件再需要、且第三方契约已经有稳定替代之后，才删或藏老的内部 helper。

---

> ## Test plan

## 测试计划

> Unit tests / Integration tests / Channel tests / Validation

单测 / 集成测试 / 通道测试 / 验证（参见原文条目，覆盖：持久化 send 意图序列化和恢复、幂等 key 复用与重复抑制、回执提交与重放跳过、`unknown_after_send` 在适配器支持时重放前对账、失败分类策略、receive 确认策略顺序、reply / followup / system / broadcast 关系映射、Gateway 失败 origin 工厂和 `shouldDropOpenClawEcho` 断言、origin 在 payload 归一化 / 分片 / 持久队列序列化和恢复中保留；以及各通道场景的契约测试和 Vitest / Testbox / qa-channel 验证）。

---

> ## Open questions

## 开放问题

> * Whether Telegram should eventually replace the grammY runner source with a fully durable polling source that can control platform-level redelivery, not only OpenClaw's persisted restart watermark.
> * Whether durable live preview state should be stored in the same queue record as the final send intent or in a sibling live-state store.
> * How long compatibility wrappers stay documented after `plugin-sdk/channel-message` ships.
> * Whether third-party plugins should implement receive adapters directly or only provide normalize/send/live hooks through `defineChannelMessageAdapter`.
> * Which receipt fields are safe to expose in public SDK versus internal runtime state.
> * Whether side effects such as self-echo caches and participated-thread markers should be modeled as send-context hooks, adapter-owned finalize steps, or receipt subscribers.
> * Which channels have native origin metadata, which need persisted outbound registries, and which cannot offer reliable cross-bot echo suppression.

- Telegram 是否最终该把 grammY runner 源替换成一个完全持久化的 polling 源，能控制平台级重投，不仅是 OpenClaw 的持久化重启水位。
- 持久化的实时预览状态该和最终 send 意图存在同一条队列记录里，还是放在并列的实时-state 存储。
- `plugin-sdk/channel-message` 发布之后，兼容包装在文档里保留多久。
- 第三方插件应当直接实现 receive 适配器，还是只通过 `defineChannelMessageAdapter` 提供归一化 / send / 实时 hook。
- 回执字段哪些能安全暴露到公共 SDK 里、哪些只能留在内部 runtime 状态里。
- 自回声缓存和参与 thread 标记这种副作用，应当建模为 send 上下文 hook、适配器拥有的 finalize 步骤、还是回执订阅者。
- 哪些通道有原生 origin 元数据、哪些需要持久化的 outbound 注册表、哪些根本无法做可靠的跨 bot 回声抑制。

---

> ## Acceptance criteria

## 验收标准

> * Every bundled message channel sends final visible output through `messages.send`.
> * Every inbound message channel enters through `messages.receive` or a documented compatibility wrapper.
> * Every preview/edit/stream channel uses `messages.live` for draft state and finalization.
> * `channel.turn` is only a wrapper.
> * Reply-named SDK helpers are compatibility exports, not the recommended path.
> * Durable recovery can replay pending final sends after restart without losing the final response or duplicating already committed sends; sends whose platform outcome is unknown are reconciled before replay or documented as at-least-once for that adapter.
> * Durable final sends fail closed when the durable intent cannot be written, unless a caller explicitly selected a documented non-durable mode.
> * Legacy channel-turn and SDK compatibility helpers default to direct channel-owned delivery; generic durable send is explicit opt-in only.
> * Receipts preserve all platform message ids for multi-part deliveries and a primary id for threading/edit convenience.
> * Durable wrappers preserve channel-local side effects before replacing direct delivery callbacks.
> * Prepared dispatchers are not counted as durable until their final delivery path explicitly uses the send context.
> * Fallback delivery handles every projected payload.
> * Durable fallback delivery records every projected payload in one replayable intent or batch plan.
> * OpenClaw-originated gateway failure output is visible to humans but tagged bot-authored room echoes are dropped before bot authorization on channels that declare support for the origin contract.
> * The docs explain send, receive, live, state, receipts, relations, failure policy, migration, and test coverage.

- 每个内置消息通道都通过 `messages.send` 发最终可见输出。
- 每个接收消息通道都通过 `messages.receive` 或一个有文档的兼容包装进入。
- 每个预览 / edit / stream 通道都用 `messages.live` 做草稿状态和收尾。
- `channel.turn` 只是一个包装。
- reply 命名的 SDK helper 只是兼容导出，不是推荐路径。
- 持久化恢复能在重启后重放 pending 的最终 send，不丢最终响应、不重复已提交的 send；平台结果未知的 send 在重放前对账，或者按该适配器文档化为"至少一次"。
- 持久化最终 send 在写不进意图时 默认拒绝 —— 除非调用者显式选了一个文档化的非持久模式。
- 旧版 channel-turn 和 SDK 兼容助手默认直接走通道自有投递；通用持久化 send 必须显式 opt-in。
- 多部分投递的回执保留所有平台消息 id，并提供一个主 id 给 threading / edit 用。
- 持久化包装在替换直接投递回调之前先保留通道本地副作用。
- prepared dispatcher 在它的最终投递路径显式使用 send 上下文之前都不算持久化。
- 降级投递处理每一个投影 payload。
- 持久化降级投递把每一个投影 payload 记进一份可重放的意图或 批次计划。
- OpenClaw 来源的 Gateway 失败输出对人可见，但带标签的、bot 作者的房间回声在那些声明支持 origin 契约的通道上、在 bot 授权之前 drop。
- 文档讲清楚 send、receive、实时、state、回执、关系、失败策略、迁移、测试覆盖。

---

> ## Related

## 相关

> * [Messages](/concepts/messages)
> * [Streaming and chunking](/concepts/streaming)
> * [Progress drafts](/concepts/progress-drafts)
> * [Retry policy](/concepts/retry)

- [消息](/concepts/messages)
- [流式与分片](/concepts/streaming)
- [进度草稿](/concepts/progress-drafts)
- [重试策略](/concepts/retry)
