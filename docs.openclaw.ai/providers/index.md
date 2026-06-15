# Provider directory / 提供者目录

OpenClaw can use many LLM providers. Pick a provider, authenticate, then set the default model as `provider/model`.

OpenClaw 可以使用多种 LLM 提供者。选择一个提供者,进行认证,然后将默认模型设置为 `provider/model`。

Looking for chat channel docs (WhatsApp/Telegram/Discord/Slack/Mattermost (plugin)/etc.)? See [Channels](/channels).

寻找聊天通道文档(WhatsApp/Telegram/Discord/Slack/Mattermost(插件)等)?参见[通道](/channels)。

## Quick start / 快速开始

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

## Provider docs / 提供者文档

- [Alibaba Model Studio](/providers/alibaba)
- [Amazon Bedrock](/providers/bedrock)
- [Amazon Bedrock Mantle](/providers/bedrock-mantle)
- [Anthropic](/providers/anthropic) (API + Claude CLI)
- [Arcee AI](/providers/arcee) (Trinity models)
- [Azure Speech](/providers/azure-speech)
- [Cerebras](/providers/cerebras)
- [Chutes](/providers/chutes)
- [Cloudflare AI Gateway](/providers/cloudflare-ai-gateway)
- [ComfyUI](/providers/comfy)
- [DeepSeek](/providers/deepseek)
- [ds4](/providers/ds4) (local DeepSeek V4)
- [ElevenLabs](/providers/elevenlabs)
- [fal](/providers/fal)
- [Fireworks](/providers/fireworks)
- [GitHub Copilot](/providers/github-copilot)
- [GMI Cloud](/providers/gmi)
- [Google (Gemini)](/providers/google)
- [Gradium](/providers/gradium)
- [Groq](/providers/groq) (LPU inference)
- [Hugging Face](/providers/huggingface) (Inference)
- [inferrs](/providers/inferrs) (local models)
- [Kilocode](/providers/kilocode)
- [LiteLLM](/providers/litellm) (unified gateway)
- [LM Studio](/providers/lmstudio) (local models)
- [MiniMax](/providers/minimax)
- [Mistral](/providers/mistral)
- [Moonshot AI](/providers/moonshot) (Kimi + Kimi Coding)
- [NVIDIA](/providers/nvidia)
- [NovitaAI](/providers/novita)
- [Ollama](/providers/ollama) (cloud + local models)
- [Ollama Cloud](/providers/ollama-cloud)
- [OpenAI](/providers/openai) (API + Codex)
- [OpenCode](/providers/opencode)
- [OpenCode Go](/providers/opencode-go)
- [OpenRouter](/providers/openrouter)
- [Perplexity](/providers/perplexity-provider) (web search)
- [Qianfan](/providers/qianfan)
- [Qwen Cloud](/providers/qwen)
- [Qwen OAuth / Portal](/providers/qwen-oauth)
- [Runway](/providers/runway)
- [SenseAudio](/providers/senseaudio)
- [SGLang](/providers/sglang) (local models)
- [StepFun](/providers/stepfun)
- [Synthetic](/providers/synthetic)
- [Tencent Cloud (TokenHub)](/providers/tencent)
- [Together AI](/providers/together)
- [Venice](/providers/venice) (Venice AI, privacy-focused)
- [Vercel AI Gateway](/providers/vercel-ai-gateway)
- [vLLM](/providers/vllm) (local models)
- [Volcengine (Doubao)](/providers/volcengine)
- [Vydra](/providers/vydra)
- [xAI](/providers/xai)
- [Xiaomi MiMo](/providers/xiaomi)
- [Z.AI](/providers/zai)

## Model configuration / 模型配置

See [Models](/providers/models) for quickstart, supported providers, and configuration patterns.

参见[模型](/providers/models)了解快速开始、支持的提供者和配置模式。

## 相关 / Related

- [Models](/providers/models) — 模型提供者快速开始和配置
- [Anthropic](/providers/anthropic) — Anthropic API 和 Claude CLI
- [OpenAI](/providers/openai) — OpenAI API 和 Codex
- [Ollama](/providers/ollama) — 云端 + 本地模型
