# Bonjour Discovery——本地服务发现

## 架构精读

> 跳过不影响阅读翻译正文。

### mDNS 替代集中式注册——为什么不需要 etcd？

传统服务发现依赖中心节点：服务启动后向 etcd 注册自己的地址，客户端查询 etcd 获取服务列表。OpenClaw 用 mDNS 省去了这个中心——Gateway 直接在本地网络广播自己的地址，客户端只需浏览就能发现。

这跟 etcd 服务注册是一个思路，但更轻量。区别在于 mDNS 是多播，不能跨子网；etcd 是单播，可以跨网络。OpenClaw 在 tailnet 上补充了 DNS-SD 来解决跨网络发现。

### TXT 记录的非权威设计——为什么元数据不能决定路由？

服务广播的 TXT 记录携带丰富的元数据（设备角色、TLS 指纹、友好名），但这些只是 UI 提示，不是路由依据。路由必须依赖 DNS 解析出的实际服务端点，而非 TXT 值。

这跟 HTTP `X-Forwarded-For` 的不可信设计类似——请求头 是提示，不是证据。恶意节点可以伪造 TXT 记录，如果客户端据此路由就会被劫持。广播的 TLS 指纹也不能覆盖已存储的 pin 值。

### 多播与单播的互补——本地发现和远程发现如何衔接？

发现机制分两层：

- **局域网**：mDNS 多播，零配置自动发现，但不能跨子网
- **跨网络**：tailnet 上的 DNS-SD 单播，覆盖广域

这跟 CDN 的边缘缓存加回源策略是一个思路——边缘优先，不可用时回源。多播优先尝试，失败后单播兜底，两者共享相同的服务类型和记录格式。

### 容器环境的自动抑制——为什么 bridge 网络是障碍？

Docker 的 bridge 网络默认阻断多播流量，Bonjour 在容器内无法工作。Plugin 检测到容器环境后自动禁用本地广播，但保留广域单播能力。

这跟健康检查的自适应降级是一个思路——检测到子系统不可用时主动关闭，避免无效重试。禁用本地广播不影响 Gateway 的网络绑定，广域发现仍然可用。

---

The platform uses multicast DNS and service discovery protocols to locate active WebSocket endpoints on the local network. An integration plugin handles local broadcast—automatically activated on macOS hosts, requiring manual setup on other operating systems or in containerized environments. For remote connections, unicast discovery over Tailscale provides equivalent functionality. This mechanism is a complementary tool, not a replacement for direct SSH or tailnet links.

平台利用多播 DNS 和服务发现协议在本地网络上定位活跃的 WebSocket 端点。集成插件处理本地广播——在 macOS 主机上自动激活，在其他操作系统或容器化环境中需要手动设置。远程连接时，Tailscale 上的单播发现提供类似功能。此机制是补充工具，不是直连 SSH 或 tailnet 链路的替代品。

## 广域单播设置 / Wide-Area Unicast Setup

When devices span multiple networks, multicast traffic fails. Administrators can deploy unicast discovery by running a DNS server on the host, publishing records under a custom zone (such as `openclaw.internal.`), and configuring split DNS routing within the Tailscale console.

设备跨多个网络时，多播流量会失败。管理员可以通过在主机上运行 DNS 服务器、在自定义域（如 `openclaw.internal.`）下发布记录、在 Tailscale 控制台内配置分割 DNS 路由来部署单播发现。

Configuration steps:
- Set the gateway to bind to the tailnet, enabling wide-area publishing in JSON settings
- Install CoreDNS with a single command, listening exclusively on port 53 at the tailnet interface
- Verify using standard lookup tools pointed at the tailnet IPv4 address
- The default WebSocket port (18789) initially binds to the loopback interface; tailnet-only deployments require explicit bind configuration

配置步骤：
- 设置 gateway 绑定到 tailnet，在 JSON 设置中启用广域发布
- 单个命令安装 CoreDNS，在 tailnet 接口上独占监听端口 53
- 验证使用标准查询工具指向 tailnet IPv4 地址
- 默认 WebSocket 端口 (18789) 初始绑定到 loopback 接口，tailnet-only 部署需要显式绑定配置

When local broadcast is unavailable, wide-area DNS-SD provides an alternative path. Multicast is tried first; when it fails, unicast takes over. Both share the same service type and record format.

当本地广播不可用时，广域 DNS-SD 提供备用路径。多播优先尝试，失败后单播接管。两者共享相同的服务类型和记录格式。

## 服务标识符和元数据 / Service Identifiers and Metadata

The system broadcasts `_openclaw-gw._tcp` to indicate the gateway transport. It also shares non-authenticated metadata hints to streamline the UI, including device roles, friendly names, local hostnames, port numbers, TLS status, SHA256 fingerprints, and optional SSH or CLI tool paths.

系统广播 `_openclaw-gw._tcp` 指示 gateway 传输。还共享非认证元数据提示以简化 UI，包括设备角色、友好名、本地主机名、端口号、TLS 状态、SHA256 指纹、以及可选的 SSH 或 CLI 工具路径。

Security: **Clients must not treat TXT records as authoritative routing**. Devices must rely on resolved service endpoints rather than metadata hints. Broadcast TLS fingerprints cannot override stored pins; mobile nodes require explicit user approval on first connection.

安全：**客户端不能把 TXT 记录视为权威路由**。设备必须依赖已解析的服务端点而非元数据提示。广播的 TLS 指纹不能覆盖已存储的 pin 值，移动节点首次连接需要显式用户批准。

## 调试与日志 / Debugging and Logging

- **macOS**: Administrators can use built-in command-line tools to browse and resolve instances
- **Gateway logs**: The system maintains a persistent log file with specific prefixes for broadcast errors, ciao watchdog interventions, and naming conflicts. If the service fails to reach announced state after multiple retries, the system disables the broadcaster for that process. Invalid system hostnames trigger a fallback to the default local domain, overridable via environment variable
- **iOS**: Mobile nodes use a specific network browser framework; debug logs are accessible via the advanced settings menu

- **macOS**：管理员可以用内置命令行工具浏览和解析实例
- **Gateway 日志**：系统维护持续日志文件，包含广播错误、ciao 守护进程干预、命名冲突的特定前缀。如果服务在多次重试后仍未达到已宣布状态，系统禁用该进程的广播器。无效的系统主机名触发回退到默认本地域，可通过环境变量覆盖
- **iOS**：移动节点使用特定网络浏览器框架，调试日志可通过高级设置菜单访问

## 插件管理和环境变量 / Plugin Management and Environment Variables

Broadcast behavior is controlled via plugin commands or environment variables. The default metadata mode is minimal; it can be extended to include CLI and SSH paths, or turned off entirely to suppress multicast while preserving wide-area publishing.

广播行为通过插件命令或环境变量控制。默认元数据模式是 minimal，可扩展为包含 CLI 和 SSH 路径，或完全关闭以抑制多播同时保留广域发布。

- Setting a specific environment variable to a truthy value disables local multicast without changing plugin settings
- Setting it to a falsy value forces broadcast, even inside containers

- 设置特定环境变量为 truthy 值禁用本地多播但不改变插件设置
- 设置为 falsy 值强制广播，即使在容器内

## 容器考虑 / Container Considerations

The plugin automatically suppresses local multicast when it detects a container environment, because bridge networks typically block the required traffic. Disabling the plugin does not change gateway network bindings or affect wide-area unicast capability. When local discovery fails after container deployment, users should verify environment configuration, check the health endpoint directly, and fall back to explicit IP addresses, MagicDNS, or SSH tunnels.

插件在检测到容器环境后自动抑制本地多播，因为桥接网络通常阻断所需流量。禁用插件不改变 gateway 网络绑定或影响广域单播能力。容器部署后本地发现失败时，用户应验证环境配置、直接检查健康端点、回退到显式 IP 地址、MagicDNS 或 SSH 隧道。

When local discovery is unavailable, wide-area unicast discovery remains available. Disabling local broadcast only stops announcing the service's own presence; it does not affect the ability to actively discover remote gateways.

当本地发现不可用时，广域单播发现仍然可用。禁用本地广播只是停止宣告自身存在，不影响主动发现远端 gateway 的能力。

## 常见故障模式 / Common Failure Modes

- **Network boundaries**: Multicast cannot cross subnets; use Tailnet or SSH
- **Blocked traffic**: Some Wi-Fi environments drop multicast packets
- **Stuck state**: Interface changes or blocked traffic may trap the broadcaster in a probing state, eventually leading to automatic disablement
- **Resolution errors**: If browsing succeeds but resolution fails, simplify the machine name by removing emojis or punctuation, then restart the service
- **Escaped characters**: The protocol escapes bytes in service instance names using decimal sequences; the UI must decode them correctly

- **网络边界**：多播不能跨子网；使用 Tailnet 或 SSH
- **被阻断的流量**：某些 Wi-Fi 环境丢弃多播包
- **卡住状态**：接口变化或被阻断的流量可能让广播器困在探测状态，最终导致自动禁用
- **解析错误**：如果浏览成功但解析失败，通过移除表情符号或标点简化机器名，然后重启服务
- **转义字符**：协议用十进制序列转义服务实例名中的字节，UI 必须正确解码
