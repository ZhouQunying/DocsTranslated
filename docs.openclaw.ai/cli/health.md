# `openclaw health`

## 架构精读

> 跳过不影响阅读翻译正文。

### 快速健康检查——为什么需要独立命令而非 `status`？

`openclaw health` 做快速健康检查（网关进程存活 + 端口可达 + 凭证有效），比 `openclaw status` 更轻量：

- **`health`**：3 秒内返回"健康/不健康"（快速判断）
- **`status`**：详细状态报告（会话数、节点数、内存使用等）

这跟 K8s 的 liveness probe vs kubectl describe 是一个思路——liveness probe 只回答"是否存活"（快速），kubectl describe 给出完整状态（慢但详细）。

### 退出码——为什么用退出码而非文本输出？

`health` 命令用退出码表示结果（0 = 健康，1 = 不健康），而非只输出文本。这允许脚本判断：

```
openclaw health && echo "OK" || echo "FAIL"
```

这跟 HTTP 健康检查端点（`/healthz` 返回 200 或 503）是一个思路——机器可读的结果（退出码/状态码）支持自动化监控（Prometheus blackbox exporter、UptimeRobot）。

---

Quick health check (gateway alive + port reachable + credentials valid) in under 3 seconds. Uses exit codes (0 = healthy, 1 = unhealthy) for script integration, unlike `status` which provides detailed reports.

快速健康检查（网关存活 + 端口可达 + 凭证有效），3 秒内完成。用退出码（0 = 健康，1 = 不健康）支持脚本集成，不同于 `status` 的详细报告。
