# Together AI

## 架构精读

> 跳过不影响阅读翻译正文。

### 开源模型的训练+推理平台——不只是推理

Together AI 不只做推理，还提供模型微调和训练。这跟 AWS SageMaker 是一个思路——不只是运行模型，还覆盖训练、微调、部署的完整 ML 生命周期。对 OpenClaw agent 来说，Together AI 的价值是**模型定制**——你可以微调一个专用模型，然后通过 Together API 调用它。

---

Together AI provides inference for open-source models through its cloud platform.

Together AI 通过其云平台为开源模型提供推理。

## Getting started / 入门

```bash
export TOGETHER_API_KEY="..."
openclaw onboard
# Choose "Together AI"
```

## Configuration / 配置

```json5
{
  agents: {
    defaults: {
      model: {
        primary: "together/meta-llama/Llama-3.3-70B-Instruct-Turbo"
      }
    }
  }
}
```

## Model routing / 模型路由

OpenClaw routes `together/*` models through the Together AI API.

OpenClaw 通过 Together AI API 路由 `together/*` 模型。

## Related / 相关

- [Provider directory](/providers) — 所有提供者列表
- [Models](/providers/models) — 模型配置
