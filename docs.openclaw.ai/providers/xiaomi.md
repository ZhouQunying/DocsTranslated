# Xiaomi MiMo

Xiaomi MiMo

小米 MiMo 提供针对代码和数学优化的推理模型。

## Getting started / 入门

```bash
export XIAOMI_API_KEY="..."
openclaw onboard
# Choose "Xiaomi MiMo"
```

## Configuration / 配置

```json5
{
  agents: {
    defaults: {
      model: {
        primary: "xiaomi/model-name"
      }
    }
  }
}
```

## Model routing / 模型路由

OpenClaw routes `xiaomi/*` models through the Xiaomi MiMo API.

OpenClaw 通过 Xiaomi MiMo API 路由 `xiaomi/*` 模型。

## Related / 相关

- [Provider directory](/providers) — 所有提供者列表
- [Models](/providers/models) — 模型配置
