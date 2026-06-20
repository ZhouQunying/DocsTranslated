# Trusted proxy auth

## 架构精读

> 跳过不影响阅读翻译正文。

### 反向代理认证

**问题**: 认证复杂 (OAuth flow、token 刷新、多因素认证),Gateway 自己做不好?

**方案**: **Trusted proxy auth**——Gateway 不做认证,完全交给反向代理:
```
用户 → 反向代理 (认证) → Gateway (信任 proxy,不认证)
```

**洞察**: 让专业工具做专业的事 (Cloudflare Access、Auth0、Okta)。

**权衡**:
- ✓ 简单: Gateway 认证逻辑极简
- ✓ 专业: proxy 专门做认证,做得比 Gateway 好

**模式**: Kubernetes OIDC 认证——kube-apiserver 不自己做 OAuth,信任外部 OIDC provider。

### Proxy 添加身份 header

**问题**: Gateway 如何知道用户身份?

**方案**: Proxy 认证成功后添加身份 header:
```
X-User-Email: user@example.com
X-User-Name: John Doe
```
Gateway 从 header 提取用户身份。

**洞察**: Header 是 proxy 添加的,Gateway 只需要信任 proxy,不需要自己验证 token。

**权衡**:
- ✓ 简单: Gateway 只提取 header
- ✓ 安全: 身份由 proxy 验证

### Gateway 验证可信来源

**问题**: 用户可以绕过 proxy,直接访问 Gateway,伪造身份 header?

**方案**: Gateway 验证请求来自**可信的 proxy** (通过源 IP):
```json
{
  gateway: {
    trustedProxies: ["192.168.1.100"]
  }
}
```
只接受来自 `192.168.1.100` 的请求。

**洞察**: 防止绕过 proxy,伪造身份。

**权衡**:
- ✓ 安全: 只信任特定 IP 的 proxy
- ✗ 不灵活: proxy IP 变化需要更新配置

**模式**: AWS ALB trusted proxy——后端实例配置信任 ALB 的 IP 段。

### 安全风险

**问题**: 配置错误会让 Gateway 完全暴露?

**方案**: **必须**正确配置:
- ✓ 配置 `trustedProxies` (只信任特定 IP)
- ✓ `trustedProxies` 不能太宽 (如 `0.0.0.0/0`)
- ✓ Proxy 必须做认证

**洞察**: 配置错误 = 没有认证,任何人都能访问。

**权衡**:
- ✗ 风险高: 配置错误 = 完全暴露
- ✓ 安全: 正确配置 = 安全

**模式**: 防火墙配置错误——`ALLOW ALL` 等于没有防火墙。

### 什么时候用 trusted proxy auth?

**问题**: 什么场景适合用 trusted proxy auth?

**方案**: 
**适合**:
- 已有反向 proxy 做认证 (如 Cloudflare Access)
- 多服务共享认证 (OpenClaw + 其他内部工具)
- 需要企业级认证 (SAML、LDAP)

**不适合**:
- 单机部署,没有反向 proxy
- 公网暴露,没有 proxy
- 简单部署,不需要复杂认证
