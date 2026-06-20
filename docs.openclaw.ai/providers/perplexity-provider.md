# Perplexity

## 架构精读

> 跳过不影响阅读翻译正文。

### 搜索 grounding——把 LLM 推理与实时信息绑定

Perplexity 的独特能力是**搜索 grounding**——LLM 的每个回答都基于实时网页搜索结果。这跟 RAG（Retrieval-Augmented Generation）是一个思路，但搜索和检索由 Perplexity 内部完成，agent 不需要自己实现 RAG 管线。

---

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
