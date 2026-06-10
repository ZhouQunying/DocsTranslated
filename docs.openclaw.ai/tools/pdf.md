# PDF tool

## 架构精读

> 跳过不影响阅读翻译正文。

### Agent 想读 PDF——但不是每个模型都能直接吃 PDF 字节

问题很直接：用户甩了个 PDF 过来让 agent 分析。Anthropic 和 Google 的 API 能直接吃 PDF 字节,其他 provider 不行。

`pdf` 工具的策略：先判断当前模型是不是原生支持 PDF 的 provider。是的话,直接把原始字节喂过去——最忠实、最省事。不是的话,走"抽取回退"：先用 PDF 库把文本抠出来,需要的话再把页面转成图片,让视觉模型看图。

跟浏览器渲染一个意思：原生支持的格式直接渲染；不支持的先转成通用格式再处理。

另一个关键点：整条回退链是"认证感知"的。你配了 Anthropic 但没给 key——那它不算数,继续往下找。说白了：有模型不等于能用,能认证才算一个合格候选。

---

> `pdf` analyzes one or more PDF documents and returns text.

`pdf` 分析一份或多份 PDF 文档,返回文本。

> Quick behavior:
>
> - Native provider mode for Anthropic and Google model providers.
> - Extraction fallback mode for other providers (extract text first, then page images when needed).
> - Supports single (`pdf`) or multi (`pdfs`) input, max 10 PDFs per call.

行为速览:

- Anthropic 和 Google 模型 provider 走原生模式。
- 其他 provider 走抽取回退模式(先抽文本,需要时再附页面图)。
- 支持单份(`pdf`)或多份(`pdfs`)输入,每次调用最多 10 份。

## 可用性

> The tool is only registered when OpenClaw can resolve a PDF-capable model config for the agent:

只有当 OpenClaw 能给 agent 解析出一份"能读 PDF"的模型配置时,工具才会注册:

> 1. `agents.defaults.pdfModel`
> 2. fallback to `agents.defaults.imageModel`
> 3. fallback to the agent's resolved session/default model
> 4. if native-PDF providers are auth-backed, prefer them ahead of generic image fallback candidates

1. `agents.defaults.pdfModel`
2. 回退到 `agents.defaults.imageModel`
3. 回退到 agent 解析出的会话 / 默认模型
4. 原生 PDF provider 有认证撑着的话,优先于通用图片回退候选

> If no usable model can be resolved, the `pdf` tool is not exposed.

解析不到可用模型时,`pdf` 工具就不暴露。

> Availability notes:
>
> - The fallback chain is auth-aware. A configured `provider/model` only counts if
>   OpenClaw can actually authenticate that provider for the agent.
> - Native PDF providers are currently **Anthropic** and **Google**.
> - If the resolved session/default provider already has a configured vision/PDF
>   model, the PDF tool reuses that before falling back to other auth-backed
>   providers.

可用性说明:

- 回退链感知认证。配了 `provider/model` 只有在 OpenClaw 真能为这个 agent 认证那个 provider 时才算数。
- 原生 PDF provider 目前是 **Anthropic** 和 **Google**。
- 解析出的会话 / 默认 provider 已经配了视觉 / PDF 模型时,PDF 工具优先复用它,再考虑回退到别的有认证撑着的 provider。

## 输入参数

> `pdf` (string) — One PDF path or URL.

`pdf`(string)—— 一份 PDF 的路径或 URL。

> `pdfs` (string[]) — Multiple PDF paths or URLs, up to 10 total.

`pdfs`(string[])—— 多份 PDF 的路径或 URL,加起来最多 10 份。

> `prompt` (string, default: "Analyze this PDF document.") — Analysis prompt.

`prompt`(string,默认 "Analyze this PDF document.")—— 分析 prompt。

> `pages` (string) — Page filter like `1-5` or `1,3,7-9`.

`pages`(string)—— 页面过滤,如 `1-5` 或 `1,3,7-9`。

> `model` (string) — Optional model override in `provider/model` form.

`model`(string)—— 可选的模型覆盖,形式 `provider/model`。

> `maxBytesMb` (number) — Per-PDF size cap in MB. Defaults to `agents.defaults.pdfMaxBytesMb` or `10`.

`maxBytesMb`(number)—— 每份 PDF 的大小上限(MB)。默认 `agents.defaults.pdfMaxBytesMb` 或 `10`。

> Input notes:
>
> - `pdf` and `pdfs` are merged and deduplicated before loading.
> - If no PDF input is provided, the tool errors.
> - `pages` is parsed as 1-based page numbers, deduped, sorted, and clamped to the configured max pages.
> - `maxBytesMb` defaults to `agents.defaults.pdfMaxBytesMb` or `10`.

输入说明:

- 加载之前,`pdf` 和 `pdfs` 会合并去重。
- 没传 PDF 输入时,工具报错。
- `pages` 按 1 开始的页码解析,去重、排序,然后被夹到配置的最大页数。
- `maxBytesMb` 默认 `agents.defaults.pdfMaxBytesMb` 或 `10`。

## 支持的 PDF 引用

> - local file path (including `~` expansion)
> - `file://` URL
> - `http://` and `https://` URL
> - OpenClaw-managed inbound refs such as `media://inbound/<id>`

- 本地文件路径(含 `~` 展开)
- `file://` URL
- `http://` 和 `https://` URL
- OpenClaw 管理的入站 ref,如 `media://inbound/<id>`

> Reference notes:
>
> - Other URI schemes (for example `ftp://`) are rejected with `unsupported_pdf_reference`.
> - In sandbox mode, remote `http(s)` URLs are rejected.
> - With workspace-only file policy enabled, local file paths outside allowed roots are rejected.
> - Managed inbound refs and replayed paths under OpenClaw's inbound media store are allowed with workspace-only file policy.

引用说明:

- 其他 URI 方案(如 `ftp://`)以 `unsupported_pdf_reference` 拒绝。
- 沙箱模式下,远程 `http(s)` URL 被拒。
- 启用了"仅工作区"文件策略时,允许根之外的本地文件路径被拒。
- 即使开了"仅工作区"文件策略,也允许 OpenClaw 入站媒体存储下面的受管理入站 ref 和回放路径。

## 执行模式

### 原生 provider 模式

> Native mode is used for provider `anthropic` and `google`.
> The tool sends raw PDF bytes directly to provider APIs.

provider 是 `anthropic` 和 `google` 时走原生模式。工具直接把原始 PDF 字节发给 provider API。

> Native mode limits:
>
> - `pages` is not supported. If set, the tool returns an error.
> - Multi-PDF input is supported; each PDF is sent as a native document block /
>   inline PDF part before the prompt.

原生模式限制:

- 不支持 `pages`。设了的话工具报错。
- 支持多份 PDF 输入;每份 PDF 作为原生文档块 / 内联 PDF 部分发,排在 prompt 前面。

### 抽取回退模式

> Fallback mode is used for non-native providers.

非原生 provider 走回退模式。

> Flow:
>
> 1. Extract text from selected pages (up to `agents.defaults.pdfMaxPages`, default `20`).
> 2. If extracted text length is below `200` chars, render selected pages to PNG images and include them.
> 3. Send extracted content plus prompt to the selected model.

流程:

1. 从所选页面抽文本(最多 `agents.defaults.pdfMaxPages`,默认 `20`)。
2. 抽出的文本长度低于 `200` 字符时,把所选页面渲染成 PNG 图片附上。
3. 把抽出的内容加 prompt 发给所选模型。

> Fallback details:
>
> - Page image extraction uses a pixel budget of `4,000,000`.
> - If the target model does not support image input and there is no extractable text, the tool errors.
> - If text extraction succeeds but image extraction would require vision on a
>   text-only model, OpenClaw drops the rendered images and continues with the
>   extracted text.
> - Extraction fallback uses the bundled `document-extract` plugin. The plugin owns
>   `pdfjs-dist`; `@napi-rs/canvas` is used only when image rendering fallback is
>   available.

回退细节:

- 页面图片抽取用 `4,000,000` 像素预算。
- 目标模型不支持图片输入、又抽不出文本时,工具报错。
- 文本抽取成功、但图片抽取需要在纯文本模型上调视觉时,OpenClaw 丢掉渲染的图片,只用抽出的文本继续。
- 抽取回退用内置的 `document-extract` 插件。插件内含 `pdfjs-dist`;`@napi-rs/canvas` 只在能用图片渲染回退时才用。

## 配置

```json5
{
  agents: {
    defaults: {
      pdfModel: {
        primary: "anthropic/claude-opus-4-6",
        fallbacks: ["openai/gpt-5.4-mini"],
      },
      pdfMaxBytesMb: 10,
      pdfMaxPages: 20,
    },
  },
}
```

> See [Configuration Reference](/gateway/configuration-reference) for full field details.

完整字段细节见 [配置参考](/gateway/configuration-reference)。

## 输出细节

> The tool returns text in `content[0].text` and structured metadata in `details`.

工具在 `content[0].text` 里返回文本,在 `details` 里返回结构化元数据。

> Common `details` fields:
>
> - `model`: resolved model ref (`provider/model`)
> - `native`: `true` for native provider mode, `false` for fallback
> - `attempts`: fallback attempts that failed before success

常见 `details` 字段:

- `model`:解析出的模型 ref(`provider/model`)
- `native`:原生 provider 模式 `true`,回退模式 `false`
- `attempts`:成功之前失败的回退尝试

> Path fields:
>
> - single PDF input: `details.pdf`
> - multiple PDF inputs: `details.pdfs[]` with `pdf` entries
> - sandbox path rewrite metadata (when applicable): `rewrittenFrom`

路径字段:

- 单份 PDF 输入:`details.pdf`
- 多份 PDF 输入:`details.pdfs[]`,每条带 `pdf` 字段
- 沙箱路径改写元数据(适用时):`rewrittenFrom`

## 错误行为

> - Missing PDF input: throws `pdf required: provide a path or URL to a PDF document`
> - Too many PDFs: returns structured error in `details.error = "too_many_pdfs"`
> - Unsupported reference scheme: returns `details.error = "unsupported_pdf_reference"`
> - Native mode with `pages`: throws clear `pages is not supported with native PDF providers` error

- 缺 PDF 输入:抛 `pdf required: provide a path or URL to a PDF document`
- PDF 太多:在 `details.error = "too_many_pdfs"` 里返回结构化错误
- 引用方案不支持:返回 `details.error = "unsupported_pdf_reference"`
- 原生模式带 `pages`:抛清晰的 `pages is not supported with native PDF providers` 错误

## 例子

> Single PDF:

单份 PDF:

```json
{
  "pdf": "/tmp/report.pdf",
  "prompt": "Summarize this report in 5 bullets"
}
```

> Multiple PDFs:

多份 PDF:

```json
{
  "pdfs": ["/tmp/q1.pdf", "/tmp/q2.pdf"],
  "prompt": "Compare risks and timeline changes across both documents"
}
```

> Page-filtered fallback model:

按页过滤的回退模型:

```json
{
  "pdf": "https://example.com/report.pdf",
  "pages": "1-3,7",
  "model": "openai/gpt-5.4-mini",
  "prompt": "Extract only customer-impacting incidents"
}
```

## 相关

> - [Tools Overview](/tools) - all available agent tools
> - [Configuration Reference](/gateway/config-agents#agent-defaults) - pdfMaxBytesMb and pdfMaxPages config

- [工具总览](/tools) —— 全部可用 agent 工具
- [配置参考](/gateway/config-agents#agent-defaults) ——`pdfMaxBytesMb` 和 `pdfMaxPages` 配置
