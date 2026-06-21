# Bridge Protocol

> **类比:已被 HTTP/2 取代的 HTTP/1.0 专有扩展。** Bridge Protocol 是 OpenClaw 早期的 TCP 节点通信协议,功能已被 WebSocket Gateway Protocol 完全吸收,现代版本彻底删除了 TCP listener 和相关配置。理解它的意义在于理解为什么 WebSocket 协议是更好的选择。
>
> **架构要点:** Bridge 的核心设计理念——受限函数白名单而非完整 API、设备 token 认证、本地发现——都被 WebSocket 协议以更灵活的方式继承。Bridge 的局限(无版本协商、TLS 可选且不可验证、LAN 发现不可跨网络)直接驱动了 WebSocket 协议的设计。

Bridge Protocol 是 OpenClaw 的**前身节点通信协议**,通过 TCP 端口 18790 传输线分隔 JSON。现代版本已完全移除,配置 schema 中的 `bridge.*` 命名空间也被删除。

## 设计目标

Bridge 试图解决四个问题:

- **受限访问**: 提供小函数白名单而非完整 API,作为安全边界
- **设备身份**: Gateway 管理设备 token 准入
- **本地发现**: 支持 LAN 发现和 tailnet 直连
- **流量隔离**: WebSocket 控制平面限制在 loopback,除非用 SSH tunnel

这些目标在 WebSocket 协议中都有更好的实现。角色/作用域分层替代了函数白名单,设备配对流程替代了简单的 token 准入,Bonjour 发现替代了 mDNS,WS 长连接替代了 TCP + 可选 TLS。

## 传输与发现

TCP 传输线分隔 JSON,默认端口 18790。TLS 可选,启用后发现记录包含 TLS 标志和 SHA-256 指纹提示。文档明确警告本地发现记录是**未认证的**,客户端不能把广播的指纹当作权威 pin——必须通过外部渠道验证。

网络绑定方面,tailnet 配置可以通过 JSON 设置绑定特定网络 IP,客户端用 MagicDNS 名或直连 IP。Bonjour 不能跨网络,远程访问需要手动配置或广域 DNS-SD。

## 握手与配对

连接流程:

1. 客户端发送 hello 消息(设备元数据 + 已有 token)
2. 未注册设备收到错误
3. 客户端发送 pair-request
4. 管理员批准后,Gateway 回复配对和初始确认

后期版本用 plugin surface URLs 替代了 server name,把 Canvas 和 A2UI 流量路由到 canvas endpoint。

## 消息帧

**上行(客户端→Gateway)**:
- Request/Response: scoped RPC (chat、config、health、skills)
- Event: 节点信号(语音转录、执行生命周期)

**下行(Gateway→客户端)**:
- Invoke: 硬件命令(摄像头、屏幕、SMS)
- Event: 聊天更新
- Ping/Pong: 保活

## 执行生命周期

设备广播 `exec.finished` 通知系统命令完成,Gateway 映射为内部系统事件。旧版本还广播 `exec.started`。被阻止的命令触发 `exec.denied`,Gateway 视为终态,不触发后续 agent 任务。

Payload 必须包含 session key,可选字段包括 run identifier、`system.run` 命令字符串、exit code、timeout、output text。Denial payload 包含 reason 字段。

## 为什么被取代

Bridge 作为隐式第一版协议,没有版本协商机制(min/maxProtocol)。它的核心局限:

- **TLS 可选且不可验证**: 发现记录的指纹提示不能被信任
- **LAN 发现不可跨网络**: 需要手动配置或广域 DNS-SD
- **函数白名单太粗糙**: 不如角色/作用域分层灵活
- **无能力协商**: 节点不能声明 caps/commands/permissions

WebSocket 协议解决了所有这些: 强制 WS 安全、Bonjour + tailnet 发现、角色/作用域细粒度权限、connect 握手时完整的能力协商。
