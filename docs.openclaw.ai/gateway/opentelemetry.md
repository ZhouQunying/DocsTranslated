# OpenTelemetry Export

## 架构精读

> 跳过不影响阅读翻译正文。

### Signal 分类——为什么需要三种遥测类型？

OpenClaw OTEL export 发送三种 signal：

1. **Counter/Histogram metric**：token 消耗、消息路由、voice interaction、queue depth、memory 使用
2. **Span trace**：model invocation、harness lifecycle、tool execution 的调用链
3. **Structured log record**：diagnostic event 的详细记录

这跟 OpenTelemetry 的 standard signal 分类是一个思路——metric 回答"what happened"（量），trace 回答"how it happened"（链路），log 回答"why it happened"（详情）。三种 signal 互补，不是互相替代。

### Privacy——为什么 prompt/tool payload 是 opt-in？

OTEL export 自动脱敏 conversation text，prompt 和 tool payload 是 opt-in（需要显式 toggle）。默认不发送。

这跟 Datadog APM 的 trace redaction 是一个思路——默认自动脱敏 HTTP header/payload，敏感数据 opt-in 发送。防止"运维开启了 OTEL 但不知道对话内容被发送到后端"。

### OTLP protocol——为什么选 protobuf over HTTP？

OTLP 使用 protobuf over HTTP 而非 JSON over HTTP。protobuf 比 JSON 更紧凑（减少网络传输成本），支持 streaming（大量数据时不会 OOM），是 OpenTelemetry 的标准协议。

兼容任何 OTLP-compatible backend（Datadog/Jaeger/Tempo/Grafana），无需代码改动。

---

The platform transmits telemetry via the "diagnostics-otel" extension utilizing protobuf over HTTP, while also supporting standard output line-delimited JSON for sandboxed environments.

平台通过 `diagnostics-otel` 插件以 protobuf over HTTP 传输遥测数据，同时支持 stdout line-delimited JSON 用于沙箱环境。