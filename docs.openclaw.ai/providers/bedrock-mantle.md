# Amazon Bedrock Mantle

Amazon Bedrock Mantle

Amazon Bedrock Mantle 为 Bedrock 模型提供托管推理层,带额外路由和容量控制。

## Getting started / 入门

```bash
export BEDROCK_MANTLE_API_KEY="..."
openclaw onboard
# Choose "Amazon Bedrock Mantle"
```

## Configuration / 配置

```json5
{
  agents: {
    defaults: {
      model: {
        primary: "amazon-bedrock-mantle/model-name"
      }
    }
  }
}
```

## Model routing / 模型路由

OpenClaw routes `amazon-bedrock-mantle/*` models through the Amazon Bedrock Mantle API.

OpenClaw 通过 Amazon Bedrock Mantle API 路由 `amazon-bedrock-mantle/*` 模型。

## Related / 相关

- [Provider directory](/providers) — 所有提供者列表
- [Models](/providers/models) — 模型配置
