# Prometheus Metrics

## 架构精读

> 跳过不影响阅读翻译正文。

### Pull-based vs push-based——为什么同系统提供两种？

OpenClaw 同时提供 Prometheus（pull-based）和 OTEL（push-based）两种遥测方式：

- **Prometheus**：`/metrics` endpoint 被 scraper 定期拉取，适合自建监控
- **OTEL**：主动推送到 backend，适合托管监控（Datadog/Grafana Cloud）

这跟 K8s 的 metrics pipeline 是一个思路——Prometheus 是 pull-based（适合内部监控），OTEL 是 push-based（适合外部 SaaS）。两者不互斥，可以同时启用。

### Label policy——为什么限制 low-cardinality？

Prometheus metric 的 label 策略是：

- **low-cardinality**：只允许有限值的 label（如 `channel_type="whatsapp"`，不允许 `peer_id="1234567890"`）
- **hard limit**：time series 数量有限制，超过限制时拒绝新数据
- **restricted data 排除**：某些敏感数据（如 peer_id）被排除在 label 之外

这跟 Prometheus 的 cardinality 最佳实践是一个思路——高基数 label 导致 time series 爆炸（每个 peer_id 一个 time series），内存和存储失控。限制 low-cardinality 标签保持系统可扩展。

### PromQL recipes——为什么提供预置查询？

文档提供预置 PromQL 查询：

- Token rate：`rate(openclaw_tokens_total[5m])`
- Hourly spend：`sum(rate(openclaw_cost_total[1h]))`
- Latency percentile：`histogram_quantile(0.95, rate(openclaw_request_duration_seconds_bucket[5m]))`
- Queue delay：`avg(openclaw_queue_delay_seconds)`

这跟 Grafana Dashboard 的预置 panel 是一个思路——不需要用户自己写 PromQL，直接 copy 可用。降低入门门槛。

---

The platform utilizes a specific module to broadcast diagnostic data. It captures fundamental stability occurrences and renders a Prometheus text endpoint to serve formatted metrics directly to scrapers.

平台通过特定模块广播诊断数据——捕获基础稳定性事件，渲染 Prometheus text endpoint 供 scraper 直接拉取。