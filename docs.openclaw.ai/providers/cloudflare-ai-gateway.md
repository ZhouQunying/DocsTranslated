# Cloudflare AI Gateway

## 架构精读

> 跳过不影响阅读翻译正文。

### CDN 层的 LLM 代理——边缘缓存和可观测性

Cloudflare AI Gateway 在 CDN 边缘层代理 LLM API 请求。这跟传统 CDN 缓存静态资源是一个思路——把 LLM 响应缓存在离用户最近的边缘节点，减少延迟。额外价值是**统一可观测性**——不管你用的是 OpenAI、Anthropic 还是其他 provider，所有请求都经过 Cloudflare，提供统一的日志、缓存命中率、速率限制。

---

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
