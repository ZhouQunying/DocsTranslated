# 网页搜索

`web_search` 工具使用配置的提供者搜索网页并返回结果。结果按查询缓存 15 分钟（可配置）。

OpenClaw 还包括用于 X/Twitter 帖子搜索的 `x_search` 和轻量级 URL 获取的 `web_fetch`。`web_fetch` 保持本地运行，而 `web_search` 和 `x_search` 可在底层使用 xAI Responses。

`web_search` 是轻量级 HTTP 工具，不是浏览器自动化。对于 JS 密集网站或登录场景，使用 [Web Browser](/tools/browser)。获取特定 URL 使用 [Web Fetch](/tools/web-fetch)。

## 快速开始

1. **选择提供者**：选择一个提供者并完成必要的设置。有些提供者无需密钥，有些使用 API 密钥。参见下方提供者页面
2. **配置**：

```bash
openclaw configure --section web
```

这会存储提供者和任何需要的凭据。也可设置环境变量（如 `BRAVE_API_KEY`）跳过此步骤。

3. **使用**：agent 现在可以调用 `web_search`：

```javascript
await web_search({ query: "OpenClaw plugin SDK" });
await x_search({ query: "dinner recipes" });
```

## 选择提供者

| 提供者 | 结果风格 | 过滤器 | API 密钥 |
| --- | --- | --- | --- |
| [Brave](/tools/brave-search) | 结构化摘要 | 国家、语言、时间、`llm-context` 模式 | `BRAVE_API_KEY` |
| [DuckDuckGo](/tools/duckduckgo-search) | 结构化摘要 | -- | 无（无需密钥） |
| [Exa](/tools/exa-search) | 结构化 + 提取 | 神经/关键词模式、日期、内容提取 | `EXA_API_KEY` |
| [Firecrawl](/tools/firecrawl) | 结构化摘要 | 通过 `firecrawl_search` 工具 | `FIRECRAWL_API_KEY` |
| [Gemini](/tools/gemini-search) | AI 合成 + 引用 | -- | `GEMINI_API_KEY` |
| [Grok](/tools/grok-search) | AI 合成 + 引用 | -- | xAI OAuth 或 `XAI_API_KEY` |
| [Kimi](/tools/kimi-search) | AI 合成 + 引用 | -- | `KIMI_API_KEY` / `MOONSHOT_API_KEY` |
| [MiniMax](/tools/minimax-search) | 结构化摘要 | 区域（`global` / `cn`） | `MINIMAX_CODE_PLAN_KEY` |
| [Ollama](/tools/ollama-search) | 结构化摘要 | -- | 本地无需；`OLLAMA_API_KEY` |
| [Parallel](/tools/parallel-search) | LLM 优化的密集摘录 | -- | `PARALLEL_API_KEY`（付费） |
| [Parallel Free](/tools/parallel-search) | LLM 优化的密集摘录 | -- | 无（免费 MCP） |
| [Perplexity](/tools/perplexity-search) | 结构化摘要 | 国家、语言、时间、域名、内容限制 | `PERPLEXITY_API_KEY` |
| [SearXNG](/tools/searxng-search) | 结构化摘要 | 类别、语言 | 无（自托管） |
| [Tavily](/tools/tavily) | 结构化摘要 | 通过 `tavily_search` 工具 | `TAVILY_API_KEY` |

## 自动检测

当 `tools.web.search.provider` 未设置时，OpenClaw 按优先级顺序自动检测第一个就绪的提供者。有密钥的 API 提供者优先于无需密钥的回退。

## 原生 OpenAI 网页搜索

直接的 OpenAI Responses 模型在 OpenClaw 网页搜索启用且未固定托管提供者时自动使用 OpenAI 托管的 `web_search` 工具。这是捆绑 OpenAI 插件中的提供者自有行为，仅适用于原生 OpenAI API 流量，不适用于兼容 OpenAI 的代理基础 URL 或 Azure 路由。将 `tools.web.search.provider` 设为其他提供者（如 `brave`）可为 OpenAI 模型保留托管 `web_search` 工具。

## 网络安全性

托管 `web_search` 提供者调用使用 OpenClaw 的受守卫获取路径。对于受信任的提供者 API 主机，OpenClaw 仅对该提供者主机名允许 Surge、Clash 和 sing-box 假 IP DNS 应答在 `198.18.0.0/15` 和 `fc00::/7` 范围内。其他私有、回环、链路本地和元数据目标仍被阻止。

此自动允许不适用于任意 `web_fetch` URL。对于 `web_fetch`，仅当受信任代理持有这些合成范围时才显式启用 `tools.web.fetch.ssrfPolicy.allowRfc2544BenchmarkRange` 和 `tools.web.fetch.ssrfPolicy.allowIpv6UniqueLocalRange`。

## 相关

- [Web Fetch](/tools/web-fetch)——轻量级 URL 获取
- [Browser](/tools/browser)——完整浏览器自动化
- 各提供者页面——详细设置和参数
