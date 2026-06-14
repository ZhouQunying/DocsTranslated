# Grok Search

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
