# Logging

## 架构精读

> 跳过不影响阅读翻译正文。

### Rolling JSONL——结构化日志的标准格式

macOS app 的日志用 JSONL（JSON Lines）格式，每行一个 JSON 对象，滚动写入。这跟 ELK stack 的 logstash 是一个思路——日志结构化后可以直接用 jq 查询，不需要正则表达式解析。JSONL 的好处是**追加写入**（append-only）和**行级解析**（line-delimited），一行损坏不影响其他行。

OpenClaw 的日志不是纯文本 + 正则，而是 JSON + 字段查询。这使得 `jq 'select(.level == "error")'` 可以过滤错误，`jq '.timestamp'` 可以提取时间。结构化日志是现代可观测性的基础。

### macOS unified logging 的隐私控制

文档提到了 macOS 的 unified logging system 和 `Enable-Private-Data` plist 配置。macOS 的日志系统默认**隐藏敏感数据**（如 token、password），需要显式配置 `Enable-Private-Data` 才能看到完整日志。

这跟 Kubernetes 的 audit logging 是一个思路。Kubernetes audit log 默认不记录 request body（可能包含 secret），需要配置 `level: Request` 才记录。OpenClaw 也是这样：默认保护隐私，调试时显式开启。隐私不是事后补丁，而是**日志系统的设计约束**。

### Subsystem filter——按模块过滤

macOS unified logging 支持按 subsystem（如 `com.openclaw.gateway`）过滤。这跟 log4j 的 logger name 是一个思路——不同模块用不同 logger，可以按模块开关日志级别。OpenClaw 的 subsystem 过滤让开发者只看 Gateway 日志或只看 App 日志，不被无关信息淹没。
