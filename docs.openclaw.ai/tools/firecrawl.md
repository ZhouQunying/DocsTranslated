# Firecrawl

## 架构精读

> 跳过不影响阅读翻译正文。

### 三种角色——什么时候该用哪个？

Firecrawl 在 OpenClaw 中扮演三种角色：`web_search` 提供者、显式插件工具（`firecrawl_search` 和 `firecrawl_scrape`）、`web_fetch` 的备选提取器。这跟瑞士军刀是一个思路——能做很多事，但专用工具在各自场景下更高效。

选择逻辑：
- **需要反反爬抓取 JS 重站点**（新闻、社交媒体、Cloudflare 保护的页面）→ 用 `firecrawl_scrape`，显式调用
- **需要搜索+抓取一体化**（搜关键词同时拿到页面内容）→ 用 `firecrawl_search`
- **`web_fetch` 失败需要回退**（Readability 提取失败，站点反爬）→ Firecrawl 自动接手，无需 agent 干预

### 机器人规避——为什么是核心价值？

很多站点（特别是新闻、社交媒体、电商）会阻止普通 HTTP 抓取。Cloudflare、DataDome、PerimeterX 等反爬服务检测 User-Agent、请求频率、JavaScript 指纹，发现是机器人就返回 403 或 CAPTCHA。

Firecrawl 用无头浏览器（Playwright/Puppeteer）+ 反检测技术（随机化 User-Agent、模拟人类行为、住宅代理 IP）绕过这些限制。代价是更慢（需要启动浏览器、等待页面渲染）、更贵（Firecrawl 按页面计费，比普通 API 贵 5-10 倍）。

所以 OpenClaw 的策略是**分层回退**：先试 `web_fetch`（HTTP GET + Readability，快、便宜），失败了再回退到 Firecrawl（慢、贵但能拿到内容）。这跟数据库连接池的"先试主库，失败切从库"是一个思路——不是所有查询都需要最贵的路径。

---

OpenClaw 可以三种方式使用 **Firecrawl**：

- 作为 `web_search` 提供者
- 作为显式插件工具：`firecrawl_search` 和 `firecrawl_scrape`
- 作为 `web_fetch` 的备选提取器

它是一个托管的提取/搜索服务，支持机器人规避和缓存，有助于处理 JS 密集网站或阻止普通 HTTP 获取的页面。

## 获取 API 密钥

1. 创建 Firecrawl 账户并生成 API 密钥
2. 将密钥存储在配置中或在 Gateway 环境中设置 `FIRECRAWL_API_KEY`

## 配置 Firecrawl 搜索

```json5
{
  tools: {
    web: {
      search: {
        provider: "firecrawl",
      },
    },
  },
  plugins: {
    entries: {
      firecrawl: {
        enabled: true,
        config: {
          webSearch: {
            apiKey: "FIRECRAWL_API_KEY_HERE",
            baseUrl: "https://api.firecrawl.dev",
          },
        },
      },
    },
  },
}
```

- 在引导流程或 `openclaw configure --section web` 中选择 Firecrawl 会自动启用捆绑的 Firecrawl 插件
- `web_search` 使用 Firecrawl 时支持 `query` 和 `count`
- 需要 Firecrawl 特定控制如 `sources`、`categories` 或结果抓取时，使用 `firecrawl_search`
- `baseUrl` 默认指向托管 Firecrawl `https://api.firecrawl.dev`。自托管覆盖仅允许用于私有/内部端点
- `FIRECRAWL_BASE_URL` 是搜索和抓取基础 URL 的共享环境回退

## 配置 Firecrawl 抓取 + web_fetch 回退

```json5
{
  plugins: {
    entries: {
      firecrawl: {
        enabled: true,
        config: {
          webFetch: {
            apiKey: "FIRECRAWL_API_KEY_HERE",
            baseUrl: "https://api.firecrawl.dev",
            onlyMainContent: true,
            maxAgeMs: 172800000,
            timeoutSeconds: 60,
          },
        },
      },
    },
  },
}
```

- Firecrawl 回退尝试仅在 API 密钥可用时运行
- `maxAgeMs` 控制缓存结果的最大年龄（毫秒）。默认为 2 天
- 旧版 `tools.web.fetch.firecrawl.*` 配置可通过 `openclaw doctor --fix` 自动迁移
- `firecrawl_scrape` 在将目标 URL 转发到 Firecrawl 前会拒绝明显的私有、回环、元数据和非 HTTP(S) URL

`firecrawl_scrape` 复用相同的 `plugins.entries.firecrawl.config.webFetch.*` 设置和环境变量。

### 自托管 Firecrawl

自行运行 Firecrawl 时设置 `plugins.entries.firecrawl.config.webSearch.baseUrl`、`plugins.entries.firecrawl.config.webFetch.baseUrl` 或 `FIRECRAWL_BASE_URL`。OpenClaw 仅对回环、私有网络、`.local`、`.internal` 或 `.localhost` 目标接受 `http://`。公共自定义主机被拒绝，以防止 Firecrawl API 密钥意外发送到任意端点。

## Firecrawl 插件工具

### `firecrawl_search`

需要 Firecrawl 特定搜索控制而非通用 `web_search` 时使用。

核心参数：`query`、`count`、`sources`、`categories`、`scrapeResults`、`timeoutSeconds`

### `firecrawl_scrape`

用于 JS 密集或受机器人保护的页面，普通 `web_fetch` 效果不佳时使用。

核心参数：`url`、`extractMode`、`maxChars`、`onlyMainContent`、`maxAgeMs`、`proxy`、`storeInCache`、`timeoutSeconds`

## 隐身/机器人规避

Firecrawl 暴露**代理模式**参数用于机器人规避（`basic`、`stealth` 或 `auto`）。OpenClaw 对 Firecrawl 请求始终使用 `proxy: "auto"` 加 `storeInCache: true`。如省略代理，Firecrawl 默认为 `auto`。`auto` 在基础尝试失败时使用隐身代理重试，可能比仅基础抓取消耗更多额度。

## `web_fetch` 如何使用 Firecrawl

`web_fetch` 提取顺序：

1. Readability（本地）
2. Firecrawl（如被选中或自动检测为活跃的 web-fetch 回退）
3. 基础 HTML 清理（最后回退）

选择开关是 `tools.web.fetch.provider`。如省略，OpenClaw 从可用凭据中自动检测第一个就绪的 web-fetch 提供者。目前捆绑的提供者是 Firecrawl。

## 相关

- [网页搜索概览](/tools/web)——所有提供者和自动检测
- [Web Fetch](/tools/web-fetch)——带 Firecrawl 回退的 web_fetch 工具
- [Tavily](/tools/tavily)——搜索 + 提取工具
