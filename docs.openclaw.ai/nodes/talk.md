# Talk Mode

OpenClaw 的 Talk mode 有两种运行时形态：**Native Talk**（macOS/iOS/Android）用本地语音识别 + Gateway chat + `talk.speak` TTS；**Browser Talk** 用 `talk.client.create`（client-owned WebRTC/WebSocket）或 `talk.session.create`（Gateway-owned relay）。Android 可选 Gateway-owned realtime relay（`talk.realtime.mode: "realtime"`）。还有 **Transcription-only** 模式（`mode: "transcription"`，无 assistant 语音响应）。

> **类比：Zoom 的实时语音 + 转录 + GPT 助手。** Zoom 实时识别语音、转录、GPT 回答问题。OpenClaw Talk 类似——Native 模式是连续语音循环（听 → 转录 → 模型 → TTS 播放），Browser 模式是 WebRTC 实时双向流，支持中断（说话时打断 assistant）和 steering（实时调整 assistant 方向）。
>
> **架构要点：** Native 循环：语音识别 → transcript 发 chat.send → 等待响应 → talk.speak TTS；Browser 用 `talk.client.toolCall` 转发 provider tool calls，不直接 `chat.send`；中断检测默认开（`interruptOnSpeech: true`）；语音指令：assistant 可在回复首行嵌入 JSON `{ "voice": "<id>", "once": true }` 控制 voice/model/speed；realtime.brain 三种：`agent-consult`（Gateway policy）、`direct-tools`（legacy）、`none`（transcription-only）；silence timeout 默认 macOS/Android 700ms、iOS 900ms；provider 选择：ElevenLabs/MLX/system（本地），realtime 用 OpenAI/Google。
