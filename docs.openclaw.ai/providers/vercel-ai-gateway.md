# Vercel AI Gateway

## 架构精读

> 跳过不影响阅读翻译正文。

### 前端框架的 AI 层——Vercel 生态集成

Vercel AI Gateway 为 Next.js/Vercel 部署提供 LLM API 代理。这跟 Cloudflare AI Gateway 类似但面向不同用户群——Cloudflare 面向基础设施团队，Vercel 面向前端团队。对 OpenClaw agent 来说，如果 agent 部署在 Vercel 上，AI Gateway 提供了**零配置的 LLM 代理**——不需要自己处理 API key 管理和缓存。

---

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
