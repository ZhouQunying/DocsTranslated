# SDK 入口点

## 架构精读

> 跳过不影响阅读翻译正文。

### 为什么插件入口拆成五种而不是一种？

一个 `definePluginEntry` 搞定所有场景写起来最简单，但 Gateway 启动时要加载几十个插件，每个都跑完整初始化，启动时间从秒级变成十秒级。五种入口点是两阶段启动策略：`defineToolPlugin` 给纯工具插件，`definePluginEntry` 给高级插件，`defineChannelPluginEntry` 给 channel 插件，`defineSetupPluginEntry` 和 `defineBundledChannelSetupEntry` 是轻量级变体，只注册 channel 不跑完整运行时。就像浏览器的关键渲染路径——先加载必要的 CSS，其他脚本异步加载。好处是禁用或未配置的 channel 不付出启动代价，坏处是插件作者需要理解哪些代码属于哪个阶段。

第二个关键设计：注册模式决定执行范围。`api.registrationMode` 有五种值：`full`（完整启动）、`discovery`（只读能力发现）、`setup-only`（仅注册 channel）、`setup-runtime`（轻量级预完整启动）、`cli-metadata`（仅 CLI 帮助信息）。这是控制启动成本的最后一道防线。即使加载了插件代码，`registrationMode` 也能告诉插件"这次只注册 CLI 描述符，不要建立网络连接"。就像 Spring 的 `@Profile` 注解——同一组件在不同 profile 下行为不同。

第三个边界：静态工具声明自动派生 manifest。`defineToolPlugin` 的 `tools` 数组是静态的，`openclaw plugins build` 构建时自动提取工具名写入 manifest，运行时不需要执行插件代码就能知道它提供哪些工具。就像 TypeScript 的类型推断——声明即文档。好处是工具名不会和 manifest 不同步，坏处是动态工具名必须用 `api.registerTool(...)` 手动注册。

---

每个插件导出一个默认入口对象。SDK 提供 helper 创建它们。

已安装插件的 `package.json` 应在可用时将运行时加载指向已构建的 JavaScript：

```json
{
  "openclaw": {
    "extensions": ["./src/index.ts"],
    "runtimeExtensions": ["./dist/index.js"],
    "setupEntry": "./src/setup-entry.ts",
    "runtimeSetupEntry": "./dist/setup-entry.js"
  }
}
```

`extensions` 和 `setupEntry` 对工作区和 git 检出开发仍是有效源入口。`runtimeExtensions` 和 `runtimeSetupEntry` 在 OpenClaw 加载已安装包时优先使用，让 npm 包避免运行时 TypeScript 编译。显式运行时入口是必需的：`runtimeSetupEntry` 需要 `setupEntry`，缺失 `runtimeExtensions` 或 `runtimeSetupEntry` 产物会让安装/发现失败，而不是默默回退到源码。如果已安装包只声明了 TypeScript 源入口，OpenClaw 会使用匹配的已构建 `dist/*.js` 同级文件（如果存在），然后回退到 TypeScript 源码。

所有入口路径必须保持在插件包目录内。运行时入口和推断的已构建 JavaScript 同级文件不会让逃逸的 `extensions` 或 `setupEntry` 源路径变为有效。

**提示**：在找操作指南？参见 [Tool Plugins](/plugins/tool-plugins)、[Channel Plugins](/plugins/sdk-channel-plugins) 或 [Provider Plugins](/plugins/sdk-provider-plugins)。

## `defineToolPlugin`

**导入：** `openclaw/plugin-sdk/tool-plugin`

用于仅添加 agent 工具的简单插件。`defineToolPlugin` 让编写源码保持精简，从 TypeBox schema 推断配置和工具参数类型，将普通返回值包装为 OpenClaw 工具结果格式，并暴露静态元数据供 `openclaw plugins build` 写入插件 manifest。

```typescript

export default defineToolPlugin({
  id: "stock-quotes",
  name: "Stock Quotes",
  description: "Fetch stock quotes.",
  configSchema: Type.Object({
    apiKey: Type.Optional(Type.String({ description: "API key." })),
  }),
  tools: (tool) => [
    tool({
      name: "quote",
      label: "Quote",
      description: "Fetch a quote.",
      parameters: Type.Object({
        symbol: Type.String({ description: "Ticker symbol." }),
      }),
      execute: async ({ symbol }, config) => ({ symbol, hasKey: Boolean(config.apiKey) }),
    }),
  ],
});
```

- `configSchema` 可选。省略时 OpenClaw 使用严格空对象 schema，生成的 manifest 仍包含 `configSchema`。
- `execute` 返回普通字符串或 JSON 可序列化值。helper 将其包装为带 `details` 的文本工具结果。
- 工具名是静态的。`openclaw plugins build` 从声明的工具派生 `contracts.tools`，作者无需手动重复名称。
- 运行时加载仍然严格。已安装插件仍需要 `openclaw.plugin.json` 和 `package.json` 的 `openclaw.extensions`；OpenClaw 不执行插件代码来推断缺失的 manifest 数据。

## `definePluginEntry`

**导入：** `openclaw/plugin-sdk/plugin-entry`

用于 provider 插件、高级工具插件、钩子插件，以及任何**不是**消息 channel 的插件。

```typescript

export default definePluginEntry({
  id: "my-plugin",
  name: "My Plugin",
  description: "Short summary",
  register(api) {
    api.registerProvider({
      /* ... */
    });
    api.registerTool({
      /* ... */
    });
  },
});
```

| 字段           | 类型                                                             | 必需 | 默认值              |
| -------------- | ---------------------------------------------------------------- | ---- | ------------------- |
| `id`           | `string`                                                         | 是   | -                   |
| `name`         | `string`                                                         | 是   | -                   |
| `description`  | `string`                                                         | 是   | -                   |
| `kind`         | `string`                                                         | 否   | -                   |
| `configSchema` | `OpenClawPluginConfigSchema \| () => OpenClawPluginConfigSchema` | 否   | 空对象 schema       |
| `register`     | `(api: OpenClawPluginApi) => void`                               | 是   | -                   |

- `id` 必须与 `openclaw.plugin.json` manifest 匹配。
- `kind` 用于独占槽位：`"memory"` 或 `"context-engine"`。
- `configSchema` 可以是函数，用于延迟求值。
- OpenClaw 在首次访问时解析并缓存该 schema，所以昂贵的 schema 构建器只运行一次。

## `defineChannelPluginEntry`

**导入：** `openclaw/plugin-sdk/channel-core`

用 channel 专用接线包装 `definePluginEntry`。自动调用 `api.registerChannel({ plugin })`，暴露可选的根帮助 CLI 元数据接缝，并在注册模式上门控 `registerFull`。

```typescript

export default defineChannelPluginEntry({
  id: "my-channel",
  name: "My Channel",
  description: "Short summary",
  plugin: myChannelPlugin,
  setRuntime: setMyRuntime,
  registerCliMetadata(api) {
    api.registerCli(/* ... */);
  },
  registerFull(api) {
    api.registerGatewayMethod(/* ... */);
  },
});
```

| 字段                    | 类型                                                             | 必需 | 默认值              |
| ----------------------- | ---------------------------------------------------------------- | ---- | ------------------- |
| `id`                    | `string`                                                         | 是   | -                   |
| `name`                  | `string`                                                         | 是   | -                   |
| `description`           | `string`                                                         | 是   | -                   |
| `plugin`                | `ChannelPlugin`                                                  | 是   | -                   |
| `configSchema`          | `OpenClawPluginConfigSchema \| () => OpenClawPluginConfigSchema` | 否   | 空对象 schema       |
| `setRuntime`            | `(runtime: PluginRuntime) => void`                               | 否   | -                   |
| `registerCliMetadata`   | `(api: OpenClawPluginApi) => void`                               | 否   | -                   |
| `registerFull`          | `(api: OpenClawPluginApi) => void`                               | 否   | -                   |

- `setRuntime` 在注册期间调用，这样可以存储运行时引用（通常通过 `createPluginRuntimeStore`）。CLI 元数据捕获期间跳过。
- `registerCliMetadata` 在 `api.registrationMode === "cli-metadata"`、`api.registrationMode === "discovery"` 和 `api.registrationMode === "full"` 时运行。用作 channel 持有的 CLI 描述符的标准位置，这样根帮助保持非激活，发现快照包含静态命令元数据，正常 CLI 命令注册仍与完整插件加载兼容。
- 发现注册是非激活的，但不是免导入的。OpenClaw 可能求值受信插件入口和 channel 插件模块来构建快照，所以保持顶层导入无副作用，将套接字、客户端、worker 和服务放在仅 `"full"` 路径后面。
- `registerFull` 仅在 `api.registrationMode === "full"` 时运行。设置专用加载期间跳过。
- 与 `definePluginEntry` 一样，`configSchema` 可以是延迟工厂，OpenClaw 在首次访问时缓存已解析的 schema。
- 插件持有的根 CLI 命令优先用 `api.registerCli(..., { descriptors: [...] })`，让命令保持懒加载而不从根 CLI 解析树消失。配对 node 功能命令优先用 `api.registerNodeCliFeature(...)`，让命令落在 `openclaw nodes` 下。其他嵌套插件命令添加 `parentPath` 并在传给注册器的 `program` 对象上注册命令；OpenClaw 在调用插件前将其解析为父命令。channel 插件优先从 `registerCliMetadata(...)` 注册这些描述符，让 `registerFull(...)` 专注于仅运行时工作。
- 如果 `registerFull(...)` 也注册 gateway RPC 方法，保持在插件专用前缀上。保留的核心 admin 命名空间（`config.*`、`exec.approvals.*`、`wizard.*`、`update.*`）始终强制为 `operator.admin`。

## `defineSetupPluginEntry`

**导入：** `openclaw/plugin-sdk/channel-core`

用于轻量级 `setup-entry.ts` 文件。仅返回 `{ plugin }`，无运行时或 CLI 接线。

```typescript

export default defineSetupPluginEntry(myChannelPlugin);
```

OpenClaw 在 channel 被禁用、未配置或启用延迟加载时加载此入口，而不是完整入口。参见 [Setup and Config](/plugins/sdk-setup#setup-entry) 了解何时重要。

实践中将 `defineSetupPluginEntry(...)` 与窄设置 helper 家族配对：

- `openclaw/plugin-sdk/setup-runtime` 用于运行时安全的设置 helper，如 `createSetupTranslator`、导入安全的设置补丁适配器、查找注释输出、`promptResolvedAllowFrom`、`splitSetupEntries` 和委托设置代理
- `openclaw/plugin-sdk/channel-setup` 用于可选安装设置表面
- `openclaw/plugin-sdk/setup-tools` 用于设置/安装 CLI/归档/文档 helper

将重型 SDK、CLI 注册和长生命周期运行时服务保持在完整入口中。

拆分设置和运行时的捆绑工作区 channel 可用 `openclaw/plugin-sdk/channel-entry-contract` 的 `defineBundledChannelSetupEntry(...)`。该契约让设置入口保持设置安全的插件/秘密导出，同时仍暴露运行时设置器：

```typescript

export default defineBundledChannelSetupEntry({
  importMetaUrl: import.meta.url,
  plugin: {
    specifier: "./channel-plugin-api.js",
    exportName: "myChannelPlugin",
  },
  runtime: {
    specifier: "./runtime-api.js",
    exportName: "setMyChannelRuntime",
  },
  registerSetupRuntime(api) {
    api.registerHttpRoute({
      path: "/my-channel/events",
      auth: "plugin",
      handler: async (req, res) => {
        /* 设置安全路由 */
      },
    });
  },
});
```

仅在设置流确实需要轻量级运行时设置器或完整 channel 入口加载前的设置安全 gateway 表面时使用该捆绑契约。`registerSetupRuntime` 仅在 `"setup-runtime"` 加载时运行；保持仅限于配置专用路由或必须在延迟完整激活前存在的方法。

## 注册模式

`api.registrationMode` 告诉插件它是如何被加载的：

| 模式              | 何时                              | 注册什么                                                                                                                |
| ----------------- | --------------------------------- | ----------------------------------------------------------------------------------------------------------------------- |
| `"full"`          | 正常 gateway 启动                 | 所有内容                                                                                                                |
| `"discovery"`     | 只读能力发现                      | channel 注册加静态 CLI 描述符；入口代码可加载，但跳过套接字、worker、客户端和服务                                       |
| `"setup-only"`    | 禁用/未配置的 channel             | 仅 channel 注册                                                                                                         |
| `"setup-runtime"` | 设置流且运行时可用                | channel 注册加完整入口加载前所需的轻量级运行时                                                                          |
| `"cli-metadata"`  | 根帮助 / CLI 元数据捕获           | 仅 CLI 描述符                                                                                                           |

`defineChannelPluginEntry` 自动处理此拆分。如果对 channel 直接使用 `definePluginEntry`，需自行检查模式：

```typescript
register(api) {
  if (
    api.registrationMode === "cli-metadata" ||
    api.registrationMode === "discovery" ||
    api.registrationMode === "full"
  ) {
    api.registerCli(/* ... */);
    if (api.registrationMode === "cli-metadata") return;
  }

  api.registerChannel({ plugin: myPlugin });
  if (api.registrationMode !== "full") return;

  // 重型仅运行时注册
  api.registerService(/* ... */);
}
```

发现模式构建非激活注册表快照。它仍可能求值插件入口和 channel 插件对象，以便 OpenClaw 注册 channel 能力和静态 CLI 描述符。将发现中的模块求值视为受信但轻量。顶层不要有网络客户端、子进程、监听器、数据库连接、后台 worker、凭证读取或其他活跃运行时副作用。

将 `"setup-runtime"` 视为设置专用启动表面必须存在而不重新进入完整捆绑 channel 运行时的窗口。适合的是 channel 注册、设置安全 HTTP 路由、设置安全 gateway 方法和委托设置 helper。重型后台服务、CLI 注册器和 provider/客户端 SDK 引导仍属于 `"full"`。

CLI 注册器具体来说：

- 注册器持有一个或多个根命令且想让 OpenClaw 在首次调用时懒加载真实 CLI 模块时用 `descriptors`
- 确保这些描述符覆盖注册器暴露的每个顶级命令根
- 描述符命令名保持为字母、数字、连字符和下划线，以字母或数字开头；OpenClaw 拒绝该形态之外的描述符名，并在渲染帮助前剥离描述中的终端控制序列
- 仅在需要急切兼容路径时单独使用 `commands`

## 插件形态

OpenClaw 按注册行为对已加载插件分类：

| 形态                  | 描述                                       |
| --------------------- | ------------------------------------------ |
| **plain-capability**  | 一种能力类型（如仅 provider）              |
| **hybrid-capability** | 多种能力类型（如 provider + 语音）         |
| **hook-only**         | 仅钩子，无能力                             |
| **non-capability**    | 工具/命令/服务但无能力                     |

用 `openclaw plugins inspect <id>` 查看插件形态。

## 相关

- [SDK Overview](/plugins/sdk-overview) - 注册 API 和子路径参考
- [Runtime Helpers](/plugins/sdk-runtime) - `api.runtime` 和 `createPluginRuntimeStore`
- [Setup and Config](/plugins/sdk-setup) - manifest、设置入口、延迟加载
- [Channel Plugins](/plugins/sdk-channel-plugins) - 构建 `ChannelPlugin` 对象
- [Provider Plugins](/plugins/sdk-provider-plugins) - provider 注册和钩子
