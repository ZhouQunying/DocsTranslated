# Model provider quickstart / 模型提供者快速开始

## 架构精读

> 跳过不影响阅读翻译正文。

### Starter set vs 完整目录——为什么要两层？

models.md 列出了"starter set"（约 25 个经过验证的提供者），而 index.md 列出完整目录（50+ 个）。这跟 AWS SDK 的"supported services"分层是一个思路。

AWS SDK 把所有服务都暴露出来，但把常用服务标记为"recommended"——新手从 recommended 开始，老手可以探索全部。OpenClaw 的 starter set 也是这个意图：筛选出最稳定、最常见、文档最完善的提供者，降低新用户的选择焦虑。

代价是 starter set 之外的提供者可能文档不完善。但这是实用主义的取舍——50+ 个提供者全部维护到同一标准不现实。分层让用户知道哪些是"一等公民"，哪些是"社区支持"。

### Provider variants——扩展点的三种模式

额外提供者变体展示了三种不同的扩展模式：

- **`anthropic-vertex`**：在 Google Vertex 上运行 Anthropic 模型的桥接。当 Vertex 凭证可用时自动启用。这是**透明代理**模式——用户不需要知道底层是 Vertex 还是直接 Anthropic
- **`copilot-proxy`**：复用 VS Code Copilot 的本地认证。这是**认证复用**模式——利用已有的认证基础设施
- **`google-gemini-cli`**：非官方 Gemini CLI OAuth 流程。这是**社区桥接**模式——在官方 API 不可用时，用 CLI 工具的认证作为替代

这三种模式代表了 provider 系统的扩展哲学：不只是"添加新 API"，还包括"桥接已有基础设施"和"利用非官方通道"。代价是系统复杂度增加，但好处是用户可以用已有的认证和工具，不需要额外申请 API key。

---

OpenClaw can use many LLM providers. Pick one, authenticate, then set the default model as `provider/model`.

OpenClaw 可以使用多种 LLM 提供者。选择一个,进行认证,然后将默认模型设置为 `provider/model`。

## Quick start (two steps) / 快速开始(两步)

- Authenticate with the provider (usually via `openclaw onboard`).
  
  与提供者进行认证(通常通过 `openclaw onboard`)。

- Set the default model:
  
  设置默认模型:

```json5
{
  agents: {
    defaults: {
      model: {
        primary: "anthropic/claude-opus-4-6"
      }
    }
  }
}
```

## Supported providers (starter set) / 支持的提供者(入门集)

- Alibaba Model Studio
- Amazon Bedrock
- Anthropic (API + Claude CLI)
- BytePlus (International)
- Chutes
- ComfyUI
- Cloudflare AI Gateway
- DeepInfra
- fal
- Fireworks
- MiniMax
- Mistral
- Moonshot AI (Kimi + Kimi Coding)
- OpenAI (API + Codex)
- OpenCode (Zen + Go)
- OpenRouter
- Qianfan
- Qwen
- Runway
- StepFun
- Synthetic
- Vercel AI Gateway
- Venice (Venice AI)
- xAI
- Z.AI (GLM)

## Additional provider variants / 额外提供者变体

- `anthropic-vertex` - install `@openclaw/anthropic-vertex-provider` for implicit Anthropic on Google Vertex support when Vertex credentials are available; no separate onboarding auth choice
  
  安装 `@openclaw/anthropic-vertex-provider` 以在 Vertex 凭证可用时隐式支持 Google Vertex 上的 Anthropic;无需单独的入门认证选择

- `copilot-proxy` - local VS Code Copilot Proxy bridge; use `openclaw onboard --auth-choice copilot-proxy`
  
  本地 VS Code Copilot Proxy 桥接;使用 `openclaw onboard --auth-choice copilot-proxy`

- `google-gemini-cli` - unofficial Gemini CLI OAuth flow; requires a local `gemini` install (`brew install gemini-cli` or `npm install -g @google/gemini-cli`); default model `google-gemini-cli/gemini-3-flash-preview`; use `openclaw onboard --auth-choice google-gemini-cli` or `openclaw models auth login --provider google-gemini-cli --set-default`
  
  非官方 Gemini CLI OAuth 流程;需要本地 `gemini` 安装(`brew install gemini-cli` 或 `npm install -g @google/gemini-cli`);默认模型 `google-gemini-cli/gemini-3-flash-preview`;使用 `openclaw onboard --auth-choice google-gemini-cli` 或 `openclaw models auth login --provider google-gemini-cli --set-default`

For the full provider catalog (xAI, Groq, Mistral, etc.) and advanced configuration, see [Model providers](/providers).

完整提供者目录(xAI、Groq、Mistral 等)和高级配置,参见[模型提供者](/providers)。

## Related / 相关

- [Model selection](/providers/models#model-selection) — 模型选择
- [Model failover](/providers/models#model-failover) — 模型故障转移
- [Models CLI](/providers/models#models-cli) — Models CLI
