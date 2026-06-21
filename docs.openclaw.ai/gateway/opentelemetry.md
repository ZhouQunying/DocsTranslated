# OpenTelemetry Export

## 架构精读

> 跳过不影响阅读翻译正文。

### Signal 分类——为什么需要三种遥测类型？

OpenClaw OTEL export 发送三种 signal：

1. **Counter/Histogram 指标**：令牌消耗、消息路由、语音交互、队列深度、内存使用
2. **Span trace**：模型调用、测试框架生命周期、工具执行的调用链
3. **Structured log record**：诊断事件的详细记录

这跟 OpenTelemetry 的标准信号分类是一个思路——指标回答"发生了什么"（量），trace 回答"怎么发生的"（链路），log 回答"为什么发生"（详情）。三种信号互补，不是互相替代。

### Privacy——为什么 prompt/工具负载 是 opt-in？

OTEL 导出自动脱敏对话文本，prompt 和工具负载是按需开启（需要显式切换）。默认不发送。

这跟 Datadog APM 的 trace redaction 是一个思路——默认自动脱敏 HTTP 请求头/负载，敏感数据按需开启发送。防止"运维开启了 OTEL 但不知道对话内容被发送到后端"。

### OTLP protocol——为什么选 protobuf over HTTP？

OTLP 使用 protobuf over HTTP 而非 JSON over HTTP。protobuf 比 JSON 更紧凑（减少网络传输成本），支持 streaming（大量数据时不会 OOM），是 OpenTelemetry 的标准协议。

兼容任何 OTLP 兼容后端（Datadog/Jaeger/Tempo/Grafana），无需代码改动。

---

The platform transmits telemetry via the "diagnostics-otel" extension utilizing protobuf over HTTP, while also supporting standard output line-delimited JSON for sandboxed environments.

平台通过 `diagnostics-otel` 插件以 protobuf over HTTP 传输遥测数据，同时支持 stdout line-delimited JSON 用于沙箱环境。