# Gemini Search

## 架构精读

> 跳过不影响阅读翻译正文。

### AI 合成答案 vs 原始搜索结果——本质区别在哪？

Brave/Perplexity 返回"这里有 10 个相关链接，你自己看"。Gemini Search 返回"根据 Google 搜索结果，答案是 X，引用来源是 Y"。

这是 RAG（检索增强生成）的两种形态：
- **传统 RAG**：检索 → 把检索结果塞进 prompt → LLM 生成答案。检索和生成是分开的两步，LLM 可能忽略检索结果或幻觉。
- **Grounded RAG**：LLM 在生成时实时参考检索结果，并标注引用。检索和生成是一体的，LLM 被约束在检索结果范围内生成。

Gemini Search 用的是后者——Google 称之为"grounding"（接地）。LLM 不是"看到搜索结果然后自由发挥"，而是"必须基于搜索结果回答，并标注每个事实的来源"。这大幅减少了幻觉，提高了事实准确性。

### 接地机制——为什么适合高可信度场景？

传统 LLM 回答"PostgreSQL 的 vacuum 作用是..."时，可能是基于训练数据（2023 年的知识）编造的。Gemini Search 回答同一问题时，会先搜 Google 拿到最新文档，然后基于这些文档生成答案，并标注"根据 PostgreSQL 16 文档..."。

这对医疗、法律、金融等高可信度场景至关重要：
- 医疗："X 药物的副作用"——必须基于最新临床数据，不能编造
- 法律："Y 法规的最新修订"——必须基于官方法律文本，不能猜测
- 金融："Z 公司的 Q3 财报"——必须基于实际披露，不能虚构

代价是失去了"浏览多个结果"的灵活性——Gemini 替你总结了，你不能自己点开链接细读。且答案质量依赖 Gemini 的合成能力——如果 Gemini 理解错了搜索结果，答案也会错。

---

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
