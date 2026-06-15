# OpenRouter

OpenRouter provides a unified API that routes requests to many models behind a single endpoint and API key. It is OpenAI-compatible, so most OpenAI SDKs work by switching the base URL.

OpenRouter 提供统一 API,将请求路由到单一端点和 API 密钥后的多种模型。它与 OpenAI 兼容,因此大多数 OpenAI SDK 通过切换基础 URL 即可工作。

## Getting started / 入门

### OAuth / OAuth 认证

```bash
openclaw onboard --auth-choice openrouter-oauth
```

OpenClaw opens OpenRouter's browser sign-in flow, exchanges the PKCE code for an OpenRouter API key, and stores that key in the default OpenRouter auth profile. On remote/headless hosts, OpenClaw prints the sign-in URL and asks you to paste the redirect URL after signing in.

OpenClaw 打开 OpenRouter 的浏览器登录流程,将 PKCE 代码交换为 OpenRouter API 密钥,并将该密钥存储在默认 OpenRouter 认证配置文件中。在远程/无头主机上,OpenClaw 打印登录 URL 并要求你在登录后粘贴重定向 URL。

### API key / API 密钥

```bash
export OPENROUTER_API_KEY="sk-or-..."
openclaw onboard
# Choose "OpenRouter"
```

## Configuration / 配置

```json5
{
  agents: {
    defaults: {
      model: {
        primary: "openrouter/anthropic/claude-opus-4-6"
      }
    }
  }
}
```

## Model routing / 模型路由

OpenClaw routes `openrouter/*` models through the OpenRouter unified API. Model IDs follow the pattern `openrouter/<provider>/<model>`.

OpenClaw 通过 OpenRouter 统一 API 路由 `openrouter/*` 模型。模型 ID 遵循 `openrouter/<provider>/<model>` 模式。

## Related / 相关

- [Provider directory](/providers) — 所有提供者列表
- [Models](/providers/models) — 模型配置
