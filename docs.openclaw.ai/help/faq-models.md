# FAQ: models and auth

## 架构精读

> 跳过不影响阅读翻译正文。

### 模型选择——为什么用 `provider/model` 格式？

OpenClaw 用 `provider/model` 格式引用模型（如 `openai/gpt-5.5`、`anthropic/claude-sonnet-4-6`）：

- **默认配置**：`agents.defaults.model.primary`
- **内置别名**：`opus`、`sonnet`、`gpt`、`gpt-mini`、`gemini`、`gemini-flash`
- **动态切换**：`/model` 命令无需重启
- **自定义别名**：`agents.defaults.models.<modelId>.alias`

这跟 Docker 镜像命名是一个思路——`registry/image:tag`（如 `docker.io/nginx:latest`），明确"来源 + 名称 + 版本"。`provider/model` 格式避免"模型名冲突"（不同提供商可能有同名模型）。

### 模型强度策略——为什么"关键任务用最强模型"？

文档建议：

- **关键任务**：用提供商栈中最强的最新模型（准确性优先）
- **日常低风险提示**：用更便宜的选项（成本优化）
- **本地模型**：Ollama 是最易路径（隐私优先）
- **警告**：弱模型/过度量化模型更易受提示注入攻击（安全风险）

这跟数据库选型是一个思路——核心交易用 PostgreSQL（强一致性），日志用 SQLite（轻量），缓存用 Redis（高速）。不同场景用不同强度，避免"一刀切"导致的成本浪费或性能不足。

### 认证双路径——为什么区分 OAuth 和 API 密钥？

两种认证路径：

- **OAuth / CLI 登录**：利用订阅访问（如 Anthropic Pro、OpenAI Plus），固定月费
- **API 密钥**：按令牌计费（pay-per-usage，按使用量付费），按量付费

凭证按智能体存储在 `~/.openclaw/agents/<agentId>/agent/auth-profiles.json`，配置文件 ID 遵循提供商前缀模式（如 `anthropic:default`、`anthropic:<email>`）。可用 `openclaw models auth order set` 控制轮换顺序，用 `openclaw models status --probe` 检查状态。

这跟云服务的计费模式是一个思路——预留实例（固定月费，适合稳定负载）vs 按需实例（按量付费，适合突发流量）。OAuth 适合"重度用户"（月费更划算），API 密钥适合"轻度用户"（按量更灵活）。

### 故障转移两阶段——为什么分层？

故障转移分两阶段：

1. **认证配置轮换**：同一提供商内的多个配置文件轮换（如 `anthropic:default` → `anthropic:backup`）
2. **模型回退**：配置的回退列表中的下一个模型（如 `claude-sonnet` → `gpt-4`）

失败配置文件应用指数退避冷却（exponential backoff cooldowns）。

这跟 DNS 故障转移是一个思路——先尝试主 DNS（同一提供商），失败后切换到备用 DNS（不同提供商）。两阶段让"同一提供商的多账户"和"跨提供商"都成为可能的容错路径。

### 多智能体路由——为什么不共用一个智能体？

可运行独立智能体，各自有不同默认模型（如 MiniMax 处理日常任务、OpenAI 处理复杂任务），通过 `/agent` 切换。每个智能体维护自己的认证存储。

**警告**：不要跨智能体复用 `agentDir`，会导致认证/会话冲突。

这跟微服务的"每个服务独立数据库"是一个思路——避免"共享状态"导致的耦合问题。独立智能体让"模型选择"和"认证隔离"都成为可能，避免"一个智能体故障影响所有"。

---

FAQ covering model selection (`provider/model` format, built-in aliases like `opus`/`sonnet`/`gpt`, `/model` command for dynamic switching), model strength strategy (strongest latest model for critical work, cheaper options for routine tasks, Ollama for local models, weak models vulnerable to prompt injection), authentication dual paths (OAuth/CLI login via subscription, API keys via pay-per-token, credentials stored per-agent in `auth-profiles.json`), model failover (two stages: auth profile rotation within provider → model fallback to next provider, exponential backoff), multi-agent routing (separate agents with different default models, `/agent` to switch, do not reuse `agentDir`).

模型与认证常见问题解答。模型选择：`provider/model` 格式、内置别名如 `opus`/`sonnet`/`gpt`、`/model` 命令动态切换。模型强度策略：关键任务用最强最新模型、日常任务用便宜选项、Ollama 本地模型、弱模型易受提示注入攻击。

认证双路径：OAuth/CLI 登录通过订阅、API 密钥按使用量计费、凭证按智能体存储在 `auth-profiles.json`。模型故障转移：两阶段（同一提供商内认证配置轮换 → 回退到下一提供商的模型、指数退避）。多智能体路由：独立智能体各自有不同默认模型、`/agent` 切换、不要复用 `agentDir`。

架构精读：`provider/model` 格式避免模型名冲突。不同场景用不同强度，避免成本浪费或性能不足。OAuth 适合重度用户，API 密钥适合轻度用户。两阶段故障转移让"同提供商多账户"和"跨提供商"都成为容错路径。
