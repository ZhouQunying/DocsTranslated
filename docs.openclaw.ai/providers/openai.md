# OpenAI

OpenAI provides developer APIs for GPT models, and Codex is also available as a ChatGPT-plan coding agent through OpenAI's Codex clients. OpenClaw uses one provider id, `openai`, for both auth shapes.

OpenAI 提供 GPT 模型的开发者 API,Codex 也可作为 ChatGPT 计划编码 agent 通过 OpenAI 的 Codex 客户端使用。OpenClaw 使用一个提供者 id `openai` 处理两种认证形式。

OpenClaw uses `openai/*` as the canonical OpenAI model route. Embedded agent turns on OpenAI models run through the native Codex app-server runtime by default; direct OpenAI API-key auth remains available for non-agent OpenAI surfaces such as images, embeddings, speech, and realtime.

OpenClaw 使用 `openai/*` 作为规范的 OpenAI 模型路由。OpenAI 模型上的嵌入式 agent 轮次默认通过原生 Codex 应用服务器运行时运行;直接 OpenAI API 密钥认证仍可用于非 agent OpenAI 表面如图像、嵌入、语音和实时。

## Auth routes / 认证路由

- **Agent models** - `openai/*` models through the Codex runtime; sign in with Codex auth for ChatGPT/Codex subscription use, or configure a Codex-compatible OpenAI API-key backup when you intentionally want API-key auth
  
  **Agent 模型** - 通过 Codex 运行时使用 `openai/*` 模型;使用 Codex 认证登录以使用 ChatGPT/Codex 订阅,或当你故意想要 API 密钥认证时配置 Codex 兼容的 OpenAI API 密钥备份

- **Non-agent surfaces** - images, embeddings, speech, realtime: use direct OpenAI API-key auth
  
  **非 agent 表面** - 图像、嵌入、语音、实时:使用直接 OpenAI API 密钥认证

## Getting started / 入门

### Codex auth (recommended for agent models) / Codex 认证(推荐用于 agent 模型)

```bash
openclaw onboard
# Choose "OpenAI" and select Codex auth
```

### API key / API 密钥

```bash
export OPENAI_API_KEY="sk-..."
openclaw onboard
# Choose "OpenAI" and select API key auth
```

## Configuration / 配置

```json5
{
  agents: {
    defaults: {
      model: {
        primary: "openai/gpt-5.4"
      }
    }
  }
}
```

## Model routing / 模型路由

OpenClaw routes `openai/*` models through the OpenAI provider. Agent models use the Codex runtime; non-agent surfaces use direct API.

OpenClaw 通过 OpenAI 提供者路由 `openai/*` 模型。Agent 模型使用 Codex 运行时;非 agent 表面使用直接 API。

## Related / 相关

- [Provider directory](/providers) — 所有提供者列表
- [Models](/providers/models) — 模型配置
- [Anthropic](/providers/anthropic) — Anthropic 提供者
