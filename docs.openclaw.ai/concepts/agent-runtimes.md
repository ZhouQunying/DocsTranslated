# Agent runtimes（Agent 运行时）

> An **agent runtime** is the component that owns one prepared model loop: it receives the prompt, drives model output, handles native tool calls, and returns the finished turn to OpenClaw.

**Agent runtime（Agent 运行时）**是负责"一次完整模型循环"的那个组件：它接收提示词、驱动模型生成输出、处理原生工具调用，最后把跑完的整轮结果交还给 OpenClaw。

> Runtimes are easy to confuse with providers because both show up near model configuration. They are different layers:

Runtime 容易和 Provider 搞混——两者都出现在模型配置附近。但它们其实是不同层次的东西：

> | Layer         | Examples                              | What it means                                                       |
> | ------------- | ------------------------------------- | ------------------------------------------------------------------- |
> | Provider      | `openai`, `anthropic`, `openai-codex` | How OpenClaw authenticates, discovers models, and names model refs. |
> | Model         | `gpt-5.5`, `claude-opus-4-6`          | The model selected for the agent turn.                              |
> | Agent runtime | `pi`, `codex`, `claude-cli`           | The low level loop or backend that executes the prepared turn.      |
> | Channel       | Telegram, Discord, Slack, WhatsApp    | Where messages enter and leave OpenClaw.                            |

| 层次              | 例子                                  | 含义                                                                |
| ----------------- | ------------------------------------- | ------------------------------------------------------------------- |
| Provider（厂商）  | `openai`、`anthropic`、`openai-codex` | OpenClaw 用什么方式认证、怎么发现模型、怎么命名模型引用             |
| Model（模型）     | `gpt-5.5`、`claude-opus-4-6`          | 这一轮 Agent 选用的具体模型                                         |
| Agent runtime（Agent 运行时） | `pi`、`codex`、`claude-cli` | 真正执行这一轮的底层循环 / 后端                                     |
| Channel（通道）   | Telegram、Discord、Slack、WhatsApp    | 消息从哪里进、回复发到哪里                                          |

> You will also see the word **harness** in code. A harness is the implementation that provides an agent runtime. For example, the bundled Codex harness implements the `codex` runtime. Public config uses `agentRuntime.id` on provider or model entries; whole-agent runtime keys are legacy and ignored. `openclaw doctor --fix` removes old whole-agent runtime pins and rewrites legacy runtime model refs to canonical provider/model refs plus model-scoped runtime policy where needed.

代码里你还会看到 **harness（载具）**这个词。harness 就是实现某个 Agent runtime 的那段代码——例如内置的 Codex harness 实现了 `codex` 这个运行时。对外配置时，runtime 写在 provider 或 model 条目下的 `agentRuntime.id` 字段里；老式的"整个 Agent 一个 runtime key"已经废弃，会被忽略。`openclaw doctor --fix` 会清掉那些过期的整 Agent 级 runtime 配置，并在需要的地方把旧式的 runtime 模型引用改写成"标准 provider/model 引用 + 按模型作用域配 runtime 策略"的新形式。

> There are two runtime families:
>
> * **Embedded harnesses** run inside OpenClaw's prepared agent loop. Today this is the built-in `pi` runtime plus registered plugin harnesses such as `codex`.
> * **CLI backends** run a local CLI process while keeping the model ref canonical. For example, `anthropic/claude-opus-4-7` with a model-scoped `agentRuntime.id: "claude-cli"` means "select the Anthropic model, execute through Claude CLI." `claude-cli` is not an embedded harness id and must not be passed to AgentHarness selection.

Runtime 分两大类：

- **嵌入式 harness（embedded harness）**：跑在 OpenClaw 自己准备好的 Agent 循环里。目前包括内置的 `pi` 运行时，以及已注册的插件 harness（例如 `codex`）。
- **CLI 后端**：启动一个本地 CLI 进程来跑，但模型引用保持标准格式。例如，`anthropic/claude-opus-4-7` 配上按模型作用域的 `agentRuntime.id: "claude-cli"`，意思是"选 Anthropic 的模型，但通过 Claude CLI 来执行"。注意：`claude-cli` 不是嵌入式 harness 的 id，不能传给 AgentHarness 的选择逻辑。

---

> ## Codex surfaces

## Codex 涉及的几个不同入口

> Most confusion comes from several different surfaces sharing the Codex name:

大部分的困惑都源于：好几个完全不同的东西名字里都带 "Codex"。

> | Surface                                          | OpenClaw name/config                 | What it does                                                                                                   |
> | ------------------------------------------------ | ------------------------------------ | -------------------------------------------------------------------------------------------------------------- |
> | Native Codex app-server runtime                  | `openai/*` model refs                | Runs OpenAI embedded agent turns through Codex app-server. This is the usual ChatGPT/Codex subscription setup. |
> | Codex OAuth auth profiles                        | `openai-codex` auth provider         | Stores ChatGPT/Codex subscription auth that the Codex app-server harness consumes.                             |
> | Codex ACP adapter                                | `runtime: "acp"`, `agentId: "codex"` | Runs Codex through the external ACP/acpx control plane. Use only when ACP/acpx is explicitly asked.            |
> | Native Codex chat-control command set            | `/codex ...`                         | Binds, resumes, steers, stops, and inspects Codex app-server threads from chat.                                |
> | OpenAI Platform API route for non-agent surfaces | `openai/*` plus API-key auth         | Used for direct OpenAI APIs such as images, embeddings, speech, and realtime.                                  |

| 入口                                       | OpenClaw 里的名字 / 配置写法           | 它的作用                                                                                                  |
| ------------------------------------------ | -------------------------------------- | --------------------------------------------------------------------------------------------------------- |
| 原生 Codex app-server 运行时               | `openai/*` 模型引用                    | 通过 Codex app-server 跑 OpenAI 的嵌入式 Agent 轮次。这是常见的 ChatGPT / Codex 订阅用户配置             |
| Codex OAuth 认证档案                       | `openai-codex` 认证 provider           | 保存 ChatGPT / Codex 订阅的认证信息，给 Codex app-server harness 使用                                    |
| Codex ACP 适配器                           | `runtime: "acp"`、`agentId: "codex"`   | 通过外部 ACP / acpx 控制面跑 Codex。**只有用户明确要求 ACP / acpx 时才用**                                |
| 原生 Codex 聊天控制命令集                  | `/codex ...`                           | 在聊天里绑定、恢复、转向、停止、查看 Codex app-server 线程                                                |
| 走 OpenAI Platform API 的非 Agent 接口     | `openai/*` 加 API key 认证             | 用于直连 OpenAI 的 API，比如图像、embedding、语音、realtime                                               |

> Those surfaces are intentionally independent. Enabling the `codex` plugin makes the native app-server features available; `openclaw doctor --fix` owns legacy `openai-codex/*` route repair and stale session pin cleanup. Selecting `openai/*` for an agent model now means "run this through Codex" unless a non-agent OpenAI API surface is being used.

这几个入口是刻意做成相互独立的。启用 `codex` 插件后，原生 app-server 的功能就可用了；`openclaw doctor --fix` 负责修复旧版 `openai-codex/*` 路由、清理过期的会话钉绑。给 Agent 模型选 `openai/*` 现在意味着"通过 Codex 跑这一轮"——除非你用的是非 Agent 类的 OpenAI API。

> The common ChatGPT/Codex subscription setup uses Codex OAuth for auth, but keeps the model ref as `openai/*` and selects the `codex` runtime:

ChatGPT / Codex 订阅用户的常见配置：用 Codex OAuth 做认证，但模型引用保留为 `openai/*`，并选择 `codex` 运行时：

> ```json5
> {
>   agents: {
>     defaults: {
>       model: "openai/gpt-5.5",
>     },
>   },
> }
> ```

```json5
{
  agents: {
    defaults: {
      model: "openai/gpt-5.5",
    },
  },
}
```

> That means OpenClaw selects an OpenAI model ref, then asks the Codex app-server runtime to run the embedded agent turn. It does not mean "use API billing," and it does not mean the channel, model provider catalog, or OpenClaw session store becomes Codex.

这等于是说：OpenClaw 选了一个 OpenAI 模型引用，然后让 Codex app-server 运行时来跑这一轮嵌入式 Agent。**这不等于"按 API 计费"**，也**不会**让通道、模型 provider 目录或 OpenClaw 会话存储变成 Codex 的。

> When the bundled `codex` plugin is enabled, natural-language Codex control should use the native `/codex` command surface (`/codex bind`, `/codex threads`, `/codex resume`, `/codex steer`, `/codex stop`) instead of ACP. Use ACP for Codex only when the user explicitly asks for ACP/acpx or is testing the ACP adapter path. Claude Code, Gemini CLI, OpenCode, Cursor, and similar external harnesses still use ACP.

启用了内置的 `codex` 插件后，用自然语言控制 Codex 应当走原生 `/codex` 命令（`/codex bind`、`/codex threads`、`/codex resume`、`/codex steer`、`/codex stop`），**不要**走 ACP。只有在用户明确要 ACP / acpx 或在测试 ACP 适配器时，Codex 才走 ACP。Claude Code、Gemini CLI、OpenCode、Cursor 这类外部 harness 仍然继续用 ACP。

> This is the agent-facing decision tree:

下面这棵决策树是给 Agent 看的——遇到哪种请求该用哪个入口：

> 1. If the user asks for **Codex bind/control/thread/resume/steer/stop**, use the native `/codex` command surface when the bundled `codex` plugin is enabled.
> 2. If the user asks for **Codex as the embedded runtime** or wants the normal subscription-backed Codex agent experience, use `openai/<model>`.
> 3. If the user explicitly chooses **PI for an OpenAI model**, keep the model ref as `openai/<model>` and set provider/model runtime policy to `agentRuntime.id: "pi"`. A selected `openai-codex` auth profile is routed internally through PI's legacy Codex-auth transport.
> 4. If legacy config still contains **`openai-codex/*` model refs**, repair it to `openai/<model>` with `openclaw doctor --fix`; doctor keeps the Codex auth route by adding provider/model-scoped `agentRuntime.id: "codex"` where the old model ref implied it. Legacy **`codex-cli/*` model refs** repair to the same `openai/<model>` Codex app-server route; OpenClaw no longer keeps a bundled Codex CLI backend.
> 5. If the user explicitly says **ACP**, **acpx**, or **Codex ACP adapter**, use ACP with `runtime: "acp"` and `agentId: "codex"`.
> 6. If the request is for **Claude Code, Gemini CLI, OpenCode, Cursor, Droid, or another external harness**, use ACP/acpx, not the native sub-agent runtime.

1. 用户要求 **Codex 的 bind / control / thread / resume / steer / stop** 时——只要内置的 `codex` 插件已启用，就走原生 `/codex` 命令。
2. 用户要求 **Codex 作为嵌入式运行时**，或者想要"订阅版 Codex Agent"的常规体验时——配 `openai/<model>`。
3. 用户明确选 **OpenAI 模型走 PI** 时——模型引用仍写 `openai/<model>`，但把 provider / model 的运行时策略设为 `agentRuntime.id: "pi"`。如果配套选了 `openai-codex` 认证档案，OpenClaw 内部会把 PI 走旧版的 Codex 认证传输路径。
4. 旧配置里还残留 **`openai-codex/*` 模型引用**时——用 `openclaw doctor --fix` 修成 `openai/<model>`；doctor 会在原引用暗含 Codex 认证路由的地方加上 `agentRuntime.id: "codex"`（按 provider / model 作用域）。旧的 **`codex-cli/*` 模型引用**也被 doctor 迁移到 `openai/<model>` 这条 Codex app-server 路径——OpenClaw 已经不再内置 Codex CLI 后端。
5. 用户明确说 **ACP**、**acpx** 或 **Codex ACP 适配器**时——用 ACP，配 `runtime: "acp"` 和 `agentId: "codex"`。
6. 请求是关于 **Claude Code、Gemini CLI、OpenCode、Cursor、Droid 或其他外部 harness** 时——用 ACP / acpx，不要用原生子 Agent 运行时。

> | You mean...                             | Use...                                       |
> | --------------------------------------- | -------------------------------------------- |
> | Codex app-server chat/thread control    | `/codex ...` from the bundled `codex` plugin |
> | Codex app-server embedded agent runtime | `openai/*` agent model refs                  |
> | OpenAI Codex OAuth                      | `openai-codex` auth profiles                 |
> | Claude Code or other external harness   | ACP/acpx                                     |

| 你想要的是……                             | 那就用……                                       |
| ---------------------------------------- | ----------------------------------------------- |
| Codex app-server 的聊天 / 线程控制       | 内置 `codex` 插件提供的 `/codex ...` 命令       |
| Codex app-server 作为嵌入式 Agent 运行时 | `openai/*` Agent 模型引用                       |
| OpenAI Codex OAuth                       | `openai-codex` 认证档案                         |
| Claude Code 或其他外部 harness           | ACP / acpx                                      |

> For the OpenAI-family prefix split, see [OpenAI](/providers/openai) and [Model providers](/concepts/model-providers). For the Codex runtime support contract, see [Codex harness runtime](/plugins/codex-harness-runtime#v1-support-contract).

OpenAI 系列前缀的具体划分见 [OpenAI](/providers/openai) 和 [Model providers](/concepts/model-providers)。Codex 运行时的支持契约见 [Codex harness runtime](/plugins/codex-harness-runtime#v1-support-contract)。

---

> ## Runtime ownership

## 运行时的"职责分工"

> Different runtimes own different amounts of the loop.

不同运行时在整个循环中负责的部分不一样：

> | Surface                     | OpenClaw PI embedded                    | Codex app-server                                                            |
> | --------------------------- | --------------------------------------- | --------------------------------------------------------------------------- |
> | Model loop owner            | OpenClaw through the PI embedded runner | Codex app-server                                                            |
> | Canonical thread state      | OpenClaw transcript                     | Codex thread, plus OpenClaw transcript mirror                               |
> | OpenClaw dynamic tools      | Native OpenClaw tool loop               | Bridged through the Codex adapter                                           |
> | Native shell and file tools | PI/OpenClaw path                        | Codex-native tools, bridged through native hooks where supported            |
> | Context engine              | Native OpenClaw context assembly        | OpenClaw projects assembled context into the Codex turn                     |
> | Compaction                  | OpenClaw or selected context engine     | Codex-native compaction, with OpenClaw notifications and mirror maintenance |
> | Channel delivery            | OpenClaw                                | OpenClaw                                                                    |

| 环节                       | OpenClaw PI 嵌入式                        | Codex app-server                                                          |
| -------------------------- | ----------------------------------------- | ------------------------------------------------------------------------- |
| 模型循环的所有者           | OpenClaw 通过 PI 嵌入式 runner 拥有       | Codex app-server 拥有                                                     |
| 线程状态的"权威源"         | OpenClaw 的会话记录（transcript）         | Codex 自己的线程为权威，OpenClaw 维护一份镜像                             |
| OpenClaw 动态工具          | 原生的 OpenClaw 工具循环                  | 通过 Codex 适配器桥接                                                     |
| 原生 shell 和文件工具      | 走 PI / OpenClaw 路径                     | Codex 原生工具，在支持的地方通过原生钩子桥接                              |
| 上下文引擎                 | 原生的 OpenClaw 上下文拼装                | OpenClaw 把拼好的上下文投射到 Codex 的轮次中                              |
| 上下文压缩（compaction）   | OpenClaw 或所选的上下文引擎               | Codex 原生压缩；OpenClaw 收到通知并维护好镜像                             |
| 通道投递（消息发出去）     | OpenClaw                                  | OpenClaw                                                                  |

> This ownership split is the main design rule:
>
> * If OpenClaw owns the surface, OpenClaw can provide normal plugin hook behavior.
> * If the native runtime owns the surface, OpenClaw needs runtime events or native hooks.
> * If the native runtime owns canonical thread state, OpenClaw should mirror and project context, not rewrite unsupported internals.

这种"谁拥有什么"的划分，是整个设计的核心规则：

- 这一环节归 OpenClaw 拥有的，OpenClaw 就能提供正常的插件钩子行为。
- 归原生运行时拥有的，OpenClaw 就要靠运行时事件或原生钩子来介入。
- 线程状态的权威源在原生运行时手里时，OpenClaw 应该做"镜像 + 上下文投射"，而不是去改写它不支持的内部细节。

---

> ## Runtime selection

## 运行时怎么选

> OpenClaw chooses an embedded runtime after provider and model resolution:

OpenClaw 是在 provider 和 model 都解析完之后才选嵌入式运行时的，按下面顺序：

> 1. Model-scoped runtime policy wins. This can live in a configured provider model entry or in `agents.defaults.models["provider/model"].agentRuntime` / `agents.list[].models["provider/model"].agentRuntime`. A provider wildcard such as `agents.defaults.models["vllm/*"].agentRuntime` applies after exact model policy, so dynamically discovered provider models can share one runtime without overriding exact per-model exceptions.
> 2. Provider-scoped runtime policy comes next at `models.providers.<provider>.agentRuntime`.
> 3. In `auto` mode, registered plugin runtimes can claim supported provider/model pairs.
> 4. If no runtime claims a turn in `auto` mode, OpenClaw uses PI as the compatibility runtime. Use an explicit runtime id when the run must be strict.

1. **按模型作用域**配的运行时策略优先。可以写在 provider 的某个模型条目里，也可以写在 `agents.defaults.models["provider/model"].agentRuntime` 或 `agents.list[].models["provider/model"].agentRuntime`。带 provider 通配的写法，比如 `agents.defaults.models["vllm/*"].agentRuntime`，会在精确匹配之后才生效——这样动态发现的 provider 模型可以共用一个运行时，而不会覆盖针对单个模型的特殊设置。
2. 其次是**按 provider 作用域**配的运行时策略：`models.providers.<provider>.agentRuntime`。
3. 在 `auto` 模式下，已注册的插件运行时可以"认领"它支持的 provider / model 组合。
4. `auto` 模式下没有任何运行时认领这一轮时，OpenClaw 退回到 PI 作为兼容运行时。如果要严格执行某个运行时，请明确写出运行时 id。

> Whole-session and whole-agent runtime pins are ignored. That includes `OPENCLAW_AGENT_RUNTIME`, session `agentHarnessId`/`agentRuntimeOverride` state, `agents.defaults.agentRuntime`, and `agents.list[].agentRuntime`. Run `openclaw doctor --fix` to remove stale whole-agent runtime config and convert legacy runtime model refs where OpenClaw can preserve the intent.

整个会话或整个 Agent 级别的运行时钉绑都会被忽略。这包括 `OPENCLAW_AGENT_RUNTIME` 环境变量、会话里的 `agentHarnessId` / `agentRuntimeOverride` 状态、`agents.defaults.agentRuntime`、`agents.list[].agentRuntime`。跑 `openclaw doctor --fix` 可以清理这些过期的 Agent 级运行时配置，并在能保留原意的地方把旧式 runtime 模型引用转换过来。

> Explicit provider/model plugin runtimes fail closed. For example, `agentRuntime.id: "codex"` on a provider or model means Codex or a clear selection/runtime error; it is never silently routed back to PI.

显式指定的 provider / model 插件运行时是"失败即拒绝"（fail-closed）的。例如，在某个 provider 或 model 上写了 `agentRuntime.id: "codex"`，那这一轮要么走 Codex，要么报一个明确的"选择 / 运行时错误"——绝**不会**悄悄退回到 PI。

> CLI backend aliases are different from embedded harness ids. The preferred Claude CLI form is:

CLI 后端别名和嵌入式 harness id 不是一回事。Claude CLI 的推荐写法是：

> ```json5
> {
>   agents: {
>     defaults: {
>       model: "anthropic/claude-opus-4-7",
>       models: {
>         "anthropic/claude-opus-4-7": {
>           agentRuntime: { id: "claude-cli" },
>         },
>       },
>     },
>   },
> }
> ```

```json5
{
  agents: {
    defaults: {
      model: "anthropic/claude-opus-4-7",
      models: {
        "anthropic/claude-opus-4-7": {
          agentRuntime: { id: "claude-cli" },
        },
      },
    },
  },
}
```

> Legacy refs such as `claude-cli/claude-opus-4-7` remain supported for compatibility, but new config should keep the provider/model canonical and put the execution backend in provider/model runtime policy.

旧式引用如 `claude-cli/claude-opus-4-7` 出于兼容性仍然支持，但新写的配置应该让 provider / model 保持标准格式，把执行后端放进 provider / model 的运行时策略里。

> Legacy `codex-cli/*` refs are different: doctor migrates them to `openai/*` so they run through the Codex app-server harness instead of preserving a Codex CLI backend.

旧式 `codex-cli/*` 引用情况不一样：doctor 会把它们迁移到 `openai/*`，让它们走 Codex app-server harness——而不是保留一个 Codex CLI 后端。

> `auto` mode is intentionally conservative for most providers. OpenAI agent models are the exception: unset runtime and `auto` both resolve to the Codex harness. Explicit PI runtime config remains an opt-in compatibility route for `openai/*` agent turns; when paired with a selected `openai-codex` auth profile, OpenClaw routes PI internally through the legacy Codex-auth transport while keeping the public model ref as `openai/*`. Stale OpenAI PI session pins are ignored by runtime selection and can be cleaned with `openclaw doctor --fix`.

`auto` 模式对大多数 provider 都刻意保守，OpenAI Agent 模型是个例外——不设运行时和写 `auto` 都会解析到 Codex harness。如果你确实想给 `openai/*` Agent 轮次走 PI，仍然可以显式配置 PI 运行时作为兼容路径；和 `openai-codex` 认证档案配套时，OpenClaw 内部会把 PI 走旧版 Codex 认证传输，但对外的模型引用保持是 `openai/*`。运行时选择会忽略残留的 OpenAI PI 会话钉绑，这些可以用 `openclaw doctor --fix` 清掉。

> If `openclaw doctor` warns that the `codex` plugin is enabled while `openai-codex/*` remains in config, treat that as legacy route state. Run `openclaw doctor --fix` to rewrite it to `openai/*` with the Codex runtime.

如果 `openclaw doctor` 提示"`codex` 插件已启用，但配置里还有 `openai-codex/*`"，那就是遗留的路由状态。跑 `openclaw doctor --fix` 把它改写为 `openai/*` + Codex 运行时即可。

---

> ## Compatibility contract

## 兼容性契约

> When a runtime is not PI, it should document what OpenClaw surfaces it supports. Use this shape for runtime docs:

只要不是 PI 运行时，文档里就该说清楚自己支持哪些 OpenClaw 能力。运行时文档照下面这套问题写：

> | Question                               | Why it matters                                                                                    |
> | -------------------------------------- | ------------------------------------------------------------------------------------------------- |
> | Who owns the model loop?               | Determines where retries, tool continuation, and final answer decisions happen.                   |
> | Who owns canonical thread history?     | Determines whether OpenClaw can edit history or only mirror it.                                   |
> | Do OpenClaw dynamic tools work?        | Messaging, sessions, cron, and OpenClaw-owned tools rely on this.                                 |
> | Do dynamic tool hooks work?            | Plugins expect `before_tool_call`, `after_tool_call`, and middleware around OpenClaw-owned tools. |
> | Do native tool hooks work?             | Shell, patch, and runtime-owned tools need native hook support for policy and observation.        |
> | Does the context engine lifecycle run? | Memory and context plugins depend on assemble, ingest, after-turn, and compaction lifecycle.      |
> | What compaction data is exposed?       | Some plugins only need notifications, while others need kept/dropped metadata.                    |
> | What is intentionally unsupported?     | Users should not assume PI equivalence where the native runtime owns more state.                  |

| 问题                              | 为什么要回答                                                                              |
| --------------------------------- | ----------------------------------------------------------------------------------------- |
| 模型循环归谁拥有？                | 决定了重试、工具续跑、最终回答这些决策发生在哪里                                          |
| 线程历史的权威源归谁？            | 决定了 OpenClaw 能不能编辑历史，还是只能镜像                                              |
| OpenClaw 的动态工具能用吗？       | 消息、会话、cron 等 OpenClaw 自有的工具都依赖这一点                                       |
| 动态工具的钩子能用吗？            | 插件指望在 OpenClaw 自有工具周围有 `before_tool_call`、`after_tool_call` 和中间件         |
| 原生工具的钩子能用吗？            | shell、patch 以及运行时自有的工具，需要靠原生钩子做策略和观察                             |
| 上下文引擎的生命周期能跑吗？      | 记忆和上下文插件依赖 assemble、ingest、after-turn、compaction 这套生命周期                |
| 暴露了哪些压缩数据？              | 有的插件只需要通知，有的需要"保留 / 丢弃"的元数据                                         |
| 哪些是刻意不支持的？              | 当原生运行时自己掌握更多状态时，用户不能想当然地认为它和 PI 行为完全一致                  |

> The Codex runtime support contract is documented in [Codex harness runtime](/plugins/codex-harness-runtime#v1-support-contract).

Codex 运行时的支持契约见 [Codex harness runtime](/plugins/codex-harness-runtime#v1-support-contract)。

---

> ## Status labels

## 状态标签的读法

> Status output may show both `Execution` and `Runtime` labels. Read them as diagnostics, not as provider names.

`status` 输出可能同时出现 `Execution` 和 `Runtime` 两个标签。把它们当诊断信息看，**不要**当成 provider 的名字：

> * A model ref such as `openai/gpt-5.5` tells you the selected provider/model.
> * A runtime id such as `codex` tells you which loop is executing the turn.
> * A channel label such as Telegram or Discord tells you where the conversation is happening.

- `openai/gpt-5.5` 这种**模型引用**告诉你选中的 provider / 模型是什么。
- `codex` 这种**运行时 id** 告诉你这一轮由哪个循环在执行。
- Telegram、Discord 这种**通道标签**告诉你对话发生在哪里。

> If a run still shows an unexpected runtime, inspect the selected provider/model runtime policy first. Legacy session runtime pins no longer decide routing.

如果某次运行的运行时还是不符合预期，先去看选中的 provider / model 的运行时策略。旧版会话级的运行时钉绑已经不再决定路由了。

---

> ## Related

## 相关

> * [Codex harness](/plugins/codex-harness)
> * [Codex harness runtime](/plugins/codex-harness-runtime)
> * [OpenAI](/providers/openai)
> * [Agent harness plugins](/plugins/sdk-agent-harness)
> * [Agent loop](/concepts/agent-loop)
> * [Models](/concepts/models)
> * [Status](/cli/status)

- [Codex harness](/plugins/codex-harness)
- [Codex harness runtime](/plugins/codex-harness-runtime)
- [OpenAI](/providers/openai)
- [Agent harness 插件](/plugins/sdk-agent-harness)
- [Agent 循环](/concepts/agent-loop)
- [Models](/concepts/models)
- [Status](/cli/status)
