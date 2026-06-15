# StepFun

StepFun

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
