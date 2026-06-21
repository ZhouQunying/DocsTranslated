# Diagnostics Export

## 架构精读

> 跳过不影响阅读翻译正文。

### Privacy model——为什么自动 redact 敏感信息？

Diagnostics export 的隐私模型是：

- **保留**：operational metric（CPU/memory/disk/process uptime）、stability record
- **排除**：conversation content（对话内容）、secret（API key/token）、key（加密密钥）

这跟 Chrome crash report 的隐私策略是一个思路——发送 stack trace 和 system info，不发送浏览历史、cookie、密码。Redaction 是自动的（不是手动勾选），防止"忘记勾选导致泄露"。

关键设计是**默认安全**。不需要用户手动 redact，系统自动识别并脱敏敏感信息。

### Stability recorder——为什么是"无内容"追踪？

Stability recorder 持续追踪 system liveness，但**不记录内容**（只记录"系统是否存活"的时间戳）：

```
openclaw diagnostics stability
```

这跟 Prometheus 的 UP metric 是一个思路——只记录 `up{job="gateway"} 1` 或 `0`，不记录具体内容。好处是数据量极小（可以保留很长时间），可以精确定位"系统什么时候挂了"。

### 触发方式——为什么 CLI 和 chat command 都要支持？

Diagnostics export 支持两种触发方式：

- **CLI**：`openclaw diagnostics export`（自动化友好）
- **Chat command**：owner 在对话中用 slash command 触发（方便，不需要退出对话）

这跟 `kubectl logs` vs `kubectl cluster-info dump` 是一个思路——轻量操作可以单命令，重量操作（导出 zip）需要明确的触发。Chat command 提供 private routing（结果只发给触发者），防止隐私泄露。

---

OpenClaw can create a local diagnostics zip for bug reports. This archive merges cleaned system health metrics, log files, and system stability information.

OpenClaw 可创建本地 diagnostics zip 用于 bug report——合并清理后的系统健康指标、log 文件和系统稳定性信息。