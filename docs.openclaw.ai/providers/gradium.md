# Gradium

## 架构精读

> 跳过不影响阅读翻译正文。

### 自动扩缩 + 故障转移——托管推理的运维保障

Gradium 提供带自动扩缩和故障转移的托管推理。这跟 AWS Auto Scaling 是一个思路——流量高峰时自动扩容，低谷时缩容，provider 故障时自动切换。对 OpenClaw agent 来说，Gradium 适合**需要高可用保障的生产场景**。

---

Gradium 提供带自动扩缩和故障转移的托管推理。

## Getting started / 入门

```bash
export GRADIUM_API_KEY="..."
openclaw onboard
# Choose "Gradium"
```

## Configuration / 配置

```json5
{
  agents: {
    defaults: {
      model: {
        primary: "gradium/model-name"
      }
    }
  }
}
```

## Model routing / 模型路由

OpenClaw routes `gradium/*` models through the Gradium API.

OpenClaw 通过 Gradium API 路由 `gradium/*` 模型。

## Related / 相关

- [Provider directory](/providers) — 所有提供者列表
- [Models](/providers/models) — 模型配置
