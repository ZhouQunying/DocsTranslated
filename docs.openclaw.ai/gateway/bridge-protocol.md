# Bridge Protocol

## 架构精读

> 跳过不影响阅读翻译正文。

### 受限函数白名单——为什么用白名单而非完整 API？

Bridge 的核心安全边界是**函数白名单**而非完整 API 暴露：

- 客户端只能调用预定义的小函数集合（chat、config、health、skills）
- Gateway 侧有允许列表校验，未注册的函数直接拒绝

这跟 gRPC 的 service definition 是一个思路——服务端声明可调用的 RPC 方法，客户端只能调用已声明的方法。但函数白名单粒度太粗，后来被 WebSocket 协议的角色/作用域分层取代。角色定义"你是谁"，作用域定义"你能做什么"，粒度更细。

### TLS 可选且不可验证——为什么驱动了 WebSocket 强制安全？

Bridge 的 TLS 是**可选的**，发现记录包含 TLS 标志和 SHA-256 指纹提示（fingerprint hint），但文档明确警告：

> 本地发现记录是**未认证的**，客户端不能把广播的指纹当作权威 pin——必须通过外部渠道验证。

这跟 SSH 的 `known_hosts` 首次信任（TOFU）是一个思路——首次连接时记录的指纹不能被信任，需要通过其他渠道确认。Bridge 的这个设计局限直接驱动了 WebSocket 协议强制 `wss://` 的设计。

### 消息帧——上行与下行的非对称设计

Bridge 的消息帧分为两个方向：

**上行（客户端→Gateway）**：
- Request/Response：scoped RPC（chat、config、health、skills）
- Event：节点信号（语音转录、执行生命周期）

**下行（Gateway→客户端）**：
- Invoke：硬件命令（摄像头、屏幕、SMS）
- Event：聊天更新
- 心跳探测/响应：保活

这跟 gRPC 的 bidirectional streaming 是一个思路——上行是客户端发起的 RPC，下行是服务端推送的事件。Bridge 的帧类型是后来 WebSocket 协议 role-based 消息分类的前身。

### 四大局限——为什么 Bridge 必须被取代？

Bridge 作为隐式第一版协议，有四个核心局限：

| 局限 | Bridge | WebSocket 解决方案 |
|------|--------|-------------------|
| **安全** | TLS 可选且指纹不可验证 | 强制 `wss://` |
| **发现** | LAN 发现不可跨网络 | Bonjour + tailnet |
| **权限** | 函数白名单太粗糙 | 角色/作用域细粒度权限 |
| **能力** | 无协商机制 | connect 握手时完整能力声明 |

这跟 HTTP/1.0 到 HTTP/2 的演进是一个思路——HTTP/1.0 的各种专有扩展（如 SPDY）被 HTTP/2 的标准机制取代。Bridge 相当于 HTTP/1.0 的专有扩展，WebSocket 协议相当于 HTTP/2 的标准机制。

### 执行生命周期——exec 事件的状态机

Bridge 的执行生命周期通过三种事件管理：

- `exec.finished`：命令完成（必须包含 session key）
- `exec.started`：命令开始（旧版本）
- `exec.denied`：命令被阻止（Gateway 视为终态，不触发后续 agent 任务）

这跟 Kubernetes Job 的 status condition 是一个思路——Job 有 `Complete`、`Failed`、`Active` 状态，exec 事件有 `started`、`finished`、`denied` 状态。拒绝 payload 包含原因字段，让调用方知道为什么被拒绝。

---

Bridge Protocol was OpenClaw's original TCP node communication protocol, transmitting line-delimited JSON on port 18790. Modern versions have completely removed it, and the `bridge.*` configuration namespace has been deleted from the schema. Its core design principles — restricted function whitelist instead of full API, device token authentication, local discovery — were all inherited by the WebSocket protocol in a more flexible way.

Bridge Protocol 是 OpenClaw 早期的 TCP 节点通信协议，通过端口 18790 传输行分隔 JSON。现代版本已完全移除，配置 schema 中的 `bridge.*` 命名空间也被删除。它的核心设计理念——受限函数白名单而非完整 API、设备 token 认证、本地发现——都被 WebSocket 协议以更灵活的方式继承。

The protocol attempted to solve four problems: restricted access via a small function whitelist as a security boundary, device identity through gateway-managed token admission, local discovery supporting LAN and tailnet direct connection, and traffic isolation limiting the WebSocket control plane to loopback unless using SSH tunnels. All four goals have better implementations in the WebSocket protocol — role/scope layering replaces function whitelists, device pairing flows replace simple token admission, Bonjour discovery replaces mDNS, and persistent WS connections replace TCP with optional TLS.

该协议试图解决四个问题：受限访问、设备身份、本地发现和流量隔离。小函数白名单作为安全边界，Gateway 管理设备 token 准入，支持 LAN 和 tailnet 直连发现，WebSocket 控制平面限制在 loopback。这四个目标在 WebSocket 协议中都有更好的实现。角色/作用域分层替代函数白名单，设备配对替代 token 准入，Bonjour 发现替代 mDNS，WS 长连接替代 TCP 加可选 TLS。

The connection flow required clients to send a hello message with device metadata and existing token, unregistered devices received an error, clients then sent a pair-request, and upon admin approval the Gateway replied with pairing confirmation and initial acknowledgment. Later versions replaced server names with plugin surface URLs, routing Canvas and A2UI traffic to the canvas endpoint.

连接流程分四步。客户端发送包含设备元数据和已有 token 的 hello 消息，未注册设备收到错误。然后客户端发送 pair-request，管理员批准后 Gateway 回复配对确认。后期版本用 plugin surface URLs 替代了 server name，把 Canvas 和 A2UI 流量路由到 canvas endpoint。

Bridge's core limitations drove the WebSocket protocol design: TLS was optional and unverifiable (discovery record fingerprint hints could not be trusted), LAN discovery could not cross networks (requiring manual configuration or wide-area DNS-SD), function whitelists were too coarse (less flexible than role/scope layering), and there was no capability negotiation (nodes could not declare caps/commands/permissions). The WebSocket protocol addressed all of these: mandatory WS security, Bonjour + tailnet discovery, role/scope fine-grained permissions, and full capability negotiation during the connect handshake.

Bridge 的核心局限驱动了 WebSocket 协议的设计。TLS 可选且不可验证，发现记录的指纹提示不能被信任。LAN 发现不可跨网络，需要手动配置或广域 DNS-SD。函数白名单太粗糙，不如角色/作用域分层灵活。无能力协商，节点不能声明 caps/commands/permissions。WebSocket 协议解决了所有这些：强制 WS 安全、Bonjour 加 tailnet 发现、角色/作用域细粒度权限、connect 握手时完整能力协商。
