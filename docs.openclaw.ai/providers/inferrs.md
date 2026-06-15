# inferrs (本地模型)

inferrs (本地模型)

inferrs 通过 OpenAI 兼容 API 提供本地模型服务。

## Getting started / 入门

```bash
export INFERRS_API_KEY="..."
openclaw onboard
# Choose "inferrs (本地模型)"
```

## Configuration / 配置

```json5
{
  agents: {
    defaults: {
      model: {
        primary: "inferrs/model-name"
      }
    }
  }
}
```

## Model routing / 模型路由

OpenClaw routes `inferrs/*` models through the inferrs (本地模型) API.

OpenClaw 通过 inferrs (本地模型) API 路由 `inferrs/*` 模型。

## Related / 相关

- [Provider directory](/providers) — 所有提供者列表
- [Models](/providers/models) — 模型配置
