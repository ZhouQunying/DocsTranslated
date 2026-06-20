# Authentication

## 架构精读

> 跳过不影响阅读翻译正文。

### OAuth vs API key

**问题**: 用 OAuth 还是 API key 连接 LLM provider?

**方案**: 两种:
- **OAuth**: 用户授权 OpenClaw 访问 LLM 账户,token 有过期时间
- **API key**: 用户生成 API key,长期有效

**洞察**: OAuth 权限细但复杂,API key 简单但粗粒度。

**权衡**:
- ✓ OAuth: 用订阅账户 (如 ChatGPT Plus),高 rate limit,低边际成本
- ✓ API key: 不会过期,适合 always-on Gateway (24/7 运行)

**模式**: GitHub PAT vs OAuth App——PAT 长期有效适合脚本,OAuth 权限细粒度但 token 会过期。

### Credential 存储位置

**问题**: 多个 agent 用不同 credential,如何隔离?

**方案**: Per-agent SQLite 数据库:
```
~/.openclaw/agents/<agentId>/agent/openclaw-agent.sqlite
```

**洞察**: 每个 agent 有自己的 credential 池,互不干扰。

**权衡**:
- ✓ 隔离: 一个 agent 的 rate limit 不影响另一个
- ✓ 灵活: 不同 agent 用不同 credential

**模式**: 浏览器 profile 隔离——每个 profile 有自己的 cookie、history、password。

### Per-session vs per-agent auth

**问题**: 一个 agent 服务多个用户,每个用户有自己的 credential?

**方案**: 两级:
- **Per-agent**: Agent 的所有 session 用同一个 credential (单用户)
- **Per-session**: 不同 session 用不同 credential (多用户)

**洞察**: Per-session auth 让每个用户的 session 用自己的 credential,互不影响。

**权衡**:
- ✓ Per-agent: 简单,适合单用户
- ✓ Per-session: 隔离,适合多用户 (团队)

**场景**: Coding agent 服务多个开发者,每个开发者有自己的 OpenAI 账户 (不同 rate limit)。

### Auth 失败的处理

**问题**: Auth 失败 (API key 无效、OAuth token 过期),自动切换到另一个 credential?

**方案**: **不自动 fallback**,直接报错。

**洞察**: Auth 失败 = 配置错误 (不是临时故障),自动切换会掩盖问题。

**权衡**:
- ✓ 明确: 用户知道"我的 key 失效了"
- ✗ 不自动: 需要用户手动修复

**模式**: 数据库连接失败——不自动切换到另一个数据库 (可能连错),报错让运维检查。

**例外**: Rate limit 是临时故障,会自动切换 credential 或等一会儿再试。

### Token 过期的处理

**问题**: OAuth token 过期,需要用户重新授权?

**方案**:
- **OAuth**: 自动用 refresh token 刷新 access token
- **API key**: 没有 refresh 机制,需要手动生成新 key

**洞察**: OAuth 协议设计了 refresh token 机制,用户授权一次后自动刷新。

**权衡**:
- ✓ OAuth: 自动刷新,用户不需要干预
- ✗ API key: 被撤销后需手动生成新 key
