# 兼容性

## 架构精读

> 跳过不影响阅读翻译正文。

### 为什么不直接删除旧契约，加个新的就完事？

VSCode 每次升级 API 版本也不直接删旧 API——它给一段迁移窗口期，旧 API 标记为 deprecated，然后才移除。OpenClaw 的兼容性注册表是这个思路的工程化版本：每个旧契约有一条记录，包含状态（active/deprecated/removal-pending/removed）、替代方案、迁移时间线。不仅标记"已弃用"，还追踪警告开始日期、替代方案文档链接、最终移除日期（不超过警告后三个月）。就像 Kubernetes 的 API 弃用策略——GA 版本给 12 个月，beta 给 9 个月，alpha 不给。好处是插件作者有明确的迁移时间线，维护者发版前跑一遍兼容记录就能决定哪些可以移除。

第二个关键：doctor 修复兼容是独立追踪的。运行时兼容路径移除后，doctor 修复可能需要继续存在，因为用户可能从前一个版本直接升级。运行时兼容和 doctor 兼容是两个注册表，独立声明。不能在运行时兼容过期时直接删除对应的 doctor 修复——先验证没有支持的升级路径仍需要它。

---

OpenClaw 通过命名兼容适配器保持旧插件契约接线，然后再移除。这在 SDK、manifest、设置、配置和 agent 运行时契约演进时保护已有捆绑和外部插件。

## 兼容注册表

插件兼容契约在核心注册表 `src/plugins/compat/registry.ts` 中追踪。

每条记录包含：

- 稳定的兼容代码
- 状态：`active`、`deprecated`、`removal-pending` 或 `removed`
- owner：SDK、config、setup、channel、provider、plugin execution、agent runtime 或 core
- 适用时的引入和弃用日期
- 替代指导
- 覆盖旧和新行为的文档、诊断和测试

注册表是维护者规划和未来插件检查器检查的源。如果插件面对行为变更，在添加适配器的同一变更中新增或更新兼容记录。

Doctor 修复和迁移兼容在 `src/commands/doctor/shared/deprecation-compat.ts` 单独追踪。这些记录覆盖旧配置形态、安装账本布局和修复填充，可能在运行时兼容路径移除后仍需保持可用。

发版扫除应检查两个注册表。不要在匹配的运行时或配置兼容记录过期时直接删除 doctor 迁移——先验证是否仍有支持的升级路径需要该修复。发版规划期间也要重新验证每个替代注释，因为 provider 和 channel 移出核心时插件所有权和配置足迹可能变化。

## 插件检查器包

插件检查器应作为独立包/仓库存在，不在核心 OpenClaw 仓库内，基于版本化兼容和 manifest 契约。

首日 CLI 应为：

```sh
openclaw-plugin-inspector ./my-plugin
```

应输出：

- manifest/schema 验证
- 正在检查的契约兼容版本
- 安装/源元数据检查
- 冷路径导入检查
- 弃用和兼容警告

CI 注释中稳定机器可读输出用 `--json`。OpenClaw 核心应暴露检查器可消费的契约和辅助，但不应从主 `openclaw` 包发布检查器二进制。

### 维护者验收通道

对外部检查器验证 OpenClaw 插件包时，用 Crabbox 支持的 Blacksmith Testbox 做可安装包验收通道。从干净的 OpenClaw 检出在包构建后运行：

```sh
pnpm crabbox:run -- --provider blacksmith-testbox --timing-json --shell -- "pnpm install && pnpm build && npm exec --yes @openclaw/plugin-inspector@0.1.0 -- ./extensions/telegram --json"
pnpm crabbox:run -- --provider blacksmith-testbox --timing-json --shell -- "npm exec --yes @openclaw/plugin-inspector@0.1.0 -- ./extensions/discord --json"
pnpm crabbox:run -- --provider blacksmith-testbox --timing-json --shell -- "npm exec --yes @openclaw/plugin-inspector@0.1.0 -- <clawhub-plugin-dir> --json"
```

此通道维护者按需使用，因为它安装外部 npm 包，可能检查仓库外克隆的插件包。本地仓库守卫覆盖 SDK 导出映射、兼容注册表元数据和捆绑扩展导入边界，并追踪已弃用 SDK 导入消耗。Testbox 检查器验证覆盖外部插件作者消费的包。

## 弃用策略

OpenClaw 不应在引入替代方案的同一发版中移除文档化的插件契约。

迁移顺序是：

1. 添加新契约
2. 通过命名兼容适配器保持旧行为接线
3. 插件作者可行动时发出诊断或警告
4. 记录替代方案和时间线
5. 测试新旧两条路径
6. 在公告的迁移窗口期内等待
7. 仅在显式破性发版批准后移除

弃用记录必须包含警告开始日期、替代方案、文档链接和最终移除日期（不超过警告开始后三个月）。不要添加带开放式移除窗口的弃用兼容路径，除非维护者明确决定它是永久兼容并标记为 `active`。

## 当前兼容区域

当前兼容记录包括：

- 遗留广泛 SDK 导入如 `openclaw/plugin-sdk/compat`
- 遗留纯钩子插件形态和 `before_agent_start`
- 遗留 `api.on("deactivate", ...)` 清理钩子名，插件迁移到 `gateway_stop`
- 遗留 `activate(api)` 插件入口点，插件迁移到 `register(api)`
- 遗留 SDK 别名如 `openclaw/extension-api`、`openclaw/plugin-sdk/channel-runtime`、`openclaw/plugin-sdk/command-auth` 状态构建器、`openclaw/plugin-sdk/test-utils`（被聚焦 `openclaw/plugin-sdk/*` 测试子路径替换）和 `ClawdbotConfig` / `OpenClawSchemaType` 类型别名
- 捆绑插件允许列表和启用行为
- 遗留 provider/channel 环境变量 manifest 元数据
- 遗留 provider 插件钩子和类型别名，provider 迁移到显式目录、auth、thinking、replay 和传输钩子
- 遗留运行时别名如 `api.runtime.taskFlow`、`api.runtime.subagent.getSession`、`api.runtime.stt` 和已弃用的 `api.runtime.config.loadConfig()` / `api.runtime.config.writeConfigFile(...)`
- 遗留记忆插件拆分注册，记忆插件迁移到 `registerMemoryCapability`
- 遗留记忆专用嵌入 provider 注册，嵌入 provider 迁移到 `api.registerEmbeddingProvider(...)` 和 `contracts.embeddingProviders`
- 遗留 channel SDK helper：原生消息 schema、提及门控、入站信封格式化和审批能力嵌套
- 遗留 channel 路由键和可比目标 helper 别名，插件迁移到 `openclaw/plugin-sdk/channel-route`
- 激活提示，被 manifest 贡献所有权替换
- `setup-api` 运行时回退，设置描述符迁移到冷 `setup.requiresRuntime: false` 元数据
- provider `discovery` 钩子，provider 目录钩子迁移到 `catalog.run(...)`
- channel `showConfigured` / `showInSetup` 元数据，channel 包迁移到 `openclaw.channel.exposure`
- 遗留运行时策略配置键，doctor 迁移 operator 到 `agentRuntime`
- 生成的捆绑 channel 配置元数据回退，注册表优先的 `channelConfigs` 元数据落地
- 持久化插件注册表禁用和安装迁移环境标志，修复流程迁移 operator 到 `openclaw plugins registry --refresh` 和 `openclaw doctor --fix`
- 遗留插件持有的网页搜索、网页抓取和 x_search 配置路径，doctor 迁移到 `plugins.entries.<plugin>.config`
- 遗留 `plugins.installs` 编写的配置和捆绑插件加载路径别名，安装元数据迁移到状态管理的插件账本

新插件代码应优先使用注册表和具体迁移指南中列出的替代方案。已有插件可继续使用兼容路径，直到文档、诊断和发版说明公告移除窗口。

## 发版说明

发版说明应包含即将到来的插件弃用，带目标日期和迁移文档链接。该警告需要在兼容路径移至 `removal-pending` 或 `removed` 之前发生。