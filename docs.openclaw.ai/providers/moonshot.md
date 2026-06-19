# Moonshot AI (Kimi + Kimi Coding)

## 架构精读

> 跳过不影响阅读翻译正文。

### 编码专用模型——Kimi Coding 的 agent 价值

Moonshot AI 的 Kimi 模型系列包括 Kimi Coding，专门优化了编程任务。这跟 Anthropic 的 Claude（通用）和 GitHub Copilot（编码专用）的分工是一个思路。对 OpenClaw agent 来说，Kimi Coding 可以作为**编码任务的专用模型**——用 `primary` 配置 Kimi Coding 做代码生成，用 `fallback` 配置通用模型做对话。

---

Moonshot AI provides the Kimi model family, including Kimi Coding for programming tasks.

Moonshot AI 提供 Kimi 模型系列,包括用于编程任务的 Kimi Coding。

## Getting started / 入门

```bash
export MOONSHOT_API_KEY="..."
openclaw onboard
# Choose "Moonshot AI"
```

## Configuration / 配置

```json5
{
  agents: {
    defaults: {
      model: {
        primary: "moonshot/kimi-k2"
      }
    }
  }
}
```

## Model routing / 模型路由

OpenClaw routes `moonshot/*` models through the Moonshot AI API.

OpenClaw 通过 Moonshot AI API 路由 `moonshot/*` 模型。

## Related / 相关

- [Provider directory](/providers) — 所有提供者列表
- [Models](/providers/models) — 模型配置
