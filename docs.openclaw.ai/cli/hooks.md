# `openclaw hooks`

## 架构精读

> 跳过不影响阅读翻译正文。

### 生命周期钩子——为什么需要事件驱动？

`openclaw hooks` 管理生命周期钩子（事件 → 动作映射）：

- **`on_message`**：收到消息时触发（如日志记录、过滤）
- **`on_response`**：生成响应时触发（如后处理、审计）
- **`on_error`**：发生错误时触发（如告警、降级）

这跟 Kubernetes admission webhook 是一个思路——在关键节点插入自定义逻辑（验证、修改、审计），不需要修改核心代码。

### 钩子链——为什么支持多个钩子？

同一事件可以注册多个钩子，按优先级顺序执行：

这跟 Express middleware 的 `next()` 是一个思路——多个中间件按顺序执行，每个可以修改请求/响应或终止链。钩子链让多个关注点（日志、过滤、审计）独立组合。

---

Manages lifecycle hooks (event → action mappings): `on_message` (log/filter), `on_response` (post-process/audit), `on_error` (alert/fallback). Multiple hooks per event execute in priority order, like Express middleware chain.

管理生命周期钩子（事件 → 动作映射）：`on_message`（日志/过滤）、`on_response`（后处理/审计）、`on_error`（告警/降级）。同一事件多个钩子按优先级顺序执行，类似 Express 中间件链。
