# Health Checks

## 架构精读

> 跳过不影响阅读翻译正文。

### Quick check vs deep diagnostic——为什么分层？

OpenClaw 的 health check 分两层：

- **Quick check**：CLI 命令（`openclaw health`）、DM 快捷验证、log tail——快速验证连通性
- **Deep diagnostic**：auth file 检查、session relink、RAM 使用分析、redacted diagnostic zip 导出——深度排查

这跟 K8s 的 liveness probe vs 就绪 probe 是一个思路——liveness 快速判断"是否活着"，就绪 深入判断"是否能接收流量"。Quick check 快速判断"channel 是否连通"，deep diagnostic 深入排查"为什么不通"。

关键设计是**分层诊断**。Quick check 目标 30 秒内给出结论，deep diagnostic 目标 5 分钟内定位根因。不会让用户在最开始就陷入深层排查。

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

这跟 systemd 的 `Restart=on-failure` + `RestartSec` 是一个思路——自动检测故障 + 自动重启，但限制重启频率防止无限循环。某些 channel 平台有豁免（platform-specific exemption）。

### `/healthz` vs conversation route——为什么第三方监控要用轻量 endpoint？

第三方监控（uptime monitoring）应该用 `/healthz` 而非 conversation route：

```
GET /healthz → 200 OK  // 轻量，不创建 session
GET /api/conversation → 会创建 session 堆积
```

这跟 AWS ELB health check 是一个思路——health check endpoint 只返回"是否活着"，不触发业务逻辑。如果监控走 conversation route，每次 ping 都会创建一个 session，最终堆积大量无用的 session。

---

Short guide to verify channel connectivity without guessing.

验证 channel 连通性的快速指南——不靠猜测。