# Chutes

## 架构精读

> 跳过不影响阅读翻译正文。

### 开源模型的云端推理——又一个无服务器选择

Chutes 为开源模型提供云端推理，定位类似 DeepInfra 和 Together AI。对 OpenClaw agent 来说，多个同类 provider 的价值是**故障转移和价格竞争**——当某个 provider 不可用或价格不合适时，可以快速切换。

---

Chutes 为开源模型提供云端推理。

## Getting started / 入门

```bash
export CHUTES_API_KEY="..."
openclaw onboard
# Choose "Chutes"
```

## Configuration / 配置

```json5
{
  agents: {
    defaults: {
      model: {
        primary: "chutes/model-name"
      }
    }
  }
}
```

## Model routing / 模型路由

OpenClaw routes `chutes/*` models through the Chutes API.

OpenClaw 通过 Chutes API 路由 `chutes/*` 模型。

## Related / 相关

- [Provider directory](/providers) — 所有提供者列表
- [Models](/providers/models) — 模型配置
