# Exec approvals — advanced

> Advanced exec-approval topics: the `safeBins` fast-path, interpreter/runtime
> binding, and approval-forwarding to chat channels (including native delivery).
> For the core policy and approval flow, see [Exec approvals](/tools/exec-approvals).

进阶的 exec 审批话题:`safeBins` 快速通道、解释器 / 运行时绑定,以及把审批转发到聊天通道(含原生投递)。核心策略和审批流程见 [Exec approvals](/tools/exec-approvals)。

## Safe bin(仅 stdin)

> `tools.exec.safeBins` defines a small list of **stdin-only** binaries (for
> example `cut`) that can run in allowlist mode **without** explicit allowlist
> entries. Safe bins reject positional file args and path-like tokens, so they
> can only operate on the incoming stream. Treat this as a narrow fast-path for
> stream filters, not a general trust list.

`tools.exec.safeBins` 定义一份小的**仅 stdin** 二进制列表(如 `cut`),在白名单模式下不需要显式白名单条目也能跑。Safe bin 拒绝位置文件参数和像路径的 token,所以它们只能在传入流上操作。把它当作流过滤器的窄快速通道,不是通用信任列表。

> <Warning>
> Do **not** add interpreter or runtime binaries (for example `python3`, `node`,
> `ruby`, `bash`, `sh`, `zsh`) to `safeBins`. If a command can evaluate code,
> execute subcommands, or read files by design, prefer explicit allowlist entries
> and keep approval prompts enabled. Custom safe bins must define an explicit
> profile in `tools.exec.safeBinProfiles.<bin>`.
> </Warning>

[展开: 警告] **不要**把解释器或运行时二进制(如 `python3`、`node`、`ruby`、`bash`、`sh`、`zsh`)加进 `safeBins`。命令本身就能 eval 代码、跑子命令或读文件的,优先用显式白名单条目,保留审批提示。自定义 safe bin 必须在 `tools.exec.safeBinProfiles.<bin>` 里定义显式 profile。

> Default safe bins:

默认 safe bin:

`cut`、`uniq`、`head`、`tail`、`tr`、`wc`

> `grep` and `sort` are not in the default list. If you opt in, keep explicit
> allowlist entries for their non-stdin workflows. For `grep` in safe-bin mode,
> provide the pattern with `-e`/`--regexp`; positional pattern form is rejected
> so file operands cannot be smuggled as ambiguous positionals.

`grep` 和 `sort` 不在默认列表里。你要 opt-in 的话,给它们的非 stdin 工作流保留显式白名单条目。`grep` 在 safe-bin 模式下,用 `-e`/`--regexp` 提供模式;位置模式形式会被拒,这样文件操作数就没法以模糊的位置参数夹带进来。

### Argv 校验和被拒标志

> Validation is deterministic from argv shape only (no host filesystem existence
> checks), which prevents file-existence oracle behavior from allow/deny
> differences. File-oriented options are denied for default safe bins; long
> options are validated fail-closed (unknown flags and ambiguous abbreviations are
> rejected).

校验完全靠 argv 形态判断(不查宿主文件系统是否存在),防止"放行 / 拒绝"差异变成"文件是否存在"的推断通道。默认 safe bin 的文件相关选项被拒;长选项按默认拒绝校验(未知 flag 和模糊缩写都被拒)。

> Denied flags by safe-bin profile:

按 safe-bin profile 的被拒标志:

- `grep`:`--dereference-recursive`、`--directories`、`--exclude-from`、`--file`、`--recursive`、`-R`、`-d`、`-f`、`-r`
- `jq`:`--argfile`、`--from-file`、`--library-path`、`--rawfile`、`--slurpfile`、`-L`、`-f`
- `sort`:`--compress-program`、`--files0-from`、`--output`、`--random-source`、`--temporary-directory`、`-T`、`-o`
- `wc`:`--files0-from`

> Safe bins also force argv tokens to be treated as **literal text** at execution
> time (no globbing and no `$VARS` expansion) for stdin-only segments, so patterns
> like `*` or `$HOME/...` cannot be used to smuggle file reads.

Safe bin 还强制 argv token 在执行时按**字面文本**处理(仅 stdin 段不展开 glob 和 `$VARS`),所以 `*` 或 `$HOME/...` 这种模式不能被用来夹带文件读取。

### 可信二进制目录

> Safe bins must resolve from trusted binary directories (system defaults plus
> optional `tools.exec.safeBinTrustedDirs`). `PATH` entries are never auto-trusted.
> Default trusted directories are intentionally minimal: `/bin`, `/usr/bin`. If
> your safe-bin executable lives in package-manager/user paths (for example
> `/opt/homebrew/bin`, `/usr/local/bin`, `/opt/local/bin`, `/snap/bin`), add them
> explicitly to `tools.exec.safeBinTrustedDirs`.

Safe bin 必须从可信二进制目录解析(系统默认加可选的 `tools.exec.safeBinTrustedDirs`)。`PATH` 里的条目永远不自动信任。默认可信目录刻意很小:`/bin`、`/usr/bin`。你的 safe-bin 可执行文件在包管理器 / 用户路径里(如 `/opt/homebrew/bin`、`/usr/local/bin`、`/opt/local/bin`、`/snap/bin`),把它们显式加进 `tools.exec.safeBinTrustedDirs`。

### shell 链式、包装器、多路复用器

> Shell chaining (`&&`, `||`, `;`) is allowed when every top-level segment
> satisfies the allowlist (including safe bins or skill auto-allow). Redirections
> remain unsupported in allowlist mode. Command substitution (`$()` / backticks) is
> rejected during allowlist parsing, including inside double quotes; use single
> quotes if you need literal `$()` text.

shell 链式(`&&`、`||`、`;`)只在每个顶层段都满足白名单(包括 safe bin 或技能自动允许)时才允许。重定向在白名单模式下仍不支持。命令替换(`$()` / 反引号)在白名单解析时被拒,双引号内也一样;需要字面 `$()` 文本就用单引号。

> On macOS companion-app approvals, raw shell text containing shell control or
> expansion syntax (`&&`, `||`, `;`, `|`, `` ` ``, `$`, `<`, `>`, `(`, `)`) is
> treated as an allowlist miss unless the shell binary itself is allowlisted.

macOS 伴侣 app 审批里,原始 shell 文本里含有 shell 控制或展开语法(`&&`、`||`、`;`、`|`、`` ` ``、`$`、`<`、`>`、`(`、`)`)时,除非 shell 二进制本身在白名单里,否则被视为白名单未命中。

> For shell wrappers (`bash|sh|zsh ... -c/-lc`), request-scoped env overrides are
> reduced to a small explicit allowlist (`TERM`, `LANG`, `LC_*`, `COLORTERM`,
> `NO_COLOR`, `FORCE_COLOR`).

shell 包装器(`bash|sh|zsh ... -c/-lc`)的请求作用域 env 覆盖被收窄到一个小的显式白名单(`TERM`、`LANG`、`LC_*`、`COLORTERM`、`NO_COLOR`、`FORCE_COLOR`)。

> For `allow-always` decisions in allowlist mode, known dispatch wrappers (`env`,
> `nice`, `nohup`, `stdbuf`, `timeout`) persist the inner executable path instead
> of the wrapper path. Shell multiplexers (`busybox`, `toybox`) are unwrapped for
> shell applets (`sh`, `ash`, etc.) the same way. If a wrapper or multiplexer
> cannot be safely unwrapped, no allowlist entry is persisted automatically.

白名单模式下的 `allow-always` 决定里,已知的派发包装器(`env`、`nice`、`nohup`、`stdbuf`、`timeout`)持久化时存的是内部可执行路径,不是包装器路径。shell 多路复用器(`busybox`、`toybox`)对 shell applet(`sh`、`ash` 等)也以同样的方式解包。包装器或多路复用器不能安全解包时,不会自动持久化白名单条目。

> If you allowlist interpreters like `python3` or `node`, prefer
> `tools.exec.strictInlineEval=true` so inline eval still requires an explicit
> approval. In strict mode, `allow-always` can still persist benign
> interpreter/script invocations, but inline-eval carriers are not persisted
> automatically.

如果你把 `python3` 或 `node` 这种解释器加进白名单,优先 `tools.exec.strictInlineEval=true`,让内联 eval 仍要显式审批。严格模式下,`allow-always` 仍能持久化无害的解释器 / 脚本调用,但内联 eval 载体不自动持久化。

### Safe bin vs 白名单

> | Topic            | `tools.exec.safeBins`                                  | Allowlist (`exec-approvals.json`)                                                  |

| 话题             | `tools.exec.safeBins`                                | 白名单(`exec-approvals.json`)                                                       |
| ---------------- | ---------------------------------------------------- | ----------------------------------------------------------------------------------- |
| 目标             | 自动允许窄的 stdin 过滤器                            | 显式信任特定可执行                                                                   |
| 匹配类型         | 可执行名 + safe-bin argv 策略                        | 解析出的可执行路径 glob,或对 PATH 调起的命令用裸命令名 glob                          |
| 参数范围         | 受 safe-bin profile 和字面 token 规则限制            | 默认按路径匹配;可选 `argPattern` 限制解析出的 argv                                  |
| 典型例子         | `head`、`tail`、`tr`、`wc`                           | `jq`、`python3`、`node`、`ffmpeg`、自定义 CLI                                       |
| 最佳用途         | 管线里的低风险文本变换                               | 任何行为更宽或有副作用的工具                                                         |

> Configuration location:
>
> - `safeBins` comes from config (`tools.exec.safeBins` or per-agent `agents.list[].tools.exec.safeBins`).
> - `safeBinTrustedDirs` comes from config (`tools.exec.safeBinTrustedDirs` or per-agent `agents.list[].tools.exec.safeBinTrustedDirs`).
> - `safeBinProfiles` comes from config (`tools.exec.safeBinProfiles` or per-agent `agents.list[].tools.exec.safeBinProfiles`). Per-agent profile keys override global keys.
> - allowlist entries live in host-local `~/.openclaw/exec-approvals.json` under `agents.<id>.allowlist` (or via Control UI / `openclaw approvals allowlist ...`).
> - `openclaw security audit` warns with `tools.exec.safe_bins_interpreter_unprofiled` when interpreter/runtime bins appear in `safeBins` without explicit profiles.
> - `openclaw doctor --fix` can scaffold missing custom `safeBinProfiles.<bin>` entries as `{}` (review and tighten afterward). Interpreter/runtime bins are not auto-scaffolded.

配置位置:

- `safeBins` 来自配置(`tools.exec.safeBins` 或单 agent 的 `agents.list[].tools.exec.safeBins`)。
- `safeBinTrustedDirs` 来自配置(`tools.exec.safeBinTrustedDirs` 或单 agent 的 `agents.list[].tools.exec.safeBinTrustedDirs`)。
- `safeBinProfiles` 来自配置(`tools.exec.safeBinProfiles` 或单 agent 的 `agents.list[].tools.exec.safeBinProfiles`)。单 agent 的 profile key 覆盖全局 key。
- 白名单条目放在宿主本地的 `~/.openclaw/exec-approvals.json` 里的 `agents.<id>.allowlist` 下(或通过 Control UI / `openclaw approvals allowlist ...`)。
- 解释器 / 运行时 bin 出现在 `safeBins` 里但没有显式 profile 时,`openclaw security audit` 会发 `tools.exec.safe_bins_interpreter_unprofiled` 警告。
- `openclaw doctor --fix` 能把缺的自定义 `safeBinProfiles.<bin>` 条目搭成 `{}`(之后自己复审并收紧)。解释器 / 运行时 bin 不会自动搭。

> Custom profile example:

自定义 profile 例子:

```json5
{
  tools: {
    exec: {
      safeBins: ["jq", "myfilter"],
      safeBinProfiles: {
        myfilter: {
          minPositional: 0,
          maxPositional: 0,
          allowedValueFlags: ["-n", "--limit"],
          deniedFlags: ["-f", "--file", "-c", "--command"],
        },
      },
    },
  },
}
```

> If you explicitly opt `jq` into `safeBins`, OpenClaw still rejects the `env` builtin in safe-bin
> mode so `jq -n env` cannot dump the host process environment without an explicit allowlist path
> or approval prompt.

显式把 `jq` opt-in 到 `safeBins` 时,OpenClaw 在 safe-bin 模式下仍拒绝 `env` 内建,所以 `jq -n env` 不能不经显式白名单路径或审批提示就把宿主进程环境 dump 出来。

## 解释器 / 运行时命令

> Approval-backed interpreter/runtime runs are intentionally conservative:

受审批支撑的解释器 / 运行时运行刻意保守:

> - Exact argv/cwd/env context is always bound.
> - Direct shell script and direct runtime file forms are best-effort bound to one concrete local
>   file snapshot.
> - Common package-manager wrapper forms that still resolve to one direct local file (for example
>   `pnpm exec`, `pnpm node`, `npm exec`, `npx`) are unwrapped before binding.
> - If OpenClaw cannot identify exactly one concrete local file for an interpreter/runtime command
>   (for example package scripts, eval forms, runtime-specific loader chains, or ambiguous multi-file
>   forms), approval-backed execution is denied instead of claiming semantic coverage it does not
>   have.
> - For those workflows, prefer sandboxing, a separate host boundary, or an explicit trusted
>   allowlist/full workflow where the operator accepts the broader runtime semantics.

- 精确的 argv / cwd / env 上下文总会绑定。
- 直接 shell 脚本和直接运行时文件形式,会尽力绑定到一份具体本地文件快照。
- 常见的、仍能解析到一份直接本地文件的包管理器包装形式(如 `pnpm exec`、`pnpm node`、`npm exec`、`npx`)在绑定前先解包。
- 解释器 / 运行时命令里 OpenClaw 无法识别"正好一份具体本地文件"时(如包脚本、eval 形式、运行时特定的 loader 链、模糊的多文件形式),受审批支撑的执行被拒,不会假装拥有它没有的语义覆盖。
- 那种工作流,优先用沙箱、独立宿主边界、或显式信任白名单 / 完整工作流 —— 运维自己接受更宽的运行时语义。

> When approvals are required, the exec tool returns immediately with an approval id. Use that id to
> correlate later approved-run system events (`Exec finished`, and `Exec running` when configured).
> If no decision arrives before the timeout, the request is treated as an approval timeout and
> surfaced as a terminal denial rather than an agent-waking system event.

需要审批时,exec 工具立即返回一个审批 id。用这个 id 关联之后的"已审批运行"系统事件(`Exec finished`,以及配置开了时的 `Exec running`)。超时前没决定到来,请求按审批超时处理,作为终态拒绝露出,不发唤醒 agent 的系统事件。

### 跟进投递行为

> After an approved async exec finishes, OpenClaw sends a followup `agent` turn to the same session.

一次审批通过的异步 exec 结束之后,OpenClaw 给同一会话发一次跟进 `agent` 轮次。

> - If a valid external delivery target exists (deliverable channel plus target `to`), followup delivery uses that channel.
> - In webchat-only or internal-session flows with no external target, followup delivery stays session-only (`deliver: false`).
> - If a caller explicitly requests strict external delivery with no resolvable external channel, the request fails with `INVALID_REQUEST`.
> - If `bestEffortDeliver` is enabled and no external channel can be resolved, delivery is downgraded to session-only instead of failing.

- 有有效的外部投递目标(可投递通道加目标 `to`)时,跟进投递走那个通道。
- 没外部目标的纯网页聊天或内部会话流程里,跟进投递保持仅会话(`deliver: false`)。
- 调用方显式请求严格外部投递但没有可解析的外部通道时,请求以 `INVALID_REQUEST` 失败。
- 启用了 `bestEffortDeliver` 但解析不到外部通道时,投递降级为仅会话,不失败。

## 把审批转发到聊天通道

> You can forward exec approval prompts to any chat channel (including plugin channels) and approve
> them with `/approve`. This uses the normal outbound delivery pipeline.

你可以把 exec 审批提示转发到任何聊天通道(含插件通道),并用 `/approve` 审批。这走正常的出站投递管线。

> Config:

配置:

```json5
{
  approvals: {
    exec: {
      enabled: true,
      mode: "session", // "session" | "targets" | "both"
      agentFilter: ["main"],
      sessionFilter: ["discord"], // 子串或正则
      targets: [
        { channel: "slack", to: "U12345678" },
        { channel: "telegram", to: "123456789" },
      ],
    },
  },
}
```

> Reply in chat:

聊天里回复:

```
/approve <id> allow-once
/approve <id> allow-always
/approve <id> deny
```

> The `/approve` command handles both exec approvals and plugin approvals. If the ID does not match a pending exec approval, it automatically checks plugin approvals instead.

`/approve` 命令同时处理 exec 审批和插件审批。id 没匹配上挂起的 exec 审批时,自动改查插件审批。

### 插件审批转发

> Plugin approval forwarding uses the same delivery pipeline as exec approvals but has its own
> independent config under `approvals.plugin`. Enabling or disabling one does not affect the other.

插件审批转发用跟 exec 审批一样的投递管线,但有独立的配置在 `approvals.plugin` 下。开关一个不影响另一个。

```json5
{
  approvals: {
    plugin: {
      enabled: true,
      mode: "targets",
      agentFilter: ["main"],
      targets: [
        { channel: "slack", to: "U12345678" },
        { channel: "telegram", to: "123456789" },
      ],
    },
  },
}
```

> The config shape is identical to `approvals.exec`: `enabled`, `mode`, `agentFilter`,
> `sessionFilter`, and `targets` work the same way.

配置形态跟 `approvals.exec` 一致:`enabled`、`mode`、`agentFilter`、`sessionFilter`、`targets` 用法相同。

> Channels that support shared interactive replies render the same approval buttons for both exec and
> plugin approvals. Channels without shared interactive UI fall back to plain text with `/approve`
> instructions.
> Plugin approval requests may restrict the available decisions. Approval surfaces use the request's
> declared decision set, and the Gateway rejects attempts to submit a decision that was not offered.

支持共享交互回复的通道,exec 和插件审批都渲染同样的审批按钮。没有共享交互 UI 的通道回退到带 `/approve` 指引的纯文本。
插件审批请求可能限制可用的决定。审批接口用请求声明的决定集,Gateway 拒绝提交未被提供的决定。

### 任意通道上的同聊审批

> When an exec or plugin approval request originates from a deliverable chat surface, the same chat
> can now approve it with `/approve` by default. This applies to channels such as Slack, Matrix, and
> Microsoft Teams in addition to the existing Web UI and terminal UI flows.

exec 或插件审批请求源自一个可投递的聊天接口时,同一聊天现在默认就能用 `/approve` 审批它。除了现有的 Web UI 和终端 UI 流程,这对 Slack、Matrix、Microsoft Teams 这些通道都适用。

> This shared text-command path uses the normal channel auth model for that conversation. If the
> originating chat can already send commands and receive replies, approval requests no longer need a
> separate native delivery adapter just to stay pending.

这条共享文本命令路径用那个对话的常规通道认证模型。源头聊天本来就能发命令、收回复时,审批请求不再需要独立的原生投递适配器才能保持挂起。

> Discord and Telegram also support same-chat `/approve`, but those channels still use their
> resolved approver list for authorization even when native approval delivery is disabled.

Discord 和 Telegram 也支持同聊 `/approve`,但即便原生审批投递关闭,这两个通道仍用它们解析出的批准人列表做授权。

> For Telegram and other native approval clients that call the Gateway directly,
> this fallback is intentionally bounded to "approval not found" failures. A real
> exec approval denial/error does not silently retry as a plugin approval.

对 Telegram 和其他直接调 Gateway 的原生审批客户端,这条回退刻意限定在"找不到审批"的失败上。真正的 exec 审批拒绝 / 错误**不**会悄悄重试为插件审批。

### 原生审批投递

> Some channels can also act as native approval clients. Native clients add approver DMs, origin-chat
> fanout, and channel-specific interactive approval UX on top of the shared same-chat `/approve`
> flow.

某些通道还能充当原生审批客户端。原生客户端在共享同聊 `/approve` 流程之上,加批准人 DM、源聊天扇出、按通道的交互式审批体验。

> When native approval cards/buttons are available, that native UI is the primary
> agent-facing path. The agent should not also echo a duplicate plain chat
> `/approve` command unless the tool result says chat approvals are unavailable or
> manual approval is the only remaining path.

原生审批卡片 / 按钮可用时,那套原生 UI 是 agent 面向的主路径。除非工具结果说"聊天审批不可用"或"手动审批是唯一剩下的路径",agent 不应该再回放一个重复的纯聊天 `/approve` 命令。

> If a native approval client is configured but no native runtime is active for
> the originating channel, OpenClaw keeps the local deterministic `/approve`
> prompt visible. If the native runtime is active and attempts delivery but no
> target receives the card, OpenClaw sends a same-chat fallback notice with the
> exact `/approve <id> <decision>` command so the request can still be resolved.

配置了原生审批客户端但源通道没有活跃的原生运行时时,OpenClaw 保留本地确定性的 `/approve` 提示可见。原生运行时活跃、尝试投递但没目标收到卡片时,OpenClaw 发一条同聊回退通知,带上精确的 `/approve <id> <decision>` 命令,这样请求仍能解决。

> Generic model:
>
> - host exec policy still decides whether exec approval is required
> - `approvals.exec` controls forwarding approval prompts to other chat destinations
> - `channels.<channel>.execApprovals` controls whether that channel acts as a native approval client
> - Slack plugin approvals can use Slack's native approval client when the request comes from Slack
>   and Slack plugin approvers resolve; `approvals.plugin` can also route plugin approvals to Slack
>   sessions or targets even when Slack exec approvals are disabled
> - WhatsApp emoji approval delivery is gated by `approvals.exec` and `approvals.plugin`, while
>   approval reactions require explicit WhatsApp approvers from `channels.whatsapp.allowFrom` or `"*"`

通用模型:

- 宿主 exec 策略仍决定"是否需要 exec 审批"
- `approvals.exec` 控制把审批提示转发到其他聊天目的地
- `channels.<channel>.execApprovals` 控制那个通道是否充当原生审批客户端
- 请求源自 Slack 且 Slack 插件批准人能解析时,Slack 插件审批可以用 Slack 的原生审批客户端;`approvals.plugin` 也能把插件审批路由到 Slack 会话或目标,哪怕 Slack exec 审批关掉
- WhatsApp emoji 审批投递由 `approvals.exec` 和 `approvals.plugin` 把关,审批反应需要 `channels.whatsapp.allowFrom` 或 `"*"` 里显式的 WhatsApp 批准人

> Native approval clients auto-enable DM-first delivery when all of these are true:
>
> - the channel supports native approval delivery
> - approvers can be resolved from explicit `execApprovals.approvers` or owner
>   identity such as `commands.ownerAllowFrom`
> - `channels.<channel>.execApprovals.enabled` is unset or `"auto"`

满足以下全部时,原生审批客户端自动启用 DM 优先投递:

- 通道支持原生审批投递
- 能从显式 `execApprovals.approvers` 或所有者身份(如 `commands.ownerAllowFrom`)解析出批准人
- `channels.<channel>.execApprovals.enabled` 没设或是 `"auto"`

> Set `enabled: false` to disable a native approval client explicitly. Set `enabled: true` to force
> it on when approvers resolve. Public origin-chat delivery stays explicit through
> `channels.<channel>.execApprovals.target`.

显式关掉某个原生审批客户端就设 `enabled: false`。批准人能解析时强制开启,就设 `enabled: true`。公开源聊天投递通过 `channels.<channel>.execApprovals.target` 保持显式。

> FAQ: [Why are there two exec approval configs for chat approvals?](/help/faq-first-run#why-are-there-two-exec-approval-configs-for-chat-approvals)

FAQ:[聊天审批为啥有两份 exec 审批配置?](/help/faq-first-run#why-are-there-two-exec-approval-configs-for-chat-approvals)

> - Discord: `channels.discord.execApprovals.*`
> - Slack: `channels.slack.execApprovals.*`
> - Telegram: `channels.telegram.execApprovals.*`
> - WhatsApp: use `approvals.exec` and `approvals.plugin` to route approval prompts to WhatsApp

- Discord:`channels.discord.execApprovals.*`
- Slack:`channels.slack.execApprovals.*`
- Telegram:`channels.telegram.execApprovals.*`
- WhatsApp:用 `approvals.exec` 和 `approvals.plugin` 把审批提示路由到 WhatsApp

> These native approval clients add DM routing and optional channel fanout on top of the shared
> same-chat `/approve` flow and shared approval buttons.

这些原生审批客户端在共享同聊 `/approve` 流程和共享审批按钮之上,加 DM 路由和可选的通道扇出。

> Shared behavior:
>
> - Slack, Matrix, Microsoft Teams, and similar deliverable chats use the normal channel auth model
>   for same-chat `/approve`
> - when a native approval client auto-enables, the default native delivery target is approver DMs
> - for Discord and Telegram, only resolved approvers can approve or deny
> - Discord approvers can be explicit (`execApprovals.approvers`) or inferred from `commands.ownerAllowFrom`
> - Telegram approvers can be explicit (`execApprovals.approvers`) or inferred from `commands.ownerAllowFrom`
> - Slack approvers can be explicit (`execApprovals.approvers`) or inferred from `commands.ownerAllowFrom`
> - Slack plugin approval DMs use Slack plugin approvers from `allowFrom` and account default
>   routing, not Slack exec approvers
> - Slack native buttons preserve approval id kind, so `plugin:` ids can resolve plugin approvals
>   without a second Slack-local fallback layer
> - WhatsApp emoji approvals handle both exec and plugin prompts only when the matching top-level
>   forwarding family is enabled and routes to WhatsApp; target-only WhatsApp forwarding stays on
>   the shared forwarding path unless it matches the same native origin target
> - Matrix native DM/channel routing and reaction shortcuts handle both exec and plugin approvals;
>   plugin authorization still comes from `channels.matrix.dm.allowFrom`
> - Matrix native prompts include `com.openclaw.approval` custom event content on the first prompt
>   event so OpenClaw-aware Matrix clients can read structured approval state while stock clients
>   keep the plain-text `/approve` fallback
> - the requester does not need to be an approver
> - the originating chat can approve directly with `/approve` when that chat already supports commands and replies
> - native Discord approval buttons route by approval id kind: `plugin:` ids go
>   straight to plugin approvals, everything else goes to exec approvals
> - native Telegram approval buttons follow the same bounded exec-to-plugin fallback as `/approve`
> - when native `target` enables origin-chat delivery, approval prompts include the command text
> - pending exec approvals expire after 30 minutes by default
> - if no operator UI or configured approval client can accept the request, the prompt falls back to `askFallback`

共享行为:

- Slack、Matrix、Microsoft Teams 这种可投递聊天,同聊 `/approve` 用常规通道认证模型
- 原生审批客户端自动启用时,默认原生投递目标是批准人 DM
- Discord 和 Telegram 上,只有解析出的批准人能审批或拒绝
- Discord 批准人可以是显式的(`execApprovals.approvers`),或从 `commands.ownerAllowFrom` 推断
- Telegram 批准人可以是显式的(`execApprovals.approvers`),或从 `commands.ownerAllowFrom` 推断
- Slack 批准人可以是显式的(`execApprovals.approvers`),或从 `commands.ownerAllowFrom` 推断
- Slack 插件审批 DM 用 `allowFrom` 里的 Slack 插件批准人和账户默认路由,不用 Slack exec 批准人
- Slack 原生按钮保留审批 id 类型,所以 `plugin:` id 能直接解析到插件审批,不需要 Slack 本地的第二层回退
- WhatsApp emoji 审批同时处理 exec 和插件提示,但只在匹配的顶层转发族开了且路由到 WhatsApp 时才行;仅 target 的 WhatsApp 转发留在共享转发路径上,除非它跟同一个原生源目标匹配
- Matrix 原生 DM / 通道路由和反应快捷键同时处理 exec 和插件审批;插件授权仍来自 `channels.matrix.dm.allowFrom`
- Matrix 原生提示在第一次提示事件里包含 `com.openclaw.approval` 自定义事件内容,这样 OpenClaw 感知的 Matrix 客户端能读结构化审批状态,普通客户端仍保留纯文本 `/approve` 回退
- 请求者不需要是批准人
- 源聊天本来就支持命令和回复时,可以直接用 `/approve` 审批
- Discord 原生审批按钮按审批 id 类型路由:`plugin:` id 直接走插件审批,其余走 exec 审批
- Telegram 原生审批按钮遵守跟 `/approve` 一样的受限 exec-到-插件回退
- 原生 `target` 启用源聊天投递时,审批提示带命令文本
- 挂起的 exec 审批默认 30 分钟过期
- 没有运维 UI 或配置好的审批客户端能接受请求时,提示回退到 `askFallback`

> Sensitive owner-only group commands such as `/diagnostics` and `/export-trajectory` use private
> owner routing for approval prompts and final results. OpenClaw first tries a private route on the
> same surface where the owner ran the command. If that surface has no private owner route, it falls
> back to the first available owner route from `commands.ownerAllowFrom`, so a Discord group command
> can still send the approval and result to the owner's Telegram DM when Telegram is the configured
> primary private interface. The group chat only gets a short acknowledgement.

敏感的仅所有者群命令(如 `/diagnostics` 和 `/export-trajectory`)对审批提示和最终结果用私密所有者路由。OpenClaw 先在所有者跑命令的同一接口上试私密路径。该接口没有私密所有者路径时,回退到 `commands.ownerAllowFrom` 里第一个可用的所有者路径 —— 这样 Telegram 是配置好的主私密接口时,一条 Discord 群命令仍能把审批和结果发到所有者的 Telegram DM。群聊只收到一条短的确认。

> Telegram defaults to approver DMs (`target: "dm"`). You can switch to `channel` or `both` when you
> want approval prompts to appear in the originating Telegram chat/topic as well. For Telegram forum
> topics, OpenClaw preserves the topic for the approval prompt and the post-approval follow-up.

Telegram 默认走批准人 DM(`target: "dm"`)。你想审批提示也出现在源 Telegram 聊天 / 话题里时,改成 `channel` 或 `both`。对 Telegram 论坛话题,OpenClaw 给审批提示和审批后跟进都保留话题。

> See:
>
> - [Discord](/channels/discord)
> - [Telegram](/channels/telegram)

见:

- [Discord](/channels/discord)
- [Telegram](/channels/telegram)

### macOS IPC 流

```
Gateway -> Node Service (WS)
                 |  IPC (UDS + token + HMAC + TTL)
                 v
             Mac App (UI + approvals + system.run)
```

> Security notes:
>
> - Unix socket mode `0600`, token stored in `exec-approvals.json`.
> - Same-UID peer check.
> - Challenge/response (nonce + HMAC token + request hash) + short TTL.

安全说明:

- Unix socket 模式 `0600`,token 存在 `exec-approvals.json` 里。
- 同 UID 对端检查。
- 挑战 / 应答(nonce + HMAC token + 请求 hash)+ 短 TTL。

## FAQ

### 审批目标上的 `accountId` 和 `threadId` 什么时候用?

> Use `accountId` when the channel has multiple configured identities and the approval prompt must
> leave through one specific account. Use `threadId` when the destination supports topics or
> threads and the prompt should stay inside that thread instead of the top-level chat.

通道配了多重身份、审批提示必须从某个特定账户发出时,用 `accountId`。目标支持话题或线程、提示应该留在那个线程里(而不是顶层聊天)时,用 `threadId`。

> A concrete Telegram case is an operations supergroup with forum topics and two Telegram bot
> accounts. The `to` value names the supergroup, `accountId` selects the bot account, and `threadId`
> selects the forum topic:

一个具体的 Telegram 案例:一个带论坛话题的运维超群,加两个 Telegram bot 账户。`to` 给超群命名,`accountId` 选 bot 账户,`threadId` 选论坛话题:

```json5
{
  approvals: {
    exec: {
      enabled: true,
      mode: "targets",
      targets: [
        {
          channel: "telegram",
          to: "-1001234567890",
          accountId: "ops-bot",
          threadId: "77",
        },
      ],
    },
  },
  channels: {
    telegram: {
      accounts: {
        default: {
          name: "Primary bot",
          botToken: "env:TELEGRAM_PRIMARY_BOT_TOKEN",
        },
        "ops-bot": {
          name: "Operations bot",
          botToken: "env:TELEGRAM_OPS_BOT_TOKEN",
        },
      },
    },
  },
}
```

> With that setup, forwarded exec approvals are posted by the `ops-bot` Telegram account into topic
> `77` of chat `-1001234567890`. A target without `accountId` uses the channel's default account, and
> a target without `threadId` posts to the top-level destination.

这套配置下,转发的 exec 审批由 `ops-bot` Telegram 账户发到聊天 `-1001234567890` 的 `77` 话题里。没 `accountId` 的 target 用通道默认账户,没 `threadId` 的 target 发到顶层目的地。

### 审批发到一个会话时,会话里所有人都能批准吗?

> No. Session delivery only controls where the prompt appears. It does not by itself authorize every
> participant in that chat to approve.

不能。会话投递只控制提示出现在哪里。它本身不授权那个聊天里所有参与者审批。

> For generic same-chat `/approve`, the sender must already be authorized for commands in that
> channel session. If the channel exposes explicit approval approvers, those approvers can authorize
> the `/approve` action even when they are not otherwise command-authorized in that session.

对通用的同聊 `/approve`,发送者必须已经在那个通道会话里有命令授权。通道暴露了显式审批批准人时,这些批准人能给 `/approve` 动作授权 —— 哪怕他们在那个会话里没有别的命令授权。

> Some channels are stricter. Discord, Telegram, Matrix, Slack native approval DMs, and similar
> native approval clients use their resolved approver lists for approval authorization. For example,
> a Telegram forum-topic approval prompt can be visible to everyone in the topic, but only numeric
> Telegram user IDs resolved from `channels.telegram.execApprovals.approvers` or
> `commands.ownerAllowFrom` can approve or deny it.

某些通道更严。Discord、Telegram、Matrix、Slack 原生审批 DM 这种原生审批客户端,用它们解析出的批准人列表做审批授权。比如,Telegram 论坛话题的审批提示对话题里所有人都可见,但只有从 `channels.telegram.execApprovals.approvers` 或 `commands.ownerAllowFrom` 解析出的数字 Telegram 用户 ID 才能批准或拒绝。

## 相关

> - [Exec approvals](/tools/exec-approvals) — core policy and approval flow
> - [Exec tool](/tools/exec)
> - [Elevated mode](/tools/elevated)
> - [Skills](/tools/skills) — skill-backed auto-allow behavior

- [Exec approvals](/tools/exec-approvals) —— 核心策略和审批流程
- [Exec tool](/tools/exec)
- [提权模式](/tools/elevated)
- [技能](/tools/skills) —— 技能撑着的自动允许行为
