# Honcho memory

> [Honcho](https://honcho.dev) adds AI-native memory to OpenClaw. It persists
> conversations to a dedicated service and builds user and agent models over time,
> giving your agent cross-session context that goes beyond workspace Markdown
> files.

[Honcho](https://honcho.dev) 给 OpenClaw 加了一套 AI 原生的记忆系统。它把每次对话写进一个专门的服务,慢慢沉淀出用户模型和 agent 模型,让你的 agent 拥有跨会话的上下文 —— 这远超工作区里那些 Markdown 文件能做到的。

## 它提供什么

> - **Cross-session memory** -- conversations are persisted after every turn, so
>   context carries across session resets, compaction, and channel switches.
> - **User modeling** -- Honcho maintains a profile for each user (preferences,
>   facts, communication style) and for the agent (personality, learned
>   behaviors).
> - **Semantic search** -- search over observations from past conversations, not
>   just the current session.
> - **Multi-agent awareness** -- parent agents automatically track spawned
>   sub-agents, with parents added as observers in child sessions.

- **跨会话记忆** —— 每一轮对话结束都会写进存储,所以上下文能跨会话重置、跨压缩、跨通道切换。
- **用户建模** —— Honcho 为每个用户维护一份画像(偏好、事实、沟通风格),为 agent 维护另一份(性格、学到的行为模式)。
- **语义检索** —— 跨过往所有对话的观察做检索,不只是当前会话。
- **多 agent 感知** —— 父 agent 自动跟住派生的子 agent;父 agent 会以观察者身份出现在子会话里。

## 可用工具

> Honcho registers tools that the agent can use during conversation:

Honcho 注册了一组工具,agent 可以在对话里用:

> **Data retrieval (fast, no LLM call):**

**数据读取(快,不调 LLM)**:

> | Tool                        | What it does                                           |
> | --------------------------- | ------------------------------------------------------ |
> | `honcho_context`            | Full user representation across sessions               |
> | `honcho_search_conclusions` | Semantic search over stored conclusions                |
> | `honcho_search_messages`    | Find messages across sessions (filter by sender, date) |
> | `honcho_session`            | Current session history and summary                    |

| 工具                        | 做什么                                       |
| --------------------------- | -------------------------------------------- |
| `honcho_context`            | 跨会话的完整用户画像                         |
| `honcho_search_conclusions` | 在已存的结论上做语义检索                     |
| `honcho_search_messages`    | 跨会话找消息(可按发送者、日期过滤)           |
| `honcho_session`            | 当前会话的历史和摘要                         |

> **Q&A (LLM-powered):**

**问答(走 LLM)**:

> | Tool         | What it does                                                              |
> | ------------ | ------------------------------------------------------------------------- |
> | `honcho_ask` | Ask about the user. `depth='quick'` for facts, `'thorough'` for synthesis |

| 工具         | 做什么                                                                |
| ------------ | --------------------------------------------------------------------- |
| `honcho_ask` | 关于用户的问答。`depth='quick'` 查事实,`'thorough'` 做综合分析        |

## 上手

> Install the plugin and run setup:

装插件,然后跑配置:

```bash
openclaw plugins install @honcho-ai/openclaw-honcho
openclaw honcho setup
openclaw gateway --force
```

> The setup command prompts for your API credentials, writes the config, and
> optionally migrates existing workspace memory files.

setup 命令会让你输入 API 凭证,把配置写进去,还可以顺手把已有的工作区记忆文件迁过去。

> <Info>
> Honcho can run entirely locally (self-hosted) or via the managed API at
> `api.honcho.dev`. No external dependencies are required for the self-hosted
> option.
> </Info>

[展开: 信息] Honcho 可以完全本地跑(自托管),也可以走托管的 API(`api.honcho.dev`)。自托管不需要任何外部依赖。

## 配置

> Settings live under `plugins.entries["openclaw-honcho"].config`:

配置项在 `plugins.entries["openclaw-honcho"].config` 下:

```json5
{
  plugins: {
    entries: {
      "openclaw-honcho": {
        config: {
          apiKey: "your-api-key", // 自托管时不填
          workspaceId: "openclaw", // 记忆隔离
          baseUrl: "https://api.honcho.dev",
        },
      },
    },
  },
}
```

> For self-hosted instances, point `baseUrl` to your local server (for example
> `http://localhost:8000`) and omit the API key.

自托管实例:把 `baseUrl` 指向你本地的服务器(例如 `http://localhost:8000`),API key 不填。

## 迁移已有记忆

> If you have existing workspace memory files (`USER.md`, `MEMORY.md`,
> `IDENTITY.md`, `memory/`, `canvas/`), `openclaw honcho setup` detects and
> offers to migrate them.

你已经有工作区记忆文件(`USER.md`、`MEMORY.md`、`IDENTITY.md`、`memory/`、`canvas/`),`openclaw honcho setup` 会识别出来,问你要不要迁过去。

> <Info>
> Migration is non-destructive -- files are uploaded to Honcho. Originals are
> never deleted or moved.
> </Info>

[展开: 信息] 迁移是无损的 —— 文件上传到 Honcho,原件既不会被删也不会被移走。

## 怎么工作的

> After every AI turn, the conversation is persisted to Honcho. Both user and
> agent messages are observed, allowing Honcho to build and refine its models over
> time.

每一轮 AI 对话结束后,会话会写进 Honcho。用户消息和 agent 消息都会被观察到,Honcho 据此持续构建和打磨自己的模型。

> During conversation, Honcho tools query the service in the `before_prompt_build`
> phase, injecting relevant context before the model sees the prompt. This ensures
> accurate turn boundaries and relevant recall.

对话过程中,Honcho 工具在 `before_prompt_build` 阶段查询服务,在模型看到 prompt 之前就把相关上下文注入进去。这能保证轮次边界准确,召回也相关。

## Honcho vs 内置记忆

> |                   | Builtin / QMD                | Honcho                              |
> | ----------------- | ---------------------------- | ----------------------------------- |
> | **Storage**       | Workspace Markdown files     | Dedicated service (local or hosted) |
> | **Cross-session** | Via memory files             | Automatic, built-in                 |
> | **User modeling** | Manual (write to MEMORY.md)  | Automatic profiles                  |
> | **Search**        | Vector + keyword (hybrid)    | Semantic over observations          |
> | **Multi-agent**   | Not tracked                  | Parent/child awareness              |
> | **Dependencies**  | None (builtin) or QMD binary | Plugin install                      |

|                | 内置 / QMD                      | Honcho                          |
| -------------- | ------------------------------- | ------------------------------- |
| **存储**       | 工作区 Markdown 文件            | 专门的服务(本地或托管)          |
| **跨会话**     | 靠记忆文件做                    | 自动、内建                      |
| **用户建模**   | 手动(写到 MEMORY.md)            | 自动画像                        |
| **检索**       | 向量 + 关键字(混合)             | 在观察上做语义检索              |
| **多 agent**  | 不跟踪                          | 父 / 子感知                     |
| **依赖**       | 无(内置)或 QMD 二进制           | 装插件                          |

> Honcho and the builtin memory system can work together. When QMD is configured,
> additional tools become available for searching local Markdown files alongside
> Honcho's cross-session memory.

Honcho 和内置记忆系统能配合用。配上 QMD 之后,还会出现新工具,用来搜索本地 Markdown 文件 —— 和 Honcho 的跨会话记忆并存。

## CLI 命令

```bash
openclaw honcho setup                        # 配置 API key,迁移文件
openclaw honcho status                       # 看连接状态
openclaw honcho ask <question>               # 关于用户的问答
openclaw honcho search <query> [-k N] [-d D] # 在记忆上做语义检索
```

## 延伸阅读

> - [Plugin source code](https://github.com/plastic-labs/openclaw-honcho)
> - [Honcho documentation](https://docs.honcho.dev)
> - [Honcho OpenClaw integration guide](https://docs.honcho.dev/v3/guides/integrations/openclaw)
> - [Memory](/concepts/memory) -- OpenClaw memory overview
> - [Context Engines](/concepts/context-engine) -- how plugin context engines work

- [插件源码](https://github.com/plastic-labs/openclaw-honcho)
- [Honcho 官方文档](https://docs.honcho.dev)
- [Honcho 接入 OpenClaw 指南](https://docs.honcho.dev/v3/guides/integrations/openclaw)
- [记忆](/concepts/memory) —— OpenClaw 记忆总览
- [上下文引擎](/concepts/context-engine) —— 插件式上下文引擎怎么工作

## 相关

> - [Memory overview](/concepts/memory)
> - [Builtin memory engine](/concepts/memory-builtin)
> - [QMD memory engine](/concepts/memory-qmd)

- [记忆总览](/concepts/memory)
- [内置记忆引擎](/concepts/memory-builtin)
- [QMD 记忆引擎](/concepts/memory-qmd)
