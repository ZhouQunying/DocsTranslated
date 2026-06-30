# `openclaw acp`

## 架构精读

> 跳过不影响阅读翻译正文。

### 智能体通信协议——为什么需要专门的命令？

`openclaw acp` 管理智能体通信协议（智能体间通信协议）：

- **`acp status`**：查看 ACP 连接状态
- **`acp peers`**：列出已连接的对端智能体
- **`acp send <peer> <message>`**：发送消息到对端

这跟 MQTT 的 `mosquitto_pub` / `mosquitto_sub` 是一个思路——消息协议的发布/订阅操作。ACP 让多个智能体互相通信（如"智能体 A 请求智能体 B 帮忙分析数据"）。

### ACP vs 直接调用——为什么用协议？

- **直接调用**：智能体 A 直接调用智能体 B 的 API（紧耦合）
- **ACP**：智能体 A 通过协议发送消息（松耦合）

这跟 REST API vs 消息队列是一个思路——REST 是同步调用（紧耦合），消息队列是异步通信（松耦合）。ACP 适合"智能体 B 可能离线"的场景。

---

Manages Agent Communication Protocol (inter-agent messaging): `acp status` (connection state), `acp peers` (connected peers), `acp send <peer> <message>`. ACP uses protocol-based messaging (loose coupling) rather than direct API calls (tight coupling).

管理 Agent Communication Protocol（智能体间消息传递）：`acp status`（连接状态）、`acp peers`（已连接对端）、`acp send <peer> <message>`。ACP 用协议消息（松耦合），而非直接 API 调用（紧耦合）。
