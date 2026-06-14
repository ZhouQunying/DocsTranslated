# SDK: 迁移指南

## 架构精读

> 跳过不影响阅读翻译正文。

### 从 barrel 导入到 subpath 导入——为什么这是 API 演进的必经之路？

旧版 OpenClaw 插件 SDK 有两个宽泛的导入表面：`compat` 重导出几十个辅助函数，`infra-runtime` 混合了系统事件、心跳状态、交付队列、fetch 辅助。问题是导入一个辅助就加载几十个无关模块，启动慢、循环依赖、API 表面不清晰。新版 SDK 把每个导入路径（`openclaw/plugin-sdk/<subpath>`）变成小的、自包含的模块。这就像前端生态的演进：从 `import _ from 'lodash'`（加载 700KB）到 `import get from 'lodash/get'`（按需加载），再到 `date-fns` 取代 `moment`（每个函数独立文件）。本质是"最小知识原则"在包级别的体现——消费者只看到自己需要的接口，不意外依赖不相关的实现。

第二个设计：6 步兼容性策略。OpenClaw 不在引入替代的同一变更中移除或重新解释已记录的插件行为。破坏性契约变更必须先经过兼容适配器、诊断、文档和弃用窗口。六步流程：先添加新契约并通过兼容适配器保持旧行为。然后发出命名旧路径和替代品的诊断或警告。接着测试覆盖两条路径并记录弃用和迁移路径。最后仅在宣布的迁移窗口后移除，通常是主版本。就像 Java 的 `@Deprecated` 注解——标记但不删除，给下游时间迁移。区别是 OpenClaw 的流程更严格：不仅标记，还要测试覆盖、诊断通知、文档说明全到位。

第三个边界：Talk 会话控制器的统一。实时语音、电话、会议和浏览器 Talk 代码正在从表面本地的回合簿记迁移到共享的 Talk 会话控制器。控制器持有公共 Talk 事件信封、活跃回合状态、捕获状态、输出音频状态、近期事件历史和过期回合拒绝。Provider 插件继续持有厂商特定的实时会话；表面插件继续持有捕获、回放、电话和会议怪癖。这就像从分散的状态管理迁移到集中的 store——Redux 之前每个组件自己管状态，Redux 之后状态集中、可预测、可调试。

---

OpenClaw 已从宽泛的向后兼容层迁移到现代插件架构，具有聚焦的、有文档的导入。如果你的插件在新架构之前构建，本指南帮助你迁移。

## 变更内容

旧插件系统提供两个宽泛的导入表面，让插件从单一入口导入任何需要的东西：

- **`openclaw/plugin-sdk/compat`** — 单一导入重导出几十个辅助函数
- **`openclaw/plugin-sdk/infra-runtime`** — 宽泛的运行时辅助桶，混合了系统事件、心跳状态、交付队列、fetch/代理辅助、文件辅助、审批类型和无关工具
- **`openclaw/plugin-sdk/config-runtime`** — 宽泛的配置兼容性桶
- **`openclaw/extension-api`** — 让插件直接访问宿主侧辅助（如嵌入式 agent runner）的桥接

这些宽泛的导入表面现在**已弃用**。它们仍在运行时工作，但新插件不得使用它们，现有插件应在下一个主版本移除前迁移。

OpenClaw 不在引入替代的同一变更中移除或重新解释已记录的插件行为。破坏性契约变更必须先经过兼容适配器、诊断、文档和弃用窗口。这适用于 SDK 导入、manifest 字段、设置 API、钩子和运行时注册行为。

## 变更原因

旧方法导致问题：

- **启动慢** — 导入一个辅助加载几十个无关模块
- **循环依赖** — 宽泛重导出容易创建导入循环
- **API 表面不清晰** — 无法区分哪些导出是稳定的、哪些是内部的

现代插件 SDK 解决了这个问题：每个导入路径（`openclaw/plugin-sdk/<subpath>`）是一个小的、自包含的模块，有明确的目的和有文档的契约。

## 兼容性策略

对外部插件，兼容性工作按以下顺序进行：

1. 添加新契约
2. 通过兼容适配器保持旧行为
3. 发出命名旧路径和替代品的诊断或警告
4. 在测试中覆盖两条路径
5. 记录弃用和迁移路径
6. 仅在宣布的迁移窗口后移除，通常是主版本

如果 manifest 字段仍被接受，插件作者可继续使用它直到文档和诊断说明否则。新代码应优先使用有文档的替代品，但现有插件不应在普通次版本发布中中断。

## 如何迁移

### 迁移运行时配置加载/写入辅助

捆绑插件应停止直接调用 `api.runtime.config.loadConfig()` 和 `api.runtime.config.writeConfigFile(...)`。优先使用已传入活跃调用路径的配置。长生命周期处理器可使用 `api.runtime.config.current()` 获取当前进程快照。长生命周期 agent 工具应在 `execute` 内使用工具上下文的 `ctx.getRuntimeConfig()`，以便在配置写入前创建的工具仍能看到刷新的运行时配置。

配置写入必须通过事务性辅助并选择写入后策略：

```typescript
await api.runtime.config.mutateConfigFile({
  afterWrite: { mode: "auto" },
  mutate(draft) {
    draft.plugins ??= {};
  },
});
```

新插件代码还应避免导入宽泛的 `openclaw/plugin-sdk/config-runtime` 兼容性桶。使用匹配工作的窄 SDK subpath：

| 需求 | 导入 |
| --- | --- |
| 配置类型如 `OpenClawConfig` | `openclaw/plugin-sdk/config-contracts` |
| 已加载配置断言和插件入口配置查找 | `openclaw/plugin-sdk/plugin-config-runtime` |
| 当前运行时快照读取 | `openclaw/plugin-sdk/runtime-config-snapshot` |
| 配置写入 | `openclaw/plugin-sdk/config-mutation` |
| 会话存储辅助 | `openclaw/plugin-sdk/session-store-runtime` |

### 查找弃用导入

搜索插件中来自任一弃用表面的导入：

```bash
grep -r "plugin-sdk/compat" my-plugin/
grep -r "plugin-sdk/infra-runtime" my-plugin/
grep -r "plugin-sdk/config-runtime" my-plugin/
grep -r "openclaw/extension-api" my-plugin/
```

### 替换为聚焦导入

旧表面的每个导出映射到特定的现代导入路径。每个窄 subpath 有明确的契约和目的，避免加载无关模块。

## 相关

- [Building plugins](/plugins/building-plugins)
- [Plugin SDK setup](/plugins/sdk-setup)
- [Plugin SDK subpaths](/plugins/sdk-subpaths)
