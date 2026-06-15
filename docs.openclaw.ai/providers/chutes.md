# Chutes

Chutes

Chutes 为开源模型提供云端推理。

## Getting started / 入门

```bash
export CHUTES_API_KEY="..."
openclaw onboard
# Choose "Chutes"
```

## Configuration / 配置

```json5
{
  agents: {
    defaults: {
      model: {
        primary: "chutes/model-name"
      }
    }
  }
}
```

## Model routing / 模型路由

OpenClaw routes `chutes/*` models through the Chutes API.

OpenClaw 通过 Chutes API 路由 `chutes/*` 模型。

## Related / 相关

- [Provider directory](/providers) — 所有提供者列表
- [Models](/providers/models) — 模型配置
