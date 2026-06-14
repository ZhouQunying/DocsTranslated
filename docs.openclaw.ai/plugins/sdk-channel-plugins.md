# SDK: Channel 插件

## 架构精读

> 跳过不影响阅读翻译正文。

### 为什么 channel 插件不需要自己的发送/编辑/回复工具？

如果每个 channel 插件都自己实现 `send`、`edit`、`react` 工具，Slack 的发送和 Telegram 的发送在核心看来就是两个完全不同的工具。agent 回合需要知道"我现在在 Slack 还是 Telegram"才能调用正确的发送。OpenClaw 的做法是反过来：核心持有一个共享的 `message` 工具，所有 channel 统一使用。插件只持有平台特定的部分——配置解析、DM 安全策略、配对流程、会话 id 映射、出站传输和线程模型。就像 React 的架构：Reconciler（核心）持有 diff 算法和组件生命周期，Renderer（插件）持有 DOM 操作或 Canvas 绘制。好处是 agent 回合代码不关心消息发到哪个平台，channel 插件只做最小的平台适配。

第二个设计：审批作为能力接口。大多数 channel 插件不需要审批特定代码——核心持有同聊天 `/approve`、共享审批按钮负载和通用回退交付。只有需要原生审批交付的 channel（如 Slack 的原生按钮、Matrix 的反应 UX）才实现 `approvalCapability` 接口。这个接口分成几个子关注点。可用性检查账户是否配置。呈现将共享审批视图映射为原生负载。传输处理发送、更新、删除原生审批消息。交互管理按钮和反应的绑定钩子。就像微服务 API Gateway 的权限模型：基础权限由网关处理，只有需要额外授权的 API 才声明自定义权限。

第三个边界：提及策略的两层分离。提及检测分成两层。插件持有证据收集：回复机器人检测、引用检测、线程参与检查。共享策略持有评估：`requireMention`、显式提及结果、隐式提及允许列表、命令绕过、最终跳过决策。好处是策略逻辑集中在一个地方测试和维护，各 channel 只需提供平台特定的检测事实。就像安全过滤链：先收集事实（IP、UA、行为），再评估策略（限流、封禁、放行）。检测可以缓存和并行，策略可以热更新，两者独立演进。

---

本指南介绍如何构建将 OpenClaw 连接到消息平台的 channel 插件。如果尚未构建过 OpenClaw 插件，先阅读 [Getting Started](/plugins/building-plugins) 了解基本包结构和 manifest 设置。

## Channel 插件工作原理

Channel 插件不需要自己的发送/编辑/回复工具。OpenClaw 在核心中持有一个共享的 `message` 工具。插件持有：

- **配置** — 账户解析和设置向导
- **安全** — DM 策略和允许列表
- **配对** — DM 审批流程
- **会话语法** — 平台特定的会话 id 如何映射为基础聊天、线程 id 和父回退
- **出站** — 向平台发送文本、媒体和投票
- **线程** — 回复如何线程化
- **心跳输入** — 心跳交付目标的可选输入/忙碌信号

核心持有共享 message 工具、提示词接线、外部会话键形状、通用 `:thread:` 簿记和调度。

新 channel 插件还应通过 `defineChannelMessageAdapter` 暴露 `message` 适配器。适配器声明原生传输实际支持哪些持久最终发送能力，并将文本/媒体发送指向与旧版 `outbound` 适配器相同的传输函数。仅在契约测试证明原生副作用和返回回执时才声明能力。

### 消息适配器能力

预览能力的 channel 应声明 `message.live.capabilities`，如 `draftPreview`、`previewFinalization`、`progressUpdates`、`nativeStreaming` 或 `quietFinalization`。原地最终化草稿预览的 channel 还应声明 `message.live.finalizer.capabilities`，如 `finalEdit`、`normalFallback`、`discardPending`、`previewReceipt` 和 `retainOnAmbiguousFailure`。

入站接收者延迟平台确认时应声明 `message.receive.defaultAckPolicy` 和 `supportedAckPolicies`，而非将确认时序隐藏在监控本地状态中。

### 会话路由和线程

如果平台在会话 id 中存储额外范围，将该解析保持在插件中，使用 `messaging.resolveSessionConversation(...)`。这是将 `rawId` 映射为基础会话 id、可选线程 id、显式 `baseConversationId` 和任何 `parentConversationCandidates` 的标准钩子。返回 `parentConversationCandidates` 时，保持从最窄父到最宽/基础会话的排序。

使用 `openclaw/plugin-sdk/channel-route` 规范化路由类字段、比较子线程与父路由，或从 `{ channel, to, accountId, threadId }` 构建稳定的去重键。

### 提及策略

保持入站提及处理分为两层：

- 插件持有的证据收集
- 共享策略评估

插件本地逻辑适合处理：

- 回复机器人检测
- 引用机器人检测
- 线程参与检查
- 服务/系统消息排除
- 证明机器人参与所需的平台原生缓存

共享辅助适合处理：

- `requireMention`
- 显式提及结果
- 隐式提及允许列表
- 命令绕过
- 最终跳过决策

首选流程：

1. 计算本地提及事实
2. 将事实传入 `resolveInboundMentionDecision({ facts, policy })`
3. 在入站门控中使用 `decision.effectiveWasMentioned`、`decision.shouldBypassMention` 和 `decision.shouldSkip`

```typescript
const facts = {
  canDetectMention: true,
  wasMentioned: mentionMatch.matched,
  hasAnyMention: mentionMatch.hasExplicitMention,
  implicitMentionKinds: [
    ...implicitMentionKindWhen("reply_to_bot", isReplyToBot),
    ...implicitMentionKindWhen("quoted_bot", isQuoteOfBot),
  ],
};

const decision = resolveInboundMentionDecision({
  facts,
  policy: {
    isGroup,
    requireMention,
    allowedImplicitMentionKinds: requireExplicitMention
      ? []
      : ["reply_to_bot", "quoted_bot"],
    allowTextCommands,
    hasControlCommand,
    commandAuthorized,
  },
});

if (decision.shouldSkip) return;
```

## 审批和 channel 能力

大多数 channel 插件不需要审批特定代码。

- 核心持有同聊天 `/approve`、共享审批按钮负载和通用回退交付
- channel 需要审批特定行为时在 channel 插件上使用一个 `approvalCapability` 对象
- `approvalCapability.authorizeActorAction` 和 `approvalCapability.getActionAvailabilityState` 是标准审批认证接缝
- 如果 channel 暴露原生执行审批，使用 `approvalCapability.getExecInitiatingSurfaceState` 获取发起表面/原生客户端状态
- 使用 `approvalCapability.delivery` 仅用于原生审批路由或回退抑制
- 使用 `approvalCapability.nativeRuntime` 用于 channel 持有的原生审批事实
- 使用 `approvalCapability.render` 仅在 channel 确实需要自定义审批负载而非共享渲染器时

`nativeRuntime` 分为几个更小的接缝：

- `availability` — 账户是否已配置以及是否应处理请求
- `presentation` — 将共享审批视图模型映射为待定/已解决/已过期的原生负载或最终操作
- `transport` — 准备目标加发送/更新/删除原生审批消息
- `interactions` — 原生按钮或反应的可选绑定/解绑/清除操作钩子
- `observe` — 可选交付诊断钩子

## 演练

### 包和 manifest

创建标准插件文件。`package.json` 中的 `channel` 字段使其成为 channel 插件：

```json
{
  "name": "@myorg/openclaw-acme-chat",
  "version": "1.0.0",
  "type": "module",
  "openclaw": {
    "extensions": ["./index.ts"],
    "setupEntry": "./setup-entry.ts",
    "channel": {
      "id": "acme-chat",
      "label": "Acme Chat",
      "blurb": "Connect OpenClaw to Acme Chat."
    }
  }
}
```

```json
{
  "id": "acme-chat",
  "kind": "channel",
  "channels": ["acme-chat"],
  "name": "Acme Chat",
  "description": "Acme Chat channel plugin",
  "configSchema": {
    "type": "object",
    "additionalProperties": false,
    "properties": {}
  },
  "channelConfigs": {
    "acme-chat": {
      "schema": {
        "type": "object",
        "additionalProperties": false,
        "properties": {
          "token": { "type": "string" },
          "allowFrom": {
            "type": "array",
            "items": { "type": "string" }
          }
        }
      },
      "uiHints": {
        "token": {
          "label": "Bot token",
          "sensitive": true
        }
      }
    }
  }
}
```

`configSchema` 验证 `plugins.entries.acme-chat.config`，用于非 channel 账户配置的插件级设置。`channelConfigs` 验证 `channels.acme-chat`，是插件运行时加载前配置 schema、设置和 UI 表面使用的冷路径源。

### 构建 channel 插件对象

`ChannelPlugin` 接口有许多可选适配器表面。从最小化开始——`id` 和 `setup`——然后按需添加适配器。

```typescript
import {
  createChatChannelPlugin,
  createChannelPluginBase,
} from "openclaw/plugin-sdk/channel-core";

export const acmeChatPlugin = createChatChannelPlugin({
  base: createChannelPluginBase({
    id: "acme-chat",
    setup: {
      resolveAccount,
      inspectAccount(cfg, accountId) {
        const section = cfg.channels?.["acme-chat"];
        return {
          enabled: Boolean(section?.token),
          configured: Boolean(section?.token),
          tokenStatus: section?.token ? "available" : "missing",
        };
      },
    },
  }),

  security: {
    dm: {
      channelKey: "acme-chat",
      resolvePolicy: (account) => account.dmPolicy,
      // ... DM 安全策略配置
    },
  },

  // ... 出站、配对、线程等适配器
});
```

## 相关

- [Building plugins](/plugins/building-plugins)
- [Channel inbound API](/plugins/sdk-channel-inbound)
- [Channel ingress API](/plugins/sdk-channel-ingress)
- [Channel outbound API](/plugins/sdk-channel-outbound)
