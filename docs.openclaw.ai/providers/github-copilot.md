# GitHub Copilot

## 架构精读

> 跳过不影响阅读翻译正文。

### IDE 代理桥接——复用已有认证基础设施

GitHub Copilot provider 通过本地代理桥接 VS Code 中的 Copilot 认证。这跟 models.md 中的 `copilot-proxy` 变体是一个思路——不重新申请 API key，而是复用已有的 IDE 认证。

设计意图是**零配置入门**。开发者已经登录了 VS Code Copilot，OpenClaw 直接复用那个认证。不需要额外注册、不需要额外付费、不需要管理密钥。代价是依赖 IDE 进程——VS Code 必须运行，代理才能工作。

---

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
