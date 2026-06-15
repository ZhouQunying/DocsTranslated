# Fireworks

Fireworks provides fast inference for open-source models through its optimized platform.

Fireworks 通过其优化平台为开源模型提供快速推理。

## Getting started / 入门

```bash
export FIREWORKS_API_KEY="..."
openclaw onboard
# Choose "Fireworks"
```

## Configuration / 配置

```json5
{
  agents: {
    defaults: {
      model: {
        primary: "fireworks/llama-v3p3-70b-instruct"
      }
    }
  }
}
```

## Model routing / 模型路由

OpenClaw routes `fireworks/*` models through the Fireworks API.

OpenClaw 通过 Fireworks API 路由 `fireworks/*` 模型。

## Related / 相关

- [Provider directory](/providers) — 所有提供者列表
- [Models](/providers/models) — 模型配置
