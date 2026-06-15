# Cerebras

Cerebras

Cerebras 通过其晶圆级硬件提供超快推理。

## Getting started / 入门

```bash
export CEREBRAS_API_KEY="..."
openclaw onboard
# Choose "Cerebras"
```

## Configuration / 配置

```json5
{
  agents: {
    defaults: {
      model: {
        primary: "cerebras/model-name"
      }
    }
  }
}
```

## Model routing / 模型路由

OpenClaw routes `cerebras/*` models through the Cerebras API.

OpenClaw 通过 Cerebras API 路由 `cerebras/*` 模型。

## Related / 相关

- [Provider directory](/providers) — 所有提供者列表
- [Models](/providers/models) — 模型配置
