# SDK: Provider 插件

## 架构精读

> 跳过不影响阅读翻译正文。

### 42 个钩子为什么不是 5 个？

Express 中间件是一条扁平的洋葱——`use()` 按注册顺序执行，每个中间件可以做任何事。Provider 钩子也是有序执行，但它是**命名的、有语义的**钩子链——`catalog` 负责模型目录，`resolveAuth` 负责认证，`buildRequest` 负责请求构建，`classifyOutcome` 负责结果分类。42 个钩子看起来很多，但它们是增量使用的：大多数 provider 只需 2-3 个（`catalog` + `resolveDynamicModel`）。就像 Linux 内核的 netfilter 框架有 PREROUTING、INPUT、FORWARD、OUTPUT、POSTROUTING 五个钩子点，每个点又可以挂多个钩子——框架预定义了语义位置，开发者只在需要的位置插入逻辑。好处是 OpenClaw 核心精确知道每个 provider 在哪些环节做了自定义，诊断和调试时可以精确定位。

第二个设计：族钩子构建器（family builder）。OpenAI 兼容的 provider 都需要类似的 replay 策略（工具调用 id 清理、助手优先排序修复）。与其每个插件手写这些钩子，不如提供一个 `buildProviderReplayFamilyHooks({ family: "openai-compatible" })` 一行搞定。这就是"约定优于配置"的体现——常见的钩子组合被预构建为 family builder，只有偏离约定的 provider 才需要手写。就像 Spring Boot 的 `@SpringBootApplication` 注解：一个注解替代了十几个 `@Configuration`，但需要自定义时随时可以拆开。当前可用的 replay family：`openai-compatible`（OpenAI 兼容传输）、`anthropic-by-model`（Claude 感知的 Anthropic 传输）、`google-gemini`（原生 Gemini）、`passthrough-gemini`（代理传输中的 Gemini）、`hybrid-anthropic-openai`（混合传输）。

第三个边界：动态模型解析。当 provider 接受任意模型 ID（如代理或路由器）时，`resolveDynamicModel` 钩子将未知 ID 解析为完整的模型配置。如果解析需要网络调用，`prepareDynamicModel` 做异步预热——`resolveDynamicModel` 在它完成后再次运行。这就像微服务的服务发现——你不知道所有上游服务的地址，但可以通过注册中心按需查询。好处是代理类 provider（如 OpenRouter）无需预先声明所有可用模型。

---

本指南介绍如何构建为 OpenClaw 添加模型 provider（LLM）的 provider 插件。如果尚未构建过 OpenClaw 插件，先阅读 [Getting Started](/plugins/building-plugins) 了解基本包结构和 manifest 设置。

> **提示：** Provider 插件向 OpenClaw 的正常推理循环添加模型。如果模型必须通过持有线程、压缩或工具事件的原生 agent 守护进程运行，将 provider 与 [agent harness](/plugins/sdk-agent-harness) 配对，而非将守护进程协议细节放入核心。

## 演练

### 包和 manifest

```json
{
  "name": "@myorg/openclaw-acme-ai",
  "version": "1.0.0",
  "type": "module",
  "openclaw": {
    "extensions": ["./index.ts"],
    "providers": ["acme-ai"],
    "compat": {
      "pluginApi": ">=2026.3.24-beta.2",
      "minGatewayVersion": "2026.3.24-beta.2"
    }
  }
}
```

```json
{
  "id": "acme-ai",
  "name": "Acme AI",
  "description": "Acme AI model provider",
  "providers": ["acme-ai"],
  "modelSupport": {
    "modelPrefixes": ["acme-"]
  },
  "setup": {
    "providers": [
      {
        "id": "acme-ai",
        "envVars": ["ACME_AI_API_KEY"]
      }
    ]
  },
  "configSchema": {
    "type": "object",
    "additionalProperties": false
  }
}
```

manifest 声明 `setup.providers[].envVars` 以便 OpenClaw 无需加载插件运行时即可检测凭证。添加 `providerAuthAliases` 当 provider 变体应复用另一个 provider id 的认证时。`modelSupport` 是可选的，让 OpenClaw 在运行时钩子存在前从简写模型 id（如 `acme-large`）自动加载 provider 插件。

### 注册 provider

最小文本 provider 需要 `id`、`label`、`auth` 和 `catalog`。`catalog` 是 provider 持有的运行时/配置钩子；它可调用实际厂商 API 并返回 `models.providers` 条目。

```typescript
import { definePluginEntry } from "openclaw/plugin-sdk/plugin-entry";
import { createProviderApiKeyAuthMethod } from "openclaw/plugin-sdk/provider-auth";

export default definePluginEntry({
  id: "acme-ai",
  name: "Acme AI",
  description: "Acme AI model provider",
  register(api) {
    api.registerProvider({
      id: "acme-ai",
      label: "Acme AI",
      docsPath: "/providers/acme-ai",
      envVars: ["ACME_AI_API_KEY"],

      auth: [
        createProviderApiKeyAuthMethod({
          providerId: "acme-ai",
          methodId: "api-key",
          label: "Acme AI API key",
          envVar: "ACME_AI_API_KEY",
          defaultModel: "acme-ai/acme-large",
        }),
      ],

      catalog: {
        order: "simple",
        run: async (ctx) => {
          const apiKey = ctx.resolveProviderApiKey("acme-ai").apiKey;
          if (!apiKey) return null;
          return {
            provider: {
              baseUrl: "https://api.acme-ai.com/v1",
              apiKey,
              api: "openai-completions",
              models: [
                {
                  id: "acme-large",
                  name: "Acme Large",
                  reasoning: true,
                  input: ["text", "image"],
                  contextWindow: 200000,
                  maxTokens: 32768,
                },
              ],
            },
          };
        },
      },
    });
  },
});
```

`registerModelCatalogProvider` 是较新的控制面目录表面，用于列表/帮助/选择器 UI。用于文本、图片生成、视频生成和音乐生成行。将厂商端点调用和响应映射保持在插件中；OpenClaw 持有共享行形状、源标签和帮助渲染。

对仅注册一个文本 provider（API 密钥认证加单个目录支持的运行时）的捆绑 provider，优先使用更窄的 `defineSingleProviderPluginEntry(...)` 辅助。`buildProvider` 是 OpenClaw 可解析真实 provider 认证时使用的实时目录路径。`buildStaticProvider` 仅用于认证配置前可安全显示的离线行；它不要求凭证或网络请求。

### 添加动态模型解析

如果 provider 接受任意模型 ID（如代理或路由器），添加 `resolveDynamicModel`：

```typescript
api.registerProvider({
  // ... id, label, auth, catalog

  resolveDynamicModel: (ctx) => ({
    id: ctx.modelId,
    name: ctx.modelId,
    provider: "acme-ai",
    api: "openai-completions",
    baseUrl: "https://api.acme-ai.com/v1",
    reasoning: false,
    input: ["text"],
    contextWindow: 128000,
    maxTokens: 8192,
  }),
});
```

如果解析需要网络调用，使用 `prepareDynamicModel` 做异步预热——`resolveDynamicModel` 在它完成后再次运行。

### 添加运行时钩子

大多数 provider 只需 `catalog` + `resolveDynamicModel`。按需增量添加钩子。

共享辅助构建器覆盖最常见的 replay/工具兼容族，插件通常无需逐个手写每个钩子：

```typescript
import { buildProviderReplayFamilyHooks } from "openclaw/plugin-sdk/provider-model-shared";
import { buildProviderStreamFamilyHooks } from "openclaw/plugin-sdk/provider-stream";
import { buildProviderToolCompatFamilyHooks } from "openclaw/plugin-sdk/provider-tools";

const GOOGLE_FAMILY_HOOKS = {
  ...buildProviderReplayFamilyHooks({ family: "google-gemini" }),
  ...buildProviderStreamFamilyHooks("google-thinking"),
  ...buildProviderToolCompatFamilyHooks("gemini"),
};

api.registerProvider({
  id: "acme-gemini-compatible",
  // ...
  ...GOOGLE_FAMILY_HOOKS,
});
```

可用的 replay family：

| 族 | 接入内容 | 捆绑示例 |
| --- | --- | --- |
| `openai-compatible` | OpenAI 兼容传输的共享 replay 策略 | `moonshot`、`ollama`、`xai` |
| `anthropic-by-model` | 按 `modelId` 选择的 Claude 感知 replay 策略 | `amazon-bedrock`、`anthropic-vertex` |
| `google-gemini` | 原生 Gemini replay 策略加引导 replay 清理 | `google`、`google-gemini-cli` |
| `passthrough-gemini` | 代理传输中 Gemini 思维签名清理 | `openrouter`、`kilocode` |
| `hybrid-anthropic-openai` | 混合 Anthropic 和 OpenAI 模型表面的混合策略 | `minimax` |

### 所有可用的 provider 钩子

OpenClaw 按以下顺序调用钩子。大多数 provider 仅使用 2-3 个：

| # | 钩子 | 使用时机 |
| --- | --- | --- |
| 1 | `catalog` | 模型目录或基础 URL 默认值 |
| 2 | `applyConfigDefaults` | 配置具体化期间的 provider 级全局默认值 |
| 3 | `normalizeModelId` | 查找前的旧版/预览模型 id 别名清理 |
| 4 | `normalizeTransport` | 通用模型组装前的 provider 族 `api`/`baseUrl` 清理 |
| 5 | `normalizeConfig` | 规范化 `models.providers.<id>` 配置 |
| 7 | `resolveConfigApiKey` | provider 持有的环境标记认证解析 |
| 10 | `resolveDynamicModel` | 接受任意上游模型 ID |
| 11 | `prepareDynamicModel` | 解析前的异步元数据获取 |
| 12 | `normalizeResolvedModel` | runner 之前的传输重写 |
| 15 | `resolveReasoningOutputMode` | 标记式 vs 原生式推理输出契约 |
| 19 | `wrapStreamFn` | 正常流路径上的自定义头部/主体包装 |
| 25 | `matchesContextOverflowError` | provider 持有的溢出检测 |
| 26 | `classifyFailoverReason` | provider 持有的限流/过载分类 |
| 35 | `prepareRuntimeAuth` | 推理前的 token 交换 |
| 38 | `createEmbeddingProvider` | provider 持有的记忆/搜索嵌入适配器 |
| 39 | `buildReplayPolicy` | 自定义转录回放/压缩策略 |
| 40 | `sanitizeReplayHistory` | 通用清理后的 provider 特定回放重写 |
| 41 | `validateReplayTurns` | 嵌入式 runner 之前的严格回放回合验证 |
| 42 | `onModelSelected` | 选择后回调（如遥测） |

关于详细描述和实际示例，参见 [Internals: Provider Runtime Hooks](/plugins/architecture-internals#provider-runtime-hooks)。

### 添加额外能力（可选）

provider 插件可在文本推理旁注册嵌入、语音、实时转录、实时语音、媒体理解、图片生成、视频生成、网页获取和网页搜索。OpenClaw 将此分类为 **hybrid-capability**（混合能力）插件——公司插件的推荐模式（每个厂商一个插件）。参见 [Internals: Capability Ownership](/plugins/architecture#capability-ownership-model)。

在 `register(api)` 中在现有 `api.registerProvider(...)` 调用旁注册每个能力。仅选择需要的能力。

## 相关

- [Building plugins](/plugins/building-plugins)
- [Plugin architecture](/plugins/architecture)
- [Agent harness plugins](/plugins/sdk-agent-harness)
