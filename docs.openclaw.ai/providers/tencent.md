# Tencent Cloud (TokenHub)

## 架构精读

> 跳过不影响阅读翻译正文。

### 腾讯云生态的模型入口——混元和其他模型

腾讯云 TokenHub 提供混元（Hunyuan）和其他模型的访问。这跟 AWS Bedrock 在 AWS 生态中的角色类似——云服务商把自研模型和第三方模型统一到同一个 API 平台。对 OpenClaw agent 来说，腾讯云的价值是**腾讯生态集成**——微信、企业微信等腾讯产品的 agent 工作流。

---

腾讯云 TokenHub 提供混元和其他模型的访问。

## Getting started / 入门

```bash
export TENCENT_API_KEY="..."
openclaw onboard
# Choose "Tencent Cloud (TokenHub)"
```

## Configuration / 配置

```json5
{
  agents: {
    defaults: {
      model: {
        primary: "tencent/model-name"
      }
    }
  }
}
```

## Model routing / 模型路由

OpenClaw routes `tencent/*` models through the Tencent Cloud (TokenHub) API.

OpenClaw 通过 Tencent Cloud (TokenHub) API 路由 `tencent/*` 模型。

## Related / 相关

- [Provider directory](/providers) — 所有提供者列表
- [Models](/providers/models) — 模型配置
