# Kilocode

## 架构精读

> 跳过不影响阅读翻译正文。

### 优化路由的托管推理——延迟优先

Kilocode 提供带优化路由的托管推理。优化路由意味着 Kilocode 在后端多个推理节点之间选择延迟最低的路径。对 OpenClaw agent 来说，这在**实时交互场景**中很重要——agent 的每个工具调用都需要快速响应。

---

Kilocode 提供带优化路由的托管推理。

## Getting started / 入门

```bash
export KILOCODE_API_KEY="..."
openclaw onboard
# Choose "Kilocode"
```

## Configuration / 配置

```json5
{
  agents: {
    defaults: {
      model: {
        primary: "kilocode/model-name"
      }
    }
  }
}
```

## Model routing / 模型路由

OpenClaw routes `kilocode/*` models through the Kilocode API.

OpenClaw 通过 Kilocode API 路由 `kilocode/*` 模型。

## Related / 相关

- [Provider directory](/providers) — 所有提供者列表
- [Models](/providers/models) — 模型配置
