# Amazon Bedrock Mantle

## 架构精读

> 跳过不影响阅读翻译正文。

### Bedrock 的托管增强层——路由和容量控制

Bedrock Mantle 为标准 Bedrock 添加了额外路由和容量控制。这跟 AWS 的"标准 vs 增强"服务模式类似（如 EC2 vs EC2 Enhanced Networking）。对 OpenClaw agent 来说，Mantle 适合**高流量生产场景**——当你需要比标准 Bedrock 更精细的流量管理和容量保障时。

---

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
