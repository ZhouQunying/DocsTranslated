# SGLang (本地模型)

SGLang (本地模型)

SGLang 提供带结构化生成的快速本地模型服务。

## Getting started / 入门

```bash
export N/A="..."
openclaw onboard
# Choose "SGLang (本地模型)"
```

## Configuration / 配置

```json5
{
  agents: {
    defaults: {
      model: {
        primary: "sglang/model-name"
      }
    }
  }
}
```

## Model routing / 模型路由

OpenClaw routes `sglang/*` models through the SGLang (本地模型) API.

OpenClaw 通过 SGLang (本地模型) API 路由 `sglang/*` 模型。

## Related / 相关

- [Provider directory](/providers) — 所有提供者列表
- [Models](/providers/models) — 模型配置
