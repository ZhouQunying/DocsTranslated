# Kilocode

Kilocode

Kilocode 提供带优化路由的托管推理。

## Getting started / 入门

```bash
export KILOCODE_API_KEY="..."
openclaw onboard
# Choose "Kilocode"
```

## Configuration / 配置

```json5
{
  agents: {
    defaults: {
      model: {
        primary: "kilocode/model-name"
      }
    }
  }
}
```

## Model routing / 模型路由

OpenClaw routes `kilocode/*` models through the Kilocode API.

OpenClaw 通过 Kilocode API 路由 `kilocode/*` 模型。

## Related / 相关

- [Provider directory](/providers) — 所有提供者列表
- [Models](/providers/models) — 模型配置
