# Vercel AI Gateway

Vercel AI Gateway

Vercel AI Gateway 为 LLM API 提供托管代理,带缓存和分析。

## Getting started / 入门

```bash
export VERCEL_API_KEY="..."
openclaw onboard
# Choose "Vercel AI Gateway"
```

## Configuration / 配置

```json5
{
  agents: {
    defaults: {
      model: {
        primary: "vercel-ai-gateway/model-name"
      }
    }
  }
}
```

## Model routing / 模型路由

OpenClaw routes `vercel-ai-gateway/*` models through the Vercel AI Gateway API.

OpenClaw 通过 Vercel AI Gateway API 路由 `vercel-ai-gateway/*` 模型。

## Related / 相关

- [Provider directory](/providers) — 所有提供者列表
- [Models](/providers/models) — 模型配置
