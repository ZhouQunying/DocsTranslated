# Diagnostics Export

## 架构精读

> 跳过不影响阅读翻译正文。

### 隐私模型——为什么自动脱敏敏感信息？

诊断导出的隐私模型是：

- **保留**：运维指标（CPU/内存/磁盘/进程运行时长）、稳定性记录
- **排除**：对话内容、密钥（API 密钥/令牌）、加密密钥

这跟 Chrome 崩溃报告的隐私策略是一个思路——发送堆栈跟踪和系统信息，不发送浏览历史、cookie、密码。脱敏是自动的（不是手动勾选），防止"忘记勾选导致泄露"。

关键设计是**默认安全**。不需要用户手动脱敏，系统自动识别并脱敏敏感信息。

### 稳定性记录器——为什么是"无内容"追踪？

稳定性记录器持续追踪系统存活状态，但**不记录内容**（只记录"系统是否存活"的时间戳）：

```
openclaw diagnostics stability
```

这跟 Prometheus 的 UP 指标是一个思路——只记录 `up{job="gateway"} 1` 或 `0`，不记录具体内容。好处是数据量极小（可以保留很长时间），可以精确定位"系统什么时候挂了"。

### 触发方式——为什么 CLI 和聊天命令都要支持？

诊断导出支持两种触发方式：

- **CLI**：`openclaw diagnostics export`（自动化友好）
- **聊天命令**：所有者在对话中用斜杠命令触发（方便，不需要退出对话）

这跟 `kubectl logs` vs `kubectl cluster-info dump` 是一个思路——轻量操作可以单命令，重量操作（导出压缩包）需要明确的触发。聊天命令提供私密路由（结果只发给触发者），防止隐私泄露。

---

OpenClaw can create a local diagnostics zip for bug reports. This archive merges cleaned system health metrics, log files, and system stability information.

OpenClaw 可创建本地 diagnostics zip 用于 bug report——合并清理后的系统健康指标、log 文件和系统稳定性信息。