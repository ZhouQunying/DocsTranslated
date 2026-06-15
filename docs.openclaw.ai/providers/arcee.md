# Arcee AI (Trinity)

Arcee AI (Trinity)

Arcee AI 通过其 API 提供 Trinity 模型。

## Getting started / 入门

```bash
export ARCEE_API_KEY="..."
openclaw onboard
# Choose "Arcee AI (Trinity)"
```

## Configuration / 配置

```json5
{
  agents: {
    defaults: {
      model: {
        primary: "arcee/model-name"
      }
    }
  }
}
```

## Model routing / 模型路由

OpenClaw routes `arcee/*` models through the Arcee AI (Trinity) API.

OpenClaw 通过 Arcee AI (Trinity) API 路由 `arcee/*` 模型。

## Related / 相关

- [Provider directory](/providers) — 所有提供者列表
- [Models](/providers/models) — 模型配置
