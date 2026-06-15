# Model provider quickstart / 模型提供者快速开始

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
