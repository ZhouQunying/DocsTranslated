# Local Models

## 架构精读

> 跳过不影响阅读翻译正文。

### 安全姿态——为什么本地模型需要更严格的 agent 作用域？

本地模型跳过了 provider 端的内容过滤层——云端 API 提供商通常在服务端对输入输出进行安全扫描和过滤，而本地部署完全绕过了这一层。这意味着 prompt 注入攻击的爆炸半径更大：恶意输入可能直接导致模型执行非预期的工具调用或泄露敏感信息。因此需要保持 agent 的作用域尽可能窄，并且始终开启 compaction 来限制上下文中累积的潜在恶意内容。可以把本地模型想象成没有防火墙的自建数据库——完全控制但也需要自己处理所有安全防护。

### 硬件底线——为什么推荐 $30k+ 的设置？

Agent loop 对模型的上下文理解能力、推理速度和工具调用准确性要求极高。单个 24 GB GPU 只能处理轻量级 prompt 且延迟显著增加。推荐至少两台满配 Mac Studio 或等价 GPU 设置（约 $30k+）才能保证流畅的 agent 交互。始终运行硬件能支持的最大全尺寸模型。更小或大量量化的模型不仅推理能力下降，还会增加安全风险。

### API 选择——为什么 Responses API 优先于 Chat Completions？

Responses API（`api: "openai-responses"`）将推理过程和最终文本分离为不同的输出通道。这对 agent 场景至关重要：用户只应看到最终文本，推理过程应在后台处理。LM Studio 等后端已支持 Responses API，应优先使用。只有当后端不支持时才回退到 Chat Completions（`api: "openai-completions"`）。

### WSL2 陷阱——为什么 Ollama 在 WSL2 下可能反复重启？

Ollama 的 Linux 安装默认启用 systemd 服务（`Restart=always`），这意味着每次系统启动都会自动运行。在 WSL2 GPU 设置下，服务可能在启动时重新加载上一个模型并钉住主机内存。WSL2 的内存管理机制与原生 Linux 不同，大量内存占用可能导致宿主机资源紧张，进而触发反复重启循环。使用 WSL2 运行 Ollama 时需要特别注意这个兼容性问题。

### 数据主权——为什么区域固定 endpoint 很重要？

Hosted 模型变体（如 MiniMax/Kimi/GLM）在 OpenRouter 上提供区域固定的 endpoint（如 US-hosted），确保数据流量不离开指定管辖范围。对于有数据合规要求的场景，这比全球任意路由更安全。但 local-only 仍然是最强的隐私路径——数据完全不离开本地机器。

---

Running OpenClaw locally with local LLMs is feasible but demands more from hardware, context management, and security posture. Smaller or heavily quantized models increase prompt injection risk and truncate context. This document targets high-end local setups and custom OpenAI-compatible servers. For quick start, LM Studio or Ollama with the `openclaw onboard` command are recommended.

本地运行 OpenClaw 配合本地 LLM 是可行的，但对硬件、上下文管理和安全姿态要求更高。更小或大量量化的模型会增加 prompt 注入风险并截断上下文。本文面向高端本地设置和自定义 OpenAI 兼容服务器。快速入门推荐 LM Studio 或 Ollama 配合 `openclaw onboard` 命令。

## 硬件要求

Hardware Requirements

推荐底线：**至少两台满配 Mac Studio 或等价 GPU 设置，约 $30k+**，用于流畅的 agent loop。单个 24 GB GPU 只能处理轻量 prompt 且延迟增加。始终运行硬件能支持的最大全尺寸模型变体——更小或大量量化的 checkpoint 会提高安全风险。

Recommended baseline: **at least two fully-loaded Mac Studios or equivalent GPU setup, approximately $30k+**, for smooth agent loop operation. A single 24 GB GPU can only handle lightweight prompts with increased latency. Always run the largest full-size model variant your hardware can support — smaller or heavily quantized checkpoints increase security risks.

## 支持的后端

Supported Backends

| Backend | Best For |
|---|---|
| ds4 | macOS Metal 上的本地 DeepSeek V4 Flash，OpenAI 兼容 tool calls |
| LM Studio | 首次本地设置，GUI 加载器，原生 Responses API |
| LiteLLM / OAI-proxy / 自定义 proxy | 前端另一个 model API，但 OpenClaw 视为 OpenAI |
| MLX / vLLM / SGLang | 高吞吐自托管，OpenAI 兼容 HTTP endpoint |
| Ollama | CLI 工作流，模型库，无操作 systemd 服务 |

Responses API（`api: "openai-responses"`）在支持时应优先使用（LM Studio 支持）。否则使用 Chat Completions（`api: "openai-completions"`）。

Responses API (`api: "openai-responses"`) should be preferred when supported (LM Studio supports it). Otherwise use Chat Completions (`api: "openai-completions"`).

**WSL2 警告**：Ollama 的 Linux 安装启用 systemd 服务（`Restart=always`），在 WSL2 GPU 设置下可能在启动时重新加载上一个模型并钉住主机内存，导致反复重启。

**WSL2 Warning**: Ollama's Linux installation enables a systemd service (`Restart=always`), which on WSL2 GPU setups may reload the previous model on boot and pin host memory, causing repeated restarts.

## LM Studio 配置

LM Studio Configuration

加载大模型（全尺寸 Qwen、DeepSeek 或 Llama），在 `http://127.0.0.1:1234` 启用本地 server，使用 Responses API 分离推理和最终文本。

Load a large model (full-size Qwen, DeepSeek, or Llama), enable the local server at `http://127.0.0.1:1234`, and use the Responses API to separate reasoning from final text.

```json5
{
  agents: {
    defaults: {
      model: { primary: "lmstudio/my-local-model" }
    }
  },
  models: {
    mode: "merge",
    providers: {
      lmstudio: {
        baseUrl: "http://127.0.0.1:1234/v1",
        apiKey: "lmstudio",
        api: "openai-responses",
        models: [{
          id: "my-local-model",
          reasoning: false,
          input: ["text"],
          cost: { input: 0, output: 0, cacheRead: 0, cacheWrite: 0 },
          contextWindow: 196608, maxTokens: 8192
        }]
      }
    }
  }
}
```

关键设置：

Key settings:

- 下载最大可用模型（避免小或大量量化的变体）
- 启动 server 并验证 `http://127.0.0.1:1234/v1/models` 列出模型
- 用 LM Studio 实际 model ID 替换 `my-local-model`
- 保持模型加载以避免 cold-start 延迟
- WhatsApp 场景用 Responses API，确保只有最终文本被发送
- 保持 hosted models 配置（`models.mode: "merge"`）作为 fallback

- Download the largest available model (avoid small or heavily quantized variants)
- Start the server and verify `http://127.0.0.1:1234/v1/models` lists the model
- Replace `my-local-model` with the actual LM Studio model ID
- Keep the model loaded to avoid cold-start latency
- Use the Responses API for WhatsApp scenarios to ensure only final text is sent
- Keep hosted models configuration (`models.mode: "merge"`) as fallback

## 混合配置

Hybrid Configurations

### Hosted primary + 本地 fallback

Hosted Primary + Local Fallback

Primary 用 hosted（如 `anthropic/claude-sonnet-4-6`），fallbacks 包含本地模型和更大的 hosted 模型。本地模型在 API 限流或宕机时接管。

Use a hosted model as primary (e.g., `anthropic/claude-sonnet-4-6`), with fallbacks including a local model and larger hosted models. The local model takes over when the API is rate-limited or down.

### 本地优先 + hosted safety net

Local Primary + Hosted Safety Net

交换 primary 和 fallback 顺序。本地模型优先，hosted 模型作为安全网。

Swap the order of primary and fallback. The local model is used first, with hosted models as a safety net.

### 区域托管 / 数据路由

Regional Hosting / Data Routing

Hosted MiniMax/Kimi/GLM 变体在 OpenRouter 上提供区域固定 endpoint（如 US-hosted），保持流量在你的管辖范围内。Local-only 仍是最强隐私路径。

Hosted MiniMax/Kimi/GLM variants on OpenRouter offer region-pinned endpoints (e.g., US-hosted), keeping traffic within your jurisdiction. Local-only remains the strongest privacy path.

## 其他 OpenAI 兼容本地 proxy

Other OpenAI-Compatible Local Proxies

MLX（`mlx_lm.server`）、vLLM、SGLang、LiteLLM、OAI-proxy 或自定义 gateway，只要暴露 OpenAI-style `/v1/chat/completions` endpoint 即可。

MLX (`mlx_lm.server`), vLLM, SGLang, LiteLLM, OAI-proxy, or custom gateways work as long as they expose an OpenAI-style `/v1/chat/completions` endpoint.

关键行为：

Key behaviors:

- 省略 `api` 时默认 `openai-completions`
- Custom/local provider 条目的 `baseUrl` origin 被信任用于 guarded model requests（loopback、LAN、tailnet、private DNS）
- 其他 private origins 需要 `request.allowPrivateNetwork: true`
- 非秘密本地 marker 如 `apiKey: "ollama-local"` 在 `baseUrl` 解析到 loopback/private LAN 时被接受

- Defaults to `openai-completions` when `api` is omitted
- Custom/local provider entries' `baseUrl` origin is trusted for guarded model requests (loopback, LAN, tailnet, private DNS)
- Other private origins require `request.allowPrivateNetwork: true`
- Non-secret local markers like `apiKey: "ollama-local"` are accepted when `baseUrl` resolves to loopback/private LAN

## 兼容性

Compatibility

### String content 需求

String Content Requirement

某些 server 只接受 string `messages[].content`，不接受 structured content-part arrays。设置 `compat.requiresStringContent: true`。

Some servers only accept string `messages[].content`, not structured content-part arrays. Set `compat.requiresStringContent: true`.

### Tool call 文本解析

Tool Call Text Parsing

某些本地模型以独立括号文本发送 tool requests（如 `[tool_name]` + JSON + `[END_TOOL_REQUEST]`）。OpenClaw 仅在名称精确匹配已注册 tool 时提升为真正 tool call，否则作为不支持的文本处理。

Some local models send tool requests as standalone bracketed text (e.g., `[tool_name]` + JSON + `[END_TOOL_REQUEST]`). OpenClaw only promotes these to real tool calls when the name exactly matches a registered tool; otherwise they are treated as unsupported text.

### 强制 tool use

Forced Tool Use

如果 tool 显示为 assistant 文本而不是运行，先验证 server 使用 tool-call-capable chat template。对于只在强制时才工作的 parser，用 per-model request override：`params.extra_body.tool_choice: "required"`。

If tools appear as assistant text rather than being executed, first verify the server uses a tool-call-capable chat template. For parsers that only work when forced, use a per-model request override: `params.extra_body.tool_choice: "required"`.

## 故障排除

Troubleshooting

自上而下排查：

Diagnose top-down:

1. **确认本地模型响应**：`openclaw infer model run --local --model <provider/model> --prompt "Reply with exactly: pong"`
2. **确认 Gateway 路由**：`openclaw infer model run --gateway --model <provider/model> --prompt "..."`
3. **尝试 lean mode**：`agents.defaults.experimental.localModelLean: true` 删除三个最重 tool（`browser`、`cron`、`message`）
4. **完全禁用 tools**：`compat.supportsTools: false`
5. **上游瓶颈**：如果 lean mode 和禁用 tools 后仍失败，问题通常是上游模型或 server 容量（context window、GPU 内存、kv-cache eviction）

1. **Confirm local model responds**: `openclaw infer model run --local --model <provider/model> --prompt "Reply with exactly: pong"`
2. **Confirm Gateway routing**: `openclaw infer model run --gateway --model <provider/model> --prompt "..."`
3. **Try lean mode**: `agents.defaults.experimental.localModelLean: true` removes the three heaviest tools (`browser`, `cron`, `message`)
4. **Disable tools entirely**: `compat.supportsTools: false`
5. **Upstream bottleneck**: If still failing after lean mode and disabling tools, the issue is usually upstream model or server capacity (context window, GPU memory, kv-cache eviction)

安全提示：本地模型跳过 provider-side 过滤。保持 agent 作用域窄且 compaction 开启，限制 prompt 注入爆炸半径。

Security note: Local models bypass provider-side filtering. Keep agent scope narrow and compaction enabled to limit the prompt injection blast radius.
