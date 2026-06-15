# Moonshot AI (Kimi + Kimi Coding)

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
