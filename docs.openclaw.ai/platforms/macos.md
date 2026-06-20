# macOS app / macOS 应用

## 架构精读

> 跳过不影响阅读翻译正文。

### Local vs Remote 模式——minikube vs 远程集群

macOS app 有两种运行模式：
- **Local**（默认）：app 连接本地 Gateway，如果本地没有就启动一个
- **Remote**：app 通过 SSH/Tailscale 连接远程 Gateway，本地不起进程

这跟 Kubernetes 的本地开发 vs 远程集群是一个思路。minikube/kind 在本地跑一个完整集群，适合开发调试。远程集群（EKS/GKE）适合生产环境，本地 kubectl 只是客户端。OpenClaw 的 macOS app 也是这样：Local 模式适合个人使用，Remote 模式适合连接到服务器上的 Gateway。

Remote 模式的巧妙设计是**自动启动本地 node host service**。这样远程 Gateway 可以把这台 Mac 当作一个 node 来用——调用它的 Canvas、Camera、Screen Recording 等 macOS 特有能力。这跟 Kubernetes 的 node registration 是一个思路：node 向 control plane 注册自己，control plane 就可以调度任务到它。

### system.run 的三层安全栈——deny/ask/allowlist

macOS app 的 `system.run`（agent 执行系统命令）有三层安全控制：
1. **security**：`deny`（全禁）、`allowlist`（白名单）、`ask`（每次问）
2. **ask**：`on-miss`（不在白名单时问）、`always`（每次都问）、`never`（从不问）
3. **allowlist**：glob 模式匹配已解析的二进制路径

这跟 AWS IAM 的三层策略是一个思路。IAM 有 explicit deny > allow > implicit deny 的优先级。OpenClaw 的 system.run 也是这样：deny 是默认，allowlist 是显式放行，ask 是兜底。

一个精妙细节：**包含 shell 控制字符（`&&`、`||`、`;`、`|`、`$` 等）的命令自动算 allowlist miss**。即使命令本身在白名单里，如果带了管道或重定向，也必须显式批准。这防止了"允许 rg 搜索"变成"允许 `rg; rm -rf /`"的逃逸。

### TCC 权限管理——macOS 的沙盒合规

macOS app "owns" TCC（Transparency, Consent, and Control）提示——Notifications、Accessibility、Screen Recording、Microphone、Speech Recognition、Automation/AppleScript。这意味着用户授权这些权限给 macOS app，而不是给 Gateway 进程。

这跟 iOS 的沙盒模型是一个思路。iOS app 必须显式请求相机、位置、通知等权限。macOS 的 TCC 是同样的模型，只是粒度更粗。OpenClaw 的 macOS app 把这些权限统一管理，agent 通过 node 协议访问，而不是直接调 macOS API。

### IPC 架构——UDS + token + HMAC + TTL

macOS app 和 node host service 之间通过 Unix Domain Socket (UDS) 通信，安全机制包括 token、HMAC 和 TTL。这跟 gRPC 的 Unix socket 传输是一个思路——本地进程间通信不走网络栈，延迟低、安全性高（文件系统权限控制访问）。

HMAC 防篡改，TTL 防重放攻击。即使攻击者抓到了 IPC 消息，也不能重放（TTL 过期）或篡改（HMAC 校验失败）。这是 defense in depth——多层安全机制，每层防不同类型的攻击。
