# Cloudflare AI Gateway

Cloudflare AI Gateway

Cloudflare AI Gateway 为 LLM API 提供托管代理,带缓存、速率限制和分析。

## Getting started / 入门

```bash
export CLOUDFLARE_API_KEY="..."
openclaw onboard
# Choose "Cloudflare AI Gateway"
```

## Configuration / 配置

```json5
{
  agents: {
    defaults: {
      model: {
        primary: "cloudflare-ai-gateway/model-name"
      }
    }
  }
}
```

## Model routing / 模型路由

OpenClaw routes `cloudflare-ai-gateway/*` models through the Cloudflare AI Gateway API.

OpenClaw 通过 Cloudflare AI Gateway API 路由 `cloudflare-ai-gateway/*` 模型。

## Related / 相关

- [Provider directory](/providers) — 所有提供者列表
- [Models](/providers/models) — 模型配置
