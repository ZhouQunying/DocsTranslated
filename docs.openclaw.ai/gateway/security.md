# Security

## 架构精读

> 跳过不影响阅读翻译正文。

### "个人助手"信任模型——为什么不是多租户？

OpenClaw 的安全边界是"一个 gateway 对应一个受信任的操作员"。
它明确不是对抗性的多租户安全边界。
这跟 SSH 的信任模型类似——你信任持有 key 的人，而不是在同一个 SSH server 上隔离多个互不信任的用户。
对于对抗性用户，指导是拆分信任边界：独立的 gateway、独立的凭证，最好是独立的 OS 用户或主机。

### 分层防御——为什么假设 model 不可信？

访问控制哲学：Identity first → 作用域 next → Model last。
假设 model 输出可被操纵（prompt injection 未解决），所以设计为有限的 blast radius。
先验证身份（token/password/trusted-proxy），再限制作用域（tool deny list、workspace 限制），最后才信任 model 输出（exec approvals、sandboxing）。
这跟银行金库是一个思路——先验身份，再限权限，最后监控行为。

### Session 隔离——为什么按 channel + peer 拆分？

`dmScope: "per-channel-peer"` 配置让每个 channel 与 peer 的组合有独立的 session。
这防止跨用户上下文泄漏，同时保持群聊隔离。
不同用户的对话不会互相污染——即使他们在同一个 gateway 上。

### Docker 端口发布——为什么绕过 host 防火墙？

Docker 发布的 container 端口绕过 host `INPUT` chain 的 iptables 规则。
必须在 `DOCKER-USER` chain 中添加过滤规则才能生效。
这是 Docker 网络架构的已知行为——很多用户在部署时忽略了这一点。

### 事件响应——四阶段流程是什么？

Contain（遏制）→ Rotate（轮换）→ Audit（审计）→ Collect（收集）。
先停止进程、关闭暴露、冻结访问；然后轮换所有凭证；再审计 logs 和 config 变更；最后收集时间戳和攻击者输入作为证据。

---

OpenClaw uses a **"personal assistant"** trust model: one trusted operator per gateway, explicitly **not an adversarial multi-tenant security boundary**. For adversarial users, the guidance is to **split trust boundaries** (separate gateways + credentials, ideally separate OS users or hosts). The security audit tool (`openclaw security audit`) can automatically check and fix common configuration issues.

OpenClaw 采用 **"个人助手"** 信任模型：每个 gateway 一个受信任的操作员，明确**不是对抗性的多租户安全边界**。对于对抗性用户，指导是**拆分信任边界**（独立的 gateway + 凭证，最好是独立的 OS 用户或主机）。安全审计工具（`openclaw security audit`）可自动检查和修复常见配置问题。

## 信任模型

OpenClaw operates under a **"personal assistant"** model: one trusted operator per gateway. It is explicitly **not an adversarial multi-tenant security boundary**. For adversarial users, the guidance is to **split trust boundaries** (separate gateways + credentials, ideally separate OS users or hosts).

OpenClaw 在 **"个人助手"** 模型下运行：每个 gateway 一个受信任的操作员。它明确**不是对抗性的多租户安全边界**。对于对抗性用户，指导是**拆分信任边界**（独立的 gateway + 凭证，最好是独立的 OS 用户或主机）。

### 访问控制哲学

Core principle: **Identity first** → **Scope next** → **Model last**. Assume model output can be manipulated; design for limited blast radius.

核心立场：**身份优先** → **作用域其次** → **模型最后**。假设 model 输出可被操纵，设计为有限的 blast radius。

This means:
这意味着：

- Verify identity first (token/password/trusted-proxy)
- 先验证身份（token/password/trusted-proxy）
- Then restrict scope (tool deny list, workspace limits)
- 再限制作用域（tool deny list、workspace 限制）
- Only then trust model output (exec approvals, sandboxing)
- 最后才信任 model 输出（exec approvals、sandboxing）

### DM Policies

Four policies control unknown senders:

四种策略控制未知发送者：

- **pairing** (default): Unknown senders receive a pairing code
- **配对模式**（默认）：未知发送者收到配对码
- **allowlist**: Unknown senders are blocked immediately
- **白名单模式**：未知发送者直接阻止
- **open**: Requires explicit `"*"` in the allowlist
- **开放模式**：需要显式 `"*"` 在 allowlist 中
- **disabled**: DMs are ignored
- **禁用模式**：DM 被忽略

### Session 隔离

For multi-user setups, use:

多用户设置时，使用：

```json5
{
  session: { dmScope: "per-channel-peer" }
}
```

This **prevents cross-user context leakage while keeping group chat isolation**. Each channel + peer combination has its own session and they don't pollute each other.

这**防止跨用户上下文泄漏，同时保持群聊隔离**。每个 channel + peer 组合有独立的 session，不会互相污染。

## 安全审计工具

Run audits regularly:

定期运行审计：

```bash
openclaw security audit
openclaw security audit --deep
openclaw security audit --fix
openclaw security audit --json
```

The `--fix` flag is **deliberately narrow** — it only flips open group policies to allowlists, restores redaction settings, and tightens file permissions. It won't auto-fix complex configuration issues.

`--fix` flag **故意狭窄**，只翻转开放的 group policies 为 allowlists，恢复 redaction 设置，收紧文件权限。不会自动修复复杂的配置问题。

## Hardened Baseline

```json5
{
  gateway: {
    mode: "local",
    bind: "loopback",
    auth: { mode: "token", token: "replace-with-long-random-token" }
  },
  session: {
    dmScope: "per-channel-peer"
  },
  tools: {
    profile: "messaging",
    deny: ["group:automation", "group:runtime", "group:fs", "sessions_spawn", "sessions_send"],
    fs: { workspaceOnly: true },
    exec: { security: "deny", ask: "always" }
  },
  channels: {
    whatsapp: { dmPolicy: "pairing", groups: { "*": { requireMention: true } } }
  }
}
```

This configuration:
这个配置：

- Gateway binds to loopback only — no network exposure
- Gateway 只绑定 loopback，不暴露到网络
- Enforces token authentication
- 强制 token 认证
- Sessions isolated by channel + peer
- Session 按 channel + peer 隔离
- Tools restricted to messaging profile, dangerous groups denied
- Tools 限制在 messaging profile，deny 危险组
- File operations restricted to workspace
- 文件操作限制在 workspace 内
- Exec requires approval every time
- Exec 需要每次批准
- WhatsApp groups require mention to respond
- WhatsApp 群组需要 mention 才响应

## 凭证存储位置

Credentials are stored under `~/.openclaw/`, including WhatsApp credentials, Telegram/Discord/Slack tokens, pairing allowlists, model auth profiles, and session transcripts. Directory permissions should be `700`, file permissions `600`.

凭证存储在 `~/.openclaw/` 下，包括 WhatsApp 凭证、Telegram/Discord/Slack tokens、配对 allowlists、model auth profiles 和 session transcripts。目录权限应为 `700`，文件权限应为 `600`。

## Prompt Injection

The documentation warns that **prompt injection is unsolved** — system prompt guardrails are only **soft guidelines**. Hard enforcement comes from tool policy, exec approvals, sandboxing, and channel allowlists.

文档警告 **prompt injection 未解决**，system prompt guardrails 只是**软指导**。硬执行来自 tool policy、exec approvals、sandboxing 和 channel allowlists。

Red flags include messages like: "ignore your instructions", "dump your filesystem", "reveal your hidden instructions".

危险信号包括消息如："ignore your instructions"、"dump your filesystem"、"reveal your hidden instructions"。

### Model Strength

The guidance is clear: **use the latest-generation, best model** for tool-enabled agents. Smaller models carry higher prompt-injection risk.

指导很明确：**使用最新一代、最佳 model** 用于 tool-enabled agents。较小的 model 携带更高的 prompt-injection 风险。

## Reverse Proxy 配置

```yaml
gateway:
  trustedProxies:
    - "10.0.0.1"
  auth:
    mode: password
    password: ${OPENCLAW_GATEWAY_PASSWORD}
```

Proxies must **override** forwarding headers, not append. Good practice:

Proxies 必须**覆盖** forwarding headers，不是追加。好的做法：

```nginx
proxy_set_header X-Forwarded-For $remote_addr;
```

Bad practice:

坏的做法：

```nginx
proxy_set_header X-Forwarded-For "$proxy_add_x_forwarded_for";
```

The latter appends to existing headers, which can be spoofed.

后者追加到已有 header，可能被伪造。

## Network Exposure

Gateway binds to loopback by default on port `18789`. Non-loopback binds increase the attack surface and require auth + firewalling. The documentation recommends **Tailscale Serve over LAN binds**.

Gateway 默认绑定 loopback，端口 `18789`。Non-loopback binds 扩大攻击面，需要 auth + firewalling。文档推荐 **Tailscale Serve 优于 LAN binds**。

### Docker + UFW

Published container ports bypass host `INPUT` rules, so rules must go in `DOCKER-USER`:

发布的 container 端口绕过 host `INPUT` 规则，所以规则必须放在 `DOCKER-USER`：

```bash
-A DOCKER-USER -s 127.0.0.0/8 -j RETURN
-A DOCKER-USER -s 10.0.0.0/8 -j RETURN
-A DOCKER-USER -m conntrack --ctstate NEW -j DROP
```

This allows loopback and private networks, blocking all other new connections.

这允许 loopback 和私有网络，阻止其他新连接。

## Browser Control Risks

Browser profiles are **sensitive state**. Recommendations include using a dedicated profile, avoiding personal daily driver profiles, and disabling browser control for sandboxed agents unless trusted.

Browser profiles 是**敏感状态**。建议使用专用 profile，避免个人日常 driver profiles。除非信任，否则对 sandboxed agents 关闭 browser control。

### SSRF Policy

Private/internal destinations are blocked by default. Opt-in requires explicitly setting `dangerouslyAllowPrivateNetwork: true`.

Private/internal 目的地默认阻止。Opt-in 需要显式设置 `dangerouslyAllowPrivateNetwork: true`。

## Sandboxing

Two approaches: full Gateway inside Docker, or tool sandbox + host gateway. Workspace access options:

两种方法：完整 Gateway 在 Docker 内，或 tool sandbox + host gateway。Workspace 访问选项：

- `"none"`: Workspace access denied
- `"none"`：workspace 禁止访问
- `"ro"`: Read-only mount at `/agent`
- `"ro"`：只读挂载到 `/agent`
- `"rw"`: Read-write mount at `/workspace`
- `"rw"`：读写挂载到 `/workspace`

## Per-Agent Profiles

### Read-Only Agent 示例

```json5
{
  agents: {
    list: [
      {
        id: "family",
        sandbox: {
          mode: "all",
          scope: "agent",
          workspaceAccess: "ro"
        },
        tools: {
          allow: ["read"],
          deny: ["write", "edit", "apply_patch", "exec", "process", "browser"]
        }
      }
    ]
  }
}
```

This agent:
这个 agent：

- Fully sandboxed (mode: "all")
- 完全 sandboxed（mode: "all"）
- Workspace read-only (ro)
- Workspace 只读（ro）
- Can only read — no write/edit/exec/browser
- 只能 read，不能 write/edit/exec/browser

## Incident Response

The documentation outlines four phases:

文档概述四个阶段：

1. **Contain**: Stop processes, close exposure, freeze access
1. **Contain**（遏制）：停止进程，关闭暴露，冻结访问
2. **Rotate**: Gateway auth, remote secrets, provider credentials
2. **Rotate**（轮换）：gateway auth、remote secrets、provider credentials
3. **Audit**: Logs, transcripts, config changes
3. **Audit**（审计）：logs、transcripts、config changes
4. **Collect**: Timestamps, transcripts, attacker input
4. **Collect**（收集）：timestamps、transcripts、attacker input

## Dangerous Flags

The audit tracks unsafe flags, including:

审计跟踪不安全的 flags，包括：

- `allowInsecureAuth`: Allows insecure authentication
- `allowInsecureAuth`：允许不安全的认证
- `dangerouslyDisableDeviceAuth`: Disables device authentication
- `dangerouslyDisableDeviceAuth`：禁用设备认证
- `dangerouslyAllowNameMatching`: Allows name matching across channels
- `dangerouslyAllowNameMatching`：允许名称匹配（跨多个 channels）
- `dangerouslyAllowPrivateNetwork`: Allows browser SSRF to private networks
- `dangerouslyAllowPrivateNetwork`：允许 browser SSRF 到私有网络

These should remain unset in production environments.

这些在生产环境应保持未设置。

## Reporting

Vulnerabilities should be reported to security@openclaw.ai. Do not disclose publicly until fixed.

漏洞应报告到 security@openclaw.ai，在修复前不要公开发布。
