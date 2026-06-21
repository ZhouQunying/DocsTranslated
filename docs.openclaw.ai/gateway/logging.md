# Logging

**总结：** Gateway 两个日志 output surface——终端显示和 JSON 格式 gateway 文件。

> **类比：ELK Stack + logrotate + 敏感数据 redact。** ELK（Elasticsearch + Logstash + Kibana）收集/索引/可视化 log，logrotate 按大小/日期滚动 log 文件，敏感数据 redact 自动脱敏。OpenClaw logging 类似——file-based logger（daily rolling + size limit + 独立 severity level）、console capture（CLI 记录 stdout/stderr 到存储）、redaction（default/custom regex 脱敏 API key/token/secret）、WebSocket log（standard/detailed 两种 inspection mode）、console formatting（颜色/组件标签/raw output）。
>
> **架构要点：** File-based logger：daily rolling log 文件、size limit、配置路径（`logging.file.path`）、终端 verbosity 和 file severity 独立控制；Console capture：CLI 记录终端消息到存储，verbosity 独立调整；Redaction：跨 output 脱敏机密信息（default regex + custom pattern），某些安全边界始终适用（如 secret reference 不会被 redact）；Gateway WebSocket log：standard mode（摘要）vs detailed inspection mode（完整 payload）；WS log style：CLI flag 控制网络流量日志的显示格式；Console formatting：终端感知文本样式（颜色编码、组件标签、raw output 选项）。
