# Android app / Android 应用

## 架构精读

> 跳过不影响阅读翻译正文。

### Companion Node——手机是 Gateway 的延伸

Android app 是 **companion node**，不托管 Gateway。它通过 WebSocket 连接 Gateway，把手机的传感器和能力（Canvas、Screen、Camera、Location、Talk mode）暴露给 agent。Gateway 是大脑，手机是感官和肢体。

这跟 IoT 的 MQTT 架构是一个思路。MQTT 中间件是中心，IoT 设备是 edge node，中间件调度命令到设备，设备上报数据到中间件。OpenClaw 的 Gateway-Android 关系也是这样：Gateway 调度 `camera.snap` 到 Android，Android 上报拍照结果到 Gateway。

### 服务发现的三层递进——mDNS → DNS-SD → 手动

Android 连接 Gateway 有三种服务发现方式：
1. **mDNS/NSD**：同一 LAN，自动发现
2. **Wide-Area Bonjour / unicast DNS-SD**：跨网络（如 Tailscale），需要配置 DNS 区域
3. **手动 host/port**：兜底方案

这跟微服务的服务发现是一个思路。Kubernetes 用 DNS + Service，Consul 用 DNS + HTTP API，Nacos 用 DNS + SDK。都是先自动发现，发现不了就手动配置。OpenClaw 也是这样：LAN 内 mDNS 自动发现，跨网络 DNS-SD，最后手动填地址。

### 远程连接的安全要求——wss:// 不是可选项

tailnet/公共主机的 Android 配对**不**使用原始 tailnet IP 的 `ws://` 端点，必须用 Tailscale Serve 或其他 `wss://` URL。明文 `ws://` 仅在私有 LAN 地址、`localhost`、`127.0.0.1`、Android 模拟器桥接（`10.0.2.2`）上允许。

这跟 gRPC 的 TLS 策略是一个思路。gRPC 默认要求 TLS，只有在明确标记为 insecure 时才允许明文。OpenClaw 也是这样：远程连接强制加密，本地连接允许明文。安全不是全局开关，而是**按场景分级**。

### Foreground Service——Android 的后台生存策略

Android app 用 **foreground service**（持久通知）保持 Gateway 连接。这是 Android 的后台限制下的生存策略——没有 foreground service，系统会在几分钟内杀掉后台进程。

这跟 iOS 的 background task 是一个思路。iOS 用 `beginBackgroundTask` 申请额外时间，Android 用 foreground service 保持进程存活。两个平台都在后台限制和用户体验之间找平衡。OpenClaw 的 Android app 选择了 foreground service——用户看到持久通知，知道 app 在运行，系统也不会杀掉它。
