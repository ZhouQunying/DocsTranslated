# Kimi Search

OpenClaw 支持 Kimi 作为 `web_search` 提供者，使用 Moonshot 网页搜索生成带引用的 AI 合成答案。

## 获取 API 密钥

1. 从 [Moonshot AI](https://platform.moonshot.cn/) 获取 API 密钥
2. 在 Gateway 环境中设置 `KIMI_API_KEY` 或 `MOONSHOT_API_KEY`，或通过以下方式配置：

```bash
openclaw configure --section web
```

在 `openclaw onboard` 或 `openclaw configure --section web` 中选择 **Kimi** 时，OpenClaw 还可询问：

- Moonshot API 区域：`https://api.moonshot.ai/v1` 或 `https://api.moonshot.cn/v1`
- 默认 Kimi 网页搜索模型（默认 `kimi-k2.6`）

## 配置

```json5
{
  plugins: {
    entries: {
      moonshot: {
        config: {
          webSearch: {
            apiKey: "sk-...", // 如设置了 KIMI_API_KEY 或 MOONSHOT_API_KEY 则可省略
            baseUrl: "https://api.moonshot.ai/v1",
            model: "kimi-k2.6",
          },
        },
      },
    },
  },
  tools: {
    web: {
      search: {
        provider: "kimi",
      },
    },
  },
}
```

如使用中国 API 主机进行聊天（`models.providers.moonshot.baseUrl`: `https://api.moonshot.cn/v1`），当 `tools.web.search.kimi.baseUrl` 被省略时，OpenClaw 会为 Kimi `web_search` 复用同一主机，使来自 [platform.moonshot.cn](https://platform.moonshot.cn/) 的密钥不会误触国际端点（通常会返回 HTTP 401）。需要不同的搜索基础 URL 时使用 `tools.web.search.kimi.baseUrl` 覆盖。

**环境替代方案：** 在 Gateway 环境中设置 `KIMI_API_KEY` 或 `MOONSHOT_API_KEY`。对于网关安装，放在 `~/.openclaw/.env` 中。

如省略 `baseUrl`，OpenClaw 默认使用 `https://api.moonshot.ai/v1`。如省略 `model`，OpenClaw 默认使用 `kimi-k2.6`。

## 工作原理

Kimi 使用 Moonshot 网页搜索合成带内联引用的答案，类似于 Gemini 和 Grok 的接地响应方法。

OpenClaw 仅在 Moonshot 返回原生网页搜索接地证据（如可重放的 `$web_search` 工具负载、`search_results` 或引用 URL）后才将 Kimi `web_search` 视为成功。如 Kimi 立即停止并返回纯聊天答案如"我无法浏览互联网"且无接地证据，OpenClaw 返回结构化的 `kimi_web_search_ungrounded` 错误而非将该文本包装为搜索结果。此时应重试查询、切换到 Brave 等结构化提供者，或在已有目标 URL 时使用 `web_fetch` / 浏览器工具。

## 支持的参数

Kimi 搜索支持 `query`。

`count` 被接受以兼容共享 `web_search`，但 Kimi 仍返回一个带引用的合成答案而非 N 结果列表。目前不支持提供者特定的过滤器。

## 相关

- [网页搜索概览](/tools/web)——所有提供者和自动检测
- [Moonshot AI](/providers/moonshot)——Moonshot 模型 + Kimi Coding 提供者文档
- [Gemini Search](/tools/gemini-search)——通过 Google 接地的 AI 合成答案
- [Grok Search](/tools/grok-search)——通过 xAI 接地的 AI 合成答案
