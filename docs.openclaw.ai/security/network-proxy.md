# Network Proxy

## 架构精读

> 跳过不影响阅读翻译正文。

### 出站代理——为什么 AI 请求需要走代理？

网络代理配置让网关的出站请求（调用 AI provider API）走 HTTP/HTTPS 代理：

```json5
{
  gateway: {
    proxy: "http://proxy.internal:8080"
  }
}
```

这跟企业网络的出站代理策略是一个思路——所有外部流量必须经过代理（审计、过滤、IP 白名单）。OpenClaw 网关调用 Anthropic/OpenAI API 时需要走企业代理才能出站。

### 入站代理——为什么需要反向代理？

入站方向用反向代理（Caddy/nginx/Traefik）终结 TLS + 做身份认证：

- **TLS 终结**：代理管理证书（Let's Encrypt 自动续期）
- **身份认证**：代理做 SSO/MFA，传 身份标识头 给网关
- **请求过滤**：代理做 rate limiting、WAF

这跟 Cloudflare 的入站代理是一个思路——Cloudflare 在边缘做 TLS 终结 + DDoS 防护 + WAF，后端服务只处理业务逻辑。

### Trusted proxy auth——为什么不能信任所有来源？

反向代理场景下，网关用 可信代理认证 模式——只信任特定 IP 来源的 身份标识头：

```json5
{
  gateway: {
    auth: {
      mode: "trusted-proxy",
      trustedProxies: ["127.0.0.1"]
    }
  }
}
```

这跟防火墙的信任区域模型是一个思路——DMZ 区域（代理服务器）可信，公网区域（直接访问）不可信。如果不限制 trustedProxies，攻击者可以绕过代理直接连接网关，伪造 身份标识头。

### 代理环境变量——为什么需要 no_proxy？

`no_proxy` 环境变量排除内部地址（localhost、内网 IP），防止内部通信也走代理：

```
no_proxy=localhost,127.0.0.1,.internal
```

这跟浏览器的代理例外规则是一个思路——访问 localhost 和内网服务时直连，不走代理。否则 WebSocket 连接（localhost:18789）也会走代理，导致性能下降或连接失败。

---

Network proxy configuration covers both outbound (gateway → AI provider API) and inbound (user → gateway) traffic paths.

网络代理配置覆盖出站（网关 → AI provider API）和入站（用户 → 网关）两条流量路径。

Outbound proxy routes AI API calls through HTTP/HTTPS proxy for enterprise auditing, filtering, and IP allowlisting. Inbound reverse proxy (Caddy/nginx/Traefik) handles TLS termination, identity authentication (SSO/MFA), and request filtering (rate limiting, WAF).

出站代理让 AI API 调用走 HTTP/HTTPS 代理，实现企业审计、过滤和 IP 白名单。入站反向代理（Caddy/nginx/Traefik）处理 TLS 终结、身份认证（SSO/MFA）和请求过滤（rate limiting、WAF）。

Trusted proxy auth restricts 身份标识头 trust to specific IP sources — without `trustedProxies` restriction, attackers can bypass the proxy and forge 身份标识头s. The `no_proxy` environment variable excludes internal addresses (localhost, internal IPs) to prevent internal WebSocket connections from routing through the proxy.

Trusted proxy auth 将 身份标识头 信任限制到特定 IP 来源——不限制 `trustedProxies`，攻击者可以绕过代理伪造 身份标识头。`no_proxy` 环境变量排除内部地址（localhost、内网 IP），防止内部 WebSocket 连接走代理。
