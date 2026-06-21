# Authentication

**总结：** AI 服务认证——标准 API key 和 OAuth。持续运行的 server 推荐静态 key，订阅制 OAuth 兼容账户也可用。

> **类比：AWS IAM Access Key + SSO token。** IAM Access Key 是长期凭证（适合 server/CI），SSO token 短期需刷新（适合个人交互）。OpenClaw auth 类似——API key 是长期静态凭证（推荐 server 使用），OAuth token 短期需刷新（订阅制账户如 Anthropic Claude CLI 兼容），多 profile 支持按 agent/session/provider 切换凭证。
>
> **架构要点：** 推荐设置：API key（任意 provider），生成后存 server（`.env` 文件或环境变量），持续 server 最稳定；Anthropic Claude CLI token：复用本地 CLI 登录（当前允许且优先），旧 JSON profile 迁移到 SQLite；API key 轮换：rate-limit 错误时循环多个 env var（`OPENAI_API_KEY`/`OPENAI_API_KEY_2`/...），优先使用 override var；运行时移除 provider auth：Control plane 删除凭证 → 活跃 run 以 auth-revoked stop code 中止，provider 侧需手动失效；credential 选择：多 profile 管理（legacy 迁移、CLI flag、session pin `/auth use <profile>`、per-agent 顺序覆盖）；OpenAI/legacy openai-codex ID：诊断工具迁移旧 ID 到标准 route；检查状态：`openclaw auth status` + `openclaw doctor`；troubleshooting：no credentials（配置 key + 检查状态）、token expired（刷新 token 或换静态 key）。
