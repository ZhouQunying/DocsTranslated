# Health checks

## 架构精读

> 跳过不影响阅读翻译正文。

### /health 端点

**问题**: 监控服务 (UptimeRobot、Pingdom) 需要轻量级健康检查,不应该调用 `/v1/chat/completions` (消耗 LLM API 额度)?

**方案**: 专门的 `/health` 端点:
```bash
curl https://gateway.example.com/health
```
返回:
- **200 OK**: Gateway 正常
- **503 Service Unavailable**: Gateway 不可用

**洞察**: `/health` 只检查进程是否存活,不消耗 LLM 资源。

**权衡**:
- ✓ 轻量: 不调用 LLM
- ✓ 专用: 为监控设计

**模式**: Kubernetes liveness probe——`/healthz` 检查 Pod 是否存活,不调用业务 API。

### Channel 连通性检查

**问题**: Gateway 进程存活 ≠ channel 正常工作 (如 WebSocket 断了、API token 过期)?

**方案**: Health check 检查 channel 连通性:
- **Discord**: WebSocket 连接状态
- **Slack**: Slack API 响应
- **WhatsApp**: WhatsApp Web 连接

**洞察**: 不只检查进程,还检查 channel 连通性 = 真正的"健康"。

**权衡**:
- ✓ 完整: 检查所有关键组件
- ✓ 准确: 不会"进程在但 channel 断了"的误判

**模式**: 数据库健康检查——不只检查进程,还检查"能不能执行查询"。

### Session 状态 ≠ socket 存活

**问题**: 监控工具检查 session 列表,看到 session 存在就认为正常,但 WebSocket 已经断了?

**方案**: 检查 **socket 状态**,不是 session 列表。

**洞察**: Session 存在 = 数据库有记录,Socket 存活 = WebSocket 连接正常。

**权衡**:
- ✓ 准确: socket 状态反映真实连接
- ✗ 复杂: 需要检查 socket,不是 session

### 外部监控服务应该用 /health

**问题**: 外部监控服务用 `/v1/chat/completions`,每分钟调用一次,一天 1440 次,浪费大量 API 额度?

**方案**: 用 `/health` 端点,**不**用 `/v1/chat/completions`。

**洞察**: `/v1/chat/completions` 调用 LLM、执行工具、返回大量数据,不适合健康检查。

**权衡**:
- ✓ 节省: `/health` 不消耗 LLM 资源
- ✓ 快: `/health` 响应快

**模式**: API rate limiting——健康检查不应该算进 rate limit。
