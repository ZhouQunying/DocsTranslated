# Bonjour Discovery

平台利用 multicast DNS 和服务发现协议在本地网络上定位活跃的 WebSocket endpoints。集成 plugin 处理本地广播,在 macOS 主机上自动激活,在其他操作系统或容器化环境中需要手动设置。远程连接时,Tailscale 上的 unicast 发现提供类似功能。此机制是补充工具,不是直连 SSH 或 tailnet 链接的替代品。

> **类比:mDNS 版的 etcd 服务发现。** etcd 让服务注册自己的地址,客户端查询 etcd 发现服务。Bonjour 类似但更轻: Gateway 在本地网络上广播自己的地址,客户端浏览发现。区别: Bonjour 是 multicast 不能跨子网,etcd 是 unicast 可以跨网络。OpenClaw 补充了广域 DNS-SD 以解决跨网络问题。
>
> **架构要点:** 服务类型 `_openclaw-gw._tcp`;TXT records 是非认证 UX hints,不能作为权威路由;TLS 指纹不能覆盖存储的 pins;macOS 自动激活 plugin,容器内自动抑制(bridge 网络通常阻止 multicast);multicast 不能跨子网,跨网络需要 Tailnet 或 SSH;广域 unicast 通过 CoreDNS 在 tailnet 接口上运行。

## 广域 unicast 设置

设备跨多个网络时,multicast 流量失败。管理员可以通过在主机上运行 DNS server,在自定义 zone (如 `openclaw.internal.`) 下发布 records,在 Tailscale 控制台内配置 split DNS 路由来部署 unicast 发现。

配置步骤:
- 设置 gateway 绑定到 tailnet,在 JSON 设置中启用广域发布
- 单个命令安装 CoreDNS,在 tailnet 接口上独占监听端口 53
- 验证使用标准 lookup 工具指向 tailnet IPv4 地址
- 默认 WebSocket 端口 (18789) 初始绑定到 loopback 接口,tailnet-only 部署需要显式绑定配置

## 服务标识符和元数据

系统广播 `_openclaw-gw._tcp` 指示 gateway 传输。还共享非认证元数据 hints 以简化 UI,包括设备 roles、友好名、本地主机名、端口号、TLS 状态、SHA256 指纹、以及可选的 SSH 或 CLI 工具路径。

安全: **客户端不能把 TXT 视为权威路由**。设备必须依赖解析的服务 endpoint 而非元数据 hints。广播的 TLS 指纹不能覆盖之前存储的 pins,移动节点首次连接需要显式用户批准。

## 调试与日志

- **macOS**: 管理员可以用内置命令行工具浏览和解析实例
- **Gateway 日志**: 系统维护持续日志文件,包含广播错误、ciao 看门狗干预、命名冲突的特定前缀。如果服务在多次重试后仍未达到已宣布状态,系统禁用该进程的 broadcaster。无效系统主机名触发 fallback 到默认本地 domain,可通过环境变量覆盖
- **iOS**: 移动节点使用特定网络浏览器框架,debug 日志可通过高级设置菜单访问

## Plugin 管理和环境变量

广播行为通过 plugin 命令或环境变量控制。默认元数据模式是 minimal,可扩展为包含 CLI 和 SSH 路径,或完全关闭以抑制 multicast 同时保留广域发布。

- 设置特定环境变量为 truthy 值禁用本地 multicast 但不改变 plugin 设置
- 设置为 falsy 值强制广播,即使在容器内

## 容器考虑

Plugin 在检测到的容器内自动抑制本地 multicast,因为 bridge 网络通常阻止所需流量。禁用 plugin 不改变 gateway 网络绑定或影响广域 unicast 能力。容器部署后本地发现失败时,用户应验证环境配置、直接检查 health endpoint、fallback 到显式 IP 地址、MagicDNS 或 SSH tunnels。

## 常见故障模式

- **网络边界**: Multicast 不能跨子网;使用 Tailnet 或 SSH
- **被阻止的流量**: 某些 Wi-Fi 环境丢弃 multicast 包
- **卡住状态**: 接口变化或被阻止的流量可能让 broadcaster 困在 probing 状态,最终导致自动禁用
- **解析错误**: 如果浏览成功但解析失败,通过移除 emojis 或标点简化机器名,然后重启服务
- **转义字符**: 协议用十进制序列转义服务实例名中的字节,UI 必须正确解码
