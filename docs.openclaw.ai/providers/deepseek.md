# DeepSeek

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
