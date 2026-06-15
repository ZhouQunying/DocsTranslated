# GitHub Copilot

GitHub Copilot

GitHub Copilot 通过本地代理桥接提供 AI 代码补全。

## Getting started / 入门

```bash
export N/A="..."
openclaw onboard
# Choose "GitHub Copilot"
```

## Configuration / 配置

```json5
{
  agents: {
    defaults: {
      model: {
        primary: "github-copilot/model-name"
      }
    }
  }
}
```

## Model routing / 模型路由

OpenClaw routes `github-copilot/*` models through the GitHub Copilot API.

OpenClaw 通过 GitHub Copilot API 路由 `github-copilot/*` 模型。

## Related / 相关

- [Provider directory](/providers) — 所有提供者列表
- [Models](/providers/models) — 模型配置
