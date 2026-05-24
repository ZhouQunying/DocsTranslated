# Exec tool

> Run shell commands in the workspace. `exec` is a mutating shell surface: commands can create, edit, or delete files wherever the selected host or sandbox filesystem permits. Disabling OpenClaw filesystem tools such as `write`, `edit`, or `apply_patch` does not make `exec` read-only.

在工作区里跑 shell 命令。`exec` 是一个会改文件的 shell 接口:在所选宿主或沙箱文件系统允许的范围内,命令可以创建、编辑、删除文件。关掉 OpenClaw 的文件系统工具(如 `write`、`edit`、`apply_patch`)**不会**让 `exec` 变成只读。

> Supports foreground + background execution via `process`. If `process` is disallowed, `exec` runs synchronously and ignores `yieldMs`/`background`.
> Background sessions are scoped per agent; `process` only sees sessions from the same agent.

通过 `process` 支持前台 + 后台执行。`process` 被禁用时,`exec` 同步跑,忽略 `yieldMs`/`background`。后台会话按 agent 隔离;`process` 只看得见同一个 agent 的会话。

## 参数

> `command` (string, required) — Shell command to run.

`command`(string,必填)—— 要跑的 shell 命令。

> `workdir` (string, default: cwd) — Working directory for the command.

`workdir`(string,默认 cwd)—— 命令的工作目录。

> `env` (object) — Key/value environment overrides merged on top of the inherited environment.

`env`(object)—— 键值对形式的环境变量覆盖,合并到继承的环境之上。

> `yieldMs` (number, default: 10000) — Auto-background the command after this delay (ms).

`yieldMs`(number,默认 10000)—— 命令延迟这么多毫秒后自动转后台。

> `background` (boolean, default: false) — Background the command immediately instead of waiting for `yieldMs`.

`background`(boolean,默认 false)—— 立即把命令转后台,不等 `yieldMs`。

> `timeout` (number, default: `tools.exec.timeoutSec`) — Override the configured exec timeout for this call. Set `timeout: 0` only when the command should run without the exec process timeout.

`timeout`(number,默认 `tools.exec.timeoutSec`)—— 覆盖本次调用的 exec 超时。只有想让命令不带 exec 进程超时跑时才设 `timeout: 0`。

> `pty` (boolean, default: false) — Run in a pseudo-terminal when available. Use for TTY-only CLIs, coding agents, and terminal UIs.

`pty`(boolean,默认 false)—— 可用时在伪终端里跑。给只能在 TTY 下跑的 CLI、编码 agent、终端 UI 用。

> `host` ('auto' | 'sandbox' | 'gateway' | 'node', default: auto) — Where to execute. `auto` resolves to `sandbox` when a sandbox runtime is active and `gateway` otherwise.

`host`('auto' | 'sandbox' | 'gateway' | 'node',默认 auto)—— 在哪里执行。`auto` 在沙箱运行时激活时解析到 `sandbox`,否则解析到 `gateway`。

> `security` ('deny' | 'allowlist' | 'full') — Ignored for normal tool calls. `gateway` / `node` security is controlled by `tools.exec.security` and `~/.openclaw/exec-approvals.json`; elevated mode can force `security=full` only when the operator explicitly grants elevated access.

`security`('deny' | 'allowlist' | 'full')—— 普通工具调用里忽略。`gateway` / `node` 安全由 `tools.exec.security` 和 `~/.openclaw/exec-approvals.json` 控制;只有运维显式授予提权访问时,提权模式才能强制 `security=full`。

> `ask` ('off' | 'on-miss' | 'always') — Approval prompt behavior for `gateway` / `node` execution.

`ask`('off' | 'on-miss' | 'always')—— `gateway` / `node` 执行的审批提示行为。

> `node` (string) — Node id/name when `host=node`.

`node`(string)——`host=node` 时的节点 id / 名字。

> `elevated` (boolean, default: false) — Request elevated mode — escape the sandbox onto the configured host path. `security=full` is forced only when elevated resolves to `full`.

`elevated`(boolean,默认 false)—— 请求提权模式 —— 突破沙箱走配置好的宿主路径。只有提权解析到 `full` 时才会强制 `security=full`。

> Notes:

说明:

> - `host` defaults to `auto`: sandbox when sandbox runtime is active for the session, otherwise gateway.
> - `host` only accepts `auto`, `sandbox`, `gateway`, or `node`. It is not a hostname selector; hostname-like values are rejected before the command runs.
> - `auto` is the default routing strategy, not a wildcard. Per-call `host=node` is allowed from `auto`; per-call `host=gateway` is only allowed when no sandbox runtime is active.
> - With no extra config, `host=auto` still "just works": no sandbox means it resolves to `gateway`; a live sandbox means it stays in the sandbox.
> - `elevated` escapes the sandbox onto the configured host path: `gateway` by default, or `node` when `tools.exec.host=node` (or the session default is `host=node`). It is only available when elevated access is enabled for the current session/provider.
> - `gateway`/`node` approvals are controlled by `~/.openclaw/exec-approvals.json`.
> - `node` requires a paired node (companion app or headless node host).
> - If multiple nodes are available, set `exec.node` or `tools.exec.node` to select one.
> - `exec host=node` is the only shell-execution path for nodes; the legacy `nodes.run` wrapper has been removed.
> - `timeout` applies to foreground, background, `yieldMs`, gateway, sandbox, and node `system.run` execution. If omitted, OpenClaw uses `tools.exec.timeoutSec`; explicit `timeout: 0` disables the exec process timeout for that call.

- `host` 默认 `auto`:会话有沙箱运行时就用沙箱,否则用 gateway。
- `host` 只接受 `auto`、`sandbox`、`gateway`、`node`。它不是主机名选择器;像主机名的值在命令运行前就会被拒。
- `auto` 是默认路由策略,不是通配符。从 `auto` 起,允许单次调用用 `host=node`;单次 `host=gateway` 只在没有沙箱运行时才允许。
- 不加额外配置,`host=auto` 也"开箱即用":没沙箱就解析到 `gateway`;有活的沙箱就留在沙箱里。
- `elevated` 突破沙箱走配置好的宿主路径:默认 `gateway`,`tools.exec.host=node`(或会话默认是 `host=node`)时走 `node`。只有当前会话 / provider 开了提权访问才可用。
- `gateway`/`node` 审批由 `~/.openclaw/exec-approvals.json` 控制。
- `node` 要求一个配对节点(伴侣 app 或无头节点宿主)。
- 多个节点可用时,设 `exec.node` 或 `tools.exec.node` 选一个。
- `exec host=node` 是节点上唯一的 shell 执行路径;旧的 `nodes.run` 包装已经移除。
- `timeout` 在前台、后台、`yieldMs`、gateway、sandbox、节点 `system.run` 执行上都生效。不设时 OpenClaw 用 `tools.exec.timeoutSec`;显式 `timeout: 0` 关掉这次调用的 exec 进程超时。

> - On non-Windows hosts, exec uses `SHELL` when set; if `SHELL` is `fish`, it prefers `bash` (or `sh`)
>   from `PATH` to avoid fish-incompatible scripts, then falls back to `SHELL` if neither exists.
> - On Windows hosts, exec prefers PowerShell 7 (`pwsh`) discovery (Program Files, ProgramW6432, then PATH),
>   then falls back to Windows PowerShell 5.1.
> - Host execution (`gateway`/`node`) rejects `env.PATH` and loader overrides (`LD_*`/`DYLD_*`) to
>   prevent binary hijacking or injected code.
> - OpenClaw sets `OPENCLAW_SHELL=exec` in the spawned command environment (including PTY and sandbox execution) so shell/profile rules can detect exec-tool context.
> - `openclaw channels login` is blocked from `exec` because it is an interactive channel-auth flow; run it in a terminal on the gateway host, or use the channel-native login tool from chat when one exists.
> - Important: sandboxing is **off by default**. If sandboxing is off, implicit `host=auto`
>   resolves to `gateway`. Explicit `host=sandbox` still fails closed instead of silently
>   running on the gateway host. Enable sandboxing or use `host=gateway` with approvals.
> - Script preflight checks (for common Python/Node shell-syntax mistakes) only inspect files inside the
>   effective `workdir` boundary. If a script path resolves outside `workdir`, preflight is skipped for
>   that file.
> - For long-running work that starts now, start it once and rely on automatic
>   completion wake when it is enabled and the command emits output or fails.
>   Use `process` for logs, status, input, or intervention; do not emulate
>   scheduling with sleep loops, timeout loops, or repeated polling.
> - For work that should happen later or on a schedule, use cron instead of
>   `exec` sleep/delay patterns.

- 非 Windows 宿主上,exec 在 `SHELL` 设了时就用它;如果 `SHELL` 是 `fish`,优先用 `PATH` 里的 `bash`(或 `sh`)避免 fish 不兼容的脚本,两个都没有再回退到 `SHELL`。
- Windows 宿主上,exec 优先发现 PowerShell 7(`pwsh`)(Program Files、ProgramW6432、PATH 顺序),没有再回退到 Windows PowerShell 5.1。
- 宿主执行(`gateway`/`node`)拒绝 `env.PATH` 和 loader 覆盖(`LD_*`/`DYLD_*`),防止二进制劫持或代码注入。
- OpenClaw 在派生的命令环境里设 `OPENCLAW_SHELL=exec`(PTY 和沙箱执行也设),这样 shell / profile 规则能识别"现在是 exec 工具上下文"。
- `openclaw channels login` 不让走 `exec`,因为它是交互式通道认证流;在 gateway 宿主的终端里跑,或者从聊天里用通道原生的登录工具(如果有的话)。
- 重要:沙箱**默认关**。沙箱关时,隐式 `host=auto` 解析到 `gateway`。显式 `host=sandbox` 仍然失败拒绝,不会默默跑到 gateway 宿主上。要么打开沙箱,要么用 `host=gateway` 加审批。
- 脚本预检(查常见的 Python/Node shell 语法错误)只看 `workdir` 边界内的文件。脚本路径解析到 `workdir` 外面,这个文件就跳过预检。
- 现在就开始的长运行任务,启动一次,依赖自动完成唤醒(它开着、命令有输出或失败时会唤)。用 `process` 看日志、状态、输入或干预;不要用 sleep 循环、超时循环、反复轮询模拟调度。
- 应该晚点跑或按时间表跑的任务,用 cron,不要用 `exec` 的 sleep / delay 模式。

## 配置

> - `tools.exec.notifyOnExit` (default: true): when true, backgrounded exec sessions enqueue a system event and request a heartbeat on exit.
> - `tools.exec.approvalRunningNoticeMs` (default: 10000): emit a single "running" notice when an approval-gated exec runs longer than this (0 disables).
> - `tools.exec.timeoutSec` (default: 1800): default per-command exec timeout in seconds. Per-call `timeout` overrides it; per-call `timeout: 0` disables the exec process timeout.
> - `tools.exec.host` (default: `auto`; resolves to `sandbox` when sandbox runtime is active, `gateway` otherwise)
> - `tools.exec.security` (default: `deny` for sandbox, `full` for gateway + node when unset)
> - `tools.exec.ask` (default: `off`)
> - No-approval host exec is the default for gateway + node. If you want approvals/allowlist behavior, tighten both `tools.exec.*` and the host `~/.openclaw/exec-approvals.json`; see [Exec approvals](/tools/exec-approvals#yolo-mode-no-approval).
> - YOLO comes from the host-policy defaults (`security=full`, `ask=off`), not from `host=auto`. If you want to force gateway or node routing, set `tools.exec.host` or use `/exec host=...`.
> - In `security=full` plus `ask=off` mode, host exec follows the configured policy directly; there is no extra heuristic command-obfuscation prefilter or script-preflight rejection layer.
> - `tools.exec.node` (default: unset)
> - `tools.exec.strictInlineEval` (default: false): when true, inline interpreter eval forms such as `python -c`, `node -e`, `ruby -e`, `perl -e`, `php -r`, `lua -e`, and `osascript -e` always require explicit approval. `allow-always` can still persist benign interpreter/script invocations, but inline-eval forms still prompt each time.
> - `tools.exec.commandHighlighting` (default: false): when true, approval prompts can highlight parser-derived command spans in the command text. Set to `true` globally or per agent to enable command text highlighting without changing exec approval policy.
> - `tools.exec.pathPrepend`: list of directories to prepend to `PATH` for exec runs (gateway + sandbox only).
> - `tools.exec.safeBins`: stdin-only safe binaries that can run without explicit allowlist entries. For behavior details, see [Safe bins](/tools/exec-approvals-advanced#safe-bins-stdin-only).
> - `tools.exec.safeBinTrustedDirs`: additional explicit directories trusted for `safeBins` path checks. `PATH` entries are never auto-trusted. Built-in defaults are `/bin` and `/usr/bin`.
> - `tools.exec.safeBinProfiles`: optional custom argv policy per safe bin (`minPositional`, `maxPositional`, `allowedValueFlags`, `deniedFlags`).

- `tools.exec.notifyOnExit`(默认 true):为 true 时,后台化的 exec 会话在退出时入队一个系统事件并请求心跳。
- `tools.exec.approvalRunningNoticeMs`(默认 10000):一个走审批的 exec 跑得比这个长时,发一次"正在运行"通知(0 关掉)。
- `tools.exec.timeoutSec`(默认 1800):默认的单命令 exec 超时(秒)。单次调用的 `timeout` 覆盖它;单次 `timeout: 0` 关掉 exec 进程超时。
- `tools.exec.host`(默认 `auto`;沙箱运行时激活时解析到 `sandbox`,否则到 `gateway`)
- `tools.exec.security`(沙箱默认 `deny`,gateway + node 没设时默认 `full`)
- `tools.exec.ask`(默认 `off`)
- gateway + node 上"无审批的宿主 exec"是默认。要审批 / 白名单行为,同时收紧 `tools.exec.*` 和宿主上的 `~/.openclaw/exec-approvals.json`;见 [Exec approvals](/tools/exec-approvals#yolo-mode-no-approval)。
- YOLO 来自宿主策略默认(`security=full`、`ask=off`),不是来自 `host=auto`。想强制走 gateway 或 node,设 `tools.exec.host` 或用 `/exec host=...`。
- `security=full` 加 `ask=off` 模式下,宿主 exec 直接按配置策略走;没有额外的启发式命令混淆预过滤器、也没有脚本预检拒绝层。
- `tools.exec.node`(默认不设)
- `tools.exec.strictInlineEval`(默认 false):为 true 时,内联解释器 eval 形式(如 `python -c`、`node -e`、`ruby -e`、`perl -e`、`php -r`、`lua -e`、`osascript -e`)总是要显式审批。`allow-always` 仍能持久化无害的解释器 / 脚本调用,但内联 eval 形式每次仍提示。
- `tools.exec.commandHighlighting`(默认 false):为 true 时,审批提示能在命令文本里高亮解析器推导出的命令片段。全局或按 agent 设 `true` 可启用命令文本高亮,不改 exec 审批策略。
- `tools.exec.pathPrepend`:exec 运行时(仅 gateway + 沙箱)预置到 `PATH` 前面的目录列表。
- `tools.exec.safeBins`:仅 stdin 的安全二进制,无需显式白名单也能跑。行为细节见 [Safe bins](/tools/exec-approvals-advanced#safe-bins-stdin-only)。
- `tools.exec.safeBinTrustedDirs`:`safeBins` 路径检查额外信任的显式目录。`PATH` 里的条目永远不自动信任。内置默认是 `/bin` 和 `/usr/bin`。
- `tools.exec.safeBinProfiles`:每个 safe bin 的可选自定义 argv 策略(`minPositional`、`maxPositional`、`allowedValueFlags`、`deniedFlags`)。

> Example:

例子:

```json5
{
  tools: {
    exec: {
      pathPrepend: ["~/bin", "/opt/oss/bin"],
    },
  },
}
```

### PATH 处理

> - `host=gateway`: merges your login-shell `PATH` into the exec environment. `env.PATH` overrides are
>   rejected for host execution. The daemon itself still runs with a minimal `PATH`:
>   - macOS: `/opt/homebrew/bin`, `/usr/local/bin`, `/usr/bin`, `/bin`
>   - Linux: `/usr/local/bin`, `/usr/bin`, `/bin`
>     - To prevent user shell configuration (like `~/.zshenv` or `/etc/zshenv`) from overriding priority paths during startup, `tools.exec.pathPrepend` entries are securely prepended to the final `PATH` inside the shell command right before execution.
> - `host=sandbox`: runs `sh -lc` (login shell) inside the container, so `/etc/profile` may reset `PATH`.
>   OpenClaw prepends `env.PATH` after profile sourcing via an internal env var (no shell interpolation);
>   `tools.exec.pathPrepend` applies here too.
> - `host=node`: only non-blocked env overrides you pass are sent to the node. `env.PATH` overrides are
>   rejected for host execution and ignored by node hosts. If you need additional PATH entries on a node,
>   configure the node host service environment (systemd/launchd) or install tools in standard locations.

- `host=gateway`:把你登录 shell 的 `PATH` 合进 exec 环境。宿主执行拒绝 `env.PATH` 覆盖。守护进程本身仍跑在最小 `PATH` 下:
  - macOS:`/opt/homebrew/bin`、`/usr/local/bin`、`/usr/bin`、`/bin`
  - Linux:`/usr/local/bin`、`/usr/bin`、`/bin`
    - 为了防止用户 shell 配置(如 `~/.zshenv` 或 `/etc/zshenv`)在启动时覆盖优先级路径,`tools.exec.pathPrepend` 的条目会在执行前安全地预置到 shell 命令里最终 `PATH` 的前面。
- `host=sandbox`:在容器里跑 `sh -lc`(登录 shell),所以 `/etc/profile` 可能重置 `PATH`。OpenClaw 在 profile 加载之后,通过内部环境变量预置 `env.PATH`(不做 shell 插值);`tools.exec.pathPrepend` 这里也生效。
- `host=node`:只把你传的、没被禁的环境覆盖发到节点。宿主执行拒绝 `env.PATH` 覆盖,节点宿主也忽略它。要在节点上加 PATH 条目,配置节点宿主服务的环境(systemd/launchd),或者把工具装到标准位置。

> Per-agent node binding (use the agent list index in config):

按 agent 绑定节点(用配置里的 agent list 索引):

```bash
openclaw config get agents.list
openclaw config set 'agents.list[0].tools.exec.node' "node-id-or-name"
```

> Control UI: the Nodes tab includes a small "Exec node binding" panel for the same settings.

Control UI:Nodes 标签页里有一个小的 "Exec node binding" 面板,做同样的设置。

## 会话覆盖(`/exec`)

> Use `/exec` to set **per-session** defaults for `host`, `security`, `ask`, and `node`.
> Send `/exec` with no arguments to show the current values.

用 `/exec` 设**按会话**的 `host`、`security`、`ask`、`node` 默认。不带参数发 `/exec` 显示当前值。

> Example:

例子:

```
/exec host=auto security=allowlist ask=on-miss node=mac-1
```

## 授权模型

> `/exec` is only honored for **authorized senders** (channel allowlists/pairing plus `commands.useAccessGroups`).
> It updates **session state only** and does not write config. To hard-disable exec, deny it via tool
> policy (`tools.deny: ["exec"]` or per-agent). Host approvals still apply unless you explicitly set
> `security=full` and `ask=off`.

`/exec` 只对**授权发送者**生效(通道白名单 / 配对加上 `commands.useAccessGroups`)。它只更新**会话状态**,不写配置。要硬关掉 exec,用工具策略拒绝它(`tools.deny: ["exec"]` 或单 agent 设)。除非你显式设 `security=full` 加 `ask=off`,否则宿主审批仍生效。

## Exec 审批(伴侣 app / 节点宿主)

> Sandboxed agents can require per-request approval before `exec` runs on the gateway or node host.
> See [Exec approvals](/tools/exec-approvals) for the policy, allowlist, and UI flow.

沙箱化的 agent 可以要求"在 gateway 或节点宿主上跑 `exec` 之前按请求审批"。策略、白名单、UI 流程见 [Exec approvals](/tools/exec-approvals)。

> When approvals are required, the exec tool returns immediately with
> `status: "approval-pending"` and an approval id. Once approved (or denied / timed out),
> the Gateway emits command progress and completion system events only for approved runs
> (`Exec running` / `Exec finished`). Denied or timed-out approvals are terminal and do not
> wake the agent session with a denial system event.
> On channels with native approval cards/buttons, the agent should rely on that
> native UI first and only include a manual `/approve` command when the tool
> result explicitly says chat approvals are unavailable or manual approval is the
> only path.

要审批时,exec 工具立即返回 `status: "approval-pending"` 和一个审批 id。审批通过(或拒绝 / 超时)后,Gateway 只为通过的运行发出命令进度和完成系统事件(`Exec running` / `Exec finished`)。被拒或超时的审批是终态,不会用拒绝系统事件唤醒 agent 会话。在有原生审批卡片 / 按钮的通道上,agent 应该优先依赖那套原生 UI;只有当工具结果明确说"聊天审批不可用"或"手动审批是唯一路径"时,才带上手动 `/approve` 命令。

## 白名单 + safe bins

> Manual allowlist enforcement matches resolved binary path globs and bare command-name
> globs. Bare names match only commands invoked through PATH, so `rg` can match
> `/opt/homebrew/bin/rg` when the command is `rg`, but not `./rg` or `/tmp/rg`.
> When `security=allowlist`, shell commands are auto-allowed only if every pipeline
> segment is allowlisted or a safe bin. Chaining (`;`, `&&`, `||`) and redirections
> are rejected in allowlist mode unless every top-level segment satisfies the
> allowlist (including safe bins). Redirections remain unsupported.
> Durable `allow-always` trust does not bypass that rule: a chained command still requires every
> top-level segment to match.

手动白名单匹配解析出的二进制路径 glob 和裸命令名 glob。裸名只匹配通过 PATH 调起的命令,所以 `rg` 在命令是 `rg` 时能匹配 `/opt/homebrew/bin/rg`,但不能匹配 `./rg` 或 `/tmp/rg`。`security=allowlist` 时,只有 pipeline 里每段都被白名单或 safe bin 覆盖,shell 命令才自动允许。白名单模式下,链式调用(`;`、`&&`、`||`)和重定向被拒绝,除非每个顶层段都满足白名单(含 safe bin)。重定向仍不支持。持久化的 `allow-always` 信任也不绕过这条规则:链式命令仍要每个顶层段都匹配。

> `autoAllowSkills` is a separate convenience path in exec approvals. It is not the same as
> manual path allowlist entries. For strict explicit trust, keep `autoAllowSkills` disabled.

`autoAllowSkills` 是 exec 审批里独立的便利路径,跟手动路径白名单条目不是一回事。要严格的显式信任,把 `autoAllowSkills` 关掉。

> Use the two controls for different jobs:
>
> - `tools.exec.safeBins`: small, stdin-only stream filters.
> - `tools.exec.safeBinTrustedDirs`: explicit extra trusted directories for safe-bin executable paths.
> - `tools.exec.safeBinProfiles`: explicit argv policy for custom safe bins.
> - allowlist: explicit trust for executable paths.

两个控制器分工不同:

- `tools.exec.safeBins`:小的、仅 stdin 的流过滤器。
- `tools.exec.safeBinTrustedDirs`:safe bin 可执行路径的显式额外信任目录。
- `tools.exec.safeBinProfiles`:自定义 safe bin 的显式 argv 策略。
- 白名单:对可执行路径的显式信任。

> Do not treat `safeBins` as a generic allowlist, and do not add interpreter/runtime binaries (for example `python3`, `node`, `ruby`, `bash`). If you need those, use explicit allowlist entries and keep approval prompts enabled.
> `openclaw security audit` warns when interpreter/runtime `safeBins` entries are missing explicit profiles, and `openclaw doctor --fix` can scaffold missing custom `safeBinProfiles` entries.
> `openclaw security audit` and `openclaw doctor` also warn when you explicitly add broad-behavior bins such as `jq` back into `safeBins`.
> If you explicitly allowlist interpreters, enable `tools.exec.strictInlineEval` so inline code-eval forms still require a fresh approval.

不要把 `safeBins` 当通用白名单,也不要往里加解释器 / 运行时二进制(如 `python3`、`node`、`ruby`、`bash`)。这些用显式白名单条目,并保留审批提示。
`openclaw security audit` 在解释器 / 运行时 `safeBins` 条目缺显式 profile 时会警告;`openclaw doctor --fix` 能把缺的自定义 `safeBinProfiles` 条目搭起来。
显式把 `jq` 这种宽行为 bin 加回 `safeBins` 时,`openclaw security audit` 和 `openclaw doctor` 也会警告。
如果你显式把解释器放进白名单,启用 `tools.exec.strictInlineEval`,让内联代码 eval 形式仍需要新的审批。

> For full policy details and examples, see [Exec approvals](/tools/exec-approvals-advanced#safe-bins-stdin-only) and [Safe bins versus allowlist](/tools/exec-approvals-advanced#safe-bins-versus-allowlist).

完整策略细节和例子见 [Exec approvals](/tools/exec-approvals-advanced#safe-bins-stdin-only) 和 [Safe bins versus allowlist](/tools/exec-approvals-advanced#safe-bins-versus-allowlist)。

## 例子

> Foreground:

前台:

```json
{ "tool": "exec", "command": "ls -la" }
```

> Background + poll:

后台 + 轮询:

```json
{"tool":"exec","command":"npm run build","yieldMs":1000}
{"tool":"process","action":"poll","sessionId":"<id>"}
```

> Polling is for on-demand status, not waiting loops. If automatic completion wake
> is enabled, the command can wake the session when it emits output or fails.

轮询是用来按需查状态,不是等待循环。自动完成唤醒开着时,命令有输出或失败时能唤醒会话。

> Send keys (tmux-style):

发按键(tmux 风格):

```json
{"tool":"process","action":"send-keys","sessionId":"<id>","keys":["Enter"]}
{"tool":"process","action":"send-keys","sessionId":"<id>","keys":["C-c"]}
{"tool":"process","action":"send-keys","sessionId":"<id>","keys":["Up","Up","Enter"]}
```

> Submit (send CR only):

提交(只发回车):

```json
{ "tool": "process", "action": "submit", "sessionId": "<id>" }
```

> Paste (bracketed by default):

粘贴(默认带 bracketed paste):

```json
{ "tool": "process", "action": "paste", "sessionId": "<id>", "text": "line1\nline2\n" }
```

## apply_patch

> `apply_patch` is a subtool of `exec` for structured multi-file edits.
> It is enabled by default for OpenAI and OpenAI Codex models. Use config only
> when you want to disable it or restrict it to specific models:

`apply_patch` 是 `exec` 下面的一个子工具,用于结构化的多文件编辑。它对 OpenAI 和 OpenAI Codex 模型默认开启。只有想关掉或限制到特定模型时才用配置:

```json5
{
  tools: {
    exec: {
      applyPatch: { workspaceOnly: true, allowModels: ["gpt-5.5"] },
    },
  },
}
```

> Notes:
>
> - Only available for OpenAI/OpenAI Codex models.
> - Tool policy still applies; `allow: ["write"]` implicitly allows `apply_patch`.
> - `deny: ["write"]` does not deny `apply_patch`; deny `apply_patch` explicitly or use `deny: ["group:fs"]` when patch writes should also be blocked.
> - Config lives under `tools.exec.applyPatch`.
> - `tools.exec.applyPatch.enabled` defaults to `true`; set it to `false` to disable the tool for OpenAI models.
> - `tools.exec.applyPatch.workspaceOnly` defaults to `true` (workspace-contained). Set it to `false` only if you intentionally want `apply_patch` to write/delete outside the workspace directory.

说明:

- 只对 OpenAI / OpenAI Codex 模型可用。
- 工具策略仍然生效;`allow: ["write"]` 隐式允许 `apply_patch`。
- `deny: ["write"]` 不拒绝 `apply_patch`;要把 patch 写也拦下,显式拒绝 `apply_patch` 或用 `deny: ["group:fs"]`。
- 配置在 `tools.exec.applyPatch` 下。
- `tools.exec.applyPatch.enabled` 默认 `true`;设成 `false` 给 OpenAI 模型关掉这个工具。
- `tools.exec.applyPatch.workspaceOnly` 默认 `true`(限定在工作区内)。只有你确实想让 `apply_patch` 写 / 删工作区外的文件时,才设成 `false`。

## 相关

> - [Exec Approvals](/tools/exec-approvals) — approval gates for shell commands
> - [Sandboxing](/gateway/sandboxing) — running commands in sandboxed environments
> - [Background Process](/gateway/background-process) — long-running exec and process tool
> - [Security](/gateway/security) — tool policy and elevated access

- [Exec Approvals](/tools/exec-approvals) —— shell 命令的审批闸门
- [沙箱](/gateway/sandboxing) —— 在沙箱环境里跑命令
- [后台进程](/gateway/background-process) —— 长运行 exec 和 process 工具
- [安全](/gateway/security) —— 工具策略和提权访问
