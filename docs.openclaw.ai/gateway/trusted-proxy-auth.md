# Trusted Proxy Auth

## 架构精读

> 跳过不影响阅读翻译正文。

### 身份感知代理委托——为什么不自己认证？

可信代理认证把认证责任交给外部身份感知代理（Pomerium/Cloudflare Access/Okta Access Gate），网关 只验证来源 IP + 提取身份请求头：

```json5
{
  gateway: {
    bind: "127.0.0.1",  // 只监听 localhost，防止绕过
    auth: {
      mode: "trusted-proxy",
      trustedProxies: ["127.0.0.1"],  // 只信任 proxy 来源
      userTag: "X-Forwarded-User"     // 从请求头提取身份
    }
  }
}
```

这跟 Cloudflare Access + 后端服务是一个思路——Access 在边缘做认证，后端信任 Access 传来的 `Cf-Access-Jwt-Assertion` 请求头而不再自己认证。好处是认证逻辑集中在代理（可以统一用 SSO/MFA），网关 代码更简单。

代价是配置错误风险——如果 `trustedProxies` 配太宽（如 `0.0.0.0/0`），任何人都能伪造身份请求头。

### 何时不使用——为什么不能"代理只做 TLS 终结"？

如果代理只做 TLS 终结（不解密身份请求头），或者有网络路径绕过代理直达 网关，不能用可信代理认证。

这跟 OAuth2 代理的限制是一个思路——代理必须能验证身份并注入身份请求头，仅做 TLS 终结不够。如果有直接访问路径（如 localhost 直接连 网关），攻击者可以绕过代理伪造身份。

### 混合令牌配置阻止——为什么不能同时开两种认证？

系统故意阻止同时启用共享密钥（令牌认证）和外部验证（可信代理认证）。

这跟防火墙的默认拒绝是一个思路——如果两种认证同时开，可能出现"令牌认证通过了但代理认证没验证"的静默失败。攻击者可能用令牌绕过代理的 MFA。强制选一种认证路径防止这种混淆。

### 操作员作用域请求头——为什么是限制而非授权？

`X-Operator-Scopes` HTTP 请求头让调用方声明特定权限级别。对浏览器升级（WebSocket），这个请求头严格作为限制（限制已协商的会话能力），而非权限授予。

这跟 OAuth2 作用域的降级是一个思路——客户端可以请求比授权范围更小的作用域（降级），但不能请求更大的作用域。`X-Operator-Scopes` 只能限制会话能力（如"只读"），不能扩展（如"给管理员权限"）。

### TLS 终结位置——为什么推荐在代理终结？

推荐在代理层集中终结 TLS + HSTS，而非 网关 直接终结。

这跟 CDN 的 TLS 策略是一个思路——CDN（代理）终结 TLS 可以集中管理证书（Let's Encrypt 自动续期）、HTTP 加固（HSTS 预加载）、限流。网关 终结 TLS 需要自己管理证书（更复杂，容易过期）。

上线建议：先短 `max-age`（如 1 天）观察，再延长（如 1 年）。子域名和预加载列表只在整个基础设施都支持 HTTPS 时加。

---

This setup allows administrators to offload user verification to an "identity-aware proxy" rather than handling it internally.

此设置让管理员把用户验证责任交给"身份感知代理"，而非内部处理。

The system intentionally blocks setups that simultaneously enable shared secrets and external verification to prevent silent failures. Users must choose one specific authentication path to ensure secure request handling.

系统故意阻止同时启用共享密钥和外部验证的配置，以防止静默失败。用户必须选择一种特定的认证路径来确保安全的请求处理。
