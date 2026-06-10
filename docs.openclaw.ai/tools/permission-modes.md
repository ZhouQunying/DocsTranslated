# Permission modes

## 架构精读

> 跳过不影响阅读翻译正文。

### Agent 要跑 shell 命令——谁来批准？

问题不是"能不能跑",而是"由谁决定能跑"。`tools.exec.mode` 是一个五档旋钮：从"全禁"到"全放"。

关键洞察：这里有**两层**独立的权限控制。OpenClaw 的 `exec.mode` 是一层,宿主的本地 approvals 文件是另一层。最终结果取两者中更严格的那个。跟防火墙规则一样：内层放行了外层还得放行才算通。

`auto` 模式最有意思：先走白名单（确定安全的直接过）,白名单没命中的走自动审查,自动审查也拿不准的才丢给人类。三级漏斗,大部分命令在第一级就通过了。

ACPX 又是独立的一层——因为它是非交互式的,没有 TTY 让你点"允许"。所以它有自己的 `permissionMode` 设置,跟宿主 exec 批准互不干涉。

---

> Permission modes decide how much authority an agent has before it can run host
> commands, write files, or ask a backend harness for extra access. Start with
> `tools.exec.mode: "auto"` when you want OpenClaw to use allowlists first, then
> Codex native auto-review or a human approval route for misses.

Permission modes 决定 agent 在跑宿主命令、写文件、或向后端 harness 请求额外权限之前有多大权限。想让 OpenClaw 先查白名单、白名单没命中再走 Codex 原生自动审查或人类审批时,用 `tools.exec.mode: "auto"`。

> Permission mode is separate from `tools.exec.host=auto`. `tools.exec.host` chooses where a command runs. `tools.exec.mode` chooses how host exec is approved.

[展开: 注意] Permission mode 跟 `tools.exec.host=auto` 是分开的。`tools.exec.host` 选命令在**哪里**跑。`tools.exec.mode` 选宿主 exec **怎么被批准**。

## 推荐默认

> Use `auto` for coding agents that need useful host access without making every miss a human prompt:

编码 agent 需要有用的宿主访问、又不想每个没命中的都弹人类审批时,用 `auto`:

```bash
openclaw config set tools.exec.mode auto
openclaw approvals get
openclaw gateway restart
```

> Then verify the effective policy:

然后验证生效的策略:

```bash
openclaw exec-policy show
```

> In `auto` mode, OpenClaw runs deterministic allowlist matches directly. Approval misses go through OpenClaw's native auto reviewer first, then fall back to the configured human approval route when needed.

`auto` 模式下,OpenClaw 直接跑确定性白名单命中的命令。没命中的先过 OpenClaw 原生自动审查,需要时再回退到配置的人类审批路径。

## OpenClaw 宿主 exec 模式

> `tools.exec.mode` is the normalized policy surface for host `exec`.

`tools.exec.mode` 是宿主 `exec` 的归一化策略面。

| 模式        | 行为                                   | 什么时候用                                        |
| ----------- | -------------------------------------- | ------------------------------------------------- |
| `deny`      | 禁止宿主 exec。                        | 不允许任何宿主命令。                              |
| `allowlist` | 只跑白名单里的命令。                   | 你有一组已知安全的命令集。                        |
| `ask`       | 白名单命中直接跑,没中就问人。         | 人类应该审查新命令。                              |
| `auto`      | 白名单命中直接跑,没中走自动审查。     | 编码会话需要实用的有防护访问。                    |
| `full`      | 不带 prompt 跑宿主 exec。             | 这个受信宿主 / 会话应该跳过审批门。              |

> For the full host exec policy, local approvals file, allowlist schema, safe bins, and forwarding behavior, see Exec approvals.

完整的宿主 exec 策略、本地 approvals 文件、白名单 schema、安全二进制、转发行为见 [Exec approvals](/tools/exec-approvals)。

## Codex Guardian 映射

> For native Codex app-server sessions, `tools.exec.mode: "auto"` maps to Codex Guardian-reviewed approvals when the local Codex requirements allow it.

原生 Codex app-server 会话中,`tools.exec.mode: "auto"` 在本地 Codex 条件允许时映射到 Codex Guardian 审查的审批。OpenClaw 通常发:

| Codex 字段          | 典型值            |
| ------------------- | ----------------- |
| `approvalPolicy`    | `on-request`      |
| `approvalsReviewer` | `auto_review`     |
| `sandbox`           | `workspace-write` |

> In `auto` mode, OpenClaw does not preserve legacy unsafe Codex overrides such as `approvalPolicy: "never"` or `sandbox: "danger-full-access"`. Use `tools.exec.mode: "full"` only when you intentionally want the no-approval posture.

`auto` 模式下,OpenClaw 不保留旧的不安全 Codex 覆盖如 `approvalPolicy: "never"` 或 `sandbox: "danger-full-access"`。只有你确实想要"无审批"姿态时才用 `tools.exec.mode: "full"`。

> For app-server setup, auth order, and native Codex runtime details, see Codex harness.

App-server 设置、认证顺序、原生 Codex 运行时详情见 [Codex harness](/plugins/codex-harness)。

## ACPX harness 权限

> ACPX sessions are non-interactive, so they cannot click a TTY permission prompt. ACPX uses separate harness-level settings under `plugins.entries.acpx.config`:

ACPX 会话是非交互式的,没法点 TTY 权限提示。ACPX 在 `plugins.entries.acpx.config` 下用独立的 harness 级设置:

| 设置                        | 常见值          | 含义                                  |
| --------------------------- | --------------- | ------------------------------------- |
| `permissionMode`            | `approve-reads` | 只自动批准读操作。                    |
| `permissionMode`            | `approve-all`   | 自动批准写和 shell 命令。             |
| `permissionMode`            | `deny-all`      | 拒绝所有权限提示。                    |
| `nonInteractivePermissions` | `fail`          | 需要提示时中止。                      |
| `nonInteractivePermissions` | `deny`          | 拒绝提示并尽可能继续。               |

> Set ACPX permissions separately from OpenClaw exec approvals:

ACPX 权限和 OpenClaw exec 审批分开设:

```bash
openclaw config set plugins.entries.acpx.config.permissionMode approve-all
openclaw config set plugins.entries.acpx.config.nonInteractivePermissions fail
openclaw gateway restart
```

> Use `approve-all` as the ACPX break-glass equivalent of a no-prompt harness session.

`approve-all` 是 ACPX 的"打碎玻璃"等价物——无提示 harness 会话。设置详情和故障模式见 [ACP agents setup](/tools/acp-agents-setup#permission-configuration)。

## 选择模式

| 目标                                      | 配置                                                        |
| ----------------------------------------- | ----------------------------------------------------------- |
| 完全禁止宿主命令                          | `tools.exec.mode: "deny"`                                   |
| 只让已知安全命令跑                        | `tools.exec.mode: "allowlist"`                              |
| 每个新命令形态都问人                      | `tools.exec.mode: "ask"`                                    |
| 先 Codex/OpenClaw 自动审查再问人          | `tools.exec.mode: "auto"`                                   |
| 完全跳过宿主 exec 审批                    | `tools.exec.mode: "full"` 加匹配的宿主 approvals 文件      |
| 让非交互 ACPX 会话能写 / exec            | `plugins.entries.acpx.config.permissionMode: "approve-all"` |

> If a command still prompts or fails after changing mode, inspect both layers:

改了模式后命令仍然弹 prompt 或失败,检查两层:

```bash
openclaw approvals get
openclaw exec-policy show
```

> Host exec uses the stricter result of OpenClaw config and the host-local approvals file. ACPX harness permissions do not loosen host exec approvals, and host exec approvals do not loosen ACPX harness prompts.

宿主 exec 取 OpenClaw 配置和宿主本地 approvals 文件中更严格的结果。ACPX harness 权限不会放松宿主 exec 审批;宿主 exec 审批也不会放松 ACPX harness 提示。

## 相关

> - Exec approvals
> - Exec approvals - advanced
> - Codex harness
> - ACP agents setup

- [Exec approvals](/tools/exec-approvals)
- [Exec approvals - advanced](/tools/exec-approvals-advanced)
- [Codex harness](/plugins/codex-harness)
- [ACP agents setup](/tools/acp-agents-setup#permission-configuration)
