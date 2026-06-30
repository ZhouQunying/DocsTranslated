# `openclaw crestodian`

## 架构精读

> 跳过不影响阅读翻译正文。

### 凭证看门狗——为什么是后台 daemon 而非按需检查？

Crestodian 是后台凭证监控 daemon，持续检查凭证健康：

- **过期检测**：OAuth 令牌即将过期时提前告警
- **有效性验证**：定期验证 API 密钥是否仍然有效
- **轮换触发**：凭证失效时自动触发轮换流程

这跟 Certbot 的证书监控是一个思路——不是等证书过期了再发现（业务中断），而是后台持续监控，提前 N 天告警。Crestodian 把"凭证健康检查"从人工定期巡检变成自动化持续监控。

### 凭证刷新——为什么自动刷新而非手动？

OAuth 令牌过期前，Crestodian 自动触发刷新流程（用 refresh token 获取新 access token）：

这跟 AWS IAM 的 STS 临时凭证是一个思路——临时凭证自动轮换，不需要人工干预。手动刷新容易遗忘，自动刷新确保凭证始终有效。

---

Background credential watchdog daemon that monitors credential health: detects expiration (alerts before OAuth tokens expire), validates effectiveness (periodic API key checks), and triggers rotation (auto-refresh with refresh token before expiration).

后台凭证看门狗 daemon，监控凭证健康：检测过期（OAuth 令牌过期前提前告警）、验证有效性（定期检查 API 密钥）、触发轮换（过期前用 refresh token 自动刷新）。
