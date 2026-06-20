# macOS IPC

## 架构精读

> 跳过不影响阅读翻译正文。

### Unix socket 连接 node host service 和 app——本地 IPC 的标准选择

macOS app 和 node host service 之间用 **Unix Domain Socket (UDS)** 通信。这跟 gRPC 的 Unix socket 传输是一个思路——本地进程间通信不走网络栈，延迟低（无 TCP 握手）、安全性高（文件系统权限控制访问）。

UDS 的选择不是随意的。TCP loopback（`127.0.0.1`）也可以本地通信，但需要分配端口、处理端口冲突、配置防火墙。UDS 用文件路径（如 `/tmp/openclaw.sock`），文件系统权限就是访问控制。OpenClaw 选择 UDS 是因为**简单且安全**。

### Gateway + node transport——跨进程通信

Gateway 和 node 之间的 transport 可能是 WebSocket 或 Unix socket，取决于 node 是本地还是远程。这跟 gRPC 的 transport 抽象是一个思路——gRPC 可以用 HTTP/2、Unix socket、in-process，业务逻辑不关心 transport。OpenClaw 也是这样：node 协议不依赖特定 transport，本地用 UDS，远程用 WebSocket。

### PeekabooBridge 的 UI automation——进程隔离 = 安全边界

PeekabooBridge 是独立的 UI automation 进程，通过 IPC 和 app 通信。这不是代码组织的选择，而是**安全边界**。UI automation 进程有高权限（Accessibility、Screen Recording），如果 agent 代码能直接访问 Peekaboo 的进程内存，就能绕过权限检查执行任意 UI 操作。把高权限 broker 放在独立进程，agent 只能通过 IPC 协议通信，即使 agent 代码被攻破，攻击者也受限于 IPC 协议的能力边界。

这跟 Chrome 的多进程架构是一个思路。Chrome 的 renderer 进程沙盒化，即使渲染的网页有恶意代码，也逃不出 renderer 进程。Peekaboo 的独立进程也是沙盒——高权限操作被限制在 broker 进程内，agent 进程没有这些权限。
