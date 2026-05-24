# Builtin memory engine

> The builtin engine is the default memory backend. It stores your memory index in
> a per-agent SQLite database and needs no extra dependencies to get started.

内置引擎是默认的记忆后端。它把记忆索引按 agent 分别存在 SQLite 数据库里,开箱即用,不用装任何额外依赖。

## 它提供什么

> - **Keyword search** via FTS5 full-text indexing (BM25 scoring).
> - **Vector search** via embeddings from any supported provider.
> - **Hybrid search** that combines both for best results.
> - **CJK support** via trigram tokenization for Chinese, Japanese, and Korean.
> - **sqlite-vec acceleration** for in-database vector queries (optional).

- **关键字检索**:基于 FTS5 全文索引(BM25 打分)。
- **向量检索**:基于任一支持的 provider 出的嵌入。
- **混合检索**:两者结合,效果最好。
- **中日韩支持**:三字组分词,处理中文、日文、韩文。
- **sqlite-vec 加速**:库内向量查询的可选加速。

## 上手

> If you have an API key for OpenAI, Gemini, Voyage, Mistral, or DeepInfra, the builtin
> engine auto-detects it and enables vector search. No config needed.

只要你有 OpenAI、Gemini、Voyage、Mistral 或 DeepInfra 中任一家的 API key,内置引擎就会自动识别并打开向量检索,不用配。

> To set a provider explicitly:

要显式指定 provider:

```json5
{
  agents: {
    defaults: {
      memorySearch: {
        provider: "openai",
      },
    },
  },
}
```

> Without an embedding provider, only keyword search is available.

没有嵌入 provider 时,只有关键字检索可用。

> To force the built-in local embedding provider, install the optional
> `node-llama-cpp` runtime package next to OpenClaw, then point `local.modelPath`
> at a GGUF file:

要强制走本地嵌入 provider,在 OpenClaw 旁边装上可选的 `node-llama-cpp` 运行时包,然后让 `local.modelPath` 指向一个 GGUF 文件:

```json5
{
  agents: {
    defaults: {
      memorySearch: {
        provider: "local",
        fallback: "none",
        local: {
          modelPath: "~/.node-llama-cpp/models/embeddinggemma-300m-qat-Q8_0.gguf",
        },
      },
    },
  },
}
```

## 支持的嵌入 provider

> | Provider  | ID          | Auto-detected | Notes                               |
> | --------- | ----------- | ------------- | ----------------------------------- |
> | OpenAI    | `openai`    | Yes           | Default: `text-embedding-3-small`   |
> | Gemini    | `gemini`    | Yes           | Supports multimodal (image + audio) |
> | Voyage    | `voyage`    | Yes           |                                     |
> | Mistral   | `mistral`   | Yes           |                                     |
> | DeepInfra | `deepinfra` | Yes           | Default: `BAAI/bge-m3`              |
> | Ollama    | `ollama`    | No            | Local, set explicitly               |
> | Local     | `local`     | Yes (first)   | Optional `node-llama-cpp` runtime   |

| Provider  | ID          | 自动识别       | 说明                              |
| --------- | ----------- | -------------- | --------------------------------- |
| OpenAI    | `openai`    | 是             | 默认 `text-embedding-3-small`     |
| Gemini    | `gemini`    | 是             | 支持多模态(图片 + 音频)           |
| Voyage    | `voyage`    | 是             |                                   |
| Mistral   | `mistral`   | 是             |                                   |
| DeepInfra | `deepinfra` | 是             | 默认 `BAAI/bge-m3`                |
| Ollama    | `ollama`    | 否             | 本地,必须显式设                   |
| Local     | `local`     | 是(优先)       | 可选的 `node-llama-cpp` 运行时    |

> Auto-detection picks the first provider whose API key can be resolved, in the
> order shown. Set `memorySearch.provider` to override.

自动识别按上表顺序找第一个 API key 能解析出来的 provider 就用。要覆盖,设 `memorySearch.provider`。

## 索引怎么工作的

> OpenClaw indexes `MEMORY.md` and `memory/*.md` into chunks (~400 tokens with
> 80-token overlap) and stores them in a per-agent SQLite database.

OpenClaw 把 `MEMORY.md` 和 `memory/*.md` 切成分块(每个约 400 token、80 token 重叠),按 agent 分别存进 SQLite 数据库。

> - **Index location:** `~/.openclaw/memory/<agentId>.sqlite`
> - **Storage maintenance:** SQLite WAL sidecars are bounded with periodic and
>   shutdown checkpoints.
> - **File watching:** changes to memory files trigger a debounced reindex (1.5s).
> - **Auto-reindex:** when the embedding provider, model, or chunking config
>   changes, the entire index is rebuilt automatically.
> - **Reindex on demand:** `openclaw memory index --force`

- **索引位置**:`~/.openclaw/memory/<agentId>.sqlite`
- **存储维护**:SQLite WAL sidecar 通过周期性 checkpoint 和关停时 checkpoint 控制大小。
- **文件监听**:记忆文件变更触发去抖的重建索引(1.5 秒)。
- **自动重建**:嵌入 provider、模型、分块配置变了,整套索引会自动重建。
- **按需重建**:`openclaw memory index --force`

> <Info>
> You can also index Markdown files outside the workspace with
> `memorySearch.extraPaths`. See the
> [configuration reference](/reference/memory-config#additional-memory-paths).
> </Info>

[展开: 信息] 工作区外的 Markdown 文件也能用 `memorySearch.extraPaths` 索引进来。见 [配置参考](/reference/memory-config#additional-memory-paths)。

## 什么时候用

> The builtin engine is the right choice for most users:
>
> - Works out of the box with no extra dependencies.
> - Handles keyword and vector search well.
> - Supports all embedding providers.
> - Hybrid search combines the best of both retrieval approaches.

内置引擎适合大多数用户:

- 开箱即用,不用装依赖。
- 关键字和向量检索都能处理得不错。
- 支持所有嵌入 provider。
- 混合检索把两种召回方式的长处都用上。

> Consider switching to [QMD](/concepts/memory-qmd) if you need reranking, query
> expansion, or want to index directories outside the workspace.

需要重排、查询扩展,或者想索引工作区外的目录时,考虑换 [QMD](/concepts/memory-qmd)。

> Consider [Honcho](/concepts/memory-honcho) if you want cross-session memory with
> automatic user modeling.

想要跨会话记忆 + 自动用户建模,考虑 [Honcho](/concepts/memory-honcho)。

## 排障

> **Memory search disabled?** Check `openclaw memory status`. If no provider is
> detected, set one explicitly or add an API key.

**记忆检索没启用?** 看 `openclaw memory status`。识别不到 provider 的话,显式设一个或加一个 API key。

> **Local provider not detected?** Confirm the local path exists and run:

**本地 provider 识别不到?** 确认本地路径存在,然后跑:

```bash
openclaw memory status --deep --agent main
openclaw memory index --force --agent main
```

> Both standalone CLI commands and the Gateway use the same `local` provider id.
> If the provider is set to `auto`, local embeddings are considered first only
> when `memorySearch.local.modelPath` points to an existing local file.

独立 CLI 命令和 Gateway 用同一个 `local` provider id。provider 设成 `auto` 时,只有 `memorySearch.local.modelPath` 指向一个真实存在的本地文件,本地嵌入才会被优先考虑。

> **Stale results?** Run `openclaw memory index --force` to rebuild. The watcher
> may miss changes in rare edge cases.

**结果过期?** 跑 `openclaw memory index --force` 重建。监听器在罕见边缘情况下可能漏掉文件变更。

> **sqlite-vec not loading?** OpenClaw falls back to in-process cosine similarity
> automatically. `openclaw memory status --deep` reports the local vector store
> separately from the embedding provider, so `Vector store: unavailable` points
> at sqlite-vec loading while `Embeddings: unavailable` points at provider/auth
> or model readiness. Check logs for the specific load error.

**sqlite-vec 加载不了?** OpenClaw 自动回退到进程内余弦相似度。`openclaw memory status --deep` 把本地向量存储和嵌入 provider 分开报告,所以 `Vector store: unavailable` 指向的是 sqlite-vec 加载问题,而 `Embeddings: unavailable` 指向的是 provider / 认证或模型就绪问题。具体加载错误看日志。

## 配置

> For embedding provider setup, hybrid search tuning (weights, MMR, temporal
> decay), batch indexing, multimodal memory, sqlite-vec, extra paths, and all
> other config knobs, see the
> [Memory configuration reference](/reference/memory-config).

嵌入 provider 配置、混合检索调参(权重、MMR、时间衰减)、批量索引、多模态记忆、sqlite-vec、额外路径,以及其他所有配置项,见 [记忆配置参考](/reference/memory-config)。

## 相关

> - [Memory overview](/concepts/memory)
> - [Memory search](/concepts/memory-search)
> - [Active memory](/concepts/active-memory)

- [记忆总览](/concepts/memory)
- [记忆检索](/concepts/memory-search)
- [Active memory](/concepts/active-memory)
