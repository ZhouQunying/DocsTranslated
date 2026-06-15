# PixVerse

PixVerse

PixVerse 提供 AI 视频生成。

## Getting started / 入门

```bash
export PIXVERSE_API_KEY="..."
openclaw onboard
# Choose "PixVerse"
```

## Configuration / 配置

```json5
{
  agents: {
    defaults: {
      model: {
        primary: "pixverse/model-name"
      }
    }
  }
}
```

## Model routing / 模型路由

OpenClaw routes `pixverse/*` models through the PixVerse API.

OpenClaw 通过 PixVerse API 路由 `pixverse/*` 模型。

## Related / 相关

- [Provider directory](/providers) — 所有提供者列表
- [Models](/providers/models) — 模型配置
