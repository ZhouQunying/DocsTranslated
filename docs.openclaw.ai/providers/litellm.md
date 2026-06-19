# LiteLLM (unified gateway)

## 架构精读

> 跳过不影响阅读翻译正文。

### 代理后面的代理——两层抽象叠加

LiteLLM 是另一个多提供者统一网关（类似 OpenRouter），但可以**自托管**。OpenClaw 通过 LiteLLM 路由请求，LiteLLM 再路由到实际后端。这是两层抽象叠加。

跟 OpenRouter 的区别是控制权。OpenRouter 是托管服务——你信任 OpenRouter 的路由策略、计费模型、安全实践。LiteLLM 可以自托管——你自己控制路由策略、密钥管理、日志审计。对安全敏感的企业来说，自托管的 LiteLLM 比托管的 OpenRouter 更合适。

代价是运维成本——你需要自己运行 LiteLLM proxy、配置后端 provider、管理密钥。但这是控制权的代价——更多控制意味着更多责任。

---

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
