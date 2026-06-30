# FAQ

## 架构精读

> 跳过不影响阅读翻译正文。

### 本地优先架构——为什么强调"数据在本地"？

OpenClaw 是"本地优先控制平面"（local-first control plane）：

- **自主托管**：用户在自己的硬件上运行 AI 助手
- **多通道连接**：接入多个聊天应用（WhatsApp、Slack、Discord）
- **数据本地化**：会话历史、认证信息留在 `~/.openclaw` 目录

这跟 Nextcloud vs Dropbox 是一个思路——Nextcloud 自托管（数据在你手里），Dropbox 云端托管（数据在别人手里）。本地优先适合"隐私敏感"场景（企业、个人日记、医疗记录）。

### 快速诊断三步法——为什么先跑这三个命令？

遇到问题时的标准排查流程：

1. **`openclaw status`**：查看健康摘要（一眼看出问题在哪）
2. **`openclaw logs`**：追踪实时日志（看到具体错误信息）
3. **`openclaw doctor`**：自动修复配置（修复常见问题）

这跟医生问诊是一个思路——先看体检报告（status），再问症状细节（logs），最后开药治疗（doctor）。三步法覆盖 80% 的常见问题，避免"一上来就看代码"的低效路径。

### 节点架构——为什么不装多个服务器？

文档建议"将电脑配对为节点"（pair your computer as a node）到中央 VPS，而非在每台机器安装完整服务器。

- **远程中心**：VPS 运行网关（接收消息、路由请求）
- **本地节点**：电脑配对为节点（执行本地硬件工具）
- **安全隔离**：远程触发本地工具，无需暴露入站命令行访问

这跟 Kubernetes 的 master-worker 架构是一个思路——master 调度（VPS），worker 执行（本地电脑）。节点架构让"集中控制 + 分布式执行"成为可能，避免每台机器重复配置。

### 安全默认值——为什么 DM 需要验证码？

平台默认启用 DM 验证模式（验证模式），未知联系人需提交验证码才能与智能体交互。

这跟手机短信的"陌生人过滤"是一个思路——未保存号码需要自报身份（"我是 XXX"），防止垃圾短信。DM 验证防止"恶意用户冒充好友"触发智能体执行危险操作。

---

FAQ covering core concepts: local-first control plane (self-hosted AI with data on personal hardware), multi-channel connectivity (WhatsApp/Slack/Discord), quick diagnostics (`openclaw status` → `openclaw logs` → `openclaw doctor`), storage locations (`~/.openclaw` for sessions/auth, workspace folder for cognitive files), node architecture (pair local computer as node to remote VPS hub), security defaults (DM verification mode for unknown contacts), prompt injection risks when processing external content.

常见问题解答，覆盖核心概念。本地优先控制平面：自主托管 AI，数据在个人硬件。多通道连接：WhatsApp/Slack/Discord。快速诊断三步法、存储位置区分、节点架构、安全默认值、提示注入风险。

核心要点：`openclaw status` 查看健康摘要，`openclaw logs` 追踪日志，`openclaw doctor` 自动修复。会话数据存 `~/.openclaw`，认知文件存工作空间目录。节点架构支持"VPS 中心 + 本地电脑节点"模式。DM 验证过滤未知联系人，防止恶意触发。

架构精读：本地优先适合隐私敏感场景（企业、医疗记录）。三步法覆盖 80% 常见问题，避免低效路径。节点架构实现"集中控制 + 分布式执行"，避免重复配置。
