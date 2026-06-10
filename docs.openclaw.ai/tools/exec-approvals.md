# Exec approvals

## 架构精读

> 跳过不影响阅读翻译正文。

### Agent 想跑 `git push`——谁来决定放不放行？

exec.md 讲了"在哪里跑"，elevated.md 讲了"怎么逃出沙箱"。这篇讲的是最后一道关：**具体这条命令到底让不让跑**。

这三层组合起来才是完整的安全栈：sandbox 隔离 → elevated 开门 → approvals 审批。缺任何一层都不完整。

### 双重策略源、取严

有两个地方配审批策略：

1. **`tools.exec.*`**：在 OpenClaw 配置里，跟着会话 / Agent 走
2. **`~/.openclaw/exec-approvals.json`**：在宿主机器上，跟着那台物理机走

生效策略 = 两者中更严的那个。凭什么？因为它们代表不同角色：配置是"Agent 运维"说了算，JSON 文件是"宿主机主人"说了算。两边都同意才放行。

这跟 Android 的权限模型一样：app manifest 声明要用摄像头（开发者意图），但用户还得单独授权（机主意图）。

### 信任模型：谁是可信发起方？

审批要有人点"同意"。谁有资格点？

Gateway 认证的用户 = 可信操作员。他们能审批所有命令。但 Agent 也可能从聊天通道收到消息——这些消息的发送者不一定可信。所以审批有个 `allowFrom` 白名单：只有白名单里的发送者的审批才算数。

这防的是：恶意用户在群聊里发 `/approve` 试图放行危险命令。

### "记住这个命令"：allow-always 的设计

每次命令都要用户确认太烦。`allow-always` 让用户说"以后这条命令不用问我了"。但记住的是**精确的命令文本**——不是"所有 git 命令"，而是"这条具体的 `git push origin main`"。

安全和便利之间的妥协点：不是按工具粒度（太粗），也不是每次都问（太烦），而是按具体命令粒度。

---

> Exec approvals are the **companion app / node host guardrail** for letting
> a sandboxed agent run commands on a real host (`gateway` or `node`). A
> safety interlock: commands are allowed only when policy + allowlist +
> (optional) user approval all agree. Exec approvals stack **on top of**
> tool policy and elevated gating (unless elevated is set to `full`, which
> skips approvals).

Exec 审批是**伴侣 app / 节点宿主的护栏**,让一个沙箱化的 agent 能在真实宿主上跑命令(`gateway` 或 `node`)。它是一道安全联锁:策略 + 白名单 + (可选)用户审批三者都同意时才放行。Exec 审批**叠加在**工具策略和提权闸门之上(除非提权设成 `full`,那会跳过审批)。

> <Note>
> Effective policy is the **stricter** of `tools.exec.*` and approvals
> defaults; if an approvals field is omitted, the `tools.exec` value is
> used. Host exec also uses local approvals state on that machine - a
> host-local `ask: "always"` in `~/.openclaw/exec-approvals.json` keeps
> prompting even if session or config defaults request `ask: "on-miss"`.
> </Note>

[展开: 注意] 实际策略是 `tools.exec.*` 和审批默认两者中**更严**的;审批字段省略时,用 `tools.exec` 的值。宿主 exec 还会用那台机器上的本地审批状态 ——`~/.openclaw/exec-approvals.json` 里的宿主本地 `ask: "always"` 会一直提示,哪怕会话或配置默认请求的是 `ask: "on-miss"`。

## 查看生效策略

> | Command                                                          | What it shows                                                                          |

| 命令                                                              | 显示什么                                                                            |
| ----------------------------------------------------------------- | ----------------------------------------------------------------------------------- |
| `openclaw approvals get` / `--gateway` / `--node <id\|name\|ip>`  | 请求的策略、宿主策略来源、生效结果。                                                |
| `openclaw exec-policy show`                                       | 本机合并后的视图。                                                                  |
| `openclaw exec-policy set` / `preset`                             | 一步把本地请求策略和本地宿主审批文件同步。                                          |

> When a local scope requests `host=node`, `exec-policy show` reports that
> scope as node-managed at runtime instead of pretending the local
> approvals file is the source of truth.

本地作用域请求 `host=node` 时,`exec-policy show` 把那个作用域报告为运行时由节点管理,不会假装本地审批文件是权威源。

> If the companion app UI is **not available**, any request that would
> normally prompt is resolved by the **ask fallback** (default: `deny`).

伴侣 app UI **不可用**时,任何本该提示的请求都按 **ask fallback**(默认 `deny`)解析。

> <Tip>
> Native chat approval clients can seed channel-specific affordances on the
> pending approval message. For example, Matrix seeds reaction shortcuts
> (`✅` allow once, `❌` deny, `♾️` allow always) while still leaving
> `/approve ...` commands in the message as a fallback.
> </Tip>

[展开: 提示] 原生聊天审批客户端可以在挂起的审批消息上预置按通道的便捷操作。比如 Matrix 预置反应快捷键(`✅` 这次允许、`❌` 拒绝、`♾️` 始终允许),同时仍在消息里留 `/approve ...` 命令作回退。

## 在哪里生效

> Exec approvals are enforced locally on the execution host:
>
> - **Gateway host** → `openclaw` process on the gateway machine.
> - **Node host** → node runner (macOS companion app or headless node host).

Exec 审批在执行宿主上本地强制:

- **Gateway 宿主** → gateway 机器上的 `openclaw` 进程。
- **节点宿主** → 节点 runner(macOS 伴侣 app 或无头节点宿主)。

### 信任模型

> - Gateway-authenticated callers are trusted operators for that Gateway.
> - Paired nodes extend that trusted operator capability onto the node host.
> - Exec approvals reduce accidental execution risk, but are **not** a per-user auth boundary or filesystem read-only policy.
> - Once approved, a command can mutate files according to the selected host or sandbox filesystem permissions.
> - Approved node-host runs bind canonical execution context: canonical cwd, exact argv, env binding when present, and pinned executable path when applicable.
> - For shell scripts and direct interpreter/runtime file invocations, OpenClaw also tries to bind one concrete local file operand. If that bound file changes after approval but before execution, the run is denied instead of executing drifted content.
> - File binding is intentionally best-effort, **not** a complete semantic model of every interpreter/runtime loader path. If approval mode cannot identify exactly one concrete local file to bind, it refuses to mint an approval-backed run instead of pretending full coverage.

- 通过 Gateway 认证的调用方就是那个 Gateway 的受信任运维。
- 已配对的节点把这种"受信任运维"能力延伸到节点宿主。
- Exec 审批降低意外执行的风险,但**不是**按用户的认证边界,也**不是**文件系统只读策略。
- 审批通过后,命令可以按所选宿主或沙箱文件系统权限改文件。
- 已审批的节点宿主运行会绑定规范的执行上下文:规范 cwd、精确 argv、(若有)env 绑定、(若适用)钉死的可执行路径。
- 对 shell 脚本和直接调用解释器 / 运行时文件,OpenClaw 还会尝试绑定一个具体的本地文件操作数。绑定的文件在审批之后、执行之前被改,运行会被拒,而不是执行漂移后的内容。
- 文件绑定刻意是尽力而为的,**不是**对每种解释器 / 运行时 loader 路径都建语义模型。审批模式无法识别"正好一个具体本地文件"来绑定时,它拒绝铸出一个受审批支撑的运行,不会假装覆盖完整。

### macOS 拆分

> - The **node host service** forwards `system.run` to the **macOS app** over local IPC.
> - The **macOS app** enforces approvals and executes the command in UI context.

- **节点宿主服务**通过本地 IPC 把 `system.run` 转给 **macOS app**。
- **macOS app** 强制审批,并在 UI 上下文里执行命令。

## 设置和存储

> Approvals live in a local JSON file on the execution host:

审批存在执行宿主上的本地 JSON 文件里:

```text
~/.openclaw/exec-approvals.json
```

> Example schema:

示例 schema:

```json
{
  "version": 1,
  "socket": {
    "path": "~/.openclaw/exec-approvals.sock",
    "token": "base64url-token"
  },
  "defaults": {
    "security": "deny",
    "ask": "on-miss",
    "askFallback": "deny",
    "autoAllowSkills": false
  },
  "agents": {
    "main": {
      "security": "allowlist",
      "ask": "on-miss",
      "askFallback": "deny",
      "autoAllowSkills": true,
      "allowlist": [
        {
          "id": "B0C8C0B3-2C2D-4F8A-9A3C-5A4B3C2D1E0F",
          "pattern": "~/Projects/**/bin/rg",
          "source": "allow-always",
          "commandText": "rg -n TODO",
          "lastUsedAt": 1737150000000,
          "lastUsedCommand": "rg -n TODO",
          "lastResolvedPath": "/Users/user/Projects/.../bin/rg"
        }
      ]
    }
  }
}
```

## 策略调节项

### `exec.security`

> `security` (`"deny" | "allowlist" | "full"`)
>   - `deny` - block all host exec requests.
>   - `allowlist` - allow only allowlisted commands.
>   - `full` - allow everything (equivalent to elevated).

`security`(`"deny" | "allowlist" | "full"`)

- `deny` —— 拦截所有宿主 exec 请求。
- `allowlist` —— 只允许白名单里的命令。
- `full` —— 全部放行(等价于提权)。

### `exec.ask`

> `ask` (`"off" | "on-miss" | "always"`)
>   - `off` - never prompt.
>   - `on-miss` - prompt only when the allowlist does not match.
>   - `always` - prompt on every command. `allow-always` durable trust does **not** suppress prompts when effective ask mode is `always`.

`ask`(`"off" | "on-miss" | "always"`)

- `off` —— 从不提示。
- `on-miss` —— 白名单没匹配上时才提示。
- `always` —— 每条命令都提示。生效的 ask 模式是 `always` 时,`allow-always` 这种持久化信任**不会**抑制提示。

### `askFallback`

> `askFallback` (`"deny" | "allowlist" | "full"`)
>   Resolution when a prompt is required but no UI is reachable.
>
> - `deny` - block.
> - `allowlist` - allow only if allowlist matches.
> - `full` - allow.

`askFallback`(`"deny" | "allowlist" | "full"`)

需要提示但拿不到 UI 时的处置:

- `deny` —— 拦截。
- `allowlist` —— 白名单匹配才放行。
- `full` —— 放行。

### `tools.exec.strictInlineEval`

> `strictInlineEval` (boolean) — When `true`, OpenClaw treats inline code-eval forms as approval-only even if the interpreter binary itself is allowlisted. Defense-in-depth for interpreter loaders that do not map cleanly to one stable file operand.

`strictInlineEval`(boolean)——`true` 时,OpenClaw 把内联代码 eval 形式当作"必须审批",哪怕解释器二进制本身在白名单里。这是给那些不容易映射到单个稳定文件操作数的解释器 loader 的纵深防御。

> Examples that strict mode catches:

严格模式抓的例子:

- `python -c`
- `node -e`、`node --eval`、`node -p`
- `ruby -e`
- `perl -e`、`perl -E`
- `php -r`
- `lua -e`
- `osascript -e`

> In strict mode these commands still need explicit approval, and
> `allow-always` does not persist new allowlist entries for them
> automatically.

严格模式下,这些命令仍然要显式审批,`allow-always` 也不会自动给它们持久化新的白名单条目。

### `tools.exec.commandHighlighting`

> `commandHighlighting` (boolean, default: false) — Controls only presentation in exec approval prompts. When enabled, OpenClaw may attach parser-derived command spans so Web approval prompts can highlight command tokens. Set it to `true` to enable command text highlighting.

`commandHighlighting`(boolean,默认 false)—— 只控制 exec 审批提示里的展示。启用时,OpenClaw 可以附上解析器推导出的命令片段,让 Web 审批提示能高亮命令 token。设成 `true` 启用命令文本高亮。

> This setting does **not** change `security`, `ask`, allowlist matching,
> strict inline-eval behavior, approval forwarding, or command execution.
> It can be set globally under `tools.exec.commandHighlighting` or per
> agent under `agents.list[].tools.exec.commandHighlighting`.

这个设置**不**改 `security`、`ask`、白名单匹配、严格内联 eval 行为、审批转发或命令执行。可以全局设在 `tools.exec.commandHighlighting`,或按 agent 设在 `agents.list[].tools.exec.commandHighlighting`。

## YOLO 模式(无审批)

> If you want host exec to run without approval prompts, you must open
> **both** policy layers - requested exec policy in OpenClaw config
> (`tools.exec.*`) **and** host-local approvals policy in
> `~/.openclaw/exec-approvals.json`.

想让宿主 exec 不弹审批就跑,你必须同时打开**两层**策略 —— OpenClaw 配置里的请求 exec 策略(`tools.exec.*`),**和**`~/.openclaw/exec-approvals.json` 里的宿主本地审批策略。

> YOLO is the default host behavior unless you tighten it explicitly:

除非你显式收紧,YOLO 就是宿主默认行为:

> | Layer                 | YOLO setting               |

| 层                     | YOLO 设置                   |
| --------------------- | -------------------------- |
| `tools.exec.security` | `gateway`/`node` 上设 `full` |
| `tools.exec.ask`      | `off`                      |
| 宿主 `askFallback`    | `full`                     |

> <Warning>
> **Important distinctions:**
>
> - `tools.exec.host=auto` chooses **where** exec runs: sandbox when available, otherwise gateway.
> - YOLO chooses **how** host exec is approved: `security=full` plus `ask=off`.
> - In YOLO mode, OpenClaw does **not** add a separate heuristic command-obfuscation approval gate or script-preflight rejection layer on top of the configured host exec policy.
> - `auto` does not make gateway routing a free override from a sandboxed session. A per-call `host=node` request is allowed from `auto`; `host=gateway` is only allowed from `auto` when no sandbox runtime is active. For a stable non-auto default, set `tools.exec.host` or use `/exec host=...` explicitly.
> </Warning>

[展开: 警告] **重要区分:**

- `tools.exec.host=auto` 决定 exec **在哪里**跑:沙箱可用就用沙箱,否则用 gateway。
- YOLO 决定宿主 exec **怎么**审批:`security=full` 加 `ask=off`。
- YOLO 模式下,OpenClaw **不**在配置好的宿主 exec 策略之上再加一道启发式命令混淆审批闸门或脚本预检拒绝层。
- `auto` 不会让"从沙箱化会话路由到 gateway"成为自由覆盖。从 `auto` 起,单次调用 `host=node` 是允许的;`host=gateway` 只在没有沙箱运行时才允许。要一个稳定的非 auto 默认,设 `tools.exec.host` 或显式用 `/exec host=...`。

> CLI-backed providers that expose their own noninteractive permission mode
> can follow this policy. Claude CLI adds
> `--permission-mode bypassPermissions` when OpenClaw's requested exec
> policy is YOLO. Override that backend behavior with explicit Claude args
> under `agents.defaults.cliBackends.claude-cli.args` / `resumeArgs` -
> for example `--permission-mode default`, `acceptEdits`, or
> `bypassPermissions`.

暴露了自己的非交互权限模式的 CLI 后端 provider 可以跟随这套策略。OpenClaw 的请求 exec 策略是 YOLO 时,Claude CLI 加 `--permission-mode bypassPermissions`。要覆盖后端行为,在 `agents.defaults.cliBackends.claude-cli.args` / `resumeArgs` 下加显式 Claude 参数 —— 比如 `--permission-mode default`、`acceptEdits`、`bypassPermissions`。

> If you want a more conservative setup, tighten either layer back to
> `allowlist` / `on-miss` or `deny`.

想更保守,把任一层收紧回 `allowlist` / `on-miss` 或 `deny`。

### 持久化的 gateway 宿主"永不提示"配置

> <Step title="Set the requested config policy">

[步骤 1: 设请求的配置策略]

```bash
openclaw config set tools.exec.host gateway
openclaw config set tools.exec.security full
openclaw config set tools.exec.ask off
openclaw gateway restart
```

> <Step title="Match the host approvals file">

[步骤 2: 让宿主审批文件匹配]

```bash
openclaw approvals set --stdin <<'EOF'
{
  version: 1,
  defaults: {
    security: "full",
    ask: "off",
    askFallback: "full"
  }
}
EOF
```

### 本地快捷

```bash
openclaw exec-policy preset yolo
```

> That local shortcut updates both:
>
> - Local `tools.exec.host/security/ask`.
> - Local `~/.openclaw/exec-approvals.json` defaults.

这个本地快捷同时更新两边:

- 本地 `tools.exec.host/security/ask`。
- 本地 `~/.openclaw/exec-approvals.json` 默认。

> It is intentionally local-only. To change gateway-host or node-host
> approvals remotely, use `openclaw approvals set --gateway` or
> `openclaw approvals set --node <id|name|ip>`.

它刻意只针对本地。要远程改 gateway 宿主或节点宿主的审批,用 `openclaw approvals set --gateway` 或 `openclaw approvals set --node <id|name|ip>`。

### 节点宿主

> For a node host, apply the same approvals file on that node instead:

节点宿主上,把同样的审批文件应用到那个节点:

```bash
openclaw approvals set --node <id|name|ip> --stdin <<'EOF'
{
  version: 1,
  defaults: {
    security: "full",
    ask: "off",
    askFallback: "full"
  }
}
EOF
```

> <Note>
> **Local-only limitations:**
>
> - `openclaw exec-policy` does not synchronize node approvals.
> - `openclaw exec-policy set --host node` is rejected.
> - Node exec approvals are fetched from the node at runtime, so node-targeted updates must use `openclaw approvals --node ...`.
> </Note>

[展开: 注意] **仅本地的限制:**

- `openclaw exec-policy` 不同步节点审批。
- `openclaw exec-policy set --host node` 被拒。
- 节点 exec 审批在运行时从节点拉,所以针对节点的更新必须用 `openclaw approvals --node ...`。

### 仅会话的快捷

> - `/exec security=full ask=off` changes only the current session.
> - `/elevated full` is a break-glass shortcut that also skips exec approvals for that session.

- `/exec security=full ask=off` 只改当前会话。
- `/elevated full` 是个紧急通道快捷,在那个会话里也会跳过 exec 审批。

> If the host approvals file stays stricter than config, the stricter host
> policy still wins.

宿主审批文件比配置更严时,更严的宿主策略仍然赢。

## 白名单(按 agent)

> Allowlists are **per agent**. If multiple agents exist, switch which agent
> you are editing in the macOS app. Patterns are glob matches.

白名单是**按 agent** 的。多个 agent 存在时,在 macOS app 里切换正在编辑的 agent。模式是 glob 匹配。

> Patterns can be resolved binary path globs or bare command-name globs.
> Bare names match only commands invoked through `PATH`, so `rg` can match
> `/opt/homebrew/bin/rg` when the command is `rg`, but **not** `./rg` or
> `/tmp/rg`. Use a path glob when you want to trust one specific binary
> location.

模式可以是解析出的二进制路径 glob,也可以是裸命令名 glob。裸名只匹配通过 `PATH` 调起的命令,所以 `rg` 在命令是 `rg` 时能匹配 `/opt/homebrew/bin/rg`,但**不能**匹配 `./rg` 或 `/tmp/rg`。要信任某个特定二进制位置,用路径 glob。

> Legacy `agents.default` entries are migrated to `agents.main` on load.
> Shell chains such as `echo ok && pwd` still need every top-level segment
> to satisfy allowlist rules.

旧的 `agents.default` 条目在加载时迁到 `agents.main`。shell 链(如 `echo ok && pwd`)仍要每个顶层段满足白名单规则。

> Examples:
>
> - `rg`
> - `~/Projects/**/bin/peekaboo`
> - `~/.local/bin/*`
> - `/opt/homebrew/bin/rg`

例子:

- `rg`
- `~/Projects/**/bin/peekaboo`
- `~/.local/bin/*`
- `/opt/homebrew/bin/rg`

### 用 argPattern 限制参数

> Add `argPattern` when an allowlist entry should match a binary and a
> specific argument shape. OpenClaw evaluates the regular expression
> against the parsed command arguments, excluding the executable token
> (`argv[0]`). For hand-authored entries, arguments are joined with a
> single space, so anchor the pattern when you need an exact match.

希望白名单条目同时匹配二进制和特定参数形态时,加 `argPattern`。OpenClaw 用正则匹配解析出的命令参数,排除可执行 token(`argv[0]`)。手写条目里参数用单个空格连起来,要精确匹配就锚定模式。

```json
{
  "version": 1,
  "agents": {
    "main": {
      "allowlist": [
        {
          "pattern": "python3",
          "argPattern": "^safe\\.py$"
        }
      ]
    }
  }
}
```

> That entry allows `python3 safe.py`; `python3 other.py` is an allowlist
> miss. If a path-only entry for the same binary is also present, unmatched
> arguments can still fall back to that path-only entry. Omit the path-only
> entry when the goal is to restrict the binary to the declared arguments.

这条允许 `python3 safe.py`;`python3 other.py` 是白名单未命中。同一二进制还有一条仅路径的条目时,没匹配上的参数仍能回退到那条仅路径的条目。想把二进制限制到声明的参数,就别留那条仅路径条目。

> Entries saved by approval flows can use an internal separator format for
> exact argv matching. Prefer the UI or approval flow to regenerate those
> entries instead of hand-editing the encoded value. If OpenClaw cannot
> parse argv for a command segment, entries with `argPattern` do not match.

审批流程存的条目可能用内部分隔符格式做精确 argv 匹配。优先用 UI 或审批流程重新生成那些条目,别手动编辑编码后的值。OpenClaw 解析不出某个命令段的 argv 时,带 `argPattern` 的条目不匹配。

> Each allowlist entry supports:

每个白名单条目支持:

> | Field              | Meaning                                                       |

| 字段                | 含义                                                       |
| ------------------- | ---------------------------------------------------------- |
| `pattern`           | 解析出的二进制路径 glob 或裸命令名 glob                    |
| `argPattern`        | 可选的 argv 正则;省略时是仅路径条目                      |
| `id`                | 给 UI 身份用的稳定 UUID                                    |
| `source`            | 条目来源,如 `allow-always`                                |
| `commandText`       | 审批流程创建条目时捕获的命令文本                          |
| `lastUsedAt`        | 上次使用时间戳                                            |
| `lastUsedCommand`   | 上次匹配上的命令                                          |
| `lastResolvedPath`  | 上次解析出的二进制路径                                    |

## 自动允许技能 CLI

> When **Auto-allow skill CLIs** is enabled, executables referenced by
> known skills are treated as allowlisted on nodes (macOS node or headless
> node host). This uses `skills.bins` over the Gateway RPC to fetch the
> skill bin list. Disable this if you want strict manual allowlists.

启用 **Auto-allow skill CLIs** 时,已知技能引用的可执行文件在节点上(macOS 节点或无头节点宿主)被视作白名单内。这通过 Gateway RPC 上的 `skills.bins` 拉技能 bin 列表。想要严格的手工白名单就关掉它。

> <Warning>
> - This is an **implicit convenience allowlist**, separate from manual path allowlist entries.
> - It is intended for trusted operator environments where Gateway and node are in the same trust boundary.
> - If you require strict explicit trust, keep `autoAllowSkills: false` and use manual path allowlist entries only.
> </Warning>

[展开: 警告]

- 这是一份**隐式便利白名单**,跟手工路径白名单条目分开。
- 它是给 Gateway 和节点在同一信任边界内的可信运维环境用的。
- 你要求严格的显式信任,就保持 `autoAllowSkills: false`,只用手工路径白名单条目。

## Safe bin 和审批转发

> For safe bins (the stdin-only fast-path), interpreter binding details, and
> how to forward approval prompts to Slack/Discord/Telegram (or run them as
> native approval clients), see
> [Exec approvals - advanced](/tools/exec-approvals-advanced).

safe bin(仅 stdin 快速通道)、解释器绑定细节,以及怎么把审批提示转发到 Slack/Discord/Telegram(或作为原生审批客户端运行),见 [Exec approvals - advanced](/tools/exec-approvals-advanced)。

## Control UI 编辑

> Use the **Control UI → Nodes → Exec approvals** card to edit defaults,
> per-agent overrides, and allowlists. Pick a scope (Defaults or an agent),
> tweak the policy, add/remove allowlist patterns, then **Save**. The UI
> shows last-used metadata per pattern so you can keep the list tidy.

用 **Control UI → Nodes → Exec approvals** 卡片编辑默认、按 agent 覆盖和白名单。选作用域(Defaults 或某个 agent),调策略,加 / 删白名单模式,然后 **Save**。UI 按模式显示上次使用元数据,方便保持列表整洁。

> The target selector chooses **Gateway** (local approvals) or a **Node**.
> Nodes must advertise `system.execApprovals.get/set` (macOS app or
> headless node host). If a node does not advertise exec approvals yet,
> edit its local `~/.openclaw/exec-approvals.json` directly.

目标选择器选 **Gateway**(本地审批)或某个 **Node**。节点必须声明 `system.execApprovals.get/set`(macOS app 或无头节点宿主)。节点还没声明 exec 审批时,直接编辑它本地的 `~/.openclaw/exec-approvals.json`。

> CLI: `openclaw approvals` supports gateway or node editing - see
> [Approvals CLI](/cli/approvals).

CLI:`openclaw approvals` 支持编辑 gateway 或节点 —— 见 [Approvals CLI](/cli/approvals)。

## 审批流程

> When a prompt is required, the gateway broadcasts
> `exec.approval.requested` to operator clients. The Control UI and macOS
> app resolve it via `exec.approval.resolve`, then the gateway forwards the
> approved request to the node host.

需要提示时,gateway 向运维客户端广播 `exec.approval.requested`。Control UI 和 macOS app 通过 `exec.approval.resolve` 解析它,然后 gateway 把审批通过的请求转给节点宿主。

> For `host=node`, approval requests include a canonical `systemRunPlan`
> payload. The gateway uses that plan as the authoritative
> command/cwd/session context when forwarding approved `system.run`
> requests.

对 `host=node`,审批请求包含一份规范的 `systemRunPlan` 载荷。gateway 转发审批通过的 `system.run` 请求时,把这份 plan 作为命令 / cwd / 会话上下文的权威源。

> That matters for async approval latency:
>
> - The node exec path prepares one canonical plan up front.
> - The approval record stores that plan and its binding metadata.
> - Once approved, the final forwarded `system.run` call reuses the stored plan instead of trusting later caller edits.
> - If the caller changes `command`, `rawCommand`, `cwd`, `agentId`, or `sessionKey` after the approval request was created, the gateway rejects the forwarded run as an approval mismatch.

这对异步审批延迟很关键:

- 节点 exec 路径一开始就准备一份规范 plan。
- 审批记录存这份 plan 和它的绑定元数据。
- 通过后,最终转发的 `system.run` 调用复用存好的 plan,不信任之后调用方的编辑。
- 审批请求创建后,调用方又改了 `command`、`rawCommand`、`cwd`、`agentId`、`sessionKey`,gateway 把转发的运行以审批不匹配拒掉。

## 系统事件

> Exec lifecycle is surfaced as system messages:
>
> - `Exec running` (only if the command exceeds the running notice threshold).
> - `Exec finished`.

Exec 生命周期以系统消息形式露出:

- `Exec running`(只在命令超过运行通知阈值时)。
- `Exec finished`。

> These are posted to the agent's session after the node reports the event.
> Denied exec approvals are terminal: OpenClaw can report the denial to the
> operator or direct chat route, but it does not post `Exec denied` back into the
> agent session or wake agent work.
> Gateway-host exec approvals emit the same lifecycle events when the
> command finishes (and optionally when running longer than the threshold).
> Approval-gated execs reuse the approval id as the `runId` in these
> messages for easy correlation.

节点上报事件之后,这些消息会贴到 agent 的会话里。被拒的 exec 审批是终态:OpenClaw 可以把拒绝报告给运维或直接聊天路径,但不会把 `Exec denied` 贴回 agent 会话,也不会唤醒 agent 工作。
Gateway 宿主的 exec 审批在命令完成时发同样的生命周期事件(可选在运行超阈值时也发)。走审批闸门的 exec 在这些消息里复用审批 id 作 `runId`,方便关联。

## 拒绝后的行为

> When an async exec approval is denied, OpenClaw treats the request as terminal.
> It can show a concise denial to the operator or direct chat route, but it does
> not send denial guidance back through the agent session. That keeps a denied
> command from becoming another model turn and prevents the agent from reusing
> output from an earlier run of the same command.

异步 exec 审批被拒时,OpenClaw 把请求当终态处理。它可以给运维或直接聊天路径展示一条紧凑的拒绝消息,但不会通过 agent 会话发回拒绝指引。这避免被拒命令变成另一次模型轮次,也防止 agent 复用同一条命令早先一次运行的输出。

## 影响

> - **`full`** is powerful; prefer allowlists when possible.
> - **`ask`** keeps you in the loop while still allowing fast approvals.
> - Per-agent allowlists prevent one agent's approvals from leaking into others.
> - Approvals only apply to host exec requests from **authorized senders**. Unauthorized senders cannot issue `/exec`.
> - `/exec security=full` is a session-level convenience for authorized operators and skips approvals by design. To hard-block host exec, set approvals security to `deny` or deny the `exec` tool via tool policy.

- **`full`** 强大;可能时优先用白名单。
- **`ask`** 让你保持在回路里,同时仍能快速审批。
- 按 agent 的白名单防止一个 agent 的审批漏到其他 agent。
- 审批只对**授权发送者**的宿主 exec 请求生效。未授权发送者不能发 `/exec`。
- `/exec security=full` 是给授权运维的会话级便利,按设计跳过审批。要硬拦宿主 exec,把审批 security 设成 `deny`,或通过工具策略拒绝 `exec` 工具。

## 相关

> - Exec approvals - advanced — Safe bins, interpreter binding, and approval forwarding to chat.
> - Exec tool — Shell command execution tool.
> - Elevated mode — Break-glass path that also skips approvals.
> - Sandboxing — Sandbox modes and workspace access.
> - Security — Security model and hardening.
> - Sandbox vs tool policy vs elevated — When to reach for each control.
> - Skills — Skill-backed auto-allow behavior.

- [Exec approvals - advanced](/tools/exec-approvals-advanced) —— safe bin、解释器绑定、把审批转发到聊天。
- [Exec tool](/tools/exec) —— shell 命令执行工具。
- [提权模式](/tools/elevated) —— 紧急通道,同时跳过审批。
- [沙箱](/gateway/sandboxing) —— 沙箱模式和工作区访问。
- [安全](/gateway/security) —— 安全模型和加固。
- [沙箱 vs 工具策略 vs 提权](/gateway/sandbox-vs-tool-policy-vs-elevated) —— 什么时候用哪种控制。
- [技能](/tools/skills) —— 技能撑着的自动允许行为。
