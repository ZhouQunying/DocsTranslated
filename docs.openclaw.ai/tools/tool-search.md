# Tool Search

> Tool Search is an experimental OpenClaw PI-agent feature. It gives PI agents one
> compact way to discover and call large tool catalogs. It is useful when the run
> has many available tools but the model is likely to need only a few of them.

Tool Search 是 OpenClaw PI agent 的实验性功能。它给 PI agent 提供一个紧凑的方式来发现和调用大型工具目录。当一次运行可用工具很多、但模型大概率只需要其中几个时,它特别有用。

> This page documents OpenClaw PI Tool Search. It is not the Codex-native tool
> search or dynamic-tools surface. Codex-native code mode, tool search, deferred
> dynamic tools, and nested tool calls are stable Codex harness surfaces and do
> not depend on `tools.toolSearch`.

这页讲的是 OpenClaw 的 PI Tool Search,**不是** Codex 原生的工具检索或动态工具接口。Codex 原生的 code 模式、工具检索、延迟动态工具、嵌套工具调用是 Codex harness 的稳定接口,不依赖 `tools.toolSearch`。

> When enabled for PI, the model receives one `tool_search_code` tool by default.
> That tool runs a short JavaScript body in an isolated Node subprocess with an
> `openclaw.tools` bridge:

为 PI 启用时,模型默认收到一个 `tool_search_code` 工具。这个工具在一个隔离的 Node 子进程里跑一段 JavaScript,带 `openclaw.tools` 桥:

```js
const hits = await openclaw.tools.search("create a GitHub issue");
const tool = await openclaw.tools.describe(hits[0].id);
return await openclaw.tools.call(tool.id, {
  title: "Crash on startup",
  body: "Steps to reproduce...",
});
```

> The catalog can include OpenClaw tools, plugin tools, MCP tools, and
> client-provided tools. The model does not see every full schema up front.
> Instead, it searches compact descriptors, describes one selected tool when it
> needs the exact schema, and calls that tool through OpenClaw.

目录里可以包含 OpenClaw 工具、插件工具、MCP 工具、客户端提供的工具。模型一开始**不会**看到每个工具的完整 schema。它先搜紧凑描述符,需要精确 schema 时再 describe 选中的那个工具,然后通过 OpenClaw 调它。

> Codex harness runs do not receive these experimental OpenClaw Tool Search
> controls. OpenClaw passes product capabilities to Codex as dynamic tools, and
> Codex owns the stable native code mode, native tool search, deferred dynamic
> tools, and nested tool calls.

Codex harness 运行**不会**收到这些 OpenClaw Tool Search 实验性控制。OpenClaw 把产品能力作为动态工具传给 Codex,稳定的原生 code 模式、原生工具检索、延迟动态工具、嵌套工具调用归 Codex 自己拥有。

## 一轮怎么跑

> At planning time the PI embedded runner builds the effective catalog for the
> run:

规划阶段,PI 嵌入式运行器为这次运行构建生效的工具目录:

> 1. Resolve the active tool policy for the agent, profile, sandbox, and session.
> 2. List eligible OpenClaw and plugin tools.
> 3. List eligible MCP tools through the session MCP runtime.
> 4. Add eligible client tools supplied for the current run.
> 5. Index compact descriptors for search.
> 6. Expose either the PI code bridge or the structured fallback tools to the
>    model.

1. 解析这个 agent、profile、沙箱、会话上的当前工具策略。
2. 列出合格的 OpenClaw 和插件工具。
3. 通过会话 MCP 运行时列出合格的 MCP 工具。
4. 加上为当前运行提供的合格客户端工具。
5. 给紧凑描述符建检索索引。
6. 把 PI code 桥 *或* 结构化回退工具暴露给模型。

> At execution time every real tool call returns to OpenClaw. The isolated Node
> runtime does not hold plugin implementations, MCP client objects, or secrets.
> `openclaw.tools.call(...)` crosses the bridge back into the Gateway, where the
> normal policy, approval, hook, logging, and result handling still apply.

执行阶段,每次真正的工具调用都回到 OpenClaw。隔离的 Node 运行时**不**持有插件实现、MCP 客户端对象或密钥。`openclaw.tools.call(...)` 跨过桥回到 Gateway,在那里走正常的策略、审批、钩子、日志、结果处理。

## 模式

> `tools.toolSearch` has two model-facing modes:
>
> - `code`: exposes `tool_search_code`, the default compact JavaScript bridge.
> - `tools`: exposes `tool_search`, `tool_describe`, and `tool_call` as plain
>   structured tools for providers that should not receive code.

`tools.toolSearch` 给模型暴露两种模式:

- `code`:暴露 `tool_search_code`,默认的紧凑 JavaScript 桥。
- `tools`:暴露 `tool_search`、`tool_describe`、`tool_call` 三个普通结构化工具,给"不应该收到代码"的 provider 用。

> Both modes use the same catalog and execution path. The only difference is the
> shape the model sees. If the current runtime cannot launch the isolated Node
> code-mode child process, the default `code` mode falls back to `tools` before
> catalog compaction.

两种模式用同一份目录和执行路径,唯一区别是模型看到的形态。当前运行时启动不了隔离 Node code 模式子进程时,默认的 `code` 模式在目录压缩之前回退到 `tools`。

> Both modes are experimental. Prefer direct tool exposure for small PI tool
> catalogs, and prefer the Codex-native stable surfaces for Codex harness runs.

两种模式都是实验性的。PI 工具目录小时优先直接暴露工具;Codex harness 运行优先用 Codex 原生的稳定接口。

> There is no separate source-selection config. When Tool Search is enabled, the
> catalog includes eligible OpenClaw, MCP, and client tools after normal policy
> filtering.

没有独立的"来源选择"配置。Tool Search 启用时,目录在正常策略过滤之后包含合格的 OpenClaw、MCP、客户端工具。

## 为什么要这个

> Large catalogs are useful but expensive. Sending every tool schema to the model
> makes the request larger, slows planning, and increases accidental tool
> selection.

大目录好用但贵。把每个工具 schema 都发给模型,请求更大、规划更慢、意外选错工具的概率更高。

> Tool Search changes the shape:
>
> - direct tools: the model sees every selected schema before the first token
> - Tool Search code mode: the model sees one compact code tool and a short API
>   contract
> - Tool Search tools mode: the model sees three compact structured fallback
>   tools
> - during the turn: the model loads only the tool schemas it actually needs

Tool Search 改变形态:

- 直接工具:模型在第一个 token 之前就看到每个选中的 schema。
- Tool Search code 模式:模型只看到一个紧凑的 code 工具和一份简短的 API 契约。
- Tool Search tools 模式:模型看到三个紧凑的结构化回退工具。
- 一轮进行中:模型只加载它实际需要的工具 schema。

> Direct tool exposure is still the right default for small catalogs. Tool Search
> is best when one run can see many tools, especially from MCP servers or
> client-provided app tools.

直接暴露工具对小目录仍然是对的默认。Tool Search 最适合"一次运行能看到很多工具"的情况,尤其是来自 MCP 服务器或客户端提供的 app 工具。

## API

> `openclaw.tools.search(query, options?)`
>
> Searches the effective catalog for the current run. Results are compact and safe
> to put back into prompt context.

`openclaw.tools.search(query, options?)`

在当前运行的生效目录里检索。结果紧凑,可以安全地放回 prompt 上下文。

```js
const hits = await openclaw.tools.search("calendar event", { limit: 5 });
```

> `openclaw.tools.describe(id)`
>
> Loads full metadata for one search result, including the exact input schema.

`openclaw.tools.describe(id)`

加载某个检索结果的完整元数据,含精确的输入 schema。

```js
const calendarCreate = await openclaw.tools.describe("mcp:calendar:create_event");
```

> `openclaw.tools.call(id, args)`
>
> Calls a selected tool through OpenClaw.

`openclaw.tools.call(id, args)`

通过 OpenClaw 调用选中的工具。

```js
await openclaw.tools.call(calendarCreate.id, {
  summary: "Planning",
  start: "2026-05-09T14:00:00Z",
});
```

> The structured fallback mode exposes the same operations as tools:
>
> - `tool_search`
> - `tool_describe`
> - `tool_call`

结构化回退模式把同样的操作暴露成工具:

- `tool_search`
- `tool_describe`
- `tool_call`

## 运行时边界

> The code bridge runs in a short-lived Node subprocess. The subprocess starts
> with Node permission mode enabled, an empty environment, no filesystem or
> network grants, and no child-process or worker grants. OpenClaw enforces a
> parent-process wall-clock timeout and kills the subprocess on timeout, including
> after async continuations.

code 桥跑在一个短生命周期的 Node 子进程里。子进程启动时开了 Node permission mode、空环境、不给文件系统和网络权限、也不给子进程或 worker 权限。OpenClaw 在父进程上强制墙钟超时,超时时杀掉子进程,包括异步延续之后。

> The runtime exposes only:
>
> - `console.log`, `console.warn`, and `console.error`
> - `openclaw.tools.search`
> - `openclaw.tools.describe`
> - `openclaw.tools.call`

运行时只暴露:

- `console.log`、`console.warn`、`console.error`
- `openclaw.tools.search`
- `openclaw.tools.describe`
- `openclaw.tools.call`

> Normal OpenClaw behavior still applies to final calls:
>
> - tool allow and deny policies
> - per-agent and per-sandbox tool restrictions
> - channel/runtime tool policy
> - approval hooks
> - plugin `before_tool_call` hooks
> - session identity, logs, and telemetry

最终调用仍然走 OpenClaw 的常规行为:

- 工具允许 / 拒绝策略
- 单 agent / 单沙箱的工具限制
- 通道 / 运行时的工具策略
- 审批钩子
- 插件的 `before_tool_call` 钩子
- 会话身份、日志、遥测

## 配置

> Enable Tool Search for PI runs with the default code bridge:

为 PI 运行启用 Tool Search,用默认 code 桥:

```bash
openclaw config set tools.toolSearch true
```

> Equivalent JSON:

等价的 JSON:

```json5
{
  tools: {
    toolSearch: true,
  },
}
```

> Use the structured fallback tools instead for PI runs:

PI 运行改用结构化回退工具:

```json5
{
  tools: {
    toolSearch: {
      mode: "tools",
    },
  },
}
```

> Tune code-mode timeout and search result limits:

调 code 模式超时和检索结果上限:

```json5
{
  tools: {
    toolSearch: {
      mode: "code",
      codeTimeoutMs: 10000,
      searchDefaultLimit: 8,
      maxSearchLimit: 20,
    },
  },
}
```

> Disable it:

关掉它:

```json5
{
  tools: {
    toolSearch: false,
  },
}
```

## Prompt 和遥测

> Tool Search records enough telemetry to compare it with direct tool exposure:
>
> - total serialized tool and prompt bytes sent to the harness
> - catalog size and source breakdown
> - search, describe, and call counts
> - final tool calls executed through OpenClaw
> - selected tool ids and sources

Tool Search 记录足够的遥测,用来跟直接暴露工具做对比:

- 发给 harness 的工具和 prompt 的总序列化字节
- 目录大小和来源分布
- search、describe、call 的计数
- 通过 OpenClaw 真正执行的最终工具调用
- 被选中的工具 id 和来源

> Session logs should make it possible to answer:
>
> - how many tool schemas the model saw up front
> - how many search and describe operations it performed
> - which final tool was called
> - whether the result came from OpenClaw, MCP, or a client tool

会话日志应该能回答:

- 模型一开始看到多少个工具 schema
- 它做了多少次 search 和 describe 操作
- 最终调了哪个工具
- 结果来自 OpenClaw、MCP,还是客户端工具

## 端到端验证

> The gateway E2E runner proves both paths with the PI harness:

gateway E2E 运行器在 PI harness 上验证两条路径:

```bash
node --import tsx scripts/tool-search-gateway-e2e.ts
```

> It creates a temporary fake plugin with a large tool catalog, starts the mock
> OpenAI provider, starts a Gateway once in direct mode and once with Tool Search
> enabled, then compares provider request payloads and session logs.

它创建一个带大目录的临时假插件,启动 mock OpenAI provider,Gateway 启动两次:一次直接模式、一次启用 Tool Search,然后对比 provider 请求载荷和会话日志。

> The regression proves:
>
> 1. Direct mode can call the fake plugin tool.
> 2. Tool Search can call the same fake plugin tool.
> 3. Direct mode exposes the fake plugin tool schemas directly to the provider.
> 4. Tool Search exposes only the compact bridge.
> 5. The Tool Search request payload is smaller for the large fake catalog.
> 6. Session logs show the expected tool-call counts and bridged call telemetry.

回归用例验证:

1. 直接模式能调假插件工具。
2. Tool Search 能调同一个假插件工具。
3. 直接模式把假插件工具 schema 直接暴露给 provider。
4. Tool Search 只暴露紧凑桥。
5. 大假目录下,Tool Search 的请求载荷更小。
6. 会话日志显示预期的工具调用计数和桥接调用遥测。

## 失败行为

> Tool Search should fail closed:
>
> - if a tool is not in the effective policy, search should not return it
> - if a selected tool becomes unavailable, `tool_call` should fail
> - if policy or approval blocks execution, the call result should report that
>   block instead of bypassing it
> - if the code bridge cannot create an isolated runtime, use `mode: "tools"` or
>   disable Tool Search for that deployment

Tool Search 应当默认拒绝:

- 工具不在生效策略里时,search 不应该返回它
- 选中的工具变得不可用时,`tool_call` 应当失败
- 策略或审批阻止执行时,调用结果应当报告阻止,**不**应当绕过
- code 桥建不出隔离运行时时,改用 `mode: "tools"`,或者在那个部署上关掉 Tool Search

## 相关

> - [Tools and plugins](/tools)
> - [Multi-agent sandbox and tools](/tools/multi-agent-sandbox-tools)
> - [Exec tool](/tools/exec)
> - [ACP agents setup](/tools/acp-agents-setup)
> - [Building plugins](/plugins/building-plugins)

- [工具和插件](/tools)
- [多 agent 沙箱和工具](/tools/multi-agent-sandbox-tools)
- [Exec tool](/tools/exec)
- [ACP agents 配置](/tools/acp-agents-setup)
- [构建插件](/plugins/building-plugins)
