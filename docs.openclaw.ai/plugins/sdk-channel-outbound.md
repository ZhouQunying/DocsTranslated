# Channel Outbound API

## 架构精读

> 跳过不影响阅读翻译正文。

### 为什么 `sendDurableMessageBatch` 有四种结果而不只是成功/失败？

支付系统建模交易结果时不会只用布尔值——至少区分已结算、已拒绝、部分成功和超时。消息发送同理：`sent`（至少一条平台消息已交付）、`suppressed`（无平台消息应视为缺失）、`partial_failed`（至少一条已交付但后续负载或副作用失败）、`failed`（无平台回执）。好处是调用者可以根据具体结果做不同处理——部分失败时可能需要重试剩余消息，而不是整个批次重来。就像 AWS SQS 的批量发送 API 返回每条消息的独立结果。

---

Channel 插件应从 `openclaw/plugin-sdk/channel-outbound` 暴露 outbound 消息行为。使用 `openclaw/plugin-sdk/channel-inbound` 做接收/上下文/调度编排。

核心持有排队、持久化、通用重试策略、钩子、回执和共享 `message` 工具。插件持有原生发送/编辑/删除调用、目标归一化、平台线程、选定引用、通知标志、账户状态和平台特定副作用。

## 适配器

大多数插件定义一个 `message` 适配器：

```ts

  defineChannelMessageAdapter,
  createMessageReceiptFromOutboundResults,
} from "openclaw/plugin-sdk/channel-outbound";

export const demoMessageAdapter = defineChannelMessageAdapter({
  id: "demo",
  durableFinal: {
    capabilities: {
      text: true,
      replyTo: true,
      thread: true,
      messageSendingHooks: true,
    },
  },
  send: {
    text: async ({ cfg, to, text, accountId, replyToId, threadId, signal }) => {
      const sent = await sendDemoMessage({
        cfg,
        to,
        text,
        accountId: accountId ?? undefined,
        replyToId: replyToId ?? undefined,
        threadId: threadId == null ? undefined : String(threadId),
        signal,
      });

      return {
        receipt: createMessageReceiptFromOutboundResults({
          results: [{ channel: "demo", messageId: sent.id, conversationId: to }],
          kind: "text",
          threadId: threadId == null ? undefined : String(threadId),
          replyToId: replyToId ?? undefined,
        }),
      };
    },
  },
});
```

仅声明原生传输实际保留的能力。用从此子路径导出的契约辅助覆盖每个声明的发送、回执、实时预览和接收确认能力。

## 已有 Outbound 适配器

如果 channel 已有兼容的 `outbound` 适配器，从它派生消息适配器而非复制发送代码：

```ts

export const messageAdapter = createChannelMessageAdapterFromOutbound({
  id: "demo",
  outbound,
  durableFinal: {
    capabilities: {
      text: true,
      media: true,
    },
  },
});
```

## 持久发送

运行时发送辅助也在 `channel-outbound` 上：

- `sendDurableMessageBatch(...)`
- `withDurableMessageSendContext(...)`
- `deliverInboundReplyWithMessageSendContext(...)`
- 草稿流式/进度辅助如 `resolveChannelStreamingPreviewChunk(...)`

`sendDurableMessageBatch(...)` 返回一个显式结果：

- `sent`：至少一条可见平台消息已交付。
- `suppressed`：无平台消息应视为缺失。
- `partial_failed`：至少一条平台消息已交付，但后续负载或副作用失败。
- `failed`：未产生平台回执。

当批次混合已发送、已抑制和已失败负载时使用 `payloadOutcomes`。不要从空的遗留直接交付结果推断钩子取消。

## 兼容调度

Inbound 回复调度应通过 `channel-inbound` 的 `dispatchChannelInboundReply(...)` 组装。保持平台交付在交付适配器中；使用 `channel-outbound` 做消息适配器、持久发送、回执、实时预览和回复管道选项。
