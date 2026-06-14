# 插件清单

## 架构精读

> 跳过不影响阅读翻译正文。

### 为什么生成这个页面而不是手动维护？

手动维护插件列表会立刻腐化——新插件加入、旧插件改名、描述过时。OpenClaw 的做法是从 `extensions/*/package.json` 和 `openclaw.plugin.json` 自动生成这个页面，就像 OpenAPI 规范自动生成客户端 SDK——单一事实源，生成产物永远跟代码同步。运行 `pnpm plugins:inventory:gen` 就能重新生成。好处是文档不会跟代码脱节，坏处是格式受限于生成器能力，手动排版做不到。

三个分发层级。核心 npm 包随 `openclaw` 一起发布，无需额外安装。官方外部包由 OpenClaw 维护但不进核心包，通过 ClawHub/npm 按需安装。仅源码检出是仓库本地插件，不发布也不作为可安装包推广。就像 Docker 镜像分层——基础层（核心）、官方镜像（外部）、本地构建（源码）。

---

这个页面从 `extensions/*/package.json`、`openclaw.plugin.json` 和根 npm 包 `files` 排除列表生成。重新生成：

```bash
pnpm plugins:inventory:gen
```

## 定义

- **核心 npm 包：** 内置在 `openclaw` npm 包中，无需单独安装插件。
- **官方外部包：** OpenClaw 维护但从核心 npm 包中省略的插件，保留在此官方清单中，通过 ClawHub 和/或 npm 按需安装。
- **仅源码检出：** 仓库本地插件，从已发布 npm 产物中省略，不作为可安装包推广。

源码检出与 npm 安装不同：`pnpm install` 后，捆绑插件从 `extensions/<id>` 加载，这样本地编辑和包本地工作区依赖可用。

## 安装插件

使用每个条目中的安装路由决定是否需要安装。标注 `included in OpenClaw` 的插件已存在于核心包中。官方外部包需要一次安装，然后重启 Gateway。

例如，Discord 是官方外部包：

```bash
openclaw plugins install @openclaw/discord
openclaw gateway restart
openclaw plugins inspect discord --runtime --json
```

在启动切换期间，普通裸包 spec 仍从 npm 安装。需要显式来源时用 `clawhub:@openclaw/discord` 或 `npm:@openclaw/discord`。安装后按插件的 setup 文档（如 [Discord](/channels/discord)）添加凭证和 channel 配置。参见 [Manage plugins](/plugins/manage-plugins) 了解更新、卸载和发布命令。

每个条目列出包名、分发路由和描述。

## 核心 npm 包

90 个插件

- **[admin-http-rpc](/plugins/reference/admin-http-rpc)** (`@openclaw/admin-http-rpc`)——已包含在 OpenClaw 中。OpenClaw admin HTTP RPC 端点。
- **[alibaba](/plugins/reference/alibaba)** (`@openclaw/alibaba-provider`)——已包含在 OpenClaw 中。添加视频生成 provider 支持。
- **[anthropic](/plugins/reference/anthropic)** (`@openclaw/anthropic-provider`)——已包含在 OpenClaw 中。为 OpenClaw 添加 Anthropic 模型 provider 支持。
- **[arcee](/plugins/reference/arcee)** (`@openclaw/arcee-provider`)——已包含在 OpenClaw 中。添加 Arcee 模型 provider 支持。
- **[azure-speech](/plugins/reference/azure-speech)** (`@openclaw/azure-speech`)——已包含在 OpenClaw 中。Azure AI Speech 文字转语音（MP3、原生 Ogg/Opus 语音笔记、PCM 电话）。
- **[bonjour](/plugins/reference/bonjour)** (`@openclaw/bonjour`)——已包含在 OpenClaw 中。通过 Bonjour/mDNS 广播本地 OpenClaw gateway。
- **[browser](/plugins/reference/browser)** (`@openclaw/browser-plugin`)——已包含在 OpenClaw 中。添加 agent 可调用工具。
- **[byteplus](/plugins/reference/byteplus)** (`@openclaw/byteplus-provider`)——已包含在 OpenClaw 中。添加 BytePlus、BytePlus Plan 模型 provider 支持。
- **[canvas](/plugins/reference/canvas)** (`@openclaw/canvas-plugin`)——已包含在 OpenClaw 中。实验性 Canvas 控制和 A2UI 渲染表面。
- **[cerebras](/plugins/reference/cerebras)** (`@openclaw/cerebras-provider`)——已包含在 OpenClaw 中。添加 Cerebras 模型 provider 支持。
- **[chutes](/plugins/reference/chutes)** (`@openclaw/chutes-provider`)——已包含在 OpenClaw 中。添加 Chutes 模型 provider 支持。
- **[clickclack](/plugins/reference/clickclack)** (`@openclaw/clickclack`)——已包含在 OpenClaw 中。添加 Clickclack channel 表面。
- **[cloudflare-ai-gateway](/plugins/reference/cloudflare-ai-gateway)** (`@openclaw/cloudflare-ai-gateway-provider`)——已包含在 OpenClaw 中。添加 Cloudflare AI Gateway 模型 provider 支持。
- **[codex-supervisor](/plugins/reference/codex-supervisor)** (`@openclaw/codex-supervisor`)——已包含在 OpenClaw 中。从 OpenClaw 监督 Codex app-server 会话。
- **[comfy](/plugins/reference/comfy)** (`@openclaw/comfy-provider`)——已包含在 OpenClaw 中。添加 ComfyUI 模型 provider 支持。
- **[copilot-proxy](/plugins/reference/copilot-proxy)** (`@openclaw/copilot-proxy`)——已包含在 OpenClaw 中。添加 Copilot Proxy 模型 provider 支持。
- **[deepgram](/plugins/reference/deepgram)** (`@openclaw/deepgram-provider`)——已包含在 OpenClaw 中。添加媒体理解 provider 和实时转录 provider 支持。
- **[deepinfra](/plugins/reference/deepinfra)** (`@openclaw/deepinfra-provider`)——已包含在 OpenClaw 中。添加 DeepInfra 模型 provider 支持。
- **[deepseek](/plugins/reference/deepseek)** (`@openclaw/deepseek-provider`)——已包含在 OpenClaw 中。添加 DeepSeek 模型 provider 支持。
- **[document-extract](/plugins/reference/document-extract)** (`@openclaw/document-extract-plugin`)——已包含在 OpenClaw 中。从本地文档附件提取文本和后备页面图片。
- **[duckduckgo](/plugins/reference/duckduckgo)** (`@openclaw/duckduckgo-plugin`)——已包含在 OpenClaw 中。添加网页搜索 provider 支持。
- **[elevenlabs](/plugins/reference/elevenlabs)** (`@openclaw/elevenlabs-speech`)——已包含在 OpenClaw 中。添加媒体理解、实时转录和文字转语音 provider 支持。
- **[exa](/plugins/reference/exa)** (`@openclaw/exa-plugin`)——已包含在 OpenClaw 中。添加网页搜索 provider 支持。
- **[fal](/plugins/reference/fal)** (`@openclaw/fal-provider`)——已包含在 OpenClaw 中。添加 fal 模型 provider 支持。
- **[file-transfer](/plugins/reference/file-transfer)** (`@openclaw/file-transfer`)——已包含在 OpenClaw 中。通过专用 node 命令在配对节点上获取、列出和写入文件。
- **[firecrawl](/plugins/reference/firecrawl)** (`@openclaw/firecrawl-plugin`)——已包含在 OpenClaw 中。添加 agent 可调用工具、网页获取和网页搜索 provider 支持。
- **[fireworks](/plugins/reference/fireworks)** (`@openclaw/fireworks-provider`)——已包含在 OpenClaw 中。添加 Fireworks 模型 provider 支持。
- **[github-copilot](/plugins/reference/github-copilot)** (`@openclaw/github-copilot-provider`)——已包含在 OpenClaw 中。添加 GitHub Copilot 模型 provider 支持。
- **[gmi](/plugins/reference/gmi)** (`@openclaw/gmi-provider`)——已包含在 OpenClaw 中。添加 Gmi、Gmi Cloud、Gmicloud 模型 provider 支持。
- **[google](/plugins/reference/google)** (`@openclaw/google-plugin`)——已包含在 OpenClaw 中。添加 Google、Google Gemini CLI、Google Vertex 模型 provider 支持。
- **[gradium](/plugins/reference/gradium)** (`@openclaw/gradium-speech`)——已包含在 OpenClaw 中。添加文字转语音 provider 支持。
- **[groq](/plugins/reference/groq)** (`@openclaw/groq-provider`)——已包含在 OpenClaw 中。添加 Groq 模型 provider 支持。
- **[huggingface](/plugins/reference/huggingface)** (`@openclaw/huggingface-provider`)——已包含在 OpenClaw 中。添加 Hugging Face 模型 provider 支持。
- **[imessage](/plugins/reference/imessage)** (`@openclaw/imessage`)——已包含在 OpenClaw 中。添加 iMessage channel 表面。
- **[inworld](/plugins/reference/inworld)** (`@openclaw/inworld-speech`)——已包含在 OpenClaw 中。Inworld 流式文字转语音（MP3、OGG_OPUS、PCM 电话）。
- **[irc](/plugins/reference/irc)** (`@openclaw/irc`)——已包含在 OpenClaw 中。添加 IRC channel 表面。
- **[kilocode](/plugins/reference/kilocode)** (`@openclaw/kilocode-provider`)——已包含在 OpenClaw 中。添加 Kilocode 模型 provider 支持。
- **[kimi](/plugins/reference/kimi)** (`@openclaw/kimi-provider`)——已包含在 OpenClaw 中。添加 Kimi、Kimi Coding 模型 provider 支持。
- **[litellm](/plugins/reference/litellm)** (`@openclaw/litellm-provider`)——已包含在 OpenClaw 中。添加 LiteLLM 模型 provider 支持。
- **[llm-task](/plugins/reference/llm-task)** (`@openclaw/llm-task`)——已包含在 OpenClaw 中。通用纯 JSON LLM 工具，用于工作流可调用的结构化任务。
- **[lmstudio](/plugins/reference/lmstudio)** (`@openclaw/lmstudio-provider`)——已包含在 OpenClaw 中。添加 LM Studio 模型 provider 支持。
- **[mattermost](/plugins/reference/mattermost)** (`@openclaw/mattermost`)——已包含在 OpenClaw 中。添加 Mattermost channel 表面。
- **[memory-core](/plugins/reference/memory-core)** (`@openclaw/memory-core`)——已包含在 OpenClaw 中。添加记忆嵌入 provider 支持和 agent 可调用工具。
- **[memory-wiki](/plugins/reference/memory-wiki)** (`@openclaw/memory-wiki`)——已包含在 OpenClaw 中。持久化 wiki 编译器和 Obsidian 友好的知识库。
- **[microsoft](/plugins/reference/microsoft)** (`@openclaw/microsoft-speech`)——已包含在 OpenClaw 中。添加文字转语音 provider 支持。
- **[microsoft-foundry](/plugins/reference/microsoft-foundry)** (`@openclaw/microsoft-foundry`)——已包含在 OpenClaw 中。添加 Microsoft Foundry 模型 provider 支持。
- **[migrate-claude](/plugins/reference/migrate-claude)** (`@openclaw/migrate-claude`)——已包含在 OpenClaw 中。将 Claude Code 和 Claude Desktop 的指令、MCP 服务器、技能和安全配置导入 OpenClaw。
- **[migrate-hermes](/plugins/reference/migrate-hermes)** (`@openclaw/migrate-hermes`)——已包含在 OpenClaw 中。将 Hermes 配置、记忆、技能和支持的凭证导入 OpenClaw。
- **[minimax](/plugins/reference/minimax)** (`@openclaw/minimax-provider`)——已包含在 OpenClaw 中。添加 MiniMax、MiniMax Portal 模型 provider 支持。
- **[mistral](/plugins/reference/mistral)** (`@openclaw/mistral-provider`)——已包含在 OpenClaw 中。添加 Mistral 模型 provider 支持。
- **[moonshot](/plugins/reference/moonshot)** (`@openclaw/moonshot-provider`)——已包含在 OpenClaw 中。添加 Moonshot 模型 provider 支持。
- **[novita](/plugins/reference/novita)** (`@openclaw/novita-provider`)——已包含在 OpenClaw 中。添加 Novita、Novita AI、Novitaai 模型 provider 支持。
- **[nvidia](/plugins/reference/nvidia)** (`@openclaw/nvidia-provider`)——已包含在 OpenClaw 中。添加 NVIDIA 模型 provider 支持。
- **[oc-path](/plugins/reference/oc-path)** (`@openclaw/oc-path`)——已包含在 OpenClaw 中。添加 openclaw path CLI 用于 oc:// 工作区文件寻址。
- **[ollama](/plugins/reference/ollama)** (`@openclaw/ollama-provider`)——已包含在 OpenClaw 中。添加 Ollama、Ollama Cloud 模型 provider 支持。
- **[open-prose](/plugins/reference/open-prose)** (`@openclaw/open-prose`)——已包含在 OpenClaw 中。OpenProse VM 技能包，附带 /prose 斜杠命令。
- **[openai](/plugins/reference/openai)** (`@openclaw/openai-provider`)——已包含在 OpenClaw 中。添加 OpenAI 模型 provider 支持。
- **[opencode](/plugins/reference/opencode)** (`@openclaw/opencode-provider`)——已包含在 OpenClaw 中。添加 OpenCode 模型 provider 支持。
- **[opencode-go](/plugins/reference/opencode-go)** (`@openclaw/opencode-go-provider`)——已包含在 OpenClaw 中。添加 OpenCode Go 模型 provider 支持。
- **[openrouter](/plugins/reference/openrouter)** (`@openclaw/openrouter-provider`)——已包含在 OpenClaw 中。添加 OpenRouter 模型 provider 支持。
- **[parallel](/tools/parallel-search)** (`@openclaw/parallel-plugin`)——已包含在 OpenClaw 中。添加网页搜索 provider 支持。
- **[perplexity](/plugins/reference/perplexity)** (`@openclaw/perplexity-plugin`)——已包含在 OpenClaw 中。添加网页搜索 provider 支持。
- **[policy](/plugins/reference/policy)** (`@openclaw/policy`)——已包含在 OpenClaw 中。为工作区合规性添加 policy 支持的 doctor 检查。
- **[qianfan](/plugins/reference/qianfan)** (`@openclaw/qianfan-provider`)——已包含在 OpenClaw 中。添加 Qianfan 模型 provider 支持。
- **[qwen](/plugins/reference/qwen)** (`@openclaw/qwen-provider`)——已包含在 OpenClaw 中。添加 Qwen、Qwen Cloud、Model Studio、DashScope 等模型 provider 支持。
- **[runway](/plugins/reference/runway)** (`@openclaw/runway-provider`)——已包含在 OpenClaw 中。添加视频生成 provider 支持。
- **[searxng](/plugins/reference/searxng)** (`@openclaw/searxng-plugin`)——已包含在 OpenClaw 中。添加网页搜索 provider 支持。
- **[senseaudio](/plugins/reference/senseaudio)** (`@openclaw/senseaudio-provider`)——已包含在 OpenClaw 中。添加媒体理解 provider 支持。
- **[sglang](/plugins/reference/sglang)** (`@openclaw/sglang-provider`)——已包含在 OpenClaw 中。添加 SGLang 模型 provider 支持。
- **[signal](/plugins/reference/signal)** (`@openclaw/signal`)——已包含在 OpenClaw 中。添加 Signal channel 表面。
- **[sms](/plugins/reference/sms)** (`@openclaw/sms`)——已包含在 OpenClaw 中。Twilio SMS channel 插件。
- **[stepfun](/plugins/reference/stepfun)** (`@openclaw/stepfun-provider`)——已包含在 OpenClaw 中。添加 StepFun、StepFun Plan 模型 provider 支持。
- **[synthetic](/plugins/reference/synthetic)** (`@openclaw/synthetic-provider`)——已包含在 OpenClaw 中。添加 Synthetic 模型 provider 支持。
- **[tavily](/plugins/reference/tavily)** (`@openclaw/tavily-plugin`)——已包含在 OpenClaw 中。添加 agent 可调用工具和网页搜索 provider 支持。
- **[telegram](/plugins/reference/telegram)** (`@openclaw/telegram`)——已包含在 OpenClaw 中。添加 Telegram channel 表面。
- **[tencent](/plugins/reference/tencent)** (`@openclaw/tencent-provider`)——已包含在 OpenClaw 中。添加 Tencent TokenHub 模型 provider 支持。
- **[together](/plugins/reference/together)** (`@openclaw/together-provider`)——已包含在 OpenClaw 中。添加 Together 模型 provider 支持。
- **[tts-local-cli](/plugins/reference/tts-local-cli)** (`@openclaw/tts-local-cli`)——已包含在 OpenClaw 中。添加文字转语音 provider 支持。
- **[venice](/plugins/reference/venice)** (`@openclaw/venice-provider`)——已包含在 OpenClaw 中。添加 Venice 模型 provider 支持。
- **[vercel-ai-gateway](/plugins/reference/vercel-ai-gateway)** (`@openclaw/vercel-ai-gateway-provider`)——已包含在 OpenClaw 中。添加 Vercel AI Gateway 模型 provider 支持。
- **[vllm](/plugins/reference/vllm)** (`@openclaw/vllm-provider`)——已包含在 OpenClaw 中。添加 vLLM 模型 provider 支持。
- **[volcengine](/plugins/reference/volcengine)** (`@openclaw/volcengine-provider`)——已包含在 OpenClaw 中。添加 Volcengine、Volcengine Plan 模型 provider 支持。
- **[voyage](/plugins/reference/voyage)** (`@openclaw/voyage-provider`)——已包含在 OpenClaw 中。添加记忆嵌入 provider 支持。
- **[vydra](/plugins/reference/vydra)** (`@openclaw/vydra-provider`)——已包含在 OpenClaw 中。添加 Vydra 模型 provider 支持。
- **[web-readability](/plugins/reference/web-readability)** (`@openclaw/web-readability-plugin`)——已包含在 OpenClaw 中。从本地 HTML 网页获取响应中提取可读文章内容。
- **[webhooks](/plugins/reference/webhooks)** (`@openclaw/webhooks`)——已包含在 OpenClaw 中。认证入站 webhook，将外部自动化绑定到 OpenClaw TaskFlow。
- **[workboard](/plugins/reference/workboard)** (`@openclaw/workboard`)——已包含在 OpenClaw 中。agent 名下 issue 和会话的仪表板工作板。
- **[xai](/plugins/reference/xai)** (`@openclaw/xai-plugin`)——已包含在 OpenClaw 中。添加 xAI 模型 provider 支持。
- **[xiaomi](/plugins/reference/xiaomi)** (`@openclaw/xiaomi-provider`)——已包含在 OpenClaw 中。添加 Xiaomi、Xiaomi Token Plan 模型 provider 支持。
- **[zai](/plugins/reference/zai)** (`@openclaw/zai-provider`)——已包含在 OpenClaw 中。添加 Z.AI 模型 provider 支持。

## 官方外部包

34 个插件

- **[acpx](/plugins/reference/acpx)** (`@openclaw/acpx`)——npm；ClawHub。OpenClaw ACP 运行时后端，持有插件名下的会话和传输管理。
- **[amazon-bedrock](/plugins/reference/amazon-bedrock)** (`@openclaw/amazon-bedrock-provider`)——npm；ClawHub。OpenClaw Amazon Bedrock provider 插件，支持模型发现、嵌入和护栏。
- **[amazon-bedrock-mantle](/plugins/reference/amazon-bedrock-mantle)** (`@openclaw/amazon-bedrock-mantle-provider`)——npm；ClawHub。OpenAI 兼容模型路由的 Amazon Bedrock Mantle provider。
- **[anthropic-vertex](/plugins/reference/anthropic-vertex)** (`@openclaw/anthropic-vertex-provider`)——npm；ClawHub。Google Vertex AI 上 Claude 模型的 Anthropic Vertex provider。
- **[brave](/plugins/reference/brave)** (`@openclaw/brave-plugin`)——npm；ClawHub。Brave Search 网页搜索 provider。
- **[codex](/plugins/reference/codex)** (`@openclaw/codex`)——npm；ClawHub。Codex app-server harness 和模型 provider 插件，持有 Codex 管理的 GPT 目录。
- **[copilot](/plugins/reference/copilot)** (`@openclaw/copilot`)——npm；ClawHub：`clawhub:@openclaw/copilot`。注册 GitHub Copilot agent 运行时。
- **[diagnostics-otel](/plugins/reference/diagnostics-otel)** (`@openclaw/diagnostics-otel`)——npm；ClawHub：`clawhub:@openclaw/diagnostics-otel`。指标和追踪的 OpenTelemetry 导出器。
- **[diagnostics-prometheus](/plugins/reference/diagnostics-prometheus)** (`@openclaw/diagnostics-prometheus`)——npm；ClawHub：`clawhub:@openclaw/diagnostics-prometheus`。运行时指标的 Prometheus 导出器。
- **[diffs](/plugins/reference/diffs)** (`@openclaw/diffs`)——npm；ClawHub。只读 diff 查看器插件和 agent 文件渲染器。
- **[diffs-language-pack](/plugins/reference/diffs-language-pack)** (`@openclaw/diffs-language-pack`)——npm；ClawHub：`clawhub:@openclaw/diffs-language-pack`。为默认 diff 查看器之外的语言添加语法高亮。
- **[discord](/plugins/reference/discord)** (`@openclaw/discord`)——npm；ClawHub。Discord channel 插件，支持频道、私信、命令和应用事件。
- **[feishu](/plugins/reference/feishu)** (`@openclaw/feishu`)——npm；ClawHub。飞书/Lark channel 插件（社区 @m1heng 维护）。
- **[google-meet](/plugins/reference/google-meet)** (`@openclaw/google-meet`)——npm；ClawHub。Google Meet 参与者插件，通过 Chrome 或 Twilio 传输加入通话。
- **[googlechat](/plugins/reference/googlechat)** (`@openclaw/googlechat`)——npm；ClawHub。Google Chat channel 插件，支持空间和私信。
- **[line](/plugins/reference/line)** (`@openclaw/line`)——npm；ClawHub。LINE Bot API 对话的 LINE channel 插件。
- **[lobster](/plugins/reference/lobster)** (`@openclaw/lobster`)——npm；ClawHub。类型化管道和可恢复审批的 Lobster 工作流工具插件。
- **[matrix](/plugins/reference/matrix)** (`@openclaw/matrix`)——ClawHub：`clawhub:@openclaw/matrix`；npm。Matrix channel 插件，支持房间和私信。
- **[memory-lancedb](/plugins/reference/memory-lancedb)** (`@openclaw/memory-lancedb`)——npm；ClawHub。LanceDB 支持的长期记忆插件，自动召回、自动捕获和向量搜索。
- **[msteams](/plugins/reference/msteams)** (`@openclaw/msteams`)——npm；ClawHub。Microsoft Teams channel 插件。
- **[nextcloud-talk](/plugins/reference/nextcloud-talk)** (`@openclaw/nextcloud-talk`)——npm；ClawHub。Nextcloud Talk channel 插件。
- **[nostr](/plugins/reference/nostr)** (`@openclaw/nostr`)——npm；ClawHub。NIP-04 加密私信的 Nostr channel 插件。
- **[openshell](/plugins/reference/openshell)** (`@openclaw/openshell-sandbox`)——npm；ClawHub。NVIDIA OpenShell CLI 的沙箱后端，支持镜像本地工作区和 SSH 命令执行。
- **[pixverse](/plugins/reference/pixverse)** (`@openclaw/pixverse-provider`)——npm；ClawHub：`clawhub:@openclaw/pixverse-provider`。PixVerse 视频生成 provider。
- **[qqbot](/plugins/reference/qqbot)** (`@openclaw/qqbot`)——npm；ClawHub。QQ Bot channel 插件，支持群聊和私信工作流。
- **[slack](/plugins/reference/slack)** (`@openclaw/slack`)——npm；ClawHub。Slack channel 插件，支持频道、私信、命令和应用事件。
- **[synology-chat](/plugins/reference/synology-chat)** (`@openclaw/synology-chat`)——npm；ClawHub。Synology Chat channel 插件。
- **[tlon](/plugins/reference/tlon)** (`@openclaw/tlon`)——npm；ClawHub。Tlon/Urbit channel 插件。
- **[tokenjuice](/plugins/reference/tokenjuice)** (`@openclaw/tokenjuice`)——npm；ClawHub：`clawhub:@openclaw/tokenjuice`。用 tokenjuice reducer 压缩 exec 和 bash 工具结果。
- **[twitch](/plugins/reference/twitch)** (`@openclaw/twitch`)——npm；ClawHub。Twitch channel 插件，支持聊天和审核工作流。
- **[voice-call](/plugins/reference/voice-call)** (`@openclaw/voice-call`)——npm；ClawHub。Twilio、Telnyx 和 Plivo 电话通话插件。
- **[whatsapp](/plugins/reference/whatsapp)** (`@openclaw/whatsapp`)——ClawHub：`clawhub:@openclaw/whatsapp`；npm。WhatsApp Web 对话的 WhatsApp channel 插件。
- **[zalo](/plugins/reference/zalo)** (`@openclaw/zalo`)——npm；ClawHub。Zalo channel 插件，支持 bot 和 webhook 对话。
- **[zalouser](/plugins/reference/zalouser)** (`@openclaw/zalouser`)——npm；ClawHub。通过原生 zca-js 集成的 Zalo 个人账户插件。

## 仅源码检出

3 个插件

- **[qa-channel](/plugins/reference/qa-channel)** (`@openclaw/qa-channel`)——仅源码检出。添加 QA Channel 表面。
- **[qa-lab](/plugins/reference/qa-lab)** (`@openclaw/qa-lab`)——仅源码检出。QA lab 插件，附带私有调试器 UI 和场景运行器。
- **[qa-matrix](/plugins/reference/qa-matrix)** (`@openclaw/qa-matrix`)——仅源码检出。Matrix QA 传输运行器和基底。
