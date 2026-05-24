# Session pruning

> Session pruning trims **old tool results** from the context before each LLM call. It reduces context bloat from accumulated tool outputs (exec results, file reads, search results) without rewriting normal conversation text.

会话裁剪在每次 LLM 调用之前，把上下文里**老的工具结果**裁掉。它降低累积工具输出（exec 结果、文件读取、搜索结果）造成的上下文膨胀，但不改写正常的对话文本。

> <Info>
>   Pruning is in-memory only -- it does not modify the on-disk session transcript. Your full history is always preserved.
> </Info>

> **说明**：裁剪只在内存里做 —— 不会改磁盘上的会话 transcript。完整历史始终保留。

---

> ## Why it matters

## 为什么重要

> Long sessions accumulate tool output that inflates the context window. This increases cost and can force [compaction](/concepts/compaction) sooner than necessary.

长会话会累积工具输出，把上下文窗口撑大。这会增加成本，还可能让 [压缩](/concepts/compaction) 比必要时机更早被触发。

> Pruning is especially valuable for **Anthropic prompt caching**. After the cache TTL expires, the next request re-caches the full prompt. Pruning reduces the cache-write size, directly lowering cost.

裁剪对 **Anthropic prompt caching** 特别有价值。缓存 TTL 过期后，下一次请求会重新缓存完整 prompt。裁剪让缓存写入更小，直接降本。

---

> ## How it works

## 工作原理

> 1. Wait for the cache TTL to expire (default 5 minutes).
> 2. Find old tool results for normal pruning (conversation text is left alone).
> 3. **Soft-trim** oversized results -- keep the head and tail, insert `...`.
> 4. **Hard-clear** the rest -- replace with a placeholder.
> 5. Reset the TTL so follow-up requests reuse the fresh cache.

1. 等缓存 TTL 过期（默认 5 分钟）。
2. 常规裁剪时，找出老的工具结果（不动对话文本）。
3. 对超大的结果做**软裁**：保留头尾、中间插 `...`。
4. 其余的**硬清**：换成占位符。
5. 重置 TTL，让后续请求复用新鲜的缓存。

---

> ## Legacy image cleanup

## 旧版图片清理

> OpenClaw also builds a separate idempotent replay view for sessions that persist raw image blocks or prompt-hydration media markers in history.

OpenClaw 还会给那些把原始图片块或 prompt-hydration 媒体标记持久化在历史里的会话单独构建一份幂等回放视图。

> * It preserves the **3 most recent completed turns** byte-for-byte so prompt cache prefixes for recent follow-ups stay stable.
> * In the replay view, older already-processed image blocks from `user` or `toolResult` history can be replaced with `[image data removed - already processed by model]`.
> * Older textual media references such as `[media attached: ...]`, `[Image: source: ...]`, and `media://inbound/...` can be replaced with `[media reference removed - already processed by model]`. Current-turn attachment markers stay intact so vision models can still hydrate fresh images.
> * The raw session transcript is not rewritten, so history viewers can still render the original message entries and their images.
> * This is separate from normal cache-TTL pruning. It exists to stop repeated image payloads or stale media refs from busting prompt caches on later turns.

- 它**逐字节**保留**最近 3 次已完成的轮次**，让最近跟进的 prompt 缓存前缀保持稳定。
- 在回放视图里，`user` 或 `toolResult` 历史里旧的、已经处理过的图片块可被替换成 `[image data removed - already processed by model]`。
- 旧的文本媒体引用（如 `[media attached: ...]`、`[Image: source: ...]`、`media://inbound/...`）可被替换成 `[media reference removed - already processed by model]`。当前轮的附件标记保持不动，让视觉模型仍然能 hydrate 新图。
- 原始会话对话记录不会被改写，历史查看器仍能渲染原始消息条目和它们的图片。
- 这跟常规的缓存 TTL 裁剪是分开的。它的目的是阻止重复图片载荷或过期媒体引用在后续轮次里把 prompt 缓存搞崩。

---

> ## Smart defaults

## 智能默认

> OpenClaw auto-enables pruning for Anthropic profiles:

OpenClaw 给 Anthropic profile 自动开裁剪：

> | Profile type                                            | Pruning enabled | Heartbeat |
> | ------------------------------------------------------- | --------------- | --------- |
> | Anthropic OAuth/token auth (including Claude CLI reuse) | Yes             | 1 hour    |
> | API key                                                 | Yes             | 30 min    |

| profile 类型                                            | 裁剪开启 | 心跳    |
| ------------------------------------------------------- | -------- | ------- |
| Anthropic OAuth/token 认证（含 Claude CLI 复用）        | 是       | 1 小时  |
| API key                                                 | 是       | 30 分钟 |

> If you set explicit values, OpenClaw does not override them.

显式设过值的话，OpenClaw 不会覆盖。

---

> ## Enable or disable

## 启用 / 关闭

> Pruning is off by default for non-Anthropic providers. To enable:

非 Anthropic provider 默认不开裁剪。开启：

> ```json5
> {
>   agents: {
>     defaults: {
>       contextPruning: { mode: "cache-ttl", ttl: "5m" },
>     },
>   },
> }
> ```

```json5
{
  agents: {
    defaults: {
      contextPruning: { mode: "cache-ttl", ttl: "5m" },
    },
  },
}
```

> To disable: set `mode: "off"`.

关掉就把 `mode` 设成 `"off"`。

---

> ## Pruning vs compaction

## 裁剪 vs 压缩

> |            | Pruning            | Compaction              |
> | ---------- | ------------------ | ----------------------- |
> | **What**   | Trims tool results | Summarizes conversation |
> | **Saved?** | No (per-request)   | Yes (in transcript)     |
> | **Scope**  | Tool results only  | Entire conversation     |

|              | 裁剪                  | 压缩                          |
| ------------ | --------------------- | ----------------------------- |
| **做什么**   | 裁剪工具结果          | 概括对话                      |
| **保存吗？** | 否（按请求）          | 是（写进对话记录）         |
| **范围**     | 只是工具结果          | 整段对话                      |

> They complement each other -- pruning keeps tool output lean between compaction cycles.

它们互补 —— 裁剪在两次压缩之间让工具输出保持精简。

---

> ## Further reading

## 进一步阅读

> * [Compaction](/concepts/compaction) -- summarization-based context reduction
> * [Gateway Configuration](/gateway/configuration) -- all pruning config knobs (`contextPruning.*`)

- [压缩](/concepts/compaction)：基于摘要的上下文缩减。
- [Gateway 配置](/gateway/configuration)：所有裁剪配置开关（`contextPruning.*`）。

---

> ## Related

## 相关

> * [Session management](/concepts/session)
> * [Session tools](/concepts/session-tool)
> * [Context engine](/concepts/context-engine)

- [会话管理](/concepts/session)
- [会话工具](/concepts/session-tool)
- [上下文引擎](/concepts/context-engine)
