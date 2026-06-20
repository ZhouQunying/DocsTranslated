# Health checks

## 架构精读

> 跳过不影响阅读翻译正文。

### /health 端点——专门给监控服务用

OpenClaw 提供专门的 `/health` 端点,给外部监控服务(如 UptimeRobot、Pingdom、Prometheus Blackbox Exporter)检查 Gateway 是否存活:

```bash
curl https://gateway.example.com/health
```

返回:
- **200 OK**: Gateway 正常运行
- **503 Service Unavailable**: Gateway 不可用

**为什么需要专门的 /health 端点?** 因为监控服务需要轻量级的健康检查,不应该:
- 调用 `/v1/chat/completions`(会消耗 LLM API 额度)
- 调用 `/v1/models`(可能返回大量数据)
- 做任何"真实"操作(如发消息、执行工具)

`/health` 端点只检查 Gateway 进程是否存活、是否能响应请求,不消耗任何 LLM 资源。

**这跟 Kubernetes 的 liveness probe 是一个思路**——Kubernetes 用 `/healthz` 或 `/livez` 检查 Pod 是否存活,不调用业务 API。OpenClaw 的 `/health` 也是同样: 轻量级健康检查,不消耗资源。

### Channel 连通性检查——不只是进程存活

Health check 不只检查"Gateway 进程在不在",还检查"channel 是否连通":

- **Discord**: 检查 WebSocket 连接是否正常(不是只检查 session 是否存在)
- **Slack**: 检查 Slack API 是否能响应
- **WhatsApp**: 检查 WhatsApp Web 连接状态

**为什么需要检查 channel 连通性?** 因为 Gateway 进程存活 ≠ channel 正常工作:
- Gateway 进程在,但 Discord WebSocket 断了 → 用户发消息 Gateway 收不到
- Gateway 进程在,但 Slack API token 过期了 → Gateway 发消息会失败
- Gateway 进程在,但 WhatsApp Web 断开了 → 用户发消息 Gateway 收不到

只检查进程存活 = 监控盲区。检查 channel 连通性 = 真正的"健康"。

**这跟数据库的健康检查**是一个思路——不只检查"数据库进程在不在",还检查"能不能执行查询"。OpenClaw 的 health check 也是同样: 不只检查进程,还检查 channel 连通性。

### Session 状态 ≠ socket 存活

文档强调: 对于 Discord 等 chat provider,**session 状态不等于 socket 存活**:
- Session 存在 → 数据库里有这个 session 的记录
- Socket 存活 → WebSocket 连接正常,能收发消息

**为什么强调这个?** 因为监控工具可能误判:
- 检查 session 列表 → 看到 session 存在 → 认为正常
- 但 WebSocket 已经断了 → 实际上不正常

正确的检查方式是检查 socket 状态,不是 session 列表。OpenClaw 的 `/health` 端点检查 socket 状态,不是 session 列表。

### 外部监控服务应该用 /health,不是 /v1/chat/completions

文档警告: 外部监控服务(UptimeRobot、Pingdom 等)应该用 `/health` 端点,**不**应该用 `/v1/chat/completions`。

**为什么?** 因为 `/v1/chat/completions` 会:
- 调用 LLM API,消耗额度
- 执行工具(如果 prompt 里有工具调用)
- 返回大量数据(完整的 LLM 响应)

监控服务每分钟调用一次 `/v1/chat/completions`,一天 1440 次,浪费大量 API 额度。`/health` 端点不调用 LLM,不消耗资源。

**这跟 API rate limiting 是一个思路**——健康检查不应该算进 rate limit,因为它不是"真实"请求。OpenClaw 的 `/health` 端点就是为监控设计的,不消耗 LLM 资源。
