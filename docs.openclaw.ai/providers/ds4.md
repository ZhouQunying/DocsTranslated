# ds4 (本地 DeepSeek V4)

ds4 (本地 DeepSeek V4)

ds4 通过 MLX 在 Apple Silicon 上本地运行 DeepSeek V4。

## Getting started / 入门

```bash
export N/A="..."
openclaw onboard
# Choose "ds4 (本地 DeepSeek V4)"
```

## Configuration / 配置

```json5
{
  agents: {
    defaults: {
      model: {
        primary: "ds4/model-name"
      }
    }
  }
}
```

## Model routing / 模型路由

OpenClaw routes `ds4/*` models through the ds4 (本地 DeepSeek V4) API.

OpenClaw 通过 ds4 (本地 DeepSeek V4) API 路由 `ds4/*` 模型。

## Related / 相关

- [Provider directory](/providers) — 所有提供者列表
- [Models](/providers/models) — 模型配置
