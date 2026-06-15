# OpenCode Go

OpenCode Go

OpenCode Go 通过 Go 运行时提供 AI 代码辅助。

## Getting started / 入门

```bash
export N/A="..."
openclaw onboard
# Choose "OpenCode Go"
```

## Configuration / 配置

```json5
{
  agents: {
    defaults: {
      model: {
        primary: "opencode-go/model-name"
      }
    }
  }
}
```

## Model routing / 模型路由

OpenClaw routes `opencode-go/*` models through the OpenCode Go API.

OpenClaw 通过 OpenCode Go API 路由 `opencode-go/*` 模型。

## Related / 相关

- [Provider directory](/providers) — 所有提供者列表
- [Models](/providers/models) — 模型配置
