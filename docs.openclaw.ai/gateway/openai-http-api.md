# OpenAI Chat Completions

> **类比:K8s 的 kubectl proxy。** kubectl proxy 把 Kubernetes API server 暴露为标准 HTTP,让现有工具可以直接访问。OpenAI HTTP API 把 OpenClaw Gateway 包装成标准 OpenAI Chat Completions 接口,让 OpenAI SDK、Open WebUI、LobeChat 等现有工具无缝接入。底层走的是同一套 agent run codepath。
>
> **类比:GraphQL 网关的 REST 兼容层。** 就像 GraphQL 网关提供 REST 兼容 endpoint 让旧客户端继续工作,OpenAI HTTP API 让 OpenClaw 的 agent-first 架构对 OpenAI 协议兼容。`model` 字段不是 provider model ID,而是 agent target——这是最关键的架构差异。
>
> **架构要点:** 默认 disabled(需要显式启用);完整 operator-access surface(不是 per-user scope);agent-first model routing(`model` 字段映射到 agent);stateless per request(通过 `user` 字段派生稳定 session key);与 `/v1/responses` 共享 auth 和 security 模型。

## 端点与配置

启用后在 Gateway 的 multiplexed port (WS + HTTP) 上提供:

| Method | Endpoint |
|--------|----------|
| POST | `/v1/chat/completions` |
| GET | `/v1/models` |
| GET | `/v1/models/{id}` |
| POST | `/v1/embeddings` |
| POST | `/v1/responses` |

```json5
{
  gateway: {
    http: {
      endpoints: {
        chatCompletions: { enabled: true }
      }
    }
  }
}
```

所有请求通过标准 Gateway agent run codepath 执行,与 `openclaw agent` 走同一路径,继承路由、权限和配置。

## 安全边界

**这是一个完整 operator-access surface**,不是窄的每用户作用域。有效凭证等同于 owner/operator secret。

**Shared-secret auth** (`token`/`password`):
- 证明持有 operator secret
- 忽略更窄的 `x-openclaw-scopes` header
- 恢复完整 operator scopes: `operator.admin`、`operator.approvals`、`operator.pairing`、`operator.read`、`operator.talk.secrets`、`operator.write`
- Chat turns 被视为 owner-sender turns

**Identity-bearing modes** (trusted-proxy/`none`):
- 认证外部可信身份
- 尊重 `x-openclaw-scopes`
- 仅在显式缩小 scopes 且省略 `operator.admin` 时失去 owner 语义
- `x-openclaw-model` 需要 `operator.admin`

**关键**: 只在 loopback、tailnet、private ingress 使用,绝不暴露到公网。对于信任分离,运行独立 Gateway。

## Agent-first model routing

OpenAI `model` 字段被解释为 **agent target**,不是 raw provider model ID:

| Model Value | Routes To |
|-------------|-----------|
| `openclaw` | 配置的默认 agent |
| `openclaw/default` | 配置的默认 agent(稳定别名) |
| `openclaw/<agentId>` | 特定 agent |

兼容别名: `openclaw:<agentId>` 和 `agent:<agentId>`。

### 可选 headers

- **`x-openclaw-model`**: 覆盖 backend provider/model。Shared-secret 可自由使用,identity-bearing 需要 `operator.admin`
- **`x-openclaw-agent-id`**: agent 路由兼容覆盖
- **`x-openclaw-session-key`**: 显式 session 路由。不能用保留命名空间(`subagent:`、`cron:`、`acp:`),否则返回 `400`
- **`x-openclaw-message-channel`**: 合成 ingress channel context

## Session behavior

**默认 stateless per request**,每次调用生成新 session key。

如果请求包含 OpenAI `user` 字符串,Gateway 从中派生稳定 session key,允许重复调用共享 agent session。最佳实践: 每个对话线程复用同一 `user` 值,避免用账户级 ID(除非你想多个对话共享一个 session)。

## Streaming (SSE)

`stream: true` 启用 Server-Sent Events:
- `Content-Type: text/event-stream`
- 每行: `data: <json>`
- 终止: `data: [DONE]`

## Chat tool contract

支持 OpenAI function-tool 子集:

- `tools`: `{ type: "function", function: { ... } }` 数组
- `tool_choice`: `"auto"`、`"none"`、`"required"`、或 `{ type: "function", function: { name: "..." } }`
- `max_completion_tokens`: per-call cap(优先于 `max_tokens`)
- `temperature`、`top_p`、`frequency_penalty`、`presence_penalty`、`seed`、`stop`: best-effort 转发

验证: `frequency_penalty` 和 `presence_penalty` 在 -2.0 到 2.0;`seed` 必须是整数;`stop` 最多 4 个非空字符串。超出范围返回 `400`。

Wire mapping: `max_completion_tokens` 发给 OpenAI-family;`max_tokens` 发给 Mistral/Chutes。`stop` 映射到 Chat Completions 的 `stop` 和 Anthropic 的 `stop_sequences`。Responses API 没有 stop 参数。

`tool_choice: "required"` 或 function-pinned 时,缩小暴露的 function-tool 集,要求 runtime 在响应前调用客户端 tool,不匹配则报错。

## `/v1/models` 和 `/v1/embeddings`

`/v1/models` 返回 OpenClaw agent-target 列表(`openclaw`、`openclaw/default`、`openclaw/<agentId>`),不是 raw provider catalog。Sub-agent 是内部执行拓扑,不作为伪模型出现。

`/v1/embeddings` 使用相同的 agent-target model IDs。用 `x-openclaw-model` 指定特定 embedding model(需要 shared-secret 或 `operator.admin`),否则走 agent 正常 embedding 配置。

## Open WebUI 快速设置

| Setting | Value |
|---------|-------|
| Base URL | `http://127.0.0.1:18789/v1` |
| Docker on macOS | `http://host.docker.internal:18789/v1` |
| API Key | Gateway bearer token |
| Model | `openclaw/default` |

## 何时使用

- 集成工具或可信后端,能安全持有 operator 凭证
- 你的集成是同一 Gateway 的另一个 operator/client surface
- **不适合**: 原生移动客户端直连远程 Gateway(用 WebChat 或 Gateway Protocol + device-token flow)
- **不适合**: 有自己用户/房间的外部消息网络(构建 channel plugin)
