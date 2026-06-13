# 运行时 Helper

## 架构精读

> 跳过不影响阅读翻译正文。

### 为什么不让插件直接 import 核心模块？

插件直接 `import { loadConfig } from "openclaw/core/config"` 写起来最快，但会把插件和核心内部布局绑死。核心重构一次，所有插件都要跟着改。`api.runtime` 是依赖注入——OpenClaw 在加载插件时把运行时能力通过 api 对象传进来，插件只看到稳定的接口。就像 Kubernetes 的 client-go——Pod 里的代码通过 ServiceAccount token 访问 API server，不直接连 etcd。好处是核心可以随意重构内部实现，坏处是多了一层间接调用。

第二个关键设计：配置快照单向流动。`api.config` 在注册时传入，整个调用链传递同一快照。`api.runtime.config.current()` 仅在长时间运行的处理器需要当前进程快照且无配置传入时才用。这避免了热路径上反复解析配置文件——就像 React 的 immutable state，组件拿到的是快照，不是可变引用。写配置必须走 `mutateConfigFile` 并声明 `afterWrite` 策略，让 Gateway 决定是否重启。

第三个边界：运行时命名空间按能力分组。`api.runtime.agent`、`api.runtime.llm`、`api.runtime.tts`、`api.runtime.subagent` 等命名空间各自独立。每个命名空间是一个聚焦的能力表面，就像 Kubernetes API 分组（core/v1、apps/v1）。好处是插件只用到自己需要的命名空间，坏处是初次接触时需要找到正确的命名空间。

---

`api.runtime` 对象在注册期间注入每个插件的参考。使用这些 helper 代替直接导入 host 内部模块。

| 方向           | 内容                                          |
| -------------- | --------------------------------------------- |
| Channel 插件   | 在 channel 插件上下文中使用这些 helper 的步骤指南 |
| Provider 插件  | 在 provider 插件上下文中使用这些 helper 的步骤指南 |

```typescript
register(api) {
  const runtime = api.runtime;
}
```

## 配置加载和写入

优先使用已传入活跃调用路径的配置，如注册期间的 `api.config` 或 channel/provider 回调上的 `cfg` 参数。这保持一个进程快照贯穿工作流，而非在热路径上重新解析配置。

`api.runtime.config.current()` 仅在长时间运行的处理器需要当前进程快照且无配置传入该函数时才用。返回值只读；编辑前需克隆或使用变更 helper。

工具工厂接收 `ctx.runtimeConfig` 加 `ctx.getRuntimeConfig()`。当配置可在工具定义创建后变更时，在长时间运行工具的 `execute` 回调内使用 getter。

用 `api.runtime.config.mutateConfigFile(...)` 或 `api.runtime.config.replaceConfigFile(...)` 持久化变更。每次写入必须选择显式 `afterWrite` 策略：

- `afterWrite: { mode: "auto" }` 让 gateway 重载规划器决定。
- `afterWrite: { mode: "restart", reason: "..." }` 在写入者知道热重载不安全时强制干净重启。
- `afterWrite: { mode: "none", reason: "..." }` 仅在调用者负责后续处理时抑制自动重载/重启。

变更 helper 返回 `afterWrite` 加类型化 `followUp` 摘要，调用者可记录或测试是否请求了重启。Gateway 仍负责重启实际发生的时间。

`api.runtime.config.loadConfig()` 和 `api.runtime.config.writeConfigFile(...)` 是 `runtime-config-load-write` 下的已弃用兼容 helper。它们在运行时警告一次，在迁移窗口内对旧外部插件保持可用。捆绑插件不得使用；如果插件代码调用它们或从插件 SDK 子路径导入这些 helper，配置边界守卫会失败。

直接 SDK 导入时，用聚焦配置子路径代替广泛的兼容 barrel。`config-contracts` 用于类型，`plugin-config-runtime` 用于已加载配置断言和插件入口查找，`runtime-config-snapshot` 用于当前进程快照，`config-mutation` 用于写入。捆绑插件测试应直接 mock 这些聚焦子路径，而不是 mock 广泛兼容 barrel。

内部 OpenClaw 运行时代码遵循相同方向：在 CLI、gateway 或进程边界加载配置一次，然后传递该值。成功的变更写入会刷新进程运行时快照并推进内部修订。长时间运行的缓存应该以运行时持有的缓存键为索引，而不是本地序列化配置。运行时模块对 `loadConfig()` 调用零容忍，必须使用传入的 `cfg`、请求 `context.getRuntimeConfig()` 或显式进程边界的 `getRuntimeConfig()`。

Provider 和 channel 执行路径必须使用活跃运行时配置快照，而非配置回读或编辑返回的文件快照。文件快照保留源值如 SecretRef 标记供 UI 和写入使用；provider 回调需要已解析的运行时视图。当 helper 可能被活跃源快照或活跃运行时快照调用时，在读取凭证前通过 `selectApplicableRuntimeConfig()` 路由。

## 可复用运行时工具

入站 `botLoopProtection` 事实用于 bot 编写的入站消息。核心在会话记录和分发前应用共享内存滑动窗口守卫，不将策略绑定到单个 channel。守卫追踪 `(scopeId, conversationId, participant pair)` 键，双向合计计数对，窗口预算超出后应用冷却，并机会性清理不活跃条目。

向 operator 暴露此行为的 channel 插件应优先用共享 `channels.defaults.botLoopProtection` 结构做基线预算，再在其上叠加 channel/provider 专用覆盖。共享配置使用秒因为面向用户：

```typescript
type ChannelBotLoopProtectionConfig = {
  enabled?: boolean;
  maxEventsPerWindow?: number;
  windowSeconds?: number;
  cooldownSeconds?: number;
};
```

用已解析的 turn 传递归一化 bot-pair 事实。核心解析默认值、单位转换和 `enabled` 语义：

```typescript
return {
  channel: "example",
  routeSessionKey,
  storePath,
  ctxPayload,
  recordInboundSession,
  runDispatch,
  botLoopProtection: {
    scopeId: "account-1",
    conversationId: "channel-1",
    senderId: "bot-a",
    receiverId: "bot-b",
    config: channelConfig.botLoopProtection,
    defaultsConfig: runtimeConfig.channels?.defaults?.botLoopProtection,
    defaultEnabled: allowBotsMode !== "off",
  },
};
```

仅对不经过共享入站回复运行器的自定义双方事件循环直接使用 `openclaw/plugin-sdk/pair-loop-guard-runtime`。

## 运行时命名空间

### api.runtime.agent

Agent 身份、目录和会话管理。

```typescript
// 解析 agent 工作目录
const agentDir = api.runtime.agent.resolveAgentDir(cfg);

// 解析 agent 工作区
const workspaceDir = api.runtime.agent.resolveAgentWorkspaceDir(cfg);

// 获取 agent 身份
const identity = api.runtime.agent.resolveAgentIdentity(cfg);

// 获取默认思考级别
const thinking = api.runtime.agent.resolveThinkingDefault({
  cfg,
  provider,
  model,
});

// 验证用户提供的思考级别对活跃 provider 档案是否有效
const policy = api.runtime.agent.resolveThinkingPolicy({ provider, model });
const level = api.runtime.agent.normalizeThinkingLevel("extra high");
if (level && policy.levels.some((entry) => entry.id === level)) {
  // 将 level 传给嵌入式运行
}

// 获取 agent 超时
const timeoutMs = api.runtime.agent.resolveAgentTimeoutMs(cfg);

// 确保工作区存在
await api.runtime.agent.ensureAgentWorkspace(cfg);

// 运行嵌入式 agent turn
const agentDir = api.runtime.agent.resolveAgentDir(cfg);
const result = await api.runtime.agent.runEmbeddedAgent({
  sessionId: "my-plugin:task-1",
  runId: crypto.randomUUID(),
  sessionFile: path.join(agentDir, "sessions", "my-plugin-task-1.jsonl"),
  workspaceDir: api.runtime.agent.resolveAgentWorkspaceDir(cfg),
  prompt: "总结最新变更",
  timeoutMs: api.runtime.agent.resolveAgentTimeoutMs(cfg),
});
```

`runEmbeddedAgent(...)` 是从插件代码启动正常 OpenClaw agent turn 的中性 helper。它使用与 channel 触发回复相同的 provider/model 解析和 agent-harness 选择。

`runEmbeddedPiAgent(...)` 保留为已有插件的已弃用兼容别名。新代码应用 `runEmbeddedAgent(...)`。

`resolveThinkingPolicy(...)` 返回 provider/model 支持的思考级别和可选默认值。Provider 插件通过思考钩子持有模型专用档案，所以工具插件应调用此运行时 helper 而非导入或复制 provider 列表。

`normalizeThinkingLevel(...)` 将用户文本如 `on`、`x-high` 或 `extra high` 转换为规范存储级别，再对照已解析策略检查。

**会话存储 helper** 在 `api.runtime.agent.session` 下：

```typescript
const entry = api.runtime.agent.session.getSessionEntry({ agentId, sessionKey });
for (const { sessionKey, entry } of api.runtime.agent.session.listSessionEntries({ agentId })) {
  // 遍历会话行，不依赖遗留 sessions.json 结构。
}
await api.runtime.agent.session.patchSessionEntry({
  agentId,
  sessionKey,
  update: (entry) => ({ thinkingLevel: "high" }),
});
```

会话工作流优先用 `getSessionEntry(...)`、`listSessionEntries(...)`、`patchSessionEntry(...)` 或 `upsertSessionEntry(...)`。这些 helper 按 agent/会话身份寻址会话，插件不依赖遗留 `sessions.json` 存储结构。仅元数据补丁不刷新会话活跃度时用 `preserveActivity: true`，回调返回完整条目且已删除字段必须保持删除时才用 `replaceEntry: true`。`loadSessionStore(...)` 保留为有意需要可变全存储克隆的调用者的已弃用兼容逃逸。

### api.runtime.agent.defaults

默认模型和 provider 常量：

```typescript
const model = api.runtime.agent.defaults.model; // 如 "anthropic/claude-sonnet-4-6"
const provider = api.runtime.agent.defaults.provider; // 如 "anthropic"
```

### api.runtime.llm

运行 host 持有的文本补全，无需导入 provider 内部模块或重复 OpenClaw 模型/auth/base URL 准备。

```typescript
const result = await api.runtime.llm.complete({
  messages: [{ role: "user", content: "总结此转录。" }],
  purpose: "my-plugin.summary",
  maxTokens: 512,
  temperature: 0.2,
});
```

该 helper 使用与 OpenClaw 内置运行时相同的简单补全准备路径和 host 持有的运行时配置快照。上下文引擎接收会话绑定的 `llm.complete` 能力，模型调用使用活跃会话的 agent，不默默回退到默认 agent。结果包含 provider/model/agent 归因加上已归一化 token、缓存和可用时的估计成本用量。

> **警告**：模型覆盖需 operator 通过配置 `plugins.entries.<id>.llm.allowModelOverride: true` opt-in。用 `plugins.entries.<id>.llm.allowedModels` 限制受信插件到特定规范 `provider/model` 目标。跨 agent 补全需 `plugins.entries.<id>.llm.allowAgentIdOverride: true`。

### api.runtime.subagent

启动和管理后台子 agent 运行。

```typescript
// 启动子 agent 运行
const { runId } = await api.runtime.subagent.run({
  sessionKey: "agent:main:subagent:search-helper",
  message: "将此查询扩展为聚焦的后续搜索。",
  provider: "openai", // 可选覆盖
  model: "gpt-4.1-mini", // 可选覆盖
  deliver: false,
});

// 等待完成
const result = await api.runtime.subagent.waitForRun({ runId, timeoutMs: 30000 });

// 读取会话消息
const { messages } = await api.runtime.subagent.getSessionMessages({
  sessionKey: "agent:main:subagent:search-helper",
  limit: 10,
});

// 删除会话
await api.runtime.subagent.deleteSession({
  sessionKey: "agent:main:subagent:search-helper",
});
```

> **警告**：模型覆盖（`provider`/`model`）需 operator 通过配置 `plugins.entries.<id>.subagent.allowModelOverride: true` opt-in。不受信插件仍可运行子 agent，但覆盖请求被拒绝。

`deleteSession(...)` 可删除同一插件通过 `api.runtime.subagent.run(...)` 创建的会话。删除任意用户或 operator 会话仍需 admin 权限的 Gateway 请求。

### api.runtime.nodes

列出连接的 node 并从 Gateway 加载的插件代码或插件 CLI 命令调用 node-host 命令。当插件持有配对设备上的本地工作（如另一台 Mac 上的浏览器或音频桥）时使用。

```typescript
const { nodes } = await api.runtime.nodes.list({ connected: true });

const result = await api.runtime.nodes.invoke({
  nodeId: "mac-studio",
  command: "my-plugin.command",
  params: { action: "start" },
  timeoutMs: 30000,
});
```

Gateway 内此运行时是进程内的。插件 CLI 命令中它通过 RPC 调用配置的 Gateway，所以 `openclaw googlemeet recover-tab` 等命令可从终端检查配对 node。Node 命令仍经过正常 Gateway node 配对、命令允许列表、插件 node-invoke 策略和 node 本地命令处理。

暴露危险 node-host 命令的插件应用 `api.registerNodeInvokePolicy(...)` 注册 node-invoke 策略。策略在命令允许列表检查后、命令转发到 node 前在 Gateway 中运行，所以直接 `node.invoke` 调用和更高级插件工具共享同一执行路径。

### api.runtime.tasks.managedFlows

将 Task Flow 运行时绑定到已有 OpenClaw 会话键或受信工具上下文，然后创建和管理 Task Flow，无需每次调用传递 owner。

Task Flow 追踪持久多步工作流状态。它不是调度器：未来唤醒用 Cron 或 `api.session.workflow.scheduleSessionTurn(...)`，然后在调度 turn 中该工作需要 flow 状态、子任务、等待或取消时使用 `managedFlows`。

```typescript
const taskFlow = api.runtime.tasks.managedFlows.fromToolContext(ctx);

const created = taskFlow.createManaged({
  controllerId: "my-plugin/review-batch",
  goal: "审查新 pull request",
});

const child = taskFlow.runTask({
  flowId: created.flowId,
  runtime: "acp",
  childSessionKey: "agent:main:subagent:reviewer",
  task: "审查 PR #123",
  status: "running",
  startedAt: Date.now(),
});

const waiting = taskFlow.setWaiting({
  flowId: created.flowId,
  expectedRevision: created.revision,
  currentStep: "await-human-reply",
  waitJson: { kind: "reply", channel: "telegram" },
});
```

已有来自自己绑定层的受信 OpenClaw 会话键时用 `bindSession({ sessionKey, requesterOrigin })`。不要从原始用户输入绑定。

### api.runtime.tts

文本转语音合成。

```typescript
// 标准 TTS
const clip = await api.runtime.tts.textToSpeech({
  text: "Hello from OpenClaw",
  cfg: api.config,
});

// 电话优化 TTS
const telephonyClip = await api.runtime.tts.textToSpeechTelephony({
  text: "Hello from OpenClaw",
  cfg: api.config,
});

// 列出可用语音
const voices = await api.runtime.tts.listVoices({
  provider: "elevenlabs",
  cfg: api.config,
});
```

使用核心 `messages.tts` 配置和 provider 选择。返回 PCM 音频缓冲区 + 采样率。

### api.runtime.mediaUnderstanding

图片、音频和视频分析。

```typescript
// 描述图片
const image = await api.runtime.mediaUnderstanding.describeImageFile({
  filePath: "/tmp/inbound-photo.jpg",
  cfg: api.config,
  agentDir: "/tmp/agent",
});

// 转录音频
const { text } = await api.runtime.mediaUnderstanding.transcribeAudioFile({
  filePath: "/tmp/inbound-audio.ogg",
  cfg: api.config,
  mime: "audio/ogg", // 可选，MIME 无法推断时
});

// 描述视频
const video = await api.runtime.mediaUnderstanding.describeVideoFile({
  filePath: "/tmp/inbound-video.mp4",
  cfg: api.config,
});

// 通用文件分析
const result = await api.runtime.mediaUnderstanding.runFile({
  filePath: "/tmp/inbound-file.pdf",
  cfg: api.config,
});
```

无输出产生时返回 `{ text: undefined }`（如跳过的输入）。

> **信息**：`api.runtime.stt.transcribeAudioFile(...)` 保留为 `api.runtime.mediaUnderstanding.transcribeAudioFile(...)` 的兼容别名。

### api.runtime.imageGeneration

图片生成。

```typescript
const result = await api.runtime.imageGeneration.generate({
  prompt: "A robot painting a sunset",
  cfg: api.config,
});

const providers = api.runtime.imageGeneration.listProviders({ cfg: api.config });
```

### api.runtime.webSearch

网页搜索。

```typescript
const providers = api.runtime.webSearch.listProviders({ config: api.config });

const result = await api.runtime.webSearch.search({
  config: api.config,
  args: { query: "OpenClaw plugin SDK", count: 5 },
});
```

### api.runtime.media

底层媒体工具。

```typescript
const webMedia = await api.runtime.media.loadWebMedia(url);
const mime = await api.runtime.media.detectMime(buffer);
const kind = api.runtime.media.mediaKindFromMime("image/jpeg"); // "image"
const isVoice = api.runtime.media.isVoiceCompatibleAudio(filePath);
const metadata = await api.runtime.media.getImageMetadata(filePath);
const resized = await api.runtime.media.resizeToJpeg(buffer, { maxWidth: 800 });
const terminalQr = await api.runtime.media.renderQrTerminal("https://openclaw.ai");
```

### api.runtime.config

当前运行时配置快照和事务配置写入。优先使用已传入活跃调用路径的配置；仅在处理器需要进程快照时直接使用 `current()`。

```typescript
const cfg = api.runtime.config.current();
await api.runtime.config.mutateConfigFile({
  afterWrite: { mode: "auto" },
  mutate(draft) {
    draft.plugins ??= {};
  },
});
```

`mutateConfigFile(...)` 和 `replaceConfigFile(...)` 返回 `followUp` 值，如 `{ mode: "restart", requiresRestart: true, reason }`，记录写入者意图而不剥夺 gateway 的重启控制权。

### api.runtime.system

系统级工具。

```typescript
await api.runtime.system.enqueueSystemEvent(event);
api.runtime.system.requestHeartbeat({
  source: "other",
  intent: "event",
  reason: "plugin-event",
});
const output = await api.runtime.system.runCommandWithTimeout(cmd, args, opts);
```

### api.runtime.events

事件订阅。

```typescript
api.runtime.events.onAgentEvent((event) => {
  /* ... */
});
api.runtime.events.onSessionTranscriptUpdate((update) => {
  /* ... */
});
```

### api.runtime.logging

日志。

```typescript
const verbose = api.runtime.logging.shouldLogVerbose();
const childLogger = api.runtime.logging.getChildLogger({ plugin: "my-plugin" }, { level: "debug" });
```

### api.runtime.modelAuth

模型和 provider auth 解析。

```typescript
const auth = await api.runtime.modelAuth.getApiKeyForModel({ model, cfg });
const providerAuth = await api.runtime.modelAuth.resolveApiKeyForProvider({
  provider: "openai",
  cfg,
});
```

### api.runtime.state

状态目录解析和 SQLite 支持的键值存储。

```typescript
const stateDir = api.runtime.state.resolveStateDir(process.env);
const store = api.runtime.state.openKeyedStore({
  namespace: "my-feature",
  maxEntries: 200,
  defaultTtlMs: 15 * 60_000,
});

await store.register("key-1", { value: "hello" });
const claimed = await store.registerIfAbsent("dedupe-key", { value: "first" });
const value = await store.lookup("key-1");
await store.consume("key-1");
await store.clear();
```

键值存储跨重启存活并按运行时绑定插件 id 隔离。原子去重认领用 `registerIfAbsent(...)`：键缺失或过期并注册时返回 `true`，活跃值已存在时返回 `false` 且不覆盖其值、创建时间或 TTL。限制：每命名空间 `maxEntries`，每插件 6,000 活跃行，JSON 值 64KB 以下，可选 TTL 过期。当写入将超出插件行上限时，运行时可能从正在写入的命名空间驱逐最旧的活跃行。兄弟命名空间不被该写入驱逐。如果命名空间无法释放足够行，写入仍失败。

> **警告**：当前版本仅捆绑插件。

### api.runtime.tools

记忆工具工厂和 CLI。

```typescript
const getTool = api.runtime.tools.createMemoryGetTool(/* ... */);
const searchTool = api.runtime.tools.createMemorySearchTool(/* ... */);
api.runtime.tools.registerMemoryCli(/* ... */);
```

### api.runtime.channel

Channel 专用运行时 helper（channel 插件加载时可用）。

`api.runtime.channel.media` 是 channel 媒体下载和存储的首选表面：

```typescript
const saved = await api.runtime.channel.media.saveRemoteMedia({
  url,
  subdir: "inbound",
  maxBytes,
  filePathHint: fileName,
});
```

远程 URL 需成为 OpenClaw 媒体时用 `saveRemoteMedia(...)`。插件已用插件持有的 auth、重定向或允许列表处理获取了 `Response` 时用 `saveResponseMedia(...)`。仅在插件需要原始字节做检查、转换、解密或重传时用 `readRemoteMediaBuffer(...)`。`fetchRemoteMedia(...)` 保留为 `readRemoteMediaBuffer(...)` 的已弃用兼容别名。

`api.runtime.channel.mentions` 是使用运行时注入的捆绑 channel 插件的共享入站提及策略表面：

```typescript
const mentionMatch = api.runtime.channel.mentions.matchesMentionWithExplicit(text, {
  mentionRegexes,
  mentionPatterns,
});

const decision = api.runtime.channel.mentions.resolveInboundMentionDecision({
  facts: {
    canDetectMention: true,
    wasMentioned: mentionMatch.matched,
    implicitMentionKinds: api.runtime.channel.mentions.implicitMentionKindWhen(
      "reply_to_bot",
      isReplyToBot,
    ),
  },
  policy: {
    isGroup,
    requireMention,
    allowTextCommands,
    hasControlCommand,
    commandAuthorized,
  },
});
```

可用提及 helper：

- `buildMentionRegexes`
- `matchesMentionPatterns`
- `matchesMentionWithExplicit`
- `implicitMentionKindWhen`
- `resolveInboundMentionDecision`

`api.runtime.channel.mentions` 有意不暴露旧的 `resolveMentionGating*` 兼容 helper。优先用归一化 `{ facts, policy }` 路径。

## 存储运行时引用

用 `createPluginRuntimeStore` 存储运行时引用供 `register` 回调外使用：

**步骤**

1. **创建存储**

   ```typescript
   import { createPluginRuntimeStore } from "openclaw/plugin-sdk/runtime-store";
   import type { PluginRuntime } from "openclaw/plugin-sdk/runtime-store";

   const store = createPluginRuntimeStore({
     pluginId: "my-plugin",
     errorMessage: "my-plugin runtime not initialized",
   });
   ```

2. **接入入口点**

   ```typescript
   export default defineChannelPluginEntry({
     id: "my-plugin",
     name: "My Plugin",
     description: "Example",
     plugin: myPlugin,
     setRuntime: store.setRuntime,
   });
   ```

3. **从其他文件访问**

   ```typescript
   export function getRuntime() {
     return store.getRuntime(); // 未初始化时抛异常
   }

   export function tryGetRuntime() {
     return store.tryGetRuntime(); // 未初始化时返回 null
   }
   ```

> **注意**：运行时存储身份优先用 `pluginId`。底层 `key` 形态用于一个插件有意需要多个运行时槽的不常见场景。

## 其他顶层 `api` 字段

除 `api.runtime` 外，API 对象还提供：

- `api.id`：插件 id。
- `api.name`：插件展示名。
- `api.config`：当前配置快照（可用时为活跃内存运行时快照）。
- `api.pluginConfig`：`plugins.entries.<id>.config` 的插件专用配置。
- `api.logger`：有范围 logger（`debug`、`info`、`warn`、`error`）。
- `api.registrationMode`：当前加载模式；`"setup-runtime"` 是轻量级预完整条目启动/设置窗口。
- `api.resolvePath(input)`：相对于插件根解析路径。

## 相关

- [Plugin internals](/plugins/architecture) — 能力模型和注册表
- [SDK entry points](/plugins/sdk-entrypoints) — `definePluginEntry` 选项
- [SDK overview](/plugins/sdk-overview) — 子路径参考
