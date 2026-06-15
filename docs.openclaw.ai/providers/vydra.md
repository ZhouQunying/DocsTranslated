# Vydra

Vydra

Vydra 提供带优化路由的托管推理。

## Getting started / 入门

```bash
export VYDRA_API_KEY="..."
openclaw onboard
# Choose "Vydra"
```

## Configuration / 配置

```json5
{
  agents: {
    defaults: {
      model: {
        primary: "vydra/model-name"
      }
    }
  }
}
```

## Model routing / 模型路由

OpenClaw routes `vydra/*` models through the Vydra API.

OpenClaw 通过 Vydra API 路由 `vydra/*` 模型。

## Related / 相关

- [Provider directory](/providers) — 所有提供者列表
- [Models](/providers/models) — 模型配置
