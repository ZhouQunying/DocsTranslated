# Exposure Runbook——暴露应急手册

## 架构精读

> 跳过不影响阅读翻译正文。

### 五级暴露模式——为什么选最严格的？

暴露 runbook 列出五级暴露模式，每级比上一级更宽：local+SSH（只有 localhost + 隧道）→ local+Tailscale（私有网络 UI）→ 网络绑定（私有网络 + 认证 + 防火墙）→ 反向代理（组织 SSO）→ 公网（最高风险，需要身份代理 + TLS）。

这跟防火墙规则的顺序是一个思路——从 deny-all 开始，按需 open port。核心原则是选能满足业务需求的最严格模式。

### Pre-flight 清单——为什么暴露前要盘点？

修改网络设置前必须记录：host 地址和 URL、认证方式、活跃频道、可达 agent、工具配置、外部凭证、备份位置。多用户场景下系统 = 共享权限，不是单机。

这跟 AWS 的 security group 审计是一个思路——开放端口前先确认谁需要访问、需要什么权限。

### 最小安全基线——为什么默认拒绝执行？

安全基线从最严格开始：loopback 绑定 + token 认证 + 非主会话沙箱 + 拒绝执行。权限增量扩展。默认拒绝执行是因为 exec 是最危险的能力——agent 能运行任意命令。

这跟最小权限原则是一个思路——先 deny-all，按需 grant。只有定义了具体威胁模型后才放宽执行权限。

### DM 和群聊暴露——为什么把消息平台当不可信？

消息平台不在信任边界内，应该用 pairing 或严格 allowlist 而不是开放策略。群聊要求用户 @mention，共享频道路由到无个人凭证的 agent。pairing 批准发送者但不创建主机安全边界。

这跟 OAuth scope 限制是一个思路——每个客户端只能访问需要的资源。pairing 不等于主机安全隔离。

### 回滚计划——为什么过曝后要立即收缩？

过曝的应急方案：回退到 loopback 绑定 + 禁用所有频道 + 拒绝执行。然后轮换所有 token 和凭证、移除通配符发送者、审查日志、重跑审计。

这跟数据库紧急维护模式是一个思路——只保留最小连接，暂停所有写操作，修复后逐步恢复。

---

### 网关可见性指南 / Gateway Visibility Guide

This document outlines a preparation and reversal guide for making the system accessible outside local networks. It applies to LAN, tailnet, or proxy setups, and helps review deployments or reverse risky configurations. A warning notes that administrators must understand access, authentication, and tool usage before expanding visibility; otherwise, they should revert to local modes.

本文档是网关对外暴露的准备和回滚指南，适用于 LAN、tailnet 或代理配置场景。帮助审查部署或撤销高风险配置。警告：管理员在扩大可见性前必须了解访问控制、认证和工具使用情况，否则应回退到本地模式。

### 选择暴露模式 / Choose the Exposure Pattern

Operators should select the most restrictive option that meets their needs.

操作员应选择能满足需求的最严格模式。

- **Local plus SSH:** Best for individual administration; keep bindings local and use tunnels.
- **Local plus Tailscale:** Ideal for private network UI access; rely on identity headers.
- **Network binding:** Suitable for private networks; requires authentication and firewalls.
- **Reverse proxy:** For organizational SSO; needs strict proxy rules and user allowlists.
- **Public internet:** High-risk; requires identity proxies, TLS, and strict limits.

- **Local + SSH：** 适合个人管理，保持本地绑定 + 隧道。
- **Local + Tailscale：** 适合私有网络 UI 访问，依赖 identity headers。
- **网络绑定：** 适合私有网络，需要认证 + 防火墙。
- **反向代理：** 适合组织 SSO，需要严格的代理规则和 user allowlist。
- **公网：** 高风险，需要身份代理 + TLS + 严格限制。

Direct public forwarding should be avoided in favor of identity-aware proxies.

直接公网转发应避免，优先使用身份感知代理。

### Pre-flight 清单 / Pre-flight Inventory

Before modifying network settings, document the host details, URLs, authentication methods, active channels, accessible agents, tool profiles, external credentials, and backup locations. If multiple users interact with the system, treat it as shared authority rather than isolated hosting.

修改网络设置前，记录 host 地址和 URL、认证方式、活跃频道、可达 agent、工具配置、外部凭证、备份位置。多用户场景下系统 = 共享权限，不是单机托管。

### 基线检查 / Baseline Checks

Execute diagnostic and security commands to identify issues. Fix critical problems immediately. When testing remote connections, explicitly provide credentials rather than relying on local configurations.

执行诊断和安全命令发现问题，立即修复严重问题。测试远程连接时显式提供凭证，不依赖本地配置。

```bash
# Run diagnostics, deep audits, and health checks
openclaw doctor
openclaw security audit --deep
openclaw health

# Probe remote URLs with explicit tokens
curl -H "Authorization: Bearer $TOKEN" https://gateway.example.com/health
```

### 最小安全基线 / Minimum Safe Baseline

Begin with a restrictive setup: local binding, token authentication, per-channel peer scoping, non-main sandboxing, messaging tool profiles, and denied execution.

从严格配置开始：本地绑定、token 认证、per-channel peer scope、非主会话沙箱、消息工具配置、拒绝执行。

```json
{
  "bind": "loopback",
  "auth": "token",
  "dmScope": "per-channel-peer",
  "sandbox": "non-main",
  "tools": { "profile": "messaging" },
  "exec": "deny"
}
```

Expand permissions incrementally. The default execution denial stops all commands; relax this only after defining specific threat models.

权限增量扩展。默认拒绝执行会阻止所有命令，只有定义了具体威胁模型后才放宽。

### DM 和群聊暴露 / DM and Group Exposure

Treat messaging platforms as untrusted. Use pairing or strict allowlists instead of open policies. Avoid combining wildcard allowlists with broad tool access. Require user mentions in group chats. Route shared channels to agents lacking personal credentials. Remember that pairing approves a sender but does not create a host security boundary.

把消息平台当不可信。用 pairing 或严格 allowlist 代替开放策略。避免通配符 allowlist + 宽工具权限的组合。群聊要求用户 @mention。共享频道路由到无个人凭证的 agent。记住 pairing 批准发送者但不创建主机安全边界。

### 反向代理检查 / Reverse Proxy Checks

Identity-aware proxies must authenticate users and block direct port access. Restrict trusted proxy lists to specific IPs and ensure the proxy strips client headers. Define allowed users if serving multiple audiences. Use local loopback modes only when local processes are trusted. Always run deep security audits after modifying proxy settings.

身份感知代理必须认证用户并阻止直接端口访问。限制 trusted proxy 列表到特定 IP，确保代理移除 client headers。服务多受众时定义允许的用户列表。只有本地进程可信时才用本地 loopback 模式。修改代理设置后始终运行深度安全审计。

### 工具和沙箱审查 / Tool and Sandbox Review

Verify session environments before allowing remote access. Deny or require approval for host execution. Disable elevated tools unless necessary. Restrict browser, node, and cron tools for open surfaces. Limit bind mounts and avoid sensitive system paths. Use separate deployments for different trust boundaries, as prompts alone cannot isolate untrusted users.

允许远程访问前验证会话环境。拒绝或要求审批 host 执行。除非必要否则禁用提权工具。对开放表面限制浏览器、node、cron 工具。限制 bind mount，避免敏感系统路径。不同信任边界用独立部署，prompt 无法隔离不可信用户。

### 变更后验证 / Post-change Validation

Following any adjustment, rerun deep audits. Test both authorized and unauthorized connections. Ensure logs hide sensitive data, routing is correct, and high-impact tools require approval. Document any remaining warnings and do not make further changes until the current state is fully understood.

任何调整后重跑深度审计。测试授权和未授权连接。确保日志隐藏敏感数据、路由正确、高影响工具需要审批。记录剩余警告，完全理解当前状态前不再做修改。

### 回滚计划 / Rollback Plan

If overexposure occurs, revert to local binding, disable all messaging channels, and deny execution.

过曝时回退到本地绑定 + 禁用所有消息频道 + 拒绝执行。

```json
{
  "bind": "loopback",
  "channels": "disabled",
  "exec": "deny"
}
```

Halt public routes, rotate all tokens and credentials, remove wildcard senders, review logs, rerun audits, and restore access using the most restrictive viable method.

停止公网路由，轮换所有 token 和凭证，移除通配符发送者，审查日志，重跑审计，用最严格的可行方法恢复访问。

### 审查清单 / Review Checklist

- Ensure the system remains loopback-only unless documented otherwise.
- Verify non-local access has proper authentication and firewalls.
- Check proxy IP restrictions and header controls.
- Confirm DM pairing and group mention requirements.
- Verify shared channels lack personal credentials.
- Ensure non-main sessions use sandboxes.
- Confirm host execution is gated and logs are redacted.
- Verify critical findings are fixed and reversal procedures are tested.

- 确保系统保持 loopback-only，除非有文档说明例外。
- 验证非本地访问有正确的认证和防火墙。
- 检查代理 IP 限制和 header 控制。
- 确认 DM pairing 和群聊 @mention 要求。
- 验证共享频道无个人凭证。
- 确保非主会话使用沙箱。
- 确认 host 执行有审批且日志脱敏。
- 验证关键问题已修复且回滚流程已测试。
