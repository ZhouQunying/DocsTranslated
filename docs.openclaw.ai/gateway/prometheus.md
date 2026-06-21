# Prometheus Metrics

**总结：** 通过特定模块广播诊断数据——捕获基础稳定性事件，渲染 Prometheus text endpoint 供 scraper 直接拉取。

> **类比：Prometheus node_exporter + 自定义 collector。** node_exporter 暴露主机 metric（CPU/memory/disk），自定义 collector 暴露应用特定 metric。OpenClaw Prometheus 类似——注册 metric（counter/histogram/gauge），暴露 `/metrics` text endpoint 供 Prometheus scrape，low-cardinality label policy（hard limit on time series + 排除 restricted data），PromQL recipe 提供常见查询（token rate/hourly spend/latency percentile/queue delay）。
>
> **架构要点：** Quick start：添加模块 + 配置 + 重启 + scraper 连接（带 credential）；Metrics exported：完整 metric 表（counter/histogram/gauge + data label）；Label policy：low-cardinality tag 规则、time series hard memory limit、restricted data 排除列表；PromQL recipes：实用查询示例（token rate/hourly spend/latency percentile/queue delay/dropped series）；Choosing between Prometheus + OTEL：pull-based metric（Prometheus scrape）vs push-based（OTEL export），按现有基础设施选择；Troubleshooting：blank response/auth failure/cardinality limit breach/data reset after restart。
