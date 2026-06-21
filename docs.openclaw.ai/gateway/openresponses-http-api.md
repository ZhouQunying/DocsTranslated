# OpenResponses API

> **类比:REST API 的多部分表单升级版。** Chat Completions 是简单的 JSON 请求/响应,OpenResponses 是 item-based 输入——可以发 message、image、file、function_call_output 等多种 item,就像从简单 JSON 升级到多部分表单。核心区别: OpenResponses 支持多模态输入(图片、文件、PDF),Chat Completions 只支持文本 messages。
>
> **架构要点:** 默认 disabled;与 OpenAI HTTP API 共享 auth/security/routing;stateless per request(`user` 字段和 `previous_response_id` 派生稳定 session);文件内容注入 system prompt 而非 user message,用 untrusted boundary markers 包裹;PDF 先解析文本,文本少则栅格化为图片(clawpdf PDFium WASM);URL fetch 有多层安全守卫(DNS 解析、私有 IP 阻止、重定向上限、hostname allowlist)。

## 端点与配置

`POST /v1/responses`,与 OpenAI HTTP API 共享 Gateway multiplexed port。

```json5
{
  gateway: {
    http: {
      endpoints: {
        responses: { enabled: true }
      }
    }
  }
}
```

请求通过标准 Gateway agent run codepath 执行,路由、权限、配置与 Gateway 一致。

## Auth、Security、Routing

与 OpenAI HTTP API 完全相同:

- Shared-secret auth 忽略 `x-openclaw-scopes`,恢复完整 operator scopes
- Identity-bearing modes 尊重 `x-openclaw-scopes`
- 完整 operator-access surface,只在 loopback/tailnet/private ingress 使用

Routing headers: `x-openclaw-agent-id`、`x-openclaw-model`、`x-openclaw-session-key`、`x-openclaw-message-channel`、`x-openclaw-scopes`。Model 接受 `openclaw`、`openclaw/default`、`openclaw/<agentId>`。

## Session behavior

默认 stateless per request。两种方式维持连续性:

- `user` 字符串: Gateway 派生稳定 session key
- `previous_response_id`: 复用 earlier response session(同 agent/user/requested-session 作用域内)

## Request shape

| Field | Notes |
|---|---|
| `input` | 字符串或 item 数组 |
| `instructions` | 合并到 system prompt |
| `tools` | 客户端 function tool 定义 |
| `tool_choice` | `"auto"`、`"none"`、`"required"`、`{ type: "function", name: "..." }` |
| `stream` | 启用 SSE |
| `max_output_tokens` | 输出限制(provider dependent) |
| `temperature`、`top_p` | Best-effort;Codex Responses backend 忽略 |
| `user` | 稳定 session 路由 |

Accepted but ignored: `max_tool_calls`、`reasoning`、`metadata`、`store`、`truncation`。

## Input items

### `message`

支持 `system`、`developer`、`user`、`assistant` roles。`system` 和 `developer` 追加到 system prompt。最近的 `user` 或 `function_call_output` 成为当前消息,更早的作为历史。

### `function_call_output`

发送 tool 结果给 model:
```json
{
  "type": "function_call_output",
  "call_id": "call_123",
  "output": "{\"temperature\": \"72F\"}"
}
```

### `input_image`

Base64 或 URL source。MIME: JPEG、PNG、GIF、WebP、HEIC、HEIF。最大 10MB。HEIC/HEIF 在有系统转换器时(macOS `sips`、ImageMagick、GraphicsMagick、ffmpeg)归一化为 JPEG。

### `input_file`

Base64 或 URL source。MIME: text/plain、text/markdown、text/html、text/csv、application/json、application/pdf。最大 5MB。

**文件处理行为**是关键架构决策:

- 文件内容解码后注入 **system prompt**(不是 user message),保持 ephemeral
- 解码文本用 untrusted boundary markers 包裹: `<<<EXTERNAL_UNTRUSTED_CONTENT id="...">>>` / `<<<END_EXTERNAL_UNTRUSTED_CONTENT id="...">>>`
- 附带 `Source: External` 元数据行
- 故意省略长 `SECURITY NOTICE:` banner 以节省 prompt budget
- **PDF**: 先解析文本;文本少则栅格化首页为图片(用 bundled `document-extract` plugin,内含 `clawpdf` 和 PDFium WASM runtime)

## URL fetch 守卫

默认 `files.allowUrl: true`、`images.allowUrl: true`、`maxUrlParts: 8`(每个请求 URL-based file + image 总数)。

多层安全:
- DNS 解析 + 私有 IP 阻止
- 重定向上限(默认 3 跳)
- 超时(默认 10s)
- 可选 hostname allowlist: 精确匹配(`cdn.example.com`)或通配符子域(`*.assets.example.com`,不匹配 apex)
- `allowUrl: false` 完全禁用 URL fetch

URL allowlist 在 fetch 前和重定向跳上都被执行。Allowlisting hostname **不绕过**私有/内部 IP 阻止。暴露到互联网的 Gateway 需要在 app-level guards 之外加网络 egress 控制。

## Streaming (SSE)

`stream: true` 启用 SSE,`Content-Type: text/event-stream`,每行 `event: <type>` + `data: <json>`,终止于 `data: [DONE]`。

事件类型: `response.created` → `response.in_progress` → `response.output_item.added` → `response.content_part.added` → `response.output_text.delta` → `response.output_text.done` → `response.content_part.done` → `response.output_item.done` → `response.completed`(或 `response.failed`)。

## 配置参考

```json5
{
  gateway: {
    http: {
      endpoints: {
        responses: {
          enabled: true,
          maxBodyBytes: 20000000,     // 20MB
          maxUrlParts: 8,
          files: {
            allowUrl: true,
            urlAllowlist: ["cdn.example.com", "*.assets.example.com"],
            maxBytes: 5242880,        // 5MB
            maxChars: 200000,         // 200k
            maxRedirects: 3,
            timeoutMs: 10000,
            pdf: { maxPages: 4, maxPixels: 4000000, minTextChars: 200 }
          },
          images: {
            allowUrl: true,
            urlAllowlist: ["images.example.com"],
            maxBytes: 10485760,       // 10MB
            maxRedirects: 3,
            timeoutMs: 10000
          }
        }
      }
    }
  }
}
```

## Usage tracking

`usage` 字段在 provider 报告 token 计数时填充。OpenClaw 归一化 OpenAI-style aliases: `input_tokens`/`output_tokens` ↔ `prompt_tokens`/`completion_tokens`。
