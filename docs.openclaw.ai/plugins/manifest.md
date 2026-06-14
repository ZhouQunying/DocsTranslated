# 插件 Manifest

## 架构精读

> 跳过不影响阅读翻译正文。

### Manifest 为什么能替代启动才知道插件能力？

传统插件系统必须加载插件代码才能知道它提供什么——就像你必须启动一个 Java 进程才能知道它注册了哪些 Spring Bean。OpenClaw 的 manifest 走了另一条路。所有插件标识、能力声明、配置 schema、认证元数据都写在 `openclaw.plugin.json` 中。核心**无需执行任何插件代码**即可完成配置验证、UI 提示生成和激活规划。这就像 Kubernetes 的 YAML 资源声明——你写 Pod spec 描述想要的状态，kube-apiserver 无需启动容器就能验证 spec 合法性、调度决策、生成状态摘要。好处是启动快（只解析 JSON 不执行 JS）、安全（不可信的插件不会在发现阶段执行代码）、可靠（manifest 损坏的插件在加载前就被阻止）。

第二个设计原则："一切必须廉价到无需启动插件运行时即可检查"。manifest 中的每个字段都遵循这个约束。`configSchema` 用 JSON Schema 验证，`providers` 是字符串数组，`activation` 是激活提示，`contracts` 是静态能力快照。全部是纯数据。没有任何字段需要执行代码才能获取。这就像编译器的常量折叠——如果能在编译时算出来就不要等到运行时。代价是有些动态信息（如实际可用模型列表）必须通过运行时钩子获取，manifest 只能声明"这个插件持有模型目录"。

第三个边界：控制面和数据面的分离。Manifest 是控制面——声明插件是什么、能做什么、何时激活。插件代码（`register(api)` 函数）是数据面——注册实际的钩子、工具、命令和 provider 流程。控制面可以在数据面不工作时仍然工作：你能读取一个未启用插件的 manifest 来生成配置 UI，就像你能 `kubectl describe` 一个未运行的 Pod。这个分离让 OpenClaw 的启动流水线能在加载任何运行时之前完成所有元数据工作。

---

此页面仅针对**原生 OpenClaw 插件 manifest**。

关于兼容捆绑布局，参见 [Plugin bundles](/plugins/bundles)。兼容捆绑格式使用不同的 manifest 文件（如 `.codex-plugin/plugin.json`、`.claude-plugin/plugin.json`）。

每个原生 OpenClaw 插件**必须**在**插件根目录**提供一个 `openclaw.plugin.json` 文件。OpenClaw 使用此 manifest **无需执行插件代码**即可验证配置。缺失或无效的 manifest 被视为插件错误并阻止配置验证。

## 此文件的用途

`openclaw.plugin.json` 是 OpenClaw 在**加载插件代码之前**读取的元数据。以下所有内容必须廉价到无需启动插件运行时即可检查。

**用于：**

- 插件标识、配置验证和配置 UI 提示
- 认证、入职和设置元数据（别名、自动启用、provider 环境变量、认证选项）
- 控制面表面的激活提示
- 简写模型族所有权
- 静态能力所有权快照（`contracts`）
- 共享 `openclaw qa` 宿主可检查的 QA runner 元数据
- 合并到目录和验证表面的 channel 特定配置元数据

**不用于：** 注册运行时行为、声明代码入口点或 npm 安装元数据。这些属于你的插件代码和 `package.json`。

## 最小示例

```json
{
  "id": "voice-call",
  "configSchema": {
    "type": "object",
    "additionalProperties": false,
    "properties": {}
  }
}
```

## 丰富示例

```json
{
  "id": "openrouter",
  "name": "OpenRouter",
  "description": "OpenRouter provider plugin",
  "version": "1.0.0",
  "providers": ["openrouter"],
  "modelSupport": {
    "modelPrefixes": ["router-"]
  },
  "cliBackends": ["openrouter-cli"],
  "setup": {
    "providers": [
      {
        "id": "openrouter",
        "envVars": ["OPENROUTER_API_KEY"]
      }
    ]
  },
  "providerAuthChoices": [
    {
      "provider": "openrouter",
      "method": "api-key",
      "choiceId": "openrouter-api-key",
      "choiceLabel": "OpenRouter API key",
      "groupId": "openrouter",
      "groupLabel": "OpenRouter",
      "cliFlag": "--openrouter-api-key",
      "cliOption": "--openrouter-api-key <key>"
    }
  ],
  "configSchema": {
    "type": "object",
    "additionalProperties": false,
    "properties": {
      "apiKey": { "type": "string" }
    }
  }
}
```

## 顶层字段参考

| 字段 | 必需 | 类型 | 含义 |
| --- | --- | --- | --- |
| `id` | 是 | `string` | 标准插件 id。用于 `plugins.entries.<id>`。 |
| `configSchema` | 是 | `object` | 此插件配置的内联 JSON Schema。 |
| `requiresPlugins` | 否 | `string[]` | 此插件生效所需的其他已安装插件 id。 |
| `enabledByDefault` | 否 | `true` | 标记捆绑插件默认启用。 |
| `legacyPluginIds` | 否 | `string[]` | 归一化到此标准 id 的旧版 id。 |
| `autoEnableWhenConfiguredProviders` | 否 | `string[]` | 当认证、配置或模型引用提及它们时自动启用此插件的 provider id。 |
| `kind` | 否 | `"memory"` \| `"context-engine"` | 声明 `plugins.slots.*` 使用的排他插件类型。 |
| `channels` | 否 | `string[]` | 此插件持有的 channel id。 |
| `providers` | 否 | `string[]` | 此插件持有的 provider id。 |
| `modelSupport` | 否 | `object` | manifest 持有的简写模型族元数据，用于在运行时前自动加载插件。 |
| `modelCatalog` | 否 | `object` | 声明式模型目录元数据，用于只读列表、入职、模型选择器。 |
| `modelIdNormalization` | 否 | `object` | provider 持有的模型 id 别名/前缀清理，必须在 provider 运行时加载前运行。 |
| `providerEndpoints` | 否 | `object[]` | manifest 持有的端点 host/baseUrl 元数据。 |
| `cliBackends` | 否 | `string[]` | 此插件持有的 CLI 推理后端 id。 |
| `syntheticAuthRefs` | 否 | `string[]` | 冷模型发现期间在运行时加载前应探测的合成认证钩子引用。 |
| `commandAliases` | 否 | `object[]` | 此插件持有的命令名，应在运行时加载前产生插件感知的诊断。 |
| `providerAuthAliases` | 否 | `Record<string, string>` | 应复用另一个 provider id 进行认证查找的 provider id。 |
| `providerAuthChoices` | 否 | `object[]` | 入职选择器、首选 provider 解析和简单 CLI 标志接线的廉价认证选项元数据。 |
| `activation` | 否 | `object` | 启动、provider、命令、channel、路由和能力触发加载的廉价激活规划器元数据。 |
| `setup` | 否 | `object` | 发现和设置表面可在不加载插件运行时情况下检查的廉价设置/入职描述符。 |
| `contracts` | 否 | `object` | 外部认证钩子、嵌入、语音、实时转录、实时语音、媒体理解、图片生成、音乐生成、视频生成、网页获取、网页搜索和工具所有权的静态能力所有权快照。 |
| `channelConfigs` | 否 | `Record<string, object>` | manifest 持有的 channel 配置元数据，在运行时加载前合并到发现和验证表面。 |
| `skills` | 否 | `string[]` | 要加载的技能目录，相对于插件根目录。 |
| `name` | 否 | `string` | 人类可读的插件名。 |
| `description` | 否 | `string` | 插件表面显示的简短摘要。 |
| `version` | 否 | `string` | 信息性插件版本。 |
| `uiHints` | 否 | `Record<string, object>` | 配置字段的 UI 标签、占位符和敏感性提示。 |

## 激活参考

当插件可以廉价声明哪些控制面事件应将其包含在激活/加载计划中时使用 `activation`。

此块是规划器元数据，不是生命周期 API。它不注册运行时行为，不替代 `register(...)`。激活规划器使用这些字段在回退到现有 manifest 所有权元数据（如 `providers`、`channels`、`commandAliases`、`setup.providers`、`contracts.tools`）之前缩小候选插件。

优先使用已描述所有权的最窄元数据。当 `providers`、`channels`、`commandAliases`、设置描述符或 `contracts` 字段表达关系时使用它们。仅在那些所有权字段无法表示时使用 `activation` 作为额外规划器提示。

每个插件应有意设置 `activation.onStartup`。仅在插件必须在 Gateway 启动期间运行时设为 `true`。当插件在启动时是惰性的且应仅从更窄触发器加载时设为 `false`。

```json
{
  "activation": {
    "onStartup": false,
    "onProviders": ["openai"],
    "onCommands": ["models"],
    "onChannels": ["web"],
    "onRoutes": ["gateway-webhook"],
    "onConfigPaths": ["browser"],
    "onCapabilities": ["provider", "tool"]
  }
}
```

| 字段 | 类型 | 含义 |
| --- | --- | --- |
| `onStartup` | `boolean` | 显式 Gateway 启动激活。每个插件应设置此项。 |
| `onProviders` | `string[]` | 应将此插件包含在激活/加载计划中的 provider id。 |
| `onAgentHarnesses` | `string[]` | 应将此插件包含在激活计划中的嵌入式 agent harness 运行时 id。 |
| `onCommands` | `string[]` | 应将此插件包含在激活计划中的命令 id。 |
| `onChannels` | `string[]` | 应将此插件包含在激活计划中的 channel id。 |
| `onRoutes` | `string[]` | 应将此插件包含在激活计划中的路由类型。 |
| `onConfigPaths` | `string[]` | 路径存在且未显式禁用时应将此插件包含在启动/加载计划中的根相对配置路径。 |
| `onCapabilities` | `Array<"provider" \| "channel" \| "tool" \| "hook">` | 控制面激活规划使用的宽泛能力提示。尽可能优先使用更窄的字段。 |

## 相关

- [Plugin architecture](/plugins/architecture)
- [Plugin architecture internals](/plugins/architecture-internals)
- [Building plugins](/plugins/building-plugins)
