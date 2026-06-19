# ElevenLabs

## 架构精读

> 跳过不影响阅读翻译正文。

### 语音合成作为 agent 工具——多模态 agent 的输出通道

ElevenLabs 提供高质量 TTS 和语音克隆。对 OpenClaw agent 来说，这不是"另一个 LLM provider"，而是**语音输出通道**。agent 可以生成文本，然后通过 ElevenLabs 把文本转为语音——实现多模态工作流（如自动播客生成、语音通知）。

---

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
