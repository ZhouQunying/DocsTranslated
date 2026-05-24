# Image generation

> The `image_generate` tool lets the agent create and edit images using your
> configured providers. In chat sessions, image generation runs asynchronously:
> OpenClaw records a background task, returns the task id immediately, and wakes
> the agent when the provider finishes. The completion agent must send generated
> images through the `message` tool. If the requester session is inactive and
> some generated images are still missing from message-tool delivery, OpenClaw
> sends an idempotent direct fallback with only the missing images.

`image_generate` 工具让 agent 用你配置好的 provider 生成和编辑图片。聊天会话里,图片生成是异步的:OpenClaw 记一份后台任务,立刻返回任务 id,provider 完成时再唤醒 agent。完成时 agent 必须通过 `message` 工具把生成的图片发出去。请求方会话不活跃、message 工具还没把某些生成图片送达时,OpenClaw 会发一次幂等的直接回退,只包含缺的那部分图片。

> <Note>
> The tool only appears when at least one image-generation provider is
> available. If you do not see `image_generate` in your agent's tools,
> configure `agents.defaults.imageGenerationModel`, set up a provider API key,
> or sign in with OpenAI Codex OAuth.
> </Note>

[展开: 注意] 只有至少一个图片生成 provider 可用时,工具才出现。你 agent 的工具列表里看不到 `image_generate` 的话,配 `agents.defaults.imageGenerationModel`、设一个 provider API key,或者用 OpenAI Codex OAuth 登录。

## 快速开始

> <Step title="Configure auth">
>     Set an API key for at least one provider (for example `OPENAI_API_KEY`,
>     `GEMINI_API_KEY`, `OPENROUTER_API_KEY`) or sign in with OpenAI Codex OAuth.

[步骤 1: 配认证] 给至少一个 provider 设 API key(如 `OPENAI_API_KEY`、`GEMINI_API_KEY`、`OPENROUTER_API_KEY`),或用 OpenAI Codex OAuth 登录。

> <Step title="Pick a default model (optional)">

[步骤 2: 选个默认模型(可选)]

```json5
{
  agents: {
    defaults: {
      imageGenerationModel: {
        primary: "openai/gpt-image-2",
        timeoutMs: 180_000,
      },
    },
  },
}
```

> Codex OAuth uses the same `openai/gpt-image-2` model ref. When an
> `openai-codex` OAuth profile is configured, OpenClaw routes image
> requests through that OAuth profile instead of first trying
> `OPENAI_API_KEY`. Explicit `models.providers.openai` config (API key,
> custom/Azure base URL) opts back into the direct OpenAI Images API
> route.

Codex OAuth 用同一个 `openai/gpt-image-2` 模型 ref。配了 `openai-codex` OAuth profile 时,OpenClaw 把图片请求走那个 OAuth profile,而不是先尝试 `OPENAI_API_KEY`。显式配置 `models.providers.openai`(API key、自定义 baseUrl、Azure 端点)能切回直连 OpenAI Images API 的路径。

> <Step title="Ask the agent">
>     _"Generate an image of a friendly robot mascot."_

[步骤 3: 让 agent 干活] _"生成一张友好的机器人吉祥物图片。"_

> The agent calls `image_generate` automatically. No tool allow-listing
> needed - it is enabled by default when a provider is available. The tool
> returns a background task id, then the completion agent sends the generated
> attachment through the `message` tool when it is ready.

agent 自动调 `image_generate`。不需要把工具加进 allow 列表 —— provider 可用时默认就开。工具返回一个后台任务 id,准备好之后完成 agent 通过 `message` 工具把生成的附件发出去。

> <Warning>
> For OpenAI-compatible LAN endpoints such as LocalAI, keep the custom
> `models.providers.openai.baseUrl` and explicitly opt in with
> `browser.ssrfPolicy.dangerouslyAllowPrivateNetwork: true`. Private and
> internal image endpoints remain blocked by default.
> </Warning>

[展开: 警告] LocalAI 这种 OpenAI 兼容的局域网端点,保留自定义 `models.providers.openai.baseUrl`,并显式设 `browser.ssrfPolicy.dangerouslyAllowPrivateNetwork: true`。私网和内网图片端点默认仍被拦截。

## 常用路径

> | Goal                                                 | Model ref                                          | Auth                                   |

| 目的                                              | 模型 ref                                            | 认证                                       |
| ------------------------------------------------- | --------------------------------------------------- | ------------------------------------------ |
| OpenAI 图片生成,API 计费                          | `openai/gpt-image-2`                                | `OPENAI_API_KEY`                           |
| OpenAI 图片生成,Codex 订阅认证                    | `openai/gpt-image-2`                                | OpenAI Codex OAuth                         |
| OpenAI 透明背景 PNG / WebP                        | `openai/gpt-image-1.5`                              | `OPENAI_API_KEY` 或 OpenAI Codex OAuth     |
| DeepInfra 图片生成                                | `deepinfra/black-forest-labs/FLUX-1-schnell`        | `DEEPINFRA_API_KEY`                        |
| OpenRouter 图片生成                               | `openrouter/google/gemini-3.1-flash-image-preview`  | `OPENROUTER_API_KEY`                       |
| LiteLLM 图片生成                                  | `litellm/gpt-image-2`                               | `LITELLM_API_KEY`                          |
| Google Gemini 图片生成                            | `google/gemini-3.1-flash-image-preview`             | `GEMINI_API_KEY` 或 `GOOGLE_API_KEY`       |

> The same `image_generate` tool handles text-to-image and reference-image
> editing. Use `image` for one reference or `images` for multiple references.
> Provider-supported output hints such as `quality`, `outputFormat`, and
> `background` are forwarded when available and reported as ignored when a
> provider does not support them. Bundled transparent-background support is
> OpenAI-specific; other providers may still preserve PNG alpha if their
> backend emits it.

同一个 `image_generate` 工具同时处理文生图和参考图编辑。一张参考图用 `image`,多张参考图用 `images`。provider 支持的输出提示(`quality`、`outputFormat`、`background`)在可用时透传过去,provider 不支持时在结果里报告被忽略。内置的透明背景支持是 OpenAI 专属;其他 provider 的后端如果自己输出 PNG alpha,可能还是会保留。

## 支持的 provider

> | Provider   | Default model                           | Edit support                       | Auth                                                  |

| Provider   | 默认模型                                  | 编辑支持                              | 认证                                                       |
| ---------- | ----------------------------------------- | ------------------------------------- | ---------------------------------------------------------- |
| ComfyUI    | `workflow`                                | 支持(1 张图,workflow 控制)        | `COMFY_API_KEY` 或云的 `COMFY_CLOUD_API_KEY`               |
| DeepInfra  | `black-forest-labs/FLUX-1-schnell`        | 支持(1 张图)                       | `DEEPINFRA_API_KEY`                                        |
| fal        | `fal-ai/flux/dev`                         | 支持(模型有各自上限)               | `FAL_KEY`                                                  |
| Google     | `gemini-3.1-flash-image-preview`          | 支持                                  | `GEMINI_API_KEY` 或 `GOOGLE_API_KEY`                       |
| LiteLLM    | `gpt-image-2`                             | 支持(最多 5 张输入图)              | `LITELLM_API_KEY`                                          |
| MiniMax    | `image-01`                                | 支持(主题参考)                     | `MINIMAX_API_KEY` 或 MiniMax OAuth(`minimax-portal`)     |
| OpenAI     | `gpt-image-2`                             | 支持(最多 4 张图)                  | `OPENAI_API_KEY` 或 OpenAI Codex OAuth                     |
| OpenRouter | `google/gemini-3.1-flash-image-preview`   | 支持(最多 5 张输入图)              | `OPENROUTER_API_KEY`                                       |
| Vydra      | `grok-imagine`                            | 不支持                                | `VYDRA_API_KEY`                                            |
| xAI        | `grok-imagine-image`                      | 支持(最多 5 张图)                  | `XAI_API_KEY`                                              |

> Use `action: "list"` to inspect available providers and models at runtime:

运行时用 `action: "list"` 查看可用的 provider 和模型:

```text
/tool image_generate action=list
```

> Use `action: "status"` to inspect the active image-generation task for the
> current session:

用 `action: "status"` 查看当前会话活跃的图片生成任务:

```text
/tool image_generate action=status
```

## Provider 能力

> | Capability            | ComfyUI            | DeepInfra | fal                       | Google         | MiniMax               | OpenAI         | Vydra | xAI            |

| 能力                       | ComfyUI               | DeepInfra | fal                          | Google     | MiniMax              | OpenAI     | Vydra | xAI       |
| -------------------------- | --------------------- | --------- | ---------------------------- | ---------- | -------------------- | ---------- | ----- | --------- |
| 生成(单次最多)           | workflow 决定        | 4         | 4                            | 4          | 9                    | 4          | 1     | 4         |
| 编辑 / 参考图              | 1 张(workflow)     | 1 张      | Flux: 1;GPT: 10;NB2: 14   | 最多 5 张  | 1 张(主题参考)     | 最多 5 张  | -     | 最多 5 张 |
| 尺寸控制                   | -                     | ✓         | ✓                            | ✓          | -                    | 最高 4K    | -     | -         |
| 宽高比                     | -                     | -         | ✓                            | ✓          | ✓                    | -          | -     | ✓         |
| 分辨率(1K/2K/4K)         | -                     | -         | ✓                            | ✓          | -                    | -          | -     | 1K、2K    |

## 工具参数

> `prompt` (string, required) — Image generation prompt. Required for `action: "generate"`.

`prompt`(string,必填)—— 图片生成 prompt。`action: "generate"` 时必填。

> `action` (`"generate" | "status" | "list"`, default: generate) — Use `"status"` to inspect the active session task or `"list"` to inspect available providers and models at runtime.

`action`(`"generate" | "status" | "list"`,默认 generate)—— `"status"` 查看当前会话活跃任务;`"list"` 运行时查看可用 provider 和模型。

> `model` (string) — Provider/model override (e.g. `openai/gpt-image-2`). Use `openai/gpt-image-1.5` for transparent OpenAI backgrounds.

`model`(string)—— provider/模型覆盖(如 `openai/gpt-image-2`)。OpenAI 透明背景用 `openai/gpt-image-1.5`。

> `image` (string) — Single reference image path or URL for edit mode.

`image`(string)—— 编辑模式的单张参考图路径或 URL。

> `images` (string[]) — Multiple reference images for edit mode (up to 5 on supporting providers).

`images`(string[])—— 编辑模式的多张参考图(支持的 provider 上最多 5 张)。

> `size` (string) — Size hint: `1024x1024`, `1536x1024`, `1024x1536`, `2048x2048`, `3840x2160`.

`size`(string)—— 尺寸提示:`1024x1024`、`1536x1024`、`1024x1536`、`2048x2048`、`3840x2160`。

> `aspectRatio` (string) — Aspect ratio: `1:1`, `2:3`, `3:2`, `3:4`, `4:3`, `4:5`, `5:4`, `9:16`, `16:9`, `21:9`.

`aspectRatio`(string)—— 宽高比:`1:1`、`2:3`、`3:2`、`3:4`、`4:3`、`4:5`、`5:4`、`9:16`、`16:9`、`21:9`。

> `resolution` (`"1K" | "2K" | "4K"`) — Resolution hint.

`resolution`(`"1K" | "2K" | "4K"`)—— 分辨率提示。

> `quality` (`"low" | "medium" | "high" | "auto"`) — Quality hint when the provider supports it.

`quality`(`"low" | "medium" | "high" | "auto"`)—— provider 支持时的质量提示。

> `outputFormat` (`"png" | "jpeg" | "webp"`) — Output format hint when the provider supports it.

`outputFormat`(`"png" | "jpeg" | "webp"`)—— provider 支持时的输出格式提示。

> `background` (`"transparent" | "opaque" | "auto"`) — Background hint when the provider supports it. Use `transparent` with `outputFormat: "png"` or `"webp"` for transparency-capable providers.

`background`(`"transparent" | "opaque" | "auto"`)—— provider 支持时的背景提示。支持透明的 provider 上,`transparent` 跟 `outputFormat: "png"` 或 `"webp"` 一起用。

> `count` (number) — Number of images to generate (1-4).

`count`(number)—— 要生成的图片数(1-4)。

> `timeoutMs` (number) — Optional provider request timeout in milliseconds. When Codex calls `image_generate` through dynamic tools, this per-call value still overrides the configured default and is capped at 600000 ms.

`timeoutMs`(number)—— 可选的 provider 请求超时(毫秒)。Codex 通过动态工具调 `image_generate` 时,这个单次调用值仍能覆盖配置默认,上限 600000 毫秒。

> `filename` (string) — Output filename hint.

`filename`(string)—— 输出文件名提示。

> `openai` (object) — OpenAI-only hints: `background`, `moderation`, `outputCompression`, and `user`.

`openai`(object)—— 仅 OpenAI 的提示:`background`、`moderation`、`outputCompression`、`user`。

> <Note>
> Not all providers support all parameters. When a fallback provider supports a
> nearby geometry option instead of the exact requested one, OpenClaw remaps to
> the closest supported size, aspect ratio, or resolution before submission.
> Unsupported output hints are dropped for providers that do not declare
> support and reported in the tool result. Tool results report the applied
> settings; `details.normalization` captures any requested-to-applied
> translation.
> </Note>

[展开: 注意] 不是每个 provider 都支持所有参数。回退 provider 支持的几何选项跟请求的不完全一致时,OpenClaw 在提交前重映射到最接近的尺寸、宽高比或分辨率。不支持的输出提示在没声明支持的 provider 上会被丢弃,并在工具结果里报告。工具结果会报告实际应用的设置;`details.normalization` 记录"请求到实际应用"的映射。

## 配置

### 模型选择

```json5
{
  agents: {
    defaults: {
      imageGenerationModel: {
        primary: "openai/gpt-image-2",
        timeoutMs: 180_000,
        fallbacks: [
          "openrouter/google/gemini-3.1-flash-image-preview",
          "google/gemini-3.1-flash-image-preview",
          "fal/fal-ai/flux/dev",
        ],
      },
    },
  },
}
```

### Provider 选择顺序

> OpenClaw tries providers in this order:

OpenClaw 按这个顺序尝试 provider:

> 1. **`model` parameter** from the tool call (if the agent specifies one).
> 2. **`imageGenerationModel.primary`** from config.
> 3. **`imageGenerationModel.fallbacks`** in order.
> 4. **Auto-detection** - auth-backed provider defaults only:
>    - current default provider first;
>    - remaining registered image-generation providers in provider-id order.

1. 工具调用里的 **`model` 参数**(agent 指定时)。
2. 配置里的 **`imageGenerationModel.primary`**。
3. 配置里的 **`imageGenerationModel.fallbacks`**,按顺序。
4. **自动识别** —— 只用有认证撑着的 provider 默认:
   - 当前默认 provider 先来;
   - 其余注册过的图片生成 provider,按 provider id 顺序。

> If a provider fails (auth error, rate limit, etc.), the next configured
> candidate is tried automatically. If all fail, the error includes details
> from each attempt.

provider 失败(认证错误、限速等),自动尝试下一个候选。全部失败时,错误里带每次尝试的细节。

> <Accordion title="Per-call model overrides are exact">
>     A per-call `model` override tries only that provider/model and does
>     not continue to configured primary/fallback or auto-detected providers.

[展开: 单次调用的模型覆盖是精确的] 单次调用的 `model` 覆盖只试那个 provider/模型,不会继续走配置的 primary/fallback 或自动识别 provider。

> <Accordion title="Auto-detection is auth-aware">
>     A provider default only enters the candidate list when OpenClaw can
>     actually authenticate that provider. Set
>     `agents.defaults.mediaGenerationAutoProviderFallback: false` to use only
>     explicit `model`, `primary`, and `fallbacks` entries.

[展开: 自动识别感知认证] 只有 OpenClaw 真能认证那个 provider 时,这个 provider 默认才会进候选列表。设 `agents.defaults.mediaGenerationAutoProviderFallback: false`,就只用显式的 `model`、`primary`、`fallbacks` 条目。

> <Accordion title="Timeouts">
>     Set `agents.defaults.imageGenerationModel.timeoutMs` for slow image
>     backends. A per-call `timeoutMs` tool parameter overrides the configured
>     default, and configured defaults override plugin-authored provider
>     defaults. Google and OpenRouter hosted image providers use 180 second
>     defaults; xAI and Azure OpenAI image generation use 600 seconds. Codex
>     dynamic-tool calls use a 120 second `image_generate` bridge default and
>     honor the same timeout budget when configured, bounded by OpenClaw's 600000
>     ms dynamic-tool bridge maximum.

[展开: 超时] 慢的图片后端,设 `agents.defaults.imageGenerationModel.timeoutMs`。单次调用的 `timeoutMs` 工具参数覆盖配置默认;配置默认覆盖插件作者写的 provider 默认。Google 和 OpenRouter 的托管图片 provider 默认 180 秒;xAI 和 Azure OpenAI 图片生成默认 600 秒。Codex 动态工具调用 `image_generate` 桥默认 120 秒,配置时也遵守同一份超时预算,上限 OpenClaw 动态工具桥的 600000 毫秒。

> <Accordion title="Inspect at runtime">
>     Use `action: "list"` to inspect the currently registered providers,
>     their default models, and auth env-var hints.

[展开: 运行时查看] 用 `action: "list"` 查看当前注册的 provider、各自的默认模型,以及认证环境变量提示。

### 图片编辑

> OpenAI, OpenRouter, Google, DeepInfra, fal, MiniMax, ComfyUI, and xAI support editing
> reference images. Pass a reference image path or URL:

OpenAI、OpenRouter、Google、DeepInfra、fal、MiniMax、ComfyUI、xAI 都支持编辑参考图。传一张参考图路径或 URL:

```text
"Generate a watercolor version of this photo" + image: "/path/to/photo.jpg"
```

> OpenAI, OpenRouter, Google, and xAI support up to 5 reference images via the
> `images` parameter. fal supports 1 reference image for Flux image-to-image, up
> to 10 for GPT Image 2 edits, and up to 14 for Nano Banana 2 edits. MiniMax and
> ComfyUI support 1.

OpenAI、OpenRouter、Google、xAI 通过 `images` 参数最多支持 5 张参考图。fal 给 Flux 图生图支持 1 张参考图;给 GPT Image 2 编辑最多 10 张;给 Nano Banana 2 编辑最多 14 张。MiniMax 和 ComfyUI 支持 1 张。

## Provider 深入

> <Accordion title="OpenAI gpt-image-2 (and gpt-image-1.5)">
>     OpenAI image generation defaults to `openai/gpt-image-2`. If an
>     `openai-codex` OAuth profile is configured, OpenClaw reuses the same
>     OAuth profile used by Codex subscription chat models and sends the
>     image request through the Codex Responses backend. Legacy Codex base
>     URLs such as `https://chatgpt.com/backend-api` are canonicalized to
>     `https://chatgpt.com/backend-api/codex` for image requests. OpenClaw
>     does **not** silently fall back to `OPENAI_API_KEY` for that request -
>     to force direct OpenAI Images API routing, configure
>     `models.providers.openai` explicitly with an API key, custom base URL,
>     or Azure endpoint.

[展开: OpenAI gpt-image-2(以及 gpt-image-1.5)] OpenAI 图片生成默认 `openai/gpt-image-2`。配了 `openai-codex` OAuth profile 时,OpenClaw 复用 Codex 订阅聊天模型在用的同一份 OAuth profile,把图片请求发到 Codex Responses 后端。旧的 Codex baseUrl(如 `https://chatgpt.com/backend-api`)在图片请求上会归一化成 `https://chatgpt.com/backend-api/codex`。OpenClaw **不**会为这个请求默默回退到 `OPENAI_API_KEY` —— 要强制走直连 OpenAI Images API,显式配置 `models.providers.openai`,带 API key、自定义 baseUrl,或 Azure 端点。

> The `openai/gpt-image-1.5`, `openai/gpt-image-1`, and
> `openai/gpt-image-1-mini` models can still be selected explicitly. Use
> `gpt-image-1.5` for transparent-background PNG/WebP output; the current
> `gpt-image-2` API rejects `background: "transparent"`.

`openai/gpt-image-1.5`、`openai/gpt-image-1`、`openai/gpt-image-1-mini` 仍可显式选用。透明背景的 PNG / WebP 输出用 `gpt-image-1.5`;当前 `gpt-image-2` API 拒绝 `background: "transparent"`。

> `gpt-image-2` supports both text-to-image generation and
> reference-image editing through the same `image_generate` tool.
> OpenClaw forwards `prompt`, `count`, `size`, `quality`, `outputFormat`,
> and reference images to OpenAI. OpenAI does **not** receive
> `aspectRatio` or `resolution` directly; when possible OpenClaw maps
> those into a supported `size`, otherwise the tool reports them as
> ignored overrides.

`gpt-image-2` 通过同一个 `image_generate` 工具支持文生图和参考图编辑。OpenClaw 把 `prompt`、`count`、`size`、`quality`、`outputFormat`、参考图都转发给 OpenAI。OpenAI **不**直接收到 `aspectRatio` 或 `resolution`;可能时 OpenClaw 把它们映射成支持的 `size`,否则工具把它们报告为被忽略的覆盖。

> OpenAI-specific options live under the `openai` object:

OpenAI 专属选项放在 `openai` 对象下:

```json
{
  "quality": "low",
  "outputFormat": "jpeg",
  "openai": {
    "background": "opaque",
    "moderation": "low",
    "outputCompression": 60,
    "user": "end-user-42"
  }
}
```

> `openai.background` accepts `transparent`, `opaque`, or `auto`;
> transparent outputs require `outputFormat` `png` or `webp` and a
> transparency-capable OpenAI image model. OpenClaw routes default
> `gpt-image-2` transparent-background requests to `gpt-image-1.5`.
> `openai.outputCompression` applies to JPEG/WebP outputs and is ignored
> for PNG outputs.

`openai.background` 接受 `transparent`、`opaque`、`auto`;透明输出要求 `outputFormat` 是 `png` 或 `webp`,且 OpenAI 图片模型支持透明。OpenClaw 把默认 `gpt-image-2` 的透明背景请求路由到 `gpt-image-1.5`。`openai.outputCompression` 对 JPEG/WebP 输出生效,PNG 输出忽略。

> The top-level `background` hint is provider-neutral and currently maps
> to the same OpenAI `background` request field when the OpenAI provider
> is selected. Providers that do not declare background support return
> it in `ignoredOverrides` instead of receiving the unsupported parameter.

顶层 `background` 提示跟 provider 无关,选了 OpenAI provider 时,当前映射到同一份 OpenAI `background` 请求字段。没声明背景支持的 provider 把它放进 `ignoredOverrides`,不会收到这个不支持的参数。

> To route OpenAI image generation through an Azure OpenAI deployment
> instead of `api.openai.com`, see
> [Azure OpenAI endpoints](/providers/openai#azure-openai-endpoints).

要把 OpenAI 图片生成走 Azure OpenAI 部署,不走 `api.openai.com`,见 [Azure OpenAI 端点](/providers/openai#azure-openai-endpoints)。

> <Accordion title="OpenRouter image models">
>     OpenRouter image generation uses the same `OPENROUTER_API_KEY` and
>     routes through OpenRouter's chat completions image API. Select
>     OpenRouter image models with the `openrouter/` prefix:

[展开: OpenRouter 图片模型] OpenRouter 图片生成用同一个 `OPENROUTER_API_KEY`,走 OpenRouter 的 chat completions 图片 API。用 `openrouter/` 前缀选 OpenRouter 图片模型:

```json5
{
  agents: {
    defaults: {
      imageGenerationModel: {
        primary: "openrouter/google/gemini-3.1-flash-image-preview",
      },
    },
  },
}
```

> OpenClaw forwards `prompt`, `count`, reference images, and
> Gemini-compatible `aspectRatio` / `resolution` hints to OpenRouter.
> Current built-in OpenRouter image model shortcuts include
> `google/gemini-3.1-flash-image-preview`,
> `google/gemini-3-pro-image-preview`, and `openai/gpt-5.4-image-2`. Use
> `action: "list"` to see what your configured plugin exposes.

OpenClaw 把 `prompt`、`count`、参考图,以及兼容 Gemini 的 `aspectRatio` / `resolution` 提示转发给 OpenRouter。当前内置的 OpenRouter 图片模型快捷方式包括 `google/gemini-3.1-flash-image-preview`、`google/gemini-3-pro-image-preview`、`openai/gpt-5.4-image-2`。用 `action: "list"` 看你装的插件暴露了什么。

> <Accordion title="MiniMax dual-auth">
>     MiniMax image generation is available through both bundled MiniMax
>     auth paths:
>
>     - `minimax/image-01` for API-key setups
>     - `minimax-portal/image-01` for OAuth setups

[展开: MiniMax 双认证] MiniMax 图片生成在内置的两条 MiniMax 认证路径上都可用:

- API key 部署用 `minimax/image-01`
- OAuth 部署用 `minimax-portal/image-01`

> <Accordion title="xAI grok-imagine-image">
>     The bundled xAI provider uses `/v1/images/generations` for prompt-only
>     requests and `/v1/images/edits` when `image` or `images` is present.

[展开: xAI grok-imagine-image] 内置 xAI provider 对仅 prompt 的请求用 `/v1/images/generations`,带 `image` 或 `images` 时用 `/v1/images/edits`。

> - Models: `xai/grok-imagine-image`, `xai/grok-imagine-image-quality`
> - Count: up to 4
> - References: one `image` or up to five `images`
> - Aspect ratios: `1:1`, `16:9`, `9:16`, `4:3`, `3:4`, `2:3`, `3:2`
> - Resolutions: `1K`, `2K`
> - Outputs: returned as OpenClaw-managed image attachments

- 模型:`xai/grok-imagine-image`、`xai/grok-imagine-image-quality`
- 数量:最多 4 张
- 参考图:一张 `image` 或最多五张 `images`
- 宽高比:`1:1`、`16:9`、`9:16`、`4:3`、`3:4`、`2:3`、`3:2`
- 分辨率:`1K`、`2K`
- 输出:作为 OpenClaw 管理的图片附件返回

> OpenClaw intentionally does not expose xAI-native `quality`, `mask`,
> `user`, or extra native-only aspect ratios until those controls exist
> in the shared cross-provider `image_generate` contract.

OpenClaw 刻意不暴露 xAI 原生的 `quality`、`mask`、`user`,以及额外的仅原生的宽高比 —— 等到跨 provider 共享的 `image_generate` 契约里有这些控件再说。

## 例子

> <Tab title="Generate (4K landscape)">

[标签: 生成(4K 横向)]

```text
/tool image_generate action=generate model=openai/gpt-image-2 prompt="A clean editorial poster for OpenClaw image generation" size=3840x2160 count=1
```

> <Tab title="Generate (transparent PNG)">

[标签: 生成(透明 PNG)]

```text
/tool image_generate action=generate model=openai/gpt-image-1.5 prompt="A simple red circle sticker on a transparent background" outputFormat=png background=transparent
```

> Equivalent CLI:

等价 CLI:

```bash
openclaw infer image generate \
  --model openai/gpt-image-1.5 \
  --output-format png \
  --background transparent \
  --prompt "A simple red circle sticker on a transparent background" \
  --json
```

> <Tab title="Generate (two square)">

[标签: 生成(两张方形)]

```text
/tool image_generate action=generate model=openai/gpt-image-2 prompt="Two visual directions for a calm productivity app icon" size=1024x1024 count=2
```

> <Tab title="Edit (one reference)">

[标签: 编辑(一张参考图)]

```text
/tool image_generate action=generate model=openai/gpt-image-2 prompt="Keep the subject, replace the background with a bright studio setup" image=/path/to/reference.png size=1024x1536
```

> <Tab title="Edit (multiple references)">

[标签: 编辑(多张参考图)]

```text
/tool image_generate action=generate model=openai/gpt-image-2 prompt="Combine the character identity from the first image with the color palette from the second" images='["/path/to/character.png","/path/to/palette.jpg"]' size=1536x1024
```

> The same `--output-format` and `--background` flags are available on
> `openclaw infer image edit`; `--openai-background` remains as an
> OpenAI-specific alias. Bundled providers other than OpenAI do not declare
> explicit background control today, so `background: "transparent"` is reported
> as ignored for them.

同样的 `--output-format` 和 `--background` 参数在 `openclaw infer image edit` 上也有;`--openai-background` 仍作为 OpenAI 专属别名。除了 OpenAI 之外的内置 provider 今天没声明显式的背景控制,所以 `background: "transparent"` 在它们上会报告为被忽略。

## 相关

> - [Tools overview](/tools) - all available agent tools
> - [ComfyUI](/providers/comfy) - local ComfyUI and Comfy Cloud workflow setup
> - [fal](/providers/fal) - fal image and video provider setup
> - [Google (Gemini)](/providers/google) - Gemini image provider setup
> - [MiniMax](/providers/minimax) - MiniMax image provider setup
> - [OpenAI](/providers/openai) - OpenAI Images provider setup
> - [Vydra](/providers/vydra) - Vydra image, video, and speech setup
> - [xAI](/providers/xai) - Grok image, video, search, code execution, and TTS setup
> - [Configuration reference](/gateway/config-agents#agent-defaults) - `imageGenerationModel` config
> - [Models](/concepts/models) - model configuration and failover

- [工具总览](/tools) —— 全部可用 agent 工具
- [ComfyUI](/providers/comfy) —— 本地 ComfyUI 和 Comfy Cloud workflow 配置
- [fal](/providers/fal) —— fal 图片和视频 provider 配置
- [Google (Gemini)](/providers/google) —— Gemini 图片 provider 配置
- [MiniMax](/providers/minimax) —— MiniMax 图片 provider 配置
- [OpenAI](/providers/openai) —— OpenAI Images provider 配置
- [Vydra](/providers/vydra) —— Vydra 图片、视频、语音配置
- [xAI](/providers/xai) —— Grok 图片、视频、搜索、code execution、TTS 配置
- [配置参考](/gateway/config-agents#agent-defaults) ——`imageGenerationModel` 配置
- [模型](/concepts/models) —— 模型配置和故障切换
