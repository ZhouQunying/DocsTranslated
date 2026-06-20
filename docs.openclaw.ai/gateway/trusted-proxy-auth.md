# Trusted proxy auth

## 架构精读

> 跳过不影响阅读翻译正文。

### 反向代理认证——把认证交给 proxy

**Trusted proxy auth** 模式下,Gateway 不做认证,完全交给反向代理(如 nginx、Caddy、Cloudflare Access):

```
用户 → 反向代理(认证) → Gateway(信任 proxy,不认证)
```

反向代理负责:
- 用户登录(OAuth、OIDC、SAML)
- 验证用户身份
- 添加身份 header(如 `X-User-Email: user@example.com`)

Gateway 负责:
- 验证请求来自可信的 proxy(检查源 IP)
- 从 header 提取用户身份
- 根据用户身份授权

**为什么这样设计?** 因为认证是复杂的事情(OAuth flow、token 刷新、多因素认证),Gateway 不应该自己做。反向代理专门做认证(Cloudflare Access、Auth0、Okta),做得比 Gateway 好。让专业工具做专业的事。

**这跟 Kubernetes 的 OIDC 认证**是一个思路——kube-apiserver 不自己做 OAuth,而是信任外部 OIDC provider(如 Dex、Auth0)。OpenClaw 的 trusted proxy auth 也是同样: Gateway 不自己做认证,信任外部 proxy。

### Proxy 添加身份 header——身份传递

反向_proxy 认证成功后,在请求里添加身份 header:

```
X-User-Email: user@example.com
X-User-Name: John Doe
```

Gateway 从 header 提取用户身份,不需要自己验证。

**为什么用 header 而不是 token?** 因为 header 是 proxy 添加的,Gateway 只需要信任 proxy。如果用 token,Gateway 需要自己验证 token(跟 OAuth 一样复杂)。Header 让 Gateway 的认证逻辑极简: 检查源 IP → 提取 header → 完成。

### Gateway 验证可信来源——防止绕过 proxy

Gateway 必须验证请求来自**可信的 proxy**,而不是直接来自用户。否则用户可以绕过 proxy,伪造身份 header:

```
恶意用户 → 直接访问 Gateway,伪造 X-User-Email: admin@example.com
```

**怎么验证?** 通过源 IP:
```json
{
  gateway: {
    trustedProxies: ["192.168.1.100"]
  }
}
```

Gateway 只接受来自 `192.168.1.100`(proxy 的 IP)的请求,其他 IP 的请求直接拒绝。

**这跟 AWS ALB 的 trusted proxy 设置**是一个思路——ALB 终结 TLS 后,后端实例需要配置信任 ALB 的 IP 段,才能正确解析 X-Forwarded-For。OpenClaw 的 trusted proxies 也是同样: 只信任特定 IP 的 proxy,防止伪造。

### 安全风险——配置错误 = 完全暴露

**文档警告**: 这是安全敏感功能,配置错误会让 Gateway 完全暴露。

**什么配置错误?**
- **没配置 trustedProxies**: Gateway 接受所有 IP 的请求,任何人都能伪造身份 header
- **trustedProxies 配置太宽**: 如 `["0.0.0.0/0"]`(所有 IP),等于没限制
- **Proxy 没做认证**: Gateway 信任 proxy,但 proxy 没验证用户身份,任何人都能通过 proxy 访问

**这跟防火墙配置错误**是一个思路——防火墙规则配置错了(如 `ALLOW ALL`),等于没有防火墙。OpenClaw 的 trusted proxy auth 也是同样: 配置错了,等于没有认证。

### 什么时候用 trusted proxy auth?

**适合的场景**:
- 已有反向 proxy 做认证(如公司用 Cloudflare Access)
- 多服务共享认证(如 OpenClaw + 其他内部工具都用同一个 proxy 认证)
- 需要企业级认证(如 SAML、LDAP)

**不适合的场景**:
- 单机部署,没有反向 proxy(直接用 API key 认证)
- 公网暴露,没有 proxy(不安全,任何人都能访问)
- 简单部署,不需要复杂认证(直接用 OpenClaw 内置的认证)
