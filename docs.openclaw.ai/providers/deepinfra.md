# DeepInfra

DeepInfra

DeepInfra 为开源模型提供无服务器推理。

## Getting started / 入门

```bash
export DEEPINFRA_API_KEY="..."
openclaw onboard
# Choose "DeepInfra"
```

## Configuration / 配置

```json5
{
  agents: {
    defaults: {
      model: {
        primary: "deepinfra/model-name"
      }
    }
  }
}
```

## Model routing / 模型路由

OpenClaw routes `deepinfra/*` models through the DeepInfra API.

OpenClaw 通过 DeepInfra API 路由 `deepinfra/*` 模型。

## Related / 相关

- [Provider directory](/providers) — 所有提供者列表
- [Models](/providers/models) — 模型配置
