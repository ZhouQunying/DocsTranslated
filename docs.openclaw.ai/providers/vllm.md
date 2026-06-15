# vLLM (本地模型)

vLLM (本地模型)

vLLM 提供带 OpenAI 兼容 API 的高吞吐本地模型服务。

## Getting started / 入门

```bash
export VLLM_API_KEY="..."
openclaw onboard
# Choose "vLLM (本地模型)"
```

## Configuration / 配置

```json5
{
  agents: {
    defaults: {
      model: {
        primary: "vllm/model-name"
      }
    }
  }
}
```

## Model routing / 模型路由

OpenClaw routes `vllm/*` models through the vLLM (本地模型) API.

OpenClaw 通过 vLLM (本地模型) API 路由 `vllm/*` 模型。

## Related / 相关

- [Provider directory](/providers) — 所有提供者列表
- [Models](/providers/models) — 模型配置
