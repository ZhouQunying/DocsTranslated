# 设置和配置

## 架构精读

> 跳过不影响阅读翻译正文。

### 为什么插件打包拆成 package.json、manifest、setup entry 三层？

这三层各有分工：`package.json` 告诉安装器"怎么装"，`openclaw.plugin.json` 告诉运行时"有什么"，`setup-entry.ts` 告诉设置器"怎么配"。就像 Android 的三层结构——APK 包管理器管安装，AndroidManifest.xml 管组件声明，Application 类管运行时初始化。好处是设置流程不需要加载完整的 crypto 库和 CLI 注册，坏处是作者需要在三个地方保持一致。

第二个关键设计：延迟加载让冷启动更快。启用 `deferConfiguredChannelFullLoadUntilAfterListen` 后，Gateway 在 listen 前只加载 setupEntry（channel 注册和必要 HTTP 路由），完整入口在 listen 后才加载。这就像 HTML 脚本标签的 `defer` 属性——非关键脚本延迟执行，先让页面可交互。好处是 Gateway 更快开始接受请求，坏处是 setupEntry 必须包含 listen 前需要的所有注册。

第三个边界：setupEntry 的职责边界。setupEntry 只注册 channel 对象、listen 前需要的 HTTP 路由和 gateway 方法。它不包含 CLI 注册、后台服务、重型 SDK 导入或仅启动后需要的 gateway 方法。判断标准是：这个注册是否影响 Gateway listen？不影响就放完整入口，影响才放 setupEntry。

---

插件打包（`package.json` 元数据）、manifest（`openclaw.plugin.json`）、设置入口和配置 schema 的参考。

**提示**：在找操作指南？操作指南在上下文中覆盖打包：[Channel plugins](/plugins/sdk-channel-plugins#step-1-package-and-manifest) 和 [Provider plugins](/plugins/sdk-provider-plugins#step-1-package-and-manifest)。

## 包元数据

`package.json` 需要一个 `openclaw` 字段，告诉插件系统你的插件提供什么：

**Channel 插件**

```json
{
  "name": "@myorg/openclaw-my-channel",
  "version": "1.0.0",
  "type": "module",
  "openclaw": {
    "extensions": ["./index.ts"],
    "setupEntry": "./setup-entry.ts",
    "channel": {
      "id": "my-channel",
      "label": "My Channel",
      "blurb": "Short description of the channel."
    }
  }
}
```

**Provider 插件 / ClawHub 基线**

```json
{
  "name": "@myorg/openclaw-my-plugin",
  "version": "1.0.0",
  "type": "module",
  "openclaw": {
    "extensions": ["./index.ts"],
    "compat": {
      "pluginApi": ">=2026.3.24-beta.2",
      "minGatewayVersion": "2026.3.24-beta.2"
    },
    "build": {
      "openclawVersion": "2026.3.24-beta.2",
      "pluginSdkVersion": "2026.3.24-beta.2"
    }
  }
}
```

> **注意**：如果在 ClawHub 外部发布插件，`compat` 和 `build` 字段是必需的。标准发布片段在 `docs/snippets/plugin-publish/` 中。

### `openclaw` 字段

入口点文件（相对于包根）。

轻量级仅设置入口（可选）。

Channel 目录元数据，用于设置、选择器、快速入门和状态表面。

此插件注册的 provider id。

安装提示：`npmSpec`、`localPath`、`defaultChoice`、`minHostVersion`、`expectedIntegrity`、`allowInvalidConfigRecovery`。

启动行为标志。

### `openclaw.channel`

`openclaw.channel` 是廉价的包元数据，用于 channel 发现和设置表面在运行时加载前使用。

| 字段                                     | 类型       | 含义                                                                |
| ---------------------------------------- | ---------- | ------------------------------------------------------------------- |
| `id`                                     | `string`   | 规范 channel id                                                     |
| `label`                                  | `string`   | 主要 channel 标签                                                   |
| `selectionLabel`                         | `string`   | 选择器/设置标签，需要与 `label` 不同时使用                          |
| `detailLabel`                            | `string`   | 辅助细节标签，用于更丰富的 channel 目录和状态表面                   |
| `docsPath`                               | `string`   | 设置和选择链接的文档路径                                            |
| `docsLabel`                             | `string`   | 覆盖标签，用于文档链接需要与 channel id 不同时                      |
| `blurb`                                 | `string`   | 简短的入门/目录描述                                                 |
| `order`                                 | `number`   | channel 目录排序顺序                                                |
| `aliases`                               | `string[]` | channel 选择的额外查找别名                                          |
| `preferOver`                            | `string[]` | 此 channel 应优先排名的低优先级插件/channel id                      |
| `systemImage`                           | `string`   | channel UI 目录的可选图标/系统图像名                                |
| `selectionDocsPrefix`                   | `string`   | 选择表面中文档链接前的前缀文本                                      |
| `selectionDocsOmitLabel`                | `boolean`  | 在选择副本中直接显示文档路径而非带标签的文档链接                    |
| `selectionExtras`                       | `string[]` | 选择副本中追加的额外短字符串                                        |
| `markdownCapable`                       | `boolean`  | 标记 channel 支持 markdown，用于出站格式化决策                      |
| `exposure`                              | `object`   | channel 可见性控制，用于设置、已配置列表和文档表面                  |
| `quickstartAllowFrom`                   | `boolean`  | 将此 channel 加入标准快速入门 `allowFrom` 设置流程                  |
| `forceAccountBinding`                   | `boolean`  | 即使只有一个账户也要求显式账户绑定                                  |
| `preferSessionLookupForAnnounceTarget`  | `boolean`  | 解析此 channel 的公告目标时优先使用会话查找                         |

示例：

```json
{
  "openclaw": {
    "channel": {
      "id": "my-channel",
      "label": "My Channel",
      "selectionLabel": "My Channel (self-hosted)",
      "detailLabel": "My Channel Bot",
      "docsPath": "/channels/my-channel",
      "docsLabel": "my-channel",
      "blurb": "Webhook-based self-hosted chat integration.",
      "order": 80,
      "aliases": ["mc"],
      "preferOver": ["my-channel-legacy"],
      "selectionDocsPrefix": "Guide:",
      "selectionExtras": ["Markdown"],
      "markdownCapable": true,
      "exposure": {
        "configured": true,
        "setup": true,
        "docs": true
      },
      "quickstartAllowFrom": true
    }
  }
}
```

`exposure` 支持：

- `configured`：将 channel 包含在已配置/状态式列表表面中
- `setup`：将 channel 包含在交互式设置/配置选择器中
- `docs`：将 channel 标记为文档/导航表面中的公开

> **注意**：`showConfigured` 和 `showInSetup` 作为遗留别名仍受支持。优先用 `exposure`。

### `openclaw.install`

`openclaw.install` 是包元数据，不是 manifest 元数据。

| 字段                           | 类型                                | 含义                                                                          |
| ------------------------------ | ----------------------------------- | ----------------------------------------------------------------------------- |
| `clawhubSpec`                  | `string`                            | 安装/更新和入门按需安装流程的标准 ClawHub spec                                |
| `npmSpec`                      | `string`                            | 安装/更新回退流程的标准 npm spec                                              |
| `localPath`                    | `string`                            | 本地开发或捆绑安装路径                                                        |
| `defaultChoice`                | `"clawhub"` \| `"npm"` \| `"local"` | 多个源可用时的首选安装源                                                      |
| `minHostVersion`               | `string`                            | 最低支持的 OpenClaw 版本，格式为 `>=x.y.z` 或 `>=x.y.z-prerelease`            |
| `expectedIntegrity`            | `string`                            | 预期的 npm dist integrity 字符串，通常为 `sha512-...`，用于固定安装            |
| `allowInvalidConfigRecovery`   | `boolean`                           | 让捆绑插件重装流程从特定的过期配置故障中恢复                                  |

**入门行为**：交互式入门也使用 `openclaw.install` 做按需安装表面。如果插件在运行时加载前暴露 provider auth 选择或 channel 设置/目录元数据，入门可以显示该选择、提示 ClawHub、npm 或本地安装、安装或启用插件，然后继续所选流程。ClawHub 入门选择使用 `clawhubSpec`，存在时优先；npm 选择需要带注册表 `npmSpec` 的受信目录元数据；精确版本和 `expectedIntegrity` 是可选的 npm 固定。如果 `expectedIntegrity` 存在，安装/更新流程对 npm 强制执行。将"显示什么"元数据保持在 `openclaw.plugin.json`，"如何安装"元数据保持在 `package.json`。

**minHostVersion 执行**：如果设置了 `minHostVersion`，安装和非捆绑 manifest 注册表加载都强制执行。旧版 host 跳过外部插件；无效版本字符串被拒绝。捆绑源插件假定与 host 检出共同版本。

**固定 npm 安装**：对于固定 npm 安装，在 `npmSpec` 中保持精确版本并添加预期的产物完整性：

```json
{
  "openclaw": {
    "install": {
      "npmSpec": "@wecom/wecom-openclaw-plugin@1.2.3",
      "expectedIntegrity": "sha512-REPLACE_WITH_NPM_DIST_INTEGRITY",
      "defaultChoice": "npm"
    }
  }
}
```

**allowInvalidConfigRecovery 范围**：`allowInvalidConfigRecovery` 不是对损坏配置的通用绕过。它仅用于窄捆绑插件恢复，这样重装/设置可以修复已知的升级遗留问题，如缺失的捆绑插件路径或该插件的过期 `channels.<id>` 条目。如果配置因无关原因损坏，安装仍然失败关闭并告诉 operator 运行 `openclaw doctor --fix`。

### 延迟完整加载

Channel 插件可通过以下方式选择延迟加载：

```json
{
  "openclaw": {
    "extensions": ["./index.ts"],
    "setupEntry": "./setup-entry.ts",
    "startup": {
      "deferConfiguredChannelFullLoadUntilAfterListen": true
    }
  }
}
```

启用后，OpenClaw 在预 listen 启动阶段仅加载 `setupEntry`，即使对已配置的 channel 也是如此。完整入口在 gateway 开始监听后加载。

> **警告**：仅在 `setupEntry` 注册了 gateway listen 前需要的所有内容（channel 注册、HTTP 路由、gateway 方法）时启用延迟加载。如果完整入口持有必需的启动能力，保持默认行为。

如果设置/完整入口注册了 gateway RPC 方法，保持在插件专用前缀上。保留的核心 admin 命名空间（`config.*`、`exec.approvals.*`、`wizard.*`、`update.*`）保持核心持有并始终解析为 `operator.admin`。

## 插件 manifest

每个原生插件必须在包根附带 `openclaw.plugin.json`。OpenClaw 用它验证配置，不需要执行插件代码。

```json
{
  "id": "my-plugin",
  "name": "My Plugin",
  "description": "Adds My Plugin capabilities to OpenClaw",
  "configSchema": {
    "type": "object",
    "additionalProperties": false,
    "properties": {
      "webhookSecret": {
        "type": "string",
        "description": "Webhook verification secret"
      }
    }
  }
}
```

channel 插件需添加 `kind` 和 `channels`：

```json
{
  "id": "my-channel",
  "kind": "channel",
  "channels": ["my-channel"],
  "configSchema": {
    "type": "object",
    "additionalProperties": false,
    "properties": {}
  }
}
```

即使没有配置的插件也必须附带 schema。空 schema 是有效的：

```json
{
  "id": "my-plugin",
  "configSchema": {
    "type": "object",
    "additionalProperties": false
  }
}
```

完整 schema 参考见 [Plugin manifest](/plugins/manifest)。

## ClawHub 发布

插件包使用包专用的 ClawHub 命令：

```bash
clawhub package publish your-org/your-plugin --dry-run
clawhub package publish your-org/your-plugin
```

> **注意**：遗留的仅技能发布别名用于技能。插件包应始终使用 `clawhub package publish`。

## 设置入口

`setup-entry.ts` 是 `index.ts` 的轻量级替代品，OpenClaw 在仅需要设置表面（入门、配置修复、禁用 channel 检查）时加载。

```typescript
// setup-entry.ts

export default defineSetupPluginEntry(myChannelPlugin);
```

这避免在设置流程期间加载重型运行时代码（crypto 库、CLI 注册、后台服务）。

在 sidecar 模块中保持设置安全导出的捆绑工作区 channel 可用 `openclaw/plugin-sdk/channel-entry-contract` 的 `defineBundledChannelSetupEntry(...)` 代替 `defineSetupPluginEntry(...)`。该捆绑契约还支持可选的 `runtime` 导出，这样设置时运行时接线保持轻量且显式。

**OpenClaw 何时使用 setupEntry 而非完整入口**：

- channel 被禁用但需要设置/入门表面
- channel 已启用但未配置
- 启用了延迟加载（`deferConfiguredChannelFullLoadUntilAfterListen`）

**setupEntry 必须注册什么**：

- channel 插件对象（通过 `defineSetupPluginEntry`）
- gateway listen 前需要的任何 HTTP 路由
- 启动期间需要的任何 gateway 方法

这些启动 gateway 方法仍应避免保留的核心 admin 命名空间如 `config.*` 或 `update.*`。

**setupEntry 不应包含什么**：

- CLI 注册
- 后台服务
- 重型运行时导入（crypto、SDK）
- 仅启动后需要的 gateway 方法

### 窄设置 helper 导入

对于热设置专用路径，仅需部分设置表面时优先用窄设置 helper 接缝而非更广的 `plugin-sdk/setup` 伞：

| 导入路径                         | 用途                                                                            | 关键导出                                                                                                                                                                                                                                                                                                       |
| -------------------------------- | ------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `plugin-sdk/setup-runtime`       | 设置时运行时 helper，在 `setupEntry` / 延迟 channel 启动中保持可用              | `createSetupTranslator`、`createPatchedAccountSetupAdapter`、`createEnvPatchedAccountSetupAdapter`、`createSetupInputPresenceValidator`、`noteChannelLookupFailure`、`noteChannelLookupSummary`、`promptResolvedAllowFrom`、`splitSetupEntries`、`createAllowlistSetupWizardProxy`、`createDelegatedSetupWizardProxy` |
| `plugin-sdk/setup-adapter-runtime` | 已弃用兼容别名；用 `plugin-sdk/setup-runtime`                                 | `createEnvPatchedAccountSetupAdapter`                                                                                                                                                                                                                                                                          |
| `plugin-sdk/setup-tools`         | 设置/安装 CLI/归档/文档 helper                                                  | `formatCliCommand`、`detectBinary`、`extractArchive`、`resolveBrewExecutable`、`formatDocsLink`、`CONFIG_DIR`                                                                                                                                                                                                   |

需要完整共享设置工具箱（包括配置补丁 helper 如 `moveSingleAccountChannelSectionToDefaultAccount(...)`）时用更广的 `plugin-sdk/setup` 接缝。

固定设置向导文案用 `createSetupTranslator(...)`。它遵循 CLI 向导区域设置（`OPENCLAW_LOCALE`，然后是系统区域变量）并回退到英语。保持插件专用设置文本在插件持有的代码中，仅对通用设置标签、状态文本和官方捆绑插件设置文案使用共享目录键。

设置补丁适配器在导入时保持热路径安全。它们的捆绑单账户提升契约表面查找是延迟的，所以导入 `plugin-sdk/setup-runtime` 不会在适配器实际使用前急切加载捆绑契约表面发现。

### Channel 持有的单账户提升

当 channel 从单账户顶层配置升级到 `channels.<id>.accounts.*` 时，默认共享行为是将提升的账户作用域值移入 `accounts.default`。

捆绑 channel 可通过其设置契约表面缩小或覆盖该提升：

- `singleAccountKeysToMove`：应移入提升账户的额外顶层键
- `namedAccountPromotionKeys`：命名账户已存在时，仅这些键移入提升账户；共享策略/投递键保持在 channel 根
- `resolveSingleAccountPromotionTarget(...)`：选择哪个现有账户接收提升值

> **注意**：Matrix 是当前的捆绑示例。如果恰好存在一个命名 Matrix 账户，或 `defaultAccount` 指向现有的非规范键如 `Ops`，提升保留该账户而不是创建新的 `accounts.default` 条目。

## 配置 schema

插件配置根据 manifest 中的 JSON Schema 验证。用户通过以下方式配置插件：

```json5
{
  plugins: {
    entries: {
      "my-plugin": {
        config: {
          webhookSecret: "abc123",
        },
      },
    },
  },
}
```

插件在注册期间以 `api.pluginConfig` 接收此配置。

channel 专用配置用 channel 配置段：

```json5
{
  channels: {
    "my-channel": {
      token: "bot-token",
      allowFrom: ["user1", "user2"],
    },
  },
}
```

### 构建 channel 配置 schema

用 `buildChannelConfigSchema` 将 Zod schema 转换为插件持有配置产物使用的 `ChannelConfigSchema` 包装器：

```typescript

const accountSchema = z.object({
  token: z.string().optional(),
  allowFrom: z.array(z.string()).optional(),
  accounts: z.object({}).catchall(z.any()).optional(),
  defaultAccount: z.string().optional(),
});

const configSchema = buildChannelConfigSchema(accountSchema);
```

如果已经用 JSON Schema 或 TypeBox 编写契约，用直接 helper 让 OpenClaw 跳过元数据路径上的 Zod 到 JSON Schema 转换：

```typescript

const configSchema = buildJsonChannelConfigSchema(
  Type.Object({
    token: Type.Optional(Type.String()),
    allowFrom: Type.Optional(Type.Array(Type.String())),
  }),
);
```

第三方插件的冷路径契约仍是插件 manifest：将生成的 JSON Schema 镜像到 `openclaw.plugin.json#channelConfigs`。这样配置 schema、设置和 UI 表面可以检查 `channels.<id>`，不需要加载运行时代码。

## 设置向导

Channel 插件可为 `openclaw onboard` 提供交互式设置向导。向导是 `ChannelPlugin` 上的 `ChannelSetupWizard` 对象：

```typescript

const setupWizard: ChannelSetupWizard = {
  channel: "my-channel",
  status: {
    configuredLabel: "Connected",
    unconfiguredLabel: "Not configured",
    resolveConfigured: ({ cfg }) => Boolean((cfg.channels as any)?.["my-channel"]?.token),
  },
  credentials: [
    {
      inputKey: "token",
      providerHint: "my-channel",
      credentialLabel: "Bot token",
      preferredEnvVar: "MY_CHANNEL_BOT_TOKEN",
      envPrompt: "Use MY_CHANNEL_BOT_TOKEN from environment?",
      keepPrompt: "Keep current token?",
      inputPrompt: "Enter your bot token:",
      inspect: ({ cfg, accountId }) => {
        const token = (cfg.channels as any)?.["my-channel"]?.token;
        return {
          accountConfigured: Boolean(token),
          hasConfiguredValue: Boolean(token),
        };
      },
    },
  ],
};
```

`ChannelSetupWizard` 类型支持 `credentials`、`textInputs`、`dmPolicy`、`allowFrom`、`groupAccess`、`prepare`、`finalize` 等。完整示例见捆绑插件包（如 Discord 插件 `src/channel.setup.ts`）。

**共享 allowFrom 提示**：仅需标准 `note -> prompt -> parse -> merge -> patch` 流程的 DM 允许列表提示，优先用 `openclaw/plugin-sdk/setup` 的共享设置 helper：`createPromptParsedAllowFromForAccount(...)`、`createTopLevelChannelParsedAllowFromPrompt(...)` 和 `createNestedChannelParsedAllowFromPrompt(...)`。

**标准 channel 设置状态**：仅按标签、分数和可选额外行变化的 channel 设置状态块，优先用 `openclaw/plugin-sdk/setup` 的 `createStandardChannelSetupStatus(...)` 而不是在每个插件中手写相同的 `status` 对象。

**可选 channel 设置表面**：仅在特定上下文中出现的可选设置表面，用 `openclaw/plugin-sdk/channel-setup` 的 `createOptionalChannelSetupSurface`：

```typescript
import { createOptionalChannelSetupSurface } from "openclaw/plugin-sdk/channel-setup";

const setupSurface = createOptionalChannelSetupSurface({
  channel: "my-channel",
  label: "My Channel",
  npmSpec: "@myorg/openclaw-my-channel",
  docsPath: "/channels/my-channel",
});
// 返回 { setupAdapter, setupWizard }
```

`plugin-sdk/channel-setup` 也暴露底层 `createOptionalChannelSetupAdapter(...)` 和 `createOptionalChannelSetupWizard(...)` 构建器，仅需可选安装表面的一半时使用。

生成的可选适配器/向导在真实配置写入时失败关闭。它们在 `validateInput`、`applyConfig` 和 `finalize` 间复用一个安装必需消息，并在 `docsPath` 设置时追加文档链接。

**二进制支持的设置 helper**：二进制支持的设置 UI 优先用共享委托 helper，而不是将相同的二进制/状态胶水复制到每个 channel：

- `createDetectedBinaryStatus(...)` 用于仅按标签、提示、分数和二进制检测变化的状态块
- `createCliPathTextInput(...)` 用于路径支持的文本输入
- `createDelegatedSetupWizardStatusResolvers(...)`、`createDelegatedPrepare(...)`、`createDelegatedFinalize(...)` 和 `createDelegatedResolveConfigured(...)` 用于 `setupEntry` 需要延迟转发到更重型完整向导时
- `createDelegatedTextInputShouldPrompt(...)` 用于 `setupEntry` 仅需委托 `textInputs[*].shouldPrompt` 决策时

## 发布和安装

**外部插件**：发布到 [ClawHub](/clawhub)，然后安装：

**npm**

```bash
openclaw plugins install @myorg/openclaw-my-plugin
```

裸包 spec 在启动切换期间从 npm 安装。

**仅 ClawHub**

```bash
openclaw plugins install clawhub:@myorg/openclaw-my-plugin
```

**npm 包 spec**：包尚未迁移到 ClawHub 或迁移期间需要直接 npm 安装路径时用 npm：

```bash
openclaw plugins install npm:@myorg/openclaw-my-plugin
```

**仓库内插件**：放在捆绑插件工作区树下，构建时自动发现。

**用户可安装**：

```bash
openclaw plugins install <package-name>
```

**信息**：npm 源安装时，`openclaw plugins install` 将包安装到 `~/.openclaw/npm/projects` 下的每插件项目中，生命周期脚本禁用。保持插件依赖树为纯 JS/TS，避免需要 `postinstall` 构建的包。

> **注意**：Gateway 启动不安装插件依赖。npm/git/ClawHub 安装流程持有依赖收敛；本地插件必须已安装其依赖。

捆绑包元数据是显式的，不从 gateway 启动时的已构建 JavaScript 推断。运行时依赖属于持有它们的插件包；打包的 OpenClaw 启动永不修复或镜像插件依赖。

## 相关

- [Building plugins](/plugins/building-plugins) — 分步入门指南
- [Plugin manifest](/plugins/manifest) — 完整 manifest schema 参考
- [SDK entry points](/plugins/sdk-entrypoints) — `definePluginEntry` 和 `defineChannelPluginEntry`
