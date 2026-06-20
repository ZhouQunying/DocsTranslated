# Ollama Cloud

## 架构精读

> 跳过不影响阅读翻译正文。

### Ollama 的托管层——从本地工具到云服务

Ollama Cloud 把 Ollama 从本地工具变成了托管服务。这跟 Docker Hub 把 Docker 从本地工具变成云端 registry 是一个思路。对 OpenClaw agent 来说，`ollama-cloud/*` 前缀提供了跟本地 `ollama/*` 相同的模型，但不需要自己运行 Ollama 服务器。

---

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
