# 添加能力

## 架构精读

> 跳过不影响阅读翻译正文。

### 为什么不直接在 channel 或工具里调用 vendor API？

最快的方式是在需要图片生成的地方直接 `import { openai } from "..."` 然后调用 API。但第二个 vendor 来时你要改所有消费者。正确做法是先定义能力契约（接口 + 注册 + 运行时 helper），再让 vendor 插件实现该契约。就像 JDBC——应用代码调用 `Connection.prepareStatement()`，不关心底层是 MySQL 还是 PostgreSQL。好处是新 vendor 不需要改消费者代码，坏处是需要先写契约层。

规则很简单：插件是所有权边界，能力是共享核心契约。不要从直接接入 vendor 开始，从定义能力开始。

---

> **信息**：这是面向 OpenClaw 核心开发者的**贡献指南**。如果你在构建外部插件，参见 [Building plugins](/plugins/building-plugins)。深层架构参考（能力模型、所有权、加载管道、运行时 helper）见 [Plugin internals](/plugins/architecture)。

当 OpenClaw 需要新的共享域如嵌入、图片生成、视频生成或未来 vendor 支持的功能区域时使用本指南。

规则：

- **插件** = 所有权边界
- **能力** = 共享核心契约

不要从直接接入 vendor 开始。从定义能力开始。

## 何时创建能力

当**所有**以下条件都满足时创建新能力：

1. 多个 vendor 可能合理地实现它
2. Channel、工具或功能插件应消费它而不关心 vendor
3. 核心需要持有回退、策略、配置或投递行为

如果工作是 vendor 专用且尚无共享契约，先停下来定义契约。

## 标准顺序

1. 定义类型化的核心契约
2. 为该契约添加插件注册
3. 添加共享运行时 helper
4. 接入一个真实 vendor 插件作为验证
5. 将功能/channel 消费者迁移到运行时 helper
6. 添加契约测试
7. 记录面向 operator 的配置和所有权模型

## 各归其位

**核心：**

- 请求/响应类型
- Provider 注册表 + 解析
- 回退行为
- 配置 schema，嵌套对象、通配符、数组元素和组合节点上传播的 `title` / `description` 文档元数据
- 运行时 helper 表面

**Vendor 插件：**

- Vendor API 调用
- Vendor auth 处理
- Vendor 专用请求规范化
- 能力实现的注册

**功能/channel 插件：**

- 调用 `api.runtime.*` 或匹配的 `plugin-sdk/*-runtime` helper
- 从不调用 vendor 实现

## Provider 和 harness 接缝

当行为属于模型 provider 契约而非通用 agent 循环时用 **provider 钩子**。示例包括传输选择后的 provider 专用请求参数、auth-profile 偏好、prompt 覆盖和模型/profile 故障转移后的后续回退路由。

当行为属于执行 turn 的运行时时用 **agent harness 钩子**。Harness 可分类成功但不可用的尝试结果（如空、仅推理或仅规划响应），让外部模型回退策略做出重试决策。

保持两个接缝窄：

- 核心持有重试/回退策略
- Provider 插件持有 provider 专用请求/auth/路由提示
- Harness 插件持有运行时专用尝试分类
- 第三方插件返回提示，不直接变更核心状态

## 文件清单

新能力预期涉及这些区域：

- `src/<capability>/types.ts`
- `src/<capability>/...registry/runtime.ts`
- `src/plugins/types.ts`
- `src/plugins/registry.ts`
- `src/plugins/captured-registration.ts`
- `src/plugins/contracts/registry.ts`
- `src/plugins/runtime/types-core.ts`
- `src/plugins/runtime/index.ts`
- `src/plugin-sdk/<capability>.ts`
- `src/plugin-sdk/<capability>-runtime.ts`
- 一个或多个捆绑插件包
- 配置、文档、测试

## 完整示例：图片生成

图片生成遵循标准形态：

1. 核心定义 `ImageGenerationProvider`
2. 核心暴露 `registerImageGenerationProvider(...)`
3. 核心暴露 `runtime.imageGeneration.generate(...)`
4. `openai`、`google`、`fal` 和 `minimax` 插件注册 vendor 支持的实现
5. 未来 vendor 注册相同契约，不改变 channel/工具

配置键有意与视觉分析路由分开：

- `agents.defaults.imageModel` 分析图片
- `agents.defaults.imageGenerationModel` 生成图片

保持分开，让回退和策略保持显式。

## 嵌入 provider

用 `embeddingProviders` 做可复用向量嵌入 provider。该契约有意比记忆更广：工具、搜索、检索、导入器或未来功能插件可消费嵌入而不依赖记忆引擎。

记忆搜索可消费通用 `embeddingProviders`。旧的 `memoryEmbeddingProviders` 契约在已有记忆专用 provider 迁移期间保留为已弃用兼容；新的可复用嵌入 provider 应用 `embeddingProviders`。

## 审查清单

发布新能力前验证：

- 没有 channel/工具直接导入 vendor 代码
- 运行时 helper 是共享路径
- 至少一个契约测试断言捆绑所有权
- 配置文档命名新的模型/配置键
- 插件文档解释所有权边界

如果 PR 跳过能力层并将 vendor 行为硬编码到 channel/工具中，退回并先定义契约。

## 相关

- [Plugin internals](/plugins/architecture) -- 能力模型、所有权、加载管道、运行时 helper
- [Building plugins](/plugins/building-plugins) -- 第一个插件教程
- [SDK overview](/plugins/sdk-overview) -- 导入映射和注册 API 参考
- [Creating skills](/tools/creating-skills) -- 伴侣贡献表面
