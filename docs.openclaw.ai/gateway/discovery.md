# Discovery and Transports

OpenClaw 解决两个看似类似的挑战: 通过 macOS 菜单栏应用远程控制 gateway,以及移动或未来节点的安全配对。核心架构目标把所有网络广播和发现逻辑放在 **Node Gateway** 进程内,客户端应用纯粹作为消费者。

> **类比:DNS + SRV records。** DNS 用 SRV records 让客户端发现服务的地址和端口。OpenClaw 的发现机制类似: Gateway 通过 Bonjour (mDNS) 或 DNS-SD 广播自己的 WebSocket endpoint,客户端浏览这些 beacon 选择 endpoint。区别: DNS SRV records 是静态配置,OpenClaw 的发现是动态的(Gateway 启动时广播,停止时消失)。
>
> **架构要点:** 两种传输方式: Direct WS (本地/tailnet 最佳体验,自动 LAN 发现,Gateway 管理 ACL) 和 SSH (万能备份,跨网络,不需要额外端口);发现机制: Bonjour (mDNS best-effort 单网络) + 广域 DNS-SD (跨网络);客户端传输选择策略: 已知直连 → 发现本地 → tailnet → SSH fallback;Gateway 是成员资格的权威来源,不是简单 proxy。

## 术语

- **Gateway**: 持久进程,管理 sessions、节点注册表、配对,运行 channels。通常每台主机一个
- **Gateway WS (control plane)**: 默认 WebSocket 接口,监听 `127.0.0.1:18789`,可暴露到本地或 tailnet 网络
- **Direct WS 传输**: 面向网络的 WebSocket 连接,绕过 SSH
- **SSH 传输 (fallback)**: 远程连接方法,通过 SSH tunnel 转发本地 gateway 端口
- **Legacy TCP bridge (removed)**: 旧的节点通信方法,**不再被广播用于发现**,从现代版本排除

## 双传输方式的原因

Direct WebSocket 在本地或 tailnet 环境提供最佳用户体验: 自动 LAN 发现、gateway-managed ACL、不需要 shell 访问。SSH 作为通用备份: 跨不同网络工作、绕过 multicast 复杂性、不需要额外开放端口。

## 发现机制

### Bonjour 和 DNS-SD

Multicast Bonjour 在单个网络内 best-effort 工作。系统支持广域 DNS-SD domains 以获得更广覆盖,包括本地网络和配置的 unicast domains。Gateway 用 bundled plugin 广播 WebSocket endpoint,在 macOS 上自动启动,其他地方需要手动激活。客户端浏览这些 beacon 选择并存储 endpoint。

#### Beacon 规格

系统用 `_openclaw-gw._tcp` 服务类型广播。非秘密 TXT records 包括:
- Role 和传输标识符设为 "gateway"
- 用户定义的 `displayName`
- 网络提示: `lanHost`、`tailnetDns`
- 端口配置: `gatewayPort`、`canvasPort`
- TLS 指示器 (`gatewayTls`) 和指纹 (`gatewayTlsSha256`,加密激活时)
- SSH 端口和 CLI 路径详情(主要在完整 mDNS 模式)

#### 安全考虑

mDNS records **缺乏认证**,客户端必须把它们视为 UX 提示。路由决策应优先使用解析的服务 endpoint 而非 TXT record 值。TLS pinning 程序必须防止广播的指纹覆盖存储的 pins,移动节点在信任安全路由上的新指纹前需要显式 out-of-band 验证。

### Tailnet 集成

跨网络部署时,Tailscale MagicDNS 名优于静态 IP,以处理动态地址变化。如果检测到,Gateway 发布这些 DNS hints 给客户端。移动节点在公网或 tailnet 路由上保持严格传输安全,需要安全连接路径(WSS 或 Tailscale Serve),禁止私有 LAN 外的明文远程 WebSocket 连接。

### 手动和 SSH 目标

直连路由不可用或禁用时,客户端默认建立 SSH tunnel 转发 loopback gateway 端口。

## 客户端传输选择策略

客户端按以下顺序评估连接:
1. 使用已知、可达的直连 endpoint
2. 接受通过用户提示发现的本地或广域 gateway
3. 尝试使用配置的 tailnet 地址的直连安全连接
4. 回退到 SSH tunnel 作为最终方案

## 认证与配对

Gateway 是节点和客户端准入的最终权威。它管理配对请求,强制认证、access scopes、rate limiting,确保它作为受控 gateway 而非简单 proxy。

## 组件职责

- **Gateway**: 广播 beacons,管理配对,托管 WebSocket 接口
- **macOS app**: 促进 gateway 选择,处理配对提示,使用 SSH 作为备份
- **移动节点**: 使用 Bonjour 获得便利,但通过配对的 WebSocket endpoint 连接
