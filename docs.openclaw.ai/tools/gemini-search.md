# Gemini Search

OpenClaw 支持带内置 [Google Search 接地](https://ai.google.dev/gemini-api/docs/grounding) 的 Gemini 模型，返回由实时 Google 搜索结果支持的 AI 合成答案并附带引用。

## 获取 API 密钥

1. 前往 [Google AI Studio](https://aistudio.google.com/apikey) 创建 API 密钥
2. 在 Gateway 环境中设置 `GEMINI_API_KEY`，或复用 `models.providers.google.apiKey`，或通过以下方式配置专用搜索密钥：

```bash
openclaw configure --section web
```

## 配置

```json5
{
  plugins: {
    entries: {
      google: {
        config: {
          webSearch: {
            apiKey: "AIza...", // 如设置了 GEMINI_API_KEY 或 models.providers.google.apiKey 则可省略
            baseUrl: "https://generativelanguage.googleapis.com/v1beta", // 可选；回退到 models.providers.google.baseUrl
            model: "gemini-2.5-flash", // 默认
          },
        },
      },
    },
  },
  tools: {
    web: {
      search: {
        provider: "gemini",
      },
    },
  },
}
```

**凭据优先级：** Gemini 网页搜索先使用 `plugins.entries.google.config.webSearch.apiKey`，然后是 `GEMINI_API_KEY`，再是 `models.providers.google.apiKey`。基础 URL 方面，专用的 `plugins.entries.google.config.webSearch.baseUrl` 优先于 `models.providers.google.baseUrl`。

对于网关安装，将环境变量放在 `~/.openclaw/.env` 中。

## 工作原理

与返回链接和摘要列表的传统搜索提供者不同，Gemini 使用 Google Search 接地生成带内联引用的 AI 合成答案。结果包括合成答案和来源 URL。

- Gemini 接地的引用 URL 会自动从 Google 重定向 URL 解析为直接 URL
- 重定向解析使用 SSRF 防护路径（HEAD + 重定向检查 + http/https 验证）后才返回最终引用 URL
- 重定向解析使用严格的 SSRF 默认值，因此到私有/内部目标的重定向会被阻止

## 支持的参数

Gemini 搜索支持 `query`、`freshness`、`date_after` 和 `date_before`。

`count` 被接受以兼容共享 `web_search`，但 Gemini 接地仍返回一个带引用的合成答案而非 N 结果列表。

`freshness` 接受 `day`、`week`、`month`、`year` 和共享快捷方式 `pd`、`pw`、`pm`、`py`。OpenClaw 将这些值或显式的 `date_after`/`date_before` 范围转换为 Gemini Google Search 接地的 `timeRangeFilter`。不支持 `country`、`language` 和 `domain_filter`。

## 模型选择

默认模型是 `gemini-2.5-flash`（快速且经济）。任何支持接地的 Gemini 模型都可通过 `plugins.entries.google.config.webSearch.model` 使用。

## 基础 URL 覆盖

当 Gemini 网页搜索必须经过操作者代理或自定义兼容 Gemini 端点时，设置 `plugins.entries.google.config.webSearch.baseUrl`。如未设置，Gemini 网页搜索复用 `models.providers.google.baseUrl`。纯 `https://generativelanguage.googleapis.com` 值会被规范化为 `https://generativelanguage.googleapis.com/v1beta`；自定义代理路径在去除尾部斜杠后保持原样。

## 相关

- [网页搜索概览](/tools/web)——所有提供者和自动检测
- [Brave Search](/tools/brave-search)——带摘要的结构化结果
- [Perplexity Search](/tools/perplexity-search)——结构化结果 + 内容提取
