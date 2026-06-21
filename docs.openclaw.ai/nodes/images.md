# Images and Media

**总结：** 出站附件路由的操作参数——命令行发送、自动回复附加文件、大小限制。基于 **Baileys Web** 实现。

> **类比：Telegram Bot API 的 sendPhoto/sendDocument + 自动压缩。** 类似 Telegram Bot API 发送媒体时按类型自动选择 API（图片 sendPhoto、文件 sendDocument、语音 sendVoice），OpenClaw 也按类型分流：图片压缩到 2048px JPEG、音频/视频直传 16MB 上限（音频加 `ptt: true` 作语音消息）、文件 100MB 上限，格式识别优先 binary signature 而非扩展名。
>
> **架构要点：** CLI：`openclaw message send --media <path> [--message <caption>] [--gif-playback]`；图片自动缩放+压缩 JPEG（2048px 上限，目标 `channels.whatsapp.mediaMaxMb` 通常 50MB）；音频/视频直传 16MB（音频作 voice message `ptt: true`）；文件 100MB；GIF 用 MP4 + `gifPlayback: true`；入站文件临时存储生成 `{{MediaUrl}}`/`{{MediaPath}}`，sandbox 模式下移到 workspace；`tools.media.*` 在模板前注入 `[Image]`/`[Audio]`/`[Video]` 标签。
