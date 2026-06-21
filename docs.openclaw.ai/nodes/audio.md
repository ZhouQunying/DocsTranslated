# Audio and Voice

**总结：** OpenClaw 处理入站音频/语音消息——下载、转录、注入 transcript 到回复流程。

> **类比：Whisper API + 多 provider fallback。** 类似 OpenAI 的 `/v1/audio/transcriptions` 端点，但支持 provider（OpenAI、Groq、Deepgram、Mistral 等）+ 本地 CLI（whisper-cpp、sherpa-onnx）双轨，自动检测优先级，失败时降级下一个。
>
> **架构要点：** 配置在 `tools.media.audio`；auto-detect 顺序：活跃回复模型 → 本地 CLI（sherpa-onnx/whisper-cli/whisper）→ provider auth（OpenAI → Groq → xAI → Deepgram → Google → SenseAudio → ElevenLabs → Mistral）；成功时 `Body` 替换为 `[Audio]` block + `{{Transcript}}`；`maxBytes` 默认 20MB，< 1024 bytes 跳过；`echoTranscript` opt-in 向 chat 发送转录确认；group mention 场景先 preflight 转录再检测 mention；CLI stdout 限制 5MB。
