# Testing: Live Suites

## 架构精读

> 跳过不影响阅读翻译正文。

### 实时测试——为什么需要"真实网络"测试？

实时套件是网络依赖的集成测试，验证真实世界功能：

- **模型矩阵测试**：两层——直接模型完成（绕过网关验证提供商 API）+ 网关冒烟测试（验证完整流水线：会话、历史、工具、沙箱策略）
- **CLI 后端验证**：测试网关与本地 CLI 工具（Claude、Gemini）的集成，验证文本轮次、图像分类、MCP 工具调用、会话恢复（不修改默认配置）
- **ACP 绑定冒烟测试**：验证与实时 ACP 智能体的会话绑定流程，确认后续消息落在绑定的会话转录中

这跟集成测试 vs 端到端测试是一个思路——集成测试验证"模块间交互"，端到端测试验证"用户可见的完整流程"。实时测试是"端到端测试"的极端版本，用真实网络和提供商验证"生产环境行为"。

### 媒体提供商覆盖——为什么单独测试？

实时套件全面测试媒体生成能力：

- **图像生成**：跨提供商（OpenAI、Google、MiniMax 等）
- **音乐生成**：通过 Google 和 MiniMax，支持生成和编辑模式
- **视频生成**：支持文本转视频和转换模式，跨多个提供商

这跟微服务的"每个服务独立测试"是一个思路——每个提供商的 API 行为可能不同（如 OpenAI 的 DALL-E vs Google 的 Imagen），需要独立验证。单独测试让"提供商特定问题"快速定位，避免"一个提供商故障影响所有测试"。

### 凭证解析——为什么强调"与 CLI 一致"？

实时测试发现凭证的方式与 CLI 完全相同：从按智能体的认证配置、配置文件、环境变量读取。文档强调"如果 CLI 能用，实时测试应该找到相同的密钥"。

这跟"测试环境与生产环境一致"是一个思路——如果测试用不同的凭证解析逻辑，测试通过不代表生产能用。"与 CLI 一致"确保"测试通过的配置"在"实际使用时"也能工作，避免"测试-生产差异"。

---

Live Suites: network-dependent integration tests validating real-world functionality. Model matrix testing (two layers: direct model completion bypassing gateway + gateway smoke tests validating full pipeline with sessions/history/tools/sandbox policies), CLI backend validation (gateway integration with local CLI tools like Claude/Gemini, testing text turns/image classification/MCP tool calls/session resumption), ACP bind smoke tests (conversation-binding flows with live ACP agents). Media provider coverage: image generation (OpenAI/Google/MiniMax), music generation (Google/MiniMax with generation/editing modes), video generation (text-to-video and transform modes). Credential resolution identical to CLI (per-agent auth profiles, config files, env vars). Real-world scenarios: tool calling, vision capabilities, aggregator support via OpenRouter, Guardian-reviewed security probes.

实时套件：网络依赖的集成测试，验证真实世界功能。模型矩阵测试（两层：直接模型完成绕过网关 + 网关冒烟测试验证完整流水线包括会话/历史/工具/沙箱策略）。CLI 后端验证（网关与本地 CLI 工具如 Claude/Gemini 的集成，测试文本轮次/图像分类/MCP 工具调用/会话恢复）。ACP 绑定冒烟测试（与实时 ACP 智能体的会话绑定流程）。

媒体提供商覆盖：图像生成（OpenAI/Google/MiniMax）、音乐生成（Google/MiniMax 支持生成/编辑模式）、视频生成（文本转视频和转换模式）。凭证解析与 CLI 一致（按智能体认证配置、配置文件、环境变量）。真实场景：工具调用、视觉能力、通过 OpenRouter 的聚合器支持、Guardian 审查的安全探测。

架构精读：实时测试是"端到端测试"的极端版本，用真实网络和提供商验证"生产环境行为"。单独测试让"提供商特定问题"快速定位。"与 CLI 一致"确保测试通过的配置在实际使用时也能工作。
