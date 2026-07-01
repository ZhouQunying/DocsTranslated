# Text-to-Speech (TTS)

## 架构精读

> 跳过不影响阅读翻译正文。

### 多 Provider 架构——为什么需要 14 个提供商？

OpenClaw TTS 支持 14 个 speech provider（OpenAI、ElevenLabs、Azure、Google Gemini、Microsoft、Local CLI 等），配置在 `messages.tts` 下，`auto: "always"` 启用自动 TTS。

这跟浏览器的 SpeechSynthesis API 是一个思路——`speechSynthesis.speak()` 把文本转为语音，使用系统 TTS 引擎。OpenClaw TTS 类似但更强大：多 provider（而非单 provider）、自动选择最佳 provider、per-智能体 voice 覆盖、personas（稳定的语音身份）、model-driven 指令动态切换 voice/model/speed。

### Per-智能体覆盖——为什么需要智能体级别定制？

当一个智能体需要不同的 provider、voice、model 或 persona 时，使用 `agents.list[].tts`。智能体配置 deep-merge 覆盖 `messages.tts`。

这跟 CSS 的层叠是一个思路——全局样式（`messages.tts`）→ 组件样式（`agents.list[].tts`）→ 内联样式（`[[tts:...]]` 指令），越具体优先级越高。Per-智能体覆盖让"全局统一 + 智能体个性化"成为可能。

### Personas——为什么需要"稳定的语音身份"？

Persona 是跨 provider 确定性地应用的稳定语音身份，携带 provider-specific bindings（voices、models、seeds、voice settings）。Fallback 策略（回退策略）控制失败时的行为：`preserve-persona`（保留 persona）、`provider-defaults`（省略 persona）、`fail`（跳过 provider）。

这跟 OAuth 的"身份提供者"是一个思路——你在 Google 登录后，无论访问哪个应用，身份都是同一个。Persona 让"语音身份"跨 provider 一致，避免"切换 provider 后声音变了"的体验断裂。

### 输出格式——为什么按通道能力区分？

TTS 输出格式由通道能力驱动：Feishu/Matrix/Telegram/WhatsApp 用 Opus voice-notes（48 kHz / 64 kbps），其他通道用 MP3（44.1 kHz / 128 kbps），Talk/电话用 Provider-native PCM 或 ulaw_8000。Feishu 和 WhatsApp 在需要时用 `ffmpeg` 把非 Opus 输出转码为 48 kHz Ogg/Opus。

这跟 HTTP 的内容协商（Content Negotiation）是一个思路——浏览器发送 `Accept: image/webp`，服务器返回 WebP；发送 `Accept: image/jpeg`，服务器返回 JPEG。按通道能力区分让"每个通道收到它支持的最佳格式"，避免"统一格式导致某些通道无法播放"。

---

Text-to-Speech tool converting outbound replies to audio across 14 speech providers (OpenAI, ElevenLabs, Azure Speech, Google Gemini, Microsoft, Local CLI, etc.). Config under `messages.tts` with `auto: "always"` enabling auto-TTS. Per-agent voice overrides via `agents.list[].tts` deep-merge. Personas provide stable spoken identity across providers with provider-specific bindings. Model-driven directives `[[tts:...]]` allow dynamic voice/model/speed overrides per reply. Output formats by channel capability: Opus voice-notes for Feishu/Matrix/Telegram/WhatsApp, MP3 for others, PCM/ulaw for Talk/telephony. Slash commands (`/tts on|off|status|audio|provider|persona`) and gateway RPC methods (`tts.status|enable|disable|convert|setProvider|setPersona|providers`). Auto-TTS flow checks reply length, summary threshold, and channel capability before attaching audio.

文本转语音工具，跨 14 个 speech provider（OpenAI、ElevenLabs、Azure Speech、Google Gemini、Microsoft、Local CLI 等）将出站回复转换为音频。配置在 `messages.tts` 下，`auto: "always"` 启用自动 TTS。Per-智能体覆盖通过 `agents.list[].tts` deep-merge。Personas 提供跨 provider 的稳定语音身份，携带 provider-specific bindings。Model-driven 指令 `[[tts:...]]` 允许每次回复的动态语音/模型/速度覆盖。输出格式按通道能力区分：Feishu/Matrix/Telegram/WhatsApp 用 Opus voice-notes，其他用 MP3，Talk/电话用 PCM/ulaw。斜杠命令（`/tts on|off|status|audio|provider|persona`）和网关 RPC 方法（`tts.status|enable|disable|convert|setProvider|setPersona|providers`）。自动 TTS 流程在附加音频前检查回复长度、摘要阈值和通道能力。
