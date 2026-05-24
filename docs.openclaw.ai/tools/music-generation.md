# Music generation

> The `music_generate` tool lets the agent create music or audio through the
> shared music-generation capability with configured providers — ComfyUI,
> fal, Google, MiniMax, and OpenRouter today.

`music_generate` 工具让 agent 通过共享的音乐生成能力,用配置好的 provider 创建音乐或音频 —— 目前是 ComfyUI、fal、Google、MiniMax、OpenRouter。

> For session-backed agent runs, OpenClaw starts music generation as a
> background task, tracks it in the task ledger, then wakes the agent again
> when the track is ready so the agent can tell the user and attach the
> finished audio. Generated-media completions are delivered by the agent through
> the message tool. If the requester session is inactive and some generated
> audio is still missing from message-tool delivery, OpenClaw sends an
> idempotent direct fallback with only the missing audio. The completion wake
> explicitly warns the agent that normal final replies are private for this
> route.

对有会话支撑的 agent 运行,OpenClaw 把音乐生成作为后台任务启动、记到任务台账,曲子好了再唤醒 agent,让它告诉用户并附上完成的音频。生成媒体的完成结果由 agent 通过 message 工具投递。请求方会话不活跃、message 工具还没把某些生成的音频送达时,OpenClaw 会发一次幂等的直接回退,只包含缺的那部分音频。完成唤醒会显式提醒 agent:在这条路径上,常规的最终回复是私密的。

> <Note>
> The built-in shared tool only appears when at least one music-generation
> provider is available. If you do not see `music_generate` in your agent's
> tools, configure `agents.defaults.musicGenerationModel` or set up a
> provider API key.
> </Note>

[展开: 注意] 内置的共享工具只有在至少一个音乐生成 provider 可用时才出现。你 agent 的工具列表里看不到 `music_generate` 的话,配 `agents.defaults.musicGenerationModel` 或设一个 provider API key。

## 快速开始

> <Tab title="Shared provider-backed">

[标签: 共享 provider 支持]

> <Step title="Configure auth">
>         Set an API key for at least one provider — for example
>         `GEMINI_API_KEY` or `MINIMAX_API_KEY`.

[步骤 1: 配认证] 给至少一个 provider 设 API key —— 如 `GEMINI_API_KEY` 或 `MINIMAX_API_KEY`。

> <Step title="Pick a default model (optional)">

[步骤 2: 选个默认模型(可选)]

```json5
{
  agents: {
    defaults: {
      musicGenerationModel: {
        primary: "google/lyria-3-clip-preview",
      },
    },
  },
}
```

> <Step title="Ask the agent">
>         _"Generate an upbeat synthpop track about a night drive through a
>         neon city."_

[步骤 3: 让 agent 干活] _"生成一首关于夜里穿过霓虹城市开车的、节奏明快的合成器流行音乐。"_

> The agent calls `music_generate` automatically. No tool
> allow-listing needed.

agent 自动调 `music_generate`。不需要把工具加进 allow 列表。

> For direct synchronous contexts without a session-backed agent run,
> the built-in tool still falls back to inline generation and returns
> the final media path in the tool result.

对没有会话支撑的直接同步上下文,内置工具仍然回退到内联生成,在工具结果里返回最终媒体路径。

> <Tab title="ComfyUI workflow">

[标签: ComfyUI 工作流]

> <Step title="Configure the workflow">
>         Configure `plugins.entries.comfy.config.music` with a workflow
>         JSON and prompt/output nodes.

[步骤 1: 配工作流] 在 `plugins.entries.comfy.config.music` 里配一份 workflow JSON 和 prompt / output 节点。

> <Step title="Cloud auth (optional)">
>         For Comfy Cloud, set `COMFY_API_KEY` or `COMFY_CLOUD_API_KEY`.

[步骤 2: 云认证(可选)] Comfy Cloud,设 `COMFY_API_KEY` 或 `COMFY_CLOUD_API_KEY`。

> <Step title="Call the tool">

[步骤 3: 调工具]

```text
/tool music_generate prompt="Warm ambient synth loop with soft tape texture"
```

> Example prompts:

例子 prompt:

```text
Generate a cinematic piano track with soft strings and no vocals.
```

```text
Generate an energetic chiptune loop about launching a rocket at sunrise.
```

## 支持的 provider

> | Provider   | Default model                | Reference inputs | Supported controls                                    | Auth                                   |

| Provider   | 默认模型                       | 参考输入        | 支持的控制                                              | 认证                                       |
| ---------- | ------------------------------ | --------------- | ------------------------------------------------------- | ------------------------------------------ |
| ComfyUI    | `workflow`                     | 最多 1 张图     | 工作流定义的音乐或音频                                  | `COMFY_API_KEY`、`COMFY_CLOUD_API_KEY`     |
| fal        | `fal-ai/minimax-music/v2.6`    | 无              | `lyrics`、`instrumental`、`durationSeconds`、`format`   | `FAL_KEY` 或 `FAL_API_KEY`                 |
| Google     | `lyria-3-clip-preview`         | 最多 10 张图    | `lyrics`、`instrumental`、`format`                      | `GEMINI_API_KEY`、`GOOGLE_API_KEY`         |
| MiniMax    | `music-2.6`                    | 无              | `lyrics`、`instrumental`、`format=mp3`                  | `MINIMAX_API_KEY` 或 MiniMax OAuth         |
| OpenRouter | `google/lyria-3-pro-preview`   | 最多 1 张图     | `lyrics`、`instrumental`、`durationSeconds`、`format`   | `OPENROUTER_API_KEY`                       |

### 能力矩阵

> The explicit mode contract used by `music_generate`, contract tests, and the
> shared live sweep:

`music_generate`、契约测试、共享实时扫描用的显式模式契约:

> | Provider   | `generate` | `edit` | Edit limit | Shared live lanes                                                         |

| Provider   | `generate` | `edit` | 编辑上限    | 共享实时通路                                                              |
| ---------- | :--------: | :----: | ----------- | ------------------------------------------------------------------------- |
| ComfyUI    |     ✓      |   ✓    | 1 张图       | 不在共享扫描里;由 `extensions/comfy/comfy.live.test.ts` 覆盖             |
| fal        |     ✓      |   —    | 无          | `generate`                                                                |
| Google     |     ✓      |   ✓    | 10 张图     | `generate`、`edit`                                                        |
| MiniMax    |     ✓      |   —    | 无          | `generate`                                                                |
| OpenRouter |     ✓      |   ✓    | 1 张图       | `generate`、`edit`                                                        |

> Use `action: "list"` to inspect available shared providers and models at
> runtime:

运行时用 `action: "list"` 查看可用的共享 provider 和模型:

```text
/tool music_generate action=list
```

> Use `action: "status"` to inspect the active session-backed music task:

用 `action: "status"` 查看当前会话支撑的活跃音乐任务:

```text
/tool music_generate action=status
```

> Direct generation example:

直接生成例子:

```text
/tool music_generate prompt="Dreamy lo-fi hip hop with vinyl texture and gentle rain" instrumental=true
```

## 工具参数

> `prompt` (string, required) — Music generation prompt. Required for `action: "generate"`.

`prompt`(string,必填)—— 音乐生成 prompt。`action: "generate"` 时必填。

> `action` (`"generate" | "status" | "list"`, default: generate) — `"status"` returns the current session task; `"list"` inspects providers.

`action`(`"generate" | "status" | "list"`,默认 generate)—— `"status"` 返回当前会话任务;`"list"` 查看 provider。

> `model` (string) — Provider/model override (e.g. `google/lyria-3-pro-preview`, `comfy/workflow`).

`model`(string)—— provider/模型覆盖(如 `google/lyria-3-pro-preview`、`comfy/workflow`)。

> `lyrics` (string) — Optional lyrics when the provider supports explicit lyric input.

`lyrics`(string)—— provider 支持显式歌词输入时的可选歌词。

> `instrumental` (boolean) — Request instrumental-only output when the provider supports it.

`instrumental`(boolean)—— provider 支持时,请求只要乐器、不要人声。

> `image` (string) — Single reference image path or URL.

`image`(string)—— 单张参考图路径或 URL。

> `images` (string[]) — Multiple reference images (up to 10 on supporting providers).

`images`(string[])—— 多张参考图(支持的 provider 上最多 10 张)。

> `durationSeconds` (number) — Target duration in seconds when the provider supports duration hints.

`durationSeconds`(number)—— provider 支持时长提示时的目标时长(秒)。

> `format` (`"mp3" | "wav"`) — Output format hint when the provider supports it.

`format`(`"mp3" | "wav"`)—— provider 支持时的输出格式提示。

> `filename` (string) — Output filename hint.

`filename`(string)—— 输出文件名提示。

> <Note>
> Not all providers support all parameters. OpenClaw still validates hard
> limits such as input counts before submission. When a provider supports
> duration but uses a shorter maximum than the requested value, OpenClaw
> clamps to the closest supported duration. Truly unsupported optional hints
> are ignored with a warning when the selected provider or model cannot honor
> them. Tool results report applied settings; `details.normalization`
> captures any requested-to-applied mapping.
> </Note>

[展开: 注意] 不是每个 provider 都支持所有参数。OpenClaw 在提交前会校验输入数量等硬限制。provider 支持时长但最大值短于请求值时,OpenClaw 夹到最接近的支持时长。所选 provider 或模型实在不支持的可选提示,会带一条警告被忽略。工具结果会报告实际应用的设置;`details.normalization` 记录"请求到实际应用"的映射。

> Provider request timeouts are operator configuration only. OpenClaw uses
> `agents.defaults.musicGenerationModel.timeoutMs` when configured, raises values
> below 120000ms to 120000ms, and otherwise defaults provider requests to
> 300000ms.

provider 请求超时只走运维配置。OpenClaw 配置了 `agents.defaults.musicGenerationModel.timeoutMs` 就用它,低于 120000 毫秒的值抬到 120000;否则 provider 请求默认 300000 毫秒。

## 异步行为

> Session-backed music generation runs as a background task:

会话支撑的音乐生成作为后台任务跑:

> - **Background task:** `music_generate` creates a background task, returns a
>   started/task response immediately, and posts the finished track later in
>   a follow-up agent message.
> - **Duplicate prevention:** while a task is `queued` or `running`, later
>   `music_generate` calls in the same session return task status instead of
>   starting another generation. Use `action: "status"` to check explicitly.
> - **Status lookup:** `openclaw tasks list` or `openclaw tasks show <taskId>`
>   inspects queued, running, and terminal status.
> - **Completion wake:** OpenClaw injects an internal completion event back
>   into the same session so the model can write the user-facing follow-up
>   itself.
> - **Prompt hint:** later user/manual turns in the same session get a small
>   runtime hint when a music task is already in flight, so the model does
>   not blindly call `music_generate` again.
> - **No-session fallback:** direct/local contexts without a real agent
>   session run inline and return the final audio result in the same turn.

- **后台任务**:`music_generate` 建一个后台任务,立刻返回 started/task 响应,曲子好了之后在 agent 跟进消息里贴出来。
- **防重复**:任务在 `queued` 或 `running` 时,同一会话里后续 `music_generate` 调用返回任务状态,而不是再启动一次生成。用 `action: "status"` 显式检查。
- **状态查询**:`openclaw tasks list` 或 `openclaw tasks show <taskId>` 查看排队、运行、终态状态。
- **完成唤醒**:OpenClaw 把内部完成事件注回同一会话,让模型自己写面向用户的跟进。
- **Prompt 提示**:同一会话里之后的用户 / 手动轮次,在音乐任务还在跑时会收到一条小的运行时提示,让模型别盲目再调一次 `music_generate`。
- **无会话回退**:没真实 agent 会话的直接 / 本地上下文里,内联跑,在同一轮里返回最终音频结果。

### 任务生命周期

> | State       | Meaning                                                                                        |

| 状态         | 含义                                                                                       |
| ------------ | ------------------------------------------------------------------------------------------ |
| `queued`     | 任务已建立,等 provider 接收。                                                              |
| `running`    | provider 正在处理(通常 30 秒到 3 分钟,看 provider 和时长)。                              |
| `succeeded`  | 曲子好了;agent 被唤醒并贴到对话里。                                                       |
| `failed`     | provider 错误或超时;agent 被唤醒,带错误细节。                                            |

> Check status from the CLI:

从 CLI 查状态:

```bash
openclaw tasks list
openclaw tasks show <taskId>
openclaw tasks cancel <taskId>
```

## 配置

### 模型选择

```json5
{
  agents: {
    defaults: {
      musicGenerationModel: {
        primary: "google/lyria-3-clip-preview",
        fallbacks: ["fal/fal-ai/minimax-music/v2.6", "minimax/music-2.6"],
      },
    },
  },
}
```

### Provider 选择顺序

> OpenClaw tries providers in this order:

OpenClaw 按这个顺序尝试 provider:

> 1. `model` parameter from the tool call (if the agent specifies one).
> 2. `musicGenerationModel.primary` from config.
> 3. `musicGenerationModel.fallbacks` in order.
> 4. Auto-detection using auth-backed provider defaults only:
>    - current default provider first;
>    - remaining registered music-generation providers in provider-id order.

1. 工具调用里的 `model` 参数(agent 指定时)。
2. 配置里的 `musicGenerationModel.primary`。
3. 配置里的 `musicGenerationModel.fallbacks`,按顺序。
4. 自动识别,只用有认证撑着的 provider 默认:
   - 当前默认 provider 先来;
   - 其余注册过的音乐生成 provider,按 provider id 顺序。

> If a provider fails, the next candidate is tried automatically. If all
> fail, the error includes details from each attempt.

provider 失败时,自动试下一个候选。全部失败时,错误里带每次尝试的细节。

> Set `agents.defaults.mediaGenerationAutoProviderFallback: false` to use only
> explicit `model`, `primary`, and `fallbacks` entries.

设 `agents.defaults.mediaGenerationAutoProviderFallback: false`,就只用显式的 `model`、`primary`、`fallbacks` 条目。

## Provider 说明

> <Accordion title="ComfyUI">
>     Workflow-driven and depends on the configured graph plus node mapping
>     for prompt/output fields. The bundled `comfy` plugin plugs into the
>     shared `music_generate` tool through the music-generation provider
>     registry.

[展开: ComfyUI] 工作流驱动,依赖配置好的图和 prompt / output 字段的节点映射。内置的 `comfy` 插件通过音乐生成 provider 注册表接到共享的 `music_generate` 工具上。

> <Accordion title="fal">
>     Uses fal model endpoints through the shared provider auth path. The
>     bundled provider defaults to `fal-ai/minimax-music/v2.6` and also exposes
>     `fal-ai/ace-step/prompt-to-audio` and
>     `fal-ai/stable-audio-25/text-to-audio` for prompt-to-audio requests.

[展开: fal] 通过共享 provider 认证路径走 fal 模型端点。内置 provider 默认 `fal-ai/minimax-music/v2.6`,也暴露 `fal-ai/ace-step/prompt-to-audio` 和 `fal-ai/stable-audio-25/text-to-audio` 用于 prompt 转音频请求。

> <Accordion title="Google (Lyria 3)">
>     Uses Lyria 3 batch generation. The current bundled flow supports
>     prompt, optional lyrics text, and optional reference images.

[展开: Google (Lyria 3)] 用 Lyria 3 批量生成。当前内置流程支持 prompt、可选歌词文本、可选参考图。

> <Accordion title="MiniMax">
>     Uses the batch `music_generation` endpoint. Supports prompt, optional
>     lyrics, instrumental mode, and mp3 output through either `minimax`
>     API-key auth or `minimax-portal` OAuth.

[展开: MiniMax] 用批量 `music_generation` 端点。支持 prompt、可选歌词、纯乐器模式、mp3 输出;走 `minimax` API key 认证或 `minimax-portal` OAuth 都可以。

> <Accordion title="OpenRouter">
>     Uses OpenRouter chat completions audio output with streaming enabled. The
>     bundled provider defaults to `google/lyria-3-pro-preview` and also exposes
>     `openrouter/google/lyria-3-clip-preview`.

[展开: OpenRouter] 用 OpenRouter chat completions 的音频输出,开了流式。内置 provider 默认 `google/lyria-3-pro-preview`,也暴露 `openrouter/google/lyria-3-clip-preview`。

## 选哪条路径

> - **Shared provider-backed** when you want model selection, provider
>   failover, and the built-in async task/status flow.
> - **Plugin path (ComfyUI)** when you need a custom workflow graph or a
>   provider that is not part of the shared bundled music capability.

- 想要模型选择、provider 故障切换和内置的异步任务 / 状态流程,用**共享 provider 支持**。
- 需要自定义工作流图、或需要某个不在内置共享音乐能力里的 provider,用**插件路径(ComfyUI)**。

> If you are debugging ComfyUI-specific behavior, see
> [ComfyUI](/providers/comfy). If you are debugging shared provider
> behavior, start with [fal](/providers/fal), [Google (Gemini)](/providers/google),
> [MiniMax](/providers/minimax), or [OpenRouter](/providers/openrouter).

排 ComfyUI 专属行为见 [ComfyUI](/providers/comfy)。排共享 provider 行为先看 [fal](/providers/fal)、[Google (Gemini)](/providers/google)、[MiniMax](/providers/minimax)、[OpenRouter](/providers/openrouter)。

## Provider 能力模式

> The shared music-generation contract supports explicit mode declarations:
>
> - `generate` for prompt-only generation.
> - `edit` when the request includes one or more reference images.

共享音乐生成契约支持显式模式声明:

- `generate` 用于仅 prompt 的生成。
- `edit` 用于请求包含一张或多张参考图时。

> New provider implementations should prefer explicit mode blocks:

新 provider 实现应当优先用显式模式块:

```typescript
capabilities: {
  generate: {
    maxTracks: 1,
    supportsLyrics: true,
    supportsFormat: true,
  },
  edit: {
    enabled: true,
    maxTracks: 1,
    maxInputImages: 1,
    supportsFormat: true,
  },
}
```

> Legacy flat fields such as `maxInputImages`, `supportsLyrics`, and
> `supportsFormat` are **not** enough to advertise edit support. Providers
> should declare `generate` and `edit` explicitly so live tests, contract
> tests, and the shared `music_generate` tool can validate mode support
> deterministically.

旧的平铺字段 `maxInputImages`、`supportsLyrics`、`supportsFormat` **不**足以声明编辑支持。provider 应该显式声明 `generate` 和 `edit`,这样实时测试、契约测试、共享 `music_generate` 工具才能确定地校验模式支持。

## 实时测试

> Opt-in live coverage for the shared bundled providers:

共享内置 provider 的可选实时覆盖:

```bash
OPENCLAW_LIVE_TEST=1 pnpm test:live -- extensions/music-generation-providers.live.test.ts
```

> Repo wrapper:

仓库包装:

```bash
pnpm test:live:media music
```

> This live file uses already-exported provider env vars ahead of stored auth
> profiles by default, and runs both `generate` and declared `edit` coverage when
> the provider enables edit mode. Coverage today:

这份实时文件默认优先用已经导出的 provider 环境变量,而不是存储的认证 profile;provider 开了编辑模式时,同时跑 `generate` 和声明的 `edit` 覆盖。今天的覆盖:

> - `google`: `generate` plus `edit`
> - `fal`: `generate` only
> - `minimax`: `generate` only
> - `openrouter`: `generate` plus `edit`
> - `comfy`: separate Comfy live coverage, not the shared provider sweep

- `google`:`generate` 加 `edit`
- `fal`:仅 `generate`
- `minimax`:仅 `generate`
- `openrouter`:`generate` 加 `edit`
- `comfy`:独立的 Comfy 实时覆盖,不在共享 provider 扫描里

> Opt-in live coverage for the bundled ComfyUI music path:

内置 ComfyUI 音乐路径的可选实时覆盖:

```bash
OPENCLAW_LIVE_TEST=1 COMFY_LIVE_TEST=1 pnpm test:live -- extensions/comfy/comfy.live.test.ts
```

> The Comfy live file also covers comfy image and video workflows when those
> sections are configured.

Comfy 实时文件也覆盖配置好的 comfy 图片和视频工作流。

## 相关

> - [Background tasks](/automation/tasks) — task tracking for detached `music_generate` runs
> - [ComfyUI](/providers/comfy)
> - [Configuration reference](/gateway/config-agents#agent-defaults) — `musicGenerationModel` config
> - [Google (Gemini)](/providers/google)
> - [MiniMax](/providers/minimax)
> - [Models](/concepts/models) — model configuration and failover
> - [Tools overview](/tools)

- [后台任务](/automation/tasks) —— 异步 `music_generate` 运行的任务跟踪
- [ComfyUI](/providers/comfy)
- [配置参考](/gateway/config-agents#agent-defaults) ——`musicGenerationModel` 配置
- [Google (Gemini)](/providers/google)
- [MiniMax](/providers/minimax)
- [模型](/concepts/models) —— 模型配置和故障切换
- [工具总览](/tools)
