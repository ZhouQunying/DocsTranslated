# OpenResponses API

## 架构精读

> 跳过不影响阅读翻译正文。

### Item-based input——为什么不用简单 JSON？

OpenResponses API 采用 item-based 输入模型，而非 Chat Completions 的简单 JSON 请求/响应：

- `input` 接受字符串或 item 数组（消息、image、file、function_call_output 等）
- 每个 item 有独立的类型和结构
- 支持多模态内容（图片、文件、PDF）直接作为输入项

这跟 REST API 升级到多部分表单（multipart form）是一个思路——Chat Completions 只接受文本 messages，OpenResponses 可以同时携带文本、图片、文件和工具调用结果。每个 item 都是独立的处理单元，网关按类型分别处理。

关键设计是**类型驱动的多态输入**。消息走消息处理路径，image 走图片归一化路径，file 走文件解码路径，function_call_output 走工具结果回传路径。不同路径在网关内部汇聚到同一个代理运行。

### 每次请求无状态——为什么会话是派生的？

OpenResponses 端点默认无状态，每次请求生成新会话密钥。连续性通过两种方式维持：

- `user` 字符串：网关从中派生稳定会话密钥
- `previous_response_id`：复用同一代理/用户/请求会话作用域内更早 response 的会话

这跟 HTTP 的会话 cookie 是一个思路——协议本身无状态，会话通过客户端提供的标识符派生。好处是网关不需要维护服务端会话状态（没有内存泄漏风险），坏处是客户端必须正确传递标识符才能维持对话连续性。

### 文件内容注入系统提示——为什么不放用户消息？

文件内容解码后注入**系统提示**（system prompt，不是用户消息），用不可信边界标记包裹：

```
<<<EXTERNAL_UNTRUSTED_CONTENT id="...">>>
文件内容
<<<END_EXTERNAL_UNTRUSTED_CONTENT id="...">>>
```

这跟 K8s 的 ConfigMap mount 是一个思路——文件内容作为配置（系统提示）挂载，而非用户输入（用户消息）。好处是 ephemeral（不持久化到会话历史），安全（边界标记告知模型这是外部不可信数据）。故意省略长 `SECURITY NOTICE:` 横幅（banner）以节省 prompt 预算。

PDF 走特殊路径：先尝试解析文本，文本过少则用 bundled `document-extract` 插件（内含 `clawpdf` 和 PDFium WASM runtime）将首页栅格化为图片传给模型。

### URL fetch 多层守卫——为什么 hostname 白名单不够？

URL fetch 有五层安全防线：

1. DNS 解析——验证域名合法性
2. 私有 IP 阻止——防止 DNS rebinding 攻击内网
3. 重定向上限（默认 3 跳）——防止重定向链攻击
4. 超时（默认 10s）——防止 SSRF 挂起
5. 可选 hostname 允许列表——精确匹配或通配符子域

关键洞察：hostname 允许列表**不绕过**私有 IP 阻止。即使 `cdn.example.com` 在白名单中，如果 DNS 解析到 10.x.x.x，请求仍然被阻止。这跟浏览器的同源策略 + CORS 是一个思路——两层检查独立执行，一层通过不代表另一层也通过。暴露到互联网的网关需要在应用层守卫之外加网络出口控制。

### SSE streaming——为什么用服务器发送事件（SSE）？

`stream: true` 启用 SSE，事件按固定顺序发射：

```
response.created → response.in_progress → response.output_item.added
→ response.content_part.added → response.output_text.delta
→ response.output_text.done → response.content_part.done
→ response.output_item.done → response.completed
```

这跟 WebSocket 的全双工相比更轻量——SSE 是单向推送（服务器 → 客户端），不需要客户端发送帧。好处是 HTTP 代理天然支持、断线重连简单、不需要帧解析。对于"生成文本并推送给客户端"这个场景，SSE 是最佳选择。

---

OpenClaw's Gateway can serve an OpenResponses-compatible `POST /v1/responses` endpoint. This endpoint is **disabled by default**. Enable it in config first.

OpenClaw 的 Gateway 可以提供 OpenResponses 兼容的 `POST /v1/responses` endpoint。此 endpoint **默认禁用**，需先在配置中启用。

Endpoint:

- `POST /v1/responses`
- Same port as the Gateway (WS + HTTP multiplex): `http://<host>:<port>/v1/responses`

Endpoint：

- `POST /v1/responses`
- 与 Gateway 共享端口（WS + HTTP 复用）：`http://<host>:<port>/v1/responses`

Under the hood, requests are executed as a normal Gateway agent run (same codepath as `openclaw agent`), so routing/permissions/config match your Gateway.

请求在底层通过标准 Gateway agent run 执行（与 `openclaw agent` 走同一代码路径），因此路由、权限和配置与 Gateway 一致。

## Authentication, security, and routing

## 认证、安全与路由

Operational behavior matches OpenAI Chat Completions:

运维行为与 OpenAI Chat Completions 一致：

- Use the matching Gateway HTTP auth path:
  - Shared-secret auth (`gateway.auth.mode="token"` or `"password"`): `Authorization: Bearer <token>`
  - Trusted-proxy auth (`gateway.auth.mode="trusted-proxy"`): identity-aware proxy headers from a configured trusted proxy source; same-host loopback proxies require explicit `gateway.auth.trustedProxy.allowLoopback = true`
  - Trusted-proxy local direct fallback: same-host callers with no `Forwarded`, `X-Forwarded-*`, or `X-Real-IP` headers can use `gateway.auth.password` / `OPENCLAW_GATEWAY_PASSWORD`
  - Private-ingress open auth (`gateway.auth.mode="none"`): no auth header — treat the endpoint as full operator access for the gateway instance
- For shared-secret auth modes (`token` and `password`), ignore narrower bearer-declared `x-openclaw-scopes` values and restore the normal full operator defaults
- For trusted identity-bearing HTTP modes (for example trusted proxy auth or `gateway.auth.mode="none"`), honor `x-openclaw-scopes` when present and otherwise fall back to the normal operator default scope set
- Select agents with `model: "openclaw"`, `model: "openclaw/default"`, `model: "openclaw/<agentId>"`, or `x-openclaw-agent-id`
- Use `x-openclaw-model` when you want to override the selected agent's backend model
- Use `x-openclaw-session-key` for explicit session routing
- Use `x-openclaw-message-channel` when you want a non-default synthetic ingress channel context

- 使用对应的 Gateway HTTP 认证路径：
  - 共享密钥认证（`gateway.auth.mode="token"` 或 `"password"`）：`Authorization: Bearer <token>`
  - 可信代理认证（`gateway.auth.mode="trusted-proxy"`）：来自已配置可信代理源的感知身份代理头；同主机回环代理需要显式设置 `gateway.auth.trustedProxy.allowLoopback = true`
  - 可信代理解析本地直接回退：同主机调用者在没有 `Forwarded`、`X-Forwarded-*` 或 `X-Real-IP` 头时可以使用 `gateway.auth.password` / `OPENCLAW_GATEWAY_PASSWORD`
  - 私有入口开放认证（`gateway.auth.mode="none"`）：无需认证头——将 endpoint 视为 gateway 实例的完整操作员访问
- 对于共享密钥认证模式（`token` 和 `password`），忽略更窄的 bearer 声明的 `x-openclaw-scopes` 值，恢复正常的完整操作员默认值
- 对于可信身份 HTTP 模式（例如可信代理认证或 `gateway.auth.mode="none"`），当 `x-openclaw-scopes` 存在时尊重它，否则回退到正常操作员默认作用域集
- 通过 `model: "openclaw"`、`model: "openclaw/default"`、`model: "openclaw/<agentId>"` 或 `x-openclaw-agent-id` 选择 agent
- 使用 `x-openclaw-model` 覆盖所选 agent 的后端模型
- 使用 `x-openclaw-session-key` 进行显式 session 路由
- 使用 `x-openclaw-message-channel` 指定非默认的合成入口 channel 上下文

Auth matrix:

- `gateway.auth.mode="token"` or `"password"` + `Authorization: Bearer ...`
  - Proves possession of the shared gateway operator secret
  - Ignores narrower `x-openclaw-scopes`
  - Restores the full default operator scope set: `operator.admin`, `operator.approvals`, `operator.pairing`, `operator.read`, `operator.talk.secrets`, `operator.write`
  - Treats chat turns on this endpoint as owner-sender turns

- Trusted identity-bearing HTTP modes (for example trusted proxy auth, or `gateway.auth.mode="none"` on private ingress)
  - Honor `x-openclaw-scopes` when the header is present
  - Fall back to the normal operator default scope set when the header is absent
  - Only lose owner semantics when the caller explicitly narrows scopes and omits `operator.admin`

认证矩阵：

- `gateway.auth.mode="token"` 或 `"password"` + `Authorization: Bearer ...`
  - 证明持有共享 gateway 操作员密钥
  - 忽略更窄的 `x-openclaw-scopes`
  - 恢复完整默认操作员作用域集：`operator.admin`、`operator.approvals`、`operator.pairing`、`operator.read`、`operator.talk.secrets`、`operator.write`
  - 将此 endpoint 上的聊天 turns 视为 owner-sender turns

- 可信身份 HTTP 模式（例如可信代理认证，或私有入口上的 `gateway.auth.mode="none"`）
  - 当 `x-openclaw-scopes` 头存在时尊重它
  - 当头不存在时回退到正常操作员默认作用域集
  - 仅在调用者显式缩小作用域且省略 `operator.admin` 时失去 owner 语义

Enable or disable this endpoint with `gateway.http.endpoints.responses.enabled`.

通过 `gateway.http.endpoints.responses.enabled` 启用或禁用此 endpoint。

## Session behavior

## Session 行为

By default the endpoint is **stateless per request** (a new session key is generated each call). If the request includes an OpenResponses `user` string, the Gateway derives a stable session key from it, so repeated calls can share an agent session.

默认情况下 endpoint **每次请求无状态**（每次调用生成新 session key）。如果请求包含 OpenResponses `user` 字符串，Gateway 从中派生稳定 session key，因此重复调用可以共享 agent session。

## Request shape (supported)

## 请求结构（已支持）

The request follows the OpenResponses API with item-based input. Current support:

请求遵循 OpenResponses API 的 item-based 输入。当前支持：

| Field | Notes |
|---|---|
| `input` | String or array of item objects |
| `instructions` | Merged into the system prompt |
| `tools` | Client tool definitions (function tools) |
| `tool_choice` | `"auto"`, `"none"`, `"required"`, or `{ "type": "function", "name": "..." }` |
| `stream` | Enables SSE streaming |
| `max_output_tokens` | Best-effort output limit (provider dependent) |
| `temperature` | Best-effort; ignored by the Codex Responses backend |
| `top_p` | Best-effort; same Codex Responses caveat |
| `user` | Stable session routing |

| 字段 | 说明 |
|---|---|
| `input` | 字符串或 item 对象数组 |
| `instructions` | 合并到 system prompt |
| `tools` | 客户端 function tool 定义 |
| `tool_choice` | `"auto"`、`"none"`、`"required"`、`{ type: "function", "name": "..." }` |
| `stream` | 启用 SSE 流式传输 |
| `max_output_tokens` | 尽力而为的输出限制（取决于 provider） |
| `temperature` | 尽力而为；Codex Responses 后端忽略 |
| `top_p` | 尽力而为；同 `temperature` 的 Codex Responses 注意事项 |
| `user` | 稳定 session 路由 |

Accepted but **currently ignored**:

已接受但**当前忽略**：

- `max_tool_calls`
- `reasoning`
- `metadata`
- `store`
- `truncation`

Supported:

已支持：

- `previous_response_id`: OpenClaw reuses the earlier response session when the request stays within the same agent/user/requested-session scope.

- `previous_response_id`：当请求保持在同一 agent/user/请求 session 作用域内时，OpenClaw 复用更早 response 的 session。

## Items (input)

## Items（输入）

### `message`

Roles: `system`, `developer`, `user`, `assistant`.

角色：`system`、`developer`、`user`、`assistant`。

- `system` and `developer` are appended to the system prompt.
- The most recent `user` or `function_call_output` item becomes the "current message."
- Earlier user/assistant messages are included as history for context.

- `system` 和 `developer` 追加到 system prompt。
- 最近的 `user` 或 `function_call_output` item 成为"当前消息"。
- 更早的 user/assistant 消息作为上下文历史包含在内。

### `function_call_output` (turn-based tools)

### `function_call_output`（轮次工具）

Send tool results back to the model:

将工具结果发送回模型：

```json
{
  "type": "function_call_output",
  "call_id": "call_123",
  "output": "{\"temperature\": \"72F\"}"
}
```

### `reasoning` and `item_reference`

### `reasoning` 和 `item_reference`

Accepted for schema compatibility but ignored when building the prompt.

为 schema 兼容性而接受，但在构建 prompt 时忽略。

## Tools (client-side function tools)

## 工具（客户端 function tools）

Provide tools with `tools: [{ type: "function", name, description?, parameters? }]`. If the agent decides to call a tool, the response returns a `function_call` output item. You then send a follow-up request with `function_call_output` to continue the turn.

通过 `tools: [{ type: "function", name, description?, parameters? }]` 提供工具。如果 agent 决定调用工具，response 返回一个 `function_call` 输出 item。然后你发送一个带 `function_call_output` 的后续请求来继续轮次。

For `tool_choice: "required"` or function-pinned `tool_choice`, the endpoint narrows the exposed client function-tool set, instructs the runtime to call a client tool before responding, and rejects the turn if it does not include a matching structured client-tool call. This contract applies to the caller-supplied HTTP `tools` list, not every internal OpenClaw agent tool. Non-streaming requests return `502` with an `api_error`; streaming requests emit a `response.failed` event. This matches the `/v1/chat/completions` contract.

对于 `tool_choice: "required"` 或函数固定的 `tool_choice`，endpoint 会缩小暴露的客户端 function-tool 集。运行时被要求在响应前调用客户端工具，如果轮次不包含匹配的调用则拒绝。此约定适用于调用者提供的 HTTP `tools` 列表，而非所有内部 OpenClaw agent 工具。非流式请求返回带 `api_error` 的 `502`；流式请求发出 `response.failed` 事件。这与 `/v1/chat/completions` 的约定一致。

## Images (`input_image`)

## 图片（`input_image`）

Supports base64 or URL sources:

支持 base64 或 URL 来源：

```json
{
  "type": "input_image",
  "source": {
    "type": "url",
    "url": "https://example.com/image.png"
  }
}
```

Allowed MIME types (current): `image/jpeg`, `image/png`, `image/gif`, `image/webp`, `image/heic`, `image/heif`. Max size (current): 10MB.

允许的 MIME 类型（当前）：`image/jpeg`、`image/png`、`image/gif`、`image/webp`、`image/heic`、`image/heif`。最大大小（当前）：10MB。

## Files (`input_file`)

## 文件（`input_file`）

Supports base64 or URL sources:

支持 base64 或 URL 来源：

```json
{
  "type": "input_file",
  "source": {
    "type": "base64",
    "media_type": "text/plain",
    "data": "SGVsbG8gV29ybGQh",
    "filename": "hello.txt"
  }
}
```

Allowed MIME types (current): `text/plain`, `text/markdown`, `text/html`, `text/csv`, `application/json`, `application/pdf`. Max size (current): 5MB.

允许的 MIME 类型（当前）：`text/plain`、`text/markdown`、`text/html`、`text/csv`、`application/json`、`application/pdf`。最大大小（当前）：5MB。

Current behavior:

当前行为：

- File content is decoded and added to the **system prompt**, not the user message, so it stays ephemeral (not persisted in session history).
- Decoded file text is wrapped as **untrusted external content** before it is added, so file bytes are treated as data, not trusted instructions.
- The boundary markers and metadata still stay in place; the long `SECURITY NOTICE:` banner is intentionally omitted to preserve prompt budget.
- PDFs are parsed for text first. If little text is found, the first pages are rasterized into images and passed to the model. PDF parsing is provided by the bundled `document-extract` plugin, which uses `clawpdf` and its packaged PDFium WebAssembly runtime.

- 文件内容解码后添加到 **system prompt**，而非 user message，因此保持临时性（不持久化到 session 历史）。
- 解码的文件文本在添加前被包裹为**不可信外部内容**，因此文件字节被视为数据而非可信指令。
- 边界标记和元数据保留不变；为节省 prompt 预算，故意省略了长 `SECURITY NOTICE:` banner。
- PDF 首先解析文本。如果找到很少文本，前几页被栅格化为图片传给模型。PDF 解析由 bundled `document-extract` 插件提供，使用 `clawpdf` 及其打包的 PDFium WebAssembly runtime。

URL fetch defaults:

URL fetch 默认值：

- `files.allowUrl`: `true`
- `images.allowUrl`: `true`
- `maxUrlParts`: `8` (total URL-based `input_file` + `input_image` parts per request)
- Requests are guarded (DNS resolution, private IP blocking, redirect caps, timeouts).
- Optional hostname allowlists are supported per input type (`files.urlAllowlist`, `images.urlAllowlist`).
  - Exact host: `"cdn.example.com"`
  - Wildcard subdomains: `"*.assets.example.com"` (does not match apex)
  - Empty or omitted allowlists mean no hostname allowlist restriction.
- To disable URL-based fetches entirely, set `files.allowUrl: false` and/or `images.allowUrl: false`.

- `files.allowUrl`：`true`
- `images.allowUrl`：`true`
- `maxUrlParts`：`8`（每个请求中基于 URL 的 `input_file` + `input_image` 总数）
- 请求受安全守卫保护（DNS 解析、私有 IP 阻止、重定向上限、超时）。
- 每种输入类型支持可选 hostname 允许列表（`files.urlAllowlist`、`images.urlAllowlist`）。
  - 精确主机名：`"cdn.example.com"`
  - 通配符子域：`"*.assets.example.com"`（不匹配 apex 域名）
  - 空或省略的允许列表表示没有 hostname 允许列表限制。
- 要完全禁用基于 URL 的获取，设置 `files.allowUrl: false` 和/或 `images.allowUrl: false`。

## File + image limits (config)

## 文件 + 图片限制（配置）

Defaults can be tuned under `gateway.http.endpoints.responses`:

默认值可在 `gateway.http.endpoints.responses` 下调优：

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

HEIC/HEIF `input_image` sources are accepted when a system converter is available and are normalized to JPEG before provider delivery. Supported converters are macOS `sips`, ImageMagick, GraphicsMagick, or ffmpeg.

当系统转换器可用时，HEIC/HEIF `input_image` 来源被接受，并在交付给 provider 前归一化为 JPEG。支持的转换器包括 macOS `sips`、ImageMagick、GraphicsMagick 或 ffmpeg。

Security note:

安全说明：

- URL allowlists are enforced before fetch and on redirect hops.
- Allowlisting a hostname does not bypass private/internal IP blocking.
- For internet-exposed gateways, apply network egress controls in addition to app-level guards.

- URL 允许列表在 fetch 前和重定向跳上都被执行。
- 将 hostname 加入允许列表**不会绕过**私有/内部 IP 阻止。
- 对于暴露到互联网的 Gateway，需要在应用层守卫之外应用网络出口控制。

## Streaming (SSE)

## 流式传输（SSE）

Set `stream: true` to receive Server-Sent Events (SSE):

设置 `stream: true` 以接收 Server-Sent Events（SSE）：

- `Content-Type: text/event-stream`
- Each event line is `event: <type>` and `data: <json>`
- Stream ends with `data: [DONE]`

- `Content-Type: text/event-stream`
- 每个事件行是 `event: <type>` 和 `data: <json>`
- 流以 `data: [DONE]` 结束

Event types currently emitted:

当前发出的事件类型：

- `response.created`
- `response.in_progress`
- `response.output_item.added`
- `response.content_part.added`
- `response.output_text.delta`
- `response.output_text.done`
- `response.content_part.done`
- `response.output_item.done`
- `response.completed`
- `response.failed` (on error)

## Usage

## 用量跟踪

`usage` is populated when the underlying provider reports token counts. OpenClaw normalizes common OpenAI-style aliases before those counters reach downstream status/session surfaces, including `input_tokens` / `output_tokens` and `prompt_tokens` / `completion_tokens`.

当底层 provider 报告 token 计数时填充 `usage`。OpenClaw 在这些计数器到达下游状态/session 界面前，归一化常见的 OpenAI 风格别名，包括 `input_tokens` / `output_tokens` 和 `prompt_tokens` / `completion_tokens`。

## Errors

## 错误

Errors use a JSON object like:

错误使用如下 JSON 对象：

```json
{
  "error": {
    "message": "...",
    "type": "invalid_request_error"
  }
}
```

Common cases:

常见情况：

- `401` missing/invalid auth — 认证缺失或无效
- `400` invalid request body — 无效请求体
- `405` wrong method — 方法不允许

## Examples

## 示例

Non-streaming:

非流式：

```bash
curl -sS http://127.0.0.1:18789/v1/responses \
  -H 'Authorization: Bearer YOUR_TOKEN' \
  -H 'Content-Type: application/json' \
  -H 'x-openclaw-agent-id: main' \
  -d '{
    "model": "openclaw",
    "input": "hi"
  }'
```

Streaming:

流式：

```bash
curl -N http://127.0.0.1:18789/v1/responses \
  -H 'Authorization: Bearer YOUR_TOKEN' \
  -H 'Content-Type: application/json' \
  -H 'x-openclaw-agent-id: main' \
  -d '{
    "model": "openclaw",
    "stream": true,
    "input": "hi"
  }'
```

## Related

## 相关

- OpenAI chat completions — `/gateway/openai-http-api`
- OpenAI provider — `/providers/openai`

- OpenAI 聊天补全 — `/gateway/openai-http-api`
- OpenAI provider — `/providers/openai`
