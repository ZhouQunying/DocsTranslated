# Text-to-Speech (TTS)

OpenClaw 把出站回复转换为音频,跨越十四个 speech providers,在 Feishu、Matrix、Telegram、WhatsApp 上传递原生语音消息,其他 channels 传递音频附件,电话和 Talk 传递 PCM/Ulaw 流。TTS 作为 Talk 的 `stt-tts` mode 的语音输出组件。Provider-native realtime sessions 内部合成语音,而不是通过此 TTS 路径。

> **类比:浏览器的 SpeechSynthesis API + 多 provider 后端。** 浏览器里 `speechSynthesis.speak()` 把文本转为语音,使用系统 TTS engine。OpenClaw TTS 类似但更强大: 支持 14 个 providers (OpenAI、ElevenLabs、Azure、Google Gemini 等),自动选择最佳 provider,支持 per-agent voice overrides,支持 personas (稳定的 spoken identity),支持 model-driven directives 动态切换 voice/model/speed。区别: 浏览器 TTS 是单 provider,OpenClaw 是多 provider + fallback + 个性化。
>
> **架构要点:** 14 个 providers 支持,包括 OpenAI、ElevenLabs、Azure Speech、Google Gemini、Microsoft (免费无 key)、Local CLI 等;config 在 `messages.tts` 下,`auto: "always"` 启用自动 TTS;per-agent voice overrides 经 `agents.list[].tts` deep-merge 覆盖;personas 是稳定的 spoken identity,跨 provider 携带 provider-specific bindings;model-driven directives `[[tts:...]]` 允许 assistant 动态覆盖单次回复的 voice/model/speed;output format 按 channel capability: Feishu/Matrix/Telegram/WhatsApp 用 Opus voice-notes,其他用 MP3,Talk/telephony 用 PCM/ulaw。

## Quick Start

1. **选择 provider** — OpenAI 和 ElevenLabs 是最可靠的托管选项;Microsoft 和 Local CLI 无需 API keys
2. **设置 API key** — 导出相关 env var (如 `OPENAI_API_KEY`、`ELEVENLABS_API_KEY`)
3. **在 config 中启用** — 设置 `messages.tts.auto: "always"` 和 `messages.tts.provider`
4. **在 chat 中尝试** — `/tts status` 显示当前状态;`/tts audio Hello from OpenClaw` 发送一次性音频回复

> Auto-TTS 默认关闭。`messages.tts.provider` 未设置时,OpenClaw 在 registry auto-select 顺序中选择第一个配置的 provider。

## 支持的 Providers

| Provider | Auth | 备注 |
|----------|------|-------|
| Azure Speech | `AZURE_SPEECH_KEY` + `AZURE_SPEECH_REGION` | 原生 Ogg/Opus voice-note 和电话 |
| DeepInfra | `DEEPINFRA_API_KEY` | OpenAI-compatible;默认 `hexgrad/Kokoro-82M` |
| ElevenLabs | `ELEVENLABS_API_KEY` 或 `XI_API_KEY` | Voice cloning,多语言,seed 确定性 |
| Google Gemini | `GEMINI_API_KEY` 或 `GOOGLE_API_KEY` | Batch TTS;经 promptTemplate 感知 persona |
| Gradium | `GRADIUM_API_KEY` | Voice-note 和电话 |
| Inworld | `INWORLD_API_KEY` | Streaming TTS;原生 Opus voice-note |
| Local CLI | 无 | 运行配置的本地 TTS 命令 |
| Microsoft | 无 | 经 node-edge-tts 的公共 Edge neural TTS;best-effort |
| MiniMax | `MINIMAX_API_KEY` (或 Token Plan 变体) | T2A v2 API;默认 `speech-2.8-hd` |
| OpenAI | `OPENAI_API_KEY` | 也用于 auto-summary |
| OpenRouter | `OPENROUTER_API_KEY` | 默认 model `hexgrad/kokoro-82m` |
| Volcengine | `VOLCENGINE_TTS_API_KEY` 或 legacy AppID/token | BytePlus Seed Speech HTTP API |
| Vydra | `VYDRA_API_KEY` | 共享 image、video、speech provider |
| xAI | `XAI_API_KEY` | Batch TTS;无原生 Opus voice-note 支持 |
| Xiaomi MiMo | `XIAOMI_API_KEY` | 经 Xiaomi chat completions 的 MiMo TTS |

> Bundled Microsoft provider 使用 Edge 的在线 neural TTS service — 无发布 SLA 的公共 web service。

## Configuration 示例

Config 在 `~/.openclaw/openclaw.json` 的 `messages.tts` 下。以下是代表性示例:

### ElevenLabs
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
          speakerVoiceId: "EXAVITQu4vr4xnSDxMaL"
        }
      }
    }
  }
}
```

### OpenAI + ElevenLabs (带 Fallback)
```json5
{
  messages: {
    tts: {
      auto: "always",
      provider: "openai",
      summaryModel: "openai/gpt-4.1-mini",
      modelOverrides: { enabled: true },
      providers: {
        openai: {
          apiKey: "${OPENAI_API_KEY}",
          model: "gpt-4o-mini-tts",
          speakerVoice: "alloy"
        },
        elevenlabs: {
          apiKey: "${ELEVENLABS_API_KEY}",
          model: "eleven_multilingual_v2",
          speakerVoiceId: "EXAVITQu4vr4xnSDxMaL",
          voiceSettings: { stability: 0.5, similarityBoost: 0.75, style: 0.0, useSpeakerBoost: true, speed: 1.0 }
        }
      }
    }
  }
}
```

### Microsoft (无需 Key)
```json5
{
  messages: {
    tts: {
      auto: "always",
      provider: "microsoft",
      providers: {
        microsoft: {
          enabled: true,
          speakerVoice: "en-US-MichelleNeural",
          lang: "en-US",
          outputFormat: "audio-24khz-48kbitrate-mono-mp3"
        }
      }
    }
  }
}
```

其他 provider 示例 (Azure Speech、Google Gemini、Gradium、Inworld、Local CLI、MiniMax、OpenRouter、Volcengine、xAI、Xiaomi MiMo) 遵循相同的结构模式,带有 provider-specific 字段。

## Per-Agent Voice Overrides

当一个 agent 需要不同的 provider、voice、model 或 persona 时,使用 `agents.list[].tts`。Agent block deep-merge 覆盖 `messages.tts`:

```json5
{
  agents: {
    list: [
      {
        id: "reader",
        tts: {
          providers: {
            elevenlabs: { speakerVoiceId: "EXAVITQu4vr4xnSDxMaL" }
          }
        }
      }
    ]
  }
}
```

TTS 设置的优先级顺序:

1. `messages.tts`
2. 活跃的 `agents.list[].tts`
3. Channel override
4. Account override
5. 本地 `/tts` preferences
6. Model overrides 启用时的 inline `[[tts:...]]` directives

## Personas

Persona 是跨 providers 确定性地应用的稳定 spoken identity,携带 provider-specific bindings 用于 voices、models、seeds、voice settings。

### 最小 Persona
```json5
{
  messages: {
    tts: {
      persona: "narrator",
      personas: {
        narrator: {
          label: "Narrator",
          provider: "elevenlabs",
          providers: {
            elevenlabs: {
              speakerVoiceId: "EXAVITQu4vr4xnSDxMaL",
              modelId: "eleven_multilingual_v2"
            }
          }
        }
      }
    }
  }
}
```

### 完整 Persona (Provider-Neutral Prompt)
```json5
{
  messages: {
    tts: {
      persona: "alfred",
      personas: {
        alfred: {
          label: "Alfred",
          description: "Dry, warm British butler narrator.",
          provider: "google",
          fallbackPolicy: "preserve-persona",
          prompt: {
            profile: "A brilliant British butler. Dry, witty, warm.",
            scene: "A quiet late-night study.",
            style: "Refined, understated, lightly amused.",
            accent: "British English.",
            pacing: "Measured, with short dramatic pauses."
          },
          providers: {
            google: {
              model: "gemini-3.1-flash-tts-preview",
              speakerVoice: "Algieba",
              promptTemplate: "audio-profile-v1"
            },
            openai: { model: "gpt-4o-mini-tts", speakerVoice: "cedar" },
            elevenlabs: {
              speakerVoiceId: "voice_id",
              seed: 42,
              voiceSettings: { stability: 0.65, similarityBoost: 0.8 }
            }
          }
        }
      }
    }
  }
}
```

### Persona 解析
1. `/tts persona <id>` 本地 preference
2. `messages.tts.persona`
3. 无 persona

### Fallback Policy

| Policy | 行为 |
|--------|------|
| `preserve-persona` | 默认;prompt 字段保持可用 |
| `provider-defaults` | 该尝试省略 persona |
| `fail` | 用 `reasonCode: "not_configured"` 跳过 provider |

## Model-Driven Directives

Assistant 可发出 `[[tts:...]]` directives 为单次回复覆盖 voice、model 或 speed:

```text
[[tts:speakerVoiceId=pMsXgVXv3BLzUgSXRplE model=eleven_v3 speed=1.1]]
[[tts:text]](laughs) Read the song once more.[[/tts:text]]
```

可用的 directive keys 包括: `provider`、`speakerVoice`/`speakerVoiceId`、`model`、`stability`、`similarityBoost`、`style`、`speed`、`useSpeakerBoost`、`vol`/`volume`、`pitch`、`emotion`、`applyTextNormalization`、`languageCode`、`seed`。

禁用:
```json5
{ messages: { tts: { modelOverrides: { enabled: false } } } }
```

## Slash Commands

```text
/tts off | on | status
/tts chat on | off | default
/tts latest
/tts provider <id>
/tts persona <id> | off
/tts limit <chars>
/tts summary off
/tts audio <text>
```

关键行为:
- `/tts on` 把本地 preference 写入 `always`;`/tts off` 写入 `off`
- `/tts latest` 读取最新的 assistant 回复并一次性作为音频发送
- `/tts audio` 生成一次性音频回复,不切换 TTS on
- `/tts status` 包含最新尝试的 fallback diagnostics

## Per-User Preferences

Slash commands 把 overrides 写入 `prefsPath` (默认 `~/.openclaw/settings/tts.json`):

| 字段 | 效果 |
|------|------|
| `auto` | 本地 auto-TTS override |
| `provider` | 本地主要 provider override |
| `persona` | 本地 persona override |
| `maxLength` | Summary 阈值 (默认 1500 chars) |
| `summarize` | Summary toggle (默认 true) |

## Output Formats

TTS 传递由 channel-capability 驱动:

| 目标 | Format |
|------|--------|
| Feishu / Matrix / Telegram / WhatsApp | Opus voice-notes (48 kHz / 64 kbps) |
| 其他 channels | MP3 (44.1 kHz / 128 kbps) |
| Talk / 电话 | Provider-native PCM 或 ulaw_8000 |

Feishu 和 WhatsApp 在需要时用 `ffmpeg` 把非 Opus 输出转码为 48 kHz Ogg/Opus。

## Auto-TTS 行为流程

```text
Reply -> TTS 启用?
  否  -> 发送文本
  是 -> 有 media / 短?
          是 -> 发送文本
          否 -> 长度 > 限制?
                   否 -> TTS -> 附加音频
                   是 -> summary 启用?
                            否 -> 发送文本
                            是 -> summarize -> TTS -> 附加音频
```

## Gateway RPC Methods

| Method | 用途 |
|--------|------|
| `tts.status` | 读取当前 TTS 状态和上次尝试 |
| `tts.enable` | 设置本地 auto preference 为 `always` |
| `tts.disable` | 设置本地 auto preference 为 `off` |
| `tts.convert` | 一次性文本转音频 |
| `tts.setProvider` | 设置本地 provider preference |
| `tts.setPersona` | 设置本地 persona preference |
| `tts.providers` | 列出配置的 providers 和状态 |

## Agent Tool

`tts` tool 把文本转为语音并返回音频附件。在 voice-note-capable channels 上,音频作为语音消息传递。WhatsApp 把音频作为 PTT voice notes 发送,可见文本单独发送。

该 tool 接受可选的 `channel` 和 `timeoutMs` 字段。

## 相关文档

- Media overview
- Music generation
- Video generation
- Slash commands
- Voice call plugin
