# Diffs

> `diffs` is an optional plugin tool with short built-in system guidance and a companion skill that turns change content into a read-only diff artifact for agents.

`diffs` 是一个可选的插件工具,带一段简短的内置系统指引,以及一个配套技能,用来把变更内容变成只读的 diff 产物给 agent 用。

> It accepts either:
>
> - `before` and `after` text
> - a unified `patch`

它接受两种输入:

- `before` 和 `after` 文本
- 一份统一 `patch`

> It can return:
>
> - a gateway viewer URL for canvas presentation
> - a rendered file path (PNG or PDF) for message delivery
> - both outputs in one call

它能返回:

- 给 canvas 展示用的 gateway 查看器 URL
- 给 message 投递用的渲染文件路径(PNG 或 PDF)
- 一次调用同时拿两个输出

> When enabled, the plugin prepends concise usage guidance into system-prompt space and also exposes a detailed skill for cases where the agent needs fuller instructions.

启用之后,插件在系统 prompt 空间里加一段紧凑的使用指引;同时暴露一个详细的技能,给 agent 需要更完整说明的场景用。

## 快速开始

> <Step title="Install the plugin">

[步骤 1: 装插件]

```bash
openclaw plugins install diffs
```

> <Step title="Enable the plugin">

[步骤 2: 启用插件]

```json5
{
  plugins: {
    entries: {
      diffs: {
        enabled: true,
      },
    },
  },
}
```

> <Step title="Pick a mode">

[步骤 3: 选模式]

> <Tab title="view">
>         Canvas-first flows: agents call `diffs` with `mode: "view"` and open `details.viewerUrl` with `canvas present`.

[标签: view] canvas 优先的流程:agent 用 `mode: "view"` 调 `diffs`,然后用 `canvas present` 打开 `details.viewerUrl`。

> <Tab title="file">
>         Chat file delivery: agents call `diffs` with `mode: "file"` and send `details.filePath` with `message` using `path` or `filePath`.

[标签: file] 聊天文件投递:agent 用 `mode: "file"` 调 `diffs`,然后用 `message` 的 `path` 或 `filePath` 发送 `details.filePath`。

> <Tab title="both">
>         Combined: agents call `diffs` with `mode: "both"` to get both artifacts in one call.

[标签: both] 二合一:agent 用 `mode: "both"` 调 `diffs`,一次拿两个产物。

## 关掉内置系统指引

> If you want to keep the `diffs` tool enabled but disable its built-in system-prompt guidance, set `plugins.entries.diffs.hooks.allowPromptInjection` to `false`:

想留着 `diffs` 工具但不要它内置的系统 prompt 指引,把 `plugins.entries.diffs.hooks.allowPromptInjection` 设成 `false`:

```json5
{
  plugins: {
    entries: {
      diffs: {
        enabled: true,
        hooks: {
          allowPromptInjection: false,
        },
      },
    },
  },
}
```

> This blocks the diffs plugin's `before_prompt_build` hook while keeping the plugin, tool, and companion skill available.

这屏蔽 diffs 插件的 `before_prompt_build` 钩子,但插件、工具、配套技能仍然可用。

> If you want to disable both the guidance and the tool, disable the plugin instead.

要把指引和工具都关掉,直接关插件。

## 典型 agent 工作流

> <Step title="Call diffs">
>     Agent calls the `diffs` tool with input.

[步骤 1: 调 diffs] agent 带输入调 `diffs` 工具。

> <Step title="Read details">
>     Agent reads `details` fields from the response.

[步骤 2: 读 details] agent 从响应里读 `details` 字段。

> <Step title="Present">
>     Agent either opens `details.viewerUrl` with `canvas present`, sends `details.filePath` with `message` using `path` or `filePath`, or does both.

[步骤 3: 展示] agent 要么用 `canvas present` 打开 `details.viewerUrl`,要么用 `message` 的 `path` 或 `filePath` 发 `details.filePath`,或者两者都做。

## 输入例子

> <Tab title="Before and after">

[标签: before 和 after]

```json
{
  "before": "# Hello\n\nOne",
  "after": "# Hello\n\nTwo",
  "path": "docs/example.md",
  "mode": "view"
}
```

> <Tab title="Patch">

[标签: Patch]

```json
{
  "patch": "diff --git a/src/example.ts b/src/example.ts\n--- a/src/example.ts\n+++ b/src/example.ts\n@@ -1 +1 @@\n-const x = 1;\n+const x = 2;\n",
  "mode": "both"
}
```

## 工具输入参考

> All fields are optional unless noted.

除非另注,所有字段都可选。

> `before` (string) — Original text. Required with `after` when `patch` is omitted.

`before`(string)—— 原始文本。省略 `patch` 时,跟 `after` 一起必填。

> `after` (string) — Updated text. Required with `before` when `patch` is omitted.

`after`(string)—— 更新后的文本。省略 `patch` 时,跟 `before` 一起必填。

> `patch` (string) — Unified diff text. Mutually exclusive with `before` and `after`.

`patch`(string)—— 统一 diff 文本。跟 `before` 和 `after` 互斥。

> `path` (string) — Display filename for before and after mode.

`path`(string)——`before`/`after` 模式下显示的文件名。

> `lang` (string) — Language override hint for before and after mode. Unknown values fall back to plain text.

`lang`(string)——`before`/`after` 模式下的语言覆盖提示。未知值回退到纯文本。

> `title` (string) — Viewer title override.

`title`(string)—— 查看器标题覆盖。

> `mode` (`"view" | "file" | "both"`) — Output mode. Defaults to plugin default `defaults.mode`. Deprecated alias: `"image"` behaves like `"file"` and is still accepted for backward compatibility.

`mode`(`"view" | "file" | "both"`)—— 输出模式。默认插件默认的 `defaults.mode`。废弃别名:`"image"` 跟 `"file"` 等价,仍然接受以兼容旧调用。

> `theme` (`"light" | "dark"`) — Viewer theme. Defaults to plugin default `defaults.theme`.

`theme`(`"light" | "dark"`)—— 查看器主题。默认插件默认的 `defaults.theme`。

> `layout` (`"unified" | "split"`) — Diff layout. Defaults to plugin default `defaults.layout`.

`layout`(`"unified" | "split"`)—— diff 布局。默认插件默认的 `defaults.layout`。

> `expandUnchanged` (boolean) — Expand unchanged sections when full context is available. Per-call option only (not a plugin default key).

`expandUnchanged`(boolean)—— 完整上下文可用时展开未改的段。仅单次调用选项(不是插件默认 key)。

> `fileFormat` (`"png" | "pdf"`) — Rendered file format. Defaults to plugin default `defaults.fileFormat`.

`fileFormat`(`"png" | "pdf"`)—— 渲染文件格式。默认插件默认的 `defaults.fileFormat`。

> `fileQuality` (`"standard" | "hq" | "print"`) — Quality preset for PNG or PDF rendering.

`fileQuality`(`"standard" | "hq" | "print"`)—— PNG / PDF 渲染的质量预设。

> `fileScale` (number) — Device scale override (`1`-`4`).

`fileScale`(number)—— 设备 scale 覆盖(`1`-`4`)。

> `fileMaxWidth` (number) — Max render width in CSS pixels (`640`-`2400`).

`fileMaxWidth`(number)—— 最大渲染宽度,CSS 像素(`640`-`2400`)。

> `ttlSeconds` (number, default: 1800) — Artifact TTL in seconds for viewer and standalone file outputs. Max 21600.

`ttlSeconds`(number,默认 1800)—— 查看器和独立文件输出的产物 TTL,秒。上限 21600。

> `baseUrl` (string) — Viewer URL origin override. Overrides plugin `viewerBaseUrl`. Must be `http` or `https`, no query/hash.

`baseUrl`(string)—— 查看器 URL origin 覆盖。覆盖插件的 `viewerBaseUrl`。必须 `http` 或 `https`,不带 query/hash。

> <Accordion title="Legacy input aliases">
>     Still accepted for backward compatibility:
>
>     - `format` -> `fileFormat`
>     - `imageFormat` -> `fileFormat`
>     - `imageQuality` -> `fileQuality`
>     - `imageScale` -> `fileScale`
>     - `imageMaxWidth` -> `fileMaxWidth`

[展开: 旧输入别名] 为兼容旧调用仍接受:

- `format` → `fileFormat`
- `imageFormat` → `fileFormat`
- `imageQuality` → `fileQuality`
- `imageScale` → `fileScale`
- `imageMaxWidth` → `fileMaxWidth`

> <Accordion title="Validation and limits">
>     - `before` and `after` each max 512 KiB.
>     - `patch` max 2 MiB.
>     - `path` max 2048 bytes.
>     - `lang` max 128 bytes.
>     - `title` max 1024 bytes.
>     - Patch complexity cap: max 128 files and 120000 total lines.
>     - `patch` and `before` or `after` together are rejected.
>     - Rendered file safety limits (apply to PNG and PDF):
>       - `fileQuality: "standard"`: max 8 MP (8,000,000 rendered pixels).
>       - `fileQuality: "hq"`: max 14 MP (14,000,000 rendered pixels).
>       - `fileQuality: "print"`: max 24 MP (24,000,000 rendered pixels).
>       - PDF also has a max of 50 pages.

[展开: 校验和上限]

- `before` 和 `after` 各自最大 512 KiB。
- `patch` 最大 2 MiB。
- `path` 最大 2048 字节。
- `lang` 最大 128 字节。
- `title` 最大 1024 字节。
- patch 复杂度上限:最多 128 个文件、总共 120000 行。
- `patch` 跟 `before` 或 `after` 一起出现会被拒。
- 渲染文件安全上限(PNG 和 PDF 都适用):
  - `fileQuality: "standard"`:最多 8 MP(8,000,000 渲染像素)。
  - `fileQuality: "hq"`:最多 14 MP(14,000,000 渲染像素)。
  - `fileQuality: "print"`:最多 24 MP(24,000,000 渲染像素)。
  - PDF 还有 50 页上限。

## 输出 details 契约

> The tool returns structured metadata under `details`.

工具在 `details` 下返回结构化元数据。

> <Accordion title="Viewer fields">
>     Shared fields for modes that create a viewer:
>
>     - `artifactId`
>     - `viewerUrl`
>     - `viewerPath`
>     - `title`
>     - `expiresAt`
>     - `inputKind`
>     - `fileCount`
>     - `mode`
>     - `context` (`agentId`, `sessionId`, `messageChannel`, `agentAccountId` when available)

[展开: 查看器字段] 创建查看器的模式共享这些字段:

- `artifactId`
- `viewerUrl`
- `viewerPath`
- `title`
- `expiresAt`
- `inputKind`
- `fileCount`
- `mode`
- `context`(`agentId`、`sessionId`、`messageChannel`、`agentAccountId`,可用时)

> <Accordion title="File fields">
>     File fields when PNG or PDF is rendered:
>
>     - `artifactId`
>     - `expiresAt`
>     - `filePath`
>     - `path` (same value as `filePath`, for message tool compatibility)
>     - `fileBytes`
>     - `fileFormat`
>     - `fileQuality`
>     - `fileScale`
>     - `fileMaxWidth`

[展开: 文件字段] 渲染 PNG 或 PDF 时的文件字段:

- `artifactId`
- `expiresAt`
- `filePath`
- `path`(跟 `filePath` 同值,给 message 工具兼容用)
- `fileBytes`
- `fileFormat`
- `fileQuality`
- `fileScale`
- `fileMaxWidth`

> <Accordion title="Compatibility aliases">
>     Also returned for existing callers:
>
>     - `format` (same value as `fileFormat`)
>     - `imagePath` (same value as `filePath`)
>     - `imageBytes` (same value as `fileBytes`)
>     - `imageQuality` (same value as `fileQuality`)
>     - `imageScale` (same value as `fileScale`)
>     - `imageMaxWidth` (same value as `fileMaxWidth`)

[展开: 兼容别名] 给已有调用方也返回:

- `format`(同 `fileFormat`)
- `imagePath`(同 `filePath`)
- `imageBytes`(同 `fileBytes`)
- `imageQuality`(同 `fileQuality`)
- `imageScale`(同 `fileScale`)
- `imageMaxWidth`(同 `fileMaxWidth`)

> Mode behavior summary:

模式行为汇总:

> | Mode     | What is returned                                                                                                       |

| 模式      | 返回什么                                                                                                              |
| --------- | --------------------------------------------------------------------------------------------------------------------- |
| `"view"`  | 仅查看器字段。                                                                                                        |
| `"file"`  | 仅文件字段,没有查看器产物。                                                                                          |
| `"both"`  | 查看器字段加文件字段。文件渲染失败时,查看器仍返回,带 `fileError` 和 `imageError` 别名。                              |

## 折叠的未改段

> - The viewer can show rows like `N unmodified lines`.
> - Expand controls on those rows are conditional and not guaranteed for every input kind.
> - Expand controls appear when the rendered diff has expandable context data, which is typical for before and after input.
> - For many unified patch inputs, omitted context bodies are not available in the parsed patch hunks, so the row can appear without expand controls. This is expected behavior.
> - `expandUnchanged` applies only when expandable context exists.

- 查看器可以显示 `N unmodified lines` 这种行。
- 这些行上的展开控件是有条件的,不保证每种输入都有。
- 渲染出的 diff 带可展开的上下文数据时,展开控件才出现 —— 这对 `before`/`after` 输入是常见情况。
- 很多 unified patch 输入里,省略的上下文正文在解析出的 patch hunk 里没有,所以这种行可能没有展开控件 —— 这是预期行为。
- `expandUnchanged` 只在有可展开上下文时生效。

## 插件默认

> Set plugin-wide defaults in `~/.openclaw/openclaw.json`:

在 `~/.openclaw/openclaw.json` 里设插件级默认:

```json5
{
  plugins: {
    entries: {
      diffs: {
        enabled: true,
        config: {
          defaults: {
            fontFamily: "Fira Code",
            fontSize: 15,
            lineSpacing: 1.6,
            layout: "unified",
            showLineNumbers: true,
            diffIndicators: "bars",
            wordWrap: true,
            background: true,
            theme: "dark",
            fileFormat: "png",
            fileQuality: "standard",
            fileScale: 2,
            fileMaxWidth: 960,
            mode: "both",
            ttlSeconds: 21600,
          },
        },
      },
    },
  },
}
```

> Supported defaults:

支持的默认:

- `fontFamily`
- `fontSize`
- `lineSpacing`
- `layout`
- `showLineNumbers`
- `diffIndicators`
- `wordWrap`
- `background`
- `theme`
- `fileFormat`
- `fileQuality`
- `fileScale`
- `fileMaxWidth`
- `mode`
- `ttlSeconds`

> Explicit tool parameters override these defaults.

显式工具参数覆盖这些默认。

### 持久化查看器 URL 配置

> `viewerBaseUrl` (string) — Plugin-owned fallback for returned viewer links when a tool call does not pass `baseUrl`. Must be `http` or `https`, no query/hash.

`viewerBaseUrl`(string)—— 工具调用没传 `baseUrl` 时,插件拥有的查看器链接回退。必须 `http` 或 `https`,不带 query/hash。

```json5
{
  plugins: {
    entries: {
      diffs: {
        enabled: true,
        config: {
          viewerBaseUrl: "https://gateway.example.com/openclaw",
        },
      },
    },
  },
}
```

## 安全配置

> `security.allowRemoteViewer` (boolean, default: false) — `false`: non-loopback requests to viewer routes are denied. `true`: remote viewers are allowed if tokenized path is valid.

`security.allowRemoteViewer`(boolean,默认 false)——`false`:对查看器路由的非环回请求被拒。`true`:tokenize 的路径有效时,允许远程查看器。

```json5
{
  plugins: {
    entries: {
      diffs: {
        enabled: true,
        config: {
          security: {
            allowRemoteViewer: false,
          },
        },
      },
    },
  },
}
```

## 产物生命周期和存储

> - Artifacts are stored under the temp subfolder: `$TMPDIR/openclaw-diffs`.
> - Viewer artifact metadata contains:
>   - random artifact ID (20 hex chars)
>   - random token (48 hex chars)
>   - `createdAt` and `expiresAt`
>   - stored `viewer.html` path
> - Default artifact TTL is 30 minutes when not specified.
> - Maximum accepted viewer TTL is 6 hours.
> - Cleanup runs opportunistically after artifact creation.
> - Expired artifacts are deleted.
> - Fallback cleanup removes stale folders older than 24 hours when metadata is missing.

- 产物存在临时子目录:`$TMPDIR/openclaw-diffs`。
- 查看器产物元数据包含:
  - 随机产物 ID(20 个十六进制字符)
  - 随机 token(48 个十六进制字符)
  - `createdAt` 和 `expiresAt`
  - 存好的 `viewer.html` 路径
- 不指定时,默认产物 TTL 30 分钟。
- 查看器 TTL 最大接受 6 小时。
- 创建产物后机会性地跑清理。
- 过期产物被删。
- 元数据缺失时,回退清理会删超过 24 小时的过期目录。

## 查看器 URL 和网络行为

> Viewer route:

查看器路由:

- `/plugins/diffs/view/{artifactId}/{token}`

> Viewer assets:

查看器资源:

- `/plugins/diffs/assets/viewer.js`
- `/plugins/diffs/assets/viewer-runtime.js`

> The viewer document resolves those assets relative to the viewer URL, so an optional `baseUrl` path prefix is preserved for both asset requests too.

查看器文档相对查看器 URL 解析这些资源,所以可选的 `baseUrl` 路径前缀对两个资源请求也保留。

> URL construction behavior:
>
> - If tool-call `baseUrl` is provided, it is used after strict validation.
> - Else if plugin `viewerBaseUrl` is configured, it is used.
> - Without either override, viewer URL defaults to loopback `127.0.0.1`.
> - If gateway bind mode is `custom` and `gateway.customBindHost` is set, that host is used.

URL 构造行为:

- 工具调用给了 `baseUrl`,严格校验后使用。
- 否则配了插件 `viewerBaseUrl` 就用。
- 都没覆盖时,查看器 URL 默认环回 `127.0.0.1`。
- gateway bind 模式是 `custom` 且设了 `gateway.customBindHost`,就用那个 host。

> `baseUrl` rules:
>
> - Must be `http://` or `https://`.
> - Query and hash are rejected.
> - Origin plus optional base path is allowed.

`baseUrl` 规则:

- 必须 `http://` 或 `https://`。
- query 和 hash 被拒。
- origin 加可选的 base 路径是允许的。

## 安全模型

> <Accordion title="Viewer hardening">
>     - Loopback-only by default.
>     - Tokenized viewer paths with strict ID and token validation.
>     - Viewer response CSP:
>       - `default-src 'none'`
>       - scripts and assets only from self
>       - no outbound `connect-src`
>     - Remote miss throttling when remote access is enabled:
>       - 40 failures per 60 seconds
>       - 60 second lockout (`429 Too Many Requests`)

[展开: 查看器加固]

- 默认只允许环回。
- tokenize 的查看器路径,带严格的 ID 和 token 校验。
- 查看器响应 CSP:
  - `default-src 'none'`
  - 脚本和资源仅来自自身
  - 没有出站 `connect-src`
- 开启远程访问时的远程未命中限流:
  - 每 60 秒 40 次失败
  - 60 秒锁定(`429 Too Many Requests`)

> <Accordion title="File rendering hardening">
>     - Screenshot browser request routing is deny-by-default.
>     - Only local viewer assets from `http://127.0.0.1/plugins/diffs/assets/*` are allowed.
>     - External network requests are blocked.

[展开: 文件渲染加固]

- 截图浏览器请求路由默认拒绝。
- 只允许 `http://127.0.0.1/plugins/diffs/assets/*` 的本地查看器资源。
- 外部网络请求被拦。

## file 模式的浏览器要求

> `mode: "file"` and `mode: "both"` need a Chromium-compatible browser.

`mode: "file"` 和 `mode: "both"` 需要一个 Chromium 兼容浏览器。

> Resolution order:

解析顺序:

> <Step title="Config">
>     `browser.executablePath` in OpenClaw config.

[步骤 1: 配置] OpenClaw 配置里的 `browser.executablePath`。

> <Step title="Environment variables">
>     - `OPENCLAW_BROWSER_EXECUTABLE_PATH`
>     - `BROWSER_EXECUTABLE_PATH`
>     - `PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH`

[步骤 2: 环境变量]

- `OPENCLAW_BROWSER_EXECUTABLE_PATH`
- `BROWSER_EXECUTABLE_PATH`
- `PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH`

> <Step title="Platform fallback">
>     Platform command/path discovery fallback.

[步骤 3: 平台回退] 平台命令 / 路径发现回退。

> Common failure text:
>
> - `Diff PNG/PDF rendering requires a Chromium-compatible browser...`

常见失败文本:

- `Diff PNG/PDF rendering requires a Chromium-compatible browser...`

> Fix by installing Chrome, Chromium, Edge, or Brave, or setting one of the executable path options above.

装 Chrome、Chromium、Edge、Brave 中任一个,或设上面任一个可执行路径选项来修。

## 排障

> <Accordion title="Input validation errors">
>     - `Provide patch or both before and after text.` — include both `before` and `after`, or provide `patch`.
>     - `Provide either patch or before/after input, not both.` — do not mix input modes.
>     - `Invalid baseUrl: ...` — use `http(s)` origin with optional path, no query/hash.
>     - `{field} exceeds maximum size (...)` — reduce payload size.
>     - Large patch rejection — reduce patch file count or total lines.

[展开: 输入校验错误]

- `Provide patch or both before and after text.` —— 同时给 `before` 和 `after`,或者给 `patch`。
- `Provide either patch or before/after input, not both.` —— 别混着用输入模式。
- `Invalid baseUrl: ...` —— 用 `http(s)` origin 加可选路径,不带 query/hash。
- `{field} exceeds maximum size (...)` —— 减小载荷大小。
- 大 patch 被拒 —— 减少 patch 文件数或总行数。

> <Accordion title="Viewer accessibility">
>     - Viewer URL resolves to `127.0.0.1` by default.
>     - For remote access scenarios, either:
>       - set plugin `viewerBaseUrl`, or
>       - pass `baseUrl` per tool call, or
>       - use `gateway.bind=custom` and `gateway.customBindHost`
>     - If `gateway.trustedProxies` includes loopback for a same-host proxy (for example Tailscale Serve), raw loopback viewer requests without forwarded client-IP headers fail closed by design.
>     - For that proxy topology:
>       - prefer `mode: "file"` or `mode: "both"` when you only need an attachment, or
>       - intentionally enable `security.allowRemoteViewer` and set plugin `viewerBaseUrl` or pass a proxy/public `baseUrl` when you need a shareable viewer URL
>     - Enable `security.allowRemoteViewer` only when you intend external viewer access.

[展开: 查看器可访问性]

- 查看器 URL 默认解析到 `127.0.0.1`。
- 远程访问场景下,选一种:
  - 设插件 `viewerBaseUrl`,或
  - 每次工具调用传 `baseUrl`,或
  - 用 `gateway.bind=custom` 加 `gateway.customBindHost`
- `gateway.trustedProxies` 为同主机代理(如 Tailscale Serve)包含环回时,没带转发客户端 IP 头的原始环回查看器请求按设计默认拒绝。
- 这种代理拓扑下:
  - 只需要附件时,优先用 `mode: "file"` 或 `mode: "both"`,或
  - 需要可分享的查看器 URL 时,刻意开 `security.allowRemoteViewer`,并设插件 `viewerBaseUrl` 或传一个代理 / 公网 `baseUrl`
- 只在你确实想让查看器对外可访问时才开 `security.allowRemoteViewer`。

> <Accordion title="Unmodified-lines row has no expand button">
>     This can happen for patch input when the patch does not carry expandable context. This is expected and does not indicate a viewer failure.

[展开: 未改行没有展开按钮] patch 输入不带可展开上下文时会这样,这是预期的,不代表查看器出问题。

> <Accordion title="Artifact not found">
>     - Artifact expired due TTL.
>     - Token or path changed.
>     - Cleanup removed stale data.

[展开: 找不到产物]

- 产物到 TTL 过期了。
- token 或路径变了。
- 清理删了过期数据。

## 运维指引

> - Prefer `mode: "view"` for local interactive reviews in canvas.
> - Prefer `mode: "file"` for outbound chat channels that need an attachment.
> - Keep `allowRemoteViewer` disabled unless your deployment requires remote viewer URLs.
> - Set explicit short `ttlSeconds` for sensitive diffs.
> - Avoid sending secrets in diff input when not required.
> - If your channel compresses images aggressively (for example Telegram or WhatsApp), prefer PDF output (`fileFormat: "pdf"`).

- canvas 上本地交互式评审,优先 `mode: "view"`。
- 需要附件的出站聊天通道,优先 `mode: "file"`。
- 除非部署需要远程查看器 URL,否则保持 `allowRemoteViewer` 关闭。
- 敏感 diff 显式设短 `ttlSeconds`。
- 不必要时,别把密钥放进 diff 输入。
- 通道压缩图片很狠时(如 Telegram 或 WhatsApp),优先 PDF 输出(`fileFormat: "pdf"`)。

> <Note>
> Diff rendering engine powered by [Diffs](https://diffs.com).
> </Note>

[展开: 注意] Diff 渲染引擎由 [Diffs](https://diffs.com) 提供。

## 相关

> - [Browser](/tools/browser)
> - [Plugins](/tools/plugin)
> - [Tools overview](/tools)

- [浏览器](/tools/browser)
- [插件](/tools/plugin)
- [工具总览](/tools)
