# StepFun

## 架构精读

> 跳过不影响阅读翻译正文。

### 多模态 AI——StepFun 的定位

StepFun 提供多模态 AI 模型。在中国 AI 厂商中（阿里 Qwen、百度 ERNIE、字节豆包、MiniMax），StepFun 的差异化主要在模型架构和推理效率。对 OpenClaw agent 来说，StepFun 是中国市场的**另一个多模态选择**。

---

StepFun 提供多模态 AI 模型。

## Getting started / 入门

```bash
export STEPFUN_API_KEY="..."
openclaw onboard
# Choose "StepFun"
```

## Configuration / 配置

```json5
{
  agents: {
    defaults: {
      model: {
        primary: "stepfun/model-name"
      }
    }
  }
}
```

## Model routing / 模型路由

OpenClaw routes `stepfun/*` models through the StepFun API.

OpenClaw 通过 StepFun API 路由 `stepfun/*` 模型。

## Related / 相关

- [Provider directory](/providers) — 所有提供者列表
- [Models](/providers/models) — 模型配置
