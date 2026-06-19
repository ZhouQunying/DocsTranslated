# DeepSeek

## 架构精读

> 跳过不影响阅读翻译正文。

### 推理模型——thinking tokens 的架构意义

DeepSeek 的 `deepseek-reasoner` 模型是推理模型——它先输出 thinking tokens（推理过程），再输出 answer tokens（最终答案）。这跟 OpenAI 的 o1/o3 是一个思路。

对 OpenClaw agent 来说，推理模型的价值是**显式推理链**。普通模型直接给答案，推理模型先展示思考过程。这对 agent 的工具调用决策特别有用——agent 可以看到模型的推理过程，判断是否应该信任这个工具调用。

代价是推理模型更慢且更贵（thinking tokens 也要计费）。但 agent 可以在关键决策点用推理模型，在简单任务用普通模型——`primary` 和 `fallback` 模型配置的典型用法。

---

DeepSeek provides high-performance reasoning models through its API.

DeepSeek 通过其 API 提供高性能推理模型。

## Getting started / 入门

```bash
export DEEPSEEK_API_KEY="sk-..."
openclaw onboard
# Choose "DeepSeek"
```

## Configuration / 配置

```json5
{
  agents: {
    defaults: {
      model: {
        primary: "deepseek/deepseek-reasoner"
      }
    }
  }
}
```

## Model routing / 模型路由

OpenClaw routes `deepseek/*` models through the DeepSeek API.

OpenClaw 通过 DeepSeek API 路由 `deepseek/*` 模型。

## Related / 相关

- [Provider directory](/providers) — 所有提供者列表
- [Models](/providers/models) — 模型配置
