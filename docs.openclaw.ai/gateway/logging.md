# Logging

## 架构精读

> 跳过不影响阅读翻译正文。

### File-based logger vs console capture——为什么两个 output surface？

OpenClaw 有两个日志输出面：

- **文件日志器**：按日滚动文件（JSON 格式），独立严重级别
- **控制台捕获**：CLI 记录终端消息到存储，详细程度独立调整

这跟 ELK Stack 的 log shipper 是一个思路——文件日志器是结构化日志（供机器消费），控制台捕获是人类可读日志（供运维消费）。两者严重级别独立配置（文件可以 DEBUG 级别记录所有内容，控制台可以 INFO 级别只显示关键信息）。

关键设计是**分离关注点**。生产环境 file 全量记录（供审计/排查），console 精简显示（供实时监控）。

### Redaction——为什么需要两层策略？

Log redaction 有默认 regex + 自定义 pattern 两层：

```json5
{
  logging: {
    redact: {
      defaults: true,  // 默认脱敏 API key/token/secret
      customPatterns: ["\\bmy-custom-pattern\\b"]  // 自定义脱敏
    }
  }
}
```

这跟 AWS CloudWatch Logs 的 data protection 是一个思路——默认脱敏常见敏感字段（API key/token/secret），自定义 pattern 脱敏业务特定敏感字段。某些安全边界始终适用（如 secret 引用不会被脱敏，因为已经是引用而非明文）。

### WebSocket log——为什么需要 standard 和 detailed 两种模式？

Gateway WebSocket 日志有两种检查模式：

- **standard**：摘要（连接/断开/消息类型/错误码）
- **detailed**：完整 payload（包括 body/header）

这跟 Chrome DevTools Network 面板的 "预览" vs "Response" 是一个思路——standard 快速查看"发生了什么"，detailed 深入排查"具体内容是什么"。默认 standard 减少日志量，调试时切 detailed。

---

The platform utilizes two distinct output surfaces: terminal displays and JSON-formatted gateway files.

平台使用两个独立的输出 surface：终端显示和 JSON 格式的 gateway 文件。