# Grok Search

## 架构精读

> 跳过不影响阅读翻译正文。

### Grok vs Gemini——同样 AI 合成，信息源完全不同

Grok Search 和 Gemini Search 都返回 AI 合成答案带引用，但它们接地的信息源完全不同。

Gemini 接地的是 Google 搜索结果——网页、文档、新闻、学术论文。这是"公开网页"的视角，覆盖了过去 25 年的互联网内容。

Grok 接地的是 xAI 的网页搜索，但独特优势是**实时 X/Twitter 数据**。如果你的查询涉及社交媒体讨论、热点事件、用户观点、实时新闻反应，Grok 能拿到 Gemini 拿不到的内容。X/Twitter 是全球最大的实时公共对话平台——突发事件、产品发布、政治事件的即时反应都在这。

选择逻辑：
- 需要网页/文档/技术答案 → Gemini（Google 索引更全）
- 需要社交媒体视角/实时讨论/用户观点 → Grok（X/Twitter 数据独有）

### OAuth 复用——一次登录解锁三个工具

Grok 的认证设计很巧妙：一次 xAI OAuth 登录同时解锁三个工具：
- `web_search`（网页搜索，AI 合成答案）
- `x_search`（X/Twitter 帖子搜索）
- `code_execution`（Python 代码执行）

这降低了配置复杂度——不需要为每个工具单独管 API 密钥。OpenClaw 检测到 xAI OAuth 可用时，自动把 Grok 设为 `web_search` 提供者，无需用户手动配置。

对比其他提供者：Brave 需要单独的 `BRAVE_API_KEY`，Perplexity 需要 `PERPLEXITY_API_KEY`，Exa 需要 `EXA_API_KEY`。每个提供者一个密钥，管理成本线性增长。xAI 的 OAuth 复用是更优雅的认证模型。

---

OpenClaw 支持 Grok 作为 `web_search` 提供者，使用 xAI 网页接地响应生成由实时搜索结果支持的 AI 合成答案并附带引用。

Grok 网页搜索在 xAI OAuth 登录可用时优先使用。如无 OAuth 配置文件，同一 xAI API 密钥也可驱动内置的 `x_search` 工具（用于 X/Twitter 帖子搜索）和 `code_execution` 工具。如将密钥存储在 `plugins.entries.xai.config.webSearch.apiKey` 下，OpenClaw 也会将其作为捆绑 xAI 模型提供者的回退密钥复用。

对于帖子级 X 指标（如转发、回复、书签或浏览量），建议使用 `x_search` 配合精确的帖子 URL 或状态 ID，而非宽泛的搜索查询。

## 引导和配置

如在以下流程中选择 **Grok**：

- `openclaw onboard`
- `openclaw configure --section web`

OpenClaw 可使用已有的 xAI OAuth 配置文件而无需提示输入单独的搜索密钥。如 OAuth 不可用，回退到 xAI API 密钥设置。OpenClaw 还可显示后续步骤以使用相同 xAI 凭据启用 `x_search`。

## 登录或获取 API 密钥

**使用 xAI OAuth：** 如已在引导或模型认证期间使用 xAI 登录，选择 Grok 作为 `web_search` 提供者。无需单独的 API 密钥：

```bash
openclaw onboard --auth-choice xai-oauth
openclaw config set tools.web.search.provider grok
```

**使用 API 密钥回退：** OAuth 不可用时从 [xAI](https://console.x.ai/) 获取 API 密钥。在 Gateway 环境中设置 `XAI_API_KEY`，或通过以下方式配置：

```bash
openclaw configure --section web
```

## 配置

```json5
{
  plugins: {
    entries: {
      xai: {
        config: {
          webSearch: {
            apiKey: "xai-...", // 如有 xAI OAuth 或 XAI_API_KEY 则可省略
            baseUrl: "https://api.x.ai/v1", // 可选 Responses API 代理/基础 URL 覆盖
          },
        },
      },
    },
  },
  tools: {
    web: {
      search: {
        provider: "grok",
      },
    },
  },
}
```

**凭据替代方案：** 使用 `openclaw models auth login --provider xai --method oauth` 登录，在 Gateway 环境中设置 `XAI_API_KEY`，或存储 `plugins.entries.xai.config.webSearch.apiKey`。对于网关安装，将环境变量放在 `~/.openclaw/.env` 中。

## 工作原理

Grok 使用 xAI 网页接地响应合成带内联引用的答案，类似于 Gemini 的 Google Search 接地方法。

## 支持的参数

Grok 搜索支持 `query`。

`count` 被接受以兼容共享 `web_search`，但 Grok 仍返回一个带引用的合成答案而非 N 结果列表。目前不支持提供者特定的过滤器。

Grok 使用提供者特定的 60 秒默认超时，因为 xAI Responses 网页接地搜索可能比共享 `web_search` 默认超时更长。设置 `tools.web.search.timeoutSeconds` 可覆盖。

## 基础 URL 覆盖

当 Grok 网页搜索应经过操作者代理或兼容 xAI 的 Responses 端点时，设置 `plugins.entries.xai.config.webSearch.baseUrl`。OpenClaw 在去除尾部斜杠后向 `<baseUrl>/responses` 发送请求。`x_search` 使用相同的 `webSearch.baseUrl` 回退，除非设置了 `plugins.entries.xai.config.xSearch.baseUrl`。

## 相关

- [网页搜索概览](/tools/web)——所有提供者和自动检测
- [x_search](/tools/web#x_search)——通过 xAI 的一级 X 搜索
- [Gemini Search](/tools/gemini-search)——通过 Google 接地的 AI 合成答案
