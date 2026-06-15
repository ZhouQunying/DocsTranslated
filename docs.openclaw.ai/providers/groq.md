# Groq (LPU inference)

Groq provides ultra-fast inference through its Language Processing Unit (LPU) hardware.

Groq 通过其语言处理单元(LPU)硬件提供超快推理。

## Getting started / 入门

```bash
export GROQ_API_KEY="gsk_..."
openclaw onboard
# Choose "Groq"
```

## Configuration / 配置

```json5
{
  agents: {
    defaults: {
      model: {
        primary: "groq/llama-3.3-70b-versatile"
      }
    }
  }
}
```

## Model routing / 模型路由

OpenClaw routes `groq/*` models through the Groq API.

OpenClaw 通过 Groq API 路由 `groq/*` 模型。

## Related / 相关

- [Provider directory](/providers) — 所有提供者列表
- [Models](/providers/models) — 模型配置
