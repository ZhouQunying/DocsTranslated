# Fireworks

## 架构精读

> 跳过不影响阅读翻译正文。

### 开源模型的托管推理——Fireworks vs Together vs 自托管

Fireworks 为开源模型提供优化推理。跟 Together AI（类似定位）相比，Fireworks 更强调推理速度优化（如 speculative decoding）。跟自托管（vLLM/SGLang）相比，Fireworks 的价值是**零运维**——不需要管理 GPU 集群，但代价是按量计费而非固定成本。

---

Fireworks provides fast inference for open-source models through its optimized platform.

Fireworks 通过其优化平台为开源模型提供快速推理。

## Getting started / 入门

```bash
export FIREWORKS_API_KEY="..."
openclaw onboard
# Choose "Fireworks"
```

## Configuration / 配置

```json5
{
  agents: {
    defaults: {
      model: {
        primary: "fireworks/llama-v3p3-70b-instruct"
      }
    }
  }
}
```

## Model routing / 模型路由

OpenClaw routes `fireworks/*` models through the Fireworks API.

OpenClaw 通过 Fireworks API 路由 `fireworks/*` 模型。

## Related / 相关

- [Provider directory](/providers) — 所有提供者列表
- [Models](/providers/models) — 模型配置
