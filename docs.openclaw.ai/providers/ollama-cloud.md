# Ollama Cloud

Ollama Cloud

Ollama Cloud 提供托管 Ollama 模型,无需本地服务器。

## Getting started / 入门

```bash
export OLLAMA_API_KEY="..."
openclaw onboard
# Choose "Ollama Cloud"
```

## Configuration / 配置

```json5
{
  agents: {
    defaults: {
      model: {
        primary: "ollama-cloud/model-name"
      }
    }
  }
}
```

## Model routing / 模型路由

OpenClaw routes `ollama-cloud/*` models through the Ollama Cloud API.

OpenClaw 通过 Ollama Cloud API 路由 `ollama-cloud/*` 模型。

## Related / 相关

- [Provider directory](/providers) — 所有提供者列表
- [Models](/providers/models) — 模型配置
