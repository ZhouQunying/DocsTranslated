# Qwen OAuth / Portal

Qwen OAuth / Portal

Qwen OAuth 通过浏览器登录为 Qwen Cloud 提供认证。

## Getting started / 入门

```bash
export N/A="..."
openclaw onboard
# Choose "Qwen OAuth / Portal"
```

## Configuration / 配置

```json5
{
  agents: {
    defaults: {
      model: {
        primary: "qwen-oauth/model-name"
      }
    }
  }
}
```

## Model routing / 模型路由

OpenClaw routes `qwen-oauth/*` models through the Qwen OAuth / Portal API.

OpenClaw 通过 Qwen OAuth / Portal API 路由 `qwen-oauth/*` 模型。

## Related / 相关

- [Provider directory](/providers) — 所有提供者列表
- [Models](/providers/models) — 模型配置
