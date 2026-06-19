# Perplexity Search

## 架构精读

> 跳过不影响阅读翻译正文。

### 两种模式——结构化结果 vs AI 合成答案

Perplexity 在 OpenClaw 中有两种工作模式，返回的数据结构完全不同：

**Search API 模式**（默认）：返回结构化结果——`{title, url, snippet}`。跟 Brave 的标准搜索模式一样，给 agent 一个"目录"，agent 自己决定点哪个链接。支持丰富的过滤：国家、语言、时间范围、域名限制、内容类型。

**AI 合成模式**（旧版兼容）：返回 AI 生成的答案带引用。跟 Gemini/Grok/Kimi 一样，Perplexity 帮你总结好了。这是为了兼容已有的 Sonar/OpenRouter 设置——如果你之前用 OpenRouter 接 Perplexity Sonar，OpenClaw 检测到 `sk-or-...` 密钥或自定义 `baseUrl` 时自动切到这个模式。

选择逻辑：
- 新部署 → 用 Search API 模式（默认），灵活、可控
- 已有 OpenRouter/Sonar 设置 → AI 合成模式自动生效，无需改配置

### OpenRouter 兼容性——为什么不强制迁移？

OpenRouter 是一个模型聚合平台，让你用一个 API 密钥访问多个提供者的模型。很多用户已经通过 OpenRouter 接了 Perplexity Sonar。

OpenClaw 的设计是**不强制迁移**——检测到你用 OpenRouter 密钥时，自动切到兼容路径。这降低了迁移成本：你不需要重新注册 Perplexity 账户、生成新密钥、改配置。保持 `provider: "perplexity"` 和 `OPENROUTER_API_KEY` 就行。

这是向后兼容的设计哲学——新用户提供新路径，老用户保持旧路径。代价是代码复杂度增加（需要维护两条路径），但用户迁移摩擦降到零。

---

OpenClaw 支持 Perplexity Search API 作为 `web_search` 提供者。返回带 `title`、`url` 和 `snippet` 字段的结构化结果。

为兼容性考虑，OpenClaw 也支持旧版 Perplexity Sonar/OpenRouter 设置。如使用 `OPENROUTER_API_KEY`、在 `plugins.entries.perplexity.config.webSearch.apiKey` 中使用 `sk-or-...` 密钥、或设置了 `plugins.entries.perplexity.config.webSearch.baseUrl` / `model`，提供者切换到聊天补全路径，返回带引用的 AI 合成答案而非结构化 Search API 结果。

## 获取 Perplexity API 密钥

1. 在 [perplexity.ai/settings/api](https://www.perplexity.ai/settings/api) 创建 Perplexity 账户
2. 在控制台生成 API 密钥
3. 将密钥存储在配置中或在 Gateway 环境中设置 `PERPLEXITY_API_KEY`

## OpenRouter 兼容性

如已通过 OpenRouter 使用 Perplexity Sonar，保持 `provider: "perplexity"` 并在 Gateway 环境中设置 `OPENROUTER_API_KEY`，或将 `sk-or-...` 密钥存储在 `plugins.entries.perplexity.config.webSearch.apiKey`。

可选兼容性控制：

- `plugins.entries.perplexity.config.webSearch.baseUrl`
- `plugins.entries.perplexity.config.webSearch.model`

## 配置示例

### 原生 Perplexity Search API

```json5
{
  plugins: {
    entries: {
      perplexity: {
        config: {
          webSearch: {
            apiKey: "pplx-...",
          },
        },
      },
    },
  },
  tools: {
    web: {
      search: {
        provider: "perplexity",
      },
    },
  },
}
```

### OpenRouter / Sonar 兼容性

```json5
{
  plugins: {
    entries: {
      perplexity: {
        config: {
          webSearch: {
            apiKey: "<openrouter-api-key>",
            baseUrl: "https://openrouter.ai/api/v1",
            model: "perplexity/sonar-pro",
          },
        },
      },
    },
  },
  tools: {
    web: {
      search: {
        provider: "perplexity",
      },
    },
  },
}
```

## 密钥存储位置

**配置方式：** 运行 `openclaw configure --section web`。它将密钥存储在 `~/.openclaw/openclaw.json` 的 `plugins.entries.perplexity.config.webSearch.apiKey` 下。该字段也接受 SecretRef 对象。

**环境方式：** 在 Gateway 进程环境中设置 `PERPLEXITY_API_KEY` 或 `OPENROUTER_API_KEY`。对于网关安装，放在 `~/.openclaw/.env` 中。

如 `provider: "perplexity"` 已配置且 Perplexity 密钥 SecretRef 未解析且无环境回退，启动/重载会快速失败。

## 工具参数

以下参数适用于原生 Perplexity Search API 路径。

| 参数 | 类型 | 描述 |
| --- | --- | --- |
| `query` | string | 搜索查询 |
| `count` | integer | 返回结果数（1-10） |
| `country` | string | 2 字母 ISO 国家代码（如 `US`、`DE`） |
| `language` | string | ISO 639-1 语言代码（如 `en`、`de`、`fr`） |
| `freshness` | string | 时间过滤——`day` 表示 24 小时 |
| `date_after` | string | 仅返回此日期之后发布的结果（`YYYY-MM-DD`） |
| `date_before` | string | 仅返回此日期之前发布的结果（`YYYY-MM-DD`） |
| `domain_filter` | string array | 域名白名单/黑名单数组（最多 20） |
| `max_tokens` | integer | 总内容预算（最多 1000000） |
| `max_tokens_per_page` | integer | 每页 token 限制 |

对于旧版 Sonar/OpenRouter 兼容性路径：

- 接受 `query`、`count` 和 `freshness`
- `count` 在该路径下仅用于兼容性；响应仍为一个带引用的合成答案而非 N 结果列表
- 仅 Search API 的过滤器如 `country`、`language`、`date_after`、`date_before`、`domain_filter`、`max_tokens` 和 `max_tokens_per_page` 会返回显式错误

**示例：**

```javascript
// 国家和语言特定搜索
await web_search({ query: "renewable energy", country: "DE", language: "de" });

// 最近结果（过去一周）
await web_search({ query: "AI news", freshness: "week" });

// 域名过滤（白名单）
await web_search({
  query: "climate research",
  domain_filter: ["nature.com", "science.org", ".edu"],
});

// 域名过滤（黑名单——以 - 为前缀）
await web_search({
  query: "product reviews",
  domain_filter: ["-reddit.com", "-pinterest.com"],
});
```

### 域名过滤规则

- 每个过滤器最多 20 个域名
- 不能在同一请求中混合白名单和黑名单
- 黑名单条目使用 `-` 前缀（如 `["-reddit.com"]`）

## 注意事项

- Perplexity Search API 返回结构化网页搜索结果（`title`、`url`、`snippet`）
- OpenRouter 或显式 `plugins.entries.perplexity.config.webSearch.baseUrl` / `model` 会将 Perplexity 切回 Sonar 聊天补全以兼容
- Sonar/OpenRouter 兼容性返回一个带引用的合成答案，而非结构化结果行
- 结果默认缓存 15 分钟（可通过 `cacheTtlMinutes` 配置）

## 相关

- [网页搜索概览](/tools/web)——所有提供者和自动检测规则
- [Brave search](/tools/brave-search)——带国家和语言过滤的结构化结果
- [Exa search](/tools/exa-search)——带内容提取的神经搜索
- [Perplexity Search API 文档](https://docs.perplexity.ai/)——官方 Perplexity Search API 快速入门和参考
