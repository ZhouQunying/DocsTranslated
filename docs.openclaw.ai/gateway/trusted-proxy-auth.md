# Trusted Proxy Auth

## 架构精读

> 跳过不影响阅读翻译正文。

### Identity-aware proxy delegation——为什么不自己认证？

Trusted proxy auth 把认证责任交给外部身份感知 proxy（Pomerium/Cloudflare Access/Okta Access Gate），Gateway 只验证来源 IP + 提取身份 header：

```json5
{
  gateway: {
    bind: "127.0.0.1",  // 只监听 localhost，防止绕过
    auth: {
      mode: "trusted-proxy",
      trustedProxies: ["127.0.0.1"],  // 只信任 proxy 来源
      userTag: "X-Forwarded-User"     // 从 header 提取身份
    }
  }
}
```

这跟 Cloudflare Access + 后端服务是一个思路——Access 在 edge 做认证，后端信任 Access 传来的 `Cf-Access-Jwt-Assertion` header 而不再自己认证。好处是认证逻辑集中在 proxy（可以统一用 SSO/MFA），Gateway 代码更简单。

代价是配置错误风险——如果 `trustedProxies` 配太宽（如 `0.0.0.0/0`），任何人都能伪造身份 header。

### When NOT to use——为什么不能"proxy 只做 TLS 终结"？

如果 proxy 只做 TLS 终结（不解密身份 header），或者有网络路径绕过 proxy 直达 Gateway，不能用 trusted proxy auth。

这跟 OAuth2 Proxy 的限制是一个思路——proxy 必须能验证身份并注入身份 header，仅做 TLS 终结不够。如果有直接访问路径（如 localhost 直接连 Gateway），攻击者可以绕过 proxy 伪造身份。

### Mixed token config 阻止——为什么不能同时开两种 auth？

系统故意阻止同时启用共享密钥（token 认证）和外部验证（trusted proxy auth）。

这跟防火墙的 default-deny 是一个思路——如果两种认证同时开，可能出现"token 认证通过了但 proxy 认证没验证"的静默失败（攻击者用 token 绕过 proxy 的 MFA）。强制选一种认证路径防止这种混淆。

### Operator scopes header——为什么是限制而非授权？

`X-Operator-Scopes` HTTP header 让 caller 声明特定权限级别。对浏览器升级（WebSocket），这个 header 严格作为限制（限制已协商的 session 能力），而非权限授予。

这跟 OAuth2 作用域 的 downgrade 是一个思路——client 可以请求比授权范围更小的作用域（downgrade），但不能请求更大的作用域。`X-Operator-Scopes` 只能限制 session 能力（如"只读"），不能扩展（如"给管理员权限"）。

### TLS termination 位置——为什么推荐在 proxy 终结？

推荐在 proxy 层集中终结 TLS + HSTS，而非 Gateway 直接终结。

这跟 CDN 的 TLS 策略是一个思路——CDN（proxy）终结 TLS 可以集中管理证书（Let's Encrypt 自动续期）、HTTP 加固（HSTS 预加载）、限流。Gateway 终结 TLS 需要自己管理证书（更复杂，容易过期）。

上线建议：先短 `max-age`（如 1 天）观察，再延长（如 1 年）。subdomain 和预加载列表只在整个基础设施都支持 HTTPS 时加。

---

This setup allows administrators to offload user verification to an "identity-aware proxy" rather than handling it internally.

此设置让管理员把用户验证责任交给"identity-aware proxy"，而非内部处理。

The system intentionally blocks setups that simultaneously enable shared secrets and external verification to prevent silent failures. Users must choose one specific authentication path to ensure secure request handling.

系统故意阻止同时启用 shared secret 和 external verification 的配置，以防止 silent failure。用户必须选择一种特定的认证路径来确保安全的请求处理。
