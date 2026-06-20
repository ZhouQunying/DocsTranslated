# Logging

## 架构精读

> 跳过不影响阅读翻译正文。

### Rolling JSONL——结构化日志的标准格式

macOS app 的日志用 **JSONL**(JSON Lines)格式: 每行一个 JSON 对象,滚动写入(文件过大时自动切到新文件)。

**为什么用 JSONL 而不是纯文本?** 纯文本日志需要正则表达式解析,容易出错。JSONL 是结构化日志,可以直接用 `jq` 查询:
- `jq 'select(.level == "error")'` 过滤错误
- `jq '.timestamp'` 提取时间
- `jq '.subsystem'` 按模块过滤

**为什么是"行级"格式?** JSONL 每行独立,一行损坏不影响其他行。如果用完整 JSON 数组(`[{...}, {...}]`),一个括号错了整个文件就废了。

**为什么"滚动"写入?** 日志文件会越来越大,滚动写入会在文件达到一定大小时自动切到新文件(如 `log-2026-06-20-001.jsonl`、`log-2026-06-20-002.jsonl`),避免单个文件过大。

这跟 Docker 的 json-file 日志驱动是一个思路——Docker 默认把容器日志写成 JSONL 格式,可以用 `docker logs --since` 按时间过滤。OpenClaw 的日志也是同样的设计理念: 结构化 + 滚动 + 行级。

### macOS unified logging 的隐私保护——默认隐藏敏感数据

macOS 的 unified logging system(统一日志系统)默认**隐藏敏感数据**(如 token、password、API key),显示为 `<private>`。需要显式配置 `Enable-Private-Data` plist 才能看到完整日志。

**为什么这样设计?** 因为日志可能被多人查看(开发者、支持人员、甚至用户上传的日志文件),如果默认显示敏感数据,就会泄露凭证。默认隐藏 + 显式开启 = 隐私安全 + 调试灵活。

**怎么开启?** 在 app 的 plist 配置里加 `Enable-Private-Data: true`,重新编译。生产环境**永远不要**开启,只在开发调试时临时开启。

这跟 Kubernetes 的 audit logging 是一个思路——Kubernetes audit log 默认不记录 request body(可能包含 secret),需要配置 `level: Request` 才记录。OpenClaw 也是这样: 默认保护隐私,调试时显式开启。隐私不是事后补丁,而是**日志系统的设计约束**。

### Subsystem filter——按模块过滤日志

macOS unified logging 支持按 **subsystem**(子系统,如 `com.openclaw.gateway`、`com.openclaw.app`)过滤。

**为什么需要子系统?** 因为 OpenClaw 有多个组件(Gateway、app、node host service),每个组件都写日志。如果所有日志混在一起,调试时很难定位问题。按 subsystem 过滤后,开发者可以只看 Gateway 日志或只看 app 日志,不被无关信息淹没。

这跟 log4j 的 logger name 是一个思路——log4j 允许不同模块用不同的 logger name,可以按 name 开关日志级别。OpenClaw 的 subsystem 是同样的设计理念: 按模块过滤,精准调试。
