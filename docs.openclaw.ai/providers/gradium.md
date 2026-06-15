# Gradium

Gradium

Gradium 提供带自动扩缩和故障转移的托管推理。

## Getting started / 入门

```bash
export GRADIUM_API_KEY="..."
openclaw onboard
# Choose "Gradium"
```

## Configuration / 配置

```json5
{
  agents: {
    defaults: {
      model: {
        primary: "gradium/model-name"
      }
    }
  }
}
```

## Model routing / 模型路由

OpenClaw routes `gradium/*` models through the Gradium API.

OpenClaw 通过 Gradium API 路由 `gradium/*` 模型。

## Related / 相关

- [Provider directory](/providers) — 所有提供者列表
- [Models](/providers/models) — 模型配置
