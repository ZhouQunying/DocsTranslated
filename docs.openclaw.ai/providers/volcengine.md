# Volcengine (Doubao)

## 架构精读

> 跳过不影响阅读翻译正文。

### 字节跳动的模型服务——云服务生态扩展

火山引擎是字节跳动的云服务平台，提供豆包（Doubao）模型系列。这跟 AWS Bedrock 在 AWS 生态中的角色类似——云服务商把 AI 模型作为云服务的一部分。对 OpenClaw agent 来说，火山引擎的价值是**字节生态集成**——如果你的业务在字节跳动的云服务上，豆包模型提供了低延迟的本地化访问。

---

火山引擎提供字节跳动豆包模型系列的访问。

## Getting started / 入门

```bash
export VOLCENGINE_API_KEY="..."
openclaw onboard
# Choose "Volcengine (Doubao)"
```

## Configuration / 配置

```json5
{
  agents: {
    defaults: {
      model: {
        primary: "volcengine/model-name"
      }
    }
  }
}
```

## Model routing / 模型路由

OpenClaw routes `volcengine/*` models through the Volcengine (Doubao) API.

OpenClaw 通过 Volcengine (Doubao) API 路由 `volcengine/*` 模型。

## Related / 相关

- [Provider directory](/providers) — 所有提供者列表
- [Models](/providers/models) — 模型配置
