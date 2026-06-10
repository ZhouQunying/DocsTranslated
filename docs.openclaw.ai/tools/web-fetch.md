# Web fetch

## 架构精读

> 跳过不影响阅读翻译正文。

### Agent 想读网页——但不是所有网页都需要跑浏览器

大部分网页内容(文章、文档、API 说明)是静态 HTML。为这些页面启动一个完整浏览器,又慢又贵。`web_fetch` 的策略：用最轻量的方式——HTTP GET + Readability 抽取正文——解决 80% 的场景。

跟 `curl` + 正文提取器一个道理。不执行 JavaScript,不渲染 CSS,就拿 HTML 原文做主内容抽取。

两层回退设计：Readability 失败了(反爬站点、结构复杂的 SPA)→ Firecrawl 接手,用反反爬模式再试。Firecrawl 也拿不到 → 那就得上完整浏览器了。

SSRF 防护是默认开着的：私有 IP、内网主机名全部屏蔽,重定向也检查。`useTrustedEnvProxy` 是给那些"DNS 由运维代理统一管"的部署用的逃生口。

---

> The `web_fetch` tool does a plain HTTP GET and extracts readable content
> (HTML to markdown or text). It does **not** execute JavaScript.

`web_fetch` 工具做一次普通 HTTP GET,抽取可读内容(HTML 转 markdown 或纯文本)。它**不**执行 JavaScript。

> For JS-heavy sites or login-protected pages, use the Web Browser instead.

JS 重的站点或需要登录的页面,改用 [Web Browser](/tools/browser)。

## 快速开始

> `web_fetch` is enabled by default -- no configuration needed. The agent can call it immediately:

`web_fetch` **默认启用**——不需要配置。Agent 可以直接调:

```javascript
await web_fetch({ url: "https://example.com/article" });
```

## 工具参数

> - `url` (string, required): URL to fetch. `http(s)` only.
> - `extractMode` (string): Output format after main-content extraction.
> - `maxChars` (number): Truncate output to this many characters.

- `url`(string,必填):要抓的 URL。只支持 `http(s)`。
- `extractMode`(string):主内容抽取后的输出格式。
- `maxChars`(number):截断输出到这么多字符。

## 怎么工作的

> 1. Fetch — Sends an HTTP GET with a Chrome-like User-Agent and Accept-Language header. Blocks private/internal hostnames and re-checks redirects.
> 2. Extract — Runs Readability (main-content extraction) on the HTML response.
> 3. Fallback (optional) — If Readability fails and Firecrawl is configured, retries through the Firecrawl API with bot-circumvention mode.
> 4. Cache — Results are cached for 15 minutes (configurable) to reduce repeated fetches of the same URL.

1. **Fetch** —— 带类 Chrome 的 User-Agent 和 `Accept-Language` 头发 HTTP GET。屏蔽私有 / 内网主机名,重定向也检查。
2. **Extract** —— 对 HTML 响应跑 Readability(主内容抽取)。
3. **Fallback(可选）** —— Readability 失败且配了 Firecrawl 时,通过 Firecrawl API 以反反爬模式重试。
4. **Cache** —— 结果缓存 15 分钟(可配),减少对同一 URL 的重复抓取。

## 进度更新

> `web_fetch` emits a public progress line only when the fetch is still pending after five seconds.

`web_fetch` 只在抓取超过 5 秒还没完时才发一行公开进度:

```text
Fetching page content...
```

> Fast cache hits and quick network responses finish before the timer fires, so they do not show a progress line. If the call is canceled, the timer is cleared. When the fetch eventually completes, the agent receives the normal tool result; the progress line is only channel UI state and never contains fetched page content.

快速缓存命中和快网络响应在定时器触发前就完了,所以不显示进度行。调用取消时定时器清除。抓取最终完成时 agent 收到正常工具结果;进度行只是通道 UI 状态,绝不包含抓到的页面内容。

## 配置

```json5
{
  tools: {
    web: {
      fetch: {
        enabled: true,              // 默认: true
        provider: "firecrawl",      // 可选;不填走自动检测
        maxChars: 50000,            // 最大输出字符
        maxCharsCap: 50000,         // maxChars 参数的硬上限
        maxResponseBytes: 2000000,  // 截断前的最大下载体积
        timeoutSeconds: 30,
        cacheTtlMinutes: 15,
        maxRedirects: 3,
        useTrustedEnvProxy: false,  // 让受信 HTTP(S) 代理解析 DNS
        readability: true,          // 用 Readability 抽取
        userAgent: "Mozilla/5.0 ...", // 覆盖 User-Agent
        ssrfPolicy: {
          allowRfc2544BenchmarkRange: true,  // 给用 198.18.0.0/15 的受信假 IP 代理
          allowIpv6UniqueLocalRange: true,   // 给用 fc00::/7 的受信假 IP 代理
        },
      },
    },
  },
}
```

## Firecrawl 回退

> If Readability extraction fails, `web_fetch` can fall back to Firecrawl for bot-circumvention and better extraction:

Readability 抽取失败时,`web_fetch` 可以回退到 [Firecrawl](/tools/firecrawl) 做反反爬和更好的抽取:

```json5
{
  tools: {
    web: {
      fetch: {
        provider: "firecrawl", // 可选;不填从可用凭证自动检测
      },
    },
  },
  plugins: {
    entries: {
      firecrawl: {
        enabled: true,
        config: {
          webFetch: {
            apiKey: "fc-...",   // FIRECRAWL_API_KEY 设了就不用填
            baseUrl: "https://api.firecrawl.dev",
            onlyMainContent: true,
            maxAgeMs: 86400000,      // 缓存时长(1 天)
            timeoutSeconds: 60,
          },
        },
      },
    },
  },
}
```

> `plugins.entries.firecrawl.config.webFetch.apiKey` supports SecretRef objects. Legacy `tools.web.fetch.firecrawl.*` config is auto-migrated by `openclaw doctor --fix`.

`plugins.entries.firecrawl.config.webFetch.apiKey` 支持 SecretRef 对象。旧的 `tools.web.fetch.firecrawl.*` 配置由 `openclaw doctor --fix` 自动迁移。

> If Firecrawl is enabled and its SecretRef is unresolved with no `FIRECRAWL_API_KEY` env fallback, gateway startup fails fast.

[展开: 注意] Firecrawl 启用但 SecretRef 未解析、又没有 `FIRECRAWL_API_KEY` 环境变量兜底时,gateway 启动时快速失败。

> Firecrawl `baseUrl` overrides are locked down: hosted traffic uses `https://api.firecrawl.dev`; self-hosted overrides must target private or internal endpoints, and `http://` is accepted only for those private targets.

[展开: 注意] Firecrawl `baseUrl` 覆盖被锁定:托管流量用 `https://api.firecrawl.dev`;自托管覆盖必须指向私有或内网端点,`http://` 只对这些私有目标接受。

> Current runtime behavior:

当前运行时行为:

> - `tools.web.fetch.provider` selects the fetch fallback provider explicitly.
> - If `provider` is omitted, OpenClaw auto-detects the first ready web-fetch provider from available credentials.
> - Non-sandboxed `web_fetch` can use installed plugins that declare `contracts.webFetchProviders` and register a matching provider at runtime. Today the bundled provider is Firecrawl.
> - Sandboxed `web_fetch` calls stay limited to bundled providers.
> - If Readability is disabled, `web_fetch` skips straight to the selected provider fallback. If no provider is available, it fails closed.

- `tools.web.fetch.provider` 显式选择回退 provider。
- 不填 `provider` 时,OpenClaw 从可用凭证自动检测第一个就绪的 web-fetch provider。
- 非沙箱的 `web_fetch` 可以用声明了 `contracts.webFetchProviders` 并在运行时注册了对应 provider 的已安装插件。目前内置的是 Firecrawl。
- 沙箱里的 `web_fetch` 调用只限内置 provider。
- Readability 关掉时,`web_fetch` 直接跳到选中的 provider 回退。没 provider 可用就默认拒绝。

## 受信环境代理

> If your deployment requires `web_fetch` to go through a trusted outbound HTTP(S) proxy, set `tools.web.fetch.useTrustedEnvProxy: true`.

部署要求 `web_fetch` 走受信出站 HTTP(S) 代理时,设 `tools.web.fetch.useTrustedEnvProxy: true`。

> In this mode, OpenClaw still applies hostname-based SSRF checks before sending the request, but it lets the proxy resolve DNS instead of doing local DNS pinning. Enable this only when the proxy is operator-controlled and enforces outbound policy after DNS resolution.

这个模式下,OpenClaw 在发请求前仍做基于主机名的 SSRF 检查,但让代理解析 DNS 而不是本地 DNS 钉扎。只有代理是运维控制的、且在 DNS 解析后仍强制出站策略时才启用。

> If no HTTP(S) proxy env var is configured, or the target host is excluded by `NO_PROXY`, `web_fetch` falls back to the normal strict path with local DNS pinning.

[展开: 注意] 没配 HTTP(S) 代理环境变量、或目标主机被 `NO_PROXY` 排除时,`web_fetch` 回退到带本地 DNS 钉扎的正常严格路径。

## 限制与安全

> - `maxChars` is clamped to `tools.web.fetch.maxCharsCap`
> - Response body is capped at `maxResponseBytes` before parsing
> - Private/internal hostnames are blocked
> - SSRF policy options are narrow opt-ins for trusted fake-IP proxy stacks
> - Redirects are checked and limited by `maxRedirects`
> - `useTrustedEnvProxy` is an explicit opt-in
> - `web_fetch` is best-effort -- some sites need the Web Browser

- `maxChars` 被夹到 `tools.web.fetch.maxCharsCap`。
- 响应体在解析前被限到 `maxResponseBytes`;超了截断加警告。
- 私有 / 内网主机名被屏蔽。
- `ssrfPolicy.allowRfc2544BenchmarkRange` 和 `ssrfPolicy.allowIpv6UniqueLocalRange` 是给受信假 IP 代理栈的窄范围 opt-in;除非你的代理管着这些合成范围并强制自己的目的地策略,否则别设。
- 重定向被检查,受 `maxRedirects` 限制。
- `useTrustedEnvProxy` 是显式 opt-in,只给运维控制的代理启用。
- `web_fetch` 是尽力而为——有些站点需要 [Web Browser](/tools/browser)。

## 工具 profiles

> If you use tool profiles or allowlists, add `web_fetch` or `group:web`:

用工具 profiles 或白名单时,加 `web_fetch` 或 `group:web`:

```json5
{
  tools: {
    allow: ["web_fetch"],
    // 或: allow: ["group:web"]  (含 web_fetch、web_search、x_search)
  },
}
```

## 相关

> - Web Search — search the web with multiple providers
> - Web Browser — full browser automation for JS-heavy sites
> - Firecrawl — Firecrawl search and scrape tools

- [Web Search](/tools/web) —— 多 provider 搜索网页。
- [Web Browser](/tools/browser) —— JS 重站点的完整浏览器自动化。
- [Firecrawl](/tools/firecrawl) —— Firecrawl 搜索和抓取工具。
