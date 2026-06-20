# Xiaomi MiMo

## 架构精读

> 跳过不影响阅读翻译正文。

### 代码和数学优化——推理模型的专用场景

小米 MiMo 提供针对代码和数学优化的推理模型。这跟 DeepSeek 的 reasoner 模型是一个思路——推理模型（thinking tokens）在需要多步骤逻辑推理的任务上表现更好。对 OpenClaw agent 来说，MiMo 适合**编程和数学任务**——如代码审查、算法分析、数学问题求解。

---

小米 MiMo 提供针对代码和数学优化的推理模型。

## Getting started / 入门

```bash
export XIAOMI_API_KEY="..."
openclaw onboard
# Choose "Xiaomi MiMo"
```

## Configuration / 配置

```json5
{
  agents: {
    defaults: {
      model: {
        primary: "xiaomi/model-name"
      }
    }
  }
}
```

## Model routing / 模型路由

OpenClaw routes `xiaomi/*` models through the Xiaomi MiMo API.

OpenClaw 通过 Xiaomi MiMo API 路由 `xiaomi/*` 模型。

## Related / 相关

- [Provider directory](/providers) — 所有提供者列表
- [Models](/providers/models) — 模型配置
