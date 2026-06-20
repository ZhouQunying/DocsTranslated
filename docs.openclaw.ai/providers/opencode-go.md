# OpenCode Go

## 架构精读

> 跳过不影响阅读翻译正文。

### Go 运行时——编译型语言的性能优势

OpenCode Go 通过 Go 运行时提供 AI 代码辅助。Go 是编译型语言，比 Zen 的解释型运行时更快且内存占用更低。对 OpenClaw agent 来说，Go 运行时适合**需要高性能代码执行**的场景——如大规模代码分析和重构。

---

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
