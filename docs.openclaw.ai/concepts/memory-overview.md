# Memory overview

> OpenClaw remembers things by writing **plain Markdown files** in your agent's workspace. The model only "remembers" what gets saved to disk — there is no hidden state.

OpenClaw 通过在 agent 工作区里写**纯 Markdown 文件**来记事。模型只"记得"被存到磁盘上的内容 —— 没有任何隐藏状态。

---

> ## How it works

## 工作原理

> Your agent has three memory-related files:
>
> * **`MEMORY.md`** — long-term memory. Durable facts, preferences, and decisions. Loaded at the start of every DM session.
> * **`memory/YYYY-MM-DD.md`** (or **`memory/YYYY-MM-DD-<slug>.md`**) — daily notes. Running context and observations. Today and yesterday's notes are loaded automatically, and slugged variants such as those written by the bundled session-memory hook on `/new` or `/reset` are now picked up alongside the date-only file.
> * **`DREAMS.md`** (optional) — Dream Diary and dreaming sweep summaries for human review, including grounded historical backfill entries.

agent 有三类与记忆相关的文件：

- **`MEMORY.md`** —— 长期记忆。长期事实、偏好、决策。每个私聊会话开始时加载。
- **`memory/YYYY-MM-DD.md`**（或 **`memory/YYYY-MM-DD-<slug>.md`**）—— 日常笔记。当前上下文和观察。今天和昨天的笔记会自动加载；带 slug 的变体（比如内置 session-memory 钩子在 `/new` 或 `/reset` 时写出的）现在也会和只带日期的文件一起被识别。
- **`DREAMS.md`**（可选）—— 梦境日记和"做梦"扫描的总结，给人类查看，含 grounded 历史回填条目。

> These files live in the agent workspace (default `~/.openclaw/workspace`).

这些文件放在 agent 工作区（默认 `~/.openclaw/workspace`）。

---

> ## What goes where

## 各放什么内容

> `MEMORY.md` is the compact, curated layer. Use it for durable facts, preferences, standing decisions, and short summaries that should be available at the start of a main private session. It is not meant to be a raw transcript, daily log, or exhaustive archive.

`MEMORY.md` 是紧凑的、精选的一层。放长期事实、偏好、长期决策、应该在主私聊会话开头就能拿到的简短总结。它不是原始 transcript、日常日志或穷尽式归档。

> `memory/YYYY-MM-DD.md` files are the working layer. Use them for detailed daily notes, observations, session summaries, and raw context that may still be useful later. These files are indexed for `memory_search` and `memory_get`, but they are not injected into the normal bootstrap prompt on every turn.

`memory/YYYY-MM-DD.md` 是工作层。放详细的日常笔记、观察、会话总结，以及之后可能还有用的原始上下文。这些文件被 `memory_search` 和 `memory_get` 索引，但不会在每轮普通引导 prompt 里被注入。

> Over time, the agent is expected to distill useful material from daily notes into `MEMORY.md` and remove stale long-term entries. The generated workspace instructions and heartbeat flow can do that periodically; you do not need to manually edit `MEMORY.md` for every remembered detail.

随着时间推移，agent 应当把日常笔记里有用的东西提炼到 `MEMORY.md`，并清掉过期的长期条目。生成的工作区说明和心跳流可以定期做这件事；不必每个细节都手动改 `MEMORY.md`。

> If `MEMORY.md` grows past the bootstrap file budget, OpenClaw keeps the file on disk intact but truncates the copy injected into the model context. Treat that as a signal to move detailed material back into `memory/*.md`, keep only the durable summary in `MEMORY.md`, or raise the bootstrap limits if you explicitly want to spend more prompt budget. Use `/context list`, `/context detail`, or `openclaw doctor` to see raw vs injected sizes and truncation status.

`MEMORY.md` 长到超过引导文件预算时，OpenClaw 让磁盘上的文件保持完整，但截断注入到模型上下文里的副本。把这视为一个信号：把详细内容挪回 `memory/*.md`、`MEMORY.md` 里只留长期总结；或者你明确想多花 prompt 预算时调高引导上限。用 `/context list`、`/context detail` 或 `openclaw doctor` 看原始 vs 注入的大小和截断状态。

> <Tip>
>   If you want your agent to remember something, just ask it: "Remember that I prefer TypeScript." It will write it to the appropriate file.
> </Tip>

> **小贴士**：要让 agent 记一件事，直接说："记一下：我偏好 TypeScript。" 它会写到合适的文件里。

---

> ## Inferred commitments

## 推断出的承诺

> Some future follow-ups are not durable facts. If you mention an interview tomorrow, the useful memory may be "check in after the interview," not "store this forever in `MEMORY.md`."

有些未来的跟进不是长期事实。你提到明天有面试时，有用的记忆是"面试后跟进一下"，不是"永远存进 `MEMORY.md`"。

> [Commitments](/concepts/commitments) are opt-in, short-lived follow-up memories for that case. OpenClaw infers them in a hidden background pass, scopes them to the same agent and channel, and delivers due check-ins through heartbeat. Explicit reminders still use [scheduled tasks](/automation/cron-jobs).

[Commitments](/concepts/commitments) 是为这种场景设的、可选启用的短期跟进记忆。OpenClaw 在一个隐藏后台 pass 里推断它们，按 agent 和通道作用域，到期跟进通过心跳投递。显式提醒仍走 [定时任务](/automation/cron-jobs)。

---

> ## Memory tools

## 记忆工具

> The agent has two tools for working with memory:
>
> * **`memory_search`** — finds relevant notes using semantic search, even when the wording differs from the original.
> * **`memory_get`** — reads a specific memory file or line range.

agent 有两个用于操作记忆的工具：

- **`memory_search`**：用语义搜索找相关笔记，即便措辞跟原文不同也能找到。
- **`memory_get`**：读某个具体的记忆文件或行范围。

> Both tools are provided by the active memory plugin (default: `memory-core`).

两个工具都由当前激活的记忆插件提供（默认 `memory-core`）。

---

> ## Memory Wiki companion plugin

## Memory Wiki 配套插件

> If you want durable memory to behave more like a maintained knowledge base than just raw notes, use the bundled `memory-wiki` plugin.

希望长期记忆更像一份维护中的知识库，而不只是原始笔记时，用内置的 `memory-wiki` 插件。

> `memory-wiki` compiles durable knowledge into a wiki vault with:
>
> * deterministic page structure
> * structured claims and evidence
> * contradiction and freshness tracking
> * generated dashboards
> * compiled digests for agent/runtime consumers
> * wiki-native tools like `wiki_search`, `wiki_get`, `wiki_apply`, and `wiki_lint`

`memory-wiki` 把长期知识编译成 wiki vault，带：

- 确定的页面结构
- 结构化的 claim 和 evidence
- 矛盾和新鲜度追踪
- 自动生成的 dashboard
- 编译给 agent / runtime 使用方的摘要
- wiki 原生工具，如 `wiki_search`、`wiki_get`、`wiki_apply`、`wiki_lint`

> It does not replace the active memory plugin. The active memory plugin still owns recall, promotion, and dreaming. `memory-wiki` adds a provenance-rich knowledge layer beside it.

它不替代当前的记忆插件。当前记忆插件仍然管召回、晋升、做梦。`memory-wiki` 在它旁边加一层带溯源的知识层。

> See [Memory Wiki](/plugins/memory-wiki).

见 [Memory Wiki](/plugins/memory-wiki)。

---

> ## Memory search

## 记忆搜索

> When an embedding provider is configured, `memory_search` uses **hybrid search** — combining vector similarity (semantic meaning) with keyword matching (exact terms like IDs and code symbols). This works out of the box once you have an API key for any supported provider.

配了 embedding provider 后，`memory_search` 用**混合搜索** —— 向量相似度（语义）加关键词匹配（精确词，如 ID、代码符号）。只要任意一个支持的 provider 有 API key，开箱即用。

> <Info>
>   OpenClaw auto-detects your embedding provider from available API keys. If you have an OpenAI, Gemini, Voyage, or Mistral key configured, memory search is enabled automatically.
> </Info>

> **说明**：OpenClaw 从可用的 API key 自动识别 embedding provider。配了 OpenAI、Gemini、Voyage 或 Mistral 的 key，记忆搜索就自动启用。

> For details on how search works, tuning options, and provider setup, see [Memory Search](/concepts/memory-search).

搜索原理、调参选项、provider 配置见 [记忆搜索](/concepts/memory-search)。

---

> ## Memory backends

## 记忆后端

> <CardGroup cols={3}>
>   <Card title="Builtin (default)" icon="database" href="/concepts/memory-builtin">
>     SQLite-based. Works out of the box with keyword search, vector similarity, and hybrid search. No extra dependencies.
>   </Card>
>
>   <Card title="QMD" icon="search" href="/concepts/memory-qmd">
>     Local-first sidecar with reranking, query expansion, and the ability to index directories outside the workspace.
>   </Card>
>
>   <Card title="Honcho" icon="brain" href="/concepts/memory-honcho">
>     AI-native cross-session memory with user modeling, semantic search, and multi-agent awareness. Plugin install.
>   </Card>
>
>   <Card title="LanceDB" icon="layers" href="/plugins/memory-lancedb">
>     Bundled LanceDB-backed memory with OpenAI-compatible embeddings, auto-recall, auto-capture, and local Ollama embedding support.
>   </Card>
> </CardGroup>

- [内置（默认）](/concepts/memory-builtin)：基于 SQLite。开箱可用，支持关键词搜索、向量相似度、混合搜索。无额外依赖。
- [QMD](/concepts/memory-qmd)：本地优先的 sidecar，带 reranking、查询扩展，能索引工作区外的目录。
- [Honcho](/concepts/memory-honcho)：AI 原生的跨会话记忆，带用户建模、语义搜索、多 agent 感知。插件安装。
- [LanceDB](/plugins/memory-lancedb)：内置 LanceDB 支持的记忆，兼容 OpenAI embedding，支持自动召回、自动抓取、本地 Ollama embedding。

---

> ## Knowledge wiki layer

## 知识 wiki 层

> <CardGroup cols={1}>
>   <Card title="Memory Wiki" icon="book" href="/plugins/memory-wiki">
>     Compiles durable memory into a provenance-rich wiki vault with claims, dashboards, bridge mode, and Obsidian-friendly workflows.
>   </Card>
> </CardGroup>

- [Memory Wiki](/plugins/memory-wiki)：把长期记忆编译成带溯源的 wiki vault，含 claim、dashboard、桥接模式、Obsidian 友好的工作流。

---

> ## Automatic memory flush

## 自动记忆 flush

> Before [compaction](/concepts/compaction) summarizes your conversation, OpenClaw runs a silent turn that reminds the agent to save important context to memory files. This is on by default — you do not need to configure anything.

[压缩](/concepts/compaction) 概括对话之前，OpenClaw 跑一个静默轮次，提醒 agent 把重要上下文存到记忆文件里。这个默认开 —— 不用你配置。

> To keep that housekeeping turn on a local model, set an exact memory-flush model override:

要让这个家务轮次跑在本地模型上，设一个精确的 memory-flush 模型覆盖：

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

> The override applies only to the memory-flush turn and does not inherit the active session fallback chain.

这个覆盖只对 memory-flush 轮次生效，不继承当前会话的回退链。

> <Tip>
>   The memory flush prevents context loss during compaction. If your agent has important facts in the conversation that are not yet written to a file, they will be saved automatically before the summary happens.
> </Tip>

> **小贴士**：memory flush 防止压缩期间丢上下文。agent 在对话里说过的、还没写进文件的重要事实，会在 summary 之前自动保存。

---

> ## Dreaming

## 做梦（Dreaming）

> Dreaming is an optional background consolidation pass for memory. It collects short-term signals, scores candidates, and promotes only qualified items into long-term memory (`MEMORY.md`).

做梦是可选的、记忆的后台整合 pass。它收集短期信号、给候选打分，只把合格的项晋升进长期记忆（`MEMORY.md`）。

> It is designed to keep long-term memory high signal:
>
> * **Opt-in**: disabled by default.
> * **Scheduled**: when enabled, `memory-core` auto-manages one recurring cron job for a full dreaming sweep.
> * **Thresholded**: promotions must pass score, recall frequency, and query diversity gates.
> * **Reviewable**: phase summaries and diary entries are written to `DREAMS.md` for human review.

设计目标是保持长期记忆的信噪比高：

- **可选启用**：默认关。
- **按调度跑**：开启后，`memory-core` 自动管理一个定时 cron 任务，做完整的做梦扫描。
- **有阈值**：晋升必须过分数、召回频率、查询多样性等门槛。
- **可审阅**：阶段总结和日记条目写到 `DREAMS.md`，给人类看。

> For phase behavior, scoring signals, and Dream Diary details, see [Dreaming](/concepts/dreaming).

阶段行为、打分信号、Dream Diary 细节见 [做梦](/concepts/dreaming)。

---

> ## Grounded backfill and live promotion

## Grounded 回填与实时晋升

> The dreaming system now has two closely related review lanes:
>
> * **Live dreaming** works from the short-term dreaming store under `memory/.dreams/` and is what the normal deep phase uses when deciding what can graduate into `MEMORY.md`.
> * **Grounded backfill** reads historical `memory/YYYY-MM-DD.md` notes as standalone day files and writes structured review output into `DREAMS.md`.

做梦系统现在有两条关系紧密的审阅队列：

- **Live dreaming**：从 `memory/.dreams/` 下的短期做梦存储工作，这是常规深度阶段在判断什么可以晋升到 `MEMORY.md` 时用的。
- **Grounded backfill**：把历史 `memory/YYYY-MM-DD.md` 笔记当独立的日文件读，把结构化审阅输出写到 `DREAMS.md`。

> Grounded backfill is useful when you want to replay older notes and inspect what the system thinks is durable without manually editing `MEMORY.md`.

想要回放旧笔记、查看系统认为哪些是长期价值的内容、又不想手动改 `MEMORY.md` 时，grounded backfill 就有用。

> When you use:
>
> ```bash
> openclaw memory rem-backfill --path ./memory --stage-short-term
> ```
>
> the grounded durable candidates are not promoted directly. They are staged into the same short-term dreaming store the normal deep phase already uses. That means:

跑：

```bash
openclaw memory rem-backfill --path ./memory --stage-short-term
```

时，grounded 的长期候选不会直接晋升，而是 staged 到常规深度阶段已经在用的同一个短期做梦存储里。也就是说：

> * `DREAMS.md` stays the human review surface.
> * the short-term store stays the machine-facing ranking surface.
> * `MEMORY.md` is still only written by deep promotion.

- `DREAMS.md` 仍然是人类审阅面。
- 短期存储仍然是面向机器的排序面。
- `MEMORY.md` 仍然只由深度晋升写入。

> If you decide the replay was not useful, you can remove the staged artifacts without touching ordinary diary entries or normal recall state:
>
> ```bash
> openclaw memory rem-backfill --rollback
> openclaw memory rem-backfill --rollback-short-term
> ```

如果你判断这次回放没用，可以在不触碰常规日记条目或常规召回状态的情况下移除 staged 产物：

```bash
openclaw memory rem-backfill --rollback
openclaw memory rem-backfill --rollback-short-term
```

---

> ## CLI

## CLI

> ```bash
> openclaw memory status          # Check index status and provider
> openclaw memory search "query"  # Search from the command line
> openclaw memory index --force   # Rebuild the index
> ```

```bash
openclaw memory status          # 看索引状态和 provider
openclaw memory search "query"  # 命令行搜索
openclaw memory index --force   # 重建索引
```

---

> ## Further reading

## 进一步阅读

> * [Builtin memory engine](/concepts/memory-builtin): default SQLite backend.
> * [QMD memory engine](/concepts/memory-qmd): advanced local-first sidecar.
> * [Honcho memory](/concepts/memory-honcho): AI-native cross-session memory.
> * [Memory LanceDB](/plugins/memory-lancedb): LanceDB-backed plugin with OpenAI-compatible embeddings.
> * [Memory Wiki](/plugins/memory-wiki): compiled knowledge vault and wiki-native tools.
> * [Memory search](/concepts/memory-search): search pipeline, providers, and tuning.
> * [Dreaming](/concepts/dreaming): background promotion from short-term recall to long-term memory.
> * [Memory configuration reference](/reference/memory-config): all config knobs.
> * [Compaction](/concepts/compaction): how compaction interacts with memory.

- [内置记忆引擎](/concepts/memory-builtin)：默认 SQLite 后端。
- [QMD 记忆引擎](/concepts/memory-qmd)：进阶的本地优先 sidecar。
- [Honcho 记忆](/concepts/memory-honcho)：AI 原生的跨会话记忆。
- [Memory LanceDB](/plugins/memory-lancedb)：LanceDB 支持的插件，兼容 OpenAI embedding。
- [Memory Wiki](/plugins/memory-wiki)：编译化的知识 vault 和 wiki 原生工具。
- [记忆搜索](/concepts/memory-search)：搜索管道、provider、调参。
- [做梦](/concepts/dreaming)：从短期召回到长期记忆的后台晋升。
- [记忆配置参考](/reference/memory-config)：所有配置开关。
- [压缩](/concepts/compaction)：压缩怎么和记忆互动。

---

> ## Related

## 相关

> * [Active memory](/concepts/active-memory)
> * [Memory search](/concepts/memory-search)
> * [Builtin memory engine](/concepts/memory-builtin)
> * [Honcho memory](/concepts/memory-honcho)
> * [Memory LanceDB](/plugins/memory-lancedb)
> * [Commitments](/concepts/commitments)

- [活跃记忆](/concepts/active-memory)
- [记忆搜索](/concepts/memory-search)
- [内置记忆引擎](/concepts/memory-builtin)
- [Honcho 记忆](/concepts/memory-honcho)
- [Memory LanceDB](/plugins/memory-lancedb)
- [Commitments](/concepts/commitments)
