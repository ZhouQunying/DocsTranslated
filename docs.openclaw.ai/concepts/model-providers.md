# Model providers / 模型提供者

## 架构精读

> 跳过不影响阅读翻译正文。

### Plugin-owned provider 行为——generic loop 和 provider-specific 的分离

OpenClaw 的核心设计是**保持通用推理循环，把 provider 特有的逻辑下沉到 provider plugin**。这意味着 OpenClaw 核心只知道"怎么调 LLM"，不知道"怎么跟 OpenAI 特有的 API 打交道"——后者由 OpenAI provider plugin 负责。

这跟 JDBC 是一个思路。JDBC 核心是 `Connection`/`Statement`/`ResultSet` 的通用接口，MySQL/PostgreSQL 的特有逻辑（连接池、prepared statement 缓存）下沉到 driver。OpenClaw 的 `registerProvider(...)` 就像 JDBC 的 `DriverManager.registerDriver()`——每个 provider plugin 注册自己的实现，核心循环用统一接口调用。

Plugin 负责的具体职责包括：onboarding、模型目录、auth 环境变量映射、传输/配置归一化、工具 schema 清理、failover 分类、OAuth 刷新、usage 报告、thinking/reasoning profile。这些都是 provider 之间不同的细节——比如 Anthropic 的 `cache_control`、OpenRouter 的 prompt caching、NVIDIA 的 vendor/model namespace，都需要 provider plugin 处理。

### Auth 顺序分层——显式配置 > 已配置 profile > 存储 profile

OpenClaw 的 auth profile 选择有三层优先级：
1. **显式配置** `auth.order[provider]`（用户明确指定顺序）
2. **已配置 profile** `auth.profiles` 按 provider 过滤
3. **存储 profile** 每 agent SQLite auth profile 条目

这跟 Linux 的名称解析顺序（`/etc/nsswitch.conf`）是一个思路——`hosts: files dns` 表示先查 `/etc/hosts`，再查 DNS。OpenClaw 的 auth 顺序也是分层查找，显式配置最高优先级。

没有显式顺序时，OpenClaw 使用**round-robin**：OAuth 优先于 API key（同类型内按 `lastUsed` 最旧优先），cooldown/disabled profile 移到最后。这保证了"免费"的订阅 auth 先消耗，付费 API key 作为后备。

### `models.providers` 作为扩展点——自定义 provider 的安全阀

`models.providers` 是 OpenClaw 的**自定义 provider 入口**。当 bundled provider plugin 不能满足需求时（比如公司内部的 LLM gateway、自建的 OpenAI-compatible proxy），用户通过 `models.providers` 添加自定义 provider。

这跟 Kubernetes 的 CRD（Custom Resource Definition）是一个思路。Kubernetes 内置了 Pod/Service/Deployment，但当这些不够时，用户用 CRD 扩展自己的资源类型。OpenClaw 的 bundled provider 就像内置资源，`models.providers` 就像 CRD——用统一的 schema 添加自定义实现。

关键设计是**非原生端点的 compat 保护**。当 `baseUrl` 不是 `api.openai.com` 时，OpenClaw 强制 `compat.supportsDeveloperRole: false`，避免 provider 因为不支持 `developer` role 而返回 400 错误。这跟浏览器的 User-Agent 嗅探是一个思路——检测到非原生端点时自动降级到兼容模式。

### API key 轮换的精确触发——只在 rate-limit 时切换

OpenClaw 的 API key 轮换**只在 rate-limit 响应时触发**（429、`rate_limit`、`quota`、`resource exhausted` 等），其他错误立即失败不轮换。

这跟数据库连接池的健康检查是一个思路。连接池不会因为一次查询失败就切换到另一个数据库——只有当检测到连接本身不可用（超时、连接断开）时才切换。OpenClaw 也是这样：只有 rate-limit 表示"这个 key 暂时不能用了"，其他错误（格式错误、模型不存在）换 key 也不会解决。

---

LLM/模型提供者的参考（不是 WhatsApp/Telegram 等聊天频道）。模型选择规则参见 Models。

## Quick rules / 快速规则

- Model ref 使用 `provider/model`（例如 `opencode/claude-opus-4-6`）。
- `agents.defaults.models` 设置后作为允许列表。
- CLI 助手：`openclaw onboard`、`openclaw models list`、`openclaw models set <provider/model>`。
- `models.providers.*.contextWindow`/`contextTokens`/`maxTokens` 设置 provider 级别默认值；`models.providers.*.models[].contextWindow`/`contextTokens`/`maxTokens` 按模型覆盖。
- Fallback 规则、冷却探测和 session 覆盖持久化：参见 Model failover。

`openclaw configure` 在添加或重新认证 provider 时保留现有的 `agents.defaults.model.primary`。`openclaw models auth login` 也是这样，除非你传递 `--set-default`。Provider plugin 可能仍在其 auth 配置补丁中返回推荐默认模型，但当主模型已存在时，OpenClaw 将其视为"使此模型可用"，而非"替换当前主模型"。

要有意切换默认模型，使用 `openclaw models set <provider/model>` 或 `openclaw models auth login --provider <id> --set-default`。

OpenAI 系列路由按前缀区分：
- `openai/<model>` 默认使用原生 Codex 应用服务器工具链处理 agent 轮次。这是常见的 ChatGPT/Codex 订阅设置。
- 遗留 Codex model ref 是遗留配置，`doctor rewrites` 将其重写为 `openai/<model>`。
- `openai/<model>` 加 `provider/model` `agentRuntime.id: "openclaw"` 使用 OpenClaw 内置运行时处理显式 API 密钥或兼容路由。

参见 OpenAI 和 Codex 工具链。如果 provider/runtime 分离令人困惑，先阅读 Agent 运行时。

Plugin 自动启用遵循相同边界：`openai/*` agent ref 为默认路由启用 Codex plugin，显式 `provider/model` `agentRuntime.id: "codex"` 或遗留 `codex/<model>` ref 也需要它。

GPT-5.5 默认通过 `openai/gpt-5.5` 上的原生 Codex 应用服务器工具链可用，当 provider/model 运行时策略显式选择 `openclaw` 时通过 OpenClaw 运行时可用。

CLI 运行时使用相同分离：选择规范 model ref 如 `anthropic/claude-*` 或 `google/gemini-*`，然后在需要本地 CLI 后端时将 provider/model 运行时策略设置为 `claude-cli` 或 `google-gemini-cli`。

遗留 `claude-cli/*` 和 `google-gemini-cli/*` ref 迁移回规范 provider ref，运行时单独记录。遗留 `codex-cli/*` ref 迁移到 `openai/*` 并使用 Codex 应用服务器路由；OpenClaw 不再保留捆绑的 Codex CLI 后端。

## Plugin-owned provider 行为

大多数 provider 特有逻辑位于 provider plugin（`registerProvider(...)`），OpenClaw 保持通用推理循环。Plugin 负责 onboarding、模型目录、auth 环境变量映射、传输/配置归一化、工具 schema 清理、failover 分类、OAuth 刷新、usage 报告、thinking/reasoning profile 等。

Provider SDK 钩子和 bundled plugin 示例的完整列表在 Provider plugin 中。需要完全自定义请求执行器的 provider 是一个单独的、更深的扩展表面。

Provider 负责的 runner 行为位于显式 provider 钩子上，如重放策略、工具 schema 归一化、流包装和传输/请求助手。遗留 `ProviderPlugin.capabilities` 静态包仅用于兼容，共享 runner 逻辑不再读取它。

## API key 轮换

通过以下方式配置多个密钥：
- `OPENCLAW_LIVE_<PROVIDER>_KEY`（单个实时覆盖，最高优先级）
- `<PROVIDER>_API_KEYS`（逗号或分号分隔列表）
- `<PROVIDER>_API_KEY`（主密钥）
- `<PROVIDER>_API_KEY_*`（编号列表，例如 `<PROVIDER>_API_KEY_1`）

对于 Google provider，`GOOGLE_API_KEY` 也作为后备包含在内。密钥选择顺序保持优先级并去重。

- 仅在 rate-limit 响应（例如 429、`rate_limit`、`quota`、`resource exhausted`、`Too many concurrent requests`、`ThrottlingException`、`concurrency limit reached`、`workers_ai ... quota limit exceeded` 或周期性 usage-limit 消息）时用下一个密钥重试。
- 非 rate-limit 失败立即失败；不尝试密钥轮换。
- 当所有候选密钥都失败时，返回最后一次尝试的最终错误。

## 官方 provider plugin

官方 provider plugin 发布自己的模型目录行。这些 provider **不**需要 `models.providers` model 条目；启用 provider plugin，设置 auth，然后选择模型。仅将 `models.providers` 用于显式自定义 provider 或窄请求设置如超时。

### OpenAI

- Provider: `openai`
- Auth: `OPENAI_API_KEY`
- 可选轮换：`OPENAI_API_KEYS`、`OPENAI_API_KEY_1`、`OPENAI_API_KEY_2`，加 `OPENCLAW_LIVE_OPENAI_KEY`（单个覆盖）
- 示例模型：`openai/gpt-5.5`、`openai/gpt-5.4-mini`
- CLI：`openclaw onboard --auth-choice openai-api-key`
- 默认传输是 `auto`；OpenClaw 将传输选择传递给共享模型运行时。
- 通过 `agents.defaults.models["openai/<model>"].params.transport` 按模型覆盖（`"sse"`、`"websocket"` 或 `"auto"`）
- OpenAI 优先处理可通过 `agents.defaults.models["openai/<model>"].params.serviceTier` 启用
- `/fast` 和 `params.fastMode` 将直接 `openai/*` Responses 请求映射到 `api.openai.com` 上的 `service_tier=priority`
- 隐藏 OpenClaw 归因头（originator、version、User-Agent）仅适用于 `api.openai.com` 上的原生 OpenAI 流量，不适用于通用 OpenAI 兼容代理
- 原生 OpenAI 路由还保留 Responses store、prompt-cache hints 和 OpenAI reasoning-compat payload shaping；代理路由不保留

```
{
  agents: { defaults: { model: { primary: "openai/gpt-5.5" } } },
}
```

### Anthropic

- Provider: `anthropic`
- Auth: `ANTHROPIC_API_KEY`
- 可选轮换：`ANTHROPIC_API_KEYS`、`ANTHROPIC_API_KEY_1`、`ANTHROPIC_API_KEY_2`，加 `OPENCLAW_LIVE_ANTHROPIC_KEY`（单个覆盖）
- 示例模型：`anthropic/claude-opus-4-6`
- CLI：`openclaw onboard --auth-choice apiKey`
- 直接公共 Anthropic 请求支持 shared `/fast` toggle 和 `params.fastMode`，包括发送到 `api.anthropic.com` 的 API 密钥和 OAuth 认证流量；OpenClaw 将其映射到 Anthropic `service_tier`（`auto` vs `standard_only`）
- 首选 Claude CLI 配置保持 model ref 规范并单独选择 CLI 后端：`anthropic/claude-opus-4-8` 加 model-scoped `agentRuntime.id: "claude-cli"`。遗留 `claude-cli/claude-opus-4-7` ref 仍可用于兼容。

```
{
  agents: { defaults: { model: { primary: "anthropic/claude-opus-4-6" } } },
}
```

### OpenAI ChatGPT/Codex OAuth

- Provider: `openai`
- Auth: OAuth (ChatGPT)
- 遗留 OpenAI Codex model ref：`openai/gpt-5.5`
- 原生 Codex 应用服务器工具链 ref：`openai/gpt-5.5`
- 原生 Codex 应用服务器工具链文档：Codex 工具链
- Plugin 边界：`openai/*` 加载 OpenAI plugin；原生 Codex 应用服务器 plugin 由 Codex 工具链运行时选择。
- CLI：`openclaw onboard --auth-choice openai` 或 `openclaw models auth login --provider openai`
- 默认传输是 `auto`（WebSocket 优先，SSE 后备）
- `params.serviceTier` 也在原生 Codex Responses 请求（`chatgpt.com/backend-api`）上转发
- 隐藏 OpenClaw 归因头仅在 `chatgpt.com/backend-api` 上的原生 Codex 流量上附加
- 共享与直接 `openai/*` 相同的 `/fast` toggle 和 `params.fastMode` 配置；OpenClaw 将其映射到 `service_tier=priority`
- `openai/gpt-5.5` 使用 Codex 目录原生 `contextWindow = 400000` 和默认运行时 `contextTokens = 272000`；用 `models.providers.openai.models[].contextTokens` 覆盖运行时上限

策略说明：OpenAI Codex OAuth 明确支持用于 OpenClaw 等外部工具/工作流。

```
{
  plugins: { entries: { codex: { enabled: true } } },
  agents: {
    defaults: {
      model: { primary: "openai/gpt-5.5" },
    },
  },
}
```

### 其他订阅式托管选项

- Z.AI Coding Plan 或通用 API 端点。
- MiniMax Coding Plan OAuth 或 API 密钥访问。
- Qwen Cloud provider 表面加 Alibaba DashScope 和 Coding Plan 端点映射。

### OpenCode

- Auth: `OPENCODE_API_KEY`（或 `OPENCODE_ZEN_API_KEY`）
- Zen 运行时 provider：`opencode`
- Go 运行时 provider：`opencode-go`
- 示例模型：`opencode/claude-opus-4-6`、`opencode-go/kimi-k2.6`
- CLI：`openclaw onboard --auth-choice opencode-zen` 或 `openclaw onboard --auth-choice opencode-go`

```
{
  agents: { defaults: { model: { primary: "opencode/claude-opus-4-6" } } },
}
```

### Google Gemini (API key)

- Provider: `google`
- Auth: `GEMINI_API_KEY`
- 可选轮换：`GEMINI_API_KEYS`、`GEMINI_API_KEY_1`、`GEMINI_API_KEY_2`、`GOOGLE_API_KEY` 后备，和 `OPENCLAW_LIVE_GEMINI_KEY`（单个覆盖）
- 示例模型：`google/gemini-3.1-pro-preview`、`google/gemini-3-flash-preview`
- 兼容：使用 `google/gemini-3.1-flash-preview` 的遗留 OpenClaw 配置归一化为 `google/gemini-3-flash-preview`
- CLI：`openclaw onboard --auth-choice gemini-api-key`
- Thinking：`/think adaptive` 使用 Google dynamic thinking。Gemini 3/3.1 省略固定 `thinkingLevel`；Gemini 2.5 发送 `thinkingBudget: -1`。

### Google Vertex 和 Gemini CLI

- Providers: `google-vertex`、`google-gemini-cli`
- Auth: Vertex 使用 gcloud ADC；Gemini CLI 使用其 OAuth 流程

Gemini CLI OAuth 在 OpenClaw 中是非官方集成。一些用户报告使用第三方客户端后 Google 账户受限。审查 Google 条款，如果选择继续使用，请使用非关键账户。

Gemini CLI OAuth 作为捆绑 `google` plugin 的一部分发布。

- 安装 Gemini CLI：`brew install gemini-cli` 或 `npm install -g @google/gemini-cli`
- 启用 plugin：`openclaw plugins enable google`
- 登录：`openclaw models auth login --provider google-gemini-cli --set-default`
- 默认模型：`google-gemini-cli/gemini-3-flash-preview`。**不**需要将 client id 或 secret 粘贴到 `openclaw.json`。CLI 登录流程将 token 存储在 gateway 主机的 auth profile 中。
- 设置项目（如果需要）：如果登录后请求失败，在 gateway 主机上设置 `GOOGLE_CLOUD_PROJECT` 或 `GOOGLE_CLOUD_PROJECT_ID`。

### Z.AI (GLM)

- Provider: `zai`
- Auth: `ZAI_API_KEY`
- 示例模型：`zai/glm-5.2`
- CLI：`openclaw onboard --auth-choice zai-api-key`
- Model ref 使用规范 `zai/*` provider ID。
- `zai-api-key` 自动检测匹配的 Z.AI 端点；`zai-coding-global`、`zai-coding-cn`、`zai-global` 和 `zai-cn` 强制特定表面

### Vercel AI Gateway

- Provider: `vercel-ai-gateway`
- Auth: `AI_GATEWAY_API_KEY`
- 示例模型：`vercel-ai-gateway/anthropic/claude-opus-4.6`、`vercel-ai-gateway/moonshotai/kimi-k2.6`
- CLI：`openclaw onboard --auth-choice ai-gateway-api-key`

### 其他 bundled provider plugin

#### 值得了解的怪癖

- **OpenRouter**：仅在验证的 `openrouter.ai` 路由上应用其应用归因头和 Anthropic `cache_control` 标记。DeepSeek、Moonshot 和 ZAI ref 符合 OpenRouter 管理的 prompt caching 的 cache-TTL 条件，但不接收 Anthropic cache 标记。作为代理式 OpenAI 兼容路径，它跳过原生 OpenAI 专属 shaping（serviceTier、Responses store、prompt-cache hints、OpenAI reasoning-compat）。Gemini 支持的 ref 仅保留 proxy-Gemini thought-signature 清理。
- **Kilocode**：Gemini 支持的 ref 遵循相同的 proxy-Gemini 清理路径；`kilocode/kilo/auto` 和其他 proxy-reasoning-unsupported ref 跳过 proxy reasoning 注入。
- **MiniMax**：API 密钥 onboarding 写入显式 M3 和 M2.7 聊天模型定义；图像理解保持在 plugin 自带的 `MiniMax-VL-01` 媒体 provider 上。
- **NVIDIA**：Model id 使用 `nvidia/<vendor>/<model>` namespace（例如 `nvidia/nvidia/nemotron-...` 与 `nvidia/moonshotai/kimi-k2.5` 并列）；选择器保留字面 `<provider>/<model-id>` 组合，而发送到 API 的规范键保持单前缀。
- **xAI**：使用 xAI Responses 路径。推荐路径是 SuperGrok/X Premium OAuth；API 密钥仍通过 `XAI_API_KEY` 或 plugin 配置工作，Grok `web_search` 在 API 密钥后备之前复用相同 auth profile。`grok-4.3` 是捆绑默认聊天模型，`grok-build-0.1` 可选择用于 build/coding 重点工作。`/fast` 或 `params.fastMode: true` 将 `grok-3`、`grok-3-mini`、`grok-4` 和 `grok-4-0709` 重写为其 `*-fast` 变体。`tool_stream` 默认开启；通过 `agents.defaults.models["xai/<model>"].params.tool_stream=false` 禁用。

## 通过 `models.providers` 的 Provider（自定义/base URL）

使用 `models.providers`（或 `models.json`）添加**自定义** provider 或 OpenAI/Anthropic 兼容代理。

许多下方 bundled provider plugin 已发布默认目录。仅当你想覆盖默认 base URL、头或模型列表时才使用显式 `models.providers.<id>` 条目。

Gateway 模型能力检查也读取显式 `models.providers.<id>.models[]` 元数据。如果自定义或代理模型接受图像，在该模型上设置 `input: ["text", "image"]`，以便 WebChat 和节点源附件路径将图像作为原生模型输入传递，而非纯文本媒体 ref。

`agents.defaults.models["provider/model"]` 仅控制 agent 的模型可见性、别名和每模型元数据。它本身不注册新运行时模型。对于自定义 provider 模型，还需添加 `models.providers.<provider>.models[]`，至少包含匹配的 `id`。

### Moonshot AI (Kimi)

Moonshot 作为 bundled provider plugin 发布。默认使用内置 provider，仅在需要覆盖 base URL 或模型元数据时添加显式 `models.providers.moonshot` 条目：

- Provider: `moonshot`
- Auth: `MOONSHOT_API_KEY`
- 示例模型：`moonshot/kimi-k2.6`
- CLI：`openclaw onboard --auth-choice moonshot-api-key` 或 `openclaw onboard --auth-choice moonshot-api-key-cn`

```
{
  agents: {
    defaults: { model: { primary: "moonshot/kimi-k2.6" } },
  },
  models: {
    mode: "merge",
    providers: {
      moonshot: {
        baseUrl: "https://api.moonshot.ai/v1",
        apiKey: "${MOONSHOT_API_KEY}",
        api: "openai-completions",
        models: [{ id: "kimi-k2.6", name: "Kimi K2.6" }],
      },
    },
  },
}
```

### Kimi coding

Kimi Coding 使用 Moonshot AI 的 Anthropic 兼容端点：

- Provider: `kimi`
- Auth: `KIMI_API_KEY`
- 示例模型：`kimi/kimi-for-coding`

```
{
  env: { KIMI_API_KEY: "sk-..." },
  agents: {
    defaults: { model: { primary: "kimi/kimi-for-coding" } },
  },
}
```

遗留 `kimi/kimi-code` 和 `kimi/k2p5` 仍作为兼容 model id 接受并归一化为 Kimi 的稳定 API model id。

### Volcano Engine (Doubao)

火山引擎在中国提供 Doubao 和其他模型的访问。

- Provider: `volcengine`（coding：`volcengine-plan`）
- Auth: `VOLCANO_ENGINE_API_KEY`
- 示例模型：`volcengine-plan/ark-code-latest`
- CLI：`openclaw onboard --auth-choice volcengine-api-key`

```
{
  agents: {
    defaults: { model: { primary: "volcengine-plan/ark-code-latest" } },
  },
}
```

Onboarding 默认使用 coding 表面，但通用 `volcengine/*` 目录同时注册。

#### 标准模型

- `volcengine/doubao-seed-1-8-251228`（Doubao Seed 1.8）
- `volcengine/doubao-seed-code-preview-251028`
- `volcengine/kimi-k2-5-260127`（Kimi K2.5）
- `volcengine/glm-4-7-251222`（GLM 4.7）
- `volcengine/deepseek-v3-2-251201`（DeepSeek V3.2 128K）

#### Coding 模型 (volcengine-plan)

- `volcengine-plan/ark-code-latest`
- `volcengine-plan/doubao-seed-code`
- `volcengine-plan/kimi-k2.5`
- `volcengine-plan/kimi-k2-thinking`
- `volcengine-plan/glm-4.7`

### BytePlus (International)

BytePlus ARK 为国际用户提供与火山引擎相同的模型访问。

- Provider: `byteplus`（coding：`byteplus-plan`）
- Auth: `BYTEPLUS_API_KEY`
- 示例模型：`byteplus-plan/ark-code-latest`
- CLI：`openclaw onboard --auth-choice byteplus-api-key`

```
{
  agents: {
    defaults: { model: { primary: "byteplus-plan/ark-code-latest" } },
  },
}
```

### Synthetic

Synthetic 在 `synthetic` provider 后提供 Anthropic 兼容模型：

- Provider: `synthetic`
- Auth: `SYNTHETIC_API_KEY`
- 示例模型：`synthetic/hf:MiniMaxAI/MiniMax-M2.5`
- CLI：`openclaw onboard --auth-choice synthetic-api-key`

```
{
  agents: {
    defaults: { model: { primary: "synthetic/hf:MiniMaxAI/MiniMax-M2.5" } },
  },
  models: {
    mode: "merge",
    providers: {
      synthetic: {
        baseUrl: "https://api.synthetic.new/anthropic",
        apiKey: "${SYNTHETIC_API_KEY}",
        api: "anthropic-messages",
        models: [{ id: "hf:MiniMaxAI/MiniMax-M2.5", name: "MiniMax M2.5" }],
      },
    },
  },
}
```

### MiniMax

MiniMax 通过 `models.providers` 配置，因为它使用自定义端点：

- MiniMax OAuth (Global)：`--auth-choice minimax-global-oauth`
- MiniMax OAuth (CN)：`--auth-choice minimax-cn-oauth`
- MiniMax API key (Global)：`--auth-choice minimax-global-api`
- MiniMax API key (CN)：`--auth-choice minimax-cn-api`

在 MiniMax 的 Anthropic 兼容流路径上，OpenClaw 默认禁用 M2.x 系列的 thinking，除非你显式设置；MiniMax-M3（和 M3.x）默认保持在 provider 的省略/自适应 thinking 路径上。`/fast on` 将 `MiniMax-M2.7` 重写为 `MiniMax-M2.7-highspeed`。

Plugin 自带的能力分离：
- 文本/聊天默认保持在 `minimax/MiniMax-M3`
- 图像生成是 `minimax/image-01` 或 `minimax-portal/image-01`
- 图像理解是两个 MiniMax auth 路径上的 plugin 自带 `MiniMax-VL-01`
- Web 搜索保持在 provider id `minimax`

### LM Studio

LM Studio 作为使用原生 API 的 bundled provider plugin 发布：

- Provider: `lmstudio`
- Auth: `LM_API_TOKEN`
- 默认推理 base URL：`http://localhost:1234/v1`

```
{
  agents: {
    defaults: { model: { primary: "lmstudio/openai/gpt-oss-20b" } },
  },
}
```

OpenClaw 使用 LM Studio 的原生 `/api/v1/models` 和 `/api/v1/models/load` 进行发现 + 自动加载，默认使用 `/v1/chat/completions` 进行推理。如果你想让 LM Studio JIT 加载、TTL 和自动驱逐管理模型生命周期，设置 `models.providers.lmstudio.params.preload: false`。

### Ollama

Ollama 作为使用 Ollama 原生 API 的 bundled provider plugin 发布：

- Provider: `ollama`
- Auth: 不需要（本地服务器）
- 示例模型：`ollama/llama3.3`

```
# 安装 Ollama，然后拉取模型：
ollama pull llama3.3
```

```
{
  agents: {
    defaults: { model: { primary: "ollama/llama3.3" } },
  },
}
```

当你用 `OLLAMA_API_KEY` 选择加入时，Ollama 在 `http://127.0.0.1:11434` 本地检测，bundled provider plugin 将 Ollama 直接添加到 `openclaw onboard` 和模型选择器。

### vLLM

vLLM 作为用于本地/自托管 OpenAI 兼容服务器的 bundled provider plugin 发布：

- Provider: `vllm`
- Auth: 可选（取决于你的服务器）
- 默认 base URL：`http://127.0.0.1:8000/v1`

要在本地选择加入自动发现（如果服务器不强制 auth，任何值都可以）：

```
export VLLM_API_KEY="vllm-local"
```

```
{
  agents: {
    defaults: { model: { primary: "vllm/your-model-id" } },
  },
}
```

### SGLang

SGLang 作为用于快速自托管 OpenAI 兼容服务器的 bundled provider plugin 发布：

- Provider: `sglang`
- Auth: 可选（取决于你的服务器）
- 默认 base URL：`http://127.0.0.1:30000/v1`

```
export SGLANG_API_KEY="sglang-local"
```

```
{
  agents: {
    defaults: { model: { primary: "sglang/your-model-id" } },
  },
}
```

### 本地代理（LM Studio、vLLM、LiteLLM 等）

示例（OpenAI 兼容）：

```
{
  agents: {
    defaults: {
      model: { primary: "lmstudio/my-local-model" },
      models: { "lmstudio/my-local-model": { alias: "Local" } },
    },
  },
  models: {
    providers: {
      lmstudio: {
        baseUrl: "http://localhost:1234/v1",
        apiKey: "${LM_API_TOKEN}",
        api: "openai-completions",
        timeoutSeconds: 300,
        models: [
          {
            id: "my-local-model",
            name: "Local Model",
            reasoning: false,
            input: ["text"],
            cost: { input: 0, output: 0, cacheRead: 0, cacheWrite: 0 },
            contextWindow: 200000,
            maxTokens: 8192,
          },
        ],
      },
    },
  },
}
```

对于自定义 provider，`reasoning`、`input`、`cost`、`contextWindow` 和 `maxTokens` 是可选的。省略时，OpenClaw 默认为：
- reasoning: false
- input: ["text"]
- cost: { input: 0, output: 0, cacheRead: 0, cacheWrite: 0 }
- contextWindow: 200000
- maxTokens: 8192

建议：设置与你的代理/模型限制匹配的显式值。

- 对于非原生端点（任何非空 `baseUrl` 且主机不是 `api.openai.com`）上的 `api: "openai-completions"`，OpenClaw 强制 `compat.supportsDeveloperRole: false` 以避免 provider 因不支持 `developer` role 而返回 400 错误。
- 代理式 OpenAI 兼容路由也跳过原生 OpenAI 专属请求 shaping：无 `service_tier`、无 Responses store、无 Completions store、无 prompt-cache hints、无 OpenAI reasoning-compat payload shaping、无隐藏 OpenClaw 归因头。
- 对于需要供应商特有字段的 OpenAI 兼容 Completions 代理，设置 `agents.defaults.models["provider/model"].params.extra_body`（或 `extraBody`）将额外 JSON 合并到出站请求体。
- 对于慢速本地模型或远程 LAN/tailnet 主机，设置 `models.providers.<id>.timeoutSeconds`。这扩展了 provider 模型 HTTP 请求处理，包括连接、头、body 流和总守护获取中止，而不增加整个 agent 运行时超时。
- Model provider HTTP 调用允许 Surge、Clash 和 sing-box 的 `198.18.0.0/15` 和 `fc00::/7` 中的 fake-IP DNS 应答，仅用于配置的 provider `baseUrl` 主机名。自定义/本地 provider 端点也信任该精确配置的 `scheme://host:port` 源用于守护模型请求，包括 loopback、LAN 和 tailnet 主机。
- 如果 `baseUrl` 为空/省略，OpenClaw 保持默认 OpenAI 行为（解析到 `api.openai.com`）。
- 对于 `api: "anthropic-messages"` 在非直接端点（除规范 `anthropic` 外的任何 provider，或自定义 `models.providers.anthropic.baseUrl` 且主机不是公共 `api.anthropic.com` 端点），OpenClaw 抑制隐式 Anthropic beta 头如 `claude-code-20250219`、`interleaved-thinking-2025-05-14` 和 OAuth 标记，以便自定义 Anthropic 兼容代理不拒绝不支持的 beta 标志。如果代理需要特定 beta 功能，显式设置 `models.providers.<id>.headers["anthropic-beta"]`。

## CLI 示例

```
openclaw onboard --auth-choice opencode-zen
openclaw models set opencode/claude-opus-4-6
openclaw models list
```

另见：Configuration 获取完整配置示例。

## 相关 / Related

- Configuration 参考 - 模型配置键
- Model failover - fallback 链和重试行为
- Models - 模型配置和别名
- Providers - 每 provider 设置指南
