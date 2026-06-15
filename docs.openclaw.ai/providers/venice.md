# Venice AI

Venice AI

Venice AI 提供隐私优先的推理,无数据保留。

## Getting started / 入门

```bash
export VENICE_API_KEY="..."
openclaw onboard
# Choose "Venice AI"
```

## Configuration / 配置

```json5
{
  agents: {
    defaults: {
      model: {
        primary: "venice/model-name"
      }
    }
  }
}
```

## Model routing / 模型路由

OpenClaw routes `venice/*` models through the Venice AI API.

OpenClaw 通过 Venice AI API 路由 `venice/*` 模型。

## Related / 相关

- [Provider directory](/providers) — 所有提供者列表
- [Models](/providers/models) — 模型配置
