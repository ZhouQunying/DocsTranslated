# ElevenLabs

ElevenLabs

ElevenLabs 提供高质量文本转语音和语音克隆。

## Getting started / 入门

```bash
export ELEVENLABS_API_KEY="..."
openclaw onboard
# Choose "ElevenLabs"
```

## Configuration / 配置

```json5
{
  agents: {
    defaults: {
      model: {
        primary: "elevenlabs/model-name"
      }
    }
  }
}
```

## Model routing / 模型路由

OpenClaw routes `elevenlabs/*` models through the ElevenLabs API.

OpenClaw 通过 ElevenLabs API 路由 `elevenlabs/*` 模型。

## Related / 相关

- [Provider directory](/providers) — 所有提供者列表
- [Models](/providers/models) — 模型配置
