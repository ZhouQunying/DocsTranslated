# TTS

## 架构精读

> 跳过不影响阅读翻译正文。

### 14 个语音提供者——怎么在它们之间做路由？

每个语音提供者有自己的认证方式、音频格式、计费模型、延迟特性。OpenClaw 不能简单地把所有请求丢给一个提供者——飞书要 Ogg/Opus 原生语音消息，电话要 PCM/Ulaw 流，其他平台要音频附件。

这跟 CDN 边缘节点选择是一个思路。CDN 不是把所有流量打到同一个节点，而是根据用户位置、延迟、成本在多个边缘节点间选最优路径。OpenClaw 的 TTS 路由同理：根据**目标渠道**在多个提供者间动态选择——飞书/Matrix/Telegram/WhatsApp 要原生语音消息，电话要 PCM/Ulaw 流，其他平台要音频附件。同时考虑**提供者能力**（是否支持 Opus、是否支持流式）和**认证状态**（哪个 API key 已配置）。

选定提供者后，音频经过该提供者特定的转码管道变成目标格式。ElevenLabs 返回 MP3，OpenAI 返回 Opus，Azure Speech 返回 Ogg——OpenClaw 的转码层把这些统一适配成目标渠道需要的格式。

### TTS 和 Talk 的 realtime 路径为什么分离？

TTS 是"文本转音频附件"——异步合成，结果作为文件交付。Talk 的 `realtime` 模式是"实时语音对话"——双向流式，延迟敏感。

两者共享同一个提供者注册表（14 个语音提供者），但执行路径完全不同：

- **TTS 路径**：agent 调用 `tts` 工具 → OpenClaw 调提供者 API → 等待合成完成 → 返回音频文件路径
- **Talk realtime 路径**：建立 WebSocket 长连接 → 双向流式传输 → 提供者在连接内部直接合成，不经过 TTS 工具

这意味着你可以在 Talk 用 OpenAI Realtime API（低延迟双向流），在 TTS 用 ElevenLabs（高质量异步合成）——互不干扰。架构上这是正确的分离：实时对话和异步合成有不同的 SLA 要求，硬塞到一条路径只会让两者都难受。

### 回退机制不是健康检查

配置了多个提供者时，选定的优先使用，其他作为回退。但这跟数据库连接池的主从切换不一样——**回退是按提供者注册表顺序，不是按健康检查结果**。

如果 ElevenLabs API 超时，它不会自动切到 OpenAI。只有当 ElevenLabs 完全未配置、认证失败、或显式被跳过时才会回退到下一个提供者。

这是有意为之的设计。自动健康检查回退会引入额外延迟（每次调用都要探活）和复杂性（探活失败时该等多久？重试几次？）。TTS 场景对延迟不敏感（异步合成），用户更关心"合成质量"而非"毫秒级切换"。所以 OpenClaw 的策略是：你显式选谁就用谁，选了不好使你改配置，不是 OpenClaw 替你切。

---

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
