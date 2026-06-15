# SenseAudio

SenseAudio

SenseAudio 提供语音和音频处理。

## Getting started / 入门

```bash
export SENSEAUDIO_API_KEY="..."
openclaw onboard
# Choose "SenseAudio"
```

## Configuration / 配置

```json5
{
  agents: {
    defaults: {
      model: {
        primary: "senseaudio/model-name"
      }
    }
  }
}
```

## Model routing / 模型路由

OpenClaw routes `senseaudio/*` models through the SenseAudio API.

OpenClaw 通过 SenseAudio API 路由 `senseaudio/*` 模型。

## Related / 相关

- [Provider directory](/providers) — 所有提供者列表
- [Models](/providers/models) — 模型配置
