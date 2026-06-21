# Authentication

## 架构精读

> 跳过不影响阅读翻译正文。

### 双轨认证——为什么 API 密钥和 OAuth 令牌并存？

OpenClaw 认证系统提供两条独立的凭证路径：

- **API 密钥**：静态长期凭证，生成后存入 `.env` 或环境变量，适合持续运行的 服务器
- **OAuth 令牌**：短期可刷新凭证，复用 CLI 登录态（如 Anthropic Claude CLI），适合订阅制账户

这跟 AWS IAM 访问密钥 + SSO 令牌是一个思路——访问密钥是长期凭证（适合 服务器/CI），SSO 令牌短期需刷新（适合个人交互）。

关键设计是**双轨独立**。API 密钥永不过期，OAuth 令牌定期刷新，两条轨道互不依赖。

### 凭证选择的优先级链——为什么需要多份配置文件？

系统支持多份凭证配置文件，选择顺序是确定性的：

1. CLI 标志（命令行指定）
2. 固定会话（`/auth use <profile>`）
3. 按代理配置
4. 默认配置文件

旧 JSON 配置文件自动迁移到 SQLite 存储。

这跟 git 远程仓库的优先级是一个思路——命令行指定的远程仓库优先于配置文件中的默认远程仓库。多份配置文件让一个网关同时对接多个提供商，每个代理用不同的凭证。

### 认证轮换策略——为什么需要多密钥轮转？

当单把密钥触发速率限制时，系统循环使用多个环境变量中的密钥：

`OPENAI_API_KEY` → `OPENAI_API_KEY_2` → ...

覆盖变量优先于默认变量。这跟 DNS 轮询是一个思路——某个端点不可用时自动切换到下一个。轮换是自动的，不需要人工干预。

### 运行时凭证撤销——为什么控制层面删除后运行会立即中止？

控制层面删除凭证后，活跃的运行实例以 `auth-revoked` 停止码（停止代码）立即中止。提供商侧的凭证需要手动失效（OpenClaw 不代替你管理提供商账户）。

这跟 K8s ServiceAccount 令牌撤销是一个思路——令牌被吊销后，使用该令牌的 Pod 立即失去 API 访问权限。但提供商侧的密钥仍然有效，直到你在提供商控制台手动删除。

### 诊断工具链——为什么 `auth status` + `doctor` 组合？

两个命令覆盖不同层面：

- `openclaw auth status`：显示当前凭证状态（哪些提供商已配置、令牌是否过期）
- `openclaw doctor`：更深层诊断（凭证有效性、令牌过期、配置一致性）

常见问题排查路径：没有凭证 → 配置密钥 + 检查状态；令牌过期 → 刷新令牌或换静态密钥。

这跟 `kubectl get pods` + `kubectl describe pod` 的组合是一个思路——前者看状态概览，后者看详细信息。

---

OpenClaw supports two authentication methods: standard API keys (static, long-lived) for always-on servers, and OAuth tokens (short-lived, refreshable) for subscription accounts like Anthropic Claude CLI. Multi-profile support allows switching credentials per agent, session, or provider. Legacy JSON profiles auto-migrate to SQLite.

OpenClaw 支持两种认证方式：标准 API key（静态、长期）用于持续运行的 server，OAuth token（短期、可刷新）用于订阅制账户（如 Anthropic Claude CLI）。多 profile 支持按 agent、session、provider 切换凭证，旧 JSON profile 自动迁移到 SQLite。
