# LiteLLM (unified gateway)

LiteLLM provides a unified proxy/gateway that routes requests to 100+ LLM providers using an OpenAI-compatible API format.

LiteLLM 提供统一的代理/网关,使用 OpenAI 兼容的 API 格式将请求路由到 100+ LLM 提供者。

## Getting started / 入门

### Self-hosted LiteLLM proxy / 自托管 LiteLLM 代理

```bash
# Start LiteLLM proxy
litellm --model gpt-4 --port 8000

# Configure OpenClaw
export LITELLM_BASE_URL="http://localhost:8000"
export LITELLM_API_KEY="sk-..."
openclaw onboard
# Choose "LiteLLM"
```

### LiteLLM Cloud / LiteLLM 云端

```bash
export LITELLM_API_KEY="..."
openclaw onboard
# Choose "LiteLLM"
```

## Configuration / 配置

```json5
{
  agents: {
    defaults: {
      model: {
        primary: "litellm/gpt-4"
      }
    }
  }
}
```

## Model routing / 模型路由

OpenClaw routes `litellm/*` models through the LiteLLM proxy. The proxy then routes to the configured backend provider.

OpenClaw 通过 LiteLLM 代理路由 `litellm/*` 模型。代理然后路由到配置的后端提供者。

## Related / 相关

- [Provider directory](/providers) — 所有提供者列表
- [Models](/providers/models) — 模型配置
