# Troubleshooting

## 架构精读

> 跳过不影响阅读翻译正文。

### Command ladder——为什么是序列化诊断？

Troubleshooting 的诊断流程是命令阶梯（命令序列）：

1. `openclaw health` → 基础健康检查
2. `openclaw doctor` → 深度配置/状态修复
3. `openclaw diagnostics export` → 导出给 support

这跟 PagerDuty 的 escalation policy 是一个思路——逐层升级，从快速检查到深度排查到上报。每层有明确的"什么情况下进入下一层"的判断标准。

### Split brain install——为什么旧程序新 config 会失败？

当旧程序遇到新 config（包含旧程序不认识的字段），结构校验失败。

这跟 K8s API versioning 的兼容性策略是一个思路——新 API server 可以处理旧 client 请求（向后兼容），但旧 API server 不能处理新 client 请求。解决方案是升级程序到匹配 config 的版本。

关键设计是**严格校验**——不认识的字段阻止启动，而不是静默忽略。静默忽略会导致"config 里写了但没生效"的隐性故障。

### Protocol mismatch after rollback——为什么降级后协议不兼容？

降级后协议版本可能不匹配。因为新版本可能引入了新的协议格式（如 session 数据结构、消息格式），旧版本无法解析。

这跟数据库迁移的逆操作是一个思路——正向迁移有升级路径，但回退迁移可能丢失新版本写入的数据。解决方案是降级前清空 session 和 pairing 状态。

---

This page serves as a deep diagnostic runbook for gateway, channels, automation, nodes, and browser issues.

Gateway/channel/automation/node/browser 问题的深度诊断 runbook。