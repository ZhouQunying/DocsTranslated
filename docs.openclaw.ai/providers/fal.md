# fal

fal

fal 通过其无服务器平台提供快速图像和视频生成。

## Getting started / 入门

```bash
export FAL_KEY="..."
openclaw onboard
# Choose "fal"
```

## Configuration / 配置

```json5
{
  agents: {
    defaults: {
      model: {
        primary: "fal/model-name"
      }
    }
  }
}
```

## Model routing / 模型路由

OpenClaw routes `fal/*` models through the fal API.

OpenClaw 通过 fal API 路由 `fal/*` 模型。

## Related / 相关

- [Provider directory](/providers) — 所有提供者列表
- [Models](/providers/models) — 模型配置
