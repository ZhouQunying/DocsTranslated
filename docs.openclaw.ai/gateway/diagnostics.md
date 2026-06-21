# Diagnostics Export

**总结：** OpenClaw 可创建本地 diagnostics zip 用于 bug report——合并清理后的系统健康指标、log 文件和系统稳定性信息。

> **类比：kubectl cluster-info dump + Chrome crash report。** kubectl cluster-info dump 导出集群状态（pod log/event/node info）用于排查，Chrome crash report 收集崩溃信息（stack trace/system info）上报。OpenClaw diagnostics export 类似——生成 zip 包含 text overview + structured JSON data + cleaned log + stability record，自动 redact 敏感信息（conversation content/secret/key），支持 CLI/chat command 触发，可自动化（CI 集成）。
>
> **架构要点：** Quick start：CLI 命令（`openclaw diagnostics export`）生成/保存/自动化 zip 创建；Chat command：owner 在对话中用 slash command 触发（private routing + Codex integration）；What the export contains：zip 内文件（text overview、structured JSON data、cleaned log）；Privacy model：保留 operational metric，排除 sensitive detail（conversation content/secret/key）；Stability recorder：持续追踪 system liveness（无内容），命令查看 record；Useful options：CLI flag 控制 output path/log limit/connection timeout；Disable diagnostics：配置关闭 recording feature 或 toggle RAM stress capture。
