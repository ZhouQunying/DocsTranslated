# Tool-loop detection

> OpenClaw has two cooperating guardrails for repetitive tool-call patterns:
>
> 1. **Loop detection** (`tools.loopDetection.enabled`) — disabled by default. Watches the rolling tool-call history for repeated patterns and unknown-tool retries.
> 2. **Post-compaction guard** (`tools.loopDetection.postCompactionGuard`) — enabled by default unless `tools.loopDetection.enabled` is explicitly `false`. Arms after every compaction-retry and aborts the run when the agent emits the same `(tool, args, result)` triple within the window.

OpenClaw 有两条配合的护栏来对付重复的工具调用模式:

1. **循环检测**(`tools.loopDetection.enabled`)—— 默认关。盯着滚动的工具调用历史,看有没有重复模式或对未知工具的反复重试。
2. **压缩后护栏**(`tools.loopDetection.postCompactionGuard`)—— 默认开,除非 `tools.loopDetection.enabled` 被显式设成 `false`。每次压缩后重试时进入预备状态,如果 agent 在窗口期内发出相同的 `(工具, 参数, 结果)` 三元组,直接中止运行。

> Both are configured under the same `tools.loopDetection` block, but the post-compaction guard runs whenever the master switch is not explicitly off. Set `tools.loopDetection.enabled: false` to silence both surfaces.

两个都在同一个 `tools.loopDetection` 块下配置,但只要总开关没显式关掉,压缩后护栏都会跑。把 `tools.loopDetection.enabled` 设成 `false` 才能让两个都闭嘴。

## 为什么要这个

> - Detect repetitive sequences that do not make progress.
> - Detect high-frequency no-result loops (same tool, same inputs, repeated errors).
> - Detect specific repeated-call patterns for known polling tools.
> - Prevent context-overflow then compaction then same-loop cycles from running indefinitely.

- 识别"反复跑、毫无进展"的序列。
- 识别高频无结果循环(同一工具、同一输入、反复同样的错)。
- 识别已知轮询型工具的特定重复调用模式。
- 防止"上下文溢出 → 压缩 → 又陷入同一个循环"无限跑下去。

## 配置块

> Global defaults, with every documented field shown:

全局默认,所有有文档的字段都列出来:

```json5
{
  tools: {
    loopDetection: {
      enabled: false, // 滚动历史检测器的总开关
      historySize: 30,
      warningThreshold: 10,
      criticalThreshold: 20,
      unknownToolThreshold: 10,
      globalCircuitBreakerThreshold: 30,
      detectors: {
        genericRepeat: true,
        knownPollNoProgress: true,
        pingPong: true,
      },
      postCompactionGuard: {
        windowSize: 3, // 压缩后重试时进入预备状态;只要 enabled 不显式 false 就跑
      },
    },
  },
}
```

> Per-agent override (optional):

按 agent 覆盖(可选):

```json5
{
  agents: {
    list: [
      {
        id: "safe-runner",
        tools: {
          loopDetection: {
            enabled: true,
            warningThreshold: 8,
            criticalThreshold: 16,
          },
        },
      },
    ],
  },
}
```

### 字段行为

> | Field                            | Default | Effect                                                                                                                          |
> | -------------------------------- | ------- | ------------------------------------------------------------------------------------------------------------------------------- |
> | `enabled`                        | `false` | Master switch for the rolling-history detectors. Setting `false` also disables the post-compaction guard.                       |
> | `historySize`                    | `30`    | Number of recent tool calls kept for analysis.                                                                                  |
> | `warningThreshold`               | `10`    | Threshold before a pattern is classified as warning-only.                                                                       |
> | `criticalThreshold`              | `20`    | Threshold for blocking repetitive no-progress loop patterns.                                                                    |
> | `unknownToolThreshold`           | `10`    | Block repeated calls to the same unavailable tool after this many misses.                                                       |
> | `globalCircuitBreakerThreshold`  | `30`    | Global no-progress breaker threshold across all detectors.                                                                      |
> | `detectors.genericRepeat`        | `true`  | Warns on repeated same-tool + same-params patterns and blocks when the same calls also return identical outcomes.               |
> | `detectors.knownPollNoProgress`  | `true`  | Detects known polling-like patterns with no state change.                                                                       |
> | `detectors.pingPong`             | `true`  | Detects alternating ping-pong patterns.                                                                                         |
> | `postCompactionGuard.windowSize` | `3`     | Number of post-compaction tool calls during which the guard stays armed and the count of identical triples that aborts the run. |

| 字段                              | 默认    | 作用                                                                                                                |
| --------------------------------- | ------- | ------------------------------------------------------------------------------------------------------------------- |
| `enabled`                         | `false` | 滚动历史检测器的总开关。设 `false` 同时把压缩后护栏关掉。                                                            |
| `historySize`                     | `30`    | 保留多少条最近的工具调用用于分析。                                                                                   |
| `warningThreshold`                | `10`    | 一个模式被判定为"仅警告"的阈值。                                                                                     |
| `criticalThreshold`               | `20`    | 拦截重复的"无进展"循环模式的阈值。                                                                                   |
| `unknownToolThreshold`            | `10`    | 同一个不可用工具被反复调用这么多次之后,直接拦掉。                                                                    |
| `globalCircuitBreakerThreshold`   | `30`    | 跨所有检测器的全局"无进展"熔断阈值。                                                                                 |
| `detectors.genericRepeat`         | `true`  | 对"同工具 + 同参数"的重复模式发警告;调用结果也完全一样时直接拦。                                                     |
| `detectors.knownPollNoProgress`   | `true`  | 识别已知轮询风格、状态没变的模式。                                                                                   |
| `detectors.pingPong`              | `true`  | 识别两边来回的乒乓模式。                                                                                             |
| `postCompactionGuard.windowSize`  | `3`     | 压缩后多少次工具调用之内,护栏保持预备状态;同时也是中止运行所需的"完全相同三元组"次数。                              |

> For `exec`, no-progress checks compare stable command outcomes and ignore volatile runtime metadata such as duration, PID, session ID, and working directory. When a run id is available, recent tool-call history is evaluated only within that run so scheduled heartbeat cycles and fresh runs do not inherit stale loop counts from earlier runs.

对 `exec`,"无进展"检查比较稳定的命令结果,忽略 duration、PID、session ID、工作目录这些易变的运行时元数据。有 run id 的话,最近工具调用历史只在这个 run 内评估,这样定时心跳周期和新的运行不会继承早先运行的过期循环计数。

## 推荐配置

> - For smaller models, set `enabled: true` and leave the thresholds at their defaults. Flagship models rarely need rolling-history detection and can leave the master switch at `false` while still benefiting from the post-compaction guard.
> - Keep thresholds ordered as `warningThreshold < criticalThreshold < globalCircuitBreakerThreshold`.
> - If false positives occur:
>   - Raise `warningThreshold` and/or `criticalThreshold`.
>   - Optionally raise `globalCircuitBreakerThreshold`.
>   - Disable only the specific detector causing issues (`detectors.<name>: false`).
>   - Reduce `historySize` for less strict historical context.
> - To disable everything (including the post-compaction guard), set `tools.loopDetection.enabled: false` explicitly.

- 小模型设 `enabled: true`,阈值用默认值。旗舰模型一般不需要滚动历史检测,总开关可以保持 `false`,同时仍享受压缩后护栏的保护。
- 阈值顺序保持 `warningThreshold < criticalThreshold < globalCircuitBreakerThreshold`。
- 出现误报时:
  - 抬高 `warningThreshold` 和 / 或 `criticalThreshold`。
  - 可选:抬高 `globalCircuitBreakerThreshold`。
  - 只关掉造成问题的那个检测器(`detectors.<名字>: false`)。
  - 降低 `historySize`,用更宽松的历史上下文。
- 要把所有都关掉(包括压缩后护栏),显式设 `tools.loopDetection.enabled: false`。

## 压缩后护栏

> When the runner completes a compaction-retry after a context-overflow, it arms a short-window guard that watches the next few tool calls. If the agent emits the same `(toolName, argsHash, resultHash)` triple multiple times within the window, the guard concludes that compaction did not break the loop and aborts the run with a `compaction_loop_persisted` error.

运行器在上下文溢出之后完成一次压缩重试时,会武装一个短窗口护栏,盯着接下来的几次工具调用。agent 在这个窗口期内发出多次相同的 `(toolName, argsHash, resultHash)` 三元组时,护栏判定"压缩没打破循环",直接报 `compaction_loop_persisted` 错误并中止运行。

> The guard is gated by the master `tools.loopDetection.enabled` flag with one twist: it stays **enabled when the flag is unset or `true`** and only deactivates when the flag is explicitly `false`. This is intentional. The guard exists to escape compaction loops that would otherwise burn unbounded tokens, so a no-config user still gets the protection.

护栏受总开关 `tools.loopDetection.enabled` 控制,但有个反转:**没设或设 `true` 都开**,只有显式设 `false` 才关。这是故意的。护栏存在的目的是从那种会无限烧 token 的压缩循环里逃出来,所以一个零配置用户也能享受这层保护。

```json5
{
  tools: {
    loopDetection: {
      // 总开关;设 false 同时把护栏和滚动检测器都关掉
      enabled: true,
      postCompactionGuard: {
        windowSize: 3, // 默认
      },
    },
  },
}
```

> - Lower `windowSize` is stricter (fewer attempts before abort).
> - Higher `windowSize` gives the agent more recovery attempts.
> - The guard never aborts when results are changing, only when results are byte-identical across the window.
> - It is intentionally narrow: it fires only in the immediate aftermath of a compaction-retry.

- 更小的 `windowSize` 更严格(更少的重试机会就中止)。
- 更大的 `windowSize` 给 agent 更多恢复机会。
- 结果在变化时护栏不会中止;只有窗口内结果逐字节完全一致时才中止。
- 它刻意收窄:只在压缩重试之后立刻触发。

> <Note>
>   The post-compaction guard runs whenever the master flag is not explicitly `false`, even if you never wrote a `tools.loopDetection` block. To verify, look for `post-compaction guard armed for N attempts` in the gateway log immediately after a compaction event.
> </Note>

[展开: 注意] 只要总开关没显式 `false`,压缩后护栏就会跑,哪怕你压根没写过 `tools.loopDetection` 块。要验证,在压缩事件刚发生时,看 gateway 日志里有没有 `post-compaction guard armed for N attempts`。

## 日志与预期行为

> When a loop is detected, OpenClaw reports a loop event and either dampens or blocks the next tool-cycle depending on severity. This protects users from runaway token spend and lockups while preserving normal tool access.

检测到循环时,OpenClaw 上报一次循环事件,并按严重度选择"抑制"或"拦截"下一次工具循环。这样既防止失控的 token 消耗和卡死,又保留正常的工具使用。

> - Warnings come first.
> - Suppression follows when patterns persist past the warning threshold.
> - Critical thresholds block the next tool-cycle and surface a clear loop-detection reason in the run record.
> - The post-compaction guard emits `compaction_loop_persisted` errors with the offending tool name and identical-call count.

- 先发警告。
- 模式持续超过警告阈值后转为抑制。
- 严重阈值拦截下一次工具循环,在 run 记录里给出清晰的循环检测原因。
- 压缩后护栏发出 `compaction_loop_persisted` 错误,带上肇事工具名和相同调用计数。

## 相关

> - Exec approvals — Allow/deny policy for shell execution.
> - Thinking levels — Reasoning effort levels and provider-policy interaction.
> - Sub-agents — Spawning isolated agents to bound runaway behavior.
> - Configuration reference — Full `tools.loopDetection` schema and merging semantics.

- [Exec approvals](/tools/exec-approvals) —— shell 执行的允许 / 拒绝策略。
- [思考级别](/tools/thinking) —— 推理 effort 级别和 provider 策略的互动。
- [Sub-agents](/tools/subagents) —— 派生隔离的 agent,把失控行为框住。
- [配置参考](/gateway/configuration-reference) —— 完整的 `tools.loopDetection` schema 和合并语义。
