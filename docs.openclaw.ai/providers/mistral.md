# Mistral

## 架构精读

> 跳过不影响阅读翻译正文。

### 开放权重 + 商业 + 多模态——一个 provider 三种模式

Mistral 同时提供开放权重模型（可自托管）和商业 API 模型，还通过 Voxtral 提供音频转录。这跟 Meta 的 Llama 策略是一个思路——用开放权重建立生态，用商业模型变现。

对 OpenClaw agent 来说，Mistral 的独特价值是**灵活部署**。同一个 `mistral/*` 前缀可以指向 Mistral 的 API（商业模型），也可以指向自托管的 Mistral 开源模型（通过 vLLM/Ollama）。这让 agent 在开发和生产之间无缝切换——开发时用 API 快速迭代，生产时自托管降低成本。

---

Mistral provides high-performance open-weight and commercial models through its API.

Mistral 通过其 API 提供高性能开放权重和商业模型。

## Getting started / 入门

```bash
export MISTRAL_API_KEY="..."
openclaw onboard
# Choose "Mistral"
```

## Configuration / 配置

```json5
{
  agents: {
    defaults: {
      model: {
        primary: "mistral/mistral-large-latest"
      }
    }
  }
}
```

## Audio transcription (Voxtral) / 音频转录

Mistral also provides audio transcription via Voxtral models. See the [Mistral docs](https://docs.mistral.ai/) for details.

Mistral 还通过 Voxtral 模型提供音频转录。详情参见 [Mistral 文档](https://docs.mistral.ai/)。

## Model routing / 模型路由

OpenClaw routes `mistral/*` models through the Mistral API.

OpenClaw 通过 Mistral API 路由 `mistral/*` 模型。

## Related / 相关

- [Provider directory](/providers) — 所有提供者列表
- [Models](/providers/models) — 模型配置
