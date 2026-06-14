# 插件架构内部

## 架构精读

> 跳过不影响阅读翻译正文。

### 为什么加载流水线要分八步而不是一个 `loadPlugins()` 搞定？

一个 `loadPlugins()` 看起来简单，但它把发现、验证、加载、注册全揉在一起了。问题是：如果某个插件的路径不安全（world-writable），你想在加载前就拒绝它，而不是加载后才发现。如果配置引用了一个不存在的插件，你想在启动时就告诉用户"这个插件被阻止了，原因是 X"，而不是默默跳过。八步流水线中，每步有明确的输入输出和失败模式。就像编译器的前端、中端、后端分离，调试时能精确定位哪一步出了问题。

第二个关键设计：manifest-first（manifest 优先）。Manifest 是控制面的唯一事实源——标识插件、发现声明的 channel/技能/配置 schema、验证配置、保存廉价的激活和设置描述符而无需加载插件运行时。运行时模块是数据面——注册实际行为如钩子、工具、命令或 provider 流程。这就像 Kubernetes 的声明式 API——你写 YAML 描述想要的状态（控制面），kubelet 负责实际执行（数据面）。控制面可以在数据面不工作时仍然工作（你能 `kubectl get` 一个不存在的 Pod）。

第三个边界：插件缓存边界。OpenClaw 不在时钟窗口后缓存插件发现结果或直接 manifest 注册表数据。安装、manifest 编辑和加载路径变更必须在下次显式元数据读取或快照重建时可见。这就像 DNS 的 TTL 设计——但 OpenClaw 选择了"永不缓存"而非"缓存 N 秒"。好处是简单可靠，坏处是每次启动都要重新读取 manifest。权衡点：manifest 文件解析器可保持有界的文件签名缓存，按路径、inode、大小、时间戳键控。但该缓存仅避免重新解析未变更的字节。它不缓存发现、注册表、所有者或策略答案。

---

关于公共能力模型、插件形态和所有权/执行契约，参见 [Plugin architecture](/plugins/architecture)。此页面是内部机制的参考：加载流水线、注册表、运行时钩子、Gateway HTTP 路由、导入路径和 schema 表。

## 加载流水线

启动时，OpenClaw 大致做这些：

1. 发现候选插件根
2. 读取原生或兼容捆绑 manifest 和包元数据
3. 拒绝不安全候选
4. 归一化插件配置（`plugins.enabled`、`allow`、`deny`、`entries`、`slots`、`load.paths`）
5. 决定每个候选的启用状态
6. 加载已启用的原生模块：已构建捆绑模块使用原生加载器；第三方本地源 TypeScript 使用紧急 Jiti 后备
7. 调用原生 `register(api)` 钩子并将注册收集到插件注册表
8. 将注册表暴露给命令/运行时表面

> **注意**
>
> `activate` 是 `register` 的遗留别名——加载器解析存在的那个（`def.register ?? def.activate`）并在同一点调用。所有捆绑插件使用 `register`；新插件优先使用 `register`。

安全门控在运行时执行**之前**发生。当入口逃逸出插件根、路径是 world-writable 或非捆绑插件的路径所有权看起来可疑时，候选被阻止。

被阻止的候选仍与其插件 id 绑定用于诊断。如果配置仍引用该 id，验证将插件报告为存在但被阻止，并指回路径安全警告，而非将配置条目视为过期。

### Manifest 优先行为

Manifest 是控制面的唯一事实源。OpenClaw 用它来：

- 标识插件
- 发现声明的 channel/技能/配置 schema 或捆绑能力
- 验证 `plugins.entries.<id>.config`
- 增强控制 UI 标签/占位符
- 显示安装/目录元数据
- 保存廉价的激活和设置描述符而无需加载插件运行时

对原生插件，运行时模块是数据面部分。它注册实际行为如钩子、工具、命令或 provider 流程。

可选的 manifest `activation` 和 `setup` 块保持在控制面。它们是激活规划和设置发现的仅元数据描述符；不替换运行时注册、`register(...)` 或 `setupEntry`。

设置发现现在优先使用描述符持有的 id 如 `setup.providers` 和 `setup.cliBackends` 来缩小候选插件，然后才回退到仍需要设置时运行时钩子的插件的 `setup-api`。Provider 设置列表使用 manifest `providerAuthChoices`、描述符派生的设置选择和安装目录元数据，不加载 provider 运行时。显式 `setup.requiresRuntime: false` 是仅描述符的切断点；省略 `requiresRuntime` 保持遗留 setup-api 后备以兼容。

### 插件缓存边界

OpenClaw 不在时钟窗口后缓存插件发现结果或直接 manifest 注册表数据。安装、manifest 编辑和加载路径变更必须在下次显式元数据读取或快照重建时可见。manifest 文件解析器可保持有界的文件签名缓存，按路径、inode、大小和时间戳键控。该缓存仅避免重新解析未变更的字节。它不缓存发现、注册表、所有者或策略答案。

## 注册表模型

插件注册表是加载时构建的运行时数据结构。它持有：

- provider 注册（文本推理、嵌入、语音、图片生成、视频生成、网页获取、网页搜索等）
- channel 注册
- CLI 后端注册
- 钩子注册（类型化和自定义）
- 工具注册
- 命令注册
- HTTP 路由注册
- 服务注册

注册表在启动时构建一次，运行时不修改。这个不可变性让并发读取安全——多个 agent 回合可同时读取注册表而不需要锁。

注册表的消费者是 OpenClaw 的运行时表面：agent 工具查找 provider 注册，消息交付查找 channel 注册，CLI 命令查找命令注册。每个消费者通过类型化的查找 API 访问注册表，而非直接遍历内部结构。

## Provider 运行时钩子

Provider 插件可声明一组运行时钩子，在模型调用的生命周期中执行。这些钩子控制认证解析、模型目录发现、请求构建、响应解析和回退行为。

关键钩子按生命周期顺序：

1. **`resolveAuth`**：在模型选择后、请求构建前解析认证。返回 API 密钥、token 或认证配置。
2. **`catalog.run(...)`**：发现可用模型。在设置 UI 和 `/model` 命令中使用。
3. **`buildRequest`**：将 agent 回合参数构建为 provider 特定的 API 请求。
4. **`parseResponse`**：将 provider API 响应解析为 OpenClaw 标准格式。
5. **`classifyOutcome`**：分类运行结果——成功、可重试失败、永久失败。驱动模型回退策略。
6. **`replay`**：当回合需要重放时（如认证过期后重新认证），重建请求状态。

这个生命周期模式适用于任何 AI 模型 provider 集成。关键是每个钩子有明确的输入输出契约，provider 插件可选择性实现——未实现的钩子使用核心默认行为。

### 钩子顺序和用法

钩子按严格顺序执行。`resolveAuth` 必须在 `buildRequest` 之前，因为请求需要认证凭证。`catalog.run(...)` 独立于其他钩子，仅在需要模型列表时调用。`classifyOutcome` 在 `parseResponse` 之后，因为它需要解析后的响应来决定结果分类。

`replay` 钩子特殊——它不在正常生命周期中执行，仅在需要重放时由核心显式调用。典型场景：认证过期，核心调用 `replay` 重建请求状态，然后重新执行 `buildRequest` → `parseResponse` → `classifyOutcome`。

## 添加新能力

当 OpenClaw 需要支持新领域（如视频理解、3D 生成、代码执行）时，正确的做法是：

1. **在核心定义能力契约**：类型化的接口，定义输入输出和错误语义。
2. **通过 SDK 暴露注册方法**：如 `api.registerVideoUnderstandingProvider(...)`。
3. **接线消费者**：channel 和功能插件通过核心契约消费能力，不直接依赖厂商。
4. **厂商插件注册实现**：各厂商根据自己的 API 实现契约。

### 能力检查清单

- 契约是否类型化且小？
- 契约是否能力特定而非厂商特定？
- 契约是否由核心持有？
- 多个插件是否可实现同一契约？
- channel/功能能否不依赖厂商直接消费？
- 是否有契约测试断言所有权？

### 能力模板

```typescript
// 1. 核心定义契约
interface VideoUnderstandingProvider {
  id: string;
  describeVideo(req: VideoUnderstandingRequest): Promise<VideoUnderstandingResult>;
}

// 2. SDK 暴露注册方法
api.registerVideoUnderstandingProvider(provider: VideoUnderstandingProvider);

// 3. 厂商实现
api.registerVideoUnderstandingProvider({
  id: "exampleai",
  async describeVideo(req) {
    return callExampleAIVideoAPI(req);
  },
});
```

这个模式确保新能力添加是一致的、可测试的、且不会将厂商特定假设烘焙到核心中。

## 相关

- [Plugin architecture](/plugins/architecture)
- [Building plugins](/plugins/building-plugins)
- [Plugin manifest](/plugins/manifest)
