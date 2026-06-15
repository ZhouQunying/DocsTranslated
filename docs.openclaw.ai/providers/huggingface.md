# Hugging Face (推理)

Hugging Face (推理)

Hugging Face 为开源模型提供推理端点。

## Getting started / 入门

```bash
export HUGGINGFACE_API_KEY="..."
openclaw onboard
# Choose "Hugging Face (推理)"
```

## Configuration / 配置

```json5
{
  agents: {
    defaults: {
      model: {
        primary: "huggingface/model-name"
      }
    }
  }
}
```

## Model routing / 模型路由

OpenClaw routes `huggingface/*` models through the Hugging Face (推理) API.

OpenClaw 通过 Hugging Face (推理) API 路由 `huggingface/*` 模型。

## Related / 相关

- [Provider directory](/providers) — 所有提供者列表
- [Models](/providers/models) — 模型配置
