# Brave Search

## 架构精读

> 跳过不影响阅读翻译正文。

### `web` vs `llm-context`——两种传输模式什么时候该选哪个？

Brave 提供两种 API 端点：标准网页搜索（`web`）和 LLM Context API（`llm-context`）。两者返回的数据结构完全不同。

`web` 模式返回传统搜索结果——标题、URL、摘要片段。agent 拿到的是一个"目录"，需要自己决定点哪个链接、读哪个页面。这跟人类用 Google 搜索的体验一样：看摘要判断相关性，点开感兴趣的细读。

`llm-context` 模式返回预提取的文本块和来源——Brave 已经帮你读过页面了，直接把关键内容抽出来给你。这跟 RAG（检索增强生成）管道里的"chunk retrieval"是一个思路：不是给 LLM 一堆链接让它自己点，而是直接给它提取好的文本片段。

选择逻辑：
- agent 需要"浏览多个结果做判断"（比如"调研一下 X 技术的现状"）→ 用 `web`，给 agent 选择权
- agent 需要"找到 X 的具体答案"（比如"PostgreSQL 的 vacuum 怎么工作"）→ 用 `llm-context`，省掉二次 `web_fetch` 调用

### LLM Context API 为什么省掉一次工具调用？

传统流程：`web_search`（拿链接列表）→ agent 选 1-2 个最相关的 → `web_fetch`（读页面内容）→ agent 基于内容回答。两次工具调用，两次延迟。

LLM Context 流程：`web_search`（拿已提取的文本块）→ agent 直接基于文本块回答。一次工具调用，一次延迟。

代价是失去了"浏览多个结果"的灵活性——Brave 替你选了哪些页面值得读，你只能接受它的选择。如果 Brave 的提取质量不好（漏了关键段落、抽错了页面），agent 拿到的就是噪声。

这是 RAG 系统的经典权衡：预处理越多，运行时越快；但预处理错了，纠正成本也高。

---

OpenClaw 支持 Brave Search API 作为 `web_search` 提供者。

## 获取 API 密钥

1. 在 [https://brave.com/search/api/](https://brave.com/search/api/) 创建 Brave Search API 账户
2. 在控制台中选择 **Search** 计划并生成 API 密钥
3. 将密钥存储在配置中或在 Gateway 环境中设置 `BRAVE_API_KEY`

## 配置示例

```json5
{
  plugins: {
    entries: {
      brave: {
        config: {
          webSearch: {
            apiKey: "BRAVE_API_KEY_HERE",
            mode: "web", // 或 "llm-context"
            baseUrl: "https://api.search.brave.com", // 可选代理/基础 URL 覆盖
          },
        },
      },
    },
  },
  tools: {
    web: {
      search: {
        provider: "brave",
        maxResults: 5,
        timeoutSeconds: 30,
      },
    },
  },
}
```

Brave 搜索设置现在位于 `plugins.entries.brave.config.webSearch.*`。旧版 `tools.web.search.apiKey` 仍通过兼容层加载，但不再是规范配置路径。

`webSearch.mode` 控制 Brave 传输方式：

- `web`（默认）：标准 Brave 网页搜索，返回标题、URL 和摘要
- `llm-context`：Brave LLM Context API，返回预提取的文本块和来源，用于知识接地

`webSearch.baseUrl` 可将 Brave 请求指向受信任的兼容代理或网关。OpenClaw 会在配置的基础 URL 后追加 `/res/v1/web/search` 或 `/res/v1/llm/context`，并将基础 URL 保留在缓存键中。公共端点必须使用 `https://`；`http://` 仅在受信任的回环或私有网络代理主机上被接受。

## 工具参数

| 参数 | 类型 | 描述 |
| --- | --- | --- |
| `query` | string | 搜索查询 |
| `count` | integer | 返回结果数（1–10） |
| `country` | string | 2 字母 ISO 国家代码（如 `US`、`DE`） |
| `language` | string | ISO 639-1 语言代码（如 `en`、`de`、`fr`） |
| `search_lang` | string | Brave 搜索语言代码（如 `en`、`en-gb`、`zh-hans`） |
| `ui_lang` | string | UI 元素的 ISO 语言代码，需包含区域子标签如 `en-US` |
| `freshness` | string | 时间过滤——`day` 表示 24 小时 |
| `date_after` | string | 仅返回此日期之后发布的结果（`YYYY-MM-DD`） |
| `date_before` | string | 仅返回此日期之前发布的结果（`YYYY-MM-DD`） |

**示例：**

```javascript
// 国家和语言特定搜索
await web_search({
  query: "renewable energy",
  country: "DE",
  language: "de",
});

// 最近结果（过去一周）
await web_search({
  query: "AI news",
  freshness: "week",
});

// 日期范围搜索
await web_search({
  query: "AI developments",
  date_after: "2024-01-01",
  date_before: "2024-06-30",
});
```

## 注意事项

- OpenClaw 使用 Brave **Search** 计划。如有旧版订阅（如原始免费计划，每月 2,000 次查询），仍然有效但不包含 LLM Context 等新功能或更高的速率限制
- 每个 Brave 计划包含**每月 $5 免费额度**（自动续期）。Search 计划每 1,000 次请求 $5，因此额度覆盖每月 1,000 次查询。在 Brave 控制台设置用量限制以避免意外费用
- `llm-context` 模式返回接地的来源条目而非标准网页搜索摘要格式
- `llm-context` 模式支持 `freshness` 和有界的 `date_after` + `date_before` 范围。不支持 `ui_lang`；没有 `date_after` 的 `date_before` 会被拒绝，因为 Brave 要求自定义新鲜度范围同时包含起止日期
- 结果默认缓存 15 分钟（可通过 `cacheTtlMinutes` 配置）
- 自定义 `webSearch.baseUrl` 值包含在 Brave 缓存标识中，因此代理特定的响应不会冲突
- 启用 `brave.http` 诊断标志可在排查时记录 Brave 请求 URL/查询参数、响应状态/时序和搜索缓存命中/未命中/写入事件。该标志不会记录 API 密钥或响应体，但搜索查询可能敏感

## 相关

- [网页搜索概览](/tools/web)——所有提供者和自动检测
- [Perplexity Search](/tools/perplexity-search)——带域名过滤的结构化结果
- [Exa Search](/tools/exa-search)——带内容提取的神经搜索
