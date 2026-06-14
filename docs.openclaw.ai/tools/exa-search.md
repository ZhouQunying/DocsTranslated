# Exa Search

OpenClaw 支持 [Exa AI](https://exa.ai/) 作为 `web_search` 提供者。Exa 提供神经搜索、关键词搜索和混合搜索模式，内置内容提取（高亮、文本、摘要）。

## 获取 API 密钥

1. 在 [exa.ai](https://exa.ai/) 注册并从控制台生成 API 密钥
2. 在 Gateway 环境中设置 `EXA_API_KEY`，或通过以下方式配置：

```bash
openclaw configure --section web
```

## 配置

```json5
{
  plugins: {
    entries: {
      exa: {
        config: {
          webSearch: {
            apiKey: "exa-...", // 如设置了 EXA_API_KEY 则可省略
            baseUrl: "https://api.exa.ai", // 可选；OpenClaw 追加 /search
          },
        },
      },
    },
  },
  tools: {
    web: {
      search: {
        provider: "exa",
      },
    },
  },
}
```

**环境替代方案：** 在 Gateway 环境中设置 `EXA_API_KEY`。对于网关安装，放在 `~/.openclaw/.env` 中。

## 基础 URL 覆盖

当 Exa 搜索请求应经过兼容代理或备选 Exa 端点时，设置 `plugins.entries.exa.config.webSearch.baseUrl`。OpenClaw 通过在裸主机前加 `https://` 来规范化，并追加 `/search`（除非路径已以此结尾）。解析后的端点包含在搜索缓存键中，因此不同 Exa 端点的结果不会共享。

## 工具参数

| 参数 | 类型 | 描述 |
| --- | --- | --- |
| `query` | string | 搜索查询 |
| `count` | integer | 返回结果数（1–100） |
| `type` | string | 搜索模式 |
| `freshness` | string | 时间过滤 |
| `date_after` | string | 此日期之后的结果（`YYYY-MM-DD`） |
| `date_before` | string | 此日期之前的结果（`YYYY-MM-DD`） |
| `contents` | object | 内容提取选项（见下文） |

### 内容提取

Exa 可在搜索结果旁返回提取的内容。传递 `contents` 对象启用：

```javascript
await web_search({
  query: "transformer architecture explained",
  type: "neural",
  contents: {
    text: true, // 完整页面文本
    highlights: { numSentences: 3 }, // 关键句子
    summary: true, // AI 摘要
  },
});
```

| 内容选项 | 类型 | 描述 |
| --- | --- | --- |
| `text` | `boolean \| { maxCharacters }` | 提取完整页面文本 |
| `highlights` | `boolean \| { maxCharacters, query, numSentences, highlightsPerUrl }` | 提取关键句子 |
| `summary` | `boolean \| { query }` | AI 生成的摘要 |

### 搜索模式

| 模式 | 描述 |
| --- | --- |
| `auto` | Exa 选择最佳模式（默认） |
| `neural` | 语义/基于意义的搜索 |
| `fast` | 快速关键词搜索 |
| `deep` | 深度彻底搜索 |
| `deep-reasoning` | 带推理的深度搜索 |
| `instant` | 最快结果 |

## 注意事项

- 如未提供 `contents` 选项，Exa 默认使用 `{ highlights: true }`，结果包含关键句子摘录
- 结果在可用时保留 Exa API 响应中的 `highlightScores` 和 `summary` 字段
- 结果描述按高亮优先、摘要次之、全文最后的顺序解析——取最先可用的
- `freshness` 和 `date_after`/`date_before` 不能组合——使用一种时间过滤模式
- 每个查询最多可返回 100 个结果（受 Exa 搜索类型限制约束）
- 结果默认缓存 15 分钟（可通过 `cacheTtlMinutes` 配置）

## 相关

- [网页搜索概览](/tools/web)——所有提供者和自动检测
- [Brave Search](/tools/brave-search)——带国家/语言过滤的结构化结果
- [Perplexity Search](/tools/perplexity-search)——带域名过滤的结构化结果
