# Provider directory / 提供者目录

## 架构精读

> 跳过不影响阅读翻译正文。

### 多提供者抽象——为什么要"provider/model"格式？

OpenClaw 用 `provider/model` 格式统一所有 LLM 提供者。`anthropic/claude-opus-4-6` 和 `ollama/llama3.3` 在 OpenClaw 内部走同一条路由管线。

这跟数据库驱动（JDBC/ODBC）是一个思路。JDBC 用 `jdbc:mysql://host/db` 和 `jdbc:postgresql://host/db` 统一了不同数据库的连接字符串。应用代码只依赖 JDBC 接口，不直接依赖 MySQL 或 PostgreSQL 的客户端库。OpenClaw 的 `provider/model` 就是 LLM 世界的 JDBC 连接字符串。

关键设计决策是**抽象程度**。三种选择：
- **完全隐藏提供者**（如 LiteLLM）：用户只写 `gpt-4`，LiteLLM 自动选择后端。问题是用户无法利用提供者特有功能
- **完全暴露提供者**（如直接 API 调用）：用户自己处理 API 差异。问题是切换成本高
- **OpenClaw 的中间层**：用户指定提供者但接口统一。既能用提供者特有能力，又能在故障转移时跨提供者切换

代价是用户需要知道提供者名称。但这是合理的信息负担——选择哪个 LLM 是架构决策，不应该被隐藏。

### 50+ 提供者——插件注册表的网络效应

OpenClaw 支持 50+ 提供者，从 Anthropic/OpenAI 等商业 API 到 Ollama/vLLM 等本地推理引擎，再到 OpenRouter/LiteLLM 等元提供者。

这跟 Terraform 的 provider ecosystem 是一个思路。Terraform 的核心价值不是 HCL 语法，而是 provider 生态——AWS、Azure、GCP、Kubernetes 都有 provider。每个 provider 实现相同的接口（Resource/DataSource），Terraform 核心引擎不需要知道每个云的具体 API。

OpenClaw 的 provider 也是同样的模式。每个 provider 实现相同的接口（认证、模型调用、流式响应），OpenClaw 核心不需要知道 Anthropic 用 Messages API 而 Google 用 Gemini API。新增一个 provider 只需要实现接口，不需要改核心代码。

网络效应在这里起作用：provider 越多 → OpenClaw 对用户越有吸引力 → 更多用户 → provider 开发者更愿意适配 OpenClaw → provider 更多。这是平台型产品的经典飞轮。

### 两步入门——onboard 作为统一入口

所有提供者都通过 `openclaw onboard` 入门。它处理认证（API key、OAuth、IAM role）并设置默认模型。

这跟 `terraform init` 是一个思路。`terraform init` 下载 provider 插件、初始化后端状态、验证认证。用户不需要手动安装 AWS provider 或配置 S3 后端——`init` 根据配置文件自动完成。

`onboard` 的设计意图是**最小化首次使用时间**。两步：认证 + 设置默认模型。这跟 Stripe 的"5 分钟集成"理念一样——把"hello world"到"生产可用"的路径缩到最短。如果用户需要 30 分钟配置才能发第一个 API 请求，他们会放弃。

---

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
