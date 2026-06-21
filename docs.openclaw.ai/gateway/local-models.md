# Local Models

本地运行 OpenClaw 配合本地 LLM 是可行的,但对硬件、上下文管理和安全姿态要求更高。更小或大量量化的模型会增加 prompt 注入风险并截断上下文。本文面向高端本地设置和自定义 OpenAI 兼容服务器。快速入门推荐 LM Studio 或 Ollama 配合 `openclaw onboard` 命令。

> **类比:自建数据库 vs 云数据库。** 云 API (Anthropic/OpenAI) 像托管数据库——开箱即用、有完整过滤和安全。本地模型像自建数据库——完全控制但需要自己处理容量规划、安全加固、故障恢复。硬件不够时,自建数据库的性能和安全都不如托管方案。
>
> **架构要点:** 推荐硬件底线是两台满配 Mac Studio 或等价 GPU 设置(~$30k+);始终运行硬件能承受的最大全尺寸模型;支持 ds4、LM Studio、LiteLLM、MLX、vLLM、SGLang、Ollama 等 OpenAI 兼容后端;Responses API 优先(如果后端支持),否则 Chat Completions;本地模型跳过 provider-side 过滤,需要保持 agent 范围窄且 compaction 开启以限制 prompt 注入爆炸半径。

## 硬件要求

推荐底线:**至少两台满配 Mac Studio 或等价 GPU 设置,约 $30k+**,用于流畅的 agent loop。单个 24 GB GPU 只能处理轻量 prompt 且延迟增加。始终运行硬件能支持的最大全尺寸模型变体——更小或大量量化的 checkpoint 会提高安全风险。

## 支持的后端

| Backend | Best For |
|---|---|
| ds4 | macOS Metal 上的本地 DeepSeek V4 Flash,OpenAI 兼容 tool calls |
| LM Studio | 首次本地设置,GUI 加载器,原生 Responses API |
| LiteLLM / OAI-proxy / 自定义 proxy | 前端另一个 model API,但 OpenClaw 视为 OpenAI |
| MLX / vLLM / SGLang | 高吞吐自托管,OpenAI 兼容 HTTP endpoint |
| Ollama | CLI 工作流,模型库,无操作 systemd 服务 |

Responses API (`api: "openai-responses"`) 在支持时应优先使用(LM Studio 支持)。否则使用 Chat Completions (`api: "openai-completions"`)。

**WSL2 警告**: Ollama 的 Linux 安装启用 systemd 服务 (`Restart=always`),在 WSL2 GPU 设置下可能在启动时重新加载上一个模型并钉住主机内存,导致反复重启。

## LM Studio 配置

加载大模型(全尺寸 Qwen、DeepSeek 或 Llama),在 `http://127.0.0.1:1234` 启用本地 server,使用 Responses API 分离推理和最终文本。

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

关键设置:
- 下载最大可用模型(避免小或大量量化的变体)
- 启动 server 并验证 `http://127.0.0.1:1234/v1/models` 列出模型
- 用 LM Studio 实际 model ID 替换 `my-local-model`
- 保持模型加载以避免 cold-start 延迟
- WhatsApp 场景用 Responses API,确保只有最终文本被发送
- 保持 hosted models 配置 (`models.mode: "merge"`) 作为 fallback

## 混合配置

### Hosted primary + 本地 fallback

Primary 用 hosted (如 `anthropic/claude-sonnet-4-6`),fallbacks 包含本地模型和更大的 hosted 模型。本地模型在 API 限流或宕机时接管。

### 本地优先 + hosted safety net

交换 primary 和 fallback 顺序。本地模型优先,hosted 模型作为安全网。

### 区域托管 / 数据路由

Hosted MiniMax/Kimi/GLM 变体在 OpenRouter 上提供区域固定 endpoint (如 US-hosted),保持流量在你的管辖范围内。Local-only 仍是最强隐私路径。

## 其他 OpenAI 兼容本地 proxy

MLX (`mlx_lm.server`)、vLLM、SGLang、LiteLLM、OAI-proxy 或自定义 gateway,只要暴露 OpenAI-style `/v1/chat/completions` endpoint 即可。

关键行为:
- 省略 `api` 时默认 `openai-completions`
- Custom/local provider 条目的 `baseUrl` origin 被信任用于 guarded model requests (loopback、LAN、tailnet、private DNS)
- 其他 private origins 需要 `request.allowPrivateNetwork: true`
- 非秘密本地 marker 如 `apiKey: "ollama-local"` 在 `baseUrl` 解析到 loopback/private LAN 时被接受

## 兼容性

### String content 需求

某些 server 只接受 string `messages[].content`,不接受 structured content-part arrays。设置 `compat.requiresStringContent: true`。

### Tool call 文本解析

某些本地模型以独立括号文本发送 tool requests (如 `[tool_name]` + JSON + `[END_TOOL_REQUEST]`)。OpenClaw 仅在名称精确匹配已注册 tool 时提升为真正 tool call,否则作为不支持的文本处理。

### 强制 tool use

如果 tool 显示为 assistant 文本而不是运行,先验证 server 使用 tool-call-capable chat template。对于只在强制时才工作的 parser,用 per-model request override: `params.extra_body.tool_choice: "required"`。

## 故障排除

自上而下排查:

1. **确认本地模型响应**: `openclaw infer model run --local --model <provider/model> --prompt "Reply with exactly: pong"`
2. **确认 Gateway 路由**: `openclaw infer model run --gateway --model <provider/model> --prompt "..."`
3. **尝试 lean mode**: `agents.defaults.experimental.localModelLean: true` 删除三个最重 tool (`browser`、`cron`、`message`)
4. **完全禁用 tools**: `compat.supportsTools: false`
5. **上游瓶颈**: 如果 lean mode 和禁用 tools 后仍失败,问题通常是上游模型或 server 容量(context window、GPU 内存、kv-cache eviction)

安全提示: 本地模型跳过 provider-side 过滤。保持 agent 范围窄且 compaction 开启,限制 prompt 注入爆炸半径。
