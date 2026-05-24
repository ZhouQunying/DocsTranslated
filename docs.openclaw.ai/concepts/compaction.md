# Compaction

> Every model has a context window: the maximum number of tokens it can process. When a conversation approaches that limit, OpenClaw **compacts** older messages into a summary so the chat can continue.

每个模型都有上下文窗口：能处理的最大 token 数。对话接近这个上限时，OpenClaw 会**压缩**旧消息成摘要，让对话能继续。

---

> ## How it works

## 工作原理

> 1. Older conversation turns are summarized into a compact entry.
> 2. The summary is saved in the session transcript.
> 3. Recent messages are kept intact.

1. 较早的对话轮次概括成一条紧凑条目。
2. 摘要写到会话对话记录里。
3. 最近的消息保持不动。

> When OpenClaw splits history into compaction chunks, it keeps assistant tool calls paired with their matching `toolResult` entries. If a split point lands inside a tool block, OpenClaw moves the boundary so the pair stays together and the current unsummarized tail is preserved.

OpenClaw 把历史分成压缩块时，让 assistant 工具调用和对应的 `toolResult` 条目成对保留。切分点落在工具块里时，OpenClaw 会移动边界，让这一对待在一起、当前未概括的尾部保留下来。

> The full conversation history stays on disk. Compaction only changes what the model sees on the next turn.

完整对话历史留在磁盘上。压缩只改变模型下一轮看到什么。

---

> ## Auto-compaction

## 自动压缩

> Auto-compaction is on by default. It runs when the session nears the context limit, or when the model returns a context-overflow error (in which case OpenClaw compacts and retries).

自动压缩默认开。会话接近上下文上限时，或模型返回上下文溢出错误时（此时 OpenClaw 压缩后重试）触发。

> You will see:
>
> * `embedded run auto-compaction start` / `complete` in normal Gateway logs.
> * `🧹 Auto-compaction complete` in verbose mode.
> * `/status` showing `🧹 Compactions: <count>`.

你会看到：

- 常规 Gateway 日志里的 `embedded run auto-compaction start` / `complete`。
- verbose 模式下的 `🧹 Auto-compaction complete`。
- `/status` 里显示 `🧹 Compactions: <次数>`。

> <Info>
>   Before compacting, OpenClaw automatically reminds the agent to save important notes to [memory](/concepts/memory) files. This prevents context loss.
> </Info>

> **说明**：压缩之前，OpenClaw 自动提醒 agent 把重要笔记存到 [记忆](/concepts/memory) 文件里，防止丢上下文。

> [展开: Recognized overflow signatures]
>
> OpenClaw detects context overflow from these provider error patterns:
>
> * `request_too_large`
> * `context length exceeded`
> * `input exceeds the maximum number of tokens`
> * `input token count exceeds the maximum number of input tokens`
> * `input is too long for the model`
> * `ollama error: context length exceeded`

[展开：识别的溢出特征]

OpenClaw 从这些 provider 错误模式里检测上下文溢出：

- `request_too_large`
- `context length exceeded`
- `input exceeds the maximum number of tokens`
- `input token count exceeds the maximum number of input tokens`
- `input is too long for the model`
- `ollama error: context length exceeded`

---

> ## Manual compaction

## 手动压缩

> Type `/compact` in any chat to force a compaction. Add instructions to guide the summary:
>
> ```
> /compact Focus on the API design decisions
> ```

任意聊天里发 `/compact` 强制压缩。加指令引导摘要：

```
/compact Focus on the API design decisions
```

> When `agents.defaults.compaction.keepRecentTokens` is set, manual compaction honors that Pi cut-point and keeps the recent tail in rebuilt context. Without an explicit keep budget, manual compaction behaves as a hard checkpoint and continues from the new summary alone.

设了 `agents.defaults.compaction.keepRecentTokens` 时，手动压缩遵守这个 Pi 切点，把最近的尾部保留在重建的上下文里。没显式 keep 预算时，手动压缩当作一个硬 checkpoint，从新摘要起继续。

---

> ## Configuration

## 配置

> Configure compaction under `agents.defaults.compaction` in your `openclaw.json`. The most common knobs are listed below; for the full reference, see [Session management deep dive](/reference/session-management-compaction).

在 `openclaw.json` 的 `agents.defaults.compaction` 下配置压缩。最常用的开关列在下面；完整参考见 [会话管理深入](/reference/session-management-compaction)。

> ### Using a different model

### 用别的模型

> By default, compaction uses the agent's primary model. Set `agents.defaults.compaction.model` to delegate summarization to a more capable or specialized model. The override accepts any `provider/model-id` string:

默认压缩用 agent 的主模型。设 `agents.defaults.compaction.model` 把摘要委派给更强或更专业的模型。覆盖接受任何 `provider/model-id` 字符串：

> ```json
> {
>   "agents": {
>     "defaults": {
>       "compaction": {
>         "model": "openrouter/anthropic/claude-sonnet-4-6"
>       }
>     }
>   }
> }
> ```

```json
{
  "agents": {
    "defaults": {
      "compaction": {
        "model": "openrouter/anthropic/claude-sonnet-4-6"
      }
    }
  }
}
```

> This works with local models too, for example a second Ollama model dedicated to summarization:

本地模型也行，比如一个专做摘要的第二个 Ollama 模型：

> ```json
> {
>   "agents": {
>     "defaults": {
>       "compaction": {
>         "model": "ollama/llama3.1:8b"
>       }
>     }
>   }
> }
> ```

```json
{
  "agents": {
    "defaults": {
      "compaction": {
        "model": "ollama/llama3.1:8b"
      }
    }
  }
}
```

> When unset, compaction starts with the active session model. If summarization fails with a model-fallback-eligible provider error, OpenClaw retries that compaction attempt through the session's existing model fallback chain. The fallback choice is temporary and is not written back to session state. An explicit `agents.defaults.compaction.model` override remains exact and does not inherit the session fallback chain.

不设的话，压缩从当前会话模型开始。摘要因为可走模型回退的 provider 错误失败时，OpenClaw 通过会话已有的模型回退链重试该次压缩。回退选择是临时的，不会写回会话状态。显式设的 `agents.defaults.compaction.model` 覆盖是精确值，不继承会话回退链。

> ### Identifier preservation

### 标识符保留

> Compaction summarization preserves opaque identifiers by default (`identifierPolicy: "strict"`). Override with `identifierPolicy: "off"` to disable, or `identifierPolicy: "custom"` plus `identifierInstructions` for custom guidance.

压缩摘要默认保留不透明的标识符（`identifierPolicy: "strict"`）。设 `identifierPolicy: "off"` 关闭，或 `identifierPolicy: "custom"` 加 `identifierInstructions` 给自定义指引。

> ### Active transcript byte guard

### 活动 transcript 字节守卫

> When `agents.defaults.compaction.maxActiveTranscriptBytes` is set, OpenClaw triggers normal local compaction before a run if the active JSONL reaches that size. This is useful for long-running sessions where provider-side context management may keep model context healthy while the local transcript keeps growing. It does not split raw JSONL bytes; it asks the normal compaction pipeline to create a semantic summary.

设了 `agents.defaults.compaction.maxActiveTranscriptBytes` 时，活动 JSONL 达到这个大小，OpenClaw 在运行前触发常规本地压缩。这对长运行会话有用 ——provider 端的上下文管理可能让模型上下文健康，但本地对话记录仍在增长。它不切原始 JSONL 字节；它让常规压缩流水线生成一份语义摘要。

> <Warning>
>   The byte guard requires `truncateAfterCompaction: true`. Without transcript rotation, the active file would not shrink and the guard remains inactive.
> </Warning>

> **警告**：字节守卫要求 `truncateAfterCompaction: true`。没有 transcript 轮换的话，活动文件不会缩小，守卫一直不激活。

> ### Successor transcripts

### 后继 transcript

> When `agents.defaults.compaction.truncateAfterCompaction` is enabled, OpenClaw does not rewrite the existing transcript in place. It creates a new active successor transcript from the compaction summary, preserved state, and unsummarized tail, then keeps the previous JSONL as the archived checkpoint source.
> Successor transcripts also drop exact duplicate long user turns that arrive inside a short retry window, so channel retry storms are not carried into the next active transcript after compaction.

启用 `agents.defaults.compaction.truncateAfterCompaction` 时，OpenClaw 不会原地改写已有对话记录。它从压缩摘要、保留状态和未概括的尾部建一份新的活动后继对话记录，把之前的 JSONL 留作归档的 checkpoint 源。
后继对话记录还会丢掉短重试窗口内到达的、字面上完全重复的长 user 轮次，避免通道重试风暴被带进压缩后的下一个活动对话记录。

> Pre-compaction checkpoints are retained only while they stay below OpenClaw's checkpoint size cap; oversized active transcripts still compact, but OpenClaw skips the large debug snapshot instead of doubling disk usage.

只在低于 OpenClaw 的 checkpoint 大小上限时才保留压缩前 checkpoint；超大的活动对话记录仍然压缩，但 OpenClaw 跳过大体积的调试快照，避免占用双倍磁盘。

> ### Compaction notices

### 压缩通知

> By default, compaction runs silently. Set `notifyUser` to show brief status messages when compaction starts and completes:

默认压缩静默运行。设 `notifyUser` 在压缩开始和完成时显示简短状态消息：

> ```json5
> {
>   agents: {
>     defaults: {
>       compaction: {
>         notifyUser: true,
>       },
>     },
>   },
> }
> ```

```json5
{
  agents: {
    defaults: {
      compaction: {
        notifyUser: true,
      },
    },
  },
}
```

> ### Memory flush

### 记忆 flush

> Before compaction, OpenClaw can run a **silent memory flush** turn to store durable notes to disk. Set `agents.defaults.compaction.memoryFlush.model` when this housekeeping turn should use a local model instead of the active conversation model:

压缩之前，OpenClaw 可以跑一个**静默记忆 flush** 轮次，把长期笔记存到磁盘。这个家务轮次想用本地模型而非当前对话模型时，设 `agents.defaults.compaction.memoryFlush.model`：

> ```json
> {
>   "agents": {
>     "defaults": {
>       "compaction": {
>         "memoryFlush": {
>           "model": "ollama/qwen3:8b"
>         }
>       }
>     }
>   }
> }
> ```

```json
{
  "agents": {
    "defaults": {
      "compaction": {
        "memoryFlush": {
          "model": "ollama/qwen3:8b"
        }
      }
    }
  }
}
```

> The memory-flush model override is exact and does not inherit the active session fallback chain. See [Memory](/concepts/memory) for details and config.

memory-flush 的模型覆盖是精确值，不继承当前会话回退链。细节和配置见 [记忆](/concepts/memory)。

---

> ## Pluggable compaction providers

## 可插拔的压缩 provider

> Plugins can register a custom compaction provider via `registerCompactionProvider()` on the plugin API. When a provider is registered and configured, OpenClaw delegates summarization to it instead of the built-in LLM pipeline.

插件可以通过插件 API 的 `registerCompactionProvider()` 注册自定义压缩 provider。注册并配置之后，OpenClaw 把摘要委派给它，不走内置 LLM 流水线。

> To use a registered provider, set its id in your config:

要用一个已注册的 provider，在配置里设它的 id：

> ```json
> {
>   "agents": {
>     "defaults": {
>       "compaction": {
>         "provider": "my-provider"
>       }
>     }
>   }
> }
> ```

```json
{
  "agents": {
    "defaults": {
      "compaction": {
        "provider": "my-provider"
      }
    }
  }
}
```

> Setting a `provider` automatically forces `mode: "safeguard"`. Providers receive the same compaction instructions and identifier-preservation policy as the built-in path, and OpenClaw still preserves recent-turn and split-turn suffix context after provider output.

设了 `provider` 会自动强制 `mode: "safeguard"`。provider 收到的压缩指令和标识符保留策略跟内置路径一样；provider 输出后，OpenClaw 仍然保留最近轮次和切分轮次后缀上下文。

> <Note>
>   If the provider fails or returns an empty result, OpenClaw falls back to built-in LLM summarization.
> </Note>

> **提示**：provider 失败或返回空结果时，OpenClaw 回退到内置 LLM 摘要。

---

> ## Compaction vs pruning

## 压缩 vs 裁剪

> |                  | Compaction                    | Pruning                          |
> | ---------------- | ----------------------------- | -------------------------------- |
> | **What it does** | Summarizes older conversation | Trims old tool results           |
> | **Saved?**       | Yes (in session transcript)   | No (in-memory only, per request) |
> | **Scope**        | Entire conversation           | Tool results only                |

|                  | 压缩                              | 裁剪                                |
| ---------------- | --------------------------------- | ----------------------------------- |
| **做什么**       | 概括较早的对话                    | 裁剪老的工具结果                    |
| **保存吗？**     | 是（写到会话对话记录）         | 否（仅内存里，按请求）              |
| **范围**         | 整段对话                          | 只是工具结果                        |

> [Session pruning](/concepts/session-pruning) is a lighter-weight complement that trims tool output without summarizing.

[会话裁剪](/concepts/session-pruning) 是一个更轻的互补机制，不做摘要、只裁工具输出。

---

> ## Troubleshooting

## 故障排查

> **Compacting too often?** The model's context window may be small, or tool outputs may be large. Try enabling [session pruning](/concepts/session-pruning).

**压缩太频繁？** 模型的上下文窗口可能太小，或者工具输出太大。试试启用 [会话裁剪](/concepts/session-pruning)。

> **Context feels stale after compaction?** Use `/compact Focus on <topic>` to guide the summary, or enable the [memory flush](/concepts/memory) so notes survive.

**压缩后上下文感觉变陈旧？** 用 `/compact Focus on <主题>` 引导摘要；或者启用 [记忆 flush](/concepts/memory)，让笔记留下来。

> **Need a clean slate?** `/new` starts a fresh session without compacting.

**想要干净起步？** `/new` 起一个新会话，不做压缩。

> For advanced configuration (reserve tokens, identifier preservation, custom context engines, OpenAI server-side compaction), see the [Session management deep dive](/reference/session-management-compaction).

进阶配置（预留 token、标识符保留、自定义上下文引擎、OpenAI 服务端压缩）见 [会话管理深入](/reference/session-management-compaction)。

---

> ## Related

## 相关

> * [Session](/concepts/session): session management and lifecycle.
> * [Session pruning](/concepts/session-pruning): trimming tool results.
> * [Context](/concepts/context): how context is built for agent turns.
> * [Hooks](/automation/hooks): compaction lifecycle hooks (`before_compaction`, `after_compaction`).

- [会话](/concepts/session)：会话管理和生命周期。
- [会话裁剪](/concepts/session-pruning)：裁剪工具结果。
- [Context](/concepts/context)：agent 轮次的上下文怎么构建。
- [钩子](/automation/钩子)：压缩生命周期钩子（`before_compaction`、`after_compaction`）。
