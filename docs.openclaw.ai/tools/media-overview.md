# Media overview

## 架构精读

> 跳过不影响阅读翻译正文。

### 图片、视频、音乐、TTS、STT——怎么统一管？

表面上是五种媒体能力,但底层就两个模式：同步和异步。TTS 几秒钟回来,贴到回复里就行——同步。图片、视频、音乐都可能跑几分钟——异步。

异步的统一模式：提交请求 → 拿到任务 id → agent 该干嘛干嘛 → provider 出结果了唤醒 agent → agent 通过 message 工具把成品发给用户。

关键设计：如果 agent 被唤醒时用户的会话已经不活跃了怎么办？OpenClaw 有一条"幂等直接回退"路径——绕过 agent,直接把缺的媒体送达,且只送"message 工具还没投递过的"那部分。这保证用户不会收不到,也不会收两遍。

跟电商订单一样：正常路径是"客服通知你取货"；客服联系不上你,系统直接发短信告诉你。

---

> OpenClaw generates images, videos, and music, understands inbound media
> (images, audio, video), and speaks replies aloud with text-to-speech. All
> media capabilities are tool-driven: the agent decides when to use them based
> on the conversation, and each tool only appears when at least one backing
> provider is configured.

OpenClaw 能生成图片、视频、音乐,能理解收到的媒体(图片、音频、视频),还能用文本转语音把回复读出来。所有媒体能力都是工具驱动的:agent 根据对话决定什么时候用,每个工具只有至少配了一个支撑 provider 时才会出现。

> Live speech uses the Talk session contract instead of the one-shot media tool
> path. Talk has three modes: provider-native `realtime`, local or streaming
> `stt-tts`, and `transcription` for observe-only speech capture. Those modes
> share provider catalogs, event envelopes, and cancellation semantics with
> telephony, meetings, browser realtime, and native push-to-talk clients.

实时语音走 Talk 会话契约,不走"一次性媒体工具"路径。Talk 有三种模式:provider 原生 `realtime`、本地或流式 `stt-tts`、用于"只观察"语音捕获的 `transcription`。这三种模式跟电话、会议、浏览器实时、原生按键说话客户端,共享 provider 目录、事件封套和取消语义。

## 能力清单

> - Image generation — Create and edit images from text prompts or reference images via `image_generate`. Async in chat sessions — runs in the background and posts the result when ready.
> - Video generation — Text-to-video, image-to-video, and video-to-video via `video_generate`. Async — runs in the background and posts the result when ready.
> - Music generation — Generate music or audio tracks via `music_generate`. Async in chat sessions on the shared media-generation task lifecycle.
> - Text-to-speech — Convert outbound replies to spoken audio via the `tts` tool plus `messages.tts` config. Synchronous.
> - Media understanding — Summarize inbound images, audio, and video using vision-capable model providers and dedicated media-understanding plugins.
> - Speech-to-text — Transcribe inbound voice messages through batch STT or Voice Call streaming STT providers.

- [图片生成](/tools/image-generation) —— 用 `image_generate` 从文本提示或参考图生成、编辑图片。聊天会话里异步,后台跑、好了再贴结果。
- [视频生成](/tools/video-generation) —— 用 `video_generate` 做文生视频、图生视频、视频生视频。异步,后台跑、好了再贴结果。
- [音乐生成](/tools/music-generation) —— 用 `music_generate` 生成音乐或音频。聊天会话里异步,跟其他媒体生成共享同一份任务生命周期。
- [文本转语音](/tools/tts) —— 用 `tts` 工具加 `messages.tts` 配置,把出站回复转成语音。同步。
- [媒体理解](/nodes/media-understanding) —— 用有视觉能力的模型 provider 和专门的媒体理解插件,总结收到的图片、音频、视频。
- [语音转文本](/nodes/audio) —— 通过批量 STT 或 Voice Call 流式 STT provider,转录收到的语音消息。

## Provider 能力矩阵

> | Provider    | Image | Video | Music | TTS | STT | Realtime voice | Media understanding |

| Provider    | 图片  | 视频  | 音乐  | TTS | STT | 实时语音       | 媒体理解            |
| ----------- | :---: | :---: | :---: | :-: | :-: | :------------: | :-----------------: |
| Alibaba     |       |   ✓   |       |     |     |                |                     |
| BytePlus    |       |   ✓   |       |     |     |                |                     |
| ComfyUI     |   ✓   |   ✓   |   ✓   |     |     |                |                     |
| DeepInfra   |   ✓   |   ✓   |       |  ✓  |  ✓  |                |          ✓          |
| Deepgram    |       |       |       |     |  ✓  |       ✓        |                     |
| ElevenLabs  |       |       |       |  ✓  |  ✓  |                |                     |
| fal         |   ✓   |   ✓   |   ✓   |     |     |                |                     |
| Google      |   ✓   |   ✓   |   ✓   |  ✓  |     |       ✓        |          ✓          |
| Gradium     |       |       |       |  ✓  |     |                |                     |
| Local CLI   |       |       |       |  ✓  |     |                |                     |
| Microsoft   |       |       |       |  ✓  |     |                |                     |
| MiniMax     |   ✓   |   ✓   |   ✓   |  ✓  |     |                |                     |
| Mistral     |       |       |       |     |  ✓  |                |                     |
| OpenAI      |   ✓   |   ✓   |       |  ✓  |  ✓  |       ✓        |          ✓          |
| OpenRouter  |   ✓   |   ✓   |   ✓   |  ✓  |  ✓  |                |          ✓          |
| Qwen        |       |   ✓   |       |     |     |                |                     |
| Runway      |       |   ✓   |       |     |     |                |                     |
| SenseAudio  |       |       |       |     |  ✓  |                |                     |
| Together    |       |   ✓   |       |     |     |                |                     |
| Vydra       |   ✓   |   ✓   |       |  ✓  |     |                |                     |
| xAI         |   ✓   |   ✓   |       |  ✓  |  ✓  |                |          ✓          |
| Xiaomi MiMo |   ✓   |       |       |  ✓  |     |                |          ✓          |

> <Note>
> Media understanding uses any vision-capable or audio-capable model registered
> in your provider config. The matrix above lists providers with dedicated
> media-understanding support; most multimodal LLM providers (Anthropic, Google,
> OpenAI, etc.) can also understand inbound media when configured as the active
> reply model.
> </Note>

[展开: 注意] 媒体理解用任何在你 provider 配置里注册过的、有视觉或音频能力的模型。上面这张矩阵列的是有专门媒体理解支持的 provider;大多数多模态 LLM provider(Anthropic、Google、OpenAI 等)在被配成当前回复模型时也能理解收到的媒体。

## 异步 vs 同步

> | Capability     | Mode         | Why                                                                                                  |
> | -------------- | ------------ | ---------------------------------------------------------------------------------------------------- |
> | Image          | Asynchronous | Provider processing can outlive a chat turn; generated attachments use the shared completion path.   |
> | Text-to-speech | Synchronous  | Provider responses return in seconds; attached to the reply audio.                                   |
> | Video          | Asynchronous | Provider processing takes 30 s to several minutes; slow queues can run up to the configured timeout. |
> | Music          | Asynchronous | Same provider-processing characteristic as video.                                                    |

| 能力           | 模式  | 为什么                                                                                |
| -------------- | ----- | ------------------------------------------------------------------------------------- |
| 图片           | 异步  | provider 处理可能比一轮对话还长;生成的附件走共享的完成路径。                          |
| 文本转语音     | 同步  | provider 几秒钟内返回;直接贴到回复音频里。                                            |
| 视频           | 异步  | provider 处理 30 秒到几分钟;慢队列能跑到配置的超时上限。                              |
| 音乐           | 异步  | 跟视频是一样的 provider 处理特性。                                                    |

> For async tools, OpenClaw submits the request to the provider, returns a task
> id immediately, and tracks the job in the task ledger. The agent continues
> responding to other messages while the job runs. When the provider finishes,
> OpenClaw wakes the agent with the generated media paths so it can tell the
> user and relay the result through the message tool. If the requester session
> is inactive and some generated media is still missing from message-tool
> delivery, OpenClaw sends an idempotent direct fallback with only the missing
> media. Media already delivered through the message tool is not posted again.

异步工具的流程是:OpenClaw 把请求提交给 provider,立刻返回一个任务 id,在任务台账里跟踪这个 job。job 跑着的时候,agent 可以继续回别的消息。provider 完成时,OpenClaw 用生成出的媒体路径唤醒 agent,让它告诉用户,并通过 message 工具把结果转发出去。请求方会话不活跃、message 工具还没把某些生成的媒体送达时,OpenClaw 会发一次幂等的直接回退,只包含缺的那部分媒体。已经通过 message 工具送达的媒体不再重发。

## 语音转文本和 Voice Call

> Deepgram, DeepInfra, ElevenLabs, Mistral, OpenAI, OpenRouter, SenseAudio, and xAI can all transcribe
> inbound audio through the batch `tools.media.audio` path when configured.
> Channel plugins that preflight a voice note for mention gating or command
> parsing mark the transcribed attachment on the inbound context, so the shared
> media-understanding pass reuses that transcript instead of making a second
> STT call for the same audio.

配置好之后,Deepgram、DeepInfra、ElevenLabs、Mistral、OpenAI、OpenRouter、SenseAudio、xAI 都能通过批量 `tools.media.audio` 路径转录收到的音频。通道插件为 @ 触发或命令解析预处理语音笔记时,会在入站上下文上打"已转录"标记。共享的媒体理解流程看到标记就复用这份转录,不会对同一份音频再发 STT。

> Deepgram, ElevenLabs, Mistral, OpenAI, and xAI also register Voice Call
> streaming STT providers, so live phone audio can be forwarded to the selected
> vendor without waiting for a completed recording.

Deepgram、ElevenLabs、Mistral、OpenAI、xAI 也注册了 Voice Call 流式 STT provider,所以实时电话音频可以直接转给选中的 vendor,不用等录完。

> For live user conversations, prefer [Talk mode](/nodes/talk). Batch audio
> attachments stay on the media path; browser realtime, native push-to-talk,
> telephony, and meeting audio should use Talk events and the session-scoped
> catalogs returned by the Gateway.

实时用户对话优先用 [Talk 模式](/nodes/talk)。批量音频附件留在媒体路径上;浏览器实时、原生按键说话、电话、会议音频应该用 Talk 事件和 Gateway 返回的会话级目录。

## Provider 映射(各家厂商在不同接口上的分布)

> <Accordion title="Google">
>     Image, video, music, batch TTS, backend realtime voice, and
>     media-understanding surfaces.

[展开: Google] 图片、视频、音乐、批量 TTS、后端实时语音、媒体理解接口。

> <Accordion title="OpenAI">
>     Image, video, batch TTS, batch STT, Voice Call streaming STT, backend
>     realtime voice, and memory-embedding surfaces.

[展开: OpenAI] 图片、视频、批量 TTS、批量 STT、Voice Call 流式 STT、后端实时语音、记忆嵌入接口。

> <Accordion title="DeepInfra">
>     Chat/model routing, image generation/editing, text-to-video, batch TTS,
>     batch STT, image media understanding, and memory-embedding surfaces.
>     DeepInfra-native rerank/classification/object-detection models are not
>     registered until OpenClaw has dedicated provider contracts for those
>     categories.

[展开: DeepInfra] 聊天 / 模型路由、图片生成 / 编辑、文生视频、批量 TTS、批量 STT、图片媒体理解、记忆嵌入接口。在 OpenClaw 为重排 / 分类 / 物体检测这几类有专门 provider 契约之前,DeepInfra 原生的这些模型不会注册进来。

> <Accordion title="xAI">
>     Image, video, search, code-execution, batch TTS, batch STT, and Voice
>     Call streaming STT. xAI Realtime voice is an upstream capability but is
>     not registered in OpenClaw until the shared realtime-voice contract can
>     represent it.

[展开: xAI] 图片、视频、搜索、code-execution、批量 TTS、批量 STT、Voice Call 流式 STT。xAI Realtime 语音是上游能力,但在共享的实时语音契约能表达它之前,不会注册进 OpenClaw。

## 相关

> - [Image generation](/tools/image-generation)
> - [Video generation](/tools/video-generation)
> - [Music generation](/tools/music-generation)
> - [Text-to-speech](/tools/tts)
> - [Media understanding](/nodes/media-understanding)
> - [Audio nodes](/nodes/audio)
> - [Talk mode](/nodes/talk)

- [图片生成](/tools/image-generation)
- [视频生成](/tools/video-generation)
- [音乐生成](/tools/music-generation)
- [文本转语音](/tools/tts)
- [媒体理解](/nodes/media-understanding)
- [音频节点](/nodes/audio)
- [Talk 模式](/nodes/talk)
