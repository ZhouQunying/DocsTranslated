# 插件架构

## 架构精读

> 跳过不影响阅读翻译正文。

### 为什么用"能力"而不是"插件类型"来分类？

如果 OpenClaw 把插件分成"provider 插件""channel 插件""工具插件"，每个插件就只能做一件事。但 OpenAI 同时提供文本推理、语音合成、图片生成、媒体理解——按类型分就得拆成四个插件，管理碎片化。"能力"是另一种思路：定义一组核心契约（文本推理、嵌入、语音、图片生成……），任何插件可以注册实现一个或多个能力。就像 Java 的 SPI（服务提供者接口）——定义 `Driver` 接口，MySQL 和 PostgreSQL 各自实现。好处是厂商插件可以聚合多个能力（OpenAI 一个插件管所有），channel 消费能力时不关心哪个厂商实现。这就是"plugin = 所有权边界，capability = 核心契约"的本质。

第二个关键设计：四层加载流水线。发现 → 启用/验证 → 运行时加载 → 表面消费。每层职责分明。关键的设计边界是：manifest/配置验证从**元数据**工作，不执行插件代码。这意味着 OpenClaw 无需加载任何运行时即可验证配置、解释缺失/禁用的插件、构建 UI/schema 提示。就像 Spring Boot 的 `@Conditional` 注解——Bean 是否创建在启动时根据条件决定，不需要实例化 Bean 才知道。

第三个边界：能力分层。三层架构：核心能力层持有共享编排、策略、回退、配置合并规则、交付语义和类型化契约。厂商插件层持有厂商特定 API、认证、模型目录、语音合成、图片生成。channel/功能插件层是 Slack/Discord/voice-call 等消费核心能力并在表面上展示的集成。TTS 是个好例子：核心持有回复时 TTS 策略、回退顺序、偏好和 channel 交付；`openai`、`elevenlabs`、`microsoft` 持有合成实现；`voice-call` 消费电话 TTS 运行时辅助。

---

这是 OpenClaw 插件系统的**深度架构参考**。关于实践指南，从以下聚焦页面开始。

## 公共能力模型

能力是 OpenClaw 内部的公共**原生插件**模型。每个原生 OpenClaw 插件注册一个或多个能力类型：

| 能力 | 注册方法 | 示例插件 |
| --- | --- | --- |
| 文本推理 | `api.registerProvider(...)` | `openai`、`anthropic` |
| CLI 推理后端 | `api.registerCliBackend(...)` | `openai`、`anthropic` |
| 嵌入 | `api.registerEmbeddingProvider(...)` | Provider 持有的向量插件 |
| 语音 | `api.registerSpeechProvider(...)` | `elevenlabs`、`microsoft` |
| 实时转录 | `api.registerRealtimeTranscriptionProvider(...)` | `openai` |
| 实时语音 | `api.registerRealtimeVoiceProvider(...)` | `openai` |
| 媒体理解 | `api.registerMediaUnderstandingProvider(...)` | `openai`、`google` |
| 会话记录源 | `api.registerTranscriptSourceProvider(...)` | `discord` |
| 图片生成 | `api.registerImageGenerationProvider(...)` | `openai`、`google`、`fal`、`minimax` |
| 音乐生成 | `api.registerMusicGenerationProvider(...)` | `google`、`minimax` |
| 视频生成 | `api.registerVideoGenerationProvider(...)` | `qwen` |
| 网页获取 | `api.registerWebFetchProvider(...)` | `firecrawl` |
| 网页搜索 | `api.registerWebSearchProvider(...)` | `google` |
| Channel / 消息 | `api.registerChannel(...)` | `msteams`、`matrix` |
| Gateway 发现 | `api.registerGatewayDiscoveryService(...)` | `bonjour` |

注册零个能力但提供钩子、工具、发现服务或后台服务的插件是**遗留纯钩子**插件。该模式仍完全受支持。

### 插件形态

OpenClaw 根据实际注册行为（不仅是静态元数据）将每个加载的插件分类为一种形态：

- **plain-capability**：精确注册一种能力类型（如纯 provider 插件 `mistral`）。
- **hybrid-capability**：注册多种能力类型（如 `openai` 持有文本推理、语音、媒体理解和图片生成）。
- **纯钩子**：仅注册钩子（类型化或自定义），无能力、工具、命令或服务。
- **non-capability**：注册工具、命令、服务或路由但无能力。

用 `openclaw plugins inspect <id>` 查看插件的形态和能力分解。

## 架构概览

OpenClaw 的插件系统有四层：

1. **Manifest + 发现**：OpenClaw 从配置路径、工作区根、全局插件根和捆绑插件找到候选插件。发现首先读取原生 `openclaw.plugin.json` manifest 加上支持的捆绑 manifest。
2. **启用 + 验证**：核心决定发现的插件是启用、禁用、阻止还是被选入排他槽位如记忆。
3. **运行时加载**：原生 OpenClaw 插件在进程内加载并将能力注册到中央注册表。打包的 JavaScript 通过原生 `require` 加载；第三方本地源 TypeScript 是紧急 Jiti 后备。兼容捆绑被归一化为注册表记录，不导入运行时代码。
4. **表面消费**：OpenClaw 其余部分读取注册表以暴露工具、channel、provider 设置、钩子、HTTP 路由、CLI 命令和服务。

重要的设计边界：

- manifest/配置验证应从 **manifest/schema 元数据**工作，不执行插件代码
- 原生能力发现可加载可信插件入口代码以构建非激活的注册表快照
- 原生运行时行为来自插件模块的 `register(api)` 路径，`api.registrationMode === "full"`

这个划分让 OpenClaw 在完整运行时激活前验证配置、解释缺失/禁用的插件和构建 UI/schema 提示。

### 激活规划

激活规划是控制面的一部分。调用者可在加载更广泛的运行时注册表前询问哪些插件与具体命令、provider、channel、路由、agent harness 或能力相关。

规划器保持当前 manifest 行为兼容：

- `activation.*` 字段是显式规划器提示
- `providers`、`channels`、`commandAliases`、`setup.providers`、`contracts.tools` 和钩子保持 manifest 所有权后备
- 仅 id 的规划器 API 保持可用于现有调用者
- plan API 报告原因标签，诊断可区分显式提示和所有权后备

> **警告**
>
> 不要将 `activation` 视为生命周期钩子或 `register(...)` 的替代品。它是用于缩小加载范围的元数据。当所有权字段已描述关系时优先使用它们；仅在需要额外规划器提示时使用 `activation`。

## 能力所有权模型

OpenClaw 将原生插件视为**公司**或**功能**的所有权边界，而不是不相关集成的杂物袋。

这意味着：

- 公司插件通常应持有该公司所有面向 OpenClaw 的表面
- 功能插件通常应持有它引入的完整功能表面
- channel 应消费共享核心能力，而非临时重新实现 provider 行为

- **厂商多能力**：`openai` 持有文本推理、语音、实时语音、媒体理解和图片生成。`google` 持有文本推理加媒体理解、图片生成和网页搜索。
- **厂商单能力**：`elevenlabs` 和 `microsoft` 持有语音；`firecrawl` 持有网页获取。
- **功能插件**：`voice-call` 持有通话传输、工具、CLI、路由和 Twilio 媒体流桥接，但消费共享语音、实时转录和实时语音能力，而非直接导入厂商插件。

关键区分：

- **plugin** = 所有权边界
- **capability** = 多个插件可实现或消费的核心契约

所以如果 OpenClaw 添加新领域如视频，第一个问题不是"哪个 provider 应硬编码视频处理？"第一个问题是"核心视频能力契约是什么？"一旦该契约存在，厂商插件可注册实现它，channel/功能插件可消费它。

如果能力尚不存在，正确做法通常是：

1. **定义能力**：在核心中定义缺失的能力。
2. **通过 SDK 暴露**：以类型化方式通过插件 API/运行时暴露它。
3. **接线消费者**：将 channel/功能对接该能力。
4. **厂商实现**：让厂商插件注册实现。

### 能力分层

用这个心智模型决定代码归属：

- **核心能力层**：共享编排、策略、回退、配置合并规则、交付语义和类型化契约。
- **厂商插件层**：厂商特定 API、认证、模型目录、语音合成、图片生成、未来视频后端、使用端点。
- **Channel/功能插件层**：Slack/Discord/voice-call 等消费核心能力并在表面上展示的集成。

例如，TTS 遵循这个形态：

- 核心持有回复时 TTS 策略、回退顺序、偏好和 channel 交付
- `openai`、`elevenlabs` 和 `microsoft` 持有合成实现
- `voice-call` 消费电话 TTS 运行时辅助

## 契约和执行

插件 API 表面故意类型化并集中在 `OpenClawPluginApi` 中。该契约定义插件可依赖的支持注册点和运行时辅助。

为什么重要：

- 插件作者获得一个稳定的内部标准
- 核心可拒绝重复所有权，如两个插件注册同一 provider id
- 启动可对格式错误的注册浮出可操作的诊断
- 契约测试可执行捆绑插件所有权并防止静默漂移

两层执行：

- **运行时注册执行**：插件注册表在插件加载时验证注册。重复的 provider id、重复的语音 provider id 和格式错误的注册产生插件诊断而非未定义行为。
- **契约测试**：捆绑插件在测试运行期间被捕获到契约注册表中，OpenClaw 可显式断言所有权。

实际效果是 OpenClaw 预先知道哪个插件持有哪个表面。这让核心和 channel 可无缝组合，因为所有权是声明的、类型化的和可测试的，而非隐式的。

### 什么属于契约

好的契约：类型化、小、能力特定、核心持有、多个插件可复用、channel/功能无需知道厂商即可消费。

坏的契约：厂商特定策略隐藏在核心中。绕过注册表的一次性插件逃生舱。channel 代码直接深入厂商实现。不属于 `OpenClawPluginApi` 或 `api.runtime` 的临时运行时对象。

拿不准时，提升抽象级别：先定义能力，然后让插件接入它。

## 执行模型

原生 OpenClaw 插件与 Gateway **同进程**运行。它们不沙箱化。加载的原生插件与核心代码有相同的进程级信任边界。

原生插件含义：插件可注册工具、网络处理器、钩子和服务。插件 bug 可崩溃或不稳定 gateway。恶意原生插件等价于 OpenClaw 进程内的任意代码执行。

兼容捆绑默认更安全，因为 OpenClaw 当前将它们视为元数据/内容包。

对非捆绑插件使用允许列表和显式安装/加载路径。将工作区插件视为开发时代码，不是生产默认。

> **信任注意：** `plugins.allow` 信任**插件 id**，不信任来源出处。具有与捆绑插件相同 id 的工作区插件在该工作区插件被启用/允许时故意遮蔽捆绑副本。这对本地开发、补丁测试和热修复是正常且有用的。捆绑插件信任从源快照解析——加载时的磁盘上的 manifest 和代码——而非从安装元数据。损坏或替换的安装记录不能静默将捆绑插件的信任表面扩展到实际源声明之外。

## 相关

- [Building plugins](/plugins/building-plugins)
- [Plugin manifest](/plugins/manifest)
- [Plugin SDK setup](/plugins/sdk-setup)
