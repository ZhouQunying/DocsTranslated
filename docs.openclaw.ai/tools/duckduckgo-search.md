# DuckDuckGo Search

## 架构精读

> 跳过不影响阅读翻译正文。

### 没有官方 API——OpenClaw 怎么集成 DuckDuckGo？

DuckDuckGo 没有公开的搜索 API（至少没有免费的大规模访问接口）。OpenClaw 的集成是**实验性、非官方**的——它从 DuckDuckGo 的非 JavaScript 搜索页面抓取 HTML，解析 DOM 提取结果。

这跟用 BeautifulSoup 爬 Wikipedia 而非用 MediaWiki API 是一个思路。优势是零成本、无需密钥、开箱即用；劣势是脆弱——DuckDuckGo 改 HTML 结构、加 CAPTCHA、或上 Cloudflare 防护就会断。

### 为什么这是回退选项而非生产级提供者？

OpenClaw 的自动检测顺序里，DuckDuckGo 排第 100（第一个无需密钥的回退）。有 API 密钥的提供者（Brave、Perplexity、Exa）优先于它。

原因有三：
- **稳定性差**：HTML 解析依赖页面结构，DuckDuckGo 改版就断
- **速率受限**：大量请求会触发机器人检测，返回 CAPTCHA 或 403
- **结果质量不可控**：官方 API 有 SLA、有结构化返回、有错误码；HTML 抓取只能"尽力解析"

适合场景：开发测试、个人使用、不想注册 API 密钥的快速原型。生产环境应选 Brave（有免费层）、Perplexity、或其他 API 支持的提供者。

---

OpenClaw 支持 DuckDuckGo 作为**无需密钥**的 `web_search` 提供者。无需 API 密钥或账户。

DuckDuckGo 是**实验性、非官方**的集成，从 DuckDuckGo 的非 JavaScript 搜索页面抓取结果——而非官方 API。可能因机器人挑战页面或 HTML 变更而偶尔中断。

## 设置

无需 API 密钥——只需将 DuckDuckGo 设为提供者：

```bash
openclaw configure --section web
# 选择 "duckduckgo" 作为提供者
```

## 配置

```json5
{
  tools: {
    web: {
      search: {
        provider: "duckduckgo",
      },
    },
  },
}
```

可选的插件级区域和 SafeSearch 设置：

```json5
{
  plugins: {
    entries: {
      duckduckgo: {
        config: {
          webSearch: {
            region: "us-en", // DuckDuckGo 区域代码
            safeSearch: "moderate", // "strict"、"moderate" 或 "off"
          },
        },
      },
    },
  },
}
```

## 工具参数

| 参数 | 类型 | 描述 |
| --- | --- | --- |
| `query` | string | 搜索查询 |
| `count` | integer | 返回结果数（1-10） |
| `region` | string | DuckDuckGo 区域代码（如 `us-en`、`uk-en`、`de-de`） |
| `safeSearch` | string | SafeSearch 级别 |

区域和 SafeSearch 也可在插件配置中设置（见上文）——工具参数每次查询覆盖配置值。

## 注意事项

- **无需 API 密钥**——开箱即用，零配置
- **实验性**——从 DuckDuckGo 的非 JavaScript HTML 搜索页面收集结果，非官方 API 或 SDK
- **机器人挑战风险**——DuckDuckGo 可能在大量或自动化使用时提供 CAPTCHA 或阻止请求
- **HTML 解析**——结果依赖页面结构，可能随时变更
- **自动检测顺序**——DuckDuckGo 是第一个无需密钥的回退（顺序 100）。配置了密钥的 API 提供者优先运行，然后是 Ollama Web Search（顺序 110），再是 SearXNG（顺序 200）
- **SafeSearch 默认为 moderate**（未配置时）

生产环境中考虑使用 [Brave Search](/tools/brave-search)（有免费层）或其他 API 支持的提供者。

## 相关

- [网页搜索概览](/tools/web)——所有提供者和自动检测
- [Brave Search](/tools/brave-search)——带免费层的结构化结果
- [Exa Search](/tools/exa-search)——带内容提取的神经搜索
