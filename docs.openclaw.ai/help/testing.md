# Testing

## 架构精读

> 跳过不影响阅读翻译正文。

### 分层测试策略——为什么"逐步增加真实性"？

OpenClaw 采用"逐步增加真实性"（increasing realism）的分层测试策略：

1. **单元/集成测试**：`pnpm test`，纯逻辑 + 进程内集成，无需外部 API 密钥（快速稳定）
2. **稳定性测试**：`pnpm test:stability:gateway`，用合成数据压测本地网关（验证内存/诊断记录器有界）
3. **端到端测试**：`pnpm test:e2e`，多实例网关网络、WebSocket 协议、Playwright 模拟浏览器 UI
4. **实时测试**：`pnpm test:live`，与真实 AI 模型/提供商交互（因成本和网络依赖，排除在标准 CI 外）

这跟测试金字塔是一个思路——单元测试（基础，快速）→ 集成测试（中等）→ 端到端测试（顶层，慢但真实）。分层让"快速反馈"和"真实验证"都成为可能，避免"所有测试都慢"或"所有测试都不真实"的极端。

### 运行方式——为什么提供多种？

文档提供多种测试运行方式：

- **标准门禁**：`pnpm build && pnpm check && pnpm check:test-types && pnpm test`（推送前完整验证）
- **本地迭代**：`pnpm test:watch`（持续反馈）、`pnpm test:max`（高 worker 上限，适合强机器）
- **定向运行**：传文件路径或 `pnpm test:changed`（仅运行最近修改的文件）
- **Docker 运行器**：`pnpm test:docker:live-models`（隔离 Linux 容器，绑定挂载本地认证目录，不修改宿主环境）

这跟 CI/CD 的"快速检查 → 完整测试 → 生产部署"是一个思路——开发时用 `watch`（快速反馈），提交前用"标准门禁"（完整验证），CI 用 Docker（隔离环境）。多种方式让"开发速度"和"测试完整性"都得到保障。

---

Tiered testing strategy with "increasing realism": unit/integration (`pnpm test`, pure logic, no API keys, fast CI), stability (`pnpm test:stability:gateway`, synthetic data stress test, bounded memory/diagnostics), end-to-end (`pnpm test:e2e`, multi-instance gateway, WebSocket protocols, Playwright browser UI), live (`pnpm test:live`, real AI models/providers, excluded from standard CI due to cost/network). Run methods: standard gate (`pnpm build && check && test`), local iteration (`test:watch`, `test:max`), targeted (`test:changed`), Docker runners (`test:docker:live-models`, isolated containers with bind-mounted auth).

分层测试策略，"逐步增加真实性"。单元/集成：`pnpm test`，纯逻辑，无需 API 密钥，快速 CI。稳定性：`pnpm test:stability:gateway`，合成数据压测，内存/诊断有界。

端到端：`pnpm test:e2e`，多实例网关，WebSocket 协议，Playwright 浏览器 UI。实时：`pnpm test:live`，真实 AI 模型/提供商，因成本/网络排除在标准 CI 外。

运行方式：标准门禁（`pnpm build && check && test`）、本地迭代（`test:watch`、`test:max`）、定向（`test:changed`）、Docker 运行器（`test:docker:live-models`，隔离容器绑定挂载认证）。

架构精读：分层让"快速反馈"和"真实验证"都成为可能。多种方式让"开发速度"和"测试完整性"都得到保障。Docker 运行器确保隔离环境，不修改宿主。
