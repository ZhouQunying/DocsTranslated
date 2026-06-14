# Channel Inbound API

## 架构精读

> 跳过不影响阅读翻译正文。

### 为什么把 channel 拆成 inbound 和 outbound 而不是一个统一 API？

Express.js 的 req/res 是同一个对象的两面——请求进来、响应出去，但它们的生命周期完全不同。Channel 插件同理：inbound 是平台事件到 agent 回复的路径——归一化、分类、预检、解析、记录、调度、完成。outbound 是消息发送到平台的路径——排队、持久化、重试、回执。混在一起就像把快递的揽件和派件写成同一个函数——代码简单了但每条路径的失败模式完全不同。拆开后 inbound 可以独立测试事件归一化，outbound 可以独立测试持久化发送。

---

Channel 插件应以 inbound 和 message 术语建模接收路径：

```text
平台事件 -> inbound 事实/上下文 -> agent 回复 -> 消息交付
```

使用 `openclaw/plugin-sdk/channel-inbound` 做 inbound 事件归一化、格式化、根和编排。使用 `openclaw/plugin-sdk/channel-outbound` 做原生发送、回执、持久交付和实时预览行为。

## 核心辅助

```ts

  buildChannelInboundEventContext,
  runChannelInboundEvent,
  dispatchChannelInboundReply,
} from "openclaw/plugin-sdk/channel-inbound";
```

- `buildChannelInboundEventContext(...)`：将归一化的 channel 事实投射到提示/会话上下文。
- `runChannelInboundEvent(...)`：对一个 inbound 平台事件运行摄取、分类、预检、解析、记录、调度和完成。
- `dispatchChannelInboundReply(...)`：用交付适配器记录并调度已组装的 inbound 回复。

注入的插件运行时在 `runtime.channel.inbound.*` 下暴露相同的高级辅助，供已接收运行时对象的捆绑/原生 channel 使用。

```ts
await runtime.channel.inbound.run({
  channel: "demo",
  accountId,
  raw: platformEvent,
  adapter: {
    ingest: normalizePlatformEvent,
    resolveTurn: resolveInboundReply,
  },
});
```

兼容调度器应组装 `dispatchChannelInboundReply(...)` 输入并保持平台交付在交付适配器中。新发送路径应优先使用消息适配器和持久消息辅助。

## 迁移

旧的 `runtime.channel.turn.*` 运行时别名已移除。使用：

- `runtime.channel.inbound.run(...)` 用于原始 inbound 事件。
- `runtime.channel.inbound.dispatchReply(...)` 用于已组装的回复上下文。
- `runtime.channel.inbound.buildContext(...)` 用于 inbound 上下文负载。
- `runtime.channel.inbound.runPreparedReply(...)` 仅用于 channel 持有的已准备调度路径，这些路径已组装自己的调度闭包。

新插件代码不应引入 `turn` 命名的 channel API。将模型或 agent turn 词汇保留在 agent/provider 代码中；channel 插件使用 inbound、message、delivery 和 reply 术语。
