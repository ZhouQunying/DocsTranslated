# Health Checks

## 架构精读

> 跳过不影响阅读翻译正文。

### 快速检查 vs 深度诊断——为什么分层？

OpenClaw 的健康检查分两层：

- **快速检查**：CLI 命令（`openclaw health`）、私信快捷验证、日志跟踪——快速验证连通性
- **深度诊断**：认证文件检查、会话重连、RAM 使用分析、脱敏诊断包导出——深度排查

这跟 K8s 的存活探针 vs 就绪探针是一个思路——存活快速判断"是否活着"，就绪 深入判断"是否能接收流量"。快速检查快速判断"频道是否连通"，深度诊断深入排查"为什么不通"。

关键设计是**分层诊断**。快速检查目标 30 秒内给出结论，深度诊断目标 5 分钟内定位根因。不会让用户在最开始就陷入深层排查。

### Health monitor——为什么需要自动轮询？

`healthMonitor` 配置自动轮询频率、不活跃阈值、每小时重启上限：

```json5
{
  healthMonitor: {
    intervalMinutes: 5,     // 每 5 分钟轮询
    inactiveThresholdMinutes: 15,  // 15 分钟不活跃触发重启
    maxRestartsPerHour: 3   // 每小时最多重启 3 次
  }
}
```

这跟 systemd 的 `Restart=on-failure` + `RestartSec` 是一个思路——自动检测故障 + 自动重启，但限制重启频率防止无限循环。某些频道平台有豁免（平台特例豁免）。

### `/healthz` vs 对话路由——为什么第三方监控要用轻量端点？

第三方监控（可用性监控）应该用 `/healthz` 而非对话路由：

```
GET /healthz → 200 OK  // 轻量，不创建 session
GET /api/conversation → 会创建 session 堆积
```

这跟 AWS ELB 健康检查是一个思路——健康检查端点只返回"是否活着"，不触发业务逻辑。如果监控走对话路由，每次请求都会创建一个会话，最终堆积大量无用的会话。

---

Short guide to verify channel connectivity without guessing.

验证 channel 连通性的快速指南——不靠猜测。