# NovitaAI

NovitaAI

NovitaAI 为开源模型提供云端推理。

## Getting started / 入门

```bash
export NOVITA_API_KEY="..."
openclaw onboard
# Choose "NovitaAI"
```

## Configuration / 配置

```json5
{
  agents: {
    defaults: {
      model: {
        primary: "novita/model-name"
      }
    }
  }
}
```

## Model routing / 模型路由

OpenClaw routes `novita/*` models through the NovitaAI API.

OpenClaw 通过 NovitaAI API 路由 `novita/*` 模型。

## Related / 相关

- [Provider directory](/providers) — 所有提供者列表
- [Models](/providers/models) — 模型配置
