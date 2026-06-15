# LM Studio (本地模型)

LM Studio (本地模型)

LM Studio 通过 OpenAI 兼容 API 提供本地模型推理。

## Getting started / 入门

```bash
export N/A="..."
openclaw onboard
# Choose "LM Studio (本地模型)"
```

## Configuration / 配置

```json5
{
  agents: {
    defaults: {
      model: {
        primary: "lmstudio/model-name"
      }
    }
  }
}
```

## Model routing / 模型路由

OpenClaw routes `lmstudio/*` models through the LM Studio (本地模型) API.

OpenClaw 通过 LM Studio (本地模型) API 路由 `lmstudio/*` 模型。

## Related / 相关

- [Provider directory](/providers) — 所有提供者列表
- [Models](/providers/models) — 模型配置
