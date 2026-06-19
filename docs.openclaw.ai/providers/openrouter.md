# OpenRouter

## 架构精读

> 跳过不影响阅读翻译正文。

### 元提供者模式——代理后面的代理

OpenRouter 本身就是一个统一 API 网关，路由到 100+ 模型。OpenClaw 再通过 `openrouter/*` 路由到 OpenRouter。这是**两层代理**——OpenClaw 代理 OpenRouter，OpenRouter 代理实际模型提供商。

这跟 CDN 的"CDN behind CDN"模式是一个思路。Cloudflare 有时候会路由请求到 Fastly，Fastly 再路由到源服务器。每一层都添加价值（缓存、安全、路由优化），但也增加延迟和调试复杂度。

设计意图是**最大化模型覆盖面**。OpenRouter 已经做了"统一多个模型 API"的脏活。OpenClaw 不需要自己实现每个模型的适配器——只需要一个 OpenRouter 适配器，就能间接访问 OpenRouter 后面的所有模型。

代价是双重抽象带来的不透明。如果 OpenRouter 的路由策略改变了（比如从 Anthropic 切到另一个 Anthropic 代理），OpenClaw 用户可能不知道。但这是使用元提供者的固有代价——你信任中间层做正确的路由。

### PKCE OAuth——无头环境的认证挑战

OpenRouter 支持 PKCE OAuth 流程。OpenClaw 打开浏览器登录，交换 PKCE 代码获取 API 密钥。在远程/无头主机上，OpenClaw 打印 URL 让用户手动粘贴。

这跟 GitHub CLI 的 device flow 是一个思路。CLI 工具无法像 Web 应用那样做 OAuth 重定向（没有浏览器）。解决方案是"用户在另一个设备上完成认证，然后把凭证传回来"。PKCE 保证了即使授权码被拦截，攻击者也无法交换 token（因为没有 code verifier）。

---

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
