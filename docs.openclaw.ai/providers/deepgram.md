# Deepgram

Deepgram

Deepgram 提供高精度语音转文本和文本转语音。

## Getting started / 入门

```bash
export DEEPGRAM_API_KEY="..."
openclaw onboard
# Choose "Deepgram"
```

## Configuration / 配置

```json5
{
  agents: {
    defaults: {
      model: {
        primary: "deepgram/model-name"
      }
    }
  }
}
```

## Model routing / 模型路由

OpenClaw routes `deepgram/*` models through the Deepgram API.

OpenClaw 通过 Deepgram API 路由 `deepgram/*` 模型。

## Related / 相关

- [Provider directory](/providers) — 所有提供者列表
- [Models](/providers/models) — 模型配置
