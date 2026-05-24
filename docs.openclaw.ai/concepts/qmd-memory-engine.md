# QMD memory engine

> [QMD](https://github.com/tobi/qmd) is a local-first search sidecar that runs
> alongside OpenClaw. It combines BM25, vector search, and reranking in a single
> binary, and can index content beyond your workspace memory files.

[QMD](https://github.com/tobi/qmd) 是一个本地优先的检索 sidecar,跟 OpenClaw 并排跑。它把 BM25、向量检索和重排塞在同一个二进制里,而且能索引工作区记忆文件之外的内容。

## 比内置引擎多了什么

> - **Reranking and query expansion** for better recall.
> - **Index extra directories** -- project docs, team notes, anything on disk.
> - **Index session transcripts** -- recall earlier conversations.
> - **Fully local** -- runs with the optional node-llama-cpp runtime package and
>   auto-downloads GGUF models.
> - **Automatic fallback** -- if QMD is unavailable, OpenClaw falls back to the
>   builtin engine seamlessly.

- **重排和查询扩展** —— 召回质量更高。
- **索引额外目录** —— 项目文档、团队笔记,磁盘上任何内容。
- **索引会话对话记录** —— 能召回早先的对话。
- **完全本地** —— 跟可选的 `node-llama-cpp` 运行时包配合,自动下载 GGUF 模型。
- **自动回退** —— QMD 不可用时,OpenClaw 无感切到内置引擎。

## 上手

### 前置条件

> - Install QMD: `npm install -g @tobilu/qmd` or `bun install -g @tobilu/qmd`
> - SQLite build that allows extensions (`brew install sqlite` on macOS).
> - QMD must be on the gateway's `PATH`.
> - macOS and Linux work out of the box. Windows is best supported via WSL2.

- 装 QMD:`npm install -g @tobilu/qmd` 或 `bun install -g @tobilu/qmd`
- 一个允许加载扩展的 SQLite(macOS 上 `brew install sqlite`)。
- QMD 必须出现在 gateway 进程的 `PATH` 里。
- macOS 和 Linux 开箱可用。Windows 最好走 WSL2。

### 开启

```json5
{
  memory: {
    backend: "qmd",
  },
}
```

> OpenClaw creates a self-contained QMD home under
> `~/.openclaw/agents/<agentId>/qmd/` and manages the sidecar lifecycle
> automatically -- collections, updates, and embedding runs are handled for you.
> It prefers current QMD collection and MCP query shapes, but still falls back to
> alternate collection pattern flags and older MCP tool names when needed.
> Boot-time reconciliation also recreates stale managed collections back to their
> canonical patterns when an older QMD collection with the same name is still
> present.

OpenClaw 在 `~/.openclaw/agents/<agentId>/qmd/` 下建一个独立的 QMD 家目录,自动管理 sidecar 的生命周期 —— collection、更新、嵌入计算都不用你管。它优先用当前版本的 QMD collection 形态和 MCP 查询形态,需要时也能回退到替代的 collection 模式参数和老的 MCP 工具名。启动时还会做一次对账:同名的旧 QMD collection 还在的话,把过期的受管理 collection 重建回规范模式。

## sidecar 怎么工作的

> - OpenClaw creates collections from your workspace memory files and any
>   configured `memory.qmd.paths`, then runs `qmd update` when the QMD manager is
>   opened and periodically afterward (default every 5 minutes). These refreshes
>   run through QMD subprocesses, not an in-process filesystem crawl. Semantic
>   modes also run `qmd embed`.
> - The default workspace collection tracks `MEMORY.md` plus the `memory/`
>   tree. Lowercase `memory.md` is not indexed as a root memory file.
> - QMD's own scanner ignores hidden paths and common dependency/build
>   directories such as `.git`, `.cache`, `node_modules`, `vendor`, `dist`, and
>   `build`. Gateway startup does not initialize QMD by default, so cold boot
>   avoids importing the memory runtime or creating the long-lived watcher before
>   memory is first used.
> - If you want a gateway-start refresh anyway, set
>   `memory.qmd.update.startup` to `idle` or `immediate`. The opt-in startup
>   refresh uses a one-shot QMD subprocess path instead of creating the full
>   long-lived in-process watcher.
> - Searches use the configured `searchMode` (default: `search`; also supports
>   `vsearch` and `query`). `search` is BM25-only, so OpenClaw skips semantic
>   vector readiness probes and embedding maintenance in that mode. If a mode
>   fails, OpenClaw retries with `qmd query`.
> - With QMD releases that advertise multi-collection filters, OpenClaw groups
>   same-source collections into one QMD search invocation. Older QMD releases
>   keep the compatible per-collection fallback.
> - If QMD fails entirely, OpenClaw falls back to the builtin SQLite engine.
>   Repeated chat-turn attempts back off briefly after an open failure so a
>   missing binary or broken sidecar dependency does not create a retry storm;
>   `openclaw memory status` and one-shot CLI probes still recheck QMD directly.

- OpenClaw 根据你的工作区记忆文件和 `memory.qmd.paths` 里配的路径建 collection,然后在 QMD 管理器打开时跑一次 `qmd update`,之后周期性再跑(默认 5 分钟一次)。这些刷新都走 QMD 子进程,不在 OpenClaw 进程内自己爬文件系统。语义模式还会跑 `qmd embed`。
- 默认工作区 collection 跟踪 `MEMORY.md` 和整个 `memory/` 树。小写的 `memory.md` 不作为根级记忆文件索引。
- QMD 自己的扫描器忽略隐藏路径,以及 `.git`、`.cache`、`node_modules`、`vendor`、`dist`、`build` 这些常见依赖 / 构建目录。Gateway 启动时默认不初始化 QMD,所以冷启动不会在第一次用到记忆之前就引入记忆运行时或建立长生命周期的监听器。
- 如果你确实想让 gateway 一启动就刷新一次,把 `memory.qmd.update.startup` 设成 `idle` 或 `immediate`。这个可选的启动刷新走一次性 QMD 子进程,不创建那个完整的长生命周期进程内监听器。
- 检索用配置好的 `searchMode`(默认 `search`,也支持 `vsearch` 和 `query`)。`search` 只用 BM25,所以这个模式下 OpenClaw 跳过语义向量就绪探测和嵌入维护。某个模式失败时,OpenClaw 用 `qmd query` 再试一次。
- 如果 QMD 版本声明支持多 collection 过滤,OpenClaw 把同源的 collection 合到一条 QMD 检索命令里。老版本 QMD 保留兼容的"按 collection 单独查"的回退路径。
- QMD 完全失败时,OpenClaw 回退到内置 SQLite 引擎。失败一次之后,接下来的对话轮次会短暂退避一下,避免"二进制找不到"或者"sidecar 依赖损坏"导致重试风暴;`openclaw memory status` 和一次性 CLI 探针仍然直接重新检查 QMD。

> <Info>
> The first search may be slow -- QMD auto-downloads GGUF models (~2 GB) for
> reranking and query expansion on the first `qmd query` run.
> </Info>

[展开: 信息] 第一次检索可能慢 —— QMD 在第一次跑 `qmd query` 时会自动下载用于重排和查询扩展的 GGUF 模型(约 2 GB)。

## 检索性能和兼容性

> OpenClaw keeps the QMD search path compatible with both current and older QMD
> installs.

OpenClaw 让 QMD 检索路径同时兼容新老 QMD 安装。

> On startup, OpenClaw checks the installed QMD help text once per manager. If the
> binary advertises support for multiple collection filters, OpenClaw searches all
> same-source collections with one command:

启动时,OpenClaw 按管理器粒度读一次 QMD 的 help 文本。二进制声明支持多 collection 过滤时,OpenClaw 一条命令搜遍所有同源 collection:

```bash
qmd search "router notes" --json -n 10 -c memory-root-main -c memory-dir-main
```

> This avoids starting one QMD subprocess for every durable-memory collection.
> Session transcript collections stay in their own source group, so mixed
> `memory` + `sessions` searches still give the result diversifier input from both
> sources.

这样就不用为每一个长期记忆 collection 各起一个 QMD 子进程。会话对话记录的 collection 留在它们自己的源分组里,所以"记忆 + 会话"的混合检索仍然能给结果多样化器喂进两个来源的输入。

> Older QMD builds only accept one collection filter. When OpenClaw detects one
> of those builds, it keeps the compatibility path and searches each collection
> separately before merging and deduplicating results.

老版本 QMD 只接受一个 collection 过滤。OpenClaw 识别到这种老版本时,会走兼容路径:每个 collection 单独查,然后合并、去重结果。

> To inspect the installed contract manually, run:

要手动看你装的 QMD 提供什么契约,跑:

```bash
qmd --help | grep -i collection
```

> Current QMD help says collection filters can target one or more collections.
> Older help usually describes a single collection.

当前版本的 QMD help 会说 collection 过滤可以指一个或多个 collection。老的 help 通常只说一个。

## 模型覆盖

> QMD model environment variables pass through unchanged from the gateway
> process, so you can tune QMD globally without adding new OpenClaw config:

QMD 模型相关的环境变量会原样从 gateway 进程透传过去,所以你能在不加新 OpenClaw 配置的前提下全局调 QMD:

```bash
export QMD_EMBED_MODEL="hf:Qwen/Qwen3-Embedding-0.6B-GGUF/Qwen3-Embedding-0.6B-Q8_0.gguf"
export QMD_RERANK_MODEL="/absolute/path/to/reranker.gguf"
export QMD_GENERATE_MODEL="/absolute/path/to/generator.gguf"
```

> After changing the embedding model, rerun embeddings so the index matches the
> new vector space.

换嵌入模型之后,重跑一次嵌入,让索引匹配新的向量空间。

## 索引额外路径

> Point QMD at additional directories to make them searchable:

让 QMD 指向额外目录,把它们变成可检索的:

```json5
{
  memory: {
    backend: "qmd",
    qmd: {
      paths: [{ name: "docs", path: "~/notes", pattern: "**/*.md" }],
    },
  },
}
```

> Snippets from extra paths appear as `qmd/<collection>/<relative-path>` in
> search results. `memory_get` understands this prefix and reads from the correct
> collection root.

额外路径下的片段在检索结果里以 `qmd/<collection>/<相对路径>` 形式出现。`memory_get` 认得这个前缀,会从正确的 collection 根去读。

## 索引会话对话记录

> Enable session indexing to recall earlier conversations:

开启会话索引,就能召回早先的对话:

```json5
{
  memory: {
    backend: "qmd",
    qmd: {
      sessions: { enabled: true },
    },
  },
}
```

> Transcripts are exported as sanitized User/Assistant turns into a dedicated QMD
> collection under `~/.openclaw/agents/<id>/qmd/sessions/`.

对话记录会以脱敏的 User/Assistant 轮次形式,导出到 `~/.openclaw/agents/<id>/qmd/sessions/` 下的一个专门的 QMD collection。

## 检索作用域

> By default, QMD search results are surfaced in direct and channel sessions
> (not groups). Configure `memory.qmd.scope` to change this:

默认 QMD 检索结果只在私聊和频道会话里露出,群里不露。要改,配 `memory.qmd.scope`:

```json5
{
  memory: {
    qmd: {
      scope: {
        default: "deny",
        rules: [{ action: "allow", match: { chatType: "direct" } }],
      },
    },
  },
}
```

> When scope denies a search, OpenClaw logs a warning with the derived channel and
> chat type so empty results are easier to debug.

作用域拒绝一次检索时,OpenClaw 会在日志里写一条警告,带上推断出的通道和聊天类型,排查"空结果"问题更容易。

## 引用

> When `memory.citations` is `auto` or `on`, search snippets include a
> `Source: <path#line>` footer. Set `memory.citations = "off"` to omit the footer
> while still passing the path to the agent internally.

`memory.citations` 是 `auto` 或 `on` 时,检索片段会带一行 `Source: <path#line>` 尾注。设成 `"off"` 可以去掉尾注,但路径仍然内部透传给 agent。

## 什么时候用

> Choose QMD when you need:
>
> - Reranking for higher-quality results.
> - To search project docs or notes outside the workspace.
> - To recall past session conversations.
> - Fully local search with no API keys.

什么时候选 QMD:

- 想要重排带来的更高质量结果。
- 想检索工作区外的项目文档或笔记。
- 想召回过去的会话对话。
- 想完全本地、不要 API key 的检索。

> For simpler setups, the [builtin engine](/concepts/memory-builtin) works well
> with no extra dependencies.

部署简单点的话,[内置引擎](/concepts/memory-builtin) 不用额外依赖,效果也不错。

## 排障

> **QMD not found?** Ensure the binary is on the gateway's `PATH`. If OpenClaw
> runs as a service, create a symlink:
> `sudo ln -s ~/.bun/bin/qmd /usr/local/bin/qmd`.

**找不到 QMD?** 确认二进制在 gateway 进程的 `PATH` 里。OpenClaw 作为服务跑的话,建一个软链:`sudo ln -s ~/.bun/bin/qmd /usr/local/bin/qmd`。

> If `qmd --version` works in your shell but OpenClaw still reports
> `spawn qmd ENOENT`, the gateway process likely has a different `PATH` than your
> interactive shell. Pin the binary explicitly:

如果你的 shell 里 `qmd --version` 能跑,但 OpenClaw 还报 `spawn qmd ENOENT`,大概率是 gateway 进程的 `PATH` 跟你交互式 shell 的不一样。把二进制路径显式钉死:

```json5
{
  memory: {
    backend: "qmd",
    qmd: {
      command: "/absolute/path/to/qmd",
    },
  },
}
```

> Use `command -v qmd` in the environment where QMD is installed, then recheck
> with `openclaw memory status --deep`.

在装了 QMD 的那个环境里跑 `command -v qmd` 拿到路径,然后用 `openclaw memory status --deep` 重新检查。

> **First search very slow?** QMD downloads GGUF models on first use. Pre-warm
> with `qmd query "test"` using the same XDG dirs OpenClaw uses.

**第一次检索特别慢?** QMD 在首次使用时会下载 GGUF 模型。用 OpenClaw 用的同一份 XDG 目录提前跑一次 `qmd query "test"` 预热。

> **Many QMD subprocesses during search?** Update QMD if possible. OpenClaw uses
> one process for same-source multi-collection searches only when the installed
> QMD advertises support for multiple `-c` filters; otherwise it keeps the older
> per-collection fallback for correctness.

**检索期间起了一堆 QMD 子进程?** 能升级 QMD 就升级。OpenClaw 只在装的 QMD 声明支持多个 `-c` 过滤时,才用单进程做同源多 collection 检索;否则为了正确性保留老的"按 collection 单独跑"的回退。

> **BM25-only QMD still trying to build llama.cpp?** Set
> `memory.qmd.searchMode = "search"`. OpenClaw treats that mode as lexical-only,
> does not run QMD vector status probes or embedding maintenance, and leaves
> semantic readiness checks to `vsearch` or `query` setups.

**只想用 BM25 的 QMD 还在尝试构建 llama.cpp?** 把 `memory.qmd.searchMode` 设成 `"search"`。OpenClaw 把这个模式当成纯词法检索,不跑 QMD 向量状态探测,也不做嵌入维护;语义就绪检查留给 `vsearch` 或 `query` 部署。

> **Search times out?** Increase `memory.qmd.limits.timeoutMs` (default: 4000ms).
> Set to `120000` for slower hardware.

**检索超时?** 把 `memory.qmd.limits.timeoutMs` 调大(默认 4000 毫秒)。慢机器设 `120000`。

> **Empty results in group chats?** Check `memory.qmd.scope` -- the default only
> allows direct and channel sessions.

**群聊里返回空结果?** 看 `memory.qmd.scope` —— 默认只允许私聊和频道会话。

> **Root memory search suddenly got too broad?** Restart the gateway or wait for
> the next startup reconciliation. OpenClaw recreates stale managed collections
> back to canonical `MEMORY.md` and `memory/` patterns when it detects a same-name
> conflict.

**根级记忆检索范围突然变得过宽?** 重启 gateway 或等下一次启动对账。OpenClaw 检测到同名冲突时,会把过期的受管理 collection 重建回规范的 `MEMORY.md` 和 `memory/` 模式。

> **Workspace-visible temp repos causing `ENAMETOOLONG` or broken indexing?**
> QMD traversal currently follows the underlying QMD scanner behavior rather than
> OpenClaw's builtin symlink rules. Keep temporary monorepo checkouts under
> hidden directories like `.tmp/` or outside indexed QMD roots until QMD exposes
> cycle-safe traversal or explicit exclusion controls.

**工作区里能看到的临时仓库引起 `ENAMETOOLONG` 或索引损坏?** QMD 的目录遍历目前跟着 QMD 自己的扫描器走,不走 OpenClaw 内置的 symlink 规则。在 QMD 暴露循环安全的遍历或显式排除控制之前,把临时 monorepo checkout 放在 `.tmp/` 这种隐藏目录下,或者放到索引的 QMD 根目录之外。

## 配置

> For the full config surface (`memory.qmd.*`), search modes, update intervals,
> scope rules, and all other knobs, see the
> [Memory configuration reference](/reference/memory-config).

完整的配置面(`memory.qmd.*`)、检索模式、更新间隔、作用域规则和其他所有调节项,见 [记忆配置参考](/reference/memory-config)。

## 相关

> - [Memory overview](/concepts/memory)
> - [Builtin memory engine](/concepts/memory-builtin)
> - [Honcho memory](/concepts/memory-honcho)

- [记忆总览](/concepts/memory)
- [内置记忆引擎](/concepts/memory-builtin)
- [Honcho 记忆](/concepts/memory-honcho)
