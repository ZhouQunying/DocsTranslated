# 工具插件

## 架构精读

> 跳过不影响阅读翻译正文。

### 为什么有 defineToolPlugin 而不是直接用 definePluginEntry？

工具插件是最简单的插件类型——只添加 agent 可调用工具，不添加 channel、provider、钩子或服务。如果用 `definePluginEntry` 写工具插件，需要手动调用 `api.registerTool`、手动维护 manifest 元数据、手动声明 `contracts.tools`。`defineToolPlugin` 把这些都自动化了：声明工具列表，构建时自动生成 manifest，运行时自动注册。就像 React 的 `useState` vs `useReducer`——简单场景用 `useState`，复杂场景才升级到 `useReducer`。好处是工具插件代码量减半，坏处是只能用固定工具名，动态工具必须用 `definePluginEntry`。

第二个关键设计：构建时生成 manifest。OpenClaw 在加载插件前需要知道插件提供哪些工具（`contracts.tools` 数组）。传统做法是运行时注册后读取，但这需要加载每个已安装插件的运行时——启动慢。`defineToolPlugin` 暴露静态元数据，`openclaw plugins build` 在构建时提取并写入 `openclaw.plugin.json`。Gateway 启动时只读 manifest 就能知道工具列表，不加载插件代码。就像 TypeScript 的 `tsconfig.json`——编译配置在构建时确定，不依赖运行时执行。

第三个边界：工具名是稳定 API。模型调用工具时用名字，所以工具名一旦发布就不能改（除非接受 breaking change）。可选工具（`optional: true`）需要用户显式启用才能被模型看到，这是安全控制——敏感工具默认不可见。就像 Linux 的 setuid 位——默认关闭，需要显式启用才能获得特权。

---

工具插件向 OpenClaw 添加 agent 可调用工具，不添加 channel、模型 provider、钩子、服务或设置后端。当插件持有固定工具列表且想让 OpenClaw 生成 manifest 元数据（让这些工具无需加载运行时代码即可被发现）时用 `defineToolPlugin`。

推荐流程：

1. 用 `openclaw plugins init` 搭建包脚手架
2. 用 `defineToolPlugin` 编写工具
3. 构建 JavaScript
4. 用 `openclaw plugins build` 生成 `openclaw.plugin.json` 和 `package.json` 元数据
5. 在发布或安装前验证生成的元数据

provider、channel、钩子、服务或混合能力插件从 [Building plugins](/plugins/building-plugins)、[Channel Plugins](/plugins/sdk-channel-plugins) 或 [Provider Plugins](/plugins/sdk-provider-plugins) 开始。

## 要求

- Node >= 22
- TypeScript ESM 包输出
- `typebox` 用于配置和工具参数 schema
- `openclaw >=2026.5.17`，首个导出 `openclaw/plugin-sdk/tool-plugin` 的 OpenClaw 版本
- 可发布 `dist/`、`openclaw.plugin.json` 和 `package.json` 的包根

生成的插件在运行时导入 `typebox`，所以保持 `typebox` 在 `dependencies` 中，不仅是 `devDependencies`。

## 快速入门

创建新插件包：

```bash
openclaw plugins init stock-quotes --name "Stock Quotes"
cd stock-quotes
npm install
npm run plugin:build
npm run plugin:validate
npm test
```

脚手架创建：

- `src/index.ts`：带 `echo` 工具的 `defineToolPlugin` 入口
- `src/index.test.ts`：小型元数据测试
- `tsconfig.json`：NodeNext TypeScript 输出到 `dist/`
- `package.json`：脚本、运行时依赖和 `openclaw.extensions: ["./dist/index.js"]`
- `openclaw.plugin.json`：初始工具的生成 manifest 元数据

预期验证输出：

```text
Plugin stock-quotes is valid.
```

## 编写工具

`defineToolPlugin` 接受插件身份、可选配置 schema 和静态工具列表。参数和配置类型从 TypeBox schema 推断。

```typescript

export default defineToolPlugin({
  id: "stock-quotes",
  name: "Stock Quotes",
  description: "Fetch stock quote snapshots.",
  configSchema: Type.Object({
    apiKey: Type.Optional(Type.String({ description: "Quote API key." })),
    baseUrl: Type.Optional(Type.String({ description: "Quote API base URL." })),
  }),
  tools: (tool) => [
    tool({
      name: "stock_quote",
      label: "Stock Quote",
      description: "Fetch a stock quote snapshot.",
      parameters: Type.Object({
        symbol: Type.String({ description: "Ticker symbol, for example OPEN." }),
      }),
      async execute({ symbol }, config, context) {
        context.signal?.throwIfAborted();
        return {
          symbol: symbol.toUpperCase(),
          configured: Boolean(config.apiKey),
          baseUrl: config.baseUrl ?? "https://api.example.com",
        };
      },
    }),
  ],
});
```

工具名是稳定 API。选择唯一、小写且足够具体以避免与核心工具或其他插件冲突的名字。

## 可选和工厂工具

当用户应在工具发送给模型前显式将其加入允许列表时设置 `optional: true`：

```typescript
tool({
  name: "workflow_run",
  description: "Run an external workflow.",
  parameters: Type.Object({ goal: Type.String() }),
  optional: true,
  execute: ({ goal }) => ({ queued: true, goal }),
});
```

`openclaw plugins build` 写入匹配的 `toolMetadata.<tool>.optional` manifest 条目，这样 OpenClaw 无需加载插件运行时代码即可发现该工具。

当工具在创建前需要运行时工具上下文时用 `factory`。工厂保持元数据静态，同时让工具为特定运行 opt out、检查沙箱状态或绑定运行时 helper。

```typescript
tool({
  name: "local_workflow",
  description: "Run a local workflow outside sandboxed sessions.",
  parameters: Type.Object({ goal: Type.String() }),
  optional: true,
  factory({ api, toolContext }) {
    if (toolContext.sandboxed) {
      return null;
    }
    return createLocalWorkflowTool(api);
  },
});
```

工厂仍用于固定工具名。当插件动态计算工具名或将工具与钩子、服务、provider、命令或其他运行时表面结合时直接用 `definePluginEntry`。

## 返回值

`defineToolPlugin` 将普通返回值包装为 OpenClaw 工具结果格式：

- 模型应看到该确切文本时返回字符串
- 想让模型看到格式化 JSON 且 OpenClaw 在 `details` 中保留原始值时返回 JSON 兼容值

```typescript
tool({
  name: "echo_text",
  description: "Echo input text.",
  parameters: Type.Object({
    input: Type.String(),
  }),
  execute: ({ input }) => input,
});
```

```typescript
tool({
  name: "echo_json",
  description: "Echo input as structured JSON.",
  parameters: Type.Object({
    input: Type.String(),
  }),
  execute: ({ input }) => ({ input, length: input.length }),
});
```

需要返回自定义 `AgentToolResult` 或复用现有 `api.registerTool` 实现时用工厂工具。需要完全动态工具或混合插件能力时用 `definePluginEntry` 代替 `defineToolPlugin`。

## 配置

`configSchema` 可选。省略时 OpenClaw 使用严格空对象 schema，生成的 manifest 仍包含 `configSchema`。

```typescript
export default defineToolPlugin({
  id: "no-config-tools",
  name: "No Config Tools",
  description: "Adds tools that do not need configuration.",
  tools: () => [],
});
```

包含 `configSchema` 时，第二个 `execute` 参数从 schema 类型化：

```typescript
const configSchema = Type.Object({
  apiKey: Type.String(),
});

export default defineToolPlugin({
  id: "configured-tools",
  name: "Configured Tools",
  description: "Adds configured tools.",
  configSchema,
  tools: (tool) => [
    tool({
      name: "configured_ping",
      description: "Check whether configuration is available.",
      parameters: Type.Object({}),
      execute: (_params, config) => ({ hasKey: config.apiKey.length > 0 }),
    }),
  ],
});
```

OpenClaw 从 Gateway 配置中的插件入口读取插件配置。不要在源码或文档示例中硬编码密钥。根据插件安全模型使用配置、环境变量或 SecretRef。

## 生成元数据

OpenClaw 从冷元数据发现已安装插件。它必须能在导入插件运行时代码前读取插件 manifest。`defineToolPlugin` 因此暴露静态元数据，`openclaw plugins build` 将该元数据写入包。

更改插件 id、name、description、配置 schema、激活或工具名后运行生成器：

```bash
npm run build
openclaw plugins build --entry ./dist/index.js
```

单工具插件的生成 manifest 如下：

```json
{
  "id": "stock-quotes",
  "name": "Stock Quotes",
  "description": "Fetch stock quote snapshots.",
  "version": "0.1.0",
  "configSchema": {
    "type": "object",
    "additionalProperties": false,
    "properties": {}
  },
  "activation": {
    "onStartup": true
  },
  "contracts": {
    "tools": ["stock_quote"]
  }
}
```

`contracts.tools` 是重要的发现契约。它告诉 OpenClaw 哪个插件持有每个工具，不需要加载每个已安装插件的运行时。如果 manifest 过期，工具可能从发现中丢失或错误插件可能被归咎于注册错误。

## 包元数据

对于简单工具插件工作流，`openclaw plugins build` 将 `package.json` 对齐到选定的单运行时入口：

```json
{
  "type": "module",
  "files": ["dist", "openclaw.plugin.json", "README.md"],
  "dependencies": {
    "typebox": "^1.1.38"
  },
  "peerDependencies": {
    "openclaw": ">=2026.5.17"
  },
  "openclaw": {
    "extensions": ["./dist/index.js"]
  }
}
```

已安装包使用已构建 JavaScript 如 `./dist/index.js`。源入口在工作区开发中有用，但发布的包不应依赖 TypeScript 运行时加载。

## 在 CI 中验证

用 `plugins build --check` 在生成元数据过期时让 CI 失败，不重写文件：

```bash
npm run build
openclaw plugins build --entry ./dist/index.js --check
openclaw plugins validate --entry ./dist/index.js
npm test
```

`plugins validate` 检查：

- `openclaw.plugin.json` 存在并通过正常 manifest 加载器
- 当前入口导出 `defineToolPlugin` 元数据
- 生成的 manifest 字段与入口元数据匹配
- `contracts.tools` 与声明的工具名匹配
- `package.json` 将 `openclaw.extensions` 指向选定的运行时入口

## 本地安装和检查

从单独的 OpenClaw 检出或已安装 CLI 安装包路径：

```bash
openclaw plugins install ./stock-quotes
openclaw plugins inspect stock-quotes --runtime
```

打包冒烟测试时，先打包然后安装 tarball：

```bash
npm pack
openclaw plugins install npm-pack:./openclaw-plugin-stock-quotes-0.1.0.tgz
openclaw plugins inspect stock-quotes --runtime --json
```

安装后，启动或重启 Gateway 并要求 agent 使用该工具。如果调试工具可见性，在更改代码前检查插件运行时和有效工具目录。

## 发布

包准备好后通过 ClawHub 发布：

```bash
clawhub package publish your-org/stock-quotes --dry-run
clawhub package publish your-org/stock-quotes
```

用显式 ClawHub 定位器安装：

```bash
openclaw plugins install clawhub:your-org/stock-quotes
```

裸 npm 包 spec 在启动切换期间仍受支持，但 ClawHub 是 OpenClaw 插件的首选发现和分发表面。

## 疑难排查

### `plugin entry not found: ./dist/index.js`

选定的入口文件不存在。运行 `npm run build`，然后重新运行 `openclaw plugins build --entry ./dist/index.js` 或 `openclaw plugins validate --entry ./dist/index.js`。

### `plugin entry does not expose defineToolPlugin metadata`

入口未导出由 `defineToolPlugin` 创建的值。检查模块默认导出是 `defineToolPlugin(...)` 结果，或用 `--entry` 传递正确入口。

### `openclaw.plugin.json generated metadata is stale`

manifest 不再匹配入口元数据。运行：

```bash
npm run build
openclaw plugins build --entry ./dist/index.js
```

提交 `openclaw.plugin.json` 和 `package.json` 变更。

### `package.json openclaw.extensions must include ./dist/index.js`

包元数据指向不同的运行时入口。运行 `openclaw plugins build --entry ./dist/index.js`，让生成器将包元数据对齐到你打算发布的入口。

### `Cannot find package 'typebox'`

已构建插件在运行时导入 `typebox`。保持 `typebox` 在 `dependencies` 中，重新安装包依赖，重新构建并重新运行验证。

### 安装后工具不出现

按顺序检查：

1. `openclaw plugins inspect <plugin-id> --runtime`
2. `openclaw plugins validate --root <plugin-root> --entry ./dist/index.js`
3. `openclaw.plugin.json` 的 `contracts.tools` 包含预期的工具名
4. `package.json` 的 `openclaw.extensions: ["./dist/index.js"]`
5. 安装插件后 Gateway 已重启或重载

## 另见

- [Building plugins](/plugins/building-plugins)
- [Plugin entry points](/plugins/sdk-entrypoints)
- [Plugin SDK subpaths](/plugins/sdk-subpaths)
- [Plugin manifest](/plugins/manifest)
- [Plugins CLI](/cli/plugins)
- [ClawHub publishing](/clawhub/publishing)
