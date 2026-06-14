# Tavily

[Tavily](https://tavily.com) 是专为 AI 应用设计的搜索 API。OpenClaw 以两种方式暴露它：

- 作为通用搜索工具 `web_search` 的提供者
- 作为显式插件工具：`tavily_search` 和 `tavily_extract`

Tavily 返回为 LLM 消费优化的结构化结果。支持可配置的搜索深度、主题过滤、域名过滤、AI 生成的答案摘要和从 URL 提取内容（包括 JavaScript 渲染的页面）。

| 属性 | 值 |
| --- | --- |
| 插件 id | `tavily` |
| 认证 | `TAVILY_API_KEY` 或配置 `apiKey` |
| 基础 URL | `https://api.tavily.com`（默认） |
| 捆绑工具 | `tavily_search`、`tavily_extract` |

## 快速开始

1. 在 [tavily.com](https://tavily.com) 创建账户，在控制台生成 API 密钥
2. 配置插件和提供者：

```json5
{
  plugins: {
    entries: {
      tavily: {
        enabled: true,
        config: {
          webSearch: {
            apiKey: "tvly-...", // 如设置了 TAVILY_API_KEY 则可省略
            baseUrl: "https://api.tavily.com",
          },
        },
      },
    },
  },
  tools: {
    web: {
      search: {
        provider: "tavily",
      },
    },
  },
}
```

3. 从任何 agent 触发 `web_search`，或直接调用 `tavily_search` 验证搜索运行

在引导流程或 `openclaw configure --section web` 中选择 Tavily 会自动启用捆绑的 Tavily 插件。

## 工具参考

### `tavily_search`

需要 Tavily 特定搜索控制而非通用 `web_search` 时使用。

| 参数 | 类型 | 约束/默认值 | 描述 |
| --- | --- | --- | --- |
| `query` | string | 必填 | 搜索查询字符串。保持在 400 字符以内 |
| `search_depth` | enum | `basic`（默认）、`advanced` | `advanced` 更慢但相关性更高 |
| `topic` | enum | `general`（默认）、`news`、`finance` | 按主题族过滤 |
| `max_results` | integer | 1-20 | 结果数量 |
| `include_answer` | boolean | 默认 `false` | 包含 Tavily AI 生成的答案摘要 |
| `time_range` | enum | `day`、`week`、`month`、`year` | 按时间过滤结果 |
| `include_domains` | string array | 无 | 仅包含这些域名的结果 |
| `exclude_domains` | string array | 无 | 排除这些域名的结果 |

搜索深度权衡：

| 深度 | 速度 | 相关性 | 适用场景 |
| --- | --- | --- | --- |
| `basic` | 更快 | 高 | 通用查询（默认） |
| `advanced` | 更慢 | 最高 | 精确研究和事实查找 |

### `tavily_extract`

从一个或多个 URL 提取干净内容。处理 JavaScript 渲染的页面，支持查询聚焦的分块以进行定向提取。

| 参数 | 类型 | 约束/默认值 | 描述 |
| --- | --- | --- | --- |
| `urls` | string array | 必填，1-20 | 要提取内容的 URL |
| `query` | string | 可选 | 按查询相关性重排提取的块 |
| `extract_depth` | enum | `basic`（默认）、`advanced` | `advanced` 用于 JS 密集页面、SPA 或动态表格 |
| `chunks_per_source` | integer | 1-5；**需要 `query`** | 每个 URL 返回的块数。没有 `query` 时报错 |
| `include_images` | boolean | 默认 `false` | 在结果中包含图片 URL |

提取深度权衡：

| 深度 | 适用场景 |
| --- | --- |
| `basic` | 简单页面。先试这个 |
| `advanced` | JS 渲染的 SPA、动态内容、表格 |

将较大的 URL 列表分批为多次 `tavily_extract` 调用（每次请求最多 20 个）。使用 `query` 加 `chunks_per_source` 仅获取相关内容而非完整页面。

## 选择正确的工具

| 需求 | 工具 |
| --- | --- |
| 快速网页搜索，无需特殊选项 | `web_search` |
| 带深度、主题、AI 答案的搜索 | `tavily_search` |
| 从特定 URL 提取内容 | `tavily_extract` |

通用 `web_search` 工具使用 Tavily 作为提供者时支持 `query` 和 `count`（最多 20 个结果）。需要 Tavily 特定控制（`search_depth`、`topic`、`include_answer`、域名过滤、时间范围）时，使用 `tavily_search`。

## 高级配置

Tavily 客户端按此顺序查找 API 密钥：

1. `plugins.entries.tavily.config.webSearch.apiKey`（通过 SecretRef 解析）
2. Gateway 环境中的 `TAVILY_API_KEY`

两者都不存在时 `tavily_extract` 会报告设置错误。

如需通过代理前置 Tavily，覆盖 `plugins.entries.tavily.config.webSearch.baseUrl`。默认为 `https://api.tavily.com`。

`chunks_per_source` 需要 `query`：`tavily_extract` 会拒绝传递 `chunks_per_source` 但没有 `query` 的调用。Tavily 按查询相关性排列块，因此该参数没有查询时毫无意义。

## 相关

- [网页搜索概览](/tools/web)——所有提供者和自动检测规则
- [Firecrawl](/tools/firecrawl)——搜索加抓取和内容提取
- [Exa Search](/tools/exa-search)——带内容提取的神经搜索
- [配置](/gateway/configuration-reference)——插件条目和工具路由的完整配置模式
