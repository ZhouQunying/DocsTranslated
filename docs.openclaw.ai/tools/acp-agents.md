# ACP agents

## 架构精读

> 跳过不影响阅读翻译正文。

### 为什么 OpenClaw 需要"再来一条通道"跑外部 harness？

一个 agent 框架做两件完全不同的事：自己跑模型（内嵌运行时）、或者让外部 CLI 工具跑模型再把结果接回来（外挂运行时）。这跟 Docker 的 build-in executor 和 BuildKit 的分离构建器是一个道理——前者简单但受限,后者复杂但能接任何后端。

ACP 就是那个分离层。OpenClaw 负责路由、权限、投递、绑定、后台任务跟踪;harness（Claude Code / Codex / Gemini CLI）负责自己的认证、模型目录、文件系统行为。两边通过 ACP 协议交换消息,互不侵入。

session 绑定模型是最巧妙的设计。三个轴完全独立：聊天表面（Discord 频道 / Telegram 话题）、ACP session（harness 运行时状态）、工作区（文件系统位置）。你可以把同一个 Codex session 从笔记本切到手机——只要换聊天表面,session 和工作区不变。

安全边界上做了明确选择：ACP 跑在宿主上,不进沙箱。因为外部 harness 本身就有自己的权限系统（Claude Code 有 permission mode、Codex 有 approval policy）,再包一层沙箱反而制造兼容问题。但代价是：沙箱化的 session 不能启动 ACP——这是有意的隔离。

---

> Agent Client Protocol (ACP) sessions let OpenClaw run external coding harnesses...

[Agent Client Protocol (ACP)](https://agentclientprotocol.com/) session 让 OpenClaw 通过 ACP 后端插件运行外部编码 harness（如 Claude Code、Cursor、Copilot、Droid、OpenClaw ACP、OpenCode、Gemini CLI 等受支持的 ACPX harness）。

每次 ACP session 启动都作为[后台任务](/automation/tasks)跟踪。

> Note: ACP is the external-harness path, not the default Codex path...

[展开: 注意] **ACP 是外挂 harness 路径,不是默认 Codex 路径。** 原生 Codex app-server 插件负责 `/codex ...` 控制和 agent 轮次的默认 `openai/gpt-*` 嵌入运行时;ACP 负责 `/acp ...` 控制和 `sessions_spawn({ runtime: "acp" })` session。

想让 Codex 或 Claude Code 作为外部 MCP 客户端直接连到已有 OpenClaw 通道对话时,用 [`openclaw mcp serve`](/cli/mcp) 而非 ACP。

## 哪个页面适合我？

> Which page do I want?

| 你想...                                                           | 看这个                                | 备注                                                                                                        |
| ----------------------------------------------------------------- | ------------------------------------- | ----------------------------------------------------------------------------------------------------------- |
| 在当前对话绑定或控制 Codex                                        | `/codex bind`、`/codex threads`       | `codex` 插件启用时的原生 Codex app-server 路径;含绑定聊天回复、图片转发、模型 / 权限、停止和引导控制。ACP 是显式回退 |
| 通过 OpenClaw 跑 Claude Code、Gemini CLI、显式 Codex ACP 或其他外挂 harness | 本页                                  | 聊天绑定 session、`/acp spawn`、`sessions_spawn({ runtime: "acp" })`、后台任务、运行时控制                  |
| 把 OpenClaw Gateway session 暴露为 ACP 服务器给编辑器或客户端     | [`openclaw acp`](/cli/acp)            | 桥接模式。IDE / 客户端通过 stdio/WebSocket 跟 OpenClaw 对话                                                |
| 复用本地 AI CLI 作为纯文本回退模型                                | [CLI Backends](/gateway/cli-backends) | 非 ACP。无 OpenClaw 工具、无 ACP 控制、无 harness 运行时                                                   |

## 开箱即用？

> Does this work out of the box?

安装官方 ACP 运行时插件后即可:

```bash
openclaw plugins install @openclaw/acpx
openclaw config set plugins.entries.acpx.enabled true
```

> Source checkouts can use the local `extensions/acpx` workspace plugin...

源码 checkout 可以在 `pnpm install` 后用本地 `extensions/acpx` 工作区插件。跑 `/acp doctor` 做就绪检查。

> OpenClaw only teaches agents about ACP spawning when ACP is truly usable...

OpenClaw 只在 ACP **真正可用**时才教 agent 关于 ACP 启动的事：ACP 必须启用、dispatch 不能被禁用、当前 session 不能被沙箱阻止、运行时后端必须已加载。条件不满足时,ACP 插件技能和 `sessions_spawn` ACP 引导保持隐藏,agent 不会建议不可用的后端。

### 首次运行注意事项

> First-run gotchas

- `plugins.allow` 设了时是限制性插件白名单,**必须**含 `acpx`;否则已安装的 ACP 后端被阻止,`/acp doctor` 报告白名单缺失。
- Codex ACP 适配器跟 `acpx` 插件一起暂存,可能时在本地启动。
- Codex ACP 用隔离的 `CODEX_HOME` 运行;OpenClaw 从宿主 Codex 配置复制受信项目条目和安全的模型 / provider 路由配置,认证、通知、钩子留在宿主配置。
- 其他目标 harness 适配器首次使用时可能按需用 `npx` 获取。
- 目标 harness 的 vendor 认证仍须在宿主上存在。
- 宿主无 npm 或网络时,首次适配器获取失败,需预热缓存或用其他方式安装。

### 运行时前置条件

> Runtime prerequisites

ACP 启动真实外部 harness 进程。OpenClaw 负责路由、后台任务状态、投递、绑定、策略;harness 负责其 provider 登录、模型目录、文件系统行为、原生工具。

怪 OpenClaw 之前先验证:

- `/acp doctor` 报告已启用、健康的后端。
- 目标 id 在 `acp.allowedAgents`（设了白名单时）中被允许。
- harness 命令能在 Gateway 宿主启动。
- 目标 harness 的 provider 认证存在（`claude`、`codex`、`gemini`、`opencode`、`droid` 等）。
- 选中模型在该 harness 中存在——模型 id 不跨 harness 通用。
- 请求的 `cwd` 存在且可访问,或省略让后端用默认。
- 权限模式匹配工作。非交互 session 不能点原生权限弹窗,所以写 / 执行密集的编码运行通常需要能无头继续的 ACPX 权限 profile。

> OpenClaw plugin tools and built-in OpenClaw tools are not exposed to ACP harnesses by default...

OpenClaw 插件工具和内置工具默认**不**暴露给 ACP harness。只有 harness 应该直接调那些工具时才在 [ACP agents - setup](/tools/acp-agents-setup) 启用显式 MCP 桥接。

## 受支持的 harness 目标

> Supported harness targets

`acpx` 后端下,用这些 harness id 作为 `/acp spawn <id>` 或 `sessions_spawn({ runtime: "acp", agentId: "<id>" })` 目标:

| Harness id | 典型后端                               | 备注                                                                    |
| ---------- | -------------------------------------- | ----------------------------------------------------------------------- |
| `claude`   | Claude Code ACP 适配器                 | 需宿主上 Claude Code 认证。                                            |
| `codex`    | Codex ACP 适配器                       | 仅原生 `/codex` 不可用或显式请求 ACP 时的回退。                        |
| `copilot`  | GitHub Copilot ACP 适配器              | 需 Copilot CLI / 运行时认证。                                          |
| `cursor`   | Cursor CLI ACP（`cursor-agent acp`）   | 本地安装暴露不同 ACP 入口时可覆盖 acpx 命令。                         |
| `droid`    | Factory Droid CLI                      | 需 Factory/Droid 认证或 harness 环境中的 `FACTORY_API_KEY`。           |
| `gemini`   | Gemini CLI ACP 适配器                  | 需 Gemini CLI 认证或 API key 设置。                                    |
| `iflow`    | iFlow CLI                              | 适配器可用性和模型控制取决于已安装 CLI。                               |
| `kilocode` | Kilo Code CLI                          | 适配器可用性和模型控制取决于已安装 CLI。                               |
| `kimi`     | Kimi/Moonshot CLI                      | 需宿主上 Kimi/Moonshot 认证。                                          |
| `kiro`     | Kiro CLI                               | 适配器可用性和模型控制取决于已安装 CLI。                               |
| `opencode` | OpenCode ACP 适配器                    | 需 OpenCode CLI / provider 认证。                                      |
| `openclaw` | 通过 `openclaw acp` 的 OpenClaw Gateway 桥接 | 让 ACP 感知的 harness 回调 OpenClaw Gateway session。                  |
| `qwen`     | Qwen Code / Qwen CLI                  | 需宿主上 Qwen 兼容认证。                                              |

> Custom acpx agent aliases can be configured...

自定义 acpx agent 别名可以在 acpx 本身配,但 OpenClaw 策略仍在 dispatch 前检查 `acp.allowedAgents` 和 `agents.list[].runtime.acp.agent` 映射。

## 运营者手册

> Operator runbook

从聊天里的快速 `/acp` 流程:

1. **启动:** `/acp spawn claude --bind here`、`/acp spawn gemini --mode persistent --thread auto`、或显式 `/acp spawn codex --bind here`。
2. **工作:** 在绑定的对话或线程中继续（或显式指定 session key）。
3. **检查状态:** `/acp status`
4. **调优:** `/acp model <provider/model>`、`/acp permissions <profile>`、`/acp timeout <seconds>`。
5. **引导:** 不替换上下文：`/acp steer tighten logging and continue`。
6. **停止:** `/acp cancel`（当前轮次）或 `/acp close`（session + 绑定）。

### 生命周期细节

> Lifecycle details

- 启动创建或恢复 ACP 运行时 session,在 OpenClaw session store 记录 ACP 元数据,父持有时可创建后台任务。
- 父持有的 ACP session 即使运行时 session 是持久的也视为后台工作;完成和跨面投递走父任务通知器而非普通用户聊天 session。
- 任务维护关闭终态或孤儿的父持有的一次性 ACP session。持久 ACP session 在活跃对话绑定存在时保留;无活跃绑定的失效持久 session 被关闭以防在任务完成后被静默恢复。
- 绑定的后续消息直接到 ACP session,直到绑定被关闭、取消聚焦、重置、或过期。
- Gateway 命令保持本地。`/acp ...`、`/status`、`/unfocus` 永远不作为普通 prompt 文本发到绑定的 ACP harness。
- `cancel` 在后端支持取消时中止活跃轮次;不删绑定或 session 元数据。
- `close` 从 OpenClaw 角度结束 ACP session 并移除绑定。harness 如果支持恢复可能仍保留上游历史。
- acpx 插件在 `close` 后清理 OpenClaw 持有的包装器和适配器进程树,Gateway 启动时收割失效的 ACPX 孤儿进程。
- 空闲运行时 worker 在 `acp.runtime.ttlMinutes` 后有资格被清理;已存储的 session 元数据仍可供 `/acp sessions` 查看。

### 原生 Codex 路由规则

> Native Codex routing rules

应路由到**原生 Codex 插件**（启用时）的自然语言触发:

- "Bind this Discord channel to Codex."
- "Attach this chat to Codex thread `<id>`."
- "Show Codex threads, then bind this one."

> Native Codex conversation binding is the default chat-control path...

原生 Codex 对话绑定是默认聊天控制路径。OpenClaw 动态工具仍通过 OpenClaw 执行,Codex 原生工具（如 shell/apply-patch）在 Codex 内执行。对于 Codex 原生工具事件,OpenClaw 注入每轮原生钩子中继让插件钩子能阻断 `before_tool_call`、观察 `after_tool_call`、把 Codex `PermissionRequest` 事件路由通过 OpenClaw 审批。Codex `Stop` 钩子中继到 OpenClaw `before_agent_finalize`,插件可在 Codex 最终回答前请求再来一轮模型。中继保持保守：不改变 Codex 原生工具参数也不重写 Codex 线程记录。只有想要 ACP 运行时 / session 模型时才用显式 ACP。嵌入式 Codex 支持边界见 [Codex harness v1 support contract](/plugins/codex-harness-runtime#v1-support-contract)。

### ACP vs sub-agent

> ACP versus sub-agents

想要外挂 harness 运行时用 ACP。`codex` 插件启用时想要 Codex 对话绑定 / 控制用**原生 Codex app-server**。想要 OpenClaw 原生委派运行用 **sub-agent**。

| 方面          | ACP session                           | Sub-agent 运行                     |
| ------------- | ------------------------------------- | ---------------------------------- |
| 运行时        | ACP 后端插件（如 acpx）              | OpenClaw 原生 sub-agent 运行时     |
| Session key   | `agent:<agentId>:acp:<uuid>`          | `agent:<agentId>:subagent:<uuid>`  |
| 主命令        | `/acp ...`                            | `/subagents ...`                   |
| 启动工具      | `sessions_spawn` 加 `runtime:"acp"`   | `sessions_spawn`（默认运行时）     |

另见 [Sub-agents](/tools/subagents)。

### ACP 怎么跑 Claude Code

> How ACP runs Claude Code

ACP 下 Claude Code 的栈:

1. OpenClaw ACP session 控制面。
2. 官方 `@openclaw/acpx` 运行时插件。
3. Claude ACP 适配器。
4. Claude 侧运行时 / session 机制。

ACP Claude 是带 ACP 控制、session 恢复、后台任务跟踪、可选对话 / 线程绑定的 **harness session**。

### ACP vs CLI 后端

> CLI backends are separate text-only local fallback runtimes...

CLI 后端是独立的纯文本本地回退运行时——见 [CLI Backends](/gateway/cli-backends)。

运营者实用规则:

- **想要 `/acp spawn`、可绑定 session、运行时控制、或持久 harness 工作？** 用 ACP。
- **想要简单的本地文本回退？** 用 CLI 后端。

## 绑定 session

> Bound sessions

### 心智模型

> Mental model

- **聊天表面** —— 人们继续对话的地方（Discord 频道、Telegram 话题、iMessage 聊天）。
- **ACP session** —— OpenClaw 路由到的持久 Codex/Claude/Gemini 运行时状态。
- **子线程 / 话题** —— 仅 `--thread ...` 创建的可选额外消息表面。
- **运行时工作区** —— harness 运行的文件系统位置（`cwd`、仓库 checkout、后端工作区）。独立于聊天表面。

### 当前对话绑定

> Current-conversation binds

`/acp spawn <harness> --bind here` 把当前对话钉到已启动的 ACP session——无子线程,同一聊天表面。OpenClaw 继续管传输、认证、安全、投递。该对话后续消息路由到同一 session;`/new` 和 `/reset` 原地重置 session;`/acp close` 移除绑定。

示例:

```text
/codex bind                                              # 原生 Codex 绑定,路由后续消息到这里
/codex model gpt-5.4                                     # 调优绑定的原生 Codex 线程
/codex stop                                              # 控制活跃的原生 Codex 轮次
/acp spawn codex --bind here                             # Codex 的显式 ACP 回退
/acp spawn codex --thread auto                           # 可能创建子线程/话题并绑定
/acp spawn codex --bind here --cwd /workspace/repo       # 同聊天绑定,Codex 在 /workspace/repo 运行
```

> Binding rules and exclusivity

绑定规则和排他性:

- `--bind here` 和 `--thread ...` 互斥。
- `--bind here` 只在支持当前对话绑定的通道上工作;否则 OpenClaw 返回明确的不支持消息。绑定跨 gateway 重启持久。
- Discord 上,`spawnSessions` 门控 `--thread auto|here` 的子线程创建——不影响 `--bind here`。
- 不带 `--cwd` 启动到不同 ACP agent 时,OpenClaw 默认继承**目标 agent** 的工作区。继承路径不存在（`ENOENT`/`ENOTDIR`）回退到后端默认;其他访问错误（如 `EACCES`）作为启动错误暴露。
- Gateway 管理命令在绑定对话中保持本地——`/acp ...` 命令由 OpenClaw 处理,即使普通后续文本路由到绑定的 ACP session;通道启用命令处理时 `/status` 和 `/unfocus` 也保持本地。

### 线程绑定 session

> Thread-bound sessions

通道适配器启用线程绑定时:

- OpenClaw 把线程绑定到目标 ACP session。
- 该线程后续消息路由到绑定的 ACP session。
- ACP 输出投递回同一线程。
- 取消聚焦 / 关闭 / 归档 / 空闲超时或最大生命期到期移除绑定。
- `/acp close`、`/acp cancel`、`/acp status`、`/status`、`/unfocus` 是 Gateway 命令,不是给 ACP harness 的 prompt。

线程绑定 ACP 需要的功能标志:

- `acp.enabled=true`
- `acp.dispatch.enabled` 默认开（设 `false` 暂停自动 ACP 线程 dispatch;显式 `sessions_spawn({ runtime: "acp" })` 调用仍工作）。
- 通道适配器线程 session 启动已启用（默认 `true`）:
  - Discord: `channels.discord.threadBindings.spawnSessions=true`
  - Telegram: `channels.telegram.threadBindings.spawnSessions=true`

> Thread binding support is adapter-specific...

线程绑定支持是适配器特定的。活跃通道适配器不支持线程绑定时,OpenClaw 返回明确的不支持 / 不可用消息。

### 支持线程的通道

> Thread-supporting channels

- 任何暴露 session / 线程绑定能力的通道适配器。
- 当前内置支持：**Discord** 线程 / 频道、**Telegram** 话题（群组 / 超级群组中的论坛话题和私聊话题）。
- 插件通道可通过同一绑定接口添加支持。

## 持久通道绑定

> Persistent channel bindings

非临时工作流用顶层 `bindings[]` 条目配置持久 ACP 绑定。

### 绑定模型

> Binding model

- `type: "acp"` —— 标记持久 ACP 对话绑定。
- `match` —— 标识目标对话。各通道形式:
  - **Discord 频道 / 线程:** `match.channel="discord"` + `match.peer.id="<channelOrThreadId>"`
  - **Slack 频道 / DM:** `match.channel="slack"` + `match.peer.id="<channelId|...>"`。优选稳定 Slack id;频道绑定也匹配该频道线程内的回复。
  - **Telegram 论坛话题:** `match.channel="telegram"` + `match.peer.id="<chatId>:topic:<topicId>"`
  - **iMessage DM / 群组:** `match.channel="imessage"` + `match.peer.id="<handle|chat_id:*|...>"`。群组绑定优选 `chat_id:*`。
- `agentId` —— 持有该绑定的 OpenClaw agent id。
- `acp` —— 可选 ACP 覆盖。
- `label` —— 可选运营者可见标签。
- `cwd` —— 可选运行时工作目录。
- `backend` —— 可选后端覆盖。

### 每 agent 运行时默认

> Runtime defaults per agent

用 `agents.list[].runtime` 按 agent 定义一次 ACP 默认:

- `agents.list[].runtime.type="acp"`
- `agents.list[].runtime.acp.agent`（harness id,如 `codex` 或 `claude`）
- `agents.list[].runtime.acp.backend`
- `agents.list[].runtime.acp.mode`
- `agents.list[].runtime.acp.cwd`

**ACP 绑定 session 的覆盖优先级:**

1. `bindings[].acp.*`
2. `agents.list[].runtime.acp.*`
3. 全局 ACP 默认（如 `acp.backend`）

### 示例

```json5
{
  agents: {
    list: [
      {
        id: "codex",
        runtime: {
          type: "acp",
          acp: {
            agent: "codex",
            backend: "acpx",
            mode: "persistent",
            cwd: "/workspace/openclaw",
          },
        },
      },
      {
        id: "claude",
        runtime: {
          type: "acp",
          acp: { agent: "claude", backend: "acpx", mode: "persistent" },
        },
      },
    ],
  },
  bindings: [
    {
      type: "acp",
      agentId: "codex",
      match: {
        channel: "discord",
        accountId: "default",
        peer: { kind: "channel", id: "222222222222222222" },
      },
      acp: { label: "codex-main" },
    },
    {
      type: "acp",
      agentId: "claude",
      match: {
        channel: "telegram",
        accountId: "default",
        peer: { kind: "group", id: "-1001234567890:topic:42" },
      },
      acp: { cwd: "/workspace/repo-b" },
    },
    {
      type: "route",
      agentId: "main",
      match: { channel: "discord", accountId: "default" },
    },
    {
      type: "route",
      agentId: "main",
      match: { channel: "telegram", accountId: "default" },
    },
  ],
  channels: {
    discord: {
      guilds: {
        "111111111111111111": {
          channels: {
            "222222222222222222": { requireMention: false },
          },
        },
      },
    },
    telegram: {
      groups: {
        "-1001234567890": {
          topics: { "42": { requireMention: false } },
        },
      },
    },
  },
}
```

### 行为

> Behavior

- OpenClaw 确保配置的 ACP session 使用前存在。
- 该通道或话题的消息路由到配置的 ACP session。
- 绑定对话中 `/new` 和 `/reset` 原地重置同一 ACP session key。
- 临时运行时绑定（如线程聚焦流创建的）在存在时仍生效。
- 跨 agent ACP 启动不带显式 `cwd` 时,OpenClaw 从 agent 配置继承目标 agent 工作区。
- 继承工作区路径不存在回退到后端默认 cwd;非缺失的访问失败作为启动错误暴露。

## 启动 ACP session

> Start ACP sessions

两种方式启动 ACP session:

### 通过 sessions_spawn

> From sessions_spawn

用 `runtime: "acp"` 从 agent 轮次或工具调用启动 ACP session。

```json
{
  "task": "Open the repo and summarize failing tests",
  "runtime": "acp",
  "agentId": "codex",
  "thread": true,
  "mode": "session"
}
```

> Note: `runtime` defaults to `subagent`...

[展开: 注意] `runtime` 默认为 `subagent`,所以 ACP session 要显式设 `runtime: "acp"`。省略 `agentId` 时 OpenClaw 在配了 `acp.defaultAgent` 时用它。`mode: "session"` 需要 `thread: true` 保持持久绑定对话。

### 通过 /acp 命令

> From /acp command

用 `/acp spawn` 做聊天中的显式运营者控制。

```text
/acp spawn codex --mode persistent --thread auto
/acp spawn codex --mode oneshot --thread off
/acp spawn codex --bind here
/acp spawn codex --thread here
```

关键标志:

- `--mode persistent|oneshot`
- `--bind here|off`
- `--thread auto|here|off`
- `--cwd <absolute-path>`
- `--label <name>`

见 [Slash commands](/tools/slash-commands)。

### `sessions_spawn` 参数

> sessions_spawn parameters

- `task`（必填）—— 发给 ACP session 的初始 prompt。
- `runtime` —— ACP session 必须为 `"acp"`。
- `agentId` —— ACP 目标 harness id。没设时回退到 `acp.defaultAgent`。
- `thread` —— 在支持的地方请求线程绑定流。
- `mode` —— `"run"` 一次性;`"session"` 持久。`thread: true` 时省略 `mode`,OpenClaw 可能按运行时路径默认持久。`mode: "session"` 需要 `thread: true`。
- `cwd` —— 请求的运行时工作目录（由后端 / 运行时策略验证）。省略时 ACP 启动继承目标 agent 工作区;继承路径不存在回退后端默认,真实访问错误返回。
- `label` —— 运营者可见标签,用于 session / banner 文本。
- `resumeSessionId` —— 恢复已有 ACP session 而非新建。agent 通过 `session/load` 重放对话历史。需要 `runtime: "acp"`。
- `streamTo` —— `"parent"` 把初始 ACP 运行进度摘要作为系统事件流回请求者 session。接受的响应含 `streamLogPath` 指向 session 维度的 JSONL 日志。父进度流默认显示 assistant 评论和 ACP 状态进度,除非 `streaming.progress.commentary=false`。Discord 在未配流模式时也默认父预览为进度模式。状态进度仍遵循 `acp.stream.tagVisibility`,`plan` 等标签除非显式启用否则保持隐藏。
- `model` —— 显式模型覆盖。Codex ACP 启动把 `openai/gpt-5.4` 等 OpenAI ref 规范化到 Codex ACP 启动配置;`openai/gpt-5.4/high` 等斜杠形式也设 Codex ACP reasoning effort。省略时用子 agent 模型默认;否则让 ACP harness 用其自身默认。其他 harness 须广告 ACP `models` 并支持 `session/set_model`;否则清晰失败而非静默回退。
- `thinking` —— 显式思考 / 推理 effort。Codex ACP 中 `minimal` 映射到低 effort,`low`/`medium`/`high`/`xhigh` 直接映射,`off` 不加 reasoning-effort 启动覆盖。省略时用子 agent 思考默认和选中模型的逐模型 `agents.defaults.models["provider/model"].params.thinking`。

> ACP `sessions_spawn` runs use `agents.defaults.subagents.runTimeoutSeconds`...

ACP `sessions_spawn` 运行用 `agents.defaults.subagents.runTimeoutSeconds` 做子轮次默认时限。工具不接受逐调超时覆盖。

## 启动绑定和线程模式

> Spawn bind and thread modes

### --bind here|off

| 模式   | 行为                                                     |
| ------ | -------------------------------------------------------- |
| `here` | 原地绑定当前活跃对话;无活跃对话时失败。                 |
| `off`  | 不创建当前对话绑定。                                     |

注意:

- `--bind here` 是运营者让通道或聊天变成 Codex 后端的最简路径。
- `--bind here` 不创建子线程。
- `--bind here` 只在暴露当前对话绑定支持的通道上可用。
- `--bind` 和 `--thread` 不能在同一 `/acp spawn` 调用中组合。

### --thread auto|here|off

| 模式   | 行为                                                                                            |
| ------ | ----------------------------------------------------------------------------------------------- |
| `auto` | 在活跃线程中：绑定该线程。线程外：在支持时创建 / 绑定子线程。                                  |
| `here` | 需要当前活跃线程;不在线程中时失败。                                                            |
| `off`  | 无绑定。Session 无绑定启动。                                                                   |

注意:

- 非线程绑定表面上默认行为等同 `off`。
- 线程绑定启动需要通道策略支持:
  - Discord: `channels.discord.threadBindings.spawnSessions=true`
  - Telegram: `channels.telegram.threadBindings.spawnSessions=true`
- 想钉当前对话不创建子线程时用 `--bind here`。

## 投递模型

> Delivery model

ACP session 可以是交互工作区或父持有的后台工作。投递路径取决于形态。

### 交互 ACP session

> Interactive ACP sessions

交互 session 意在持续在可见聊天表面对话:

- `/acp spawn ... --bind here` 把当前对话绑到 ACP session。
- `/acp spawn ... --thread ...` 把通道线程 / 话题绑到 ACP session。
- 持久配置的 `bindings[].type="acp"` 路由匹配对话到同一 ACP session。

绑定对话后续消息直接路由到 ACP session,ACP 输出投递回同一通道 / 线程 / 话题。

OpenClaw 发给 harness 的内容:

- 普通绑定后续作为 prompt 文本发送,harness / 后端支持时加附件。
- `/acp` 管理命令和本地 Gateway 命令在 ACP dispatch 前被拦截。
- 运行时生成的完成事件按目标物化。OpenClaw agent 得到内部运行时上下文信封;外部 ACP harness 得到含子结果和指令的纯 prompt。原始 `<<BEGIN_OPENCLAW_INTERNAL_CONTEXT>>` 信封永远不该发到外部 harness 或作为 ACP 用户 transcript 文本持久化。
- ACP transcript 条目用用户可见触发文本或纯完成 prompt。内部事件元数据尽量在 OpenClaw 中保持结构化,不视为用户创作的聊天内容。

### 父持有的一次性 ACP session

> Parent-owned one-shot ACP sessions

另一 agent 运行启动的一次性 ACP session 是后台子,类似 sub-agent:

- 父用 `sessions_spawn({ runtime: "acp", mode: "run" })` 请求工作。
- 子在自己的 ACP harness session 中运行。
- 子轮次跑在原生 sub-agent 启动使用的同一后台通道上,慢 ACP harness 不阻塞无关的主 session 工作。
- 完成通过任务完成 announce 路径报回。OpenClaw 在发给外部 harness 前把内部完成元数据转为纯 ACP prompt,harness 看不到 OpenClaw 专属运行时上下文标记。
- 父在面向用户回复有用时用普通 assistant 语气重写子结果。

**不要**把此路径当父子间的对等聊天。子已有回父的完成通道。

### sessions_send 和 A2A 投递

> sessions_send and A2A delivery

`sessions_send` 可以在启动后向另一 session 发消息。对普通对等 session,OpenClaw 在注入消息后用 agent-to-agent（A2A）后续路径:

- 等目标 session 回复。
- 可选让请求者和目标交换有界数量的后续轮次。
- 要求目标产生 announce 消息。
- 把 announce 投递到可见通道或线程。

该 A2A 路径是发送者需要可见后续时对等发送的回退。无关 session 能看到并向 ACP 目标发消息时（如宽泛的 `tools.sessions.visibility` 设置下）保持启用。

OpenClaw 只在请求者是自己父持有的一次性 ACP 子的父时跳过 A2A 后续。因为在任务完成之上再跑 A2A 会唤醒父带子结果、转发父回复回子、创建父 / 子回声环。此时 `sessions_send` 结果报告 `delivery.status="skipped"`——完成路径已对结果负责。

### 恢复已有 session

> Resume an existing session

用 `resumeSessionId` 继续之前的 ACP session 而非新建。agent 通过 `session/load` 重放对话历史,带着之前的完整上下文继续。

```json
{
  "task": "Continue where we left off - fix the remaining test failures",
  "runtime": "acp",
  "agentId": "codex",
  "resumeSessionId": "<previous-session-id>"
}
```

常见用例:

- 把 Codex session 从笔记本移交到手机——让 agent 接着之前的进度。
- 继续你在 CLI 中交互开始的编码 session,现在无头通过 agent。
- 接上被 gateway 重启或空闲超时中断的工作。

注意:

- `resumeSessionId` 只在 `runtime: "acp"` 时生效;默认 sub-agent 运行时忽略此 ACP 专属字段。
- `streamTo` 只在 `runtime: "acp"` 时生效;默认 sub-agent 运行时忽略此 ACP 专属字段。
- `resumeSessionId` 是宿主本地 ACP/harness 恢复 id,不是 OpenClaw 通道 session key;OpenClaw 仍在 dispatch 前检查 ACP 启动策略和目标 agent 策略,ACP 后端或 harness 负责加载该上游 id 的授权。
- `resumeSessionId` 恢复上游 ACP 对话历史;`thread` 和 `mode` 仍正常应用于你创建的新 OpenClaw session,所以 `mode: "session"` 仍需 `thread: true`。
- 目标 agent 须支持 `session/load`（Codex 和 Claude Code 支持）。
- session id 未找到时启动清晰失败——不静默回退到新 session。

### 部署后冒烟测试

> Post-deploy smoke test

Gateway 部署后跑端到端实时检查:

1. 验证目标宿主上部署的 gateway 版本和 commit。
2. 向活 agent 开临时 ACPX 桥接 session。
3. 让该 agent 调 `sessions_spawn` 带 `runtime: "acp"`、`agentId: "codex"`、`mode: "run"`、task `Reply with exactly LIVE-ACP-SPAWN-OK`。
4. 验证 `accepted=yes`、真实 `childSessionKey`、无验证错误。
5. 清理临时桥接 session。

门控保持 `mode: "run"` 并跳过 `streamTo: "parent"`——线程绑定 `mode: "session"` 和流中继路径是更丰富的独立集成验证。

## 沙箱兼容性

> Sandbox compatibility

ACP session 当前跑在宿主运行时,**不在** OpenClaw 沙箱内。

> Warning: Security boundary

[展开: 警告] **安全边界:**

- 外部 harness 按自己的 CLI 权限和选中 `cwd` 读写。
- OpenClaw 沙箱策略**不**包装 ACP harness 执行。
- OpenClaw 仍强制 ACP 功能门、允许的 agent、session 归属、通道绑定、Gateway 投递策略。
- 沙箱强制的 OpenClaw 原生工作用 `runtime: "subagent"`。

当前限制:

- 请求者 session 沙箱化时,`sessions_spawn({ runtime: "acp" })` 和 `/acp spawn` 都被阻止。
- `sessions_spawn` 加 `runtime: "acp"` 不支持 `sandbox: "require"`。

## Session 目标解析

> Session target resolution

多数 `/acp` action 接受可选 session 目标（`session-key`、`session-id`、或 `session-label`）。

**解析顺序:**

1. 显式目标参数（或 `/acp steer` 的 `--session`）
   - 先试 key
   - 再试 UUID 形状的 session id
   - 再试 label
2. 当前线程绑定（此对话 / 线程绑到 ACP session 时）。
3. 当前请求者 session 回退。

当前对话绑定和线程绑定都参与步骤 2。

无目标解析时 OpenClaw 返回清晰错误（`Unable to resolve session target: ...`）。

## ACP 控制命令

> ACP controls

| 命令                 | 作用                                              | 示例                                                          |
| -------------------- | ------------------------------------------------- | ------------------------------------------------------------- |
| `/acp spawn`         | 创建 ACP session;可选当前绑定或线程绑定。        | `/acp spawn codex --bind here --cwd /repo`                    |
| `/acp cancel`        | 取消目标 session 进行中的轮次。                   | `/acp cancel agent:codex:acp:<uuid>`                          |
| `/acp steer`         | 向运行中 session 发引导指令。                     | `/acp steer --session support inbox prioritize failing tests` |
| `/acp close`         | 关闭 session 并解除线程目标绑定。                 | `/acp close`                                                  |
| `/acp status`        | 显示后端、模式、状态、运行时选项、能力。          | `/acp status`                                                 |
| `/acp set-mode`      | 设目标 session 运行时模式。                       | `/acp set-mode plan`                                          |
| `/acp set`           | 通用运行时配置选项写入。                          | `/acp set model openai/gpt-5.4`                               |
| `/acp cwd`           | 设运行时工作目录覆盖。                            | `/acp cwd /Users/user/Projects/repo`                          |
| `/acp permissions`   | 设审批策略 profile。                              | `/acp permissions strict`                                     |
| `/acp timeout`       | 设运行时超时（秒）。                              | `/acp timeout 120`                                            |
| `/acp model`         | 设运行时模型覆盖。                                | `/acp model anthropic/claude-opus-4-6`                        |
| `/acp reset-options` | 移除 session 运行时选项覆盖。                     | `/acp reset-options`                                          |
| `/acp sessions`      | 从 store 列出最近 ACP session。                   | `/acp sessions`                                               |
| `/acp doctor`        | 后端健康、能力、可操作修复。                      | `/acp doctor`                                                 |
| `/acp install`       | 打印确定性安装和启用步骤。                        | `/acp install`                                                |

> `/acp status` shows the effective runtime options...

`/acp status` 显示生效运行时选项和运行时级 / 后端级 session 标识符。后端缺能力时不支持的控制错误清晰暴露。`/acp sessions` 读当前绑定或请求者 session 的 store;目标 token 通过 gateway session 发现解析,含自定义逐 agent `session.store` 根。

### 运行时选项映射

> Runtime options mapping

`/acp` 有便捷命令和通用 setter。等价操作:

| 命令                         | 映射到                               | 备注                                                                                                                                  |
| ---------------------------- | ------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------- |
| `/acp model <id>`            | 运行时配置 key `model`               | Codex ACP 中 OpenClaw 把 `openai/<model>` 规范化到适配器模型 id,斜杠推理后缀如 `openai/gpt-5.4/high` 映射到 `reasoning_effort`。     |
| `/acp set thinking <level>`  | 标准选项 `thinking`                  | OpenClaw 在有时发后端广告的等价名,优选 `thinking`、再 `effort`、`reasoning_effort`、或 `thought_level`。Codex ACP 适配器映射到 `reasoning_effort`。 |
| `/acp permissions <profile>` | 标准选项 `permissionProfile`         | OpenClaw 在有时发后端广告的等价名,如 `approval_policy`、`permission_profile`、`permissions`、或 `permission_mode`。                   |
| `/acp timeout <seconds>`     | 标准选项 `timeoutSeconds`            | OpenClaw 在有时发后端广告的等价名,如 `timeout` 或 `timeout_seconds`。                                                                |
| `/acp cwd <path>`            | 运行时 cwd 覆盖                      | 直接更新。                                                                                                                            |
| `/acp set <key> <value>`     | 通用                                 | `key=cwd` 用 cwd 覆盖路径。                                                                                                          |
| `/acp reset-options`         | 清除所有运行时覆盖                   | -                                                                                                                                     |

## acpx harness、插件设置和权限

> acpx harness, plugin setup, and permissions

acpx harness 配置（Claude Code / Codex / Gemini CLI 别名）、插件工具和 OpenClaw 工具 MCP 桥接、ACP 权限模式见 [ACP agents - setup](/tools/acp-agents-setup)。

## 故障排查

> Troubleshooting

| 症状                                                                    | 可能原因                                                                                     | 修复                                                                                                                      |
| ----------------------------------------------------------------------- | -------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------- |
| `ACP runtime backend is not configured`                                 | 后端插件缺失、禁用、或被 `plugins.allow` 阻止。                                             | 安装并启用后端插件,白名单含 `acpx`,再跑 `/acp doctor`。                                                                 |
| `ACP is disabled by policy (acp.enabled=false)`                         | ACP 全局禁用。                                                                               | 设 `acp.enabled=true`。                                                                                                   |
| `ACP dispatch is disabled by policy`                                    | 普通线程消息自动 dispatch 禁用。                                                             | 设 `acp.dispatch.enabled=true` 恢复自动线程路由;显式 `sessions_spawn` 调用仍工作。                                       |
| `ACP agent "<id>" is not allowed by policy`                             | Agent 不在白名单。                                                                           | 用允许的 `agentId` 或更新 `acp.allowedAgents`。                                                                           |
| `/acp doctor` 启动后立即报后端未就绪                                    | 后端插件缺失、禁用、被策略阻止、或配置的可执行文件不可用。                                   | 安装 / 启用后端插件,重跑 `/acp doctor`,保持不健康时 inspect 后端安装或策略错误。                                         |
| Harness 命令未找到                                                      | 适配器 CLI 未装、外部插件缺失、或非 Codex 适配器首次 `npx` 获取失败。                        | 跑 `/acp doctor`,在 Gateway 宿主安装 / 预热适配器,或显式配 acpx agent 命令。                                             |
| Harness 报模型未找到                                                    | 模型 id 对另一 provider/harness 有效但不对当前 ACP 目标。                                    | 用该 harness 列出的模型,在 harness 中配该模型,或省略覆盖。                                                               |
| Harness 报 vendor 认证错误                                              | OpenClaw 健康但目标 CLI/provider 未登录。                                                    | 在 Gateway 宿主环境登录或提供所需 provider key。                                                                          |
| `Unable to resolve session target: ...`                                 | 坏 key/id/label token。                                                                      | 跑 `/acp sessions`,复制精确 key/label,重试。                                                                             |
| `--bind here requires running /acp spawn inside an active conversation` | 无活跃可绑定对话时用了 `--bind here`。                                                       | 移到目标聊天 / 频道重试,或用无绑定启动。                                                                                 |
| `Conversation bindings are unavailable for <channel>.`                  | 适配器缺当前对话 ACP 绑定能力。                                                              | 用 `--thread ...`（支持时）、配顶层 `bindings[]`、或换到受支持通道。                                                      |
| `--thread here` 需在活跃线程中                                          | 线程外用了 `--thread here`。                                                                 | 移到目标线程或用 `--thread auto`/`off`。                                                                                  |
| `Only <user-id> can rebind this ...`                                    | 另一用户持有活跃绑定目标。                                                                   | 以持有者身份重绑或用不同对话 / 线程。                                                                                     |
| `Thread bindings are unavailable for <channel>.`                        | 适配器缺线程绑定能力。                                                                       | 用 `--thread off` 或移到受支持适配器 / 通道。                                                                             |
| `Sandboxed sessions cannot spawn ACP sessions ...`                      | ACP 运行时在宿主侧;请求者 session 沙箱化。                                                  | 沙箱 session 用 `runtime="subagent"`,或从非沙箱 session 跑 ACP 启动。                                                    |
| `sessions_spawn sandbox="require" is unsupported for runtime="acp"`     | ACP 运行时请求了 `sandbox="require"`。                                                       | 需沙箱时用 `runtime="subagent"`,或从非沙箱 session 用 ACP 加 `sandbox="inherit"`。                                       |
| `Cannot apply --model ... did not advertise model support`              | 目标 harness 不暴露通用 ACP 模型切换。                                                       | 用广告了 ACP `models`/`session/set_model` 的 harness、用 Codex ACP model ref、或在 harness 中直接配模型。                 |
| 绑定 session 缺 ACP 元数据                                             | 过期 / 已删的 ACP session 元数据。                                                           | 用 `/acp spawn` 重建,再重绑 / 聚焦线程。                                                                                 |
| `AcpRuntimeError: Permission prompt unavailable in non-interactive mode` | `permissionMode` 在非交互 ACP session 阻止写 / 执行。                                        | 设 `plugins.entries.acpx.config.permissionMode` 为 `approve-all` 并重启 gateway。见 [Permission configuration](/tools/acp-agents-setup#permission-configuration)。 |
| ACP session 早期失败输出少                                              | 权限弹窗被 `permissionMode`/`nonInteractivePermissions` 阻止。                               | 查 gateway 日志的 `AcpRuntimeError`。完全权限设 `permissionMode=approve-all`;优雅降级设 `nonInteractivePermissions=deny`。 |
| ACP session 完成工作后无限挂起                                          | Harness 进程完成但 ACP session 未报完成。                                                    | 更新 OpenClaw;当前 acpx 清理在关闭和 Gateway 启动时收割 OpenClaw 持有的过期包装器和适配器进程。                           |
| Harness 看到 `<<BEGIN_OPENCLAW_INTERNAL_CONTEXT>>`                      | 内部事件信封泄漏跨 ACP 边界。                                                                | 更新 OpenClaw 并重跑完成流;外部 harness 只应收到纯完成 prompt。                                                           |

> Note: `Command blocked by PreToolUse hook: Native hook relay unavailable`...

[展开: 注意] `Command blocked by PreToolUse hook: Native hook relay unavailable` 属于原生 Codex 钩子中继,不是 ACP/acpx。在绑定的 Codex 聊天中用 `/new` 或 `/reset` 开始新 session;如果一次有效之后下一个原生工具调用又出现,重启 Codex app-server 或 OpenClaw Gateway 而非重复 `/new`。见 [Codex harness troubleshooting](/plugins/codex-harness#troubleshooting)。

## 相关

> Related

- [ACP agents - setup](/tools/acp-agents-setup)
- [Agent send](/tools/agent-send)
- [CLI Backends](/gateway/cli-backends)
- [Codex harness](/plugins/codex-harness)
- [Codex harness runtime](/plugins/codex-harness-runtime)
- [Multi-agent sandbox tools](/tools/multi-agent-sandbox-tools)
- [`openclaw acp`（桥接模式）](/cli/acp)
- [Sub-agents](/tools/subagents)
