# Context engine

> A **context engine** controls how OpenClaw builds model context for each run: which messages to include, how to summarize older history, and how to manage context across subagent boundaries.

**上下文引擎（context engine）**控制 OpenClaw 每次运行怎么构建给模型的上下文：包含哪些消息、怎么概括较早的历史、怎么跨 sub-agent 边界管理上下文。

> OpenClaw ships with a built-in `legacy` engine and uses it by default - most users never need to change this. Install and select a plugin engine only when you want different assembly, compaction, or cross-session recall behavior.

OpenClaw 自带一个内置的 `legacy` 引擎，默认就用它 —— 大多数用户根本不用换。只有想要不同的组装、压缩或跨会话召回行为时才装并切换插件引擎。

---

> ## Quick start

## 快速上手

> [步骤 1: Check which engine is active]
>
> ```bash
> openclaw doctor
> # or inspect config directly:
> cat ~/.openclaw/openclaw.json | jq '.plugins.slots.contextEngine'
> ```

[步骤 1：查看当前激活的引擎]

```bash
openclaw doctor
# 或者直接看配置：
cat ~/.openclaw/openclaw.json | jq '.plugins.slots.contextEngine'
```

> [步骤 2: Install a plugin engine]
>
> Context engine plugins are installed like any other OpenClaw plugin.

[步骤 2：装一个插件引擎]

上下文引擎插件和 OpenClaw 其他插件一样安装。

> [标签页: From npm]
>
> ```bash
> openclaw plugins install @martian-engineering/lossless-claw
> ```

[标签页：从 npm 装]

```bash
openclaw plugins install @martian-engineering/lossless-claw
```

> [标签页: From a local path]
>
> ```bash
> openclaw plugins install -l ./my-context-engine
> ```

[标签页：从本地路径装]

```bash
openclaw plugins install -l ./my-context-engine
```

> [步骤 3: Enable and select the engine]
>
> ```json5
> // openclaw.json
> {
>   plugins: {
>     slots: {
>       contextEngine: "lossless-claw", // must match the plugin's registered engine id
>     },
>     entries: {
>       "lossless-claw": {
>         enabled: true,
>         // Plugin-specific config goes here (see the plugin's docs)
>       },
>     },
>   },
> }
> ```
>
> Restart the gateway after installing and configuring.

[步骤 3：启用并选中引擎]

```json5
// openclaw.json
{
  plugins: {
    slots: {
      contextEngine: "lossless-claw", // 必须和插件注册的引擎 id 一致
    },
    entries: {
      "lossless-claw": {
        enabled: true,
        // 插件专属配置（看插件文档）
      },
    },
  },
}
```

装好并配置完之后重启 Gateway。

> [步骤 4: Switch back to legacy (optional)]
>
> Set `contextEngine` to `"legacy"` (or remove the key entirely - `"legacy"` is the default).

[步骤 4：切回 legacy（可选）]

把 `contextEngine` 设回 `"legacy"`（或者整段 key 删掉 ——`"legacy"` 是默认值）。

---

> ## How it works

## 工作原理

> Every time OpenClaw runs a model prompt, the context engine participates at four lifecycle points:

OpenClaw 每次跑模型 prompt 时，上下文引擎在四个生命周期点参与：

> [展开: 1. Ingest]
>
> Called when a new message is added to the session. The engine can store or index the message in its own data store.

[展开：1. Ingest]

会话里加入新消息时调用。引擎可以把消息存到或索引到自己的数据存储里。

> [展开: 2. Assemble]
>
> Called before each model run. The engine returns an ordered set of messages (and an optional `systemPromptAddition`) that fit within the token budget.

[展开：2. Assemble]

每次模型运行之前调用。引擎返回一组按顺序排列、控制在 token 预算内的消息（和可选的 `systemPromptAddition`）。

> [展开: 3. Compact]
>
> Called when the context window is full, or when the user runs `/compact`. The engine summarizes older history to free space.

[展开：3. Compact]

上下文窗口满或用户跑 `/compact` 时调用。引擎概括较早的历史，腾出空间。

> [展开: 4. After turn]
>
> Called after a run completes. The engine can persist state, trigger background compaction, or update indexes.

[展开：4. After turn]

运行完成后调用。引擎可以持久化状态、触发后台压缩或更新索引。

> For the bundled non-ACP Codex harness, OpenClaw applies the same lifecycle by projecting assembled context into Codex developer instructions and the current turn prompt. Codex still owns its native thread history and native compactor.

对非 ACP 的内置 Codex harness，OpenClaw 也走同一套生命周期，做法是把组装好的上下文投射到 Codex 开发者指令和当前轮 prompt 里。Codex 仍然掌握自己的原生线程历史和原生压缩器。

> ### Subagent lifecycle (optional)

### Sub-agent 生命周期（可选）

> OpenClaw calls two optional subagent lifecycle hooks:

OpenClaw 调用两个可选的 sub-agent 生命周期钩子：

> <ParamField path="prepareSubagentSpawn" type="method">
>   Prepare shared context state before a child run starts. The hook receives parent/child session keys, `contextMode` (`isolated` or `fork`), available transcript ids/files, and optional TTL. If it returns a rollback handle, OpenClaw calls it when spawn fails after preparation succeeds.
> </ParamField>

- `prepareSubagentSpawn`（method）：子运行启动前准备共享上下文状态。钩子收到父 / 子 session key、`contextMode`（`isolated` 或 `fork`）、可用的 transcript id / 文件、可选 TTL。如果它返回一个 rollback 句柄，派生在准备成功后失败时 OpenClaw 会调它。

> <ParamField path="onSubagentEnded" type="method">
>   Clean up when a subagent session completes or is swept.
> </ParamField>

- `onSubagentEnded`（method）：sub-agent 会话完成或被清理时收尾。

> ### System prompt addition

### 系统提示词追加

> The `assemble` method can return a `systemPromptAddition` string. OpenClaw prepends this to the system prompt for the run. This lets engines inject dynamic recall guidance, retrieval instructions, or context-aware hints without requiring static workspace files.

`assemble` 方法可以返回一个 `systemPromptAddition` 字符串。OpenClaw 把它前置到该次运行的系统提示词里。这样引擎就能注入动态的召回指引、检索说明或上下文感知提示，不必依赖静态工作区文件。

---

> ## The legacy engine

## legacy 引擎

> The built-in `legacy` engine preserves OpenClaw's original behavior:
>
> * **Ingest**: no-op (the session manager handles message persistence directly).
> * **Assemble**: pass-through (the existing sanitize → validate → limit pipeline in the runtime handles context assembly).
> * **Compact**: delegates to the built-in summarization compaction, which creates a single summary of older messages and keeps recent messages intact.
> * **After turn**: no-op.

内置的 `legacy` 引擎保留 OpenClaw 原来的行为：

- **Ingest**：空操作（会话管理器自己处理消息持久化）。
- **Assemble**：透传（运行时已有的 sanitize → validate → limit 流水线负责上下文组装）。
- **Compact**：委托给内置摘要压缩，把旧消息合成一份摘要，保留最近消息不动。
- **After turn**：空操作。

> The legacy engine does not register tools or provide a `systemPromptAddition`.

legacy 引擎不注册工具，也不提供 `systemPromptAddition`。

> When no `plugins.slots.contextEngine` is set (or it's set to `"legacy"`), this engine is used automatically.

`plugins.slots.contextEngine` 没设置（或设为 `"legacy"`）时，自动使用这个引擎。

---

> ## Plugin engines

## 插件引擎

> A plugin can register a context engine using the plugin API:

插件可以通过插件 API 注册一个上下文引擎：

> ```ts
> import { buildMemorySystemPromptAddition } from "openclaw/plugin-sdk/core";
>
> export default function register(api) {
>   api.registerContextEngine("my-engine", (ctx) => ({
>     info: {
>       id: "my-engine",
>       name: "My Context Engine",
>       ownsCompaction: true,
>     },
>
>     async ingest({ sessionId, message, isHeartbeat }) {
>       // Store the message in your data store
>       return { ingested: true };
>     },
>
>     async assemble({ sessionId, messages, tokenBudget, availableTools, citationsMode }) {
>       // Return messages that fit the budget
>       return {
>         messages: buildContext(messages, tokenBudget),
>         estimatedTokens: countTokens(messages),
>         systemPromptAddition: buildMemorySystemPromptAddition({
>           availableTools: availableTools ?? new Set(),
>           citationsMode,
>         }),
>       };
>     },
>
>     async compact({ sessionId, force }) {
>       // Summarize older context
>       return { ok: true, compacted: true };
>     },
>   }));
> }
> ```

```ts
import { buildMemorySystemPromptAddition } from "openclaw/plugin-sdk/core";

export default function register(api) {
  api.registerContextEngine("my-engine", (ctx) => ({
    info: {
      id: "my-engine",
      name: "My Context Engine",
      ownsCompaction: true,
    },

    async ingest({ sessionId, message, isHeartbeat }) {
      // 把消息存到你的数据存储
      return { ingested: true };
    },

    async assemble({ sessionId, messages, tokenBudget, availableTools, citationsMode }) {
      // 返回贴合预算的消息
      return {
        messages: buildContext(messages, tokenBudget),
        estimatedTokens: countTokens(messages),
        systemPromptAddition: buildMemorySystemPromptAddition({
          availableTools: availableTools ?? new Set(),
          citationsMode,
        }),
      };
    },

    async compact({ sessionId, force }) {
      // 概括较早的上下文
      return { ok: true, compacted: true };
    },
  }));
}
```

> The factory `ctx` includes optional `config`, `agentDir`, and `workspaceDir` values so plugins can initialize per-agent or per-workspace state before the first lifecycle hook runs.

工厂参数 `ctx` 里带可选的 `config`、`agentDir`、`workspaceDir`，插件可以在第一个生命周期钩子运行前初始化 per-agent 或 per-workspace 的状态。

> Then enable it in config:
>
> ```json5
> {
>   plugins: {
>     slots: {
>       contextEngine: "my-engine",
>     },
>     entries: {
>       "my-engine": {
>         enabled: true,
>       },
>     },
>   },
> }
> ```

然后在配置里启用：

```json5
{
  plugins: {
    slots: {
      contextEngine: "my-engine",
    },
    entries: {
      "my-engine": {
        enabled: true,
      },
    },
  },
}
```

> ### The ContextEngine interface

### ContextEngine 接口

> Required members:

必需成员：

> | Member             | Kind     | Purpose                                                  |
> | ------------------ | -------- | -------------------------------------------------------- |
> | `info`             | Property | Engine id, name, version, and whether it owns compaction |
> | `ingest(params)`   | Method   | Store a single message                                   |
> | `assemble(params)` | Method   | Build context for a model run (returns `AssembleResult`) |
> | `compact(params)`  | Method   | Summarize/reduce context                                 |

| 成员               | 类型     | 用途                                                      |
| ------------------ | -------- | --------------------------------------------------------- |
| `info`             | 属性     | 引擎 id、名字、版本、是否拥有压缩                         |
| `ingest(params)`   | 方法     | 存一条消息                                                |
| `assemble(params)` | 方法     | 给模型运行构建上下文（返回 `AssembleResult`）             |
| `compact(params)`  | 方法     | 概括 / 缩减上下文                                         |

> `assemble` returns an `AssembleResult` with:

`assemble` 返回 `AssembleResult`：

> <ParamField path="messages" type="Message[]" required>
>   The ordered messages to send to the model.
> </ParamField>

- `messages`（`Message[]`，必填）：要发给模型的有序消息。

> <ParamField path="estimatedTokens" type="number" required>
>   The engine's estimate of total tokens in the assembled context. OpenClaw uses this for compaction threshold decisions and diagnostic reporting.
> </ParamField>

- `estimatedTokens`（`number`，必填）：引擎对组装后上下文总 token 数的估算。OpenClaw 用它来判断压缩阈值和报诊断信息。

> <ParamField path="systemPromptAddition" type="string">
>   Prepended to the system prompt.
> </ParamField>

- `systemPromptAddition`（`string`）：前置到系统提示词。

> <ParamField path="promptAuthority" type="&#x22;assembled&#x22; | &#x22;preassembly_may_overflow&#x22;">
>   Controls which token estimate the runner uses for preemptive overflow prechecks. Defaults to `"assembled"`, which means only the assembled prompt's estimate is checked - appropriate for engines that return a windowed, self-contained context. Set to `"preassembly_may_overflow"` only when your assembled view can hide overflow risk in the underlying transcript; the runner then takes the maximum of the assembled estimate and the pre-assembly (unwindowed) session-history estimate when deciding whether to preemptively compact. Either way, the messages you return are still what the model sees - `promptAuthority` only affects the precheck.
> </ParamField>

- `promptAuthority`（`"assembled" | "preassembly_may_overflow"`）：控制 runner 在做抢占式溢出预检时采用哪个 token 估算。默认 `"assembled"`，只检查组装后的 prompt 估算 —— 适合返回窗口内、自包含上下文的引擎。只有当组装后的视图可能掩盖底层 transcript 的溢出风险时才设 `"preassembly_may_overflow"`；这时 runner 在判断是否抢占式压缩时取组装估算和组装前（未窗口化）会话历史估算两者的最大值。无论哪种，模型看到的仍然是你返回的消息 ——`promptAuthority` 只影响预检。

> `compact` returns a `CompactResult`. When compaction rotates the active transcript, `result.sessionId` and `result.sessionFile` identify the successor session that the next retry or turn must use.

`compact` 返回 `CompactResult`。压缩轮换了活动 transcript 时，`result.sessionId` 和 `result.sessionFile` 指出后续重试或下一轮必须使用的继任会话。

> Optional members:

可选成员：

> | Member                         | Kind   | Purpose                                                                                                         |
> | ------------------------------ | ------ | --------------------------------------------------------------------------------------------------------------- |
> | `bootstrap(params)`            | Method | Initialize engine state for a session. Called once when the engine first sees a session (e.g., import history). |
> | `ingestBatch(params)`          | Method | Ingest a completed turn as a batch. Called after a run completes, with all messages from that turn at once.     |
> | `afterTurn(params)`            | Method | Post-run lifecycle work (persist state, trigger background compaction).                                         |
> | `prepareSubagentSpawn(params)` | Method | Set up shared state for a child session before it starts.                                                       |
> | `onSubagentEnded(params)`      | Method | Clean up after a subagent ends.                                                                                 |
> | `dispose()`                    | Method | Release resources. Called during gateway shutdown or plugin reload - not per-session.                           |

| 成员                           | 类型 | 用途                                                                                          |
| ------------------------------ | ---- | --------------------------------------------------------------------------------------------- |
| `bootstrap(params)`            | 方法 | 初始化某个会话的引擎状态。引擎第一次见到这个会话时调用一次（比如导入历史）。                  |
| `ingestBatch(params)`          | 方法 | 按批量摄入一个完成的轮次。运行完成后一次性带上该轮所有消息调用。                              |
| `afterTurn(params)`            | 方法 | 运行后生命周期工作（持久化状态、触发后台压缩）。                                              |
| `prepareSubagentSpawn(params)` | 方法 | 子会话启动前设置共享状态。                                                                    |
| `onSubagentEnded(params)`      | 方法 | sub-agent 结束后清理。                                                                        |
| `dispose()`                    | 方法 | 释放资源。Gateway 关停或插件重载时调用 —— 不是每会话调一次。                                  |

> ### ownsCompaction

### ownsCompaction

> `ownsCompaction` controls whether Pi's built-in in-attempt auto-compaction stays enabled for the run:

`ownsCompaction` 控制 Pi 内置的"尝试中"自动压缩对该次运行是否仍然启用：

> [展开: ownsCompaction: true]
>
> The engine owns compaction behavior. OpenClaw disables Pi's built-in auto-compaction for that run, and the engine's `compact()` implementation is responsible for `/compact`, overflow recovery compaction, and any proactive compaction it wants to do in `afterTurn()`. OpenClaw may still run the pre-prompt overflow safeguard; when it predicts the full transcript will overflow, the recovery path calls the active engine's `compact()` before submitting another prompt.

[展开：ownsCompaction: true]

引擎拥有压缩行为。OpenClaw 在该次运行里禁用 Pi 的内置自动压缩，引擎的 `compact()` 实现负责 `/compact`、溢出恢复压缩，以及它想在 `afterTurn()` 里做的任何主动压缩。OpenClaw 仍然可能跑提交前的溢出护栏；当它预判完整 transcript 会溢出时，恢复路径在再次提交 prompt 前会调用当前引擎的 `compact()`。

> [展开: ownsCompaction: false or unset]
>
> Pi's built-in auto-compaction may still run during prompt execution, but the active engine's `compact()` method is still called for `/compact` and overflow recovery.

[展开：ownsCompaction: false 或未设置]

Pi 的内置自动压缩在提交执行期间仍然可能跑，但 `/compact` 和溢出恢复仍然走当前引擎的 `compact()` 方法。

> <Warning>
>   `ownsCompaction: false` does **not** mean OpenClaw automatically falls back to the legacy engine's compaction path.
> </Warning>

> **警告**：`ownsCompaction: false` **并不意味着** OpenClaw 会自动回退到 legacy 引擎的压缩路径。

> That means there are two valid plugin patterns:

也就是说，有效的插件模式有两种：

> [标签页: Owning mode]
>
> Implement your own compaction algorithm and set `ownsCompaction: true`.

[标签页：Owning 模式]

实现你自己的压缩算法，设 `ownsCompaction: true`。

> [标签页: Delegating mode]
>
> Set `ownsCompaction: false` and have `compact()` call `delegateCompactionToRuntime(...)` from `openclaw/plugin-sdk/core` to use OpenClaw's built-in compaction behavior.

[标签页：Delegating 模式]

设 `ownsCompaction: false`，然后让 `compact()` 调 `openclaw/plugin-sdk/core` 的 `delegateCompactionToRuntime(...)`，复用 OpenClaw 内置的压缩行为。

> A no-op `compact()` is unsafe for an active non-owning engine because it disables the normal `/compact` and overflow-recovery compaction path for that engine slot.

对一个活跃的非 owning 引擎来说，空操作的 `compact()` 是不安全的 —— 它会让该引擎槽位下的常规 `/compact` 和溢出恢复压缩失效。

---

> ## Configuration reference

## 配置参考

> ```json5
> {
>   plugins: {
>     slots: {
>       // Select the active context engine. Default: "legacy".
>       // Set to a plugin id to use a plugin engine.
>       contextEngine: "legacy",
>     },
>   },
> }
> ```

```json5
{
  plugins: {
    slots: {
      // 选当前激活的上下文引擎，默认 "legacy"。
      // 想用插件引擎就写插件 id。
      contextEngine: "legacy",
    },
  },
}
```

> <Note>
>   The slot is exclusive at run time - only one registered context engine is resolved for a given run or compaction operation. Other enabled `kind: "context-engine"` plugins can still load and run their registration code; `plugins.slots.contextEngine` only selects which registered engine id OpenClaw resolves when it needs a context engine.
> </Note>

> **提示**：这个 slot 在运行时是独占的 —— 一次运行或压缩操作只解析一个已注册的上下文引擎。其他启用了 `kind: "context-engine"` 的插件仍然可以加载、跑它们的注册代码；`plugins.slots.contextEngine` 只决定 OpenClaw 需要上下文引擎时解析哪一个已注册的引擎 id。

> <Note>
>   **Plugin uninstall:** when you uninstall the plugin currently selected as `plugins.slots.contextEngine`, OpenClaw resets the slot back to the default (`legacy`). The same reset behavior applies to `plugins.slots.memory`. No manual config edit is required.
> </Note>

> **提示**：**卸载插件**时 —— 你卸载的是当前选定的 `plugins.slots.contextEngine`，OpenClaw 会把这个槽重置为默认（`legacy`）。`plugins.slots.memory` 也是同样的重置行为，不用手动改配置。

---

> ## Relationship to compaction and memory

## 与压缩和记忆的关系

> [展开: Compaction]
>
> Compaction is one responsibility of the context engine. The legacy engine delegates to OpenClaw's built-in summarization. Plugin engines can implement any compaction strategy (DAG summaries, vector retrieval, etc.).

[展开：压缩]

压缩是上下文引擎的一项职责。legacy 引擎把它委托给 OpenClaw 内置的摘要。插件引擎可以实现任何压缩策略（DAG 摘要、向量检索等）。

> [展开: Memory plugins]
>
> Memory plugins (`plugins.slots.memory`) are separate from context engines. Memory plugins provide search/retrieval; context engines control what the model sees. They can work together - a context engine might use memory plugin data during assembly. Plugin engines that want the active memory prompt path should prefer `buildMemorySystemPromptAddition(...)` from `openclaw/plugin-sdk/core`, which converts the active memory prompt sections into a ready-to-prepend `systemPromptAddition`. If an engine needs lower-level control, it can still pull raw lines from `openclaw/plugin-sdk/memory-host-core` via `buildActiveMemoryPromptSection(...)`.

[展开：记忆插件]

记忆插件（`plugins.slots.memory`）和上下文引擎是两回事。记忆插件提供搜索 / 检索；上下文引擎控制模型看到什么。它们可以协作 —— 上下文引擎可能在 assemble 时用记忆插件的数据。想走当前记忆提示词路径的插件引擎，优先用 `openclaw/plugin-sdk/core` 的 `buildMemorySystemPromptAddition(...)`，它把当前记忆提示词段转换成一个可直接前置的 `systemPromptAddition`。引擎需要更底层控制时，仍可通过 `openclaw/plugin-sdk/memory-host-core` 的 `buildActiveMemoryPromptSection(...)` 拿到原始行。

> [展开: Session pruning]
>
> Trimming old tool results in-memory still runs regardless of which context engine is active.

[展开：会话裁剪]

不论当前是哪个上下文引擎，内存里裁剪旧工具结果的逻辑都照样运行。

---

> ## Tips

## 小贴士

> * Use `openclaw doctor` to verify your engine is loading correctly.
> * If switching engines, existing sessions continue with their current history. The new engine takes over for future runs.
> * Engine errors are logged and surfaced in diagnostics. If a plugin engine fails to register or the selected engine id cannot be resolved, OpenClaw does not fall back automatically; runs fail until you fix the plugin or switch `plugins.slots.contextEngine` back to `"legacy"`.
> * For development, use `openclaw plugins install -l ./my-engine` to link a local plugin directory without copying.

- 用 `openclaw doctor` 验证引擎是否正常加载。
- 切换引擎时，已有会话继续沿用它们的当前历史。新引擎从下一次运行起接管。
- 引擎错误会写日志，并在诊断里显示。插件引擎注册失败、或选定的引擎 id 解析不出来时，OpenClaw 不会自动回退；运行会直接失败，直到你把插件修好，或者把 `plugins.slots.contextEngine` 切回 `"legacy"`。
- 开发时用 `openclaw plugins install -l ./my-engine` 链接本地插件目录，不用复制。

---

> ## Related

## 相关

> * [Compaction](/concepts/compaction) - summarizing long conversations
> * [Context](/concepts/context) - how context is built for agent turns
> * [Plugin Architecture](/plugins/architecture) - registering context engine plugins
> * [Plugin manifest](/plugins/manifest) - plugin manifest fields
> * [Plugins](/tools/plugin) - plugin overview

- [压缩](/concepts/compaction)：概括长对话
- [Context](/concepts/context)：agent 轮次的上下文怎么构建
- [插件架构](/plugins/architecture)：注册上下文引擎插件
- [插件清单](/plugins/manifest)：插件清单字段
- [插件](/tools/plugin)：插件总览
