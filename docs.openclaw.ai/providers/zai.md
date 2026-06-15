# Z.AI (GLM)

Z.AI (GLM)

Z.AI 提供 GLM 模型系列的访问。

## Getting started / 入门

```bash
export ZAI_API_KEY="..."
openclaw onboard
# Choose "Z.AI (GLM)"
```

## Configuration / 配置

```json5
{
  agents: {
    defaults: {
      model: {
        primary: "zai/model-name"
      }
    }
  }
}
```

## Model routing / 模型路由

OpenClaw routes `zai/*` models through the Z.AI (GLM) API.

OpenClaw 通过 Z.AI (GLM) API 路由 `zai/*` 模型。

## Related / 相关

- [Provider directory](/providers) — 所有提供者列表
- [Models](/providers/models) — 模型配置
