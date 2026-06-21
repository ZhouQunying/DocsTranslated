# Discovery and Transports——发现与传输

## 架构精读

> 跳过不影响阅读翻译正文。

### Gateway 作为唯一发现源——为什么客户端不负责发现？

核心架构目标把所有网络广播和发现逻辑放在 Node Gateway 进程内，客户端应用纯粹作为消费者。Gateway 负责广播自己的端点，客户端只负责浏览和选择。

这跟微服务里的 service mesh 是一个思路——sidecar proxy 负责所有网络发现，应用进程只关心业务逻辑。客户端不维护发现状态，减少状态不一致的可能。一个进程既是服务发现的广播源，又是请求路由的网关。

### 双传输的互补设计——为什么需要直连 WS 和 SSH？

直连 WebSocket 和 SSH 不是二选一，而是互补：

- **直连 WS**：本地或 tailnet 环境下体验最优，自动局域网发现，gateway 管理 ACL，不需要 shell 访问
- **SSH**：万能备份，跨不同网络工作，绕过多播复杂性，不需要额外开放端口

这跟 CDN 加回源策略是一个思路——CDN 优先提供低延迟服务，不可用时回源到 origin server。双传输保证了局域网的即插即用体验和跨网络的可靠连接。

### 传输选择的确定性优先级——为什么不能并行尝试？

客户端选择传输时遵循确定性优先级链：

1. 已知直连端点
2. 发现的本地 gateway
3. tailnet 直连
4. SSH 回退

每一步都有明确的触发条件。优先级高的成功就不再尝试后续路径。

这跟 DNS 解析链是一个思路——hosts 文件优先于 DNS 查询，DNS 查询优先于默认网关。确定性顺序防止"不知道走哪条路"的歧义。

### Bonjour 的动态特性——为什么优于静态 DNS SRV？

传统 DNS SRV 记录是静态配置，服务地址变化时需要手动更新。OpenClaw 的发现机制是动态的——Gateway 启动时广播端点，停止时广播消失，客户端自动感知变化。

这跟 Consul 的动态服务注册是一个思路——服务实例的上下线实时反映在目录中，不需要人工干预。区别在于 Bonjour 基于多播限于单网络，广域场景需要 DNS-SD 补充。

---

OpenClaw addresses two seemingly similar challenges: remotely controlling a gateway through a macOS menu bar app, and secure pairing for mobile or future nodes. The core architectural goal places all network broadcasting and discovery logic inside the **Node Gateway** process, with client applications acting purely as consumers.

OpenClaw 解决两个看似类似的挑战：通过 macOS 菜单栏应用远程控制 gateway，以及移动或未来节点的安全配对。核心架构目标把所有网络广播和发现逻辑放在 **Node Gateway** 进程内，客户端应用纯粹作为消费者。

## 术语 / Terminology

- **Gateway**: A persistent process that manages sessions, node registry, pairing, and runs channels. Typically one per host
- **Gateway WS (control plane)**: The default WebSocket interface, listening on `127.0.0.1:18789`, which can be exposed to the local or tailnet network
- **Direct WS transport**: A network-facing WebSocket connection that bypasses SSH
- **SSH transport (fallback)**: A remote connection method that forwards the local gateway port through an SSH tunnel
- **Legacy TCP bridge (removed)**: The old node communication method, **no longer broadcast for discovery**, excluded from modern versions

- **Gateway**：持久进程，管理 sessions、节点注册表、配对，运行 channels。通常每台主机一个
- **Gateway WS (control plane)**：默认 WebSocket 接口，监听 `127.0.0.1:18789`，可暴露到本地或 tailnet 网络
- **Direct WS 传输**：面向网络的 WebSocket 连接，绕过 SSH
- **SSH 传输 (fallback)**：远程连接方法，通过 SSH 隧道转发本地 gateway 端口
- **Legacy TCP bridge (removed)**：旧的节点通信方法，**不再被广播用于发现**，从现代版本排除

## 双传输方式的原因 / Why Two Transports

Direct WebSocket provides the best user experience in local or tailnet environments: automatic LAN discovery, gateway-managed ACL, and no need for shell access. SSH serves as a universal backup: it works across different networks, bypasses multicast complexity, and requires no additional open ports.

Direct WebSocket 在本地或 tailnet 环境提供最佳用户体验：自动局域网发现、gateway 管理的 ACL、不需要 shell 访问。SSH 作为通用备份：跨不同网络工作、绕过多播复杂性、不需要额外开放端口。

## 发现机制 / Discovery Mechanisms

### Bonjour 和 DNS-SD

Multicast Bonjour works best-effort within a single network. The system supports wide-area DNS-SD domains for broader coverage, including the local network and configured unicast domains. The Gateway broadcasts its WebSocket endpoint using a bundled plugin—auto-started on macOS, requiring manual activation elsewhere. Clients browse these beacons to select and store endpoints.

多播 Bonjour 在单个网络内尽力工作。系统支持广域 DNS-SD 域以获得更广覆盖，包括本地网络和配置的单播域。Gateway 用捆绑插件广播 WebSocket 端点——在 macOS 上自动启动，其他地方需要手动激活。客户端浏览这些信标来选择并存储端点。

#### Beacon 规格 / Beacon Specification

The system broadcasts with the `_openclaw-gw._tcp` service type. Non-secret TXT records include:
- Role and transport identifier set to "gateway"
- User-defined `displayName`
- Network hints: `lanHost`, `tailnetDns`
- Port configuration: `gatewayPort`, `canvasPort`
- TLS indicator (`gatewayTls`) and fingerprint (`gatewayTlsSha256`, when encryption is active)
- SSH port and CLI path details (mainly in full mDNS mode)

系统用 `_openclaw-gw._tcp` 服务类型广播。非秘密 TXT 记录包括：
- 角色和传输标识符设为 "gateway"
- 用户定义的 `displayName`
- 网络提示：`lanHost`、`tailnetDns`
- 端口配置：`gatewayPort`、`canvasPort`
- TLS 指示器（`gatewayTls`）和指纹（`gatewayTlsSha256`，加密激活时）
- SSH 端口和 CLI 路径详情（主要在完整 mDNS 模式）

#### 安全考虑 / Security Considerations

mDNS records **lack authentication**, and clients must treat them as UX hints. Routing decisions should prefer resolved service endpoints over TXT record values. TLS pinning routines must prevent broadcast fingerprints from overriding stored pins; mobile nodes require explicit out-of-band verification before trusting a new fingerprint on a secure route.

mDNS 记录**缺乏认证**，客户端必须把它们视为 UX 提示。路由决策应优先使用已解析的服务端点而非 TXT 记录值。TLS 固定程序必须防止广播的指纹覆盖已存储的 pin 值，移动节点在信任安全路由上的新指纹前需要显式的带外验证。

### Tailnet 集成 / Tailnet Integration

For cross-network deployments, Tailscale MagicDNS names are preferred over static IPs to handle dynamic address changes. If detected, the Gateway publishes these DNS hints to clients. Mobile nodes maintain strict transport security on public or tailnet routes, requiring a secure connection path (WSS or Tailscale Serve), and prohibiting plaintext remote WebSocket connections outside private LANs.

跨网络部署时，Tailscale MagicDNS 名优于静态 IP，以处理动态地址变化。如果检测到，Gateway 会把这些 DNS 提示发布给客户端。移动节点在公网或 tailnet 路由上保持严格传输安全，需要安全连接路径（WSS 或 Tailscale Serve），禁止私有局域网外的明文远程 WebSocket 连接。

### 手动和 SSH 目标 / Manual and SSH Targets

When a direct route is unavailable or disabled, the client defaults to establishing an SSH tunnel that forwards the loopback gateway port.

直连路由不可用或禁用时，客户端默认建立 SSH 隧道转发 loopback gateway 端口。

## 客户端传输选择策略

The client evaluates connections in the following order:
1. Use a known, reachable direct endpoint
2. Accept a local or wide-area gateway discovered through user prompts
3. Attempt a direct secure connection using a configured tailnet address
4. Fall back to an SSH tunnel as the last resort

客户端按以下顺序评估连接：
1. 使用已知、可达的直连端点
2. 接受通过用户提示发现的本地或广域 gateway
3. 尝试使用配置的 tailnet 地址的直连安全连接
4. 回退到 SSH 隧道作为最终方案

## 认证与配对 / Authentication and Pairing

The Gateway is the ultimate authority for node and client admission. It manages pairing requests, enforces authentication, access controls, and rate limiting, ensuring it operates as a controlled gateway rather than a simple proxy.

Gateway 是节点和客户端准入的最终权威。它管理配对请求，强制认证、访问控制、速率限制，确保它作为受控 gateway 而非简单代理。

## 组件职责 / Component Responsibilities

- **Gateway**: Broadcasts beacons, manages pairing, hosts the WebSocket interface
- **macOS app**: Facilitates gateway selection, handles pairing prompts, uses SSH as backup
- **Mobile nodes**: Use Bonjour for convenience, but connect through paired WebSocket endpoints

- **Gateway**：广播信标，管理配对，托管 WebSocket 接口
- **macOS 应用**：促进 gateway 选择，处理配对提示，使用 SSH 作为备份
- **移动节点**：使用 Bonjour 获得便利，但通过已配对的 WebSocket 端点连接
