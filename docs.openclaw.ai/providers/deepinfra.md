# DeepInfra

## 架构精读

> 跳过不影响阅读翻译正文。

### 无服务器开源推理——按需计费、无预置

DeepInfra 为开源模型提供无服务器推理，定位类似 fal（媒体生成）但面向文本模型。对 OpenClaw agent 来说，无服务器的价值是**按需计费、无预置**——不需要预留 GPU 实例，只在调用时付费。

---

DeepInfra 为开源模型提供无服务器推理。

## Getting started / 入门

```bash
export DEEPINFRA_API_KEY="..."
openclaw onboard
# Choose "DeepInfra"
```

## Configuration / 配置

```json5
{
  agents: {
    defaults: {
      model: {
        primary: "deepinfra/model-name"
      }
    }
  }
}
```

## Model routing / 模型路由

OpenClaw routes `deepinfra/*` models through the DeepInfra API.

OpenClaw 通过 DeepInfra API 路由 `deepinfra/*` 模型。

## Related / 相关

- [Provider directory](/providers) — 所有提供者列表
- [Models](/providers/models) — 模型配置
