# `openclaw system`

## 架构精读

> 跳过不影响阅读翻译正文。

### 系统级辅助——为什么需要专门的命令？

`openclaw system` 提供网关系统级操作：

- **`system event`**：入队系统事件（下一次心跳插入对话）
- **`system heartbeat`**：控制心跳（启用/禁用/查看最近）
- **`system presence`**：查看活跃节点和实例

这跟 Linux 的 `sysctl` 是一个思路——系统级参数调整（内核参数/心跳配置），不影响应用层逻辑。

### 系统事件——为什么通过心跳注入？

`system event` 入队事件，下一次心跳时作为"System:"消息插入对话。不直接发送，而是等心跳周期。

这跟 syslog 的异步日志是一个思路——事件入队后异步处理，不阻塞当前操作。心跳注入确保事件在合适的时机出现（而非打断当前对话流）。

---

Gateway system-level operations: `system event` (queue events for heartbeat injection), `system heartbeat` (enable/disable/view last), `system presence` (active nodes and instances). Events inject as "System:" messages during heartbeat cycles.

网关系统级操作：`system event`（入队事件，心跳时注入）、`system heartbeat`（启用/禁用/查看最近）、`system presence`（活跃节点和实例）。事件在心跳周期作为"System:"消息注入。
