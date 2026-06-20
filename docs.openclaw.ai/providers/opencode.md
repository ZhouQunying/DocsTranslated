# OpenCode

## 架构精读

> 跳过不影响阅读翻译正文。

### Zen + Go 双运行时——编码 agent 的执行引擎

OpenCode 提供 Zen 和 Go 两种运行时。双运行时让 agent 可以根据任务选择执行环境——Zen 适合快速交互，Go 适合需要编译和高性能的场景。对 OpenClaw agent 来说，OpenCode 是**编码任务的专用执行引擎**。

---

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
