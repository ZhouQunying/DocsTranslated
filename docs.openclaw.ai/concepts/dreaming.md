# Dreaming

> Dreaming is the background memory consolidation system in `memory-core`. It helps OpenClaw move strong short-term signals into durable memory while keeping the process explainable and reviewable.

做梦(Dreaming)是 `memory-core` 里的后台记忆整理系统。它帮 OpenClaw 把短期记忆中信号强的部分搬进长期记忆,同时让整个过程可解释、可复盘。

> <Note>
> Dreaming is **opt-in** and disabled by default.
> </Note>

[展开: 注意] 做梦是 **可选** 的,默认关闭。

## 做梦写什么

> Dreaming keeps two kinds of output:
>
> - **Machine state** in `memory/.dreams/` (recall store, phase signals, ingestion checkpoints, locks).
> - **Human-readable output** in `DREAMS.md` (or existing `dreams.md`) and optional phase report files under `memory/dreaming/<phase>/YYYY-MM-DD.md`.

做梦保留两类输出:

- **机器状态** 放在 `memory/.dreams/`(召回存储、阶段信号、吸收进度检查点、锁)。
- **给人看的内容** 写到 `DREAMS.md`(或者已有的 `dreams.md`),以及可选的阶段报告文件 `memory/dreaming/<阶段>/YYYY-MM-DD.md`。

> Long-term promotion still writes only to `MEMORY.md`.

提拔到长期记忆的内容仍然只写 `MEMORY.md`。

## 阶段模型

> Dreaming uses three cooperative phases:

做梦用三个相互配合的阶段:

> | Phase | Purpose                                   | Durable write     |
> | ----- | ----------------------------------------- | ----------------- |
> | Light | Sort and stage recent short-term material | No                |
> | Deep  | Score and promote durable candidates      | Yes (`MEMORY.md`) |
> | REM   | Reflect on themes and recurring ideas     | No                |

| 阶段     | 目的                                  | 是否落盘到长期记忆     |
| -------- | ------------------------------------- | ---------------------- |
| 浅睡     | 整理、暂存最近的短期材料              | 否                     |
| 深睡     | 给候选打分,把够格的提拔成长期        | 是(`MEMORY.md`)        |
| REM      | 反思主题和反复出现的想法              | 否                     |

> These phases are internal implementation details, not separate user-configured "modes."

这些阶段是内部实现细节,不是用户能单独配置的"模式"。

> <AccordionGroup>
>   <Accordion title="Light phase">
>     Light phase ingests recent daily memory signals and recall traces, dedupes them, and stages candidate lines.
>
>     - Reads from short-term recall state, recent daily memory files, and redacted session transcripts when available.
>     - Writes a managed `## Light Sleep` block when storage includes inline output.
>     - Records reinforcement signals for later deep ranking.
>     - Never writes to `MEMORY.md`.
>
>   </Accordion>

[展开: 浅睡阶段] 浅睡阶段吸收最近的日记忆信号和召回轨迹,去重,然后把候选行暂存起来。

- 从短期召回状态、最近的日记忆文件,以及(如果有的话)脱敏的会话对话记录里读。
- 存储包含内联输出时,写一个受管理的 `## Light Sleep` 块。
- 记下强化信号,留给深睡阶段做排序。
- 永远不写 `MEMORY.md`。

> <Accordion title="Deep phase">
>     Deep phase decides what becomes long-term memory.
>
>     - Ranks candidates using weighted scoring and threshold gates.
>     - Requires `minScore`, `minRecallCount`, and `minUniqueQueries` to pass.
>     - Rehydrates snippets from live daily files before writing, so stale/deleted snippets are skipped.
>     - Appends promoted entries to `MEMORY.md`.
>     - Writes a `## Deep Sleep` summary into `DREAMS.md` and optionally writes `memory/dreaming/deep/YYYY-MM-DD.md`.
>
>   </Accordion>

[展开: 深睡阶段] 深睡阶段决定哪些内容能成为长期记忆。

- 用加权打分和阈值门做候选排序。
- 必须过 `minScore`、`minRecallCount`、`minUniqueQueries` 三道门。
- 在写之前从活的日文件里重新取一遍片段,这样过期或已删的片段会被跳过。
- 把提拔的条目追加到 `MEMORY.md`。
- 在 `DREAMS.md` 里写一份 `## Deep Sleep` 摘要,可选写一份 `memory/dreaming/deep/YYYY-MM-DD.md`。

> <Accordion title="REM phase">
>     REM phase extracts patterns and reflective signals.
>
>     - Builds theme and reflection summaries from recent short-term traces.
>     - Writes a managed `## REM Sleep` block when storage includes inline output.
>     - Records REM reinforcement signals used by deep ranking.
>     - Never writes to `MEMORY.md`.
>
>   </Accordion>
> </AccordionGroup>

[展开: REM 阶段] REM 阶段抽取模式和反思类信号。

- 从最近的短期轨迹里构建主题和反思摘要。
- 存储包含内联输出时,写一个受管理的 `## REM Sleep` 块。
- 记下 REM 强化信号,深睡排序会用。
- 永远不写 `MEMORY.md`。

## 会话对话记录吸收

> Dreaming can ingest redacted session transcripts into the dreaming corpus. When transcripts are available, they are fed into the light phase alongside daily memory signals and recall traces. Personal and sensitive content is redacted before ingestion.

做梦能把脱敏后的会话对话记录吸进做梦语料里。有对话记录可用时,它们和日记忆信号、召回轨迹一起喂给浅睡阶段。个人和敏感内容在吸收之前会被抹除。

## 梦境日记

> Dreaming also keeps a narrative **Dream Diary** in `DREAMS.md`. After each phase has enough material, `memory-core` runs a best-effort background subagent turn and appends a short diary entry. It uses the default runtime model unless `dreaming.model` is configured. If the configured model is unavailable, Dream Diary retries once with the session default model.

做梦还在 `DREAMS.md` 里维护一份叙事式的**梦境日记**。每个阶段攒够材料后,`memory-core` 跑一次尽力而为的后台 subagent 轮次,追加一段简短的日记。它用默认运行时模型,除非配了 `dreaming.model`。配的模型不可用时,梦境日记会用会话默认模型再试一次。

> <Note>
> This diary is for human reading in the Dreams UI, not a promotion source. Dreaming-generated diary/report artifacts are excluded from short-term promotion. Only grounded memory snippets are eligible to promote into `MEMORY.md`.
> </Note>

[展开: 注意] 这份日记是给人在 Dreams UI 里看的,不是提拔的来源。做梦生成的日记 / 报告产物都被排除在短期提拔之外。只有"有据可查"(grounded)的记忆片段才能被提拔到 `MEMORY.md`。

> There is also a grounded historical backfill lane for review and recovery work:

还有一条"有据可查的历史回灌"通路,用于复盘和恢复:

> <AccordionGroup>
>   <Accordion title="Backfill commands">
>     - `memory rem-harness --path ... --grounded` previews grounded diary output from historical `YYYY-MM-DD.md` notes.
>     - `memory rem-backfill --path ...` writes reversible grounded diary entries into `DREAMS.md`.
>     - `memory rem-backfill --path ... --stage-short-term` stages grounded durable candidates into the same short-term evidence store the normal deep phase already uses.
>     - `memory rem-backfill --rollback` and `--rollback-short-term` remove those staged backfill artifacts without touching ordinary diary entries or live short-term recall.
>
>   </Accordion>
> </AccordionGroup>

[展开: 回灌命令]

- `memory rem-harness --path ... --grounded` 预览基于历史 `YYYY-MM-DD.md` 笔记生成的有据可查的日记输出。
- `memory rem-backfill --path ...` 把可回滚的、有据可查的日记条目写到 `DREAMS.md`。
- `memory rem-backfill --path ... --stage-short-term` 把有据可查的长期候选暂存到深睡阶段已经在用的同一份短期证据库里。
- `memory rem-backfill --rollback` 和 `--rollback-short-term` 移除那些被暂存的回灌产物,不动正常的日记条目,也不动正在跑的短期召回。

> The Control UI exposes the same diary backfill/reset flow so you can inspect results in the Dreams scene before deciding whether the grounded candidates deserve promotion. The Scene also shows a distinct grounded lane so you can see which staged short-term entries came from historical replay, which promoted items were grounded-led, and clear only grounded-only staged entries without touching ordinary live short-term state.

Control UI 把同一套日记回灌 / 重置流程暴露出来,你能在 Dreams 场景里检查结果,然后再决定哪些有据可查的候选值得提拔。Scene 里还有一条独立的"有据可查"通路,你能看出:哪些暂存的短期条目来自历史回放、哪些提拔出的条目是基于历史回放,并且只清掉"仅来自历史回放"的暂存条目,不动正常的实时短期状态。

## 深睡排序信号

> Deep ranking uses six weighted base signals plus phase reinforcement:

深睡排序用 6 个加权基础信号,再加上阶段强化:

> | Signal              | Weight | Description                                       |
> | ------------------- | ------ | ------------------------------------------------- |
> | Frequency           | 0.24   | How many short-term signals the entry accumulated |
> | Relevance           | 0.30   | Average retrieval quality for the entry           |
> | Query diversity     | 0.15   | Distinct query/day contexts that surfaced it      |
> | Recency             | 0.15   | Time-decayed freshness score                      |
> | Consolidation       | 0.10   | Multi-day recurrence strength                     |
> | Conceptual richness | 0.06   | Concept-tag density from snippet/path             |

| 信号       | 权重 | 说明                                       |
| ---------- | ---- | ------------------------------------------ |
| 频率       | 0.24 | 这条条目累积了多少短期信号                 |
| 相关性     | 0.30 | 这条条目的平均检索质量                     |
| 查询多样性 | 0.15 | 把它召出来的不同查询 / 日上下文数          |
| 新鲜度     | 0.15 | 时间衰减后的新鲜度得分                     |
| 巩固度     | 0.10 | 跨天重现的强度                             |
| 概念丰富度 | 0.06 | 从片段 / 路径推断的概念标签密度            |

> Light and REM phase hits add a small recency-decayed boost from `memory/.dreams/phase-signals.json`.

浅睡和 REM 阶段命中会从 `memory/.dreams/phase-signals.json` 加一个小幅度、随时间衰减的加成。

## QA 影子试验报告覆盖

> QA Lab includes a report-only scenario for exploring how a future dreaming
> shadow trial could review a candidate memory before promotion. The scenario asks
> an agent to compare a baseline answer with an answer that can use the candidate
> memory, then write a local report with a verdict, reason, and risk flags.

QA Lab 里有一个仅出报告的场景,用来探索"未来某天做梦的影子试验怎么在提拔前评审一条候选记忆"。场景让 agent 对比"基线答案"和"能用候选记忆的答案",然后写一份本地报告,带结论、理由、风险标记。

> This coverage is intentionally scoped to QA. It verifies that the report artifact
> stays separate from `MEMORY.md` and that the agent does not claim the candidate
> was promoted. It does not add production shadow-trial behavior or change the
> deep-phase promotion engine.

这个覆盖刻意只放在 QA 里。它验证两件事:报告产物跟 `MEMORY.md` 是分开的;agent 不会谎称候选已经被提拔。它不在生产环境里加任何"影子试验"行为,也不改深睡阶段的提拔引擎。

## 调度

> When enabled, `memory-core` auto-manages one cron job for a full dreaming sweep. Each sweep runs phases in order: light → REM → deep.

开启之后,`memory-core` 自动管理一个完整做梦扫一遍的 cron 任务。每一遍按顺序跑阶段:浅睡 → REM → 深睡。

> The sweep includes the primary runtime workspace and any configured agent workspaces, deduped by path, so subagent workspace fan-out does not exclude the main agent's `DREAMS.md` and memory state.

这一遍会扫主运行时工作区,以及配置好的所有 agent 工作区,按路径去重,所以 subagent 工作区扇出不会把主 agent 的 `DREAMS.md` 和记忆状态漏掉。

> Default cadence behavior:

默认节奏:

> | Setting              | Default       |
> | -------------------- | ------------- |
> | `dreaming.frequency` | `0 3 * * *`   |
> | `dreaming.model`     | default model |

| 配置项               | 默认值        |
| -------------------- | ------------- |
| `dreaming.frequency` | `0 3 * * *`   |
| `dreaming.model`     | 默认模型      |

## 快速开始

> <Tabs>
>   <Tab title="Enable dreaming">

[标签: 启用做梦]

```json
{
  "plugins": {
    "entries": {
      "memory-core": {
        "config": {
          "dreaming": {
            "enabled": true
          }
        }
      }
    }
  }
}
```

> <Tab title="Custom sweep cadence">

[标签: 自定义扫一遍的节奏]

```json
{
  "plugins": {
    "entries": {
      "memory-core": {
        "config": {
          "dreaming": {
            "enabled": true,
            "timezone": "America/Los_Angeles",
            "frequency": "0 */6 * * *"
          }
        }
      }
    }
  }
}
```

## Slash 命令

```
/dreaming status
/dreaming on
/dreaming off
/dreaming help
```

## CLI 工作流

> <Tab title="Promotion preview / apply">

[标签: 提拔预览 / 应用]

```bash
openclaw memory promote
openclaw memory promote --apply
openclaw memory promote --limit 5
openclaw memory status --deep
```

> Manual `memory promote` uses deep-phase thresholds by default unless overridden with CLI flags.

手动跑的 `memory promote` 默认用深睡阶段的阈值,除非用 CLI 参数显式覆盖。

> <Tab title="Explain promotion">
>     Explain why a specific candidate would or would not promote:

[标签: 解释为什么提拔 / 不提拔] 解释某条候选为什么会(或不会)被提拔:

```bash
openclaw memory promote-explain "router vlan"
openclaw memory promote-explain "router vlan" --json
```

> <Tab title="REM harness preview">
>     Preview REM reflections, candidate truths, and deep promotion output without writing anything:

[标签: REM 试运行预览] 预览 REM 反思、候选事实和深睡提拔输出,不写任何东西:

```bash
openclaw memory rem-harness
openclaw memory rem-harness --json
```

## 关键默认值

> All settings live under `plugins.entries.memory-core.config.dreaming`.

所有配置都在 `plugins.entries.memory-core.config.dreaming` 下。

> <ParamField path="enabled" type="boolean" default="false">
>   Enable or disable the dreaming sweep.
> </ParamField>

`enabled`(boolean,默认 `false`):开 / 关做梦扫一遍。

> <ParamField path="frequency" type="string" default="0 3 * * *">
>   Cron cadence for the full dreaming sweep.
> </ParamField>

`frequency`(string,默认 `0 3 * * *`):完整做梦扫一遍的 cron 节奏。

> <ParamField path="model" type="string">
>   Optional Dream Diary subagent model override. Use a canonical `provider/model` value when also setting a subagent `allowedModels` allowlist.
> </ParamField>

`model`(string):梦境日记 subagent 的模型覆盖,可选。同时设了 subagent `allowedModels` 白名单时,这里用规范的 `provider/model` 值。

> <Warning>
> `dreaming.model` requires `plugins.entries.memory-core.subagent.allowModelOverride: true`. To restrict it, also set `plugins.entries.memory-core.subagent.allowedModels`. Trust or allowlist failures stay visible instead of falling back silently; the retry only covers model-unavailable errors.
> </Warning>

[展开: 警告] `dreaming.model` 需要 `plugins.entries.memory-core.subagent.allowModelOverride: true`。要再限制范围,设 `plugins.entries.memory-core.subagent.allowedModels`。信任或白名单失败会显式可见,不会默默回退;只有"模型不可用"那种错才走重试。

> <Note>
> Phase policy, thresholds, and storage behavior are internal implementation details (not user-facing config). See [Memory configuration reference](/reference/memory-config#dreaming) for the full key list.
> </Note>

[展开: 注意] 阶段策略、阈值、存储行为都是内部实现细节(不是用户层配置)。完整的 key 列表见 [记忆配置参考](/reference/memory-config#dreaming)。

## Dreams UI

> When enabled, the Gateway **Dreams** tab shows:
>
> - current dreaming enabled state
> - phase-level status and managed-sweep presence
> - short-term, grounded, signal, and promoted-today counts
> - next scheduled run timing
> - a distinct grounded Scene lane for staged historical replay entries
> - an expandable Dream Diary reader backed by `doctor.memory.dreamDiary`

开启之后,Gateway 的 **Dreams** 标签页显示:

- 当前做梦是否开启
- 阶段级状态和受管理扫一遍是否存在
- 短期、有据可查、信号、今日已提拔的计数
- 下一次计划运行时间
- 一条独立的"有据可查"Scene 通路,显示暂存的历史回放条目
- 可展开的梦境日记阅读器,数据来自 `doctor.memory.dreamDiary`

## 做梦永远没跑:状态显示 blocked

> If `openclaw memory status` reports `Dreaming status: blocked`, the managed cron exists but the default agent heartbeat is not firing. Check that heartbeat is enabled for the default agent and that its target is not `none`, then run `openclaw memory status --deep` again after the next heartbeat interval.

`openclaw memory status` 报 `Dreaming status: blocked` 时,意思是受管理的 cron 是有的,但默认 agent 的心跳没在跑。看默认 agent 的心跳是不是开了、`target` 不是 `none`,然后等下一个心跳周期再跑一次 `openclaw memory status --deep`。

## 相关

> - [Memory](/concepts/memory)
> - [Memory CLI](/cli/memory)
> - [Memory configuration reference](/reference/memory-config)
> - [Memory search](/concepts/memory-search)

- [记忆](/concepts/memory)
- [Memory CLI](/cli/memory)
- [记忆配置参考](/reference/memory-config)
- [记忆检索](/concepts/memory-search)
