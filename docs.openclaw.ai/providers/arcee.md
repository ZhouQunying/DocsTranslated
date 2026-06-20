# Arcee AI (Trinity)

## 架构精读

> 跳过不影响阅读翻译正文。

### 专业模型厂商——Trinity 模型的定位

Arcee AI 提供 Trinity 模型系列。跟 Anthropic/OpenAI（通用大模型）不同，Arcee 更专注于特定领域的模型微调。对 OpenClaw agent 来说，Arcee 的价值是**领域专用模型**——当通用模型在特定任务上表现不佳时，专业微调模型可能是更好的选择。

---

Arcee AI 通过其 API 提供 Trinity 模型。

## Getting started / 入门

```bash
export ARCEE_API_KEY="..."
openclaw onboard
# Choose "Arcee AI (Trinity)"
```

## Configuration / 配置

```json5
{
  agents: {
    defaults: {
      model: {
        primary: "arcee/model-name"
      }
    }
  }
}
```

## Model routing / 模型路由

OpenClaw routes `arcee/*` models through the Arcee AI (Trinity) API.

OpenClaw 通过 Arcee AI (Trinity) API 路由 `arcee/*` 模型。

## Related / 相关

- [Provider directory](/providers) — 所有提供者列表
- [Models](/providers/models) — 模型配置
