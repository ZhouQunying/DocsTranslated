# SDK 测试

## 架构精读

> 跳过不影响阅读翻译正文。

### 为什么测试也拆成十几个子路径而不是一个 test-utils？

这和 SDK 拆子路径是同一个原因：避免拉进不需要的依赖。`plugin-sdk/channel-contract-testing` 只拉 channel 契约测试需要的东西，`plugin-sdk/provider-http-test-mocks` 只拉 provider HTTP mock。就像 Jest 的 `jest.mock` 只 mock 指定模块而不是整个运行时——好处是每个测试文件只加载自己需要的测试基础设施，坏处是需要找到正确的子路径。

第二个关键设计：loader 支持的冒烟测试加手写 mock 的组合策略。手写 mock 快但跳过了真实 loader 的接受门控（manifest 验证、权限检查）。文档明确要求每个注册表面至少加一个 loader 支持的冒烟测试，确保 manifest 的 `kind` 字段和实际注册能力匹配。这就像单元测试加集成测试——单元测试快但可能漏掉集成问题，集成测试慢但能发现 manifest 和代码不一致的问题。

第三个边界：契约测试验证注册所有权。捆绑插件有专门的契约测试，断言哪个插件注册了哪个 provider、注册形状是否正确、运行时契约是否合规。这不是功能测试，是系统级不变量验证。就像 HTTP API 的契约测试——不验证单个请求是否正确，而是验证 API 契约本身是否被遵守。

---

OpenClaw 插件的测试工具、模式和 lint 执行的参考。

**提示**：在找测试示例？操作指南包含完整的测试示例：[Channel plugin tests](/plugins/sdk-channel-plugins#step-6-test) 和 [Provider plugin tests](/plugins/sdk-provider-plugins#step-6-test)。

## 测试工具

这些测试 helper 子路径是 OpenClaw 自己的捆绑插件测试的仓库本地源入口点。它们不是第三方插件的包导出，可能导入 Vitest 或其他仅仓库的测试依赖。

**插件 API mock 导入：** `openclaw/plugin-sdk/plugin-test-api`

**Agent 运行时契约导入：** `openclaw/plugin-sdk/agent-runtime-test-contracts`

**Channel 契约导入：** `openclaw/plugin-sdk/channel-contract-testing`

**Channel 测试 helper 导入：** `openclaw/plugin-sdk/channel-test-helpers`

**Channel 目标测试导入：** `openclaw/plugin-sdk/channel-target-testing`

**插件契约导入：** `openclaw/plugin-sdk/plugin-test-contracts`

**插件运行时测试导入：** `openclaw/plugin-sdk/plugin-test-runtime`

**Provider 契约导入：** `openclaw/plugin-sdk/provider-test-contracts`

**Provider HTTP mock 导入：** `openclaw/plugin-sdk/provider-http-test-mocks`

**环境/网络测试导入：** `openclaw/plugin-sdk/test-env`

**通用测试辅助导入：** `openclaw/plugin-sdk/test-fixtures`

**Node 内置 mock 导入：** `openclaw/plugin-sdk/test-node-mocks`

在 OpenClaw 仓库内，新的捆绑插件测试优先用下面的聚焦子路径。广泛的 `openclaw/plugin-sdk/testing` barrel 仅用于遗留兼容。仓库守卫拒绝 `plugin-sdk/testing` 和 `plugin-sdk/test-utils` 的新真实导入；这些名称仅作为兼容记录测试的已弃用兼容表面保留。

```typescript

  shouldAckReaction,
  removeAckReactionAfterReply,
} from "openclaw/plugin-sdk/channel-feedback";

  bundledPluginRoot,
  createCliRuntimeCapture,
  typedCases,
} from "openclaw/plugin-sdk/test-fixtures";

```

### 可用导出

| 导出                                                   | 用途                                                                                                                                     |
| ------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------- |
| `createTestPluginApi`                                  | 构建最小插件 API mock，用于直接注册单元测试。从 `plugin-sdk/plugin-test-api` 导入                                                        |
| `AUTH_PROFILE_RUNTIME_CONTRACT`                        | 原生 agent 运行时适配器的共享 auth-profile 契约辅助。从 `plugin-sdk/agent-runtime-test-contracts` 导入                               |
| `DELIVERY_NO_REPLY_RUNTIME_CONTRACT`                   | 原生 agent 运行时适配器的共享投递抑制契约辅助。从 `plugin-sdk/agent-runtime-test-contracts` 导入                                     |
| `OUTCOME_FALLBACK_RUNTIME_CONTRACT`                    | 原生 agent 运行时适配器的共享回退分类契约辅助。从 `plugin-sdk/agent-runtime-test-contracts` 导入                                     |
| `createParameterFreeTool`                              | 构建动态工具 schema 辅助，用于原生运行时契约测试。从 `plugin-sdk/agent-runtime-test-contracts` 导入                                   |
| `expectChannelInboundContextContract`                  | 断言 channel 入站上下文形状。从 `plugin-sdk/channel-contract-testing` 导入                                                               |
| `installChannelOutboundPayloadContractSuite`           | 安装 channel 出站负载契约用例。从 `plugin-sdk/channel-contract-testing` 导入                                                             |
| `createStartAccountContext`                            | 构建 channel 账户生命周期上下文。从 `plugin-sdk/channel-test-helpers` 导入                                                               |
| `installChannelActionsContractSuite`                   | 安装通用 channel 消息动作契约用例。从 `plugin-sdk/channel-test-helpers` 导入                                                             |
| `installChannelSetupContractSuite`                     | 安装通用 channel 设置契约用例。从 `plugin-sdk/channel-test-helpers` 导入                                                                 |
| `installChannelStatusContractSuite`                    | 安装通用 channel 状态契约用例。从 `plugin-sdk/channel-test-helpers` 导入                                                                 |
| `expectDirectoryIds`                                   | 断言目录列表函数的 channel 目录 id。从 `plugin-sdk/channel-test-helpers` 导入                                                            |
| `assertBundledChannelEntries`                          | 断言捆绑 channel 入口点暴露预期的公开契约。从 `plugin-sdk/channel-test-helpers` 导入                                                     |
| `formatEnvelopeTimestamp`                              | 格式化确定性信封时间戳。从 `plugin-sdk/channel-test-helpers` 导入                                                                        |
| `expectPairingReplyText`                               | 断言 channel 配对回复文本并提取其代码。从 `plugin-sdk/channel-test-helpers` 导入                                                         |
| `describePluginRegistrationContract`                   | 安装插件注册契约检查。从 `plugin-sdk/plugin-test-contracts` 导入                                                                         |
| `registerSingleProviderPlugin`                         | 在 loader 冒烟测试中注册一个 provider 插件。从 `plugin-sdk/plugin-test-runtime` 导入                                                     |
| `registerProviderPlugin`                               | 捕获一个插件的所有 provider 类型。从 `plugin-sdk/plugin-test-runtime` 导入                                                               |
| `registerProviderPlugins`                              | 跨多个插件捕获 provider 注册。从 `plugin-sdk/plugin-test-runtime` 导入                                                                   |
| `requireRegisteredProvider`                            | 断言 provider 集合包含一个 id。从 `plugin-sdk/plugin-test-runtime` 导入                                                                  |
| `createRuntimeEnv`                                     | 构建已 mock 的 CLI/插件运行时环境。从 `plugin-sdk/plugin-test-runtime` 导入                                                              |
| `createPluginSetupWizardStatus`                        | 构建 channel 插件的设置状态 helper。从 `plugin-sdk/plugin-test-runtime` 导入                                                             |
| `describeOpenAIProviderRuntimeContract`                | 安装 provider 家族运行时契约检查。从 `plugin-sdk/provider-test-contracts` 导入                                                           |
| `expectPassthroughReplayPolicy`                        | 断言 provider 重放策略直通 provider 持有的工具和元数据。从 `plugin-sdk/provider-test-contracts` 导入                                     |
| `runRealtimeSttLiveTest`                               | 用共享音频辅助 运行实时 STT provider 测试。从 `plugin-sdk/provider-test-contracts` 导入                                              |
| `normalizeTranscriptForMatch`                          | 模糊断言前规范化实时转录输出。从 `plugin-sdk/provider-test-contracts` 导入                                                               |
| `expectExplicitVideoGenerationCapabilities`            | 断言视频 provider 声明显式生成模式能力。从 `plugin-sdk/provider-test-contracts` 导入                                                     |
| `expectExplicitMusicGenerationCapabilities`            | 断言音乐 provider 声明显式生成/编辑能力。从 `plugin-sdk/provider-test-contracts` 导入                                                    |
| `mockSuccessfulDashscopeVideoTask`                     | 安装成功的 DashScope 兼容视频任务响应。从 `plugin-sdk/provider-test-contracts` 导入                                                      |
| `getProviderHttpMocks`                                 | 访问可选 provider HTTP/auth Vitest mock。从 `plugin-sdk/provider-http-test-mocks` 导入                                                   |
| `installProviderHttpMockCleanup`                       | 每次测试后重置 provider HTTP/auth mock。从 `plugin-sdk/provider-http-test-mocks` 导入                                                    |
| `installCommonResolveTargetErrorCases`                 | 目标解析错误处理的共享测试用例。从 `plugin-sdk/channel-target-testing` 导入                                                              |
| `shouldAckReaction`                                    | 检查 channel 是否应添加确认反应。从 `plugin-sdk/channel-feedback` 导入                                                                   |
| `removeAckReactionAfterReply`                          | 回复投递后移除确认反应。从 `plugin-sdk/channel-feedback` 导入                                                                            |
| `createTestRegistry`                                   | 构建 channel 插件注册表辅助。从 `plugin-sdk/plugin-test-runtime` 或 `plugin-sdk/channel-test-helpers` 导入                           |
| `createEmptyPluginRegistry`                            | 构建空插件注册表辅助。从 `plugin-sdk/plugin-test-runtime` 或 `plugin-sdk/channel-test-helpers` 导入                                  |
| `setActivePluginRegistry`                              | 为插件运行时测试安装注册表辅助。从 `plugin-sdk/plugin-test-runtime` 或 `plugin-sdk/channel-test-helpers` 导入                        |
| `createRequestCaptureJsonFetch`                        | 在媒体 helper 测试中捕获 JSON fetch 请求。从 `plugin-sdk/test-env` 导入                                                                  |
| `withServer`                                           | 对一次性本地 HTTP 服务器运行测试。从 `plugin-sdk/test-env` 导入                                                                          |
| `createMockIncomingRequest`                            | 构建最小入站 HTTP 请求对象。从 `plugin-sdk/test-env` 导入                                                                                |
| `withFetchPreconnect`                                  | 安装预连接钩子后运行 fetch 测试。从 `plugin-sdk/test-env` 导入                                                                           |
| `withEnv` / `withEnvAsync`                             | 临时补丁环境变量。从 `plugin-sdk/test-env` 导入                                                                                          |
| `createTempHomeEnv` / `withTempHome` / `withTempDir`   | 创建隔离的文件系统测试辅助。从 `plugin-sdk/test-env` 导入                                                                            |
| `createMockServerResponse`                             | 创建最小 HTTP 服务器响应 mock。从 `plugin-sdk/test-env` 导入                                                                             |
| `createCliRuntimeCapture`                              | 在测试中捕获 CLI 运行时输出。从 `plugin-sdk/test-fixtures` 导入                                                                          |
| `importFreshModule`                                    | 用新查询 token 导入 ESM 模块以绕过模块缓存。从 `plugin-sdk/test-fixtures` 导入                                                           |
| `bundledPluginRoot` / `bundledPluginFile`              | 解析捆绑插件源或 dist 辅助路径。从 `plugin-sdk/test-fixtures` 导入                                                                   |
| `mockNodeBuiltinModule`                                | 安装窄 Node 内置 Vitest mock。从 `plugin-sdk/test-node-mocks` 导入                                                                       |
| `createSandboxTestContext`                             | 构建沙箱测试上下文。从 `plugin-sdk/test-fixtures` 导入                                                                                   |
| `writeSkill`                                           | 写入技能辅助。从 `plugin-sdk/test-fixtures` 导入                                                                                     |
| `makeAgentAssistantMessage`                            | 构建 agent 转录消息辅助。从 `plugin-sdk/test-fixtures` 导入                                                                          |
| `peekSystemEvents` / `resetSystemEventsForTest`        | 检查和重置系统事件辅助。从 `plugin-sdk/test-fixtures` 导入                                                                           |
| `sanitizeTerminalText`                                 | 清理终端输出用于断言。从 `plugin-sdk/test-fixtures` 导入                                                                                 |
| `countLines` / `hasBalancedFences`                     | 断言分块输出形状。从 `plugin-sdk/test-fixtures` 导入                                                                                     |
| `runProviderCatalog`                                   | 用测试依赖执行 provider 目录钩子                                                                                                         |
| `resolveProviderWizardOptions`                         | 在契约测试中解析 provider 设置向导选项                                                                                                   |
| `resolveProviderModelPickerEntries`                    | 在契约测试中解析 provider 模型选择器条目                                                                                                 |
| `buildProviderPluginMethodChoice`                      | 构建 provider 向导选择 id 用于断言                                                                                                       |
| `setProviderWizardProvidersResolverForTest`            | 为隔离测试注入 provider 向导 provider                                                                                                    |
| `createProviderUsageFetch`                             | 构建 provider 用量 fetch 辅助                                                                                                         |
| `useFrozenTime` / `useRealTime`                        | 冻结和恢复计时器，用于时间敏感测试。从 `plugin-sdk/test-env` 导入                                                                        |
| `createTestWizardPrompter`                             | 构建已 mock 的设置向导提示器                                                                                                             |
| `createRuntimeTaskFlow`                                | 创建隔离的运行时任务流状态                                                                                                               |
| `typedCases`                                           | 为表格驱动测试保留字面类型。从 `plugin-sdk/test-fixtures` 导入                                                                           |

捆绑插件契约套件也使用 SDK 测试子路径做仅测试的注册表、manifest、公共产物和运行时辅助。依赖捆绑 OpenClaw 清单的核心专用套件保持在 `src/plugins/contracts` 下。新的扩展测试保持在文档化的聚焦 SDK 子路径如 `plugin-sdk/plugin-test-api`、`plugin-sdk/channel-contract-testing`、`plugin-sdk/agent-runtime-test-contracts`、`plugin-sdk/channel-test-helpers`、`plugin-sdk/plugin-test-contracts`、`plugin-sdk/plugin-test-runtime`、`plugin-sdk/provider-test-contracts`、`plugin-sdk/provider-http-test-mocks`、`plugin-sdk/test-env` 或 `plugin-sdk/test-fixtures`，而不是导入广泛的 `plugin-sdk/testing` 兼容 barrel、仓库 `src/**` 文件或仓库 `test/helpers/*` 桥接。

### 类型

聚焦测试子路径也重新导出测试文件中有用的类型：

```typescript

  ChannelAccountSnapshot,
  ChannelGatewayContext,
} from "openclaw/plugin-sdk/channel-contract";

```

## 测试目标解析

用 `installCommonResolveTargetErrorCases` 为 channel 目标解析添加标准错误用例：

```typescript

describe("my-channel target resolution", () => {
  installCommonResolveTargetErrorCases({
    resolveTarget: ({ to, mode, allowFrom }) => {
      // 你的 channel 目标解析逻辑
      return myChannelResolveTarget({ to, mode, allowFrom });
    },
    implicitAllowFrom: ["user1", "user2"],
  });

  // 添加 channel 专用测试用例
  it("should resolve @username targets", () => {
    // ...
  });
});
```

## 测试模式

### 测试注册契约

将手写 `api` mock 传给 `register(api)` 的单元测试不会执行 OpenClaw 的 loader 接受门控。为插件依赖的每个注册表面至少添加一个 loader 支持的冒烟测试，特别是钩子和独占能力如记忆。

真实 loader 在必需元数据缺失或插件调用其不持有的能力 API 时让插件注册失败。例如 `api.registerHook(...)` 需要钩子名，`api.registerMemoryCapability(...)` 需要插件 manifest 或导出入口声明 `kind: "memory"`。

### 测试运行时配置访问

测试捆绑 channel 插件时优先用 `openclaw/plugin-sdk/channel-test-helpers` 的共享插件运行时 mock。其已弃用的 `runtime.config.loadConfig()` 和 `runtime.config.writeConfigFile(...)` mock 默认抛异常，这样测试能捕获兼容 API 的新用法。仅在测试显式覆盖遗留兼容行为时覆盖这些 mock。

### 单元测试 channel 插件

```typescript

describe("my-channel plugin", () => {
  it("should resolve account from config", () => {
    const cfg = {
      channels: {
        "my-channel": {
          token: "test-token",
          allowFrom: ["user1"],
        },
      },
    };

    const account = myPlugin.setup.resolveAccount(cfg, undefined);
    expect(account.token).toBe("test-token");
  });

  it("should inspect account without materializing secrets", () => {
    const cfg = {
      channels: {
        "my-channel": { token: "test-token" },
      },
    };

    const inspection = myPlugin.setup.inspectAccount(cfg, undefined);
    expect(inspection.configured).toBe(true);
    expect(inspection.tokenStatus).toBe("available");
    // 不暴露 token 值
    expect(inspection).not.toHaveProperty("token");
  });
});
```

### 单元测试 provider 插件

```typescript

describe("my-provider plugin", () => {
  it("should resolve dynamic models", () => {
    const model = myProvider.resolveDynamicModel({
      modelId: "custom-model-v2",
      // ... context
    });

    expect(model.id).toBe("custom-model-v2");
    expect(model.provider).toBe("my-provider");
    expect(model.api).toBe("openai-completions");
  });

  it("should return catalog when API key is available", async () => {
    const result = await myProvider.catalog.run({
      resolveProviderApiKey: () => ({ apiKey: "test-key" }),
      // ... context
    });

    expect(result?.provider?.models).toHaveLength(2);
  });
});
```

### Mock 插件运行时

对于使用 `createPluginRuntimeStore` 的代码，在测试中 mock 运行时：

```typescript

const store = createPluginRuntimeStore
PluginRuntime
({
  pluginId: "test-plugin",
  errorMessage: "test runtime not set",
});

// 测试设置中
const mockRuntime = {
  agent: {
    resolveAgentDir: vi.fn().mockReturnValue("/tmp/agent"),
    // ... other mocks
  },
  config: {
    current: vi.fn(() => ({}) as const),
    mutateConfigFile: vi.fn(),
    replaceConfigFile: vi.fn(),
  },
  // ... other namespaces
} as unknown as PluginRuntime;

store.setRuntime(mockRuntime);

// 测试后
store.clearRuntime();
```

### 用每实例 stub 测试

优先用每实例 stub 而非原型变更：

```typescript
// 优先：每实例 stub
const client = new MyChannelClient();
client.sendMessage = vi.fn().mockResolvedValue({ id: "msg-1" });

// 避免：原型变更
// MyChannelClient.prototype.sendMessage = vi.fn();
```

## 契约测试（仓库内插件）

捆绑插件有验证注册所有权的契约测试：

```bash
pnpm test -- src/plugins/contracts/
```

这些测试断言：

- 哪些插件注册了哪些 provider
- 哪些插件注册了哪些语音 provider
- 注册形状正确性
- 运行时契约合规

### 运行有范围测试

特定插件：

```bash
pnpm test -- <bundled-plugin-root>/my-channel/
```

仅契约测试：

```bash
pnpm test -- src/plugins/contracts/shape.contract.test.ts
pnpm test -- src/plugins/contracts/auth-choice.contract.test.ts
pnpm test -- src/plugins/contracts/runtime-seams.contract.test.ts
```

## Lint 执行（仓库内插件）

`pnpm check` 对仓库内插件执行三条规则：

1. **禁止单片根导入** -- `openclaw/plugin-sdk` 根 barrel 被拒绝
2. **禁止直接 `src/` 导入** -- 插件不能直接导入 `../../src/`
3. **禁止自导入** -- 插件不能导入自己的 `plugin-sdk/<name>` 子路径

外部插件不受这些 lint 规则约束，但建议遵循相同模式。

## 测试配置

OpenClaw 使用带 V8 覆盖率阈值的 Vitest。插件测试：

```bash
# 运行所有测试
pnpm test

# 运行特定插件测试
pnpm test -- <bundled-plugin-root>/my-channel/src/channel.test.ts

# 用特定测试名过滤器运行
pnpm test -- <bundled-plugin-root>/my-channel/ -t "resolves account"

# 带覆盖率运行
pnpm test:coverage
```

本地运行导致内存压力时：

```bash
OPENCLAW_VITEST_MAX_WORKERS=1 pnpm test
```

## 相关

- [SDK Overview](/plugins/sdk-overview) -- 导入约定
- [SDK Channel Plugins](/plugins/sdk-channel-plugins) -- channel 插件接口
- [SDK Provider Plugins](/plugins/sdk-provider-plugins) -- provider 插件钩子
- [Building Plugins](/plugins/building-plugins) -- 入门指南
