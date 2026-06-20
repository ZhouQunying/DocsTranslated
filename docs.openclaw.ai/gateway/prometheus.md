# Prometheus metrics

## 架构精读

> 跳过不影响阅读翻译正文。

### Plugin 模式 + 认证保护——metrics 不是公开端点

Prometheus metrics 通过 `diagnostics-prometheus` plugin 暴露,**需要 Gateway 认证**:

```bash
curl -H "Authorization: Bearer <token>" https://gateway.example.com/metrics
```

**为什么 metrics 需要认证?** 因为 metrics 包含敏感信息:
- Session 数量(暴露系统规模)
- Token 消耗(暴露使用模式和成本)
- 错误率(暴露系统健康状况)
- 模型使用(暴露使用了哪些 provider)

如果 `/metrics` 是公开端点,任何人都能看到这些信息,可能被用于:
- **竞争情报**: 竞争对手知道你的系统规模和成本
- **攻击侦察**: 攻击者知道系统的错误率和瓶颈
- **隐私泄露**: 知道用户数量和活跃度

**这跟 Kubernetes 的 /metrics 端点**是一个思路——kube-apiserver 的 `/metrics` 需要认证,不是公开端点。OpenClaw 的 Prometheus metrics 也是同样: 需要认证,防止信息泄露。

### text/plain 格式——Prometheus 的标准 exposition format

Metrics 端点返回 `text/plain; version=0.0.4; charset=utf-8`,这是 Prometheus 的标准 exposition 格式:

```
# HELP openclaw_sessions_total Total number of sessions
# TYPE openclaw_sessions_total counter
openclaw_sessions_total 1234

# HELP openclaw_llm_tokens_total Total LLM tokens consumed
# TYPE openclaw_llm_tokens_total counter
openclaw_llm_tokens_total{provider="openai",model="gpt-4"} 56789
```

**为什么用标准格式?** 因为 Prometheus 的 scrape 工具只能解析标准格式。如果用自定义格式(如 JSON),Prometheus 无法直接 scrape,需要额外的 exporter。

**这跟 HTTP 的 Content-Type header 是一个思路**——Content-Type 告诉客户端数据的格式,客户端按格式解析。OpenClaw 的 Prometheus metrics 用标准 Content-Type,Prometheus 直接 scrape,不需要适配。

### Operator scope 权限——只有运维人员能看

Metrics 端点使用 **operator scope**(运维权限),只有配置了 operator 权限的用户能访问:

**为什么需要 operator scope?** 因为 metrics 是运维数据,不是普通用户应该看到的:
- 普通用户: 只关心"我的消息能不能正常发送"
- 运维人员: 关心"系统有多少 session、消耗多少 token、错误率多少"

如果普通用户能看 metrics,可能困惑("为什么 token 消耗这么多?"),或者滥用("我知道系统有多少 session,可以估算成本")。

Operator scope 让 metrics 只对运维人员开放,普通用户看不到。

### Scrape 配置——通过认证路径

Prometheus scrape 配置需要通过认证:

```yaml
scrape_configs:
  - job_name: 'openclaw'
    static_configs:
      - targets: ['gateway.example.com:443']
    scheme: https
    bearer_token: '<token>'
```

**为什么需要 bearer_token?** 因为 metrics 端点需要认证,Prometheus scrape 时必须带上 token。如果不带 token,请求被拒绝。

**这跟 GitHub API 的认证**是一个思路——GitHub API 需要 token 认证,匿名请求有严格的 rate limit。OpenClaw 的 Prometheus metrics 也是同样: 需要 token 认证,不允许匿名访问。

### Trusted diagnostics——只信任内部数据

Prometheus plugin 监听 **trusted diagnostics**(可信诊断数据)和 core-emitted gateway metrics(核心网关指标):

**什么是 trusted diagnostics?** 内部生成的诊断数据,不是用户输入的:
- Session 数量(内部统计)
- Token 消耗(内部统计)
- 错误率(内部统计)

**为什么强调 trusted?** 因为用户输入的数据不可信(可能被篡改),不应该作为 metrics 导出。如果 metrics 包含用户输入的数据(如"用户发送的消息内容"),可能被用于:
- **信息泄露**: 通过 metrics 看到其他用户的消息
- **数据污染**: 恶意用户发送特定内容,影响 metrics 统计

只导出 trusted diagnostics,保证 metrics 的安全性和准确性。
