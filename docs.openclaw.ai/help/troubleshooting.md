# General Troubleshooting

## 架构精读

> 跳过不影响阅读翻译正文。

### 故障排查决策树——为什么按层次定位？

`help/troubleshooting` 提供分层故障排查路径：

- **状态检查**：`openclaw status` 查看健康摘要
- **网关探测**：`openclaw doctor` 自动修复配置
- **日志追踪**：`openclaw logs` 查看实时日志

这跟急诊分诊是一个思路——先快速评估（生命体征），再针对性检查（CT/验血），最后深入诊断（专家会诊）。分层排查避免"一头扎进细节"导致的方向错误。

### 常见故障域——为什么分类处理？

文档按故障域分类：

1. **消息流**：传输连接、配对状态、发送者过滤
2. **UI/网关连接**：设备身份、Origin 限制、认证令牌
3. **自动化/心跳**：调度器状态、静默时段、任务间隔
4. **节点/执行工具**：OS 权限、后台应用、安全策略
5. **浏览器自动化**：插件限制、可执行路径、CDP 目标

这跟 OSI 七层模型是一个思路——物理层 → 数据链路层 → 网络层 → 传输层，每层独立排查。故障域分类让"逐层排除"成为可能，而非随机尝试。

---

Structured troubleshooting guide with layered diagnostic approach: status checks (`openclaw status`), gateway probes (`openclaw doctor`), log monitoring (`openclaw logs`). Organized by failure domains: message flow, UI/gateway connectivity, automation/heartbeats, node/execution tools, browser automation. Common issues include port conflicts, auth token mismatches, disabled schedulers, and missing OS permissions.

结构化故障排查指南，提供分层诊断方法：状态检查（`openclaw status`）、网关探测（`openclaw doctor`）、日志监控（`openclaw logs`）。按故障域组织：消息流、UI/网关连接、自动化/心跳、节点/执行工具、浏览器自动化。常见问题包括端口冲突、认证令牌不匹配、调度器禁用、缺少 OS 权限。
