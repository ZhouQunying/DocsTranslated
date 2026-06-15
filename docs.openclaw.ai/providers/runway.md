# Runway

Runway

Runway 提供 AI 视频和图像生成。

## Getting started / 入门

```bash
export RUNWAY_API_KEY="..."
openclaw onboard
# Choose "Runway"
```

## Configuration / 配置

```json5
{
  agents: {
    defaults: {
      model: {
        primary: "runway/model-name"
      }
    }
  }
}
```

## Model routing / 模型路由

OpenClaw routes `runway/*` models through the Runway API.

OpenClaw 通过 Runway API 路由 `runway/*` 模型。

## Related / 相关

- [Provider directory](/providers) — 所有提供者列表
- [Models](/providers/models) — 模型配置
