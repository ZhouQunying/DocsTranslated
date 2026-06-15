# Mistral

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
