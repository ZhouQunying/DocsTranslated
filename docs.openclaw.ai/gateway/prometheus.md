# Prometheus metrics

## 架构精读

> 跳过不影响阅读翻译正文。

### Plugin 模式 + 认证保护

**问题**: Metrics 包含敏感信息 (session 数量、token 消耗、错误率),公开会泄露?

**方案**: 通过 `diagnostics-prometheus` plugin 暴露,**需要认证**:
```bash
curl -H "Authorization: Bearer <token>" https://gateway.example.com/metrics
```

**洞察**: Metrics 不是公开端点,需要认证防止信息泄露。

**权衡**:
- ✓ 安全: 防止竞争情报、攻击侦察、隐私泄露
- ✗ 复杂: 需要配置认证

**模式**: Kubernetes /metrics 端点——需要认证,不是公开端点。

### text/plain 格式

**问题**: 自定义格式 Prometheus 无法直接 scrape,需要额外 exporter?

**方案**: 返回 `text/plain; version=0.0.4; charset=utf-8` (Prometheus 标准 exposition 格式):
```
# HELP openclaw_sessions_total Total number of sessions
# TYPE openclaw_sessions_total counter
openclaw_sessions_total 1234

# HELP openclaw_llm_tokens_total Total LLM tokens consumed
# TYPE openclaw_llm_tokens_total counter
openclaw_llm_tokens_total{provider="openai",model="gpt-4"} 56789
```

**洞察**: 标准格式,Prometheus 直接 scrape,不需要适配。

**权衡**:
- ✓ 兼容: Prometheus 直接解析
- ✓ 标准: 不需要额外 exporter

**模式**: HTTP Content-Type header——告诉客户端数据格式。

### Operator scope 权限

**问题**: Metrics 是运维数据,普通用户不应该看到?

**方案**: 使用 **operator scope** (运维权限),只有配置了 operator 权限的用户能访问。

**洞察**: Metrics 只对运维人员开放,普通用户看不到。

**权衡**:
- ✓ 安全: 防止普通用户困惑或滥用
- ✓ 清晰: 运维数据只给运维人员

### Scrape 配置

**问题**: Prometheus scrape 时需要认证?

**方案**: 配置 bearer_token:
```yaml
scrape_configs:
  - job_name: 'openclaw'
    static_configs:
      - targets: ['gateway.example.com:443']
    scheme: https
    bearer_token: '<token>'
```

**洞察**: Scrape 时必须带 token,否则请求被拒绝。

**权衡**:
- ✓ 安全: 不允许匿名访问
- ✗ 复杂: 需要配置 token

**模式**: GitHub API 认证——需要 token,匿名请求有严格 rate limit。

### Trusted diagnostics

**问题**: 用户输入的数据不可信 (可能被篡改),不应该作为 metrics 导出?

**方案**: 只导出 **trusted diagnostics** (可信诊断数据) 和 core-emitted gateway metrics:
- Session 数量 (内部统计)
- Token 消耗 (内部统计)
- 错误率 (内部统计)

**洞察**: 只导出内部生成的数据,不导出用户输入的数据。

**权衡**:
- ✓ 安全: 防止信息泄露、数据污染
- ✓ 准确: 只导出可信数据
