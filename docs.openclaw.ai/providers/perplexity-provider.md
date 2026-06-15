# Perplexity

Perplexity

Perplexity 提供基于网页搜索的搜索和推理模型。

## Getting started / 入门

```bash
export PERPLEXITY_API_KEY="..."
openclaw onboard
# Choose "Perplexity"
```

## Configuration / 配置

```json5
{
  agents: {
    defaults: {
      model: {
        primary: "perplexity-provider/model-name"
      }
    }
  }
}
```

## Model routing / 模型路由

OpenClaw routes `perplexity-provider/*` models through the Perplexity API.

OpenClaw 通过 Perplexity API 路由 `perplexity-provider/*` 模型。

## Related / 相关

- [Provider directory](/providers) — 所有提供者列表
- [Models](/providers/models) — 模型配置
