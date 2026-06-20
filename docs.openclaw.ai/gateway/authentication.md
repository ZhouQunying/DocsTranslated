# Authentication

## 架构精读

> 跳过不影响阅读翻译正文。

### OAuth vs API key——两种认证方式的权衡

OpenClaw 支持两种认证方式连接 LLM provider:

**OAuth**(Open Authorization,开放授权协议):
- 用户授权 OpenClaw 访问他们的 LLM 账户(如 ChatGPT 账户)
- OpenClaw 拿到的是 OAuth token,不是用户的密码
- Token 有过期时间,需要定期刷新

**API key**(API 密钥):
- 用户在 provider 网站生成一个 API key,粘贴到 OpenClaw 配置
- API key 是长期有效的,不会过期(除非用户手动撤销)
- API key 按使用量计费

**什么时候用 OAuth?** 当用户有订阅账户时(如 ChatGPT Plus)。订阅账户通常有更高的 rate limit 和更低的边际成本(订阅费固定,不额外收费)。OAuth 让 OpenClaw 用用户的订阅账户,不额外花钱。

**什么时候用 API key?** 当用户没有订阅,或者需要更稳定的认证时。API key 不会过期,不需要刷新,适合 always-on 的 Gateway(如服务器上的 OpenClaw,24/7 运行)。

**这跟 GitHub 的 Personal Access Token vs OAuth App 是一个思路**——PAT 是长期有效的 API key,适合脚本和 CI/CD。OAuth App 需要用户授权,token 会过期,但权限更细粒度。OpenClaw 的 OAuth vs API key 也是同样的权衡: OAuth 权限细但复杂,API key 简单但粗粒度。

### Credential 存储位置——per-agent 隔离

每个 agent 的 credential 存储在独立的 SQLite 数据库里:

```
~/.openclaw/agents/<agentId>/agent/openclaw-agent.sqlite
```

**为什么 per-agent 隔离?** 因为不同 agent 可能用不同的 credential:
- Coding agent 用用户 A 的 OpenAI key
- Support agent 用用户 B 的 OpenAI key
- 如果共享 credential,一个 agent 的 rate limit 会影响另一个 agent

隔离让每个 agent 有自己的 credential 池,互不干扰。这跟 **浏览器的 profile 隔离**是一个思路——Chrome 的每个 profile 有自己的 cookie、history、password,不共享。OpenClaw 的 agent credential 也是同样: 每个 agent 有自己的 credential,不共享。

### Per-session vs per-agent auth——认证的作用域

OpenClaw 的认证可以在两个层级:

**Per-agent**(每个 agent 一个认证):
- Agent 的所有 session 用同一个 credential
- 简单,适合单用户场景

**Per-session**(每个 session 一个认证):
- 不同 session 可以用不同的 credential
- 复杂,适合多用户场景(如一个 agent 服务多个用户,每个用户用自己的 credential)

**为什么需要 per-session?** 想象一个场景: 一个 coding agent 服务团队里的多个开发者。每个开发者有自己的 OpenAI 账户(不同的 rate limit 和配额)。如果 agent 用同一个 credential,一个开发者用完了 rate limit,其他开发者也用不了。Per-session auth 让每个开发者的 session 用自己的 credential,互不影响。

### Auth 失败的处理——不自动 fallback

当 auth 失败时(如 API key 无效、OAuth token 过期),OpenClaw **不**自动切换到另一个 credential,而是直接报错。

**为什么不自动 fallback?** 因为 auth 失败通常意味着**配置错误**,不是临时故障:
- API key 无效 → 用户粘贴错了,或者 key 被撤销了
- OAuth token 过期 → 需要用户重新授权
- 自动切换可能掩盖问题,用户不知道"我的 key 失效了"

这跟 **数据库连接失败**是一个思路——连接失败时,应用不会自动切换到另一个数据库(可能连到错误的数据库),而是报错让运维人员检查。OpenClaw 的 auth 失败也是同样: 报错让用户检查,不自动切换。

**例外**: rate limit 不是 auth 失败,是临时故障(请求太多,等一会儿就好)。rate limit 时 OpenClaw 会自动切换到另一个 credential(如果有),或者等一会儿再试。

### Token 过期的处理——自动刷新 vs 手动重新授权

**OAuth token 过期**: OpenClaw 自动用 refresh token 刷新 access token,用户不需要干预。Refresh token 是长期有效的,access token 是短期有效的。

**API key 过期/撤销**: 没有 refresh 机制,需要用户手动去 provider 网站生成新 key,粘贴到 OpenClaw 配置。

**为什么 OAuth 能自动刷新?** 因为 OAuth 协议设计了 refresh token 机制。用户授权一次,应用拿到 refresh token,之后可以自动刷新,不需要用户反复授权。

**为什么 API key 不能自动刷新?** 因为 API key 是长期有效的,没有"过期"的概念(除非用户手动撤销)。如果 key 被撤销了,只能用户手动生成新 key。
