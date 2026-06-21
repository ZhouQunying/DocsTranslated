# Security

OpenClaw 采用 **"个人助手"** 信任模型: 每个 gateway 一个受信任的 operator,明确**不是对抗性的多租户安全边界**。对于对抗性用户,指导是**拆分信任边界**(独立的 gateway + 凭证,最好是独立的 OS 用户或 host)。安全审计工具 (`openclaw security audit`) 可自动检查和修复常见配置问题。

> **类比:SSH key + chroot + 防火墙规则的组合。** SSH key 是你的身份凭证,chroot 限制你能访问的目录,防火墙规则限制你能连接的网络。OpenClaw 安全模型类似: gateway auth (token/password) 是身份,workspace 限制是 chroot,binding + firewall 是网络边界。区别: SSH 是单一工具,OpenClaw 是完整的 agent 系统,需要多层防护。
>
> **架构要点:** 访问控制哲学: Identity first → Scope next → Model last (假设 model 可被操纵);DM policy 四种: pairing (默认)、allowlist、open、disabled;session 隔离用 `dmScope: "per-channel-peer"` 防止跨用户上下文泄漏;prompt injection **未解决**,system prompt 只是软指导,硬执行靠 tool policy + exec approvals + sandboxing;browser control profiles 是敏感状态,默认阻止 private/internal 网络 (SSRF),opt-in 需要 `dangerouslyAllowPrivateNetwork: true`;Docker 发布端口绕过 host INPUT 规则,必须在 DOCKER-USER chain 添加规则;incident response 四阶段: Contain → Rotate → Audit → Collect。

## 信任模型

OpenClaw 在 **"个人助手"** 模型下运行: 每个 gateway 一个受信任的 operator。它明确**不是对抗性的多租户安全边界**。对于对抗性用户,指导是**拆分信任边界**(独立的 gateway + 凭证,最好是独立的 OS 用户或 host)。

### 访问控制哲学

核心立场: **身份优先** → **作用域其次** → **模型最后**。假设 model 可被操纵,设计为有限的 blast radius (爆炸半径)。

这意味着:
- 先验证身份 (token/password/trusted-proxy)
- 再限制作用域 (tool deny list, workspace 限制)
- 最后才信任 model 的输出 (exec approvals, sandboxing)

### DM Policies

四种策略控制未知发送者:

- **pairing** (默认): 未知发送者收到配对码
- **allowlist**: 未知发送者直接阻止
- **open**: 需要显式 `"*"` 在 allowlist 中
- **disabled**: DM 被忽略

### Session 隔离

多用户设置时,使用:

```json5
{
  session: { dmScope: "per-channel-peer" }
}
```

这**防止跨用户上下文泄漏,同时保持群聊隔离**。每个 channel + peer 组合有独立的 session,不会互相污染。

## 安全审计工具

定期运行审计:

```bash
openclaw security audit
openclaw security audit --deep
openclaw security audit --fix
openclaw security audit --json
```

`--fix` flag **故意狭窄**,只翻转开放的 group policies 为 allowlists,恢复 redaction 设置,收紧文件权限。不会自动修复复杂的配置问题。

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

这个配置:
- Gateway 只绑定 loopback,不暴露到网络
- 强制 token 认证
- Session 按 channel + peer 隔离
- Tools 限制在 messaging profile,deny 危险组
- 文件操作限制在 workspace 内
- Exec 需要每次批准
- WhatsApp 群组需要 mention 才响应

## 凭证存储位置

凭证存储在 `~/.openclaw/` 下,包括 WhatsApp 凭证、Telegram/Discord/Slack tokens、配对 allowlists、model auth profiles、session transcripts。目录权限应为 `700`,文件权限应为 `600`。

## Prompt Injection

文档警告 **prompt injection 未解决**,system prompt guardrails 只是**软指导**。硬执行来自 tool policy、exec approvals、sandboxing、channel allowlists。

危险信号包括消息如: "ignore your instructions"、"dump your filesystem"、"reveal your hidden instructions"。

### Model Strength

指导很明确: **使用最新一代、最佳 model** 用于 tool-enabled agents。较小的 model 携带更高的 prompt-injection 风险。

## Reverse Proxy 配置

```yaml
gateway:
  trustedProxies:
    - "10.0.0.1"
  auth:
    mode: password
    password: ${OPENCLAW_GATEWAY_PASSWORD}
```

Proxies 必须**覆盖** forwarding headers,不是追加。好的做法:

```nginx
proxy_set_header X-Forwarded-For $remote_addr;
```

坏的做法:

```nginx
proxy_set_header X-Forwarded-For "$proxy_add_x_forwarded_for";
```

后者追加到已有 header,可能被伪造。

## Network Exposure

Gateway 默认绑定 loopback,端口 `18789`。Non-loopback binds 扩大攻击面,需要 auth + firewalling。文档推荐 **Tailscale Serve 优于 LAN binds**。

### Docker + UFW

发布的 container 端口绕过 host `INPUT` 规则,所以规则必须放在 `DOCKER-USER`:

```bash
-A DOCKER-USER -s 127.0.0.0/8 -j RETURN
-A DOCKER-USER -s 10.0.0.0/8 -j RETURN
-A DOCKER-USER -m conntrack --ctstate NEW -j DROP
```

这允许 loopback 和私有网络,阻止其他新连接。

## Browser Control Risks

Browser profiles 是**敏感状态**。建议包括使用专用 profile,避免个人日常 driver profiles,除非信任否则对 sandboxed agents 关闭 browser control。

### SSRF Policy

Private/internal 目的地默认阻止。Opt-in 需要显式设置 `dangerouslyAllowPrivateNetwork: true`。

## Sandboxing

两种方法: 完整 Gateway 在 Docker 内,或 tool sandbox + host gateway。Workspace 访问选项:

- `"none"`: workspace 禁止访问
- `"ro"`: 只读挂载到 `/agent`
- `"rw"`: 读写挂载到 `/workspace`

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

这个 agent:
- 完全 sandboxed (mode: "all")
- Workspace 只读 (ro)
- 只能 read,不能 write/edit/exec/browser

## Incident Response

文档概述四个阶段:

1. **Contain** (遏制): 停止进程,关闭暴露,冻结访问
2. **Rotate** (轮换): gateway auth, remote secrets, provider credentials
3. **Audit** (审计): logs, transcripts, config changes
4. **Collect** (收集): timestamps, transcripts, attacker input

## Dangerous Flags

审计跟踪不安全的 flags,包括:

- `allowInsecureAuth`: 允许不安全的认证
- `dangerouslyDisableDeviceAuth`: 禁用设备认证
- `dangerouslyAllowNameMatching`: 允许名称匹配 (跨多个 channels)
- `dangerouslyAllowPrivateNetwork`: 允许 browser SSRF 到私有网络

这些在生产环境应保持未设置。

## Reporting

漏洞应报告到 security@openclaw.ai,在修复前不要公开发布。
