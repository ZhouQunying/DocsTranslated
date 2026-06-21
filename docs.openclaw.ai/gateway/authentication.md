# Authentication

## 架构精读

> 跳过不影响阅读翻译正文。

### 双轨认证——为什么 API key 和 OAuth 并存？

OpenClaw 认证系统提供两条独立的凭证路径：

- **API key**：静态长期凭证，生成后存入 `.env` 或环境变量，适合持续运行的 server
- **OAuth token**：短期可刷新凭证，复用 CLI 登录态（如 Anthropic Claude CLI），适合订阅制账户

这跟 AWS IAM Access Key + SSO token 是一个思路——Access Key 是长期凭证（适合 server/CI），SSO token 短期需刷新（适合个人交互）。

关键设计是**双轨独立**。API key 永不过期，OAuth token 定期刷新，两条轨道互不依赖。

### Credential 选择的优先级链——为什么需要多 profile？

系统支持多 credential profile，选择顺序是确定性的：

1. CLI flag（命令行指定）
2. session pin（`/auth use <profile>`）
3. per-agent 配置
4. 默认 profile

旧 JSON profile 自动迁移到 SQLite 存储。

这跟 git remote 的优先级是一个思路——命令行指定的 remote 优先于配置文件中的默认 remote。多 profile 让一个 gateway 同时对接多个 provider，每个 agent 用不同的凭证。

### Auth 轮换策略——为什么需要多 key 轮转？

当单 key 触发 rate-limit 时，系统循环使用多个环境变量中的 key：

`OPENAI_API_KEY` → `OPENAI_API_KEY_2` → ...

override var 优先于默认 var。这跟 DNS round-robin 是一个思路——一个 endpoint 不可用时自动切换到下一个。轮换是自动的，不需要人工干预。

### Runtime credential 撤销——为什么 Control Plane 删除后 run 立即中止？

Control Plane 删除凭证后，活跃的 run 以 `auth-revoked` stop code 立即中止。Provider 侧的凭证需要手动失效（OpenClaw 不代替你管理 provider 账户）。

这跟 K8s ServiceAccount token 撤销是一个思路——token 被吊销后，使用该 token 的 pod 立即失去 API 访问权限。但 provider 侧的 key 仍然有效，直到你在 provider 控制台手动删除。

### 诊断工具链——为什么 `auth status` + `doctor` 组合？

两个命令覆盖不同层面：

- `openclaw auth status`：显示当前 credential 状态（哪些 provider 已配置、token 是否过期）
- `openclaw doctor`：更深层诊断（credential 有效性、token 过期、config 一致性）

常见问题排查路径：no credentials → 配置 key + 检查状态；token expired → 刷新 token 或换静态 key。

这跟 `kubectl get pods` + `kubectl describe pod` 的组合是一个思路——前者看状态概览，后者看详细信息。

---

OpenClaw supports two authentication methods: standard API keys (static, long-lived) for always-on servers, and OAuth tokens (short-lived, refreshable) for subscription accounts like Anthropic Claude CLI. Multi-profile support allows switching credentials per agent, session, or provider. Legacy JSON profiles auto-migrate to SQLite.

OpenClaw 支持两种认证方式：标准 API key（静态、长期）用于持续运行的 server，OAuth token（短期、可刷新）用于订阅制账户（如 Anthropic Claude CLI）。多 profile 支持按 agent、session、provider 切换凭证，旧 JSON profile 自动迁移到 SQLite。
