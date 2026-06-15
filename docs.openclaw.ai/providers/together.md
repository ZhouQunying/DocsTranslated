# Together AI

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
