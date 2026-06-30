# FAQ: first-run setup

## 架构精读

> 跳过不影响阅读翻译正文。

### 安装流程——为什么提供多种方式？

OpenClaw 提供三种安装路径：

- **远程脚本**：标准路径（一键安装，适合快速上手）
- **Git 克隆**：开发者路径（可审查源码，适合安全审计）
- **详细输出模式**：故障排查路径（安装卡住时，`--verbose` 显示隐藏错误）

这跟 Node.js 的安装方式是一个思路——nvm（版本管理）、官方安装包（一键）、源码编译（开发者）。多种方式满足不同用户需求：快速上手 vs 源码审计 vs 故障排查。

### 认证灵活性——为什么支持本地和远程两种模式？

认证方式按访问场景分：

- **本地访问**：localhost 连接需要密码或令牌（简单直接）
- **远程访问**：Tailscale、SSH 隧道、可信反向代理（安全隔离）
- **本地模型**：无需云订阅，数据留在设备（隐私优先）
- **OAuth 订阅**：主流提供商的订阅制（成本优化）

这跟 Git 的认证方式是一个思路——HTTPS 密码（简单）、SSH 密钥（安全）、GPG 签名（审计）。多种认证方式让"本地开发"和"远程生产"都有合适方案。

### 运行时要求——为什么强调 Node 22+？

网关硬性要求：

- **Node 22+**：必须（新版本特性，如原生 ESM 支持）
- **Bun 不推荐**：运行时不稳定（兼容性问题）
- **硬件最低**：512MB-1GB RAM、1 核、500MB 磁盘（个人部署）
- **平台广泛**：树莓派、Linux VPS（无需专用硬件）

这跟 Python 3.8+ 的版本要求是一个思路——新版本引入关键特性（如 `walrus` 运算符），旧版本不再维护。Node 22+ 的要求确保"现代 JavaScript 特性"可用，Bun 不推荐是因为"生产稳定性"优先。

### 常见首次问题——为什么按症状分类？

文档按症状分类常见问题：

1. **初始化卡住**：重启网关 + 运行 `openclaw doctor`
2. **速率限制（429）**：等待窗口重置或升级计划
3. **心跳跳过**：静默时段或无到期任务
4. **SSL 阻断**：某些 ISP 误判文档域名，需禁用安全过滤器或用 GitHub 镜像

这跟 Stack Overflow 的 FAQ 是一个思路——按"我看到了什么症状"组织，而非"什么模块出了问题"。症状分类让"不懂内部结构的用户"也能快速找到答案。

---

FAQ covering first-run setup: installation paths (remote script, Git clone, verbose mode), authentication options (localhost password/token, remote via Tailscale/SSH/proxy, local-only models, OAuth subscriptions), runtime requirements (Node 22+, Bun not recommended, 512MB-1GB RAM, runs on Raspberry Pi/VPS), common first-time issues (stuck onboarding → restart + doctor, rate limiting → wait/upgrade, heartbeat skips → quiet hours, SSL blocks → disable filters or use GitHub mirror).

首次设置常见问题解答。安装路径：远程脚本、Git 克隆、详细输出模式。认证选项：localhost 密码/令牌、远程通过 Tailscale/SSH/代理、纯本地模型、OAuth 订阅。运行时要求：Node 22+、不推荐 Bun、512MB-1GB RAM、可运行在树莓派/VPS。

常见首次问题：初始化卡住（重启 + doctor）、速率限制（等待/升级）、心跳跳过（静默时段）、SSL 阻断（禁用过滤器或用 GitHub 镜像）。

架构精读：多种安装路径满足不同需求（快速上手 vs 源码审计 vs 故障排查）。认证灵活性让"本地开发"和"远程生产"都有合适方案。Node 22+ 确保现代 JavaScript 特性可用。
