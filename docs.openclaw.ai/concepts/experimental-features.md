# Experimental features

> Experimental features in OpenClaw are **opt-in preview surfaces**. They are behind explicit flags because they still need real-world mileage before they deserve a stable default or a long-lived public contract.

OpenClaw 里的实验功能是**显式启用的预览特性**。它们藏在显式开关后面，因为还需要更多实战检验，才配得上稳定默认值或长期公开契约。

> Treat them differently from normal config:
>
> * Keep them **off by default** unless the related doc tells you to try one.
> * Expect **shape and behavior to change** faster than stable config.
> * Prefer the stable path first when one already exists.
> * If you are rolling OpenClaw out broadly, test experimental flags in a smaller environment before baking them into a shared baseline.

跟普通配置不同对待：

- 除非相关文档让你试，否则**默认关掉**。
- 预期它的**形状和行为**比稳定配置变得更快。
- 已经有稳定路径的，优先用稳定路径。
- 在大范围铺开 OpenClaw 时，先在小范围环境里测试实验开关，再把它写进共享基线。

---

> ## Currently documented flags

## 当前有文档的开关

> | Surface                  | Key                                                       | Use it when                                                                                                    | More                                                                                          |
> | ------------------------ | --------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------- |
> | Local model runtime      | `agents.defaults.experimental.localModelLean`             | A smaller or stricter local backend chokes on OpenClaw's full default tool surface                             | [Local Models](/gateway/local-models)                                                         |
> | Memory search            | `agents.defaults.memorySearch.experimental.sessionMemory` | You want `memory_search` to index prior session transcripts and accept the extra storage/indexing cost         | [Memory configuration reference](/reference/memory-config#session-memory-search-experimental) |
> | Structured planning tool | `tools.experimental.planTool`                             | You want the structured `update_plan` tool exposed for multi-step work tracking in compatible runtimes and UIs | [Gateway configuration reference](/gateway/config-tools#toolsexperimental)                    |

| 涉及面                | Key                                                       | 适合开启的场景                                                                                  | 更多                                                                                          |
| --------------------- | --------------------------------------------------------- | ----------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------- |
| 本地模型运行时        | `agents.defaults.experimental.localModelLean`             | 较小或较严格的本地后端被 OpenClaw 完整默认工具面卡住                                            | [本地模型](/gateway/local-models)                                                             |
| 记忆搜索              | `agents.defaults.memorySearch.experimental.sessionMemory` | 你希望 `memory_search` 索引以往的会话 transcript，并能接受额外的存储 / 索引成本                 | [记忆配置参考](/reference/memory-config#session-memory-search-experimental)                    |
| 结构化计划工具        | `tools.experimental.planTool`                             | 你希望在兼容的 runtime 和 UI 里暴露结构化的 `update_plan` 工具来追踪多步工作                    | [Gateway 配置参考](/gateway/config-tools#toolsexperimental)                                   |

---

> ## Local model lean mode

## 本地模型精简模式

> `agents.defaults.experimental.localModelLean: true` is a pressure-release valve for weaker local-model setups. When it is on, OpenClaw drops three default tools — `browser`, `cron`, and `message` — from the agent's tool surface for every turn. Nothing else changes.

`agents.defaults.experimental.localModelLean: true` 是给弱本地模型部署留的一个泄压阀。打开它后，OpenClaw 在每一轮里把三个默认工具 ——`browser`、`cron`、`message` —— 从 agent 工具面里去掉。其他什么都不变。

> ### Why these three tools

### 为什么是这三个工具

> These three tools have the largest descriptions and the most parameter shapes in the default OpenClaw runtime. On a small-context or stricter OpenAI-compatible backend that is the difference between:
>
> * Tool schemas fitting cleanly in the prompt vs. crowding out conversation history.
> * The model picking the right tool vs. emitting malformed tool calls because there are too many similar-looking schemas.
> * The Chat Completions adapter staying inside the server's structured-output limits vs. tripping a 400 on tool-call payload size.

这三个在 OpenClaw 默认 runtime 里描述最大、参数形状最多。在小上下文或较严格的 OpenAI 兼容后端上，这就是这三件事的分水岭：

- 工具 schema 能干净塞进 prompt vs. 把对话历史挤掉。
- 模型挑对工具 vs. 因为相似 schema 太多而生成畸形的工具调用。
- Chat Completions 适配器留在服务端的结构化输出上限内 vs. 因为工具调用载荷太大而触发 400。

> Removing them does not silently rewire OpenClaw — it just makes the tool list shorter. The model still has `read`, `write`, `edit`, `exec`, `apply_patch`, web search/fetch (when configured), memory, and session/agent tools available.

去掉它们并不会悄悄重接 OpenClaw —— 只是让工具列表变短。`read`、`write`、`edit`、`exec`、`apply_patch`、web 搜索 / fetch（已配置时）、memory、session / agent 工具都还在。

> ### When to turn it on

### 什么时候开

> Enable lean mode when you have already proved the model can talk to the Gateway but full agent turns misbehave. The typical signal chain is:
>
> 1. `openclaw infer model run --gateway --model <ref> --prompt "Reply with exactly: pong"` succeeds.
> 2. A normal agent turn fails with malformed tool calls, oversized prompts, or the model ignoring its tools.
> 3. Toggling `localModelLean: true` clears the failure.

已经验证模型能跟 Gateway 通信，但完整 agent 轮次行为不对劲时，开精简模式。典型信号链：

1. `openclaw infer model run --gateway --model <ref> --prompt "Reply with exactly: pong"` 成功。
2. 普通 agent 轮次失败：畸形工具调用、prompt 过大或模型无视工具。
3. 把 `localModelLean: true` 打开就清掉了这个故障。

> ### When to leave it off

### 什么时候保持关闭

> If your backend handles the full default runtime cleanly, leave this off. Lean mode is a workaround, not a default. It exists because some local stacks need a smaller tool surface to behave; hosted models and well-resourced local rigs do not.

如果后端能干净处理完整默认 runtime，就保持关闭。精简模式是一个绕开方案，不是默认值。它存在是因为有些本地栈需要更小的工具面才能正常工作；托管模型和资源充足的本地机器并不需要它。

> Lean mode also does not replace `tools.profile`, `tools.allow`/`tools.deny`, or the model `compat.supportsTools: false` escape hatch. If you need a permanent narrower tool surface for a specific agent, prefer those stable knobs over the experimental flag.

精简模式也不会替代 `tools.profile`、`tools.allow` / `tools.deny`，或模型的 `compat.supportsTools: false` 这道逃生口。某个 agent 需要长期更窄的工具面时，优先用那些稳定开关，而不是实验开关。

> ### Enable

### 启用

> ```json5
> {
>   agents: {
>     defaults: {
>       experimental: {
>         localModelLean: true,
>       },
>     },
>   },
> }
> ```

```json5
{
  agents: {
    defaults: {
      experimental: {
        localModelLean: true,
      },
    },
  },
}
```

> Restart the Gateway after changing the flag, then confirm the trimmed tool list with:
>
> ```bash
> openclaw status --deep
> ```

改完开关重启 Gateway，然后确认裁剪后的工具列表：

```bash
openclaw status --deep
```

> The deep status output lists the active agent tools; `browser`, `cron`, and `message` should be absent when lean mode is on.

deep status 输出会列出活跃 agent 工具；精简模式开着时，`browser`、`cron`、`message` 应当看不到。

---

> ## Experimental does not mean hidden

## 实验性 ≠ 藏起来

> If a feature is experimental, OpenClaw should say so plainly in docs and in the config path itself. What it should **not** do is smuggle preview behavior into a stable-looking default knob and pretend that is normal. That's how config surfaces get messy.

如果一个功能是实验性的，OpenClaw 应该在文档里和配置路径本身上把这件事讲清楚。**不应该**做的是把预览行为偷偷塞进一个看起来稳定的默认开关，假装这很正常。配置面就是这么变乱的。

---

> ## Related

## 相关

> * [Features](/concepts/features)
> * [Release channels](/install/development-channels)

- [功能特性](/concepts/features)
- [发布通道](/install/development-channels)
