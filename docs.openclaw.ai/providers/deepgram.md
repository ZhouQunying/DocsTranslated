# Deepgram

## 架构精读

> 跳过不影响阅读翻译正文。

### 语音输入通道——agent 的"耳朵"

Deepgram 提供高精度语音转文本（STT）和文本转语音（TTS）。如果 ElevenLabs 是 agent 的"嘴巴"（语音输出），Deepgram 就是 agent 的"耳朵"（语音输入）。对 OpenClaw agent 来说，Deepgram 实现了**语音到语音**的完整工作流——用户说话，Deepgram 转文本，agent 处理，ElevenLabs 生成回复语音。

---

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
