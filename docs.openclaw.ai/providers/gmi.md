# GMI Cloud

GMI Cloud

GMI Cloud 为开源模型提供 GPU 加速推理。

## Getting started / 入门

```bash
export GMI_API_KEY="..."
openclaw onboard
# Choose "GMI Cloud"
```

## Configuration / 配置

```json5
{
  agents: {
    defaults: {
      model: {
        primary: "gmi/model-name"
      }
    }
  }
}
```

## Model routing / 模型路由

OpenClaw routes `gmi/*` models through the GMI Cloud API.

OpenClaw 通过 GMI Cloud API 路由 `gmi/*` 模型。

## Related / 相关

- [Provider directory](/providers) — 所有提供者列表
- [Models](/providers/models) — 模型配置
