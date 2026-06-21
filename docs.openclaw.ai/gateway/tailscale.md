# Tailscale

OpenClaw 自动为私有 tailnet 流量配置 Tailscale Serve,或为公开 web 暴露配置 Funnel,专门针对 dashboard 和 WebSocket 连接。系统保持 Gateway 限制在本地 loopback 地址,让 Tailscale 处理加密、流量导向和 header 注入。

> **类比:Nginx + Let's Encrypt 自动化。** Nginx 是 reverse proxy,Let's Encrypt 自动颁发 TLS 证书。Tailscale Serve 类似: 它是 reverse proxy,Tailscale 自动处理 TLS 和路由。区别: Nginx 需要你配置 upstream 和 SSL,Tailscale Serve 完全自动——Gateway 保持 loopback,Tailscale 处理一切。Funnel 更进一步,把服务暴露到公网(类似 ngrok)。
>
> **架构要点:** 三种模式: serve (tailnet 内部)、funnel (公网暴露)、off (默认);Gateway 保持 loopback,Tailscale 处理加密和路由;Serve + `allowTailscale: true` 时 Control UI/WebSocket 可用 identity headers 免 token;HTTP API endpoints 不用 Tailscale identity-header auth;Funnel 需要密码保护,缺少时阻止启动;Funnel 限制 TLS 流量到端口 443、8443、10000。

## 操作模式

三种状态:

- **serve**: 限制可见性到内部 tailnet。Gateway 保持在 localhost 地址
- **funnel**: 通过加密通道公开广播服务,强制要求 shared secret
- **off**: 默认行为,OpenClaw 忽略这些功能,但后台 daemon 可能保持活跃

## 认证与安全

Handshake 行为由 auth mode 配置决定,支持无认证、token、password、trusted proxy。

用 Serve + 允许 Tailscale 认证时,Control UI 和 WebSocket 可用 identity headers。系统通过检查 forwarded IP 地址与本地 daemon 来验证用户。此验证**仅适用于包含特定 forwarded protocol 和 host headers 的 loopback 流量**。

此验证路径**绕过已有 device identity 的浏览器 session 的设备配对步骤**,但继续拒绝缺少 device credentials 的客户端。标准 HTTP API 路由**完全忽略这些 identity headers**,依赖传统 gateway 认证方法。

**安全考虑**: 此无 token 方法假设安全的主机环境。如果未授权的本地进程可能执行,管理员必须禁用 Tailscale 认证允许,强制显式 token 或 password。

## 配置

### 内部 Tailnet (Serve)

设置 bind 为 loopback,mode 为 serve。用户通过 MagicDNS URL 访问。通过命名 Tailscale Service 而非机器 hostname 路由流量时,用 `svc:<dns-label>` 格式指定 service name。需要 host 是网络中已批准的 tagged node。

```json5
{
  gateway: {
    bind: "loopback",
    tailscale: { mode: "serve" }
  }
}
```

### 直连 Tailnet 绑定

直接在 Tailnet IP 上监听(不用 Serve 或 Funnel),设置 bind 为 tailnet 并配置 auth token。通过 Tailscale IP 和端口 18789 访问。此场景下 localhost 连接会失败。

```json5
{
  gateway: {
    bind: "tailnet",
    auth: { token: "your-token" }
  }
}
```

### 公网 (Funnel)

设置 mode 为 funnel 并强制 password 认证。**强烈建议通过环境变量而非配置文件提供 secret**。

```json5
{
  gateway: {
    bind: "loopback",
    auth: { password: "your-password" },
    tailscale: { mode: "funnel" }
  }
}
```

## 高级功能

- **Service names**: service name 参数仅适用于 Serve 模式,需要 `svc:` 前缀
- **清理**: 可配置系统在 shutdown 时自动撤销 Tailscale 路由
- **Route preservation**: 特定 preservation 设置允许外部配置的 Funnel routes 在重启后存活。激活时,系统在应用 Serve 配置前检查已有 Funnel 状态以防止覆盖
- **绑定默认值**: bind 默认 auto(偏好 loopback),可强制 tailnet 用于独占网络访问
- **暴露范围**: 只暴露 control 接口和 WebSocket;node 连接使用同一 WebSocket endpoint

## 远程浏览器控制

控制远程浏览器时,在同一 tailnet 内的目标机器上运行 node host。Gateway 把命令代理到此 node。**不应用 Funnel 处理此场景**;把 node pairing 等同于 operator access。

## 前提条件和限制

- CLI 工具必须已安装和认证
- Funnel 缺少密码保护时阻止启动
- Serve 需要 tailnet HTTPS 并添加 identity headers,Funnel 不注入这些 headers
- Funnel 需要 daemon 版本 1.38.3+,MagicDNS,HTTPS,特定 node 属性
- Funnel 严格限制 TLS 流量到端口 443、8443、10000
- macOS 用户必须使用开源应用变体才能启用 Funnel
