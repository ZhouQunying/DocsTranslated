# Voice Call 插件

## 架构精读

> 跳过不影响阅读翻译正文。

### 为什么把电话呼叫做成插件而不是内置？

电话呼叫涉及运营商信令（Twilio/Telnyx/Plivo 各有各的 webhook 协议）、媒体流（PCM 音频的双向传输）和 TTS（文本转语音）。这三块各自演进速度不同，硬塞进核心运行时会拖慢整个 Gateway 的发布节奏。插件化后，新增一个运营商只需写一个 provider adapter，不用碰核心。就像 Kubernetes 的 CSI 驱动——存储引擎在进程外，核心调度器保持轻量。

第二个关键边界：音频模式互斥。`realtime`（全双工实时语音，如 Gemini 实时语音）和 `streaming`（单向转录 + TTS 回读）不能同时开启。两者走完全不同的音频管道——前者是双向低延迟流，后者是单向转录加异步合成。混用会导致音频管道冲突，就像你不能同时用 TCP 和 UDP 传同一个数据流。

第三个值得注意的设计：caller ID 是弱信任。`allowFrom` 白名单做的是来电显示过滤，不是强身份认证。PSTN/VoIP 的来电号码可以被伪造，webhook 签名只验证运营商投递的完整性，不验证来电者是否真的持有那个号码。这就像邮件的 From 头——可以过滤垃圾邮件，但不能证明发件人身份。

---

Voice Call 插件为 OpenClaw 提供语音通话能力。支持出站通知、多轮对话、全双工实时语音、流式转录，以及带白名单策略的入站呼叫。

**当前 provider：** `twilio`（Programmable Voice + Media Streams）、`telnyx`（Call Control v2）、`plivo`（Voice API + XML transfer + GetInput 语音）、`mock`（开发/无网络）。

> **注意**：Voice Call 插件运行在 **Gateway 进程内**。若使用远程 Gateway，需在运行 Gateway 的机器上安装和配置插件，然后重启 Gateway 加载。

## 快速开始

**步骤**

1. **安装插件**

   从 npm：

   ```bash
   openclaw plugins install @openclaw/voice-call
   ```

   从本地文件夹（开发）：

   ```bash
   PLUGIN_SRC=./path/to/local/voice-call-plugin
   openclaw plugins install "$PLUGIN_SRC"
   cd "$PLUGIN_SRC" && pnpm install
   ```

   裸包名跟随当前官方发布标签。仅在需要可复现安装时固定精确版本。安装后重启 Gateway 让插件加载。

2. **配置 provider 和 webhook**

   在 `plugins.entries.voice-call.config` 下设置配置（完整结构见下方[配置](#配置)）。至少需要：`provider`、provider 凭证、`fromNumber` 和公网可达的 webhook URL。

3. **验证设置**

   ```bash
   openclaw voicecall setup
   ```

   默认输出对聊天日志和终端友好。检查插件启用状态、provider 凭证、webhook 暴露和是否只有一种音频模式（`streaming` 或 `realtime`）激活。脚本使用 `--json`。

4. **冒烟测试**

   ```bash
   openclaw voicecall smoke
   openclaw voicecall smoke --to "+15555550123"
   ```

   两者默认都是干跑。加 `--yes` 实际拨打短出站通知呼叫：

   ```bash
   openclaw voicecall smoke --to "+15555550123" --yes
   ```

> **警告**：Twilio、Telnyx 和 Plivo 的设置必须解析到**公网可达的 webhook URL**。若 `publicUrl`、隧道 URL、Tailscale URL 或服务回退解析到回环或私有网络空间，设置会失败而不是启动一个无法接收运营商 webhook 的 provider。

## 配置

若 `enabled: true` 但所选 provider 缺少凭证，Gateway 启动日志记录设置未完成警告，列出缺少的键并跳过启动运行时。命令、RPC 调用和 agent 工具使用时仍返回具体缺少的 provider 配置。

> **注意**：Voice Call 凭证支持 SecretRef。`plugins.entries.voice-call.config.twilio.authToken`、`plugins.entries.voice-call.config.realtime.providers.*.apiKey`、`plugins.entries.voice-call.config.streaming.providers.*.apiKey` 和 `plugins.entries.voice-call.config.tts.providers.*.apiKey` 通过标准 SecretRef 表面解析；详见 [SecretRef 凭证表面](/reference/secretref-credential-surface)。

```json5
{
  plugins: {
    entries: {
      "voice-call": {
        enabled: true,
        config: {
          provider: "twilio", // 或 "telnyx" | "plivo" | "mock"
          fromNumber: "+15550001234", // Twilio 也可用 TWILIO_FROM_NUMBER
          toNumber: "+15550005678",
          sessionScope: "per-phone", // per-phone | per-call
          numbers: {
            "+15550009999": {
              inboundGreeting: "Silver Fox Cards，有什么可以帮忙？",
              responseSystemPrompt: "你是一位简洁的棒球卡专家。",
              tts: {
                providers: {
                  openai: { speakerVoice: "alloy" },
                },
              },
            },
          },

          twilio: {
            accountSid: "ACxxxxxxxx",
            authToken: "...",
          },
          telnyx: {
            apiKey: "...",
            connectionId: "...",
            // Telnyx webhook 公钥来自 Mission Control Portal
            // （Base64；也可通过 TELNYX_PUBLIC_KEY 设置）。
            publicKey: "...",
          },
          plivo: {
            authId: "MAxxxxxxxxxxxxxxxxxxxx",
            authToken: "...",
          },

          // Webhook 服务器
          serve: {
            port: 3334,
            path: "/voice/webhook",
          },

          // Webhook 安全（隧道/代理推荐）
          webhookSecurity: {
            allowedHosts: ["voice.example.com"],
            trustedProxyIPs: ["100.64.0.1"],
          },

          // 公网暴露（选一种）
          // publicUrl: "https://example.ngrok.app/voice/webhook",
          // tunnel: { provider: "ngrok" },
          // tailscale: { mode: "funnel", path: "/voice/webhook" },

          outbound: {
            defaultMode: "notify", // notify | conversation
          },

          streaming: { enabled: true /* 见流式转录 */ },
          realtime: { enabled: false /* 见实时语音 */ },
        },
      },
    },
  },
}
```

### Provider 暴露和安全说明

- Twilio、Telnyx 和 Plivo 都需要**公网可达**的 webhook URL。
- `mock` 是本地开发 provider（无网络调用）。
- Telnyx 需要 `telnyx.publicKey`（或 `TELNYX_PUBLIC_KEY`），除非 `skipSignatureVerification` 为 true。
- `skipSignatureVerification` 仅限本地测试。
- ngrok 免费层需将 `publicUrl` 设为精确 ngrok URL；始终强制签名验证。
- `tunnel.allowNgrokFreeTierLoopbackBypass: true` 仅在 `tunnel.provider="ngrok"` 且 `serve.bind` 是回环时允许 Twilio webhook 无效签名（ngrok 本地 agent）。仅限本地开发。
- Ngrok 免费层 URL 可能变化或添加过渡行为；若 `publicUrl` 漂移，Twilio 签名会失败。生产环境建议用稳定域名或 Tailscale funnel。

### 流式连接上限

- `streaming.preStartTimeoutMs` 关闭从未发送有效 `start` 帧的套接字。
- `streaming.maxPendingConnections` 限制未认证预启动套接字总数。
- `streaming.maxPendingConnectionsPerIp` 限制每源 IP 未认证预启动套接字数。
- `streaming.maxConnections` 限制开放媒体流套接字总数（待处理 + 活跃）。

### 遗留配置迁移

使用 `provider: "log"`、`twilio.from` 或遗留 `streaming.*` OpenAI 键的旧配置可通过 `openclaw doctor --fix` 重写。运行时回退目前仍接受旧 voice-call 键，但重写路径是 `openclaw doctor --fix`，兼容 shim 是临时的。

自动迁移的流式键：

- `streaming.sttProvider` → `streaming.provider`
- `streaming.openaiApiKey` → `streaming.providers.openai.apiKey`
- `streaming.sttModel` → `streaming.providers.openai.model`
- `streaming.silenceDurationMs` → `streaming.providers.openai.silenceDurationMs`
- `streaming.vadThreshold` → `streaming.providers.openai.vadThreshold`

## 会话范围

Voice Call 默认用 `sessionScope: "per-phone"`，同一来电者的重复呼叫保持对话记忆。设 `sessionScope: "per-call"` 让每次运营商呼叫从全新上下文开始，例如前台、预订、IVR 或 Google Meet 桥接流程，同一电话号码可能代表不同会议。

## 实时语音对话

`realtime` 为实时通话音频选择全双工实时语音 provider。它与 `streaming` 不同，后者仅将音频转发给实时转录 provider。

> **警告**：`realtime.enabled` 不能与 `streaming.enabled` 组合。每次呼叫选一种音频模式。

当前运行时行为：

- `realtime.enabled` 支持 Twilio Media Streams。
- `realtime.provider` 可选。未设置时，Voice Call 使用第一个注册的实时语音 provider。
- 捆绑实时语音 provider：Google Gemini 实时语音（`google`）和 OpenAI（`openai`），由各自的 provider 插件注册。
- Provider 原始配置在 `realtime.providers.<providerId>` 下。
- Voice Call 默认暴露共享 `openclaw_agent_consult` 实时工具。实时模型可在来电者要求更深推理、当前信息或正常 OpenClaw 工具时调用它。
- `realtime.consultPolicy` 可选添加指引，控制实时模型何时调用 `openclaw_agent_consult`。
- `realtime.agentContext.enabled` 默认关闭。启用后，Voice Call 在会话设置时向实时 provider 指令注入有界的 agent 身份和选定的工作区文件胶囊。
- `realtime.fastContext.enabled` 默认关闭。启用后，Voice Call 先搜索索引记忆/会话上下文获取咨询问题，在 `realtime.fastContext.timeoutMs` 内返回这些片段给实时模型，仅在 `realtime.fastContext.fallbackToConsult` 为 true 时才回退到完整咨询 agent。
- 若 `realtime.provider` 指向未注册的 provider 或根本没有实时语音 provider 注册，Voice Call 记录警告并跳过实时媒体而不是让整个插件失败。
- 咨询会话键优先复用已存储的呼叫会话，然后回退到配置的 `sessionScope`（默认 `per-phone`，隔离呼叫用 `per-call`）。

### 工具策略

`realtime.toolPolicy` 控制咨询运行：

| 策略             | 行为                                                                                                         |
| ---------------- | ------------------------------------------------------------------------------------------------------------ |
| `safe-read-only` | 暴露咨询工具，限制常规 agent 只能用 `read`、`web_search`、`web_fetch`、`x_search`、`memory_search`、`memory_get` |
| `owner`          | 暴露咨询工具，常规 agent 使用正常 agent 工具策略                                                             |
| `none`           | 不暴露咨询工具。自定义 `realtime.tools` 仍传递给实时 provider                                                |

`realtime.consultPolicy` 仅控制实时模型指令：

| 策略        | 指引                                                         |
| ----------- | ------------------------------------------------------------ |
| `auto`      | 保持默认 prompt，让 provider 决定何时调用咨询工具            |
| `substantive` | 直接回答简单对话衔接，在事实、记忆、工具或上下文前先咨询   |
| `always`    | 每次实质性回答前先咨询                                       |

### Agent 语音上下文

启用 `realtime.agentContext` 让语音桥听起来像配置的 OpenClaw agent，而无需在常规轮次上付出完整 agent 咨询往返的代价。上下文胶囊在实时会话创建时添加一次，不增加每轮延迟。`openclaw_agent_consult` 调用仍运行完整 OpenClaw agent，应用于工具工作、当前信息、记忆查找或工作区状态。

```json5
{
  plugins: {
    entries: {
      "voice-call": {
        config: {
          agentId: "main",
          realtime: {
            enabled: true,
            provider: "google",
            toolPolicy: "safe-read-only",
            consultPolicy: "substantive",
            agentContext: {
              enabled: true,
              maxChars: 6000,
              includeIdentity: true,
              includeWorkspaceFiles: true,
              files: ["SOUL.md", "IDENTITY.md", "USER.md"],
            },
          },
        },
      },
    },
  },
}
```

### 实时 provider 示例

**Google Gemini 实时语音**

默认：API key 来自 `realtime.providers.google.apiKey`、`GEMINI_API_KEY` 或 `GOOGLE_GENERATIVE_AI_API_KEY`；模型 `gemini-2.5-flash-native-audio-preview-12-2025`；语音 `Kore`。`sessionResumption` 和 `contextWindowCompression` 默认开启用于更长、可重连的呼叫。用 `silenceDurationMs`、`startSensitivity` 和 `endSensitivity` 调优电话音频的更快轮次切换。

```json5
{
  plugins: {
    entries: {
      "voice-call": {
        config: {
          provider: "twilio",
          inboundPolicy: "allowlist",
          allowFrom: ["+15550005678"],
          realtime: {
            enabled: true,
            provider: "google",
            instructions: "简短说话。使用更深工具前调用 openclaw_agent_consult。",
            toolPolicy: "safe-read-only",
            consultPolicy: "substantive",
            consultThinkingLevel: "low",
            consultFastMode: true,
            agentContext: { enabled: true },
            providers: {
              google: {
                apiKey: "${GEMINI_API_KEY}",
                model: "gemini-2.5-flash-native-audio-preview-12-2025",
                speakerVoice: "Kore",
                silenceDurationMs: 500,
                startSensitivity: "high",
              },
            },
          },
        },
      },
    },
  },
}
```

**OpenAI**

```json5
{
  plugins: {
    entries: {
      "voice-call": {
        config: {
          realtime: {
            enabled: true,
            provider: "openai",
            providers: {
              openai: { apiKey: "${OPENAI_API_KEY}" },
            },
          },
        },
      },
    },
  },
}
```

provider 专用实时语音选项见 [Google provider](/providers/google) 和 [OpenAI provider](/providers/openai)。

## 流式转录

`streaming` 为实时通话音频选择实时转录 provider。

当前运行时行为：

- `streaming.provider` 可选。未设置时，Voice Call 使用第一个注册的实时转录 provider。
- 捆绑实时转录 provider：Deepgram（`deepgram`）、ElevenLabs（`elevenlabs`）、Mistral（`mistral`）、OpenAI（`openai`）和 xAI（`xai`），由各自的 provider 插件注册。
- Provider 原始配置在 `streaming.providers.<providerId>` 下。
- Twilio 发送接受的流 `start` 消息后，Voice Call 立即注册流，在 provider 连接期间排队入站媒体通过转录 provider，并在实时转录就绪后才开始初始问候。
- 若 `streaming.provider` 指向未注册的 provider 或没有 provider 注册，Voice Call 记录警告并跳过媒体流而不是让整个插件失败。

### 流式 provider 示例

**OpenAI**

默认：API key `streaming.providers.openai.apiKey` 或 `OPENAI_API_KEY`；模型 `gpt-4o-transcribe`；`silenceDurationMs: 800`；`vadThreshold: 0.5`。

```json5
{
  plugins: {
    entries: {
      "voice-call": {
        config: {
          streaming: {
            enabled: true,
            provider: "openai",
            streamPath: "/voice/stream",
            providers: {
              openai: {
                apiKey: "sk-...", // OPENAI_API_KEY 已设置时可选
                model: "gpt-4o-transcribe",
                silenceDurationMs: 800,
                vadThreshold: 0.5,
              },
            },
          },
        },
      },
    },
  },
}
```

**xAI**

默认：API key `streaming.providers.xai.apiKey` 或 `XAI_API_KEY`；端点 `wss://api.x.ai/v1/stt`；编码 `mulaw`；采样率 `8000`；`endpointingMs: 800`；`interimResults: true`。

```json5
{
  plugins: {
    entries: {
      "voice-call": {
        config: {
          streaming: {
            enabled: true,
            provider: "xai",
            streamPath: "/voice/stream",
            providers: {
              xai: {
                apiKey: "${XAI_API_KEY}", // XAI_API_KEY 已设置时可选
                endpointingMs: 800,
                language: "en",
              },
            },
          },
        },
      },
    },
  },
}
```

## 通话 TTS

Voice Call 使用核心 `messages.tts` 配置做通话流式语音。可在插件配置下用**相同结构**覆盖——它与 `messages.tts` 深度合并。

```json5
{
  tts: {
    provider: "elevenlabs",
    providers: {
      elevenlabs: {
        speakerVoiceId: "pMsXgVXv3BLzUgSXRplE",
        modelId: "eleven_multilingual_v2",
      },
    },
  },
}
```

> **警告**：**语音通话忽略 Microsoft speech。** 电话音频需要 PCM；当前 Microsoft 传输不暴露电话 PCM 输出。

行为说明：

- 插件配置内的遗留 `tts.<provider>` 键（`openai`、`elevenlabs`、`microsoft`、`edge`）由 `openclaw doctor --fix` 修复；提交的配置应用 `tts.providers.<provider>`。
- Twilio 媒体流启用时使用核心 TTS；否则呼叫回退到 provider 原生语音。
- 若 Twilio 媒体流已活跃，Voice Call 不回退到 TwiML `Say`。若该状态下电话 TTS 不可用，播放请求失败而不是混合两条播放路径。
- 电话 TTS 回退到次要 provider 时，Voice Call 记录带 provider 链（`from`、`to`、`attempts`）的警告供调试。
- Twilio 打断或流拆除清空待处理 TTS 队列时，已排队播放请求结算而不是让来电者等待播放完成。

### TTS 示例

**仅核心 TTS**

```json5
{
  messages: {
    tts: {
      provider: "openai",
      providers: {
        openai: { speakerVoice: "alloy" },
      },
    },
  },
}
```

**覆盖为 ElevenLabs（仅通话）**

```json5
{
  plugins: {
    entries: {
      "voice-call": {
        config: {
          tts: {
            provider: "elevenlabs",
            providers: {
              elevenlabs: {
                apiKey: "elevenlabs_key",
                speakerVoiceId: "pMsXgVXv3BLzUgSXRplE",
                modelId: "eleven_multilingual_v2",
              },
            },
          },
        },
      },
    },
  },
}
```

**OpenAI 模型覆盖（深度合并）**

```json5
{
  plugins: {
    entries: {
      "voice-call": {
        config: {
          tts: {
            providers: {
              openai: {
                model: "gpt-4o-mini-tts",
                speakerVoice: "marin",
              },
            },
          },
        },
      },
    },
  },
}
```

## 入站呼叫

入站策略默认 `disabled`。启用入站呼叫需设置：

```json5
{
  inboundPolicy: "allowlist",
  allowFrom: ["+15550001234"],
  inboundGreeting: "你好！有什么可以帮忙？",
}
```

> **警告**：`inboundPolicy: "allowlist"` 是低保真来电显示过滤。插件规范化 provider 提供的 `From` 值并与 `allowFrom` 比较。Webhook 验证证明 provider 投递和负载完整性，但**不**证明 PSTN/VoIP 来电号码的所有权。将 `allowFrom` 视为来电显示过滤，不是强来电者身份。

自动响应使用 agent 系统。用 `responseModel`、`responseSystemPrompt` 和 `responseTimeoutMs` 调优。

### 按号码路由

一个 Voice Call 插件接收多个电话号码的呼叫且每个号码需像不同线路时，使用 `numbers`。例如一个号码用随和的个人助理，另一个用商务人格、不同响应 agent 和不同 TTS 语音。

路由从 provider 提供的被叫 `To` 号码选择。键必须是 E.164 号码。呼叫到达时，Voice Call 解析匹配路由一次并将匹配路由存储在呼叫记录上。该有效配置在问候、经典自动响应路径、实时咨询路径和 TTS 播放中复用。无路由匹配时使用全局 Voice Call 配置。出站呼叫不使用 `numbers`；发起呼叫时显式传入出站目标、消息和会话。

路由覆盖当前支持：

- `inboundGreeting`
- `tts`
- `agentId`
- `responseModel`
- `responseSystemPrompt`
- `responseTimeoutMs`

`tts` 路由值深度合并到全局 Voice Call `tts` 配置之上，通常只需覆盖 provider 语音：

```json5
{
  inboundGreeting: "你好，这里是主线。",
  responseSystemPrompt: "你是默认语音助手。",
  tts: {
    provider: "openai",
    providers: {
      openai: { speakerVoice: "coral" },
    },
  },
  numbers: {
    "+15550001111": {
      inboundGreeting: "Silver Fox Cards，有什么可以帮忙？",
      responseSystemPrompt: "你是一位简洁的棒球卡专家。",
      tts: {
        providers: {
          openai: { speakerVoice: "alloy" },
        },
      },
    },
  },
}
```

### 口语输出契约

自动响应时，Voice Call 向系统 prompt 追加严格口语输出契约：

```text
{"spoken":"..."}
```

Voice Call 防御性提取语音文本：

- 忽略标记为推理/错误内容的负载。
- 解析直接 JSON、围栏 JSON 或内联 `"spoken"` 键。
- 回退到纯文本并移除可能的规划/元引导段落。

这保持口语播放聚焦来电者面向文本，避免规划文本泄漏到音频。

### 对话启动行为

出站 `conversation` 呼叫的首条消息处理与实时播放状态绑定：

- 打断队列清空和自动响应仅在初始问候正在说话时被抑制。
- 初始播放失败时，呼叫返回 `listening`，初始消息保持排队等待重试。
- Twilio 流式的初始播放在流连接时开始，无额外延迟。
- 打断中止活跃播放并清空已排队但未播放的 Twilio TTS 条目。清空条目结算为跳过，后续响应逻辑可继续而不等待永远不会播放的音频。
- 实时语音对话使用实时流自己的开场轮次。Voice Call **不**为该初始消息发送遗留 `Say` TwiML 更新，因此出站 `Connect Stream` 会话保持连接。

### Twilio 流断开宽限期

Twilio 媒体流断开时，Voice Call 等待 **2000 ms** 再自动结束呼叫：

- 若流在该窗口内重连，自动结束取消。
- 宽限期后无流重新注册，呼叫结束以防止卡住的活跃呼叫。

## 过期呼叫回收器

用 `staleCallReaperSeconds` 结束从未收到终端 webhook 的呼叫（例如从未完成的 notify 模式呼叫）。默认 `0`（禁用）。

推荐范围：

- **生产：** notify 风格流程 `120`–`300` 秒。
- 保持此值**高于 `maxDurationSeconds`** 让正常呼叫可完成。好的起点是 `maxDurationSeconds + 30–60` 秒。

```json5
{
  plugins: {
    entries: {
      "voice-call": {
        config: {
          maxDurationSeconds: 300,
          staleCallReaperSeconds: 360,
        },
      },
    },
  },
}
```

## Webhook 安全

代理或隧道在 Gateway 前面时，插件从传入请求重建公网 URL 做签名验证。这些选项控制哪些转接头被信任：

- `webhookSecurity.allowedHosts`：转接头的主机白名单。
- `webhookSecurity.trustForwardingHeaders`：无白名单时信任转接头。
- `webhookSecurity.trustedProxyIPs`：仅在请求远程 IP 匹配列表时信任转接头。

额外保护：

- Twilio 和 Plivo 启用 Webhook **重放保护**。重放的有效 webhook 请求被确认但跳过副作用。
- Twilio 对话轮次在 `Gather` 回调中包含每轮令牌，因此过期/重放的语音回调无法满足更新的待处理转录轮次。
- 缺少 provider 要求的签名头时，未认证 webhook 请求在 body 读取前被拒绝。
- voice-call webhook 使用共享预认证 body 档案（64 KB / 5 秒）加签名验证前的每 IP 在途上限。

稳定公网主机示例：

```json5
{
  plugins: {
    entries: {
      "voice-call": {
        config: {
          publicUrl: "https://voice.example.com/voice/webhook",
          webhookSecurity: {
            allowedHosts: ["voice.example.com"],
          },
        },
      },
    },
  },
}
```

## CLI

```bash
openclaw voicecall call --to "+15555550123" --message "Hello from OpenClaw"
openclaw voicecall start --to "+15555550123"   # call 的别名
openclaw voicecall continue --call-id <id> --message "有什么问题？"
openclaw voicecall speak --call-id <id> --message "稍等"
openclaw voicecall dtmf --call-id <id> --digits "ww123456#"
openclaw voicecall end --call-id <id>
openclaw voicecall status --call-id <id>
openclaw voicecall tail
openclaw voicecall latency                      # 汇总日志中的轮次延迟
openclaw voicecall expose --mode funnel
```

Gateway 已运行时，运维 `voicecall` 命令委托给 Gateway 持有的 voice-call 运行时，CLI 不绑定第二个 webhook 服务器。若无 Gateway 可达，命令回退到独立 CLI 运行时。

`latency` 从默认 voice-call 存储路径读取 `calls.jsonl`。用 `--file <path>` 指向不同日志，`--last <n>` 限制分析最后 N 条记录（默认 200）。输出包括轮次延迟和听候时间的 p50/p90/p99。

## Agent 工具

工具名：`voice_call`。

| 动作            | 参数                                       |
| --------------- | ------------------------------------------ |
| `initiate_call` | `message`、`to?`、`mode?`、`dtmfSequence?` |
| `continue_call` | `callId`、`message`                        |
| `speak_to_user` | `callId`、`message`                        |
| `send_dtmf`     | `callId`、`digits`                         |
| `end_call`      | `callId`                                   |
| `get_status`    | `callId`                                   |

本仓库附带匹配技能文档 `skills/voice-call/SKILL.md`。

## Gateway RPC

| 方法                 | 参数                                       |
| -------------------- | ------------------------------------------ |
| `voicecall.initiate` | `to?`、`message`、`mode?`、`dtmfSequence?` |
| `voicecall.continue` | `callId`、`message`                        |
| `voicecall.speak`    | `callId`、`message`                        |
| `voicecall.dtmf`     | `callId`、`digits`                         |
| `voicecall.end`      | `callId`                                   |
| `voicecall.status`   | `callId`                                   |

`dtmfSequence` 仅对 `mode: "conversation"` 有效。Notify 模式呼叫如需连接后数字，应在呼叫存在后用 `voicecall.dtmf`。

## 故障排查

### 设置失败 webhook 暴露

从运行 Gateway 的同一环境跑设置：

```bash
openclaw voicecall setup
openclaw voicecall setup --json
```

`twilio`、`telnyx` 和 `plivo` 的 `webhook-exposure` 必须绿色。配置的 `publicUrl` 指向本地或私有网络空间时仍会失败，因为运营商无法回调这些地址。不要用 `localhost`、`127.0.0.1`、`0.0.0.0`、`10.x`、`172.16.x`-`172.31.x`、`192.168.x`、`169.254.x`、`fc00::/7` 或 `fd00::/8` 作 `publicUrl`。

Twilio notify 模式出站呼叫在创建呼叫请求中直接发送初始 `Say` TwiML，因此首次口语消息不依赖 Twilio 获取 webhook TwiML。状态回调、对话呼叫、连接前 DTMF、实时流和连接后呼叫控制仍需公网 webhook。

使用一种公网暴露路径：

```json5
{
  plugins: {
    entries: {
      "voice-call": {
        config: {
          publicUrl: "https://voice.example.com/voice/webhook",
          // 或
          tunnel: { provider: "ngrok" },
          // 或
          tailscale: { mode: "funnel", path: "/voice/webhook" },
        },
      },
    },
  },
}
```

改完配置后重启或重载 Gateway，然后运行：

```bash
openclaw voicecall setup
openclaw voicecall smoke
```

`voicecall smoke` 默认干跑，除非传 `--yes`。

### Provider 凭证失败

检查所选 provider 和所需凭证字段：

- Twilio：`twilio.accountSid`、`twilio.authToken` 和 `fromNumber`，或 `TWILIO_ACCOUNT_SID`、`TWILIO_AUTH_TOKEN` 和 `TWILIO_FROM_NUMBER`。
- Telnyx：`telnyx.apiKey`、`telnyx.connectionId`、`telnyx.publicKey` 和 `fromNumber`。
- Plivo：`plivo.authId`、`plivo.authToken` 和 `fromNumber`。

凭证必须存在于 Gateway 宿主机。编辑本地 shell profile 不影响已运行的 Gateway，直到重启或重载环境。

### 呼叫启动但 provider webhook 不到达

确认 provider 控制台指向精确公网 webhook URL：

```text
https://voice.example.com/voice/webhook
```

然后检查运行时状态：

```bash
openclaw voicecall status --call-id <id>
openclaw voicecall tail
openclaw logs --follow
```

常见原因：

- `publicUrl` 指向的路径与 `serve.path` 不同。
- Gateway 启动后隧道 URL 变化。
- 代理转发请求但剥离或重写 host/proto 头。
- 防火墙或 DNS 将公网主机名路由到 Gateway 以外的地方。
- Gateway 重启时 Voice Call 插件未启用。

反向代理或隧道在 Gateway 前面时，将 `webhookSecurity.allowedHosts` 设为公网主机名，或用 `webhookSecurity.trustedProxyIPs` 指定已知代理地址。仅在代理边界在你控制下时使用 `webhookSecurity.trustForwardingHeaders`。

### 签名验证失败

Provider 签名根据 OpenClaw 从传入请求重建的公网 URL 检查。签名失败时：

- 确认 provider webhook URL 精确匹配 `publicUrl`，包括 scheme、host 和 path。
- ngrok 免费层 URL 变化时更新 `publicUrl`。
- 确认代理保留原始 host 和 proto 头，或配置 `webhookSecurity.allowedHosts`。
- 本地测试外不要启用 `skipSignatureVerification`。

### Google Meet Twilio 加入失败

Google Meet 用此插件做 Twilio 拨入加入。先验证 Voice Call：

```bash
openclaw voicecall setup
openclaw voicecall smoke --to "+15555550123"
```

然后显式验证 Google Meet 传输：

```bash
openclaw googlemeet setup --transport twilio
```

Voice Call 绿色但 Meet 参与者从未加入时，检查 Meet 拨入号码、PIN 和 `--dtmf-sequence`。电话可健康而会议拒绝或忽略错误的 DTMF 序列。

Google Meet 通过 `voicecall.start` 启动 Twilio 电话腿，带连接前 DTMF 序列。PIN 派生序列包含 Google Meet 插件的 `voiceCall.dtmfDelayMs` 作为前导 Twilio 等待数字。默认 12 秒因为 Meet 拨入提示可能延迟到达。Voice Call 然后在请求介绍问候前重定向回实时处理。

用 `openclaw logs --follow` 查看实时阶段追踪。健康的 Twilio Meet 加入按此顺序记录：

- Google Meet 将 Twilio 加入委托给 Voice Call。
- Voice Call 存储连接前 DTMF TwiML。
- Twilio 初始 TwiML 在实时处理前被消费和服务。
- Voice Call 为 Twilio 呼叫服务实时 TwiML。
- Google Meet 在 DTMF 后延迟后用 `voicecall.speak` 请求介绍语音。

`openclaw voicecall tail` 仍显示持久化呼叫记录；对呼叫状态和转录有用，但不是每个 webhook/实时转换都出现在那里。

### 实时呼叫无语音

确认只启用一种音频模式。`realtime.enabled` 和 `streaming.enabled` 不能同时为 true。

实时 Twilio 呼叫还需验证：

- 实时 provider 插件已加载并注册。
- `realtime.provider` 未设置或指向已注册的 provider。
- Provider API key 对 Gateway 进程可用。
- `openclaw logs --follow` 显示实时 TwiML 已服务、实时桥已启动、初始问候已排队。

## 相关

- [Talk 模式](/nodes/talk)
- [Text-to-speech](/tools/tts)
- [Voice wake](/nodes/voicewake)
