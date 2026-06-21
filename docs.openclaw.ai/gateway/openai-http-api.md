# OpenAI Chat Completions

## 架构精读

> 跳过不影响阅读翻译正文。

### Agent-first 与 OpenAI 兼容——为什么 model 字段不是 provider model ID？

OpenAI HTTP API 的核心架构差异是 `model` 字段映射到 **agent target** 而非 provider model ID：

```
model: "openclaw"              → 配置的默认 agent
model: "openclaw/default"      → 配置的默认 agent（稳定别名）
model: "openclaw/<agentId>"    → 特定 agent
```

这跟 GraphQL 网关提供 REST 兼容端点是一个思路——让现有客户端（OpenAI SDK、Open WebUI、LobeChat）继续工作，但底层走的是 Gateway agent run codepath 而非直接 provider 调用。`model` 字段不是"用哪个模型"，而是"路由到哪个 agent"。

### 安全边界——为什么操作员访问等同于所有者机密？

这是一个**完整的操作员访问面**，不是窄的每用户作用域：

- **共享密钥认证**：证明持有操作员机密，恢复全部操作员权限（管理员、approvals、pairing、read、talk.secrets、write）
- **Identity-bearing modes**：认证外部可信身份，尊重 `x-openclaw-scopes`，仅在显式缩小作用域且省略 `operator.admin` 时失去所有者语义

这跟 K8s 的 `cluster-admin` kubeconfig 是一个思路——持有管理员 kubeconfig 等同于集群完全控制权。只在 loopback、tailnet、private ingress 使用，**绝不暴露到公网**。对于信任分离，运行独立 Gateway。

### 无状态会话派生——为什么用 user 字段而非 cookie？

默认**无状态每次请求**，每次调用生成新会话密钥：

- 请求包含 OpenAI `user` 字符串时，Gateway 从中派生稳定会话密钥
- 重复调用共享同一 agent 会话

这跟 HTTP 的无 cookie（小型跟踪标识）会话是一个思路。服务端从请求特征派生会话 ID，客户端不需要显式管理 cookie（存储在浏览器中的小型跟踪标识）。最佳实践：每个对话线程复用同一 `user` 值，避免用账户级 ID（除非你想多个对话共享一个会话）。

### Wire mapping——为什么同一参数有不同字段名？

同一逻辑参数在不同 provider 协议中有不同字段名：

| 逻辑参数 | OpenAI 协议 | Mistral/Chutes 协议 | Anthropic 协议 |
|---------|------------|-------------------|--------------|
| max tokens | `max_completion_tokens` | `max_tokens` | `max_tokens` |
| stop sequences | `stop` | `stop` | `stop_sequences` |

这跟 ORM 的方言适配器（dialect adapter）是一个思路——不同数据库驱动有不同 API，ORM 层统一映射。Responses API 没有 `stop`（停止）参数，这是 OpenAI 和 Anthropic 协议差异的体现。

### 端点配置——为什么默认 disabled？

启用后在 Gateway 的多路复用端口（WS + HTTP）上提供：

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

默认禁用是因为这是操作员访问面——显式启用确保管理员知道暴露了完整操作权限。所有请求通过标准 Gateway agent run codepath 执行，与 `openclaw agent` 走同一路径，继承路由、权限和配置。

---

The OpenAI HTTP API wraps OpenClaw Gateway as a standard OpenAI Chat Completions endpoint, allowing existing tools like OpenAI SDK, Open WebUI, and LobeChat to connect directly. Under the hood, requests follow the same agent run codepath. It is disabled by default (requiring explicit enablement), the `model` field maps to agent targets rather than provider model IDs, and it shares auth and security with `/v1/responses`.

OpenAI HTTP API 把 OpenClaw Gateway 包装成标准 OpenAI Chat Completions 接口，让 OpenAI SDK、Open WebUI、LobeChat 等现有工具直接接入。底层走的是同一套 agent run codepath。默认 disabled（需要显式启用），`model` 字段映射到 agent target 而非 provider model ID，与 `/v1/responses` 共享 auth 和安全模型。

This is a full operator-access surface — valid credentials are equivalent to owner/operator secrets. Shared-secret auth proves possession of the operator secret and restores full operator scopes; identity-bearing modes authenticate external trusted identities and respect `x-openclaw-scopes`. It should only be used on loopback, tailnet, or private ingress — never exposed to the public internet. For trust separation, run a separate Gateway.

这是一个完整的操作员访问接口——有效凭证等同于 owner/operator secret。共享密钥认证证明持有 operator secret 并恢复全部 operator 作用域；身份承载模式认证外部可信身份并尊重 `x-openclaw-scopes`。只在 loopback、tailnet、private ingress 使用，绝不暴露到公网。对于信任分离，运行独立 Gateway。

The OpenAI `model` field is interpreted as an agent target: `openclaw` and `openclaw/default` both route to the configured default agent, while `openclaw/<agentId>` routes to a specific agent. Compatible aliases include `openclaw:<agentId>` and `agent:<agentId>`. Optional headers allow overriding the backend provider/model, session routing, and synthesized ingress channel context.

OpenAI `model` 字段被解释为 agent target：`openclaw` 和 `openclaw/default` 都路由到配置的默认 agent，`openclaw/<agentId>` 路由到特定 agent。兼容别名包括 `openclaw:<agentId>` 和 `agent:<agentId>`。可选 headers 允许覆盖后端 provider/model、session 路由和合成的 ingress channel context。

By default the API is stateless per request, generating a new session key each time. If the request includes an OpenAI `user` string, the Gateway derives a stable session key from it, allowing repeated calls to share the same agent session. Best practice: reuse the same `user` value per conversation thread, avoid account-level IDs unless you want multiple conversations to share a session.

默认无状态每次请求，每次调用生成新 session key。如果请求包含 OpenAI `user` 字符串，Gateway 从中派生稳定 session key，允许重复调用共享同一 agent session。最佳实践：每个对话线程复用同一 `user` 值，避免用账户级 ID（除非你想多个对话共享一个 session）。
