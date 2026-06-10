# Thinking levels

## 架构精读

> 跳过不影响阅读翻译正文。

### 不是所有问题都需要"深度思考"——但怎么让用户控制？

"今天星期几"不需要推理链。"帮我设计一个分布式锁"需要。如果所有请求都用最高推理级别——慢、贵、有时反而更差（简单问题过度思考会hallucinate）。

Thinking levels 让用户（或 Agent 自己）按需调节推理深度。`/t low` = 快速回答，`/t max` = 全力推理。

### 有意思的设计：provider 映射层

不同模型 provider 对"推理级别"的实现完全不同——Claude 用 `thinking` 参数，OpenAI 用 `reasoning_effort`，有的模型根本不支持。

OpenClaw 在中间加了一层映射：用户说 `high`，系统查当前模型的 profile，翻译成那个 provider 能理解的参数。用户不需要知道底层用的是什么模型。

跟操作系统的设备驱动一个意思：应用只说"打印"，驱动层负责翻译成具体打印机能听懂的协议。

---

## 做什么

> - Inline directive in any inbound body: `/t <level>`, `/think:<level>`, or `/thinking <level>`.
> - Levels (aliases): `off | minimal | low | medium | high | xhigh | adaptive | max`
>   - minimal → "think"
>   - low → "think hard"
>   - medium → "think harder"
>   - high → "ultrathink" (max budget)
>   - xhigh → "ultrathink+" (GPT-5.2+ and Codex models, plus Anthropic Claude Opus 4.7 effort)
>   - adaptive → provider-managed adaptive thinking (supported for Claude 4.6 on Anthropic/Bedrock, Anthropic Claude Opus 4.7, and Google Gemini dynamic thinking)
>   - max → provider max reasoning (Anthropic Claude Opus 4.7; Ollama maps this to its highest native `think` effort)
>   - `x-high`, `x_high`, `extra-high`, `extra high`, and `extra_high` map to `xhigh`.
>   - `highest` maps to `high`.

- 任何入站消息里的内联指令:`/t <级别>`、`/think:<级别>`、或 `/thinking <级别>`。
- 级别(别名):`off | minimal | low | medium | high | xhigh | adaptive | max`
  - minimal → "think"
  - low → "think hard"
  - medium → "think harder"
  - high → "ultrathink"(预算上限)
  - xhigh → "ultrathink+"(GPT-5.2+ 和 Codex 模型,以及 Anthropic Claude Opus 4.7 的 effort)
  - adaptive → provider 管理的自适应思考(支持 Anthropic / Bedrock 上的 Claude 4.6、Anthropic Claude Opus 4.7、Google Gemini 的动态思考)
  - max → provider 最大推理(Anthropic Claude Opus 4.7;Ollama 上映射到它原生 `think` 的最高级别)
  - `x-high`、`x_high`、`extra-high`、`extra high`、`extra_high` 都映射到 `xhigh`。
  - `highest` 映射到 `high`。

> - Provider notes:
>   - Thinking menus and pickers are provider-profile driven. Provider plugins declare the exact level set for the selected model, including labels such as binary `on`.
>   - `adaptive`, `xhigh`, and `max` are only advertised for provider/model profiles that support them. Typed directives for unsupported levels are rejected with that model's valid options.
>   - Existing stored unsupported levels are remapped by provider profile rank. `adaptive` falls back to `medium` on non-adaptive models, while `xhigh` and `max` fall back to the largest supported non-off level for the selected model.
>   - Anthropic Claude 4.6 models default to `adaptive` when no explicit thinking level is set.
>   - Anthropic Claude Opus 4.7 does not default to adaptive thinking. Its API effort default remains provider-owned unless you explicitly set a thinking level.
>   - Anthropic Claude Opus 4.7 maps `/think xhigh` to adaptive thinking plus `output_config.effort: "xhigh"`, because `/think` is a thinking directive and `xhigh` is the Opus 4.7 effort setting.
>   - Anthropic Claude Opus 4.7 also exposes `/think max`; it maps to the same provider-owned max effort path.
>   - Direct DeepSeek V4 models expose `/think xhigh|max`; both map to DeepSeek `reasoning_effort: "max"` while lower non-off levels map to `high`.
>   - OpenRouter-routed DeepSeek V4 models expose `/think xhigh` and send OpenRouter-supported `reasoning_effort` values. Stored `max` overrides fall back to `xhigh`.
>   - Ollama thinking-capable models expose `/think low|medium|high|max`; `max` maps to native `think: "high"` because Ollama's native API accepts `low`, `medium`, and `high` effort strings.
>   - OpenAI GPT models map `/think` through model-specific Responses API effort support. `/think off` sends `reasoning.effort: "none"` only when the target model supports it; otherwise OpenClaw omits the disabled reasoning payload instead of sending an unsupported value.
>   - Custom OpenAI-compatible catalog entries can opt into `/think xhigh` by setting `models.providers.<provider>.models[].compat.supportedReasoningEfforts` to include `"xhigh"`. This uses the same compat metadata that maps outbound OpenAI reasoning effort payloads, so menus, session validation, agent CLI, and `llm-task` agree with transport behavior.
>   - Stale configured OpenRouter Hunter Alpha refs skip proxy reasoning injection because that retired route could return final answer text through reasoning fields.
>   - Google Gemini maps `/think adaptive` to Gemini's provider-owned dynamic thinking. Gemini 3 requests omit a fixed `thinkingLevel`, while Gemini 2.5 requests send `thinkingBudget: -1`; fixed levels still map to the closest Gemini `thinkingLevel` or budget for that model family.
>   - MiniMax (`minimax/*`) on the Anthropic-compatible streaming path defaults to `thinking: { type: "disabled" }` unless you explicitly set thinking in model params or request params. This avoids leaked `reasoning_content` deltas from MiniMax's non-native Anthropic stream format.
>   - Z.AI (`zai/*`) only supports binary thinking (`on`/`off`). Any non-`off` level is treated as `on` (mapped to `low`).
>   - Moonshot (`moonshot/*`) maps `/think off` to `thinking: { type: "disabled" }` and any non-`off` level to `thinking: { type: "enabled" }`. When thinking is enabled, Moonshot only accepts `tool_choice` `auto|none`; OpenClaw normalizes incompatible values to `auto`.

- Provider 说明:
  - 思考菜单和选择器由 provider profile 驱动。Provider 插件声明所选模型的具体级别集,包括二选一的 `on` 标签。
  - `adaptive`、`xhigh`、`max` 只对支持它们的 provider / 模型 profile 暴露。给不支持的级别打指令会被拒绝,并提示该模型的可选项。
  - 已存的不支持级别会按 provider profile 的层级重映射。`adaptive` 在非自适应模型上回退到 `medium`;`xhigh` 和 `max` 回退到所选模型支持的最大非 `off` 级别。
  - Anthropic Claude 4.6 模型在没显式设思考级别时默认 `adaptive`。
  - Anthropic Claude Opus 4.7 **不**默认自适应思考。它的 API effort 默认由 provider 管理,除非你显式设思考级别。
  - Anthropic Claude Opus 4.7 把 `/think xhigh` 映射到自适应思考加 `output_config.effort: "xhigh"`,因为 `/think` 是思考指令、`xhigh` 是 Opus 4.7 的 effort 设置。
  - Anthropic Claude Opus 4.7 还暴露 `/think max`,映射到同一条 provider 持有的 max effort 路径。
  - 直连 DeepSeek V4 模型暴露 `/think xhigh|max`;两个都映射到 DeepSeek 的 `reasoning_effort: "max"`,更低的非 off 级别映射到 `high`。
  - OpenRouter 转 DeepSeek V4 模型暴露 `/think xhigh`,发 OpenRouter 支持的 `reasoning_effort` 值。已存的 `max` 覆盖回退到 `xhigh`。
  - Ollama 支持思考的模型暴露 `/think low|medium|high|max`;`max` 映射到原生 `think: "high"`,因为 Ollama 原生 API 只接受 `low`、`medium`、`high` 三个 effort 字符串。
  - OpenAI GPT 模型按各模型在 Responses API 上的 effort 支持映射 `/think`。`/think off` 只在目标模型支持时发 `reasoning.effort: "none"`;否则 OpenClaw 直接省略关掉推理的载荷,而不是发不支持的值。
  - 自定义 OpenAI 兼容目录条目可以通过把 `models.providers.<provider>.models[].compat.supportedReasoningEfforts` 设成含 `"xhigh"` 来启用 `/think xhigh`。这用的是同一份 compat 元数据,跟出站 OpenAI 推理 effort 载荷映射一致,所以菜单、会话校验、agent CLI、`llm-task` 跟传输行为一致。
  - 过期的 OpenRouter Hunter Alpha 配置 ref 跳过代理推理注入,因为这条已退役的路径可能通过推理字段返回最终答案文本。
  - Google Gemini 把 `/think adaptive` 映射到 Gemini provider 持有的动态思考。Gemini 3 请求省略固定的 `thinkingLevel`,Gemini 2.5 请求发 `thinkingBudget: -1`;固定级别仍按该模型家族最接近的 Gemini `thinkingLevel` 或预算映射。
  - MiniMax(`minimax/*`)在 Anthropic 兼容流式路径上默认 `thinking: { type: "disabled" }`,除非你在模型参数或请求参数里显式设思考。这避免了 MiniMax 非原生 Anthropic 流式格式中泄漏的 `reasoning_content` 增量。
  - Z.AI(`zai/*`)只支持二选一思考(`on`/`off`)。任何非 `off` 级别都被当作 `on`(映射到 `low`)。
  - Moonshot(`moonshot/*`)把 `/think off` 映射到 `thinking: { type: "disabled" }`,把任何非 `off` 级别映射到 `thinking: { type: "enabled" }`。思考开启时,Moonshot 只接受 `tool_choice` 为 `auto|none`;OpenClaw 把不兼容的值归一化成 `auto`。

## 解析顺序

> 1. Inline directive on the message (applies only to that message).
> 2. Session override (set by sending a directive-only message).
> 3. Per-agent default (`agents.list[].thinkingDefault` in config).
> 4. Global default (`agents.defaults.thinkingDefault` in config).
> 5. Fallback: provider-declared default when available; otherwise reasoning-capable models resolve to `medium` or the nearest supported non-`off` level for that model, and non-reasoning models stay `off`.

1. 消息上的内联指令(只影响这条消息)。
2. 会话覆盖(发一条只含指令的消息来设)。
3. 单 agent 默认(配置里 `agents.list[].thinkingDefault`)。
4. 全局默认(配置里 `agents.defaults.thinkingDefault`)。
5. 回退:有 provider 声明的默认就用;否则有推理能力的模型解析到 `medium` 或该模型支持的最接近非 `off` 级别,没推理能力的模型保持 `off`。

## 设会话默认

> - Send a message that is **only** the directive (whitespace allowed), e.g. `/think:medium` or `/t high`.
> - That sticks for the current session (per-sender by default). Use `/think default` to clear the session override and inherit the configured/provider default; aliases include `inherit`, `clear`, `reset`, and `unpin`.
> - `/think off` stores an explicit off override. It disables thinking until you change or clear the session override.
> - Confirmation reply is sent (`Thinking level set to high.` / `Thinking disabled.`). If the level is invalid (e.g. `/thinking big`), the command is rejected with a hint and the session state is left unchanged.
> - Send `/think` (or `/think:`) with no argument to see the current thinking level.

- 发一条**只有**指令(允许空白)的消息,如 `/think:medium` 或 `/t high`。
- 它在当前会话里生效(默认按发送者粒度)。用 `/think default` 清掉会话覆盖、继承配置 / provider 默认;别名有 `inherit`、`clear`、`reset`、`unpin`。
- `/think off` 存一个显式 off 覆盖。在你改或清这个会话覆盖之前一直关思考。
- 会发确认回复(`Thinking level set to high.` / `Thinking disabled.`)。级别无效(如 `/thinking big`),命令被拒,带提示,会话状态不变。
- 不带参数发 `/think`(或 `/think:`)看当前思考级别。

## 按 agent 应用

> - **Embedded Pi**: the resolved level is passed to the in-process Pi agent runtime.
> - **Claude CLI backend**: non-off levels are passed to Claude Code as `--effort` when using `claude-cli`; see [CLI backends](/gateway/cli-backends).

- **内置 Pi**:解析出的级别传给进程内 Pi agent 运行时。
- **Claude CLI 后端**:用 `claude-cli` 时,非 off 级别作为 `--effort` 传给 Claude Code;见 [CLI 后端](/gateway/cli-backends)。

## 快速模式(/fast)

> - Levels: `on|off|default`.
> - Directive-only message toggles a session fast-mode override and replies `Fast mode enabled.` / `Fast mode disabled.`. Use `/fast default` to clear the session override and inherit the configured default; aliases include `inherit`, `clear`, `reset`, and `unpin`.
> - Send `/fast` (or `/fast status`) with no mode to see the current effective fast-mode state.
> - OpenClaw resolves fast mode in this order:
>   1. Inline/directive-only `/fast on|off` override (`/fast default` clears this layer)
>   2. Session override
>   3. Per-agent default (`agents.list[].fastModeDefault`)
>   4. Per-model config: `agents.defaults.models["<provider>/<model>"].params.fastMode`
>   5. Fallback: `off`
> - For `openai/*`, fast mode maps to OpenAI priority processing by sending `service_tier=priority` on supported Responses requests.
> - For `openai-codex/*`, fast mode sends the same `service_tier=priority` flag on Codex Responses. OpenClaw keeps one shared `/fast` toggle across both auth paths.
> - For direct public `anthropic/*` requests, including OAuth-authenticated traffic sent to `api.anthropic.com`, fast mode maps to Anthropic service tiers: `/fast on` sets `service_tier=auto`, `/fast off` sets `service_tier=standard_only`.
> - For `minimax/*` on the Anthropic-compatible path, `/fast on` (or `params.fastMode: true`) rewrites `MiniMax-M2.7` to `MiniMax-M2.7-highspeed`.
> - Explicit Anthropic `serviceTier` / `service_tier` model params override the fast-mode default when both are set. OpenClaw still skips Anthropic service-tier injection for non-Anthropic proxy base URLs.
> - `/status` shows `Fast` only when fast mode is enabled.

- 级别:`on|off|default`。
- 只含指令的消息切换会话级 fast 覆盖,回复 `Fast mode enabled.` / `Fast mode disabled.`。用 `/fast default` 清会话覆盖、继承配置默认;别名有 `inherit`、`clear`、`reset`、`unpin`。
- 不带模式发 `/fast`(或 `/fast status`)看当前生效的 fast 状态。
- OpenClaw 按这个顺序解析 fast:
  1. 内联 / 只含指令的 `/fast on|off` 覆盖(`/fast default` 清这一层)
  2. 会话覆盖
  3. 单 agent 默认(`agents.list[].fastModeDefault`)
  4. 单模型配置:`agents.defaults.models["<provider>/<model>"].params.fastMode`
  5. 回退:`off`
- 对 `openai/*`,fast 映射到 OpenAI 优先处理:在支持的 Responses 请求上发 `service_tier=priority`。
- 对 `openai-codex/*`,fast 在 Codex Responses 上发同样的 `service_tier=priority`。OpenClaw 让 `/fast` 在两条认证路径上共享同一个切换。
- 对直连公共 `anthropic/*` 请求(包括发到 `api.anthropic.com` 的 OAuth 认证流量),fast 映射到 Anthropic 服务等级:`/fast on` 设 `service_tier=auto`,`/fast off` 设 `service_tier=standard_only`。
- 对 Anthropic 兼容路径上的 `minimax/*`,`/fast on`(或 `params.fastMode: true`)把 `MiniMax-M2.7` 改写成 `MiniMax-M2.7-highspeed`。
- 同时设了显式 Anthropic `serviceTier` / `service_tier` 模型参数时,它们覆盖 fast 默认。非 Anthropic 代理 baseUrl 上仍跳过 Anthropic 服务等级注入。
- `/status` 只在 fast 开启时显示 `Fast`。

## 详细输出指令(/verbose 或 /v)

> - Levels: `on` (minimal) | `full` | `off` (default).
> - Directive-only message toggles session verbose and replies `Verbose logging enabled.` / `Verbose logging disabled.`; invalid levels return a hint without changing state.
> - `/verbose off` stores an explicit session override; clear it via the Sessions UI by choosing `inherit`.
> - Inline directive affects only that message; session/global defaults apply otherwise.
> - Send `/verbose` (or `/verbose:`) with no argument to see the current verbose level.
> - When verbose is on, agents that emit structured tool results (Pi, other JSON agents) send each tool call back as its own metadata-only message, prefixed with `<emoji> <tool-name>: <arg>` when available. These tool summaries are sent as soon as each tool starts (separate bubbles), not as streaming deltas.
> - Tool failure summaries remain visible in normal mode, but raw error detail suffixes are hidden unless verbose is `full`.
> - When verbose is `full`, tool outputs are also forwarded after completion (separate bubble, truncated to a safe length). If you toggle `/verbose on|full|off` while a run is in-flight, subsequent tool bubbles honor the new setting.
> - `agents.defaults.toolProgressDetail` controls the shape of `/verbose` tool summaries and progress-draft tool lines. Use `"explain"` (default) for compact human labels such as `🛠️ Exec: checking JS syntax`; use `"raw"` when you also want the raw command/detail appended for debugging. Per-agent `agents.list[].toolProgressDetail` overrides the default.
>   - `explain`: `🛠️ Exec: check JS syntax for /tmp/app.js`
>   - `raw`: `🛠️ Exec: check JS syntax for /tmp/app.js, node --check /tmp/app.js`

- 级别:`on`(最少)|`full`|`off`(默认)。
- 只含指令的消息切换会话 verbose,回复 `Verbose logging enabled.` / `Verbose logging disabled.`;无效级别返回提示,状态不变。
- `/verbose off` 存一个显式会话覆盖;在 Sessions UI 里选 `inherit` 清掉。
- 内联指令只影响这条消息;否则按会话 / 全局默认。
- 不带参数发 `/verbose`(或 `/verbose:`)看当前 verbose 级别。
- verbose 开着时,发送结构化工具结果的 agent(Pi 和其他 JSON agent)会把每个工具调用作为独立的"仅元数据"消息发回来,有的话带前缀 `<emoji> <工具名>: <参数>`。这些工具摘要在每个工具一启动就发(独立气泡),不是流式增量。
- 工具失败摘要在普通模式下也可见,但原始错误细节后缀只在 verbose 是 `full` 时才显示。
- verbose 是 `full` 时,工具输出在完成后也会转发(独立气泡,截断到安全长度)。运行进行中切换 `/verbose on|full|off` 时,后续工具气泡遵守新设置。
- `agents.defaults.toolProgressDetail` 控制 `/verbose` 工具摘要和进度草稿工具行的形状。用 `"explain"`(默认)出紧凑的人类标签,如 `🛠️ Exec: checking JS syntax`;调试时要原始命令 / 细节附在后面就用 `"raw"`。单 agent 的 `agents.list[].toolProgressDetail` 覆盖默认。
  - `explain`:`🛠️ Exec: check JS syntax for /tmp/app.js`
  - `raw`:`🛠️ Exec: check JS syntax for /tmp/app.js, node --check /tmp/app.js`

## 插件 trace 指令(/trace)

> - Levels: `on` | `off` (default).
> - Directive-only message toggles session plugin trace output and replies `Plugin trace enabled.` / `Plugin trace disabled.`.
> - Inline directive affects only that message; session/global defaults apply otherwise.
> - Send `/trace` (or `/trace:`) with no argument to see the current trace level.
> - `/trace` is narrower than `/verbose`: it only exposes plugin-owned trace/debug lines such as Active Memory debug summaries.
> - Trace lines can appear in `/status` and as a follow-up diagnostic message after the normal assistant reply.

- 级别:`on` | `off`(默认)。
- 只含指令的消息切换会话插件 trace 输出,回复 `Plugin trace enabled.` / `Plugin trace disabled.`。
- 内联指令只影响这条消息;否则按会话 / 全局默认。
- 不带参数发 `/trace`(或 `/trace:`)看当前 trace 级别。
- `/trace` 比 `/verbose` 窄:它只暴露插件持有的 trace / 调试行,如主动记忆调试摘要。
- Trace 行可以在 `/status` 里露出,也可以作为跟在正常 assistant 回复后的跟进诊断消息出现。

## 推理可见性(/reasoning)

> - Levels: `on|off|stream`.
> - Directive-only message toggles whether thinking blocks are shown in replies.
> - When enabled, reasoning is sent as a **separate message** prefixed with `Thinking`.
> - `stream` (Telegram only): streams reasoning into the Telegram draft bubble while the reply is generating, then sends the final answer without reasoning.
> - Alias: `/reason`.
> - Send `/reasoning` (or `/reasoning:`) with no argument to see the current reasoning level.
> - Resolution order: inline directive, then session override, then per-agent default (`agents.list[].reasoningDefault`), then global default (`agents.defaults.reasoningDefault`), then fallback (`off`).

- 级别:`on|off|stream`。
- 只含指令的消息切换"思考块是否在回复里显示"。
- 开启时,推理作为**独立消息**发出,前缀 `Thinking`。
- `stream`(仅 Telegram):生成回复时把推理流到 Telegram 草稿气泡里,然后发不带推理的最终答案。
- 别名:`/reason`。
- 不带参数发 `/reasoning`(或 `/reasoning:`)看当前推理级别。
- 解析顺序:内联指令 → 会话覆盖 → 单 agent 默认(`agents.list[].reasoningDefault`)→ 全局默认(`agents.defaults.reasoningDefault`)→ 回退(`off`)。

> Malformed local-model reasoning tags are handled conservatively. Closed `<think>...</think>` blocks stay hidden on normal replies, and unclosed reasoning after already visible text is also hidden. If a reply is fully wrapped in a single unclosed opening tag and would otherwise deliver as empty text, OpenClaw removes the malformed opening tag and delivers the remaining text.

本地模型出的格式错的推理标签会保守处理。闭合的 `<think>...</think>` 块在正常回复里仍然隐藏;已经有可见文本后面又出现的未闭合推理也隐藏。整条回复被单个未闭合的开标签包住、否则会以空文本投递时,OpenClaw 去掉这个畸形开标签,把剩下的文本投出去。

## 相关

> - Elevated mode docs live in [Elevated mode](/tools/elevated).

- 提权模式文档见 [Elevated mode](/tools/elevated)。

## 心跳

> - Heartbeat probe body is the configured heartbeat prompt (default: `Read HEARTBEAT.md if it exists (workspace context). Follow it strictly. Do not infer or repeat old tasks from prior chats. If nothing needs attention, reply HEARTBEAT_OK.`). Inline directives in a heartbeat message apply as usual (but avoid changing session defaults from heartbeats).
> - Heartbeat delivery defaults to the final payload only. To also send the separate `Thinking` message (when available), set `agents.defaults.heartbeat.includeReasoning: true` or per-agent `agents.list[].heartbeat.includeReasoning: true`.

- 心跳探测正文是配置的心跳 prompt(默认:`Read HEARTBEAT.md if it exists (workspace context). Follow it strictly. Do not infer or repeat old tasks from prior chats. If nothing needs attention, reply HEARTBEAT_OK.`)。心跳消息里的内联指令照常生效(但别从心跳里改会话默认)。
- 心跳投递默认只发最终载荷。要同时发独立的 `Thinking` 消息(有的话),设 `agents.defaults.heartbeat.includeReasoning: true` 或单 agent 的 `agents.list[].heartbeat.includeReasoning: true`。

## 网页聊天 UI

> - The web chat thinking selector mirrors the session's stored level from the inbound session store/config when the page loads.
> - Picking another level writes the session override immediately via `sessions.patch`; it does not wait for the next send and it is not a one-shot `thinkingOnce` override.
> - The first option is always the clear-override choice. It shows `Inherited: <resolved level>`, including `Inherited: Off` when inherited thinking is disabled.
> - Explicit picker choices use their direct level labels while preserving provider labels when present (for example `Maximum` for a provider-labeled `max` option).
> - The picker uses `thinkingLevels` returned by the gateway session row/defaults, with `thinkingOptions` kept as a legacy label list. The browser UI does not keep its own provider regex list; plugins own model-specific level sets.
> - `/think:<level>` still works and updates the same stored session level, so chat directives and the picker stay in sync.

- 网页聊天的思考选择器在页面加载时,镜像入站会话存储 / 配置里这个会话存的级别。
- 选另一个级别会通过 `sessions.patch` 立即写入会话覆盖;不等下一次发送,也不是一次性的 `thinkingOnce` 覆盖。
- 第一个选项永远是"清除覆盖"。它显示 `Inherited: <解析出的级别>`,包括继承的思考被关掉时显示 `Inherited: Off`。
- 显式选择用各自级别的直接标签,有 provider 标签时保留 provider 标签(例如 provider 标过 `max` 的选项显示 `Maximum`)。
- 选择器用 gateway session 行 / 默认返回的 `thinkingLevels`,`thinkingOptions` 作为旧版标签列表保留。浏览器 UI 不维护自己的 provider 正则列表;插件持有具体模型的级别集。
- `/think:<级别>` 仍然能用,更新同一份存的会话级别,所以聊天指令和选择器保持同步。

## Provider profile

> - Provider plugins can expose `resolveThinkingProfile(ctx)` to define the model's supported levels and default.
> - Provider plugins that proxy Claude models should reuse `resolveClaudeThinkingProfile(modelId)` from `openclaw/plugin-sdk/provider-model-shared` so direct Anthropic and proxy catalogs stay aligned.
> - Each profile level has a stored canonical `id` (`off`, `minimal`, `low`, `medium`, `high`, `xhigh`, `adaptive`, or `max`) and may include a display `label`. Binary providers use `{ id: "low", label: "on" }`.
> - Tool plugins that need to validate an explicit thinking override should use `api.runtime.agent.resolveThinkingPolicy({ provider, model })` plus `api.runtime.agent.normalizeThinkingLevel(...)`; they should not keep their own provider/model level lists.
> - Tool plugins with access to configured custom model metadata can pass `catalog` into `resolveThinkingPolicy` so `compat.supportedReasoningEfforts` opt-ins are reflected in plugin-side validation.
> - Published legacy hooks (`supportsXHighThinking`, `isBinaryThinking`, and `resolveDefaultThinkingLevel`) remain as compatibility adapters, but new custom level sets should use `resolveThinkingProfile`.
> - Gateway rows/defaults expose `thinkingLevels`, `thinkingOptions`, and `thinkingDefault` so ACP/chat clients render the same profile ids and labels that runtime validation uses.

- Provider 插件可以暴露 `resolveThinkingProfile(ctx)`,定义模型支持的级别集和默认。
- 代理 Claude 模型的 provider 插件应该复用 `openclaw/plugin-sdk/provider-model-shared` 里的 `resolveClaudeThinkingProfile(modelId)`,这样直连 Anthropic 和代理目录保持一致。
- profile 里每个级别有一个存储用的规范 `id`(`off`、`minimal`、`low`、`medium`、`high`、`xhigh`、`adaptive`、`max`),还可以有显示用的 `label`。二选一 provider 用 `{ id: "low", label: "on" }`。
- 需要校验显式思考覆盖的工具插件应当用 `api.runtime.agent.resolveThinkingPolicy({ provider, model })` 加 `api.runtime.agent.normalizeThinkingLevel(...)`;不要自己维护 provider / 模型级别列表。
- 能拿到配置好的自定义模型元数据的工具插件,可以把 `catalog` 传给 `resolveThinkingPolicy`,让 `compat.supportedReasoningEfforts` 的 opt-in 反映到插件侧校验里。
- 已发布的旧版钩子(`supportsXHighThinking`、`isBinaryThinking`、`resolveDefaultThinkingLevel`)作为兼容适配器保留,但新的自定义级别集应当用 `resolveThinkingProfile`。
- gateway 的 row / 默认暴露 `thinkingLevels`、`thinkingOptions`、`thinkingDefault`,这样 ACP / 聊天客户端渲染的 profile id 和 label 跟运行时校验用的一致。
