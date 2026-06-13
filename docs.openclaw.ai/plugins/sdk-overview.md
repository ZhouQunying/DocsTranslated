# Plugin SDK 概述

## 架构精读

> 跳过不影响阅读翻译正文。

### 为什么 SDK 拆成几十个子路径而不是一个 barrel 文件？

一个 `openclaw/plugin-sdk` 导出所有东西写起来方便，但每个 import 都会拉进整棵依赖树。Gateway 启动时要加载几十个插件，每个插件都拉完整 barrel 的话，启动时间从秒级变成十秒级。拆成 `openclaw/plugin-sdk/plugin-entry`、`openclaw/plugin-sdk/channel-core` 等窄子路径后，每个插件只拉自己需要的模块。就像 ES module 的 tree-shaking——编译器帮你去掉没用到的代码，但前提是你没有把所有东西塞进一个文件。

第二个关键设计：`register(api)` 是依赖注入，不是全局注册。插件入口导出 `definePluginEntry({ register(api) { ... } })`，OpenClaw 在加载插件时调用该注册函数并传入 api 对象。插件通过 api 对象注册工具、provider、钩子等。这就像 Java 的 `Module.configure(binder)` 或 React 的 `useContext`——能力通过参数传入，不依赖全局变量。好处是测试时可以注入 mock api，坏处是多了一层间接。

第三个边界：独占槽位。上下文引擎和记忆能力同时只能有一个活跃。`api.registerContextEngine(id, factory)` 注册上下文引擎时，新注册的替换旧的。这是有意设计——上下文组装和记忆召回是有状态的全局行为，多个实现同时活跃会产生冲突。就像浏览器的 Service Worker——同一作用域只能有一个活跃。

---

插件 SDK 是插件与核心之间的类型化契约。本页是**导入什么**和**可以注册什么**的参考。

> **注意**：本页面向插件作者，即在 OpenClaw 内部使用插件 SDK 子路径导入的人群。外部应用、脚本、仪表盘、CI 作业和 IDE 扩展如需通过 Gateway 运行 agent，改用 [OpenClaw App SDK](/concepts/openclaw-sdk) 和对应的 SDK 包。

**提示**：在找操作指南？从 [Building plugins](/plugins/building-plugins) 开始，channel 插件用 [Channel plugins](/plugins/sdk-channel-plugins)，provider 插件用 [Provider plugins](/plugins/sdk-provider-plugins)，本地 AI CLI 后端用 [CLI backend plugins](/plugins/cli-backend-plugins)，工具或生命周期钩子插件用 [Plugin hooks](/plugins/hooks)。

## 导入约定

始终从特定子路径导入：

```typescript

```

每个子路径是一个小的、自包含的模块。这保持启动快速并防止循环依赖问题。Channel 专用入口/构建 helper 优先用 `openclaw/plugin-sdk/channel-core`；`openclaw/plugin-sdk/core` 保留给更广的伞状表面和 `buildChannelConfigSchema` 等共享 helper。

Channel 配置通过 `openclaw.plugin.json#channelConfigs` 发布 channel 持有的 JSON Schema。`plugin-sdk/channel-config-schema` 子路径用于共享 schema 原语和通用构建器。OpenClaw 捆绑插件用 `plugin-sdk/bundled-channel-config-schema` 保留捆绑 channel schema。已弃用兼容导出保留在 `plugin-sdk/channel-config-schema-legacy`；两个捆绑 schema 子路径都不是新插件的模式。

> **警告**：不要导入 provider 或 channel 品牌的便利接缝（如 `openclaw/plugin-sdk/slack`、`.../discord`、`.../signal`、`.../whatsapp`）。捆绑插件在自己的 `api.ts` / `runtime-api.ts` barrel 内组合通用 SDK 子路径；核心消费者应用这些插件本地 barrel 或在需求确实跨 channel 时添加窄通用 SDK 契约。

少量捆绑插件 helper 接缝在有追踪 owner 使用时仍出现在生成的导出映射中。它们仅供捆绑插件维护，不是新第三方插件的推荐导入路径。

`openclaw/plugin-sdk/discord` 和 `openclaw/plugin-sdk/telegram-account` 也保留为有追踪 owner 使用的已弃用兼容门面。不要将这些导入路径复制到新插件中；改用注入的运行时 helper 和通用 channel SDK 子路径。

## 子路径参考

插件 SDK 以按领域分组的窄子路径集合暴露（插件入口、channel、provider、auth、runtime、capability、memory 和保留的捆绑插件 helper）。完整目录（分组并链接）见 [Plugin SDK subpaths](/plugins/sdk-subpaths)。

编译器入口点清单在 `scripts/lib/plugin-sdk-entrypoints.json`；包导出从公开子集中生成，减去 `scripts/lib/plugin-sdk-private-local-only-subpaths.json` 中列出的仓库本地测试/内部子路径。运行 `pnpm plugin-sdk:surface` 审计公开导出数量。足够旧且捆绑扩展生产代码未使用的已弃用公开子路径追踪在 `scripts/lib/plugin-sdk-deprecated-public-subpaths.json`；广泛的已弃用重导出 barrel 追踪在 `scripts/lib/plugin-sdk-deprecated-barrel-subpaths.json`。

## 注册 API

`register(api)` 回调接收一个 `OpenClawPluginApi` 对象，具有以下方法：

### 能力注册

| 方法                                             | 注册内容                          |
| ------------------------------------------------ | --------------------------------- |
| `api.registerProvider(...)`                      | 文本推理（LLM）                   |
| `api.registerAgentHarness(...)`                  | 实验性底层 agent 执行器           |
| `api.registerCliBackend(...)`                    | 本地 CLI 推理后端                 |
| `api.registerChannel(...)`                       | 消息 channel                      |
| `api.registerEmbeddingProvider(...)`              | 可复用向量嵌入 provider           |
| `api.registerSpeechProvider(...)`                | 文本转语音 / STT 合成             |
| `api.registerRealtimeTranscriptionProvider(...)` | 流式实时转录                      |
| `api.registerRealtimeVoiceProvider(...)`         | 双工实时语音会话                  |
| `api.registerMediaUnderstandingProvider(...)`    | 图片/音频/视频分析                |
| `api.registerImageGenerationProvider(...)`       | 图片生成                          |
| `api.registerMusicGenerationProvider(...)`       | 音乐生成                          |
| `api.registerVideoGenerationProvider(...)`       | 视频生成                          |
| `api.registerWebFetchProvider(...)`              | 网页抓取 provider                 |
| `api.registerWebSearchProvider(...)`             | 网页搜索                          |

用 `api.registerEmbeddingProvider(...)` 注册的嵌入 provider 也必须在插件清单的 `contracts.embeddingProviders` 中列出。这是可复用向量生成的通用嵌入表面。记忆搜索可消费该通用 provider 表面。旧的 `api.registerMemoryEmbeddingProvider(...)` 和 `contracts.memoryEmbeddingProviders` 接缝是已弃用兼容，等已有记忆专用 provider 迁移。

### 工具和命令

简单纯工具插件用 [`defineToolPlugin`](/plugins/tool-plugins) 和固定工具名。混合插件或完全动态工具注册直接用 `api.registerTool(...)`。

| 方法                          | 注册内容                                   |
| ----------------------------- | ------------------------------------------ |
| `api.registerTool(tool, opts?)` | Agent 工具（必选或 `{ optional: true }`）  |
| `api.registerCommand(def)`    | 自定义命令（绕过 LLM）                     |

插件命令可在 agent 需要简短命令持有路由提示时设置 `agentPromptGuidance`。保持该文本关于命令本身；不要向核心 prompt 构建器添加 provider 或插件专用策略。

Guidance 条目可以是遗留字符串（应用到所有 prompt 表面）或结构化条目：

```ts
agentPromptGuidance: [
  "全局命令提示。",
  { text: "仅在主 OpenClaw prompt 中显示。", surfaces: ["openclaw_main"] },
];
```

结构化 `surfaces` 可包含 `openclaw_main`、`codex_app_server`、`cli_backend`、`acp_backend` 或 `subagent`。`pi_main` 保留为 `openclaw_main` 的已弃用别名。有意全表面引导时省略 `surfaces`。不要传空 `surfaces` 数组；它被拒绝，这样意外范围丢失不会变成全局 prompt 文本。

原生 Codex app-server 开发者指令比其他 prompt 表面更严格：只有显式限定到 `codex_app_server` 的引导才提升到该更高优先级通道。遗留字符串引导和未限定结构化引导为兼容保留在非 Codex prompt 表面。

### 基础设施

| 方法                                         | 注册内容                         |
| -------------------------------------------- | -------------------------------- |
| `api.registerHook(events, handler, opts?)`   | 事件钩子                         |
| `api.registerHttpRoute(params)`              | Gateway HTTP 端点                |
| `api.registerGatewayMethod(name, handler)`    | Gateway RPC 方法                 |
| `api.registerGatewayDiscoveryService(service)` | 本地 Gateway 发现广播器        |
| `api.registerCli(registrar, opts?)`          | CLI 子命令                       |
| `api.registerNodeCliFeature(registrar, opts?)` | `openclaw nodes` 下的 Node 功能 CLI |
| `api.registerService(service)`               | 后台服务                         |
| `api.registerInteractiveHandler(registration)` | 交互处理器                     |
| `api.registerAgentToolResultMiddleware(...)`  | 运行时工具结果中间件             |
| `api.registerMemoryPromptSupplement(builder)` | 加性记忆相邻 prompt 段           |
| `api.registerMemoryCorpusSupplement(adapter)` | 加性记忆搜索/读取语料            |

### 工作流插件的 Host 钩子

Host 钩子是 SDK 接缝，供需要参与 host 生命周期而非仅添加 provider、channel 或工具的插件使用。它们是通用契约；Plan Mode 可用，但审批工作流、工作区策略门控、后台监控、设置向导和 UI 伴侣插件也可用。

| 方法                                                                               | 持有的契约                                                      |
| ---------------------------------------------------------------------------------- | --------------------------------------------------------------- |
| `api.session.state.registerSessionExtension(...)`                                  | 插件持有的 JSON 兼容会话状态，通过 Gateway 会话投影             |
| `api.session.workflow.enqueueNextTurnInjection(...)`                               | 持久恰好一次上下文注入到一会话的下一 agent turn                 |
| `api.registerTrustedToolPolicy(...)`                                               | 捆绑/受信预插件工具策略，可阻断或重写工具参数                   |
| `api.registerToolMetadata(...)`                                                    | 工具目录展示元数据，不改变工具实现                              |
| `api.registerCommand(...)`                                                         | 有范围插件命令；命令结果可设 `continueAgent: true`              |
| `api.session.controls.registerControlUiDescriptor(...)`                            | Control UI 贡献描述符，用于会话、工具、运行或设置表面           |
| `api.lifecycle.registerRuntimeLifecycle(...)`                                      | 插件持有运行时资源在 reset/delete/reload 路径的清理回调         |
| `api.agent.events.registerAgentEventSubscription(...)`                             | 已清理事件订阅，用于工作流状态和监控                            |
| `api.runContext.setRunContext(...)` / `getRunContext(...)` / `clearRunContext(...)` | 每运行插件草稿状态，在终端运行生命周期清除                      |
| `api.session.workflow.registerSessionSchedulerJob(...)`                            | 插件持有调度作业的清理元数据；不调度工作或创建任务记录          |
| `api.session.workflow.sendSessionAttachment(...)`                                  | 仅捆绑：host 介导的文件附件投递到活跃直接出站会话路由           |
| `api.session.workflow.scheduleSessionTurn(...)` / `unscheduleSessionTurnsByTag(...)` | 仅捆绑：Cron 支持的调度会话 turn 加基于标签的清理             |
| `api.session.controls.registerSessionAction(...)`                                  | 类型化会话动作，客户端可通过 Gateway 分发                       |

新插件代码使用分组命名空间：

- `api.session.state.registerSessionExtension(...)`
- `api.session.workflow.enqueueNextTurnInjection(...)`
- `api.session.workflow.registerSessionSchedulerJob(...)`
- `api.session.workflow.sendSessionAttachment(...)`
- `api.session.workflow.scheduleSessionTurn(...)`
- `api.session.workflow.unscheduleSessionTurnsByTag(...)`
- `api.session.controls.registerSessionAction(...)`
- `api.session.controls.registerControlUiDescriptor(...)`
- `api.agent.events.registerAgentEventSubscription(...)`
- `api.agent.events.emitAgentEvent(...)`
- `api.runContext.setRunContext(...)` / `getRunContext(...)` / `clearRunContext(...)`
- `api.lifecycle.registerRuntimeLifecycle(...)`

等价的扁平方法保留为已有插件的已弃用兼容别名。不要添加调用 `api.registerSessionExtension`、`api.enqueueNextTurnInjection`、`api.registerControlUiDescriptor`、`api.registerRuntimeLifecycle`、`api.registerAgentEventSubscription`、`api.emitAgentEvent`、`api.setRunContext`、`api.getRunContext`、`api.clearRunContext`、`api.registerSessionSchedulerJob`、`api.registerSessionAction`、`api.sendSessionAttachment`、`api.scheduleSessionTurn` 或 `api.unscheduleSessionTurnsByTag` 的新插件代码。

`scheduleSessionTurn(...)` 是 Gateway Cron 调度器的会话范围便利。Cron 负责计时并在 turn 运行时创建后台任务记录；Plugin SDK 仅约束目标会话、插件持有命名和清理。当工作本身需要持久多步 Task Flow 状态时，在调度 turn 内使用 `api.runtime.tasks.managedFlows`。

契约有意拆分权限：

- 外部插件可持有会话扩展、UI 描述符、命令、工具元数据、下一 turn 注入和普通钩子。
- 受信工具策略在普通 `before_tool_call` 钩子前运行，仅限捆绑，因为它们参与 host 安全策略。
- 保留命令所有权仅限捆绑。外部插件应用自己的命令名或别名。
- `allowPromptInjection=false` 禁用 prompt 变更钩子，包括 `agent_turn_prepare`、`before_prompt_build`、`heartbeat_prompt_contribution`、遗留 `before_agent_start` 的 prompt 字段和 `enqueueNextTurnInjection`。

非 Plan 消费者示例：

| 插件原型             | 使用的钩子                                                                   |
| -------------------- | ---------------------------------------------------------------------------- |
| 审批工作流           | 会话扩展、命令延续、下一 turn 注入、UI 描述符                                |
| 预算/工作区策略门控  | 受信工具策略、工具元数据、会话投影                                           |
| 后台生命周期监控     | 运行时生命周期清理、agent 事件订阅、会话调度器所有权/清理、心跳 prompt 贡献、UI 描述符 |
| 设置或入门向导       | 会话扩展、有范围命令、Control UI 描述符                                      |

> **注意**：保留的核心 admin 命名空间（`config.*`、`exec.approvals.*`、`wizard.*`、`update.*`）始终保持 `operator.admin`，即使插件试图分配更窄的 gateway 方法 scope。插件持有方法优先用插件专用前缀。

何时使用工具结果中间件

捆绑插件可在需要在执行后、运行时将结果反馈给模型前重写工具结果时使用 `api.registerAgentToolResultMiddleware(...)`。这是 tokenjuice 等异步输出缩减器的受信运行时中性接缝。

捆绑插件必须为每个目标运行时声明 `contracts.agentToolResultMiddleware`，例如 `["openclaw", "codex"]`。外部插件不能注册此中间件；不需要预模型工具结果计时的工作保持用普通 OpenClaw 插件钩子。旧的嵌入式 runner 专用扩展工厂注册路径已移除。

### Gateway 发现注册

`api.registerGatewayDiscoveryService(...)` 让插件在本地发现传输（如 mDNS/Bonjour）上广播活跃 Gateway。OpenClaw 在本地发现启用时在 Gateway 启动期间调用该服务，传递当前 Gateway 端口和非秘密 TXT 提示数据，并在 Gateway 关闭时调用返回的 `stop` 处理器。

```typescript
api.registerGatewayDiscoveryService({
  id: "my-discovery",
  async advertise(ctx) {
    const handle = await startMyAdvertiser({
      gatewayPort: ctx.gatewayPort,
      tls: ctx.gatewayTlsEnabled,
      displayName: ctx.machineDisplayName,
    });
    return { stop: () => handle.stop() };
  },
});
```

Gateway 发现插件不能将广播的 TXT 值视为秘密或认证。发现是路由提示；Gateway auth 和 TLS 固定仍负责信任。

### CLI 注册元数据

`api.registerCli(registrar, opts?)` 接受两种命令元数据：

- `commands`：注册器持有的显式命令名
- `descriptors`：解析时命令描述符，用于 CLI help、路由和懒加载插件 CLI 注册
- `parentPath`：嵌套命令组的可选父命令路径，如 `["nodes"]`

配对 node 功能优先用 `api.registerNodeCliFeature(registrar, opts?)`。它是 `api.registerCli(..., { parentPath: ["nodes"] })` 的小包装，让 `openclaw nodes canvas` 等命令成为显式插件持有的 node 功能。

想让插件命令在正常根 CLI 路径保持懒加载时，提供覆盖该注册器暴露的每个顶级命令根的 `descriptors`。

```typescript
api.registerCli(
  async ({ program }) => {
    const { registerMatrixCli } = await import("./src/cli.js");
    registerMatrixCli({ program });
  },
  {
    descriptors: [
      {
        name: "matrix",
        description: "管理 Matrix 账号、验证、设备和 profile 状态",
        hasSubcommands: true,
      },
    ],
  },
);
```

嵌套命令接收已解析的父命令为 `program`：

```typescript
api.registerCli(
  async ({ program }) => {
    const { registerNodesCanvasCommands } = await import("./src/cli.js");
    registerNodesCanvasCommands(program);
  },
  {
    parentPath: ["nodes"],
    descriptors: [
      {
        name: "canvas",
        description: "从配对 node 捕获或渲染 canvas 内容",
        hasSubcommands: true,
      },
    ],
  },
);
```

仅当不需要懒加载根 CLI 注册时单独使用 `commands`。该急切兼容路径仍支持，但不安装解析时懒加载的描述符支持占位符。

### CLI 后端注册

`api.registerCliBackend(...)` 让插件持有本地 AI CLI 后端（如 `claude-cli` 或 `my-cli`）的默认配置。

- 后端 `id` 成为 `my-cli/gpt-5` 等模型引用中的 provider 前缀。
- 后端 `config` 使用与 `agents.defaults.cliBackends.<id>` 相同的结构。
- 用户配置仍优先。OpenClaw 在运行 CLI 前将 `agents.defaults.cliBackends.<id>` 合并到插件默认之上。
- 后端需要合并后兼容重写时用 `normalizeConfig`（如规范化旧 flag 形态）。
- 请求范围 argv 重写属于 CLI 方言时用 `resolveExecutionArgs`，如将 OpenClaw 思考级别映射到原生 effort flag。

端到端编写指南见 [CLI backend plugins](/plugins/cli-backend-plugins)。

### 独占槽位

| 方法                                     | 注册内容                                                                                       |
| ---------------------------------------- | ---------------------------------------------------------------------------------------------- |
| `api.registerContextEngine(id, factory)` | 上下文引擎（同时一个活跃）。`assemble()` 回调接收 `availableTools` 和 `citationsMode`          |
| `api.registerMemoryCapability(capability)` | 统一记忆能力                                                                                 |
| `api.registerMemoryPromptSection(builder)` | 记忆 prompt 段构建器                                                                         |
| `api.registerMemoryFlushPlan(resolver)`  | 记忆 flush 计划解析器                                                                          |
| `api.registerMemoryRuntime(runtime)`     | 记忆运行时适配器                                                                               |

### 已弃用记忆嵌入适配器

| 方法                                         | 注册内容                           |
| -------------------------------------------- | ---------------------------------- |
| `api.registerMemoryEmbeddingProvider(adapter)` | 活跃插件的记忆嵌入适配器         |

- `registerMemoryCapability` 是首选的独占记忆插件 API。
- `registerMemoryCapability` 还可暴露 `publicArtifacts.listArtifacts(...)`，让伴侣插件通过 `openclaw/plugin-sdk/memory-host-core` 消费导出的记忆产物，而非深入特定记忆插件的私有布局。
- `registerMemoryPromptSection`、`registerMemoryFlushPlan` 和 `registerMemoryRuntime` 是遗留兼容的独占记忆插件 API。
- `MemoryFlushPlan.model` 可将 flush turn 固定到精确 `provider/model` 引用，如 `ollama/qwen3:8b`，不继承活跃回退链。
- `registerMemoryEmbeddingProvider` 已弃用。新嵌入应用 `api.registerEmbeddingProvider(...)` 和 `contracts.embeddingProviders`。
- 已有记忆专用 provider 在迁移窗口内继续工作，但插件检查将此报告为非捆绑插件的兼容债务。

### 事件和生命周期

| 方法                                       | 作用             |
| ------------------------------------------ | ---------------- |
| `api.on(hookName, handler, opts?)`         | 类型化生命周期钩子 |
| `api.onConversationBindingResolved(handler)` | 对话绑定回调   |

示例、常见钩子名和守卫语义见 [Plugin hooks](/plugins/hooks)。

### 钩子决策语义

- `before_tool_call`：返回 `{ block: true }` 是终结的。任何处理器设置后，更低优先级处理器被跳过。
- `before_tool_call`：返回 `{ block: false }` 被视为无决策（等同于省略 `block`），不是覆盖。
- `before_install`：返回 `{ block: true }` 是终结的。任何处理器设置后，更低优先级处理器被跳过。
- `before_install`：返回 `{ block: false }` 被视为无决策（等同于省略 `block`），不是覆盖。
- `reply_dispatch`：返回 `{ handled: true, ... }` 是终结的。任何处理器声明分发后，更低优先级处理器和默认模型分发路径被跳过。
- `message_sending`：返回 `{ cancel: true }` 是终结的。任何处理器设置后，更低优先级处理器被跳过。
- `message_sending`：返回 `{ cancel: false }` 被视为无决策（等同于省略 `cancel`），不是覆盖。
- `message_received`：需要入站线程/话题路由时用类型化 `threadId` 字段。`metadata` 保留给 channel 专用额外信息。
- `message_sending`：优先用类型化 `replyToId` / `threadId` 路由字段再回退到 channel 专用 `metadata`。
- `gateway_start`：用 `ctx.config`、`ctx.workspaceDir` 和 `ctx.getCron?.()` 获取 gateway 持有的启动状态，不依赖内部 `gateway:startup` 钩子。
- `cron_changed`：观察 gateway 持有的 cron 生命周期变更。同步外部唤醒调度器时用 `event.job?.state?.nextRunAtMs` 和 `ctx.getCron?.()`，保持 OpenClaw 作为到期检查和执行的唯一真相源。

### API 对象字段

| 字段                   | 类型                      | 描述                                                             |
| ---------------------- | ------------------------- | ---------------------------------------------------------------- |
| `api.id`               | `string`                  | 插件 id                                                          |
| `api.name`             | `string`                  | 展示名                                                           |
| `api.version`          | `string?`                 | 插件版本（可选）                                                 |
| `api.description`      | `string?`                 | 插件描述（可选）                                                 |
| `api.source`           | `string`                  | 插件来源路径                                                     |
| `api.rootDir`          | `string?`                 | 插件根目录（可选）                                               |
| `api.config`           | `OpenClawConfig`          | 当前配置快照（可用时为活跃内存运行时快照）                       |
| `api.pluginConfig`     | `Record<string, unknown>` | `plugins.entries.<id>.config` 的插件专用配置                     |
| `api.runtime`          | `PluginRuntime`           | [运行时 helper](/plugins/sdk-runtime)                            |
| `api.logger`           | `PluginLogger`            | 有范围 logger（`debug`、`info`、`warn`、`error`）                |
| `api.registrationMode` | `PluginRegistrationMode`  | 当前加载模式；`"setup-runtime"` 是轻量级预完整条目启动/设置窗口  |
| `api.resolvePath(input)` | `(string) => string`    | 相对于插件根解析路径                                             |

## 内部模块约定

插件内部用本地 barrel 文件做内部导入：

```
my-plugin/
  api.ts            # 外部消费者的公开导出
  runtime-api.ts    # 仅内部运行时导出
  index.ts          # 插件入口点
  setup-entry.ts    # 轻量级仅设置入口（可选）
```

> **警告**：永远不要在生产代码中通过 `openclaw/plugin-sdk/<your-plugin>` 导入自己的插件。内部导入通过 `./api.ts` 或 `./runtime-api.ts` 路由。SDK 路径仅是外部契约。

门面加载的捆绑插件公开表面（`api.ts`、`runtime-api.ts`、`index.ts`、`setup-entry.ts` 和类似公开入口文件）在 OpenClaw 已运行时优先使用活跃运行时配置快照。尚无运行时快照时回退到磁盘上已解析的配置文件。打包的捆绑插件门面应通过 OpenClaw 的插件门面加载器加载；从 `dist/extensions/...` 直接导入会绕过打包安装用于插件持有代码的清单和运行时 sidecar 检查。

Provider 插件可在 helper 有意为 provider 专用且尚不属于通用 SDK 子路径时暴露窄插件本地契约 barrel。捆绑示例：

- **Anthropic**：公开 `api.ts` / `contract-api.ts` 接缝用于 Claude beta-header 和 `service_tier` 流 helper。
- **`@openclaw/openai-provider`**：`api.ts` 导出 provider 构建器、默认模型 helper 和实时 provider 构建器。
- **`@openclaw/openrouter-provider`**：`api.ts` 导出 provider 构建器加上入门/配置 helper。

> **警告**：扩展生产代码也应避免 `openclaw/plugin-sdk/<other-plugin>` 导入。如果 helper 确实共享，将其提升到中性 SDK 子路径如 `openclaw/plugin-sdk/speech`、`.../provider-model-shared` 或其他能力导向表面，而非将两个插件耦合在一起。

## 相关

| 方向       | 内容                                        |
| ---------- | ------------------------------------------- |
| 入口点     | `definePluginEntry` 和 `defineChannelPluginEntry` 选项 |
| 运行时 helper | 完整 `api.runtime` 命名空间参考          |
| 设置和配置 | 打包、清单和配置 schema                     |
| 测试       | 测试工具和 lint 规则                        |
| SDK 迁移   | 从已弃用表面迁移                            |
| 插件内部   | 深层架构和能力模型                          |
