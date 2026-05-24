# Lobster

> Lobster is a workflow shell that lets OpenClaw run multi-step tool sequences as a single, deterministic operation with explicit approval checkpoints.

Lobster 是一个工作流壳层,让 OpenClaw 把多步工具序列作为单一、确定性的操作来运行,带显式的审批检查点。

> Lobster is one authoring layer above detached background work. For flow orchestration above individual tasks, see [Task Flow](/automation/taskflow) (`openclaw tasks flow`). For the task activity ledger, see [`openclaw tasks`](/automation/tasks).

Lobster 是分离式后台工作之上的一层创作层。比单任务更高层的流程编排见 [Task Flow](/automation/taskflow)(`openclaw tasks flow`)。任务活动台账见 [`openclaw tasks`](/automation/tasks)。

## 钩子

> Your assistant can build the tools that manage itself. Ask for a workflow, and 30 minutes later you have a CLI plus pipelines that run as one call. Lobster is the missing piece: deterministic pipelines, explicit approvals, and resumable state.

你的助手能构建用来管理它自己的工具。要一个工作流,30 分钟后你就有了一套 CLI 加一份只需一次调用的管线。Lobster 是缺失的那块:确定性管线、显式审批、可恢复的状态。

## 为什么要这个

> Today, complex workflows require many back-and-forth tool calls. Each call costs tokens, and the LLM has to orchestrate every step. Lobster moves that orchestration into a typed runtime:

如今复杂的工作流要靠很多来回的工具调用,每次调用都烧 token,LLM 还得编排每一步。Lobster 把这种编排搬进类型化的运行时:

> - **One call instead of many**: OpenClaw runs one Lobster tool call and gets a structured result.
> - **Approvals built in**: Side effects (send email, post comment) halt the workflow until explicitly approved.
> - **Resumable**: Halted workflows return a token; approve and resume without re-running everything.

- **一次调用代替多次**:OpenClaw 跑一次 Lobster 工具调用,拿到一份结构化结果。
- **审批内建**:有副作用的动作(发邮件、贴评论)会暂停工作流,等显式审批通过。
- **可恢复**:暂停的工作流返回一个 token;批准后恢复,不用重跑全部。

## 为什么用 DSL 而不是普通程序?

> Lobster is intentionally small. The goal is not "a new language," it's a predictable, AI-friendly pipeline spec with first-class approvals and resume tokens.

Lobster 刻意小。目标不是"一门新语言",而是一份可预测、对 AI 友好的管线规范,把审批和恢复 token 作为一等公民。

> - **Approve/resume is built in**: A normal program can prompt a human, but it can't _pause and resume_ with a durable token without you inventing that runtime yourself.
> - **Determinism + auditability**: Pipelines are data, so they're easy to log, diff, replay, and review.
> - **Constrained surface for AI**: A tiny grammar + JSON piping reduces "creative" code paths and makes validation realistic.
> - **Safety policy baked in**: Timeouts, output caps, sandbox checks, and allowlists are enforced by the runtime, not each script.
> - **Still programmable**: Each step can call any CLI or script. If you want JS/TS, generate `.lobster` files from code.

- **审批 / 恢复内建**:普通程序也能向人提问,但要做到带持久化 token 的 _暂停再恢复_,你得自己造那套运行时。
- **确定性 + 可审计**:管线是数据,所以好记日志、好做 diff、好回放、好评审。
- **给 AI 的受限接口**:微型语法 + JSON 管道,减少了"创造性"代码路径,让校验变得现实。
- **安全策略烤进去了**:超时、输出上限、沙箱检查、白名单由运行时强制,不靠每个脚本自己写。
- **仍然可编程**:每一步都能调任何 CLI 或脚本。要 JS/TS 的话,用代码生成 `.lobster` 文件。

## 它怎么工作

> OpenClaw runs Lobster workflows **in-process** using an embedded runner. No external CLI subprocess is spawned; the workflow engine executes inside the gateway process and returns a JSON envelope directly.
> If the pipeline pauses for approval, the tool returns a `resumeToken` so you can continue later.

OpenClaw 用嵌入式运行器**进程内**跑 Lobster 工作流。不派生外部 CLI 子进程;工作流引擎在 gateway 进程内执行,直接返回 JSON 封套。
管线为了审批暂停时,工具返回一个 `resumeToken`,你可以稍后继续。

## 模式:小 CLI + JSON 管道 + 审批

> Build tiny commands that speak JSON, then chain them into a single Lobster call. (Example command names below - swap in your own.)

写几个说 JSON 的小命令,然后把它们串成一次 Lobster 调用。(下面的命令名是示例,换成你自己的。)

```bash
inbox list --json
inbox categorize --json
inbox apply --json
```

```json
{
  "action": "run",
  "pipeline": "exec --json --shell 'inbox list --json' | exec --stdin json --shell 'inbox categorize --json' | exec --stdin json --shell 'inbox apply --json' | approve --preview-from-stdin --limit 5 --prompt 'Apply changes?'",
  "timeoutMs": 30000
}
```

> If the pipeline requests approval, resume with the token:

管线请求审批时,用 token 恢复:

```json
{
  "action": "resume",
  "token": "<resumeToken>",
  "approve": true
}
```

> AI triggers the workflow; Lobster executes the steps. Approval gates keep side effects explicit and auditable.

AI 触发工作流;Lobster 执行各步骤。审批闸门让副作用保持显式、可审计。

> Example: map input items into tool calls:

例子:把输入项映射成工具调用:

```bash
gog.gmail.search --query 'newer_than:1d' \
  | openclaw.invoke --tool message --action send --each --item-key message --args-json '{"provider":"telegram","to":"..."}'
```

## JSON 专属的 LLM 步骤(llm-task)

> For workflows that need a **structured LLM step**, enable the optional
> `llm-task` plugin tool and call it from Lobster. This keeps the workflow
> deterministic while still letting you classify/summarize/draft with a model.

需要**结构化 LLM 步骤**的工作流,启用可选的 `llm-task` 插件工具,从 Lobster 里调。这让工作流保持确定性,同时仍能用模型做分类 / 摘要 / 起草。

> Enable the tool:

启用工具:

```json
{
  "plugins": {
    "entries": {
      "llm-task": { "enabled": true }
    }
  },
  "agents": {
    "list": [
      {
        "id": "main",
        "tools": { "alsoAllow": ["llm-task"] }
      }
    ]
  }
}
```

### 重要限制:嵌入式 Lobster vs `openclaw.invoke`

> The bundled Lobster plugin runs workflows **in-process** inside the gateway. In that embedded mode, `openclaw.invoke` does **not** automatically inherit a gateway URL/auth context for nested OpenClaw CLI tool calls.

内置 Lobster 插件在 gateway 内**进程内**跑工作流。在这种嵌入式模式下,`openclaw.invoke` **不会**自动为嵌套的 OpenClaw CLI 工具调用继承 gateway URL / 认证上下文。

> That means this pattern is **not currently reliable in the embedded runner**:

也就是说,这种模式**目前在嵌入式运行器里不可靠**:

```lobster
openclaw.invoke --tool llm-task --action json --args-json '{ ... }'
```

> Use the example below only when running the **standalone Lobster CLI** in an environment where `openclaw.invoke` is already configured with the correct gateway/auth context.

只在跑**独立 Lobster CLI** 且环境里 `openclaw.invoke` 已经配好了正确 gateway / 认证上下文时,才用下面的例子。

> Use it in a standalone Lobster CLI pipeline:

独立 Lobster CLI 管线里用:

```lobster
openclaw.invoke --tool llm-task --action json --args-json '{
  "prompt": "Given the input email, return intent and draft.",
  "thinking": "low",
  "input": { "subject": "Hello", "body": "Can you help?" },
  "schema": {
    "type": "object",
    "properties": {
      "intent": { "type": "string" },
      "draft": { "type": "string" }
    },
    "required": ["intent", "draft"],
    "additionalProperties": false
  }
}'
```

> If you are using the embedded Lobster plugin today, prefer either:
>
> - a direct `llm-task` tool call outside Lobster, or
> - non-`openclaw.invoke` steps inside the Lobster pipeline until a supported embedded bridge is added.

今天你在用嵌入式 Lobster 插件的话,优先用:

- Lobster 外面直接调 `llm-task` 工具,或
- Lobster 管线里不带 `openclaw.invoke` 的步骤,等到支持的嵌入式桥加上为止。

> See [LLM Task](/tools/llm-task) for details and configuration options.

细节和配置选项见 [LLM Task](/tools/llm-task)。

## 工作流文件(.lobster)

> Lobster can run YAML/JSON workflow files with `name`, `args`, `steps`, `env`, `condition`, and `approval` fields. In OpenClaw tool calls, set `pipeline` to the file path.

Lobster 能跑 YAML/JSON 工作流文件,带 `name`、`args`、`steps`、`env`、`condition`、`approval` 字段。OpenClaw 工具调用里,把 `pipeline` 设成文件路径。

```yaml
name: inbox-triage
args:
  tag:
    default: "family"
steps:
  - id: collect
    command: inbox list --json
  - id: categorize
    command: inbox categorize --json
    stdin: $collect.stdout
  - id: approve
    command: inbox apply --approve
    stdin: $categorize.stdout
    approval: required
  - id: execute
    command: inbox apply --execute
    stdin: $categorize.stdout
    condition: $approve.approved
```

> Notes:
>
> - `stdin: $step.stdout` and `stdin: $step.json` pass a prior step's output.
> - `condition` (or `when`) can gate steps on `$step.approved`.

说明:

- `stdin: $step.stdout` 和 `stdin: $step.json` 传递前一步的输出。
- `condition`(或 `when`)能用 `$step.approved` 控制步骤是否跑。

## 装 Lobster

> Bundled Lobster workflows run in-process; no separate `lobster` binary is required. The embedded runner ships with the Lobster plugin.

内置 Lobster 工作流进程内跑;不需要单独的 `lobster` 二进制。嵌入式运行器随 Lobster 插件一起出。

> If you need the standalone Lobster CLI for development or external pipelines, install it from the [Lobster repo](https://github.com/openclaw/lobster) and ensure `lobster` is on `PATH`.

开发或外部管线需要独立 Lobster CLI 的话,从 [Lobster 仓库](https://github.com/openclaw/lobster) 装,确保 `lobster` 在 `PATH` 上。

## 启用工具

> Lobster is an **optional** plugin tool (not enabled by default).

Lobster 是**可选**插件工具(默认不开)。

> Recommended (additive, safe):

推荐(增量、安全):

```json
{
  "tools": {
    "alsoAllow": ["lobster"]
  }
}
```

> Or per-agent:

或按 agent:

```json
{
  "agents": {
    "list": [
      {
        "id": "main",
        "tools": {
          "alsoAllow": ["lobster"]
        }
      }
    ]
  }
}
```

> Avoid using `tools.allow: ["lobster"]` unless you intend to run in restrictive allowlist mode.

除非你想跑严格白名单模式,否则别用 `tools.allow: ["lobster"]`。

> <Note>
> Allowlists are opt-in for optional plugins. `alsoAllow` enables only the named optional plugin tools while preserving the normal core tool set. To restrict core tools, use `tools.allow` with the core tools or groups you want.
> </Note>

[展开: 注意] 白名单对可选插件是 opt-in 的。`alsoAllow` 只启用你点名的可选插件工具,同时保留正常的核心工具集。要限制核心工具,用 `tools.allow` 加你想要的核心工具或工具组。

## 例子:邮件归类

> Without Lobster:

不用 Lobster:

```
用户:"看我邮件,起草回信"
→ openclaw 调 gmail.list
→ LLM 总结
→ 用户:"给 #2 和 #5 起草回信"
→ LLM 起草
→ 用户:"发 #2"
→ openclaw 调 gmail.send
(每天重复,没有"已归类哪些"的记忆)
```

> With Lobster:

用 Lobster:

```json
{
  "action": "run",
  "pipeline": "email.triage --limit 20",
  "timeoutMs": 30000
}
```

> Returns a JSON envelope (truncated):

返回一份 JSON 封套(截断):

```json
{
  "ok": true,
  "status": "needs_approval",
  "output": [{ "summary": "5 need replies, 2 need action" }],
  "requiresApproval": {
    "type": "approval_request",
    "prompt": "Send 2 draft replies?",
    "items": [],
    "resumeToken": "..."
  }
}
```

> User approves → resume:

用户批准 → 恢复:

```json
{
  "action": "resume",
  "token": "<resumeToken>",
  "approve": true
}
```

> One workflow. Deterministic. Safe.

一个工作流。确定。安全。

## 工具参数

### `run`

> Run a pipeline in tool mode.

在工具模式下跑一条管线。

```json
{
  "action": "run",
  "pipeline": "gog.gmail.search --query 'newer_than:1d' | email.triage",
  "cwd": "workspace",
  "timeoutMs": 30000,
  "maxStdoutBytes": 512000
}
```

> Run a workflow file with args:

带参数跑一份工作流文件:

```json
{
  "action": "run",
  "pipeline": "/path/to/inbox-triage.lobster",
  "argsJson": "{\"tag\":\"family\"}"
}
```

### `resume`

> Continue a halted workflow after approval.

审批后继续一条暂停的工作流。

```json
{
  "action": "resume",
  "token": "<resumeToken>",
  "approve": true
}
```

### 可选输入

> - `cwd`: Relative working directory for the pipeline (must stay within the gateway working directory).
> - `timeoutMs`: Abort the workflow if it exceeds this duration (default: 20000).
> - `maxStdoutBytes`: Abort the workflow if output exceeds this size (default: 512000).
> - `argsJson`: JSON string passed to `lobster run --args-json` (workflow files only).

- `cwd`:管线的相对工作目录(必须留在 gateway 工作目录内)。
- `timeoutMs`:工作流超过这个时长就中止(默认 20000)。
- `maxStdoutBytes`:输出超过这个大小就中止(默认 512000)。
- `argsJson`:传给 `lobster run --args-json` 的 JSON 字符串(仅工作流文件)。

## 输出封套

> Lobster returns a JSON envelope with one of three statuses:
>
> - `ok` → finished successfully
> - `needs_approval` → paused; `requiresApproval.resumeToken` is required to resume
> - `cancelled` → explicitly denied or cancelled

Lobster 返回一份 JSON 封套,带三种状态之一:

- `ok` → 成功完成
- `needs_approval` → 暂停;恢复需要 `requiresApproval.resumeToken`
- `cancelled` → 显式拒绝或取消

> The tool surfaces the envelope in both `content` (pretty JSON) and `details` (raw object).

工具在 `content`(格式化 JSON)和 `details`(原始对象)里都暴露封套。

## 审批

> If `requiresApproval` is present, inspect the prompt and decide:
>
> - `approve: true` → resume and continue side effects
> - `approve: false` → cancel and finalize the workflow

`requiresApproval` 出现时,看 prompt 决定:

- `approve: true` → 恢复并继续副作用
- `approve: false` → 取消并收尾工作流

> Use `approve --preview-from-stdin --limit N` to attach a JSON preview to approval requests without custom jq/heredoc glue. Resume tokens are now compact: Lobster stores workflow resume state under its state dir and hands back a small token key.

用 `approve --preview-from-stdin --limit N` 给审批请求附上 JSON 预览,不用自己写 jq / heredoc 胶水。恢复 token 现在很紧凑:Lobster 把工作流恢复状态存在它的状态目录下,给你一个小 token key。

## OpenProse

> OpenProse pairs well with Lobster: use `/prose` to orchestrate multi-agent prep, then run a Lobster pipeline for deterministic approvals. If a Prose program needs Lobster, allow the `lobster` tool for sub-agents via `tools.subagents.tools`. See [OpenProse](/prose).

OpenProse 跟 Lobster 配合很好:用 `/prose` 编排多 agent 准备,然后跑一条 Lobster 管线做确定性审批。Prose 程序需要 Lobster 时,通过 `tools.subagents.tools` 给 sub-agent 放行 `lobster` 工具。见 [OpenProse](/prose)。

## 安全

> - **Local in-process only** - workflows execute inside the gateway process; no network calls from the plugin itself.
> - **No secrets** - Lobster doesn't manage OAuth; it calls OpenClaw tools that do.
> - **Sandbox-aware** - disabled when the tool context is sandboxed.
> - **Hardened** - timeouts and output caps enforced by the embedded runner.

- **仅本地进程内** —— 工作流在 gateway 进程内执行;插件本身不发网络调用。
- **不管密钥** —— Lobster 不管 OAuth;它调管 OAuth 的 OpenClaw 工具。
- **沙箱感知** —— 工具上下文是沙箱化的时禁用。
- **加固过** —— 超时和输出上限由嵌入式运行器强制。

## 排障

> - **`lobster timed out`** → increase `timeoutMs`, or split a long pipeline.
> - **`lobster output exceeded maxStdoutBytes`** → raise `maxStdoutBytes` or reduce output size.
> - **`lobster returned invalid JSON`** → ensure the pipeline runs in tool mode and prints only JSON.
> - **`lobster failed`** → check gateway logs for the embedded runner error details.

- **`lobster timed out`** → 调大 `timeoutMs`,或把长管线拆开。
- **`lobster output exceeded maxStdoutBytes`** → 调大 `maxStdoutBytes`,或减少输出。
- **`lobster returned invalid JSON`** → 确认管线在工具模式下跑,只打印 JSON。
- **`lobster failed`** → 看 gateway 日志里嵌入式运行器的错误细节。

## 延伸阅读

> - [Plugins](/tools/plugin)
> - [Plugin tool authoring](/plugins/building-plugins#registering-agent-tools)

- [插件](/tools/plugin)
- [插件工具编写](/plugins/building-plugins#registering-agent-tools)

## 案例:社区工作流

> One public example: a "second brain" CLI + Lobster pipelines that manage three Markdown vaults (personal, partner, shared). The CLI emits JSON for stats, inbox listings, and stale scans; Lobster chains those commands into workflows like `weekly-review`, `inbox-triage`, `memory-consolidation`, and `shared-task-sync`, each with approval gates. AI handles judgment (categorization) when available and falls back to deterministic rules when not.

一个公开例子:"第二大脑" CLI + Lobster 管线,管理三个 Markdown 仓库(个人、伴侣、共享)。CLI 输出 JSON 形式的统计、收件箱列表、过期扫描;Lobster 把这些命令串成 `weekly-review`、`inbox-triage`、`memory-consolidation`、`shared-task-sync` 这种工作流,每个都带审批闸门。AI 在可用时处理判断(分类),不可用时回退到确定性规则。

> - Thread: [https://x.com/plattenschieber/status/2014508656335770033](https://x.com/plattenschieber/status/2014508656335770033)
> - Repo: [https://github.com/bloomedai/brain-cli](https://github.com/bloomedai/brain-cli)

- 帖子:[https://x.com/plattenschieber/status/2014508656335770033](https://x.com/plattenschieber/status/2014508656335770033)
- 仓库:[https://github.com/bloomedai/brain-cli](https://github.com/bloomedai/brain-cli)

## 相关

> - [Automation](/automation) - scheduling Lobster workflows
> - [Automation Overview](/automation) - all automation mechanisms
> - [Tools Overview](/tools) - all available agent tools

- [自动化](/automation) —— 调度 Lobster 工作流
- [自动化总览](/automation) —— 全部自动化机制
- [工具总览](/tools) —— 全部可用 agent 工具
