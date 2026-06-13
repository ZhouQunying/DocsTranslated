# 构建插件

## 架构精读

> 跳过不影响阅读翻译正文。

### 为什么插件不直接放进核心仓库？

OpenClaw 核心运行时只关心调度、模型路由和工具分发。每加一种消息渠道或模型 provider，就多一套协议适配和依赖版本。插件化后，新 channel 或 provider 作为独立 npm 包发布，用户按需安装。就像浏览器扩展——浏览器不需要内置每个网站的支持，扩展按需提供。

第二个关键设计：清单声明所有权，运行时负责执行。`openclaw.plugin.json` 告诉 OpenClaw "这个插件提供哪些工具"，但不会在启动时加载所有插件。OpenClaw 只在工具被调用时才加载对应插件的运行时。这就像 Java 的 SPI 机制——声明在 META-INF，实现在运行时按需加载。好处是启动快、内存省，坏处是首次调用可能有冷启动延迟。

第三个边界：工具分必选和可选。必选工具在插件启用后始终可用；可选工具需要用户显式 `tools.allow` 才暴露给模型。这是最小权限原则的应用——副作用大的工具（如执行二进制、调用外部 API）不应默认启用，就像 Linux 的 sudo 需要显式授权。

---

插件在不修改核心的前提下扩展 OpenClaw。插件可添加消息渠道、模型 provider、本地 CLI 后端、agent 工具、钩子、媒体 provider 或其他插件持有的能力。

不需要将外部插件添加到 OpenClaw 仓库。将包发布到 [ClawHub](/clawhub)，用户用以下命令安装：

```bash
openclaw plugins install clawhub:<package-name>
```

裸包规格在启动切换期间仍从 npm 安装。需要 ClawHub 解析时使用 `clawhub:` 前缀。

## 前置要求

- 使用 Node 22.19 或更新版本，以及 `npm` 或 `pnpm` 等包管理器。
- 熟悉 TypeScript ESM 模块。
- 仓库内捆绑插件开发需克隆仓库并运行 `pnpm install`。源码检出插件开发仅限 pnpm，因为 OpenClaw 从 `extensions/*` 工作区包加载捆绑插件。

## 选择插件形态

| 形态          | 用途                                   |
| ------------- | -------------------------------------- |
| Channel 插件  | 将 OpenClaw 连接到消息平台             |
| Provider 插件 | 添加模型、媒体、搜索、抓取、语音或实时 provider |
| CLI 后端插件  | 通过 OpenClaw 模型回退运行本地 AI CLI  |
| Tool 插件     | 注册 agent 工具                        |

## 快速开始

通过注册一个必选 agent 工具构建最小工具插件。这是最短的有用插件形态，展示包、清单、入口点和本地验证。

**步骤**

1. **创建包元数据**

   ```json package.json
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

   ```json openclaw.plugin.json
   {
     "id": "my-plugin",
     "name": "My Plugin",
     "description": "为 OpenClaw 添加自定义工具",
     "contracts": {
       "tools": ["my_tool"]
     },
     "activation": {
       "onStartup": true
     },
     "configSchema": {
       "type": "object",
       "additionalProperties": false
     }
   }
   ```

   已发布的外部插件应将运行时入口指向构建后的 JavaScript 文件。完整入口点契约见 [SDK 入口点](/plugins/sdk-entrypoints)。

   每个插件都需要清单，即使没有配置。运行时工具必须出现在 `contracts.tools` 中，这样 OpenClaw 不必急切加载每个插件运行时就能发现所有权。刻意设置 `activation.onStartup`。本例在 Gateway 启动时启动。

   完整清单字段见 [Plugin manifest](/plugins/manifest)。

2. **注册工具**

   ```typescript index.ts
   import { Type } from "typebox";
   import { definePluginEntry } from "openclaw/plugin-sdk/plugin-entry";

   export default definePluginEntry({
     id: "my-plugin",
     name: "My Plugin",
     description: "为 OpenClaw 添加自定义工具",
     register(api) {
       api.registerTool({
         name: "my_tool",
         description: "回显一个输入值",
         parameters: Type.Object({ input: Type.String() }),
         async execute(_id, params) {
           return {
             content: [{ type: "text", text: `Got: ${params.input}` }],
           };
         },
       });
     },
   });
   ```

   非 channel 插件使用 `definePluginEntry`。Channel 插件使用 `defineChannelPluginEntry`。

3. **测试运行时**

   已安装或外部插件可检查加载的运行时：

   ```bash
   openclaw plugins inspect my-plugin --runtime --json
   ```

   若插件注册了 CLI 命令，也运行该命令。例如 demo 命令应有执行证明如 `openclaw demo-plugin ping`。

   本仓库内的捆绑插件，OpenClaw 从 `extensions/*` 工作区发现源码检出插件包。运行最近的定向测试：

   ```bash
   pnpm test -- extensions/my-plugin/
   pnpm check
   ```

4. **发布**

   发布前验证包：

   ```bash
   clawhub package publish your-org/your-plugin --dry-run
   clawhub package publish your-org/your-plugin
   ```

   规范 ClawHub 片段在 `docs/snippets/plugin-publish/`。

5. **安装**

   通过 ClawHub 安装已发布的包：

   ```bash
   openclaw plugins install clawhub:your-org/your-plugin
   ```

## 注册工具

工具可必选或可选。必选工具在插件启用后始终可用。可选工具需要用户 opt-in。

```typescript
register(api) {
  api.registerTool(
    {
      name: "workflow_tool",
      description: "运行工作流",
      parameters: Type.Object({ pipeline: Type.String() }),
      async execute(_id, params) {
        return { content: [{ type: "text", text: params.pipeline }] };
      },
    },
    { optional: true },
  );
}
```

每个用 `api.registerTool(...)` 注册的工具也必须在插件清单中声明：

```json
{
  "contracts": {
    "tools": ["workflow_tool"]
  },
  "toolMetadata": {
    "workflow_tool": {
      "optional": true
    }
  }
}
```

用户用 `tools.allow` 选择加入：

```json5
{
  tools: { allow: ["workflow_tool"] }, // 或 ["my-plugin"] 启用该插件所有工具
}
```

可选工具控制工具是否暴露给模型。当工具或钩子应在模型选定后、动作执行前请求批准时，使用 [plugin permission requests](/plugins/plugin-permission-requests)。

副作用、不常见二进制或不应默认暴露的能力用可选工具。工具名不能与核心工具冲突；冲突被跳过并在插件诊断中报告。格式错误的注册（包括无 `parameters` 的工具描述符）同样被跳过和报告。注册的工具是类型化函数，模型在策略和允许列表检查通过后可调用。

工具工厂接收运行时提供的上下文对象。当工具需要为当前轮次记录、展示或适配活跃模型时使用 `ctx.activeModel`。对象可包含 `provider`、`modelId` 和 `modelRef`。将其视为信息性运行时元数据，不是对本地 operator、已安装插件代码或修改后 OpenClaw 运行时的安全边界。敏感本地工具仍应要求显式插件或 operator opt-in，并在活跃模型元数据缺失或不合适时失败关闭。

清单声明所有权和发现；执行仍调用已注册的活跃工具实现。保持 `toolMetadata.<tool>.optional: true` 与 `api.registerTool(..., { optional: true })` 对齐，这样 OpenClaw 可避免加载该插件运行时直到工具被显式允许。

## 导入约定

从聚焦的 SDK 子路径导入：

```typescript

```

不要从已弃用的根 barrel 导入：

```typescript

```

插件包内部，用 `api.ts` 和 `runtime-api.ts` 等本地 barrel 文件做内部导入。不要通过 SDK 路径导入自己的插件。Provider 专用 helper 应留在 provider 包中，除非接缝确实通用。

自定义 Gateway RPC 方法是高级入口点。保持在插件专用前缀上；核心 admin 命名空间如 `config.*`、`exec.approvals.*`、`operator.admin.*`、`wizard.*` 和 `update.*` 保留并解析为 `operator.admin`。`openclaw/plugin-sdk/gateway-method-runtime` 桥保留给声明 `contracts.gatewayMethodDispatch: ["authenticated-request"]` 的插件 HTTP 路由。

完整导入映射见 [Plugin SDK 概述](/plugins/sdk-overview)。

## 提交前检查清单

- **package.json** 有正确的 `openclaw` 元数据
- **openclaw.plugin.json** 清单存在且有效
- 入口点使用 `defineChannelPluginEntry` 或 `definePluginEntry`
- 所有导入使用聚焦的 `plugin-sdk/<subpath>` 路径
- 内部导入使用本地模块，不用 SDK 自引用
- 测试通过（`pnpm test -- <bundled-plugin-root>/my-plugin/`）
- `pnpm check` 通过（仓库内插件）

## 针对 beta 版本测试

1. 关注 [openclaw/openclaw](https://github.com/openclaw/openclaw/releases) 的 GitHub 发布标签，通过 `Watch` > `Releases` 订阅。Beta 标签形如 `v2026.3.N-beta.1`。也可开启官方 OpenClaw X 账号 [@openclaw](https://x.com/openclaw) 的通知获取发布公告。
2. beta 标签一出现就测试你的插件。稳定版前的窗口通常只有几小时。
3. 测试后在 `plugin-forum` Discord 频道的你的插件帖子中发 `all good` 或坏了什么。还没有帖子就创建一个。
4. 如果有东西坏了，开或更新标题为 `Beta blocker: 插件名 - 摘要` 的 issue 并打 `beta-blocker` 标签。把 issue 链接放在你的帖子里。
5. 开标题为 `fix(插件id): beta blocker - 摘要` 的 PR 到 `main`，在 PR 和你的 Discord 帖子中都链接 issue。贡献者不能给 PR 打标签，所以标题是维护者和自动化的 PR 端信号。有 PR 的 blocker 会被合并；没有 PR 的可能照样发布。维护者在 beta 测试期间关注这些帖子。
6. 沉默等于绿色。错过窗口的话，你的修复大概率进下一个周期。

## 下一步

| 方向          | 内容                             |
| ------------- | -------------------------------- |
| Channel 插件  | 构建消息渠道插件                 |
| Provider 插件 | 构建模型 provider 插件           |
| CLI 后端插件  | 注册本地 AI CLI 后端             |
| SDK 概述      | 导入映射和注册 API 参考          |
| 运行时 Helper | 通过 api.runtime 使用 TTS、搜索、子 agent |
| 测试          | 测试工具和模式                   |
| Plugin Manifest | 完整清单 schema 参考           |

## 相关

- [Plugin hooks](/plugins/hooks)
- [Plugin architecture](/plugins/architecture)
