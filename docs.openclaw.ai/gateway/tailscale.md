# Tailscale

## 架构精读

> 跳过不影响阅读翻译正文。

### Loopback + 反向代理——为什么不直接暴露端口？

网关保持 loopback 绑定，Tailscale 处理加密、路由和请求头注入。
三种模式可选：serve（tailnet 内部）、Funnel（公网通道，公网暴露）、off（默认）。
这跟 Nginx + Let's Encrypt 是一个思路——应用只监听本地，反向代理处理 TLS 和外部路由。
区别在于 Tailscale Serve 完全自动化，不需要手动配置 `upstream` 和 SSL。

### Identity 请求头认证——为什么可以免令牌？

Tailscale Serve + `allowTailscale: true` 时，Control UI 和 WebSocket 可用身份请求头免令牌认证。
系统通过检查 forwarded IP 与本地 daemon 来验证用户身份。
此验证**仅适用于 loopback 流量**，且需要特定的转发协议和主机请求头。
HTTP API 端点不使用此认证路径，仍依赖传统网关认证方法。

### 公网通道暴露——为什么强制密码保护？

公网通道（Funnel）把服务暴露到公网，系统强制要求密码保护。
缺少密码配置时，系统阻止启动。
公网通道严格限制 TLS 流量到端口 443、8443、10000。
这跟 ngrok 是一个思路——公网暴露需要认证保底，否则任何人都能访问你的代理。

### Service name 路由——为什么按服务而非主机名寻址？

Serve 模式下可用 `svc:<dns-label>` 格式指定 Tailscale 服务名称，按服务名而非机器主机名路由流量。
需要宿主机是 tailnet 中已批准的 tagged node。
这种方式让服务发现和路由不依赖具体的机器名，更灵活。

---

OpenClaw automatically configures Tailscale Serve for private tailnet traffic, or Funnel for public web exposure, specifically for the dashboard and WebSocket connections. The system keeps Gateway bound to the local loopback address, letting Tailscale handle encryption, traffic routing, and header injection.

OpenClaw 自动为私有 tailnet 流量配置 Tailscale Serve，或为公开 web 暴露配置 Funnel，专门针对 dashboard 和 WebSocket 连接。系统保持 网关 限制在本地 loopback 地址，让 Tailscale 处理加密、流量导向和 header 注入。

## 操作模式

Three states:

三种状态：

- **serve**: Restrict visibility to internal tailnet. Gateway stays on localhost address
- **serve**：限制可见性到内部 tailnet。网关 保持在 localhost 地址
- **funnel**: Publicly broadcast the service over encrypted tunnel, requiring a shared secret
- **funnel**：通过加密通道公开广播服务，强制要求 shared secret
- **off**: Default behavior; OpenClaw ignores these features, but the background daemon may stay active
- **off**：默认行为，OpenClaw 忽略这些功能，但后台 daemon 可能保持活跃

## 认证与安全

Handshake behavior depends on the auth mode configuration, supporting unauthenticated, token, password, and trusted proxy modes.

握手行为由 auth mode 配置决定，支持无认证、token、password 和 trusted proxy。

With Serve + Tailscale auth allowed, the Control UI and WebSocket can use identity headers. The system validates users by checking forwarded IP addresses against the local daemon. This validation **only applies to loopback traffic containing specific forwarded protocol and host headers**.

用 Serve + 允许 Tailscale 认证时，Control UI 和 WebSocket 可用 identity headers。系统通过检查 forwarded IP 地址与本地 daemon 来验证用户。此验证**仅适用于包含特定 forwarded protocol 和 host headers 的 loopback 流量**。

This validation path **bypasses the device pairing step for browser sessions that already have device identity**, while still rejecting clients lacking device credentials. Standard HTTP API routes **completely ignore these identity headers** and rely on traditional gateway auth methods.

此验证路径**绕过已有 device identity 的浏览器 session 的设备配对步骤**，但继续拒绝缺少 device credentials 的客户端。标准 HTTP API 路由**完全忽略这些 identity headers**，依赖传统网关认证方法。

**Security consideration**: This token-free approach assumes a secure host environment. If unauthorized local processes might execute, admins must disable Tailscale auth allow and require explicit token or password.

**安全考虑**：此无 token 方法假设安全的主机环境。如果未授权的本地进程可能执行，管理员必须禁用 Tailscale 认证允许，强制显式 token 或 password。

## 配置

### 内部 Tailnet (Serve)

Set bind to loopback and mode to serve. Users access via the MagicDNS URL. When routing traffic by Tailscale Service name rather than machine hostname, use `svc:<dns-label>` format. Requires the host to be an approved tagged node in the network.

设置 bind 为 loopback，mode 为 serve。用户通过 MagicDNS URL 访问。按 Tailscale Service name 而非机器 hostname 路由流量时，用 `svc:<dns-label>` 格式指定 service name。需要 host 是网络中已批准的 tagged node。

```json5
{
  gateway: {
    bind: "loopback",
    tailscale: { mode: "serve" }
  }
}
```

### 直连 Tailnet 绑定

Listen directly on the Tailnet IP (without Serve or Funnel). Set bind to tailnet and configure an auth token. Access via Tailscale IP on port 18789. Localhost connections will fail in this mode.

直接在 Tailnet IP 上监听（不用 Serve 或 Funnel），设置 bind 为 tailnet 并配置 auth token。通过 Tailscale IP 和端口 18789 访问。此模式下 localhost 连接会失败。

```json5
{
  gateway: {
    bind: "tailnet",
    auth: { token: "your-token" }
  }
}
```

### 公网 (Funnel)

Set mode to funnel and enforce password authentication. **Strongly recommended to provide the secret via environment variables rather than config files**.

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

- **Service names**: The service name parameter only applies in Serve mode and requires the `svc:` prefix
- **Service names**：service name 参数仅适用于 Serve 模式，需要 `svc:` 前缀
- **Cleanup**: The system can auto-revoke Tailscale routes on shutdown
- **清理**：可配置系统在 shutdown 时自动撤销 Tailscale 路由
- **Route preservation**: Specific preservation settings allow externally configured Funnel routes to survive restarts. When active, the system checks existing Funnel state before applying Serve config to prevent overwrites
- **Route preservation**：特定 preservation 设置允许外部配置的 Funnel routes 在重启后存活。激活时，系统在应用 Serve 配置前检查已有 Funnel 状态，防止覆盖
- **Bind defaults**: Bind defaults to auto (preferring loopback); can be forced to tailnet for exclusive network access
- **绑定默认值**：bind 默认 auto（偏好 loopback），可强制 tailnet 用于独占网络访问
- **Exposure scope**: Only the control interface and WebSocket are exposed; node connections use the same WebSocket endpoint
- **暴露范围**：只暴露 control 接口和 WebSocket；node 连接使用同一 WebSocket endpoint

## 远程浏览器控制

When controlling a remote browser, run a node host on the target machine within the same tailnet. The gateway proxies commands to this node. **Funnel does not handle this scenario** — treat node pairing as equivalent to operator access.

控制远程浏览器时，在同一 tailnet 内的目标机器上运行 node host。网关 把命令代理到此 node。**不应用 Funnel 处理此场景**；把 node pairing 等同于 operator access。

## 前提条件和限制

- CLI tool must be installed and authenticated
- CLI 工具必须已安装和认证
- Funnel blocks startup when password protection is missing
- Funnel 缺少密码保护时阻止启动
- Serve requires tailnet HTTPS and adds identity headers; Funnel does not inject these headers
- Serve 需要 tailnet HTTPS 并添加 identity headers，Funnel 不注入这些 headers
- Funnel requires daemon version 1.38.3+, MagicDNS, HTTPS, and specific node attributes
- Funnel 需要 daemon 版本 1.38.3+、MagicDNS、HTTPS 和特定 node 属性
- Funnel strictly limits TLS traffic to ports 443, 8443, and 10000
- Funnel 严格限制 TLS 流量到端口 443、8443、10000
- macOS users must use the open-source app variant to enable Funnel
- macOS 用户必须使用开源应用变体才能启用 Funnel
