# Health Checks

**总结：** 验证 channel 连通性的快速指南——不靠猜测。

> **类比：K8s liveness/readiness probe + Prometheus blackbox exporter。** K8s liveness probe 验证 pod 存活，readiness probe 验证 pod 可接收流量，blackbox exporter 从外部探测 endpoint。OpenClaw health check 类似——quick check（CLI/DM/tail log 快速验证连通性）、deep diagnostic（auth file/session relink/RAM/diagnostic zip 深度排查）、health monitor（自动轮询 + 不活跃阈值 + 重启上限 + 平台豁免）、uptime monitoring（第三方监控用轻量 `/healthz` 而非 conversation route）。
>
> **架构要点：** Quick check：CLI 命令（`openclaw health`）、DM 快捷验证、log tail；Deep diagnostic：auth file 检查、session relink、RAM 使用、redacted diagnostic zip 导出；Health monitor config：自动轮询频率（`healthMonitor.intervalMinutes`）、不活跃阈值（`inactiveThresholdMinutes`）、每小时重启上限（`maxRestartsPerHour`）、平台豁免（某些 channel 跳过）；Uptime monitoring：第三方监控用 `/healthz` 轻量 endpoint（避免触发 session 创建堆积）；When something fails：token expired（刷新）、local server 无响应（检查端口/进程）、inbound text delivery 受限（检查 DM policy）；Dedicated `health` command：`openclaw health` 获取实时 gateway 状态报告（可用 modifier 控制输出）。
