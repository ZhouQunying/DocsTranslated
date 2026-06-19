# SenseAudio

## 架构精读

> 跳过不影响阅读翻译正文。

### 音频处理——超越语音的音频能力

SenseAudio 提供语音和音频处理能力。跟 Deepgram（专注语音转文本）和 ElevenLabs（专注文本转语音）不同，SenseAudio 覆盖更广泛的音频处理场景——包括音频增强、降噪、分离等。对 OpenClaw agent 来说，这是**通用音频处理**的工具层。

---

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
