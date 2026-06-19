# Cerebras

## 架构精读

> 跳过不影响阅读翻译正文。

### 晶圆级芯片——为什么整个晶圆是一个芯片？

Cerebras 用晶圆级芯片（Wafer Scale Engine）做推理——把整个硅晶圆做成一个芯片，而不是切割成几百个小芯片。这跟 Groq 的 LPU 走的是同一条路：**用定制硬件碾压 GPU 的推理延迟**。

对 OpenClaw agent 来说，Cerebras 的价值跟 Groq 类似——快速推理层。但 Cerebras 的技术路线不同：Groq 是确定性执行架构（每个 token 的计算时间可预测），Cerebras 是大规模并行（晶圆上的几十万个核心同时计算）。两者都比亚马逊/谷歌的通用 GPU 集群快得多。

---

Cerebras 通过其晶圆级硬件提供超快推理。

## Getting started / 入门

```bash
export CEREBRAS_API_KEY="..."
openclaw onboard
# Choose "Cerebras"
```

## Configuration / 配置

```json5
{
  agents: {
    defaults: {
      model: {
        primary: "cerebras/model-name"
      }
    }
  }
}
```

## Model routing / 模型路由

OpenClaw routes `cerebras/*` models through the Cerebras API.

OpenClaw 通过 Cerebras API 路由 `cerebras/*` 模型。

## Related / 相关

- [Provider directory](/providers) — 所有提供者列表
- [Models](/providers/models) — 模型配置
