# Parallel Search

OpenClaw 捆绑了两个 [Parallel](https://parallel.ai/) `web_search` 提供者：

- **Parallel Search (Free)**（`parallel-free`）——Parallel 的免费 [Search MCP](https://docs.parallel.ai/integrations/mcp/search-mcp)。无需账户或 API 密钥。未配置其他网页搜索提供者时 OpenClaw 自动选择它，使 `web_search` 无需设置即可工作
- **Parallel Search**（`parallel`）——Parallel 的付费 Search API。需要 `PARALLEL_API_KEY`，提供更高的速率限制和目标调优

两者都返回从为 AI agent 构建的网页索引中排名的、LLM 优化的摘录。将 `tools.web.search.provider` 设为 `parallel-free` 或 `parallel` 以显式选择。

OpenAI Responses 模型在 `tools.web.search.provider` 未设置时使用 OpenAI 原生网页搜索，因此会绕过 Parallel 提供者。将 `tools.web.search.provider` 设为 `parallel-free` 或 `parallel` 可将其路由到 Parallel。

## API 密钥（付费提供者）

`parallel-free` 无需设置。付费 `parallel` 提供者需要 API 密钥：

1. 在 [platform.parallel.ai](https://platform.parallel.ai) 注册并从控制台生成 API 密钥
2. 在 Gateway 环境中设置 `PARALLEL_API_KEY`，或通过以下方式配置：

```bash
openclaw configure --section web
```

## 配置

```json5
{
  plugins: {
    entries: {
      parallel: {
        config: {
          webSearch: {
            apiKey: "par-...", // 如设置了 PARALLEL_API_KEY 则可省略
            baseUrl: "https://api.parallel.ai", // 可选；OpenClaw 追加 /v1/search
          },
        },
      },
    },
  },
  tools: {
    web: {
      search: {
        provider: "parallel",
      },
    },
  },
}
```

**环境替代方案：** 在 Gateway 环境中设置 `PARALLEL_API_KEY`。对于网关安装，放在 `~/.openclaw/.env` 中。

## 基础 URL 覆盖

基础 URL 覆盖仅适用于付费 `parallel` 提供者。免费 `parallel-free` 提供者始终使用 `https://search.parallel.ai/mcp`。

当 Parallel 请求应经过兼容代理或备选 Parallel 端点（如 Cloudflare AI Gateway）时，设置 `plugins.entries.parallel.config.webSearch.baseUrl`。OpenClaw 通过在裸主机前加 `https://` 来规范化，并追加 `/v1/search`（除非路径已以此结尾）。解析后的端点包含在搜索缓存键中，因此不同 Parallel 端点的结果不会共享。

## 工具参数

OpenClaw 暴露 Parallel 的原生搜索形态，使模型可同时填写自然语言目标和几个简短的关键词查询——这是 Parallel [推荐](https://docs.parallel.ai/search/best-practices)的最佳结果搭配。

| 参数 | 类型 | 描述 |
| --- | --- | --- |
| `query` | string | 底层问题或目标的自然语言描述（最多 5000 字符）。应为自包含的 |
| `queries` | string array | 简洁的关键词搜索查询，每个 3-6 词（1-5 条，每条最多 200 字符）。提供 2-3 个多样化查询以获得最佳结果 |
| `count` | integer | 返回结果数（1-40） |
| `sessionId` | string | 可选 Parallel 会话 id。在同一任务的后续搜索中传递之前 Parallel 结果的 `sessionId`，使 Parallel 可分组相关调用并改善后续结果 |
| `modelId` | string | 可选的调用模型标识符（如 `claude-opus-4-7`、`gpt-5.5`）。让 Parallel 根据模型能力调整默认设置。传递精确的活跃模型标识；不要缩短为族别名 |

## 注意事项

- Parallel 基于 LLM 推理效用而非人类点击率排名和压缩结果；预期每个结果中的密集摘录而非完整页面内容
- 结果摘录以 `excerpts` 数组返回，同时合并到 `description` 字段以兼容通用 `web_search` 契约
- Parallel 在每个响应上返回 `session_id`；OpenClaw 在工具负载中以 `sessionId` 暴露它，供调用者分组后续搜索
- OpenClaw 始终将解析后的结果数作为 `advanced_settings.max_results` 转发给 Parallel。调用者的 `count` 参数优先，然后是顶层 `tools.web.search.maxResults` 设置，否则使用 OpenClaw 通用 `web_search` 默认值（5）。这在切换提供者时保持结果量一致
- 结果默认缓存 15 分钟（可通过 `cacheTtlMinutes` 配置）
- 免费 `parallel-free` 提供者接受相同参数。它在客户端应用 `count`，在未提供时为每次调用生成 `session_id`

## 相关

- [网页搜索概览](/tools/web)——所有提供者和自动检测
- [Exa search](/tools/exa-search)——带内容提取的神经搜索
- [Perplexity Search](/tools/perplexity-search)——带域名过滤的结构化结果
