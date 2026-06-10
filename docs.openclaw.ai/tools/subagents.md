# Sub-agents

## 架构精读

> 跳过不影响阅读翻译正文。

### 主 agent 忙着——怎么并行跑别的任务又不阻塞用户？

传统方案：开线程。但 LLM agent 不是线程池——每个"线程"有自己的上下文窗口、token 开销、工具权限。所以 sub-agent 不是 fork,是独立会话。

关键设计：push-based 完成通知。子 agent 干完了主动"汇报"给父 session,而不是父不停轮询"你好了没"。跟微服务里的事件驱动一样——回调而非轮询。`sessions_yield` 是父"我先让出控制权,等孩子完成事件"的原语。

隔离是默认的。子 agent 不继承父的 session 工具（防止子 agent 以父的名义发消息）。需要父的上下文时用 `context: "fork"` 显式分叉——代价是 token 翻倍,所以只在真正需要时用。

嵌套深度限制（默认 1,最大 5）是防止递归爆炸的安全阀。推荐深度 2 的"编排者模式"：主 agent → 编排子 agent → 工人子子 agent。每层只看到直接子代的完成通知,不跨级。

线程绑定是另一个维度：子 agent 可以绑到聊天通道的一个线程上,后续该线程的用户消息继续路由到同一个子 agent session。这让长对话场景（如一个子 agent 负责一个 PR review）有了持久上下文。

---

> Sub-agents are background agent runs spawned from an existing agent run.
> They run in their own session and, when finished, announce their result back
> to the requester chat channel. Each sub-agent run is tracked as a background task.

Sub-agent 是从已有 agent 运行中孵化的后台 agent 运行。它们在自己的 session（`agent:<agentId>:subagent:<uuid>`）里跑,完成后向请求者聊天通道**宣告**结果。每个 sub-agent 运行被跟踪为[后台任务](/automation/tasks)。

> Primary goals:

主要目标:

> - Parallelize work without blocking the main run.
> - Keep sub-agents isolated by default.
> - Keep the tool surface hard to misuse.
> - Support configurable nesting depth for orchestrator patterns.

- 并行化研究 / 长任务 / 慢工具,不阻塞主运行。
- 默认隔离（session 分离 + 可选沙箱）。
- 工具面不易误用：sub-agent 默认**不**拿 session 工具。
- 支持可配嵌套深度,用于编排者模式。

> Cost note: each sub-agent has its own context and token usage by default...

[展开: 注意] **开销注意:** 每个 sub-agent 默认有自己的上下文和 token 用量。重或重复任务可以给 sub-agent 配便宜模型,主 agent 留高质量模型。通过 `agents.defaults.subagents.model` 或逐 agent 覆盖配置。子确实需要请求者当前 transcript 时,agent 可以在那次孵化上请求 `context: "fork"`。线程绑定的子 agent session 默认 `context: "fork"`。

## 斜杠命令

> Use `/subagents` to inspect sub-agent runs for the current session:

用 `/subagents` 检查当前 session 的 sub-agent 运行:

```text
/subagents list
/subagents log <id|#> [limit] [tools]
/subagents info <id|#>
```

> `/subagents info` shows run metadata...

`/subagents info` 显示运行元数据（状态、时间戳、session id、transcript 路径、清理）。用 `sessions_history` 做有边界的安全过滤回顾;需要完整原始 transcript 时查磁盘上的 transcript 路径。

### 线程绑定控制

> These commands work on channels that support persistent thread bindings.

这些命令在支持持久线程绑定的通道上工作:

```text
/focus <subagent-label|session-key|session-id|session-label>
/unfocus
/agents
/session idle <duration|off>
/session max-age <duration|off>
```

### 孵化行为

> Agents start background sub-agents with `sessions_spawn`...

Agent 用 `sessions_spawn` 启动后台 sub-agent。Sub-agent 完成后作为内部父 session 事件返回;父 / 请求者 agent 决定是否需要面向用户的更新。

> Non-blocking, push-based completion:

非阻塞、push-based 完成:

- `sessions_spawn` 非阻塞;立即返回 run id。
- 完成时 sub-agent 向父 / 请求者 session 报告。
- 需要子结果的 agent 轮次应在孵化后调 `sessions_yield`,结束当前轮次让完成事件作为下一个模型可见消息到达。
- 完成是 push-based。孵化后**不要**在循环中轮询 `/subagents list`、`sessions_list`、`sessions_history`。
- 子输出是给请求者 agent 综合的报告 / 证据,不是用户指令文本,不能覆盖系统 / 开发者 / 用户策略。
- 完成时 OpenClaw 尽力关闭该 sub-agent session 打开的浏览器 tab / 进程。

> Completion delivery:

完成投递:

- OpenClaw 通过带稳定幂等 key 的 `agent` 轮次把完成交回请求者 session。
- 请求者运行仍活跃时,先尝试 wake/steer 该运行而不是开第二条回复路径。
- 活跃请求者不能被唤醒时,回退到带相同完成上下文的请求者 agent 移交。
- 成功父移交完成 sub-agent 投递,即使父决定不需要可见用户更新。
- 原生 sub-agent 不拿 message 工具。它们向父返回纯 assistant 文本;人类可见回复由父的正常投递策略管。

> Completion handoff metadata:

完成移交元数据:

- `Result` —— 子最新可见 `assistant` 回复文本。终端失败运行不复用已捕获回复文本。
- `Status` —— `completed; ready for parent review` / `failed` / `timed out` / `unknown`。
- 紧凑运行时 / token 统计。
- 审查指令、后续指导、最终更新指令。

> Modes and ACP runtime:

模式和 ACP 运行时:

- `--model` 和 `--thinking` 覆盖该次运行的默认值。
- 持久线程绑定 session 用 `sessions_spawn` 加 `thread: true` 和 `mode: "session"`。
- 请求者通道不支持线程绑定时用 `mode: "run"`。
- ACP harness session（Claude Code、Gemini CLI、OpenCode 等）用 `runtime: "acp"`。

## Context 模式

> Native sub-agents start isolated unless the caller explicitly asks to fork the current transcript.

原生 sub-agent 默认隔离启动,除非调用者显式请求 fork 当前 transcript。

| 模式       | 什么时候用                                                          | 行为                                          |
| ---------- | ------------------------------------------------------------------- | --------------------------------------------- |
| `isolated` | 新研究、独立实现、慢工具、或任何能在任务文本中说清的                | 创建干净子 transcript。默认值,token 用量低。 |
| `fork`     | 工作依赖当前对话、先前工具结果、或请求者 transcript 中的细微指令    | 分叉请求者 transcript 到子 session。          |

`fork` 谨慎用。它是上下文相关委派,不是写清晰任务 prompt 的替代品。

## 工具: `sessions_spawn`

> Starts a sub-agent run with `deliver: false` on the global `subagent` lane...

在全局 `subagent` 队列启动 sub-agent 运行（`deliver: false`）,然后跑 announce 步骤把 announce 回复发到请求者聊天通道。

> Availability depends on the caller's effective tool policy...

可用性取决于调用者的生效工具策略。`coding` 和 `full` profile 默认暴露 `sessions_spawn`。`messaging` profile 不暴露;需要委派的 agent 加 `tools.alsoAllow: ["sessions_spawn", "sessions_yield", "subagents"]` 或用 `tools.profile: "coding"`。

**默认值:**

- **Model:** 原生 sub-agent 继承调用者,除非设了 `agents.defaults.subagents.model`。
- **Thinking:** 继承调用者,除非设了 `agents.defaults.subagents.thinking`。
- **Run timeout:** `agents.defaults.subagents.runTimeoutSeconds`（默认 `0`,无超时）。
- **Task delivery:** 原生 sub-agent 在首条可见 `[Subagent Task]` 消息中收到委派任务。

### 委派 prompt 模式

> `agents.defaults.subagents.delegationMode` controls prompt guidance only...

`agents.defaults.subagents.delegationMode` 只控制 prompt 引导;不改工具策略也不强制委派。

- `suggest`（默认）:保留标准 prompt 提示用 sub-agent 处理更大或更慢的工作。
- `prefer`:告诉主 agent 保持响应性,把比直接回复更复杂的都通过 `sessions_spawn` 委派。

### 工具参数

- `task`（必填）—— sub-agent 的任务描述。
- `taskName` —— 可选稳定句柄,用于后续状态输出中识别特定子。
- `label` —— 可选人类可读标签。
- `agentId` —— 在 `subagents.allowAgents` 允许时孵化到另一个配置的 agent id。
- `cwd` —— 可选任务工作目录。
- `runtime` —— `acp` 只用于外部 ACP harness。
- `model` —— 覆盖 sub-agent 模型。
- `thinking` —— 覆盖思考级别。
- `thread` —— `true` 时请求该 sub-agent session 的通道线程绑定。
- `mode` —— `session` 需要 `thread: true`。
- `cleanup` —— `"delete"` 在 announce 后立即归档。
- `sandbox` —— `require` 在目标子运行时不沙箱化时拒绝孵化。
- `context` —— `fork` 分叉请求者 transcript 到子 session。

> `sessions_spawn` does not accept channel-delivery params...

[展开: 警告] `sessions_spawn` **不**接受通道投递参数。原生 sub-agent 向请求者报告其最新 assistant 轮次;外部投递留给父 / 请求者 agent。

## 工具: `sessions_yield`

> Ends the current model turn and waits for runtime events...

结束当前模型轮次,等待运行时事件（主要是 sub-agent 完成事件）作为下一条消息到达。孵化了子工作但在完成到达前不能给最终答案时用。

> `sessions_yield` is the waiting primitive. Do not replace it with polling loops...

`sessions_yield` 是等待原语。不要用 `subagents`、`sessions_list`、`sessions_history`、shell `sleep` 的轮询循环替代。

## 工具: `subagents`

> Lists spawned sub-agent runs owned by the requester session...

列出请求者 session 已孵化的 sub-agent 运行。范围是当前请求者;子只能看到自己控制的子。

用 `subagents` 做按需状态和调试。等完成事件用 `sessions_yield`。

## 线程绑定 session

> When thread bindings are enabled for a channel, a sub-agent can stay bound to a thread...

通道启用线程绑定时,sub-agent 可以绑到一个线程,后续该线程的用户消息继续路由到同一 sub-agent session。

### 支持线程的通道

任何有 session 绑定适配器的通道都能支持。内置适配器目前含 Discord 线程、Matrix 线程、Telegram 论坛话题、飞书当前对话绑定。用逐通道 `threadBindings` 配置键控制启用、超时、`spawnSessions`。

### 手动控制

| 命令               | 效果                                                     |
| ------------------ | -------------------------------------------------------- |
| `/focus <target>`  | 绑定当前线程到 sub-agent/session 目标                    |
| `/unfocus`         | 移除当前绑定线程的绑定                                   |
| `/agents`          | 列出活跃运行和绑定状态                                   |
| `/session idle`    | 检查 / 更新空闲自动解绑                                  |
| `/session max-age` | 检查 / 更新硬上限                                        |

### 白名单

- `agents.list[].subagents.allowAgents` —— 可通过显式 `agentId` 目标的配置 agent id 列表（`["*"]` 允许任何）。默认只有请求者 agent。
- `agents.defaults.subagents.allowAgents` —— 请求者 agent 没设时的默认目标白名单。
- `agents.defaults.subagents.requireAgentId` —— 阻止省略 `agentId` 的孵化调用。
- `agents.defaults.subagents.announceTimeoutMs` —— Gateway announce 投递尝试的逐调超时。

> If the requester session is sandboxed, `sessions_spawn` rejects targets that would run unsandboxed.

请求者 session 沙箱化时,`sessions_spawn` 拒绝会跑在非沙箱的目标。

### Discovery

用 `agents_list` 看 `sessions_spawn` 当前允许的 agent id。响应含每个 agent 的生效模型和嵌入式运行时元数据。

### 自动归档

- Sub-agent session 在 `agents.defaults.subagents.archiveAfterMinutes`（默认 `60`）后自动归档。
- 归档用 `sessions.delete` 并把 transcript 重命名为 `*.deleted.<timestamp>`。
- `cleanup: "delete"` 在 announce 后立即归档。
- 配置的运行超时**不**自动归档;只停运行。session 留到自动归档。
- 浏览器清理和归档清理分开：跟踪的浏览器 tab / 进程在运行结束时尽力关闭。

## 嵌套 sub-agent

> By default, sub-agents cannot spawn their own sub-agents (`maxSpawnDepth: 1`)...

默认 sub-agent 不能孵化自己的 sub-agent（`maxSpawnDepth: 1`）。设 `maxSpawnDepth: 2` 启用一层嵌套——**编排者模式**：main → 编排 sub-agent → 工人 sub-sub-agent。

```json5
{
  agents: {
    defaults: {
      subagents: {
        maxSpawnDepth: 2,
        maxChildrenPerAgent: 5,
        maxConcurrent: 8,
        runTimeoutSeconds: 900,
        announceTimeoutMs: 120000,
      },
    },
  },
}
```

### 深度层级

| 深度 | Session key 形状                             | 角色                 | 能孵化?                      |
| ---- | -------------------------------------------- | -------------------- | ---------------------------- |
| 0    | `agent:<id>:main`                            | 主 agent             | 总是                         |
| 1    | `agent:<id>:subagent:<uuid>`                 | Sub-agent / 编排者   | 仅 `maxSpawnDepth >= 2` 时   |
| 2    | `agent:<id>:subagent:<uuid>:subagent:<uuid>` | Sub-sub-agent / 工人 | 永不                         |

### Announce 链

结果沿链向上流:

1. 深度 2 工人完成 → announce 给父（深度 1 编排者）。
2. 深度 1 编排者收到 announce,综合结果,完成 → announce 给 main。
3. 主 agent 收到 announce,投递给用户。

每层只看到直接子代的 announce。

### 各深度工具策略

- 深度 1（编排者,`maxSpawnDepth >= 2`）:拿 `sessions_spawn`、`subagents`、`sessions_list`、`sessions_history`。
- 深度 1（叶子,`maxSpawnDepth == 1`）:无 session 工具。
- 深度 2（叶子工人）:无 session 工具,`sessions_spawn` 总是拒绝。

### 每 agent 孵化限制

每个 agent session（任何深度）最多 `maxChildrenPerAgent`（默认 `5`）个活跃子。防止单个编排者的失控扇出。

### 级联停止

停止深度 1 编排者自动停止其所有深度 2 子。主聊天中 `/stop` 停止所有深度 1 agent 并级联到它们的深度 2 子。

## 认证

> Sub-agent auth is resolved by agent id, not by session type...

Sub-agent 认证按 **agent id** 解析,不按 session 类型。auth store 从该 agent 的 `agentDir` 加载。主 agent 的 auth profile 作为**回退**合并;agent profile 冲突时覆盖主 profile。合并是加法性的。

## Announce

> Sub-agents report back via an announce step:

Sub-agent 通过 announce 步骤报告:

- Announce 步骤在 sub-agent session 内跑（不是请求者 session）。
- Sub-agent 回复精确 `ANNOUNCE_SKIP` 时不发布。
- 最新 assistant 文本是精确静默 token `NO_REPLY` / `no_reply` 时 announce 输出被抑制。

投递取决于请求者深度:

- 顶层请求者 session 用带外部投递的后续 `agent` 调用。
- 嵌套请求者 sub-agent session 收到内部后续注入（`deliver=false`）。

### Stats 行

Announce 载荷末尾含 stats 行:运行时长、token 用量、估计成本、`sessionKey`、`sessionId`、transcript 路径。

## 工具策略

> Sub-agents use the same profile and tool-policy pipeline as the parent...

Sub-agent 先用跟父或目标 agent 同样的 profile 和工具策略管线。之后 OpenClaw 应用 sub-agent 限制层。

无限制性 `tools.profile` 时,sub-agent 拿**除 message 工具、session 工具、系统工具外的所有工具**。

### 通过配置覆盖

```json5
{
  tools: {
    subagents: {
      tools: {
        deny: ["gateway", "cron"],
      },
    },
  },
}
```

`tools.subagents.tools.allow` 是最终 allow-only 过滤器。能收窄已解析工具集但不能加回被 `tools.profile` 移除的。

## 并发

Sub-agent 用专用进程内队列通道:

- **通道名:** `subagent`
- **并发:** `agents.defaults.subagents.maxConcurrent`（默认 `8`）

## 活性和恢复

OpenClaw 不把 `endedAt` 缺失当作 sub-agent 仍活的永久证明。超过陈旧运行窗口的未结束运行不再计为活跃 / 待定。

Gateway 重启后,陈旧未结束的恢复运行被修剪。标记了 `abortedLastRun: true` 的子 session 通过孤儿恢复流程可恢复。同一 sub-agent 子在快速重新卡住窗口内被反复接受恢复时,OpenClaw 持久化恢复墓碑并停止后续重启的自动恢复。

## 停止

主聊天发 `/stop` 中止请求者 session 并停止从它孵化的任何活跃 sub-agent 运行,级联到嵌套子。

## 限制

- Sub-agent announce 是**尽力而为**。Gateway 重启时待定 announce 工作丢失。
- Sub-agent 仍共享同一 Gateway 进程资源;`maxConcurrent` 当安全阀。
- `sessions_spawn` 总是非阻塞：立即返回 `{ status: "accepted", runId, childSessionKey }`。
- Sub-agent 上下文只注入 `AGENTS.md` 和 `TOOLS.md`。
- 最大嵌套深度 5（`maxSpawnDepth` 范围 1-5）。多数场景推荐深度 2。
- `maxChildrenPerAgent` 限制每 session 活跃子（默认 `5`,范围 `1-20`）。

## 相关

- [ACP agents](/tools/acp-agents)
- [Agent send](/tools/agent-send)
- [后台任务](/automation/tasks)
- [多 agent 沙箱工具](/tools/multi-agent-sandbox-tools)
