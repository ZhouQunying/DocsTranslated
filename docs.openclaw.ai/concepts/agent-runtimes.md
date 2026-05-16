# Agent runtimes

> An **agent runtime** is the component that owns one prepared model loop: it receives the prompt, drives model output, handles native tool calls, and returns the finished turn to OpenClaw.

**agent runtime（agent 运行时）**是拥有一个准备好的模型循环的组件：接 prompt、驱动模型输出、处理原生工具调用、把跑完的轮次交还给 OpenClaw。

> Runtimes are easy to confuse with providers because both show up near model configuration. They are different layers:

runtime 容易和 provider 混 —— 两者在模型配置附近都会出现。它们其实是不同层：

> | Layer         | Examples                              | What it means                                                       |
> | ------------- | ------------------------------------- | ------------------------------------------------------------------- |
> | Provider      | `openai`, `anthropic`, `openai-codex` | How OpenClaw authenticates, discovers models, and names model refs. |
> | Model         | `gpt-5.5`, `claude-opus-4-6`          | The model selected for the agent turn.                              |
> | Agent runtime | `pi`, `codex`, `claude-cli`           | The low level loop or backend that executes the prepared turn.      |
> | Channel       | Telegram, Discord, Slack, WhatsApp    | Where messages enter and leave OpenClaw.                            |

| 层            | 例子                                  | 含义                                                                  |
| ------------- | ------------------------------------- | --------------------------------------------------------------------- |
| Provider      | `openai`、`anthropic`、`openai-codex` | OpenClaw 怎么认证、怎么发现模型、怎么命名模型引用。                   |
| Model         | `gpt-5.5`、`claude-opus-4-6`          | 这次 agent 轮次选的模型。                                             |
| Agent runtime | `pi`、`codex`、`claude-cli`           | 执行已准备好轮次的底层循环或后端。                                    |
| Channel       | Telegram、Discord、Slack、WhatsApp    | 消息进出 OpenClaw 的地方。                                            |

> You will also see the word **harness** in code. A harness is the implementation that provides an agent runtime. For example, the bundled Codex harness implements the `codex` runtime. Public config uses `agentRuntime.id` on provider or model entries; whole-agent runtime keys are legacy and ignored. `openclaw doctor --fix` removes old whole-agent runtime pins and rewrites legacy runtime model refs to canonical provider/model refs plus model-scoped runtime policy where needed.

代码里还会看到 **harness** 这个词。harness 是某个 agent runtime 的具体实现。比如内置的 Codex harness 实现了 `codex` runtime。公开配置在 provider 或 model 条目上用 `agentRuntime.id`；整 agent 级的 runtime key 是旧的、会被忽略。`openclaw doctor --fix` 会去掉旧的整 agent runtime 钉定，把旧的 runtime model 引用改写成标准的 provider/model 引用 + 必要时按 model 作用域的 runtime policy。

> There are two runtime families:
>
> * **Embedded harnesses** run inside OpenClaw's prepared agent loop. Today this is the built-in `pi` runtime plus registered plugin harnesses such as `codex`.
> * **CLI backends** run a local CLI process while keeping the model ref canonical. For example, `anthropic/claude-opus-4-7` with a model-scoped `agentRuntime.id: "claude-cli"` means "select the Anthropic model, execute through Claude CLI." `claude-cli` is not an embedded harness id and must not be passed to AgentHarness selection.

runtime 分两类：

- **嵌入式 harness**：跑在 OpenClaw 准备好的 agent 循环里。当前包括内置的 `pi` runtime 和已注册的插件 harness（比如 `codex`）。
- **CLI 后端**：跑一个本地 CLI 进程，但 model 引用保持标准形态。例如 `anthropic/claude-opus-4-7` 加一个 model 作用域的 `agentRuntime.id: "claude-cli"` 意思是"选 Anthropic 模型，通过 Claude CLI 执行"。`claude-cli` 不是嵌入式 harness id，不能传给 AgentHarness 选择器。

---

> ## Codex surfaces

## Codex 涉及的几个面

> Most confusion comes from several different surfaces sharing the Codex name:

大部分混乱来自几个不同的东西都叫 Codex：

> | Surface                                          | OpenClaw name/config                 | What it does                                                                                                   |
> | ------------------------------------------------ | ------------------------------------ | -------------------------------------------------------------------------------------------------------------- |
> | Native Codex app-server runtime                  | `openai/*` model refs                | Runs OpenAI embedded agent turns through Codex app-server. This is the usual ChatGPT/Codex subscription setup. |
> | Codex OAuth auth profiles                        | `openai-codex` auth provider         | Stores ChatGPT/Codex subscription auth that the Codex app-server harness consumes.                             |
> | Codex ACP adapter                                | `runtime: "acp"`, `agentId: "codex"` | Runs Codex through the external ACP/acpx control plane. Use only when ACP/acpx is explicitly asked.            |
> | Native Codex chat-control command set            | `/codex ...`                         | Binds, resumes, steers, stops, and inspects Codex app-server threads from chat.                                |
> | OpenAI Platform API route for non-agent surfaces | `openai/*` plus API-key auth         | Used for direct OpenAI APIs such as images, embeddings, speech, and realtime.                                  |

| 涉及面                                       | OpenClaw 里的名字 / 配置             | 作用                                                                                                |
| -------------------------------------------- | ------------------------------------ | --------------------------------------------------------------------------------------------------- |
| 原生 Codex app-server runtime                | `openai/*` 模型引用                  | 通过 Codex app-server 跑 OpenAI 的嵌入式 agent 轮次。这是常见的 ChatGPT / Codex 订阅部署。          |
| Codex OAuth 认证 profile                     | `openai-codex` auth provider         | 保存 ChatGPT / Codex 订阅认证，Codex app-server harness 用它。                                      |
| Codex ACP 适配器                             | `runtime: "acp"`、`agentId: "codex"` | 通过外部 ACP / acpx 控制面跑 Codex。只在用户明确要 ACP / acpx 时用。                                |
| 原生 Codex 聊天控制命令集                    | `/codex ...`                         | 在聊天里绑定、恢复、转向、停止、查看 Codex app-server 线程。                                        |
| 非 agent 用途的 OpenAI Platform API 路由     | `openai/*` 加 API key 认证           | 用于直连 OpenAI API，比如图像、embedding、语音、realtime。                                          |

> Those surfaces are intentionally independent. Enabling the `codex` plugin makes the native app-server features available; `openclaw doctor --fix` owns legacy `openai-codex/*` route repair and stale session pin cleanup. Selecting `openai/*` for an agent model now means "run this through Codex" unless a non-agent OpenAI API surface is being used.

这几面有意做成相互独立。启用 `codex` 插件让原生 app-server 功能可用；`openclaw doctor --fix` 负责修旧的 `openai-codex/*` 路由和清理过期会话钉定。给 agent 模型选 `openai/*` 现在意味着"通过 Codex 跑这个" —— 除非用的是非 agent 用途的 OpenAI API 面。

> The common ChatGPT/Codex subscription setup uses Codex OAuth for auth, but keeps the model ref as `openai/*` and selects the `codex` runtime:
>
> ```json5
> {
>   agents: {
>     defaults: {
>       model: "openai/gpt-5.5",
>     },
>   },
> }
> ```

常见的 ChatGPT / Codex 订阅部署用 Codex OAuth 认证，但 model 引用仍是 `openai/*`，选 `codex` runtime：

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

意思是 OpenClaw 选了一个 OpenAI 模型引用，然后让 Codex app-server runtime 跑嵌入式 agent 轮次。这并不意味着"用 API 计费"，也不意味着通道、模型 provider 目录或 OpenClaw 会话存储被 Codex 接管。

> When the bundled `codex` plugin is enabled, natural-language Codex control should use the native `/codex` command surface (`/codex bind`, `/codex threads`, `/codex resume`, `/codex steer`, `/codex stop`) instead of ACP. Use ACP for Codex only when the user explicitly asks for ACP/acpx or is testing the ACP adapter path. Claude Code, Gemini CLI, OpenCode, Cursor, and similar external harnesses still use ACP.

启用了内置的 `codex` 插件后，自然语言的 Codex 控制应当用原生 `/codex` 命令（`/codex bind`、`/codex threads`、`/codex resume`、`/codex steer`、`/codex stop`），不要走 ACP。只有用户明确要 ACP / acpx 或测试 ACP 适配器路径时，Codex 才走 ACP。Claude Code、Gemini CLI、OpenCode、Cursor 这类外部 harness 仍然走 ACP。

> This is the agent-facing decision tree:
>
> 1. If the user asks for **Codex bind/control/thread/resume/steer/stop**, use the native `/codex` command surface when the bundled `codex` plugin is enabled.
> 2. If the user asks for **Codex as the embedded runtime** or wants the normal subscription-backed Codex agent experience, use `openai/<model>`.
> 3. If the user explicitly chooses **PI for an OpenAI model**, keep the model ref as `openai/<model>` and set provider/model runtime policy to `agentRuntime.id: "pi"`. A selected `openai-codex` auth profile is routed internally through PI's legacy Codex-auth transport.
> 4. If legacy config still contains **`openai-codex/*` model refs**, repair it to `openai/<model>` with `openclaw doctor --fix`; doctor keeps the Codex auth route by adding provider/model-scoped `agentRuntime.id: "codex"` where the old model ref implied it. Legacy **`codex-cli/*` model refs** repair to the same `openai/<model>` Codex app-server route; OpenClaw no longer keeps a bundled Codex CLI backend.
> 5. If the user explicitly says **ACP**, **acpx**, or **Codex ACP adapter**, use ACP with `runtime: "acp"` and `agentId: "codex"`.
> 6. If the request is for **Claude Code, Gemini CLI, OpenCode, Cursor, Droid, or another external harness**, use ACP/acpx, not the native sub-agent runtime.

agent 视角的决策树：

1. 用户要 **Codex bind / control / thread / resume / steer / stop** 时，启用了内置 `codex` 插件就用原生 `/codex` 命令面。
2. 用户要 **Codex 作为嵌入式 runtime**，或者想要常规订阅版 Codex agent 体验，用 `openai/<model>`。
3. 用户明确选 **OpenAI 模型走 PI** 时，model 引用保留为 `openai/<model>`，把 provider/model 运行时策略设为 `agentRuntime.id: "pi"`。选定 `openai-codex` 认证 profile 时，会内部走 PI 的旧版 Codex-auth 传输。
4. 旧配置里仍有 **`openai-codex/*` 模型引用**时，用 `openclaw doctor --fix` 修成 `openai/<model>`；旧引用隐含了 Codex 路由的话，doctor 会加一条按 provider/model 作用域的 `agentRuntime.id: "codex"`。旧的 **`codex-cli/*` 模型引用**也修成同样的 `openai/<model>` Codex app-server 路由；OpenClaw 不再保留内置的 Codex CLI 后端。
5. 用户明确说 **ACP**、**acpx** 或 **Codex ACP 适配器**时，用 ACP，配 `runtime: "acp"` 和 `agentId: "codex"`。
6. 请求是 **Claude Code、Gemini CLI、OpenCode、Cursor、Droid 或其他外部 harness** 时，走 ACP / acpx，不要走原生 sub-agent runtime。

> | You mean...                             | Use...                                       |
> | --------------------------------------- | -------------------------------------------- |
> | Codex app-server chat/thread control    | `/codex ...` from the bundled `codex` plugin |
> | Codex app-server embedded agent runtime | `openai/*` agent model refs                  |
> | OpenAI Codex OAuth                      | `openai-codex` auth profiles                 |
> | Claude Code or other external harness   | ACP/acpx                                     |

| 你想要的是...                                | 用...                                              |
| -------------------------------------------- | -------------------------------------------------- |
| Codex app-server 聊天 / 线程控制             | 内置 `codex` 插件提供的 `/codex ...`               |
| Codex app-server 嵌入式 agent runtime        | `openai/*` agent 模型引用                          |
| OpenAI Codex OAuth                           | `openai-codex` 认证 profile                        |
| Claude Code 或其他外部 harness               | ACP / acpx                                         |

> For the OpenAI-family prefix split, see [OpenAI](/providers/openai) and [Model providers](/concepts/model-providers). For the Codex runtime support contract, see [Codex harness runtime](/plugins/codex-harness-runtime#v1-support-contract).

OpenAI 系列前缀的划分见 [OpenAI](/providers/openai) 和 [Model providers](/concepts/model-providers)。Codex runtime 的支持契约见 [Codex harness runtime](/plugins/codex-harness-runtime#v1-support-contract)。

---

> ## Runtime ownership

## 运行时的归属

> Different runtimes own different amounts of the loop.

不同 runtime 拥有循环里不同部分。

> | Surface                     | OpenClaw PI embedded                    | Codex app-server                                                            |
> | --------------------------- | --------------------------------------- | --------------------------------------------------------------------------- |
> | Model loop owner            | OpenClaw through the PI embedded runner | Codex app-server                                                            |
> | Canonical thread state      | OpenClaw transcript                     | Codex thread, plus OpenClaw transcript mirror                               |
> | OpenClaw dynamic tools      | Native OpenClaw tool loop               | Bridged through the Codex adapter                                           |
> | Native shell and file tools | PI/OpenClaw path                        | Codex-native tools, bridged through native hooks where supported            |
> | Context engine              | Native OpenClaw context assembly        | OpenClaw projects assembled context into the Codex turn                     |
> | Compaction                  | OpenClaw or selected context engine     | Codex-native compaction, with OpenClaw notifications and mirror maintenance |
> | Channel delivery            | OpenClaw                                | OpenClaw                                                                    |

| 涉及面                       | OpenClaw PI 嵌入式                    | Codex app-server                                                            |
| ---------------------------- | ------------------------------------- | --------------------------------------------------------------------------- |
| 模型循环归属                 | OpenClaw 通过 PI 嵌入式 runner        | Codex app-server                                                            |
| 标准线程状态                 | OpenClaw transcript                   | Codex 线程 + OpenClaw transcript 镜像                                       |
| OpenClaw 动态工具            | OpenClaw 原生工具循环                 | 通过 Codex 适配器桥接                                                       |
| 原生 shell 和文件工具        | PI / OpenClaw 路径                    | Codex 原生工具，支持的部分通过 native hook 桥接                             |
| 上下文引擎                   | OpenClaw 原生上下文组装               | OpenClaw 把组装好的上下文投射到 Codex 轮次里                                |
| 压缩                         | OpenClaw 或所选上下文引擎             | Codex 原生压缩，OpenClaw 收通知并维护镜像                                   |
| 通道投递                     | OpenClaw                              | OpenClaw                                                                    |

> This ownership split is the main design rule:
>
> * If OpenClaw owns the surface, OpenClaw can provide normal plugin hook behavior.
> * If the native runtime owns the surface, OpenClaw needs runtime events or native hooks.
> * If the native runtime owns canonical thread state, OpenClaw should mirror and project context, not rewrite unsupported internals.

这种归属切分是主要设计原则：

- OpenClaw 拥有的部分，可以提供正常的插件钩子行为。
- 原生 runtime 拥有的部分，OpenClaw 要靠 runtime 事件或 native hook。
- 原生 runtime 拥有标准线程状态时，OpenClaw 应该做镜像和上下文投射，不要去改写它不支持的内部结构。

---

> ## Runtime selection

## runtime 选择

> OpenClaw chooses an embedded runtime after provider and model resolution:

OpenClaw 在解析完 provider 和 model 之后挑选嵌入式 runtime：

> 1. Model-scoped runtime policy wins. This can live in a configured provider model entry or in `agents.defaults.models["provider/model"].agentRuntime` / `agents.list[].models["provider/model"].agentRuntime`. A provider wildcard such as `agents.defaults.models["vllm/*"].agentRuntime` applies after exact model policy, so dynamically discovered provider models can share one runtime without overriding exact per-model exceptions.
> 2. Provider-scoped runtime policy comes next at `models.providers.<provider>.agentRuntime`.
> 3. In `auto` mode, registered plugin runtimes can claim supported provider/model pairs.
> 4. If no runtime claims a turn in `auto` mode, OpenClaw uses PI as the compatibility runtime. Use an explicit runtime id when the run must be strict.

1. model 作用域的 runtime 策略优先。它可以放在某个已配置 provider 的 model 条目里，也可以放在 `agents.defaults.models["provider/model"].agentRuntime` / `agents.list[].models["provider/model"].agentRuntime`。`agents.defaults.models["vllm/*"].agentRuntime` 这种 provider 通配在精确 model 策略之后生效，这样动态发现的 provider 模型可以共享一个 runtime，又不覆盖精确的按 model 例外。
2. 接着是 provider 作用域的 runtime 策略：`models.providers.<provider>.agentRuntime`。
3. `auto` 模式下，已注册的插件 runtime 可以认领它支持的 provider/model 对。
4. `auto` 模式下没人认领时，OpenClaw 用 PI 作为兼容 runtime。需要严格行为时用显式 runtime id。

> Whole-session and whole-agent runtime pins are ignored. That includes `OPENCLAW_AGENT_RUNTIME`, session `agentHarnessId`/`agentRuntimeOverride` state, `agents.defaults.agentRuntime`, and `agents.list[].agentRuntime`. Run `openclaw doctor --fix` to remove stale whole-agent runtime config and convert legacy runtime model refs where OpenClaw can preserve the intent.

整 session 和整 agent 级的 runtime 钉定都会被忽略。包括 `OPENCLAW_AGENT_RUNTIME`、会话里的 `agentHarnessId` / `agentRuntimeOverride` 状态、`agents.defaults.agentRuntime`、`agents.list[].agentRuntime`。跑 `openclaw doctor --fix` 移除过期的整 agent runtime 配置，并在能保留语义的地方把旧 runtime 模型引用转换过来。

> Explicit provider/model plugin runtimes fail closed. For example, `agentRuntime.id: "codex"` on a provider or model means Codex or a clear selection/runtime error; it is never silently routed back to PI.

显式的 provider/model 插件 runtime 是 fail-closed 的。比如在 provider 或 model 上写 `agentRuntime.id: "codex"`，要么走 Codex，要么报清晰的选择 / runtime 错误，绝不会悄悄回退到 PI。

> CLI backend aliases are different from embedded harness ids. The preferred Claude CLI form is:
>
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

CLI 后端别名跟嵌入式 harness id 不是一回事。Claude CLI 推荐写法：

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

旧引用比如 `claude-cli/claude-opus-4-7` 仍然兼容，但新配置应该让 provider/model 保持标准形式，把执行后端写到 provider/model 的 runtime 策略里。

> Legacy `codex-cli/*` refs are different: doctor migrates them to `openai/*` so they run through the Codex app-server harness instead of preserving a Codex CLI backend.

旧的 `codex-cli/*` 引用不一样：doctor 会把它们迁移到 `openai/*`，这样它们走 Codex app-server harness 跑，而不是保留 Codex CLI 后端。

> `auto` mode is intentionally conservative for most providers. OpenAI agent models are the exception: unset runtime and `auto` both resolve to the Codex harness. Explicit PI runtime config remains an opt-in compatibility route for `openai/*` agent turns; when paired with a selected `openai-codex` auth profile, OpenClaw routes PI internally through the legacy Codex-auth transport while keeping the public model ref as `openai/*`. Stale OpenAI PI session pins are ignored by runtime selection and can be cleaned with `openclaw doctor --fix`.

`auto` 模式对大部分 provider 故意保守。OpenAI agent 模型是例外：runtime 没设和 `auto` 都解析到 Codex harness。`openai/*` agent 轮次想用 PI 走兼容路径时，仍然可以显式配 PI runtime；选定 `openai-codex` 认证 profile 时，OpenClaw 内部把 PI 走旧版 Codex-auth 传输，公开的 model 引用仍是 `openai/*`。过期的 OpenAI PI 会话钉定在 runtime 选择时被忽略，可以用 `openclaw doctor --fix` 清理。

> If `openclaw doctor` warns that the `codex` plugin is enabled while `openai-codex/*` remains in config, treat that as legacy route state. Run `openclaw doctor --fix` to rewrite it to `openai/*` with the Codex runtime.

如果 `openclaw doctor` 警告说 `codex` 插件开了但配置里还有 `openai-codex/*`，把它当成旧路由状态处理。跑 `openclaw doctor --fix` 把它改写成 `openai/*` + Codex runtime。

---

> ## Compatibility contract

## 兼容契约

> When a runtime is not PI, it should document what OpenClaw surfaces it supports.
> Use this shape for runtime docs:

非 PI 的 runtime 应当在文档里说明它支持哪些 OpenClaw 面。runtime 文档按这套问题写：

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

| 问题                              | 为什么重要                                                                                       |
| --------------------------------- | ------------------------------------------------------------------------------------------------ |
| 谁拥有模型循环？                  | 决定重试、工具继续、最终答案这些决策发生在哪里。                                                 |
| 谁拥有标准线程历史？              | 决定 OpenClaw 是能改历史，还是只能镜像它。                                                       |
| OpenClaw 动态工具能用吗？         | 消息、会话、cron 和 OpenClaw 自己的工具都依赖这个。                                              |
| 动态工具钩子能用吗？              | 插件期望在 OpenClaw 自己的工具周围有 `before_tool_call`、`after_tool_call` 和 middleware。       |
| 原生工具钩子能用吗？              | shell、patch 和 runtime 自有工具需要 native hook 支持，用于策略和观察。                          |
| 上下文引擎生命周期会跑吗？        | 记忆和上下文插件依赖 assemble、ingest、after-turn、compaction 生命周期。                         |
| 压缩暴露了哪些数据？              | 有些插件只要通知，有些要保留 / 丢弃元数据。                                                      |
| 哪些是有意不支持的？              | 原生 runtime 拥有更多状态时，用户不应假设跟 PI 等价。                                            |

> The Codex runtime support contract is documented in [Codex harness runtime](/plugins/codex-harness-runtime#v1-support-contract).

Codex runtime 的支持契约文档见 [Codex harness runtime](/plugins/codex-harness-runtime#v1-support-contract)。

---

> ## Status labels

## 状态标签

> Status output may show both `Execution` and `Runtime` labels. Read them as diagnostics, not as provider names.

status 输出里可能同时有 `Execution` 和 `Runtime` 标签。把它们当作诊断信息看，不是 provider 名字。

> * A model ref such as `openai/gpt-5.5` tells you the selected provider/model.
> * A runtime id such as `codex` tells you which loop is executing the turn.
> * A channel label such as Telegram or Discord tells you where the conversation is happening.

- 像 `openai/gpt-5.5` 这种 model 引用告诉你选了哪个 provider/model。
- 像 `codex` 这种 runtime id 告诉你哪个循环在执行这一轮。
- 像 Telegram、Discord 这种 channel 标签告诉你对话在哪里发生。

> If a run still shows an unexpected runtime, inspect the selected provider/model runtime policy first. Legacy session runtime pins no longer decide routing.

某次运行的 runtime 不符合预期时，先看选定的 provider/model runtime 策略。旧版 session runtime 钉定不再决定路由。

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
- [模型](/concepts/models)
- [Status](/cli/status)
