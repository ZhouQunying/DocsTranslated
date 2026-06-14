# Channel Ingress API

## 架构精读

> 跳过不影响阅读翻译正文。

### 为什么需要单独的 ingress 层而不是在 inbound 里做访问控制？

Kubernetes 的 Ingress 资源是流量到达 Service 之前的门——路由、TLS 终止、速率限制都在那里做。Channel ingress 是同样思路：平台事件到达 agent 之前先过访问控制层。DM/群组允许列表、配对存储、路由门控、命令门控、事件认证、提及激活、脱敏诊断和准入——这些策略都不应混在事件处理逻辑里。好处是策略变更不影响事件处理代码，坏处是多了一层要理解。关键区分：插件持有平台事实和副作用，核心持有通用策略。

---

Channel ingress 是 inbound channel 事件的实验性访问控制边界。使用 `openclaw/plugin-sdk/channel-ingress-runtime` 做接收路径。旧的 `openclaw/plugin-sdk/channel-ingress` 子路径保持导出为第三方插件的已弃用兼容外观。

插件持有平台事实和副作用。核心持有通用策略：DM/群组允许列表、配对存储 DM 条目、路由门控、命令门控、事件认证、提及激活、脱敏诊断和准入。

## 运行时解析器

```ts

  defineStableChannelIngressIdentity,
  resolveChannelMessageIngress,
} from "openclaw/plugin-sdk/channel-ingress-runtime";

const identity = defineStableChannelIngressIdentity({
  key: "platform-user-id",
  normalize: normalizePlatformUserId,
  sensitivity: "pii",
});

const result = await resolveChannelMessageIngress({
  channelId: "my-channel",
  accountId,
  identity,
  subject: { stableId: platformUserId },
  conversation: { kind: isGroup ? "group" : "direct", id: conversationId },
  event: { kind: "message", authMode: "inbound", mayPair: !isGroup },
  policy: {
    dmPolicy: config.dmPolicy,
    groupPolicy: config.groupPolicy,
    groupAllowFromFallbackToAllowFrom: true,
  },
  allowFrom: config.allowFrom,
  groupAllowFrom: config.groupAllowFrom,
  accessGroups: cfg.accessGroups,
  route,
  readStoreAllowFrom,
  command: hasControlCommand ? { allowTextCommands: true, hasControlCommand } : undefined,
});
```

不要预计算有效允许列表、命令持有者或命令组。解析器从原始允许列表、存储回调、路由描述符、访问组、策略和对话类型派生它们。

## 结果

捆绑插件应直接消费现代投影：

- `ingress`：有序门控决策和准入
- `senderAccess`：仅发送者/对话授权
- `routeAccess`：路由和路由发送者投影
- `commandAccess`：命令授权；未运行命令门控时为 false
- `activationAccess`：提及/激活结果

事件认证仍可在有序 `ingress.graph` 和决定性 `ingress.reasonCode` 上获得；不发出单独的事件投影。

已弃用的第三方 SDK 辅助可能在内部重建旧形态。新捆绑接收路径不应将现代结果转换回本地 DTO。

## 访问组

`accessGroup:<name>` 条目保持脱敏。核心自己解析静态 `message.senders` 组，仅对需要平台查找的动态组调用 `resolveAccessGroupMembership`。缺失、不支持和失败的组做默认拒绝。

## 事件模式

| `authMode` | 含义 |
| --- | --- |
| `inbound` | 普通 inbound 发送者门控 |
| `command` | 回调或作用域按钮的命令门控 |
| `origin-subject` | 行动者必须匹配原始消息主体 |
| `route-only` | 仅路由门控，用于路由作用域可信事件 |
| `none` | 插件持有的内部事件绕过共享认证 |

对反应、按钮、回调和原生命令使用 `mayPair: false`。

## 路由和激活

使用路由描述符做房间、主题、公会、线程或嵌套路由策略：

```ts
route: {
  id: "room",
  allowed: roomAllowed,
  enabled: roomEnabled,
  senderPolicy: "replace",
  senderAllowFrom: roomAllowFrom,
  blockReason: "room_sender_not_allowlisted",
}
```

当插件有多个可选路由描述符时使用 `channelIngressRoutes(...)`；它过滤禁用的分支，同时保持路由事实通用并按每个描述符的 `precedence` 排序。

提及门控是激活门。提及未命中返回 `admission: "skip"`，回合内核不处理仅观察回合。大多数 channel 应在发送者和命令门控之后保留激活。在文本命令绕过禁用时，必须在发送者允许列表噪音之前静默非提及流量的公共聊天表面可选择 `activation.order: "before-sender"`。持有隐式激活的 channel（如 bot 线程中的回复）可传递 `activation.allowedImplicitMentionKinds`；投影的 `activationAccess.shouldBypassMention` 随后报告命令或隐式激活何时绕过了显式提及。

## 脱敏

原始发送者值和原始允许列表条目仅是解析器输入。它们不得出现在已解析状态、决策、诊断、快照或兼容事实中。使用不透明主体 id、条目 id、路由 id 和诊断 id。

## 验证

```bash
pnpm test src/channels/message-access/message-access.test.ts src/plugin-sdk/channel-ingress-runtime.test.ts
pnpm plugin-sdk:api:check
```
