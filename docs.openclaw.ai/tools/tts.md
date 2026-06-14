# TTS

OpenClaw 可将出站回复转换为音频，支持 **14 个语音提供者**，并在飞书、Matrix、Telegram 和 WhatsApp 上交付原生语音消息，在其他平台上交付音频附件，为电话和 Talk 提供 PCM/Ulaw 流。

TTS 是 Talk 的 `stt-tts` 模式的语音输出部分。提供者原生的 `realtime` Talk 会话在实时提供者内部合成语音而不调用此 TTS 路径，`transcription` 会话则不合成助手语音响应。

## 快速开始

1. **选择提供者**：OpenAI 和 ElevenLabs 是最可靠的托管选项。Microsoft 和 Local CLI 无需 API 密钥。参见[提供者矩阵](#支持的提供者)获取完整列表
2. **设置 API 密钥**：导出提供者的环境变量（如 `OPENAI_API_KEY`、`ELEVENLABS_API_KEY`）。Microsoft 和 Local CLI 不需要密钥
3. **在配置中启用**：设置 `messages.tts.auto: "always"` 和 `messages.tts.provider`：

```json5
{
  messages: {
    tts: {
      auto: "always",
      provider: "elevenlabs",
    },
  },
}
```

4. **在聊天中试用**：`/tts status` 显示当前状态。`/tts audio Hello from OpenClaw` 发送一次性音频回复。

Auto-TTS 默认**关闭**。当 `messages.tts.provider` 未设置时，OpenClaw 按注册表自动选择顺序选择第一个已配置的提供者。内置 `tts` agent 工具仅限显式意图：除非用户请求音频、使用 `/tts` 或启用 Auto-TTS/指令语音，普通聊天保持文本。

## 支持的提供者

| 提供者 | 认证 | 说明 |
| --- | --- | --- |
| **Azure Speech** | `AZURE_SPEECH_KEY` + `AZURE_SPEECH_REGION` | 原生 Ogg/Opus 语音消息输出和电话 |
| **DeepInfra** | `DEEPINFRA_API_KEY` | 兼容 OpenAI 的 TTS。默认 `hexgrad/Kokoro-82M` |
| **ElevenLabs** | `ELEVENLABS_API_KEY` 或 `XI_API_KEY` | 语音克隆、多语言、通过 `seed` 确定性；流式用于 Discord 语音播放 |
| **Google Gemini** | `GEMINI_API_KEY` 或 `GOOGLE_API_KEY` | Gemini API 批量 TTS；通过 `promptTemplate: "audio-profile-v1"` 感知人设 |
| **Gradium** | `GRADIUM_API_KEY` | 语音消息和电话输出 |
| **Inworld** | `INWORLD_API_KEY` | 流式 TTS API。原生 Opus 语音消息和 PCM 电话 |
| **Local CLI** | 无 | 运行配置的本地 TTS 命令 |
| **Microsoft** | 无 | 通过 `node-edge-tts` 的公共 Edge 神经 TTS。尽力而为，无 SLA |
| **MiniMax** | `MINIMAX_API_KEY` | T2A v2 API。默认 `speech-2.8-hd` |
| **OpenAI** | `OPENAI_API_KEY` | 也用于自动摘要；支持人设 `instructions` |
| **OpenRouter** | `OPENROUTER_API_KEY` | 默认模型 `hexgrad/kokoro-82m` |
| **Volcengine** | `VOLCENGINE_TTS_API_KEY` | BytePlus Seed Speech HTTP API |
| **Vydra** | `VYDRA_API_KEY` | 共享图像、视频和语音提供者 |
| **xAI** | `XAI_API_KEY` | xAI 批量 TTS。**不**支持原生 Opus 语音消息 |
| **Xiaomi MiMo** | `XIAOMI_API_KEY` | 通过 Xiaomi 聊天补全的 MiMo TTS |

如配置了多个提供者，选定的优先使用，其他作为回退选项。自动摘要使用 `summaryModel`（或 `agents.defaults.model.primary`），因此如保持摘要启用，该提供者也必须经过认证。

捆绑的 **Microsoft** 提供者通过 `node-edge-tts` 使用 Microsoft Edge 在线神经 TTS 服务。它是没有已发布 SLA 或配额的公共网络服务——视为尽力而为。旧版提供者 id `edge` 被规范化为 `microsoft`，`openclaw doctor --fix` 重写持久化配置；新配置应始终使用 `microsoft`。

## 配置

TTS 配置位于 `~/.openclaw/openclaw.json` 的 `messages.tts` 下。选择一个预设并根据需要调整提供者块：

```json5
{
  messages: {
    tts: {
      auto: "always",
      provider: "elevenlabs",
      providers: {
        elevenlabs: {
          apiKey: "${ELEVENLABS_API_KEY}",
          model: "eleven_multilingual_v2",
          speakerVoiceId: "EXAVITQu4vr4xnSDxMaL",
        },
      },
    },
  },
}
```

每个提供者有自己的配置字段（`apiKey`、`model`、`speakerVoice`/`speakerVoiceId`、`lang`、`outputFormat` 等）。参见各提供者文档获取详细参数。

## 相关

- [Talk](/tools/talk)——实时语音对话
- [配置参考](/gateway/configuration-reference)——完整 `messages.tts` 模式
