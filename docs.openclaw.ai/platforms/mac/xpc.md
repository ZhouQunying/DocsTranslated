# macOS IPC

## 架构精读

> 跳过不影响阅读翻译正文。

### Unix socket——本地进程间通信的标准选择

macOS app 和 node host service(运行在同一台机器上的两个进程)之间用 **Unix Domain Socket (UDS)** 通信。UDS 是 Unix/Linux/macOS 系统提供的本地进程间通信机制,通过文件路径(如 `/tmp/openclaw.sock`)建立连接,不走网络栈。

**为什么用 UDS 而不是 TCP?** TCP loopback(`127.0.0.1`)也可以本地通信,但有几个问题:
- 需要分配端口(可能跟其他服务冲突)
- 需要配置防火墙(即使是本地端口)
- 没有内置的访问控制(任何能访问 `127.0.0.1` 的进程都能连)

UDS 用文件路径,**文件系统权限就是访问控制**。`/tmp/openclaw.sock` 的权限设为 `0600`(只有 owner 能读写),其他用户/进程就访问不了。延迟也更低——不需要 TCP 的三次握手。

OpenClaw 选择 UDS 是因为**简单且安全**: 不需要端口管理,不需要防火墙配置,权限由文件系统控制。

### Gateway + node transport——协议独立于传输层

Gateway 和 node 之间的传输层可能是 WebSocket 或 Unix socket,取决于 node 是本地还是远程:
- **本地 node**(如 macOS app、CLI node host): 用 Unix socket,延迟低、权限可控
- **远程 node**(如 Android app、iOS app、远程 CLI): 用 WebSocket(需要 wss:// 加密)

**为什么这样设计?** 因为 node 协议(定义 node 能做什么、Gateway 怎么调用)不应该绑定到特定传输层。协议独立于传输 = **可以灵活部署**: 本地部署用 UDS,远程部署用 WebSocket,协议代码不用改。

这跟 HTTP 协议独立于传输层是一个思路——HTTP 可以跑在 TCP、TLS、QUIC 上,HTTP 协议本身不关心底层传输。OpenClaw 的 node 协议也是这样: 可以跑在 UDS、WebSocket 上,协议不关心传输。

### PeekabooBridge 的 UI automation——进程隔离 = 安全边界

PeekabooBridge 是独立的 UI automation 进程,通过 IPC(进程间通信,这里用 Unix socket)和 app 通信。这不是代码组织的选择,而是**安全边界**。

**为什么独立进程?** UI automation 进程有高权限(Accessibility 权限可以控制其他 app、Screen Recording 权限可以录屏)。如果 agent 代码能直接访问 Peekaboo 的进程内存,就能绕过权限检查执行任意 UI 操作(如读取其他 app 的密码、录制屏幕上的敏感信息)。

把高权限 broker 放在独立进程,agent 只能通过 IPC 协议通信(IPC 协议定义了允许的操作,如"点击这个按钮"、"读取这个文本"),即使 agent 代码被攻破,攻击者也受限于 IPC 协议的能力边界——不能直接读内存、不能执行协议外的操作。

这跟 Chrome 的多进程架构是一个思路——Chrome 的 renderer 进程沙盒化(只能渲染网页,不能访问文件系统),即使渲染的网页有恶意代码,也逃不出 renderer 进程。Peekaboo 的独立进程也是沙盒——高权限操作被限制在 broker 进程内,agent 进程没有这些权限。
