# `openclaw webhooks`

## 架构精读

> 跳过不影响阅读翻译正文。

### Webhook 管理——为什么需要专门的命令？

`openclaw webhooks` 管理入站 webhook（外部系统触发事件）：

- **`webhooks list`**：列出已配置 webhook（URL + 事件类型）
- **`webhooks add <url> <events>`**：添加 webhook
- **`webhooks remove <id>`**：删除 webhook
- **`webhooks test <id>`**：发送测试事件

这跟 GitHub webhook 管理是一个思路——注册 URL + 事件类型，外部系统发送 POST 请求触发内部操作。

### Webhook vs 轮询——为什么用推送？

- **轮询**：客户端定期查询"有新事件吗？"（浪费资源）
- **Webhook**：服务器有新事件时主动推送（高效）

这跟 WebSocket vs HTTP 轮询是一个思路——推送（WebSocket/webhook）比轮询更高效（不需要定期查询），但需要服务器支持长连接或回调 URL。

---

Manages inbound webhooks (external system event triggers): `webhooks list` (URL + event types), `webhooks add <url> <events>`, `webhooks remove <id>`, `webhooks test <id>` (send test event). Webhooks use push model (server pushes on new events) rather than polling (client periodically queries).

管理入站 webhook（外部系统事件触发）：`webhooks list`（URL + 事件类型）、`webhooks add <url> <events>`、`webhooks remove <id>`、`webhooks test <id>`（发送测试事件）。Webhook 用推送模型（服务器有新事件时推送），而非轮询（客户端定期查询）。
