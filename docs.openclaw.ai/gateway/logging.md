# Logging

## 架构精读

> 跳过不影响阅读翻译正文。

### 基于文件的日志器 vs 控制台捕获——为什么两个输出面？

OpenClaw 有两个日志输出面：

- **文件日志器**：按日滚动文件（JSON 格式），独立严重级别
- **控制台捕获**：CLI 记录终端消息到存储，详细程度独立调整

这跟 ELK Stack 的日志收集器是一个思路——文件日志器是结构化日志（供机器消费），控制台捕获是人类可读日志（供运维消费）。两者严重级别独立配置（文件可以 DEBUG 级别记录所有内容，控制台可以 INFO 级别只显示关键信息）。

关键设计是**分离关注点**。生产环境文件全量记录（供审计/排查），控制台精简显示（供实时监控）。

### 脱敏——为什么需要两层策略？

日志脱敏有默认正则表达式 + 自定义模式两层：

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

这跟 AWS CloudWatch Logs 的数据保护是一个思路——默认脱敏常见敏感字段（API 密钥/令牌/密钥），自定义模式脱敏业务特定敏感字段。某些安全边界始终适用（如密钥引用不会被脱敏，因为已经是引用而非明文）。

### WebSocket 日志——为什么需要标准和详细两种模式？

网关 WebSocket 日志有两种检查模式：

- **标准**：摘要（连接/断开/消息类型/错误码）
- **详细**：完整负载（包括正文/请求头）

这跟 Chrome DevTools Network 面板的 "预览" vs "响应" 是一个思路——标准快速查看"发生了什么"，详细深入排查"具体内容是什么"。默认标准减少日志量，调试时切详细。

---

The platform utilizes two distinct output surfaces: terminal displays and JSON-formatted gateway files.

平台使用两个独立的输出 surface：终端显示和 JSON 格式的 gateway 文件。