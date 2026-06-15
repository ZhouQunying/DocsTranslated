# OpenCode

OpenCode

OpenCode 通过其 Zen 和 Go 运行时提供 AI 代码辅助。

## Getting started / 入门

```bash
export N/A="..."
openclaw onboard
# Choose "OpenCode"
```

## Configuration / 配置

```json5
{
  agents: {
    defaults: {
      model: {
        primary: "opencode/model-name"
      }
    }
  }
}
```

## Model routing / 模型路由

OpenClaw routes `opencode/*` models through the OpenCode API.

OpenClaw 通过 OpenCode API 路由 `opencode/*` 模型。

## Related / 相关

- [Provider directory](/providers) — 所有提供者列表
- [Models](/providers/models) — 模型配置
