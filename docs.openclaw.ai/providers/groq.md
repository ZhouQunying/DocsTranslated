# Groq (LPU inference)

## 架构精读

> 跳过不影响阅读翻译正文。

### 专用硅 vs 通用 GPU——硬件层推理优化

Groq 用 LPU（Language Processing Unit）替代 GPU 做推理。这跟 Google TPU 替代 GPU 做训练是一个思路——通用 GPU 什么都能算，但为 LLM 推理定制的 ASIC 在吞吐和延迟上碾压通用硬件。

对 OpenClaw 来说，Groq 的价值不是"另一个模型提供商"，而是**推理速度层**。当 agent 需要快速工具调用循环（每秒多次调用），Groq 的低延迟比 Anthropic/OpenAI 的通用 API 更合适。代价是模型选择有限——Groq 只托管能在 LPU 上高效运行的模型。

---

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
