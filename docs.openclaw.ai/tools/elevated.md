# Elevated mode

## 架构精读

> 跳过不影响阅读翻译正文。

### 沙箱装不了系统包——怎么让 Agent 临时出去跑？

场景：Agent 跑在沙箱容器里，需要执行 `apt install` 或访问宿主的 GPU。沙箱里做不了这事。你也不想彻底关掉沙箱——大部分时候它的隔离是你要的。

这就是 elevated 解决的问题：**不关沙箱，但允许特定命令"逃出去"在宿主上跑**。

### 三个级别、一个关键区分

- `on` / `ask`：逃出沙箱，但命令仍然过审批流程（白名单 + 用户确认）
- `full`：逃出沙箱 + 跳过审批。等于 Agent 在宿主上裸跑。
- `off`：回到沙箱。

关键：elevated 只管"在哪里跑"这一个维度。它**不覆盖**工具策略里的其他限制（比如被禁的工具还是被禁的）。说白了——elevated 是开门，不是给钥匙。进了门之后你能做什么，还是由审批策略说了算（除非你开到 `full`，那审批也跳了）。

### 为什么不直接关沙箱？

关沙箱 = 永久的。所有命令都在宿主跑，没有回头路。elevated 是可切换的——这次操作需要宿主权限就 `on`，完了就 `off` 回沙箱。运维可以在配置里把 elevated 锁死成 `off`，Agent 压根没法请求提权。

三层控制叠加：全局配置允不允许 → 运行时 Agent 允不允许 → 发消息的人在不在白名单里。三个 AND 都过了才放行。

---

> When an agent runs inside a sandbox, its `exec` commands are confined to the
> sandbox environment. **Elevated mode** lets the agent break out and run commands
> outside the sandbox instead, with configurable approval gates.

agent 跑在沙箱里时,它的 `exec` 命令被限制在沙箱环境内。**提权模式**让 agent 突破出去、在沙箱外面跑命令,带可配置的审批闸门。

> <Info>
>   Elevated mode only changes behavior when the agent is **sandboxed**. For
>   unsandboxed agents, exec already runs on the host.
> </Info>

[展开: 信息] 提权模式只在 agent **跑在沙箱里**时才改变行为。没沙箱的 agent,exec 本来就跑在宿主上。

## 指令

> Control elevated mode per-session with slash commands:

按会话用 slash 命令控制提权模式:

> | Directive        | What it does                                                           |
> | ---------------- | ---------------------------------------------------------------------- |
> | `/elevated on`   | Run outside the sandbox on the configured host path, keep approvals    |
> | `/elevated ask`  | Same as `on` (alias)                                                   |
> | `/elevated full` | Run outside the sandbox on the configured host path and skip approvals |
> | `/elevated off`  | Return to sandbox-confined execution                                   |

| 指令               | 做什么                                                |
| ------------------ | ----------------------------------------------------- |
| `/elevated on`     | 走配置好的宿主路径,在沙箱外跑,保留审批              |
| `/elevated ask`    | 同 `on`(别名)                                       |
| `/elevated full`   | 走配置好的宿主路径,在沙箱外跑,跳过审批              |
| `/elevated off`    | 回到沙箱内执行                                        |

> Also available as `/elev on|off|ask|full`.

`/elev on|off|ask|full` 也可以。

> Send `/elevated` with no argument to see the current level.

不带参数发 `/elevated` 看当前级别。

## 怎么工作的

> <Steps>
>   <Step title="Check availability">

[步骤 1: 检查是否可用]

> Elevated must be enabled in config and the sender must be on the allowlist:

提权必须在配置里开启,并且发送者必须在白名单里:

```json5
{
  tools: {
    elevated: {
      enabled: true,
      allowFrom: {
        discord: ["user-id-123"],
        whatsapp: ["+15555550123"],
      },
    },
  },
}
```

> <Step title="Set the level">

[步骤 2: 设级别]

> Send a directive-only message to set the session default:

发一条只含指令的消息来设会话默认:

```
/elevated full
```

> Or use it inline (applies to that message only):

或者用内联(只影响这条消息):

```
/elevated on run the deployment script
```

> <Step title="Commands run outside the sandbox">

[步骤 3: 命令在沙箱外跑]

> With elevated active, `exec` calls leave the sandbox. The effective host is
> `gateway` by default, or `node` when the configured/session exec target is
> `node`. In `full` mode, exec approvals are skipped. In `on`/`ask` mode,
> configured approval rules still apply.

提权激活后,`exec` 调用离开沙箱。生效的宿主默认是 `gateway`;配置 / 会话的 exec 目标是 `node` 时用 `node`。`full` 模式下跳过 exec 审批。`on`/`ask` 模式下仍按配置的审批规则走。

## 解析顺序

> 1. **Inline directive** on the message (applies only to that message)
> 2. **Session override** (set by sending a directive-only message)
> 3. **Global default** (`agents.defaults.elevatedDefault` in config)

1. 消息上的**内联指令**(只影响这条消息)
2. **会话覆盖**(发只含指令的消息来设)
3. **全局默认**(配置里的 `agents.defaults.elevatedDefault`)

## 可用性和白名单

> - **Global gate**: `tools.elevated.enabled` (must be `true`)
> - **Sender allowlist**: `tools.elevated.allowFrom` with per-channel lists
> - **Per-agent gate**: `agents.list[].tools.elevated.enabled` (can only further restrict)
> - **Per-agent allowlist**: `agents.list[].tools.elevated.allowFrom` (sender must match both global + per-agent)
> - **Discord fallback**: if `tools.elevated.allowFrom.discord` is omitted, `channels.discord.allowFrom` is used as fallback
> - **All gates must pass**; otherwise elevated is treated as unavailable

- **全局闸门**:`tools.elevated.enabled`(必须 `true`)
- **发送者白名单**:`tools.elevated.allowFrom`,按通道列名单
- **单 agent 闸门**:`agents.list[].tools.elevated.enabled`(只能进一步收紧)
- **单 agent 白名单**:`agents.list[].tools.elevated.allowFrom`(发送者必须同时匹配全局和单 agent)
- **Discord 回退**:`tools.elevated.allowFrom.discord` 没设时,用 `channels.discord.allowFrom` 作回退
- **所有闸门都得过**;否则提权被当作不可用

> Allowlist entry formats:

白名单条目格式:

> | Prefix                  | Matches                         |
> | ----------------------- | ------------------------------- |
> | (none)                  | Sender ID, E.164, or From field |
> | `name:`                 | Sender display name             |
> | `username:`             | Sender username                 |
> | `tag:`                  | Sender tag                      |
> | `id:`, `from:`, `e164:` | Explicit identity targeting     |

| 前缀                    | 匹配什么                            |
| ----------------------- | ----------------------------------- |
| (无前缀)               | 发送者 ID、E.164 号码、或 From 字段 |
| `name:`                 | 发送者显示名                        |
| `username:`             | 发送者 username                     |
| `tag:`                  | 发送者标签                          |
| `id:`、`from:`、`e164:` | 显式指定身份                        |

## 提权**不**控制什么

> - **Tool policy**: if `exec` is denied by tool policy, elevated cannot override it.
> - **Host selection policy**: elevated does not turn `auto` into a free cross-host override. It uses the configured/session exec target rules, choosing `node` only when the target is already `node`.
> - **Separate from `/exec`**: the `/exec` directive adjusts per-session exec defaults for authorized senders and does not require elevated mode.

- **工具策略**:`exec` 被工具策略拒绝时,提权也覆盖不了。
- **宿主选择策略**:提权不会把 `auto` 变成自由的跨宿主覆盖。它走配置 / 会话的 exec 目标规则,只有目标本来就是 `node` 时才选 `node`。
- **跟 `/exec` 是分开的**:`/exec` 指令调整授权发送者的会话 exec 默认,不需要提权模式。

> <Note>
>   The bash chat command (`!` prefix; `/bash` alias) is a separate gate that requires `tools.elevated` to be enabled in addition to its own `tools.bash.enabled` flag. Disabling elevated locks `!` shell commands out as well.
> </Note>

[展开: 注意] bash 聊天命令(`!` 前缀;`/bash` 别名)是单独一道闸门,除了它自己的 `tools.bash.enabled` 标志,还要求 `tools.elevated` 开。关掉提权也会一并锁死 `!` shell 命令。

## 相关

> - Exec tool — Shell command execution from the agent.
> - Exec approvals — Approval and allowlist system for `exec`.
> - Sandboxing — Gateway-level sandbox configuration.
> - Sandbox vs Tool Policy vs Elevated — How the three gates compose during a tool call.

- [Exec tool](/tools/exec) —— agent 跑 shell 命令。
- [Exec approvals](/tools/exec-approvals) —— `exec` 的审批和白名单系统。
- [沙箱](/gateway/sandboxing) —— Gateway 级的沙箱配置。
- [沙箱 vs 工具策略 vs 提权](/gateway/sandbox-vs-tool-policy-vs-elevated) —— 一次工具调用里,这三道闸门怎么组合。
