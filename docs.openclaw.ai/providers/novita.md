# NovitaAI

## 架构精读

> 跳过不影响阅读翻译正文。

### 开源模型的云端推理——同类 provider 中的价格竞争者

NovitaAI 为开源模型提供云端推理。在 Fireworks、Together、DeepInfra、Chutes 等同类 provider 中，NovitaAI 的差异化主要在定价和模型可用性。对 OpenClaw agent 来说，多个同类 provider 增加了**价格谈判和故障转移**的灵活性。

---

NovitaAI 为开源模型提供云端推理。

## Getting started / 入门

```bash
export NOVITA_API_KEY="..."
openclaw onboard
# Choose "NovitaAI"
```

## Configuration / 配置

```json5
{
  agents: {
    defaults: {
      model: {
        primary: "novita/model-name"
      }
    }
  }
}
```

## Model routing / 模型路由

OpenClaw routes `novita/*` models through the NovitaAI API.

OpenClaw 通过 NovitaAI API 路由 `novita/*` 模型。

## Related / 相关

- [Provider directory](/providers) — 所有提供者列表
- [Models](/providers/models) — 模型配置
