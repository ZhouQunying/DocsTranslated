# OpenTelemetry Export

**总结：** 通过 `diagnostics-otel` 插件以 protobuf over HTTP 传输遥测数据——兼容标准 OTLP ingestion backend，无需代码改动。沙箱环境也支持 stdout line-delimited JSON。

> **类比：Datadog Agent + Jaeger + 标准 OTLP protocol。** Datadog Agent 收集 metric/trace/log 推送到 Datadog backend，Jaeger 收集 distributed trace，OTLP 是 OpenTelemetry 标准协议。OpenClaw OTEL export 类似——内部 event record → `diagnostics-otel` 插件 → OTLP HTTP protobuf 推送到 backend（Datadog/Jaeger/Tempo/任何 OTLP 兼容），三种 signal（counter/histogram metric、span trace、structured log），自动脱敏 conversation text，opt-in 记录 prompt/tool payload。
>
> **架构要点：** How it fits together：内部 event record → `diagnostics-otel` extension → provider header propagation → activation condition；Quick start：安装插件 + JSON 配置 endpoint/protocol/header + 重启；Signals exported：三种遥测类型（counter/histogram metric、span trace、structured log record）；Configuration reference：endpoint/protocol/header 的 JSON 参数和环境变量；Privacy + content capture：自动脱敏 conversation text，opt-in toggle 记录 prompt/tool payload；Sampling + flushing：data reduction 规则、transmission interval、request correlation；Exported metrics：按子系统列出（model consumption/message routing/vocal interaction/queue/memory）；Exported spans：trace segment（model invocation/harness lifecycle/tool execution）；Diagnostic event catalog：驱动 metric/span 的内部事件列表；Without exporter：保留内部 event 给自定义 destination 或用 targeted debug flag；Disable：停用遥测插件。
