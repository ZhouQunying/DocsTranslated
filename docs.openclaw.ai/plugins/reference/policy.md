# Policy 插件参考

## 架构精读

> 跳过不影响阅读翻译正文。

### 策略引擎为什么是"观察证据"而非"执行规则"？

传统策略引擎（如防火墙、RBAC）在请求路径上执行规则——匹配则拒绝，不匹配则放行。OpenClaw 的 policy 插件走了一条不同的路：它**观察**现有的 OpenClaw 设置和工作区声明作为证据，通过 `openclaw policy check` 和 `openclaw doctor --lint` 报告漂移。就像 Kubernetes 的 Admission Controller 或 Open Policy Agent（OPA）——它们不修改资源，只验证资源是否符合声明的策略。好处是策略检查是幂等的、可审计的、不干扰运行时。`policy compare` 比较两个策略文件的一致性——纯配置级别，不检查运行时状态、凭证或密钥值。

策略覆盖的维度很广。包括 channel 一致性、受管工具元数据、MCP 服务器姿态、模型 provider 姿态、私有网络访问姿态、Gateway 暴露姿态。还包括 agent 工作区/工具姿态、全局/逐 agent 工具姿态、沙箱运行时姿态、入站/channel 访问姿态、数据处理姿态和配置密钥 provider 姿态。

命名策略范围（`scopes.<scopeName>`）可为其列出的选择器添加更严格的普通策略段落。`agentIds` 支持 `tools`、`agents.workspace`、`sandbox` 和 `dataHandling.memory`；`channelIds` 支持 `ingress.channels`。未在 `agents.list[]` 中显式列出的运行时 agent id 根据继承的全局/默认姿态检查，而非静默通过无证据。

---

添加策略支持的工作区一致性 doctor 检查。

## 分发

- 包：`@openclaw/policy`
- 安装路径：包含在 OpenClaw 中

## 行为

Policy 插件为策略管理的 OpenClaw 设置和受管工作区声明贡献 doctor 健康检查。策略当前覆盖 channel 一致性、受管工具元数据、MCP 服务器姿态、模型 provider 姿态、私有网络访问姿态、Gateway 暴露姿态。还覆盖 agent 工作区/工具姿态、配置的全局/逐 agent 工具姿态、配置的沙箱运行时姿态、入站/channel 访问姿态、数据处理姿态和 OpenClaw 配置密钥 provider 姿态。

策略将编写的要求存储在 `policy.jsonc` 中，观察现有的 OpenClaw 设置和工作区声明作为证据，并通过 `openclaw policy check` 和 `openclaw doctor --lint` 报告漂移。干净的策略检查发出策略、证据、发现和证明哈希，操作者可记录用于审计。

`openclaw policy compare --baseline <file>` 将一个策略文件与另一个策略文件比较。它仅是配置级别的一致性。使用策略规则元数据验证被检查的策略未缺失或弱于编写的基线。不检查运行时状态、凭证或密钥值。

工具姿态规则可要求批准的配置文件和仅工作区的文件系统工具。还可要求有界的 exec 安全设置、禁用的提升模式、精确的 `alsoAllow` 条目和必需的工具拒绝条目。证据记录加性 `alsoAllow` 条目，因为它们可拓宽有效工具姿态。这些检查仅观察配置一致性；不读取运行时审批状态或添加运行时执行。

沙箱姿态规则可要求批准的沙箱模式/后端和拒绝主机容器网络。还可拒绝容器命名空间加入、要求只读容器挂载、拒绝容器运行时套接字挂载和无限制容器配置文件。以及要求沙箱浏览器 CDP 源范围。这些检查仅观察配置一致性；不读取运行时审批状态、检查活跃容器或添加运行时执行。

数据处理规则可要求敏感日志编辑、拒绝遥测内容捕获、要求会话保留维护和拒绝会话转录记忆索引。这些检查仅观察配置一致性；不检查原始日志、遥测导出、转录、记忆文件、密钥或个人数据。

## 相关

- [policy](/cli/policy)
