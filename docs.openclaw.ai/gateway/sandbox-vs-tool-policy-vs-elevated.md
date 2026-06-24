# Sandbox vs Tool Policy vs Elevated——三层控制分离

## 架构精读

> 跳过不影响阅读翻译正文。

### 三层控制——为什么需要分离运行位置、工具可用性和执行特权？

OpenClaw 有三层独立控制：沙箱决定工具在哪里运行（宿主机 vs 容器），工具策略决定哪些工具可用，elevated 作为沙箱外的执行应急出口。这跟网络安全的三层防御是一个思路——网络隔离 + 应用权限 + 紧急通道，三层独立不互相替代。

混淆这三层是常见的配置错误来源。比如"工具 X 被阻止"可能是沙箱工具策略的问题，也可能是 elevated 没启用。`openclaw sandbox explain` 可以看到实际生效的配置。

### Deny 总是赢——为什么工具策略是硬限制？

工具策略多层叠加（base profile + provider profile + global/agent policy + sandbox policy），但 `deny` 总是赢。如果 `allow` 非空，未列出的都被阻止。工具策略按名字过滤，不检查 `exec` 内的副作用。这跟防火墙规则是一个思路——deny 规则优先于 allow，按名字匹配而非内容检查。

`/exec` 命令不能覆盖被 deny 的工具，工具策略是硬限制。

### Elevated 作为应急出口——为什么只影响执行？

Elevated 只让 `exec` 在沙箱外运行，不授予额外工具权限，不覆盖工具的 allow/deny 规则。这跟 sudo 的应急模式是一个思路——临时提权执行特定命令，不改变用户的整体权限。如果已经是直连模式（无沙箱），elevated 是空操作。

### 沙箱监牢的常见修复——怎么排查"工具被阻止"？

"工具 X 被沙箱工具策略阻止"：禁用沙箱（`sandbox.mode=off`），或从 `sandbox.tools.deny` 移除，或添加到 `sandbox.tools.allow`。查看 `openclaw logs` 的 `agents/tool-policy` 条目定位具体规则。

"以为是 main 但被沙箱化了"：non-main 模式下，群组/频道会话不是 main。使用主会话 key，或把模式切换为 off。

---

### 概述 / Overview

OpenClaw utilizes three distinct management mechanisms. First, isolation determines the execution environment for utilities. Second, utility rules dictate availability. Third, host execution serves as an external escape mechanism for restricted environments.

OpenClaw 使用三层独立控制。第一层隔离决定工具执行环境。第二层工具策略决定可用性。第三层宿主机执行作为受限环境的应急出口。

### 快速排查 / Rapid Troubleshooting

To inspect actual system behavior, utilize the explanation command.

查看系统实际行为使用 explain 命令：

```bash
openclaw sandbox explain
openclaw sandbox explain --session agent:main:main
openclaw sandbox explain --agent work
openclaw sandbox explain --json
```

You can append flags for specific sessions, agents, or JSON output. This reveals the active mode, session status, effective permissions, and configuration paths for fixes.

可以附加特定 session、agent 或 JSON 输出的标志。显示活跃模式、session 状态、生效权限和修复的配置路径。

### 隔离：执行环境 / Isolation: Execution Environments

The execution location is managed via the default mode configuration. Settings include turning it completely off, restricting only non-primary sessions, or isolating everything.

执行位置通过默认模式配置管理。选项：完全关闭、只隔离非主会话、全部隔离。

#### 目录挂载和安全 / Directory Bindings and Security

Docker bindings bypass filesystem restrictions, exposing host directories to containers. Omitting access modes defaults to read-write, though read-only is safer for sensitive data. Shared scopes disregard agent-specific bindings. The system validates sources multiple times to prevent symlink-based directory escapes, rejecting invalid leaf paths. Exposing the Docker socket grants extensive host control and requires deliberate intent. Workspace access settings operate independently from binding modes.

Docker 挂载绕过文件系统限制，把宿主机目录暴露给容器。省略访问模式默认 read-write，敏感数据建议 read-only。Shared 作用域忽略 agent 特定挂载。系统多次验证来源防止基于 symlink 的目录逃逸，拒绝无效的叶路径。暴露 Docker socket 授予广泛的宿主机控制，需要刻意为之。Workspace 访问设置独立于挂载模式运行。

### 工具策略：可用性和调用 / Utility Rules: Availability and Invocation

Availability depends on multiple configuration layers, including base profiles, provider-specific profiles, and global or agent-level allowances. Isolation-specific rules apply only when restrictions are active.

可用性取决于多层配置：base profile、provider 特定 profile、全局/agent 级 allow/deny。隔离特定规则只在限制活跃时生效。

Key principles include:

- Denials always take precedence.
- Non-empty allowlists block unlisted items.
- Policies act as hard limits that execution commands cannot bypass.
- Filtering occurs by utility name, ignoring internal command side effects.
- Session defaults modified via execution commands do not grant new access.
- Provider configurations accept specific model identifiers.
- Audit logs record policy enforcement details.

关键原则：

- Deny 总是优先。
- 非空 allowlist 阻止未列出的项。
- 策略是硬限制，执行命令不能绕过。
- 按工具名过滤，不检查内部命令副作用。
- 通过执行命令修改的 session 默认值不授予新访问。
- Provider 配置接受特定模型标识。
- 审计日志记录策略执行详情。

#### 工具分组和快捷方式 / Utility Categories and Shortcuts

Policies support grouped expansions for multiple utilities.

策略支持工具分组扩展：

```json5
{
  tools: {
    sandbox: {
      tools: {
        allow: ["group:runtime", "group:fs", "group:sessions", "group:memory"]
      }
    }
  }
}
```

Categories include runtime execution, filesystem operations, session management, memory, web access, UI elements, automation, messaging, nodes, agents, media, core built-ins, and plugins.

分组包括：运行时执行、文件系统操作、session 管理、记忆、Web 访问、UI 元素、自动化、消息、节点、agent、媒体、核心内置和插件。

For isolated external servers, the policy acts as a secondary gate. If configured servers only display built-in utilities, add the specific plugin group or server-prefixed names to the additional allowlist, then reload the gateway.

对隔离的外部服务器，策略作为第二道门。如果配置的服务器只显示内置工具，把特定插件组或服务器前缀名称添加到额外 allowlist，然后重新加载网关。

### 宿主机执行：外部命令运行 / Host Execution: External Command Running

This feature solely impacts execution commands without providing additional utilities. When isolated, activating this mode runs commands externally, though approvals might still be necessary. Using the full variant skips session approvals. It remains inactive if already running directly and cannot override existing allow or deny rules. It adheres to standard target rules without granting arbitrary cross-host capabilities.

此功能只影响执行命令，不提供额外工具。隔离时激活此模式在沙箱外运行命令，但审批可能仍然必要。full 变体跳过 session 审批。如果已经是直连模式则不活跃，不能覆盖现有 allow/deny 规则。遵循标准目标规则，不授予任意跨主机能力。

Configuration gates involve global or agent-specific enablement and sender allowlists per provider.

配置门控涉及全局/agent 级启用和每个 provider 的发送者 allowlist。

### 标准隔离修复 / Standard Isolation Corrections

#### 解决工具被阻止 / Resolving Blocked Utility Errors

Resolve this by disabling isolation globally or per-agent. Alternatively, remove the utility from the deny list or add it to the allow list. Review audit logs to identify the specific blocking rule.

全局或 per-agent 禁用隔离来解决。或从 deny 列表移除工具，或添加到 allow 列表。查看审计日志定位具体的阻止规则。

#### 主会话意外被隔离 / Unexpected Isolation in Primary Sessions

When configured for non-primary sessions, group or channel keys are treated as isolated. Utilize the primary session key or disable the mode entirely.

配置为非主会话隔离时，群组/频道会话被视为隔离的。使用主会话 key 或完全禁用模式。

### 相关文档 / Associated Documentation

Consult documentation for comprehensive isolation references, multi-agent overrides, and elevated execution modes.

参考文档获取完整的隔离参考、多 agent 覆盖和 elevated 执行模式。
