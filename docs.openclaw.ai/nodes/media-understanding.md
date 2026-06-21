# Media Understanding

**总结：** 入站图片/音频/视频理解（可选）——provider + CLI fallback 链。

> **类比：LangChain 的 Document Loader + 多 provider 路由。** LangChain 用 loader 把 PDF/图片转成 Document 给 chain 处理。OpenClaw media understanding 类似——把入站媒体预处理成文本摘要注入回复 pipeline，但支持 provider API + 本地 CLI 双轨、按 capability 分治、多模型有序 fallback。
>
> **架构要点：** 配置在 `tools.media`，按 capability 分治（image/audio/video）；流程：收集附件 → 按 policy 选择（默认 first）→ 选首个合格模型（size + capability + auth 检查）→ 失败降级下一个；成功时 `Body` 替换为 `[Image]`/`[Audio]`/`[Video]` block，音频设 `{{Transcript}}`；默认 `maxChars` 500（image/video）、`maxBytes` image 10MB/audio 20MB/video 50MB；auto-detect 顺序：活跃回复模型 → agents.defaults.imageModel → 本地 CLI（音频）→ Gemini CLI → provider auth（按 capability 有不同 fallback 链）；`scope` 可按 channel/chatType/session 限制。
