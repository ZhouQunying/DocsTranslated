# Qwen OAuth / Portal

## 架构精读

> 跳过不影响阅读翻译正文。

### 浏览器 OAuth——不需要 API key 的认证路径

Qwen OAuth 通过浏览器登录认证，不需要申请 DashScope API key。这跟 models.md 中的 `google-gemini-cli` 变体是一个思路——**降低入门摩擦**。对于想快速试用 Qwen 但不想注册 DashScope 账号的用户，OAuth 登录是最快路径。

---

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
