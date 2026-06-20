# Synthetic

## 架构精读

> 跳过不影响阅读翻译正文。

### 模型托管和推理——通用 AI 基础设施

Synthetic 提供通用的 AI 模型托管和推理。在 provider 生态中，Synthetic 的定位是**通用基础设施层**——不强调特定模型或优化，而是提供可靠的推理端点。

---

Synthetic 提供 AI 模型托管和推理。

## Getting started / 入门

```bash
export SYNTHETIC_API_KEY="..."
openclaw onboard
# Choose "Synthetic"
```

## Configuration / 配置

```json5
{
  agents: {
    defaults: {
      model: {
        primary: "synthetic/model-name"
      }
    }
  }
}
```

## Model routing / 模型路由

OpenClaw routes `synthetic/*` models through the Synthetic API.

OpenClaw 通过 Synthetic API 路由 `synthetic/*` 模型。

## Related / 相关

- [Provider directory](/providers) — 所有提供者列表
- [Models](/providers/models) — 模型配置
