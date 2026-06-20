# Models CLI / 模型 CLI

## 架构精读

> 跳过不影响阅读翻译正文。

### 模型选择优先级链——跟 DNS 解析一样的分层查找

OpenClaw 选择模型的优先级是：
1. `agents.defaults.model.primary`（或 `agents.defaults.model`）
2. `agents.defaults.model.fallbacks`（按顺序）
3. Provider auth failover（在同一个 provider 内部，切换不同 auth profile）

这跟 DNS 解析的分层查找是一个思路——先查本地缓存，再查 /etc/hosts，再查 DNS 服务器。每一层都是下一层的 fallback。

关键设计是**auth failover 在 provider 内部发生**。比如 OpenAI provider 有三个 auth profile（API key A、API key B、Codex 订阅）。当 A 触发速率限制时，OpenClaw 先尝试 B 和 Codex，而不是直接跳到 fallback model。这避免了不必要的模型切换——同一个模型的不同 auth profile 应该先全部尝试。

### Allowlist 作为安全边界——"Model is not allowed"的 pre-flight 验证

`agents.defaults.models` 设置后成为**显式允许列表**。不在列表中的模型被拒绝，且在生成回复之前——这就是为什么"看起来像没有响应"。

这跟 Kubernetes 的 RBAC 是一个思路。RBAC 不是"你能做什么"，而是"只有明确允许的你才能做"。默认拒绝（deny by default）是安全系统的基本原则。OpenClaw 的 model allowlist 把"agent 能用哪些模型"从隐式（所有可用）变成显式（只允许列表中的）。

`provider/*` 通配符是个巧妙设计——允许某个 provider 的所有模型而不需要逐个列出。新模型从 provider 端加入时自动可用，不需要更新 allowlist。这跟 AWS IAM 的 `arn:aws:s3:::my-bucket/*` 通配符是一个思路。

### Merge vs Replace——配置更新的安全语义

`openclaw config set` 对 model/provider 映射**拒绝纯赋值**（会移除现有条目），强制使用 `--merge`（增量添加）或 `--replace`（显式替换）。

这跟 Git 的 merge vs rebase 是一个思路。纯赋值就像 `git reset --hard`——丢失所有未提交的更改。`--merge` 像 `git merge`——保留现有内容，添加新内容。`--replace` 像 `git reset --hard`，但需要显式声明——用户必须说"我知道这会覆盖所有内容"。

设计意图是**防止意外配置丢失**。当用户想添加一个新模型，却不小心覆盖了整个模型列表时，这是灾难性的。强制 `--merge` 或 `--replace` 让用户明确表达意图。

### Models.json 的 merge 语义——source-authoritative 标记持久化

`models.json` 的 merge 模式优先级：自定义 provider 写入 `models.providers`，provider-plugin catalogs 作为 plugin-owned shards 存储。标记持久化是**source-authoritative**——OpenClaw 从活动源配置快照（pre-resolution）写入标记，而非从已解析的运行时秘密值。

这跟 Terraform 的 state 管理是一个思路。Terraform state 是 source-authoritative——它记录的是 Terraform 认为的资源状态，而非实际查询到的云资源状态。当 state 和实际状态不一致时，Terraform 信任 state（然后用 `terraform plan` 检测差异）。

---

Auth profile rotation, cooldowns, and how that interacts with fallbacks.

Auth profile 轮换、冷却时间以及与 fallback 的交互。

Quick provider overview and examples.

快速 provider 概览和示例。

OpenClaw, Codex, and other agent loop runtimes.

OpenClaw、Codex 和其他 agent 循环运行时。

Model config keys.

模型配置键。

Model refs choose a provider and model. They do not usually choose the low-level agent runtime. OpenAI agent refs are the main exception: `openai/gpt-5.5` runs through the Codex app-server runtime by default on the official OpenAI provider. Subscription Copilot refs (`github-copilot/*`) can additionally be opted into the external GitHub Copilot agent runtime plugin — that path stays explicit (no autofallback). Explicit runtime overrides belong on provider/model policy, not on the whole agent or session. In Codex runtime mode, the `openai/gpt-*` ref does not imply API-key billing; auth can come from a Codex account or `openai` OAuth profile. See Agent runtimes and GitHub Copilot agent runtime.

Model ref 选择 provider 和模型。它们通常不选择底层 agent 运行时。OpenAI agent ref 是主要例外：`openai/gpt-5.5` 在官方 OpenAI provider 上默认通过 Codex 应用服务器运行时运行。订阅 Copilot ref（`github-copilot/*`）可以额外选择加入外部 GitHub Copilot agent 运行时插件——该路径保持显式（无自动回退）。显式运行时覆盖属于 provider/model 策略，而非整个 agent 或 session。在 Codex 运行时模式下，`openai/gpt-*` ref 不意味着 API 密钥计费；认证可以来自 Codex 账户或 `openai` OAuth profile。参见 Agent 运行时和 GitHub Copilot agent 运行时。

## How model selection works / 模型选择如何工作

OpenClaw selects models in this order:

OpenClaw 按以下顺序选择模型：

### Primary model / 主模型

`agents.defaults.model.primary` (or `agents.defaults.model`).

### Fallbacks / 后备模型

`agents.defaults.model.fallbacks` (in order).

`agents.defaults.model.fallbacks`（按顺序）。

### Provider auth failover / Provider 认证故障转移

Auth failover happens inside a provider before moving to the next model.

认证故障转移在移动到下一个模型之前在 provider 内部发生。

## Selection source and fallback behavior / 选择源和后备行为

The same `provider/model` can mean different things depending on where it came from:

同一个 `provider/model` 根据来源可能意味着不同的事情：

## Quick model policy / 快速模型策略

## Onboarding (recommended) / 入门（推荐）

If you don't want to hand-edit config, run onboarding:

如果你不想手动编辑配置，运行入门：

```
openclaw onboard
```

It can set up model + auth for common providers, including OpenAI Code (Codex) subscription (OAuth) and Anthropic (API key or Claude CLI).

它可以为常见 provider 设置模型 + 认证，包括 OpenAI Code (Codex) 订阅 (OAuth) 和 Anthropic（API 密钥或 Claude CLI）。

## Config keys (overview) / 配置键（概览）

Model refs are normalized to lowercase. Provider IDs are otherwise exact; use the provider ID advertised by the plugin.

Model ref 被规范化为小写。Provider ID 否则是精确的；使用插件宣传的 provider ID。

Provider configuration examples (including OpenCode) live in OpenCode.

Provider 配置示例（包括 OpenCode）在 OpenCode 中。

### Safe allowlist edits / 安全允许列表编辑

Use additive writes when updating `agents.defaults.models` by hand:

手动更新 `agents.defaults.models` 时使用增量写入：

```
openclaw config set agents.defaults.models '{"openai/gpt-5.4":{}}' --strict-json --merge
```

`openclaw config set` protects model/provider maps from accidental clobbers. A plain object assignment to `agents.defaults.models`, `models.providers`, or `models.providers.<id>.models` is rejected when it would remove existing entries. Use `--merge` for additive changes; use `--replace` only when the provided value should become the complete target value.

`openclaw config set` 保护 model/provider 映射免受意外覆盖。对 `agents.defaults.models`、`models.providers` 或 `models.providers.<id>.models` 的纯对象赋值在会移除现有条目时被拒绝。对增量更改使用 `--merge`；仅当提供的值应成为完整目标值时使用 `--replace`。

Interactive provider setup and `openclaw configure --section model` also merge provider-scoped selections into the existing allowlist, so adding Codex, Ollama, or another provider does not drop unrelated model entries. Configure preserves an existing `agents.defaults.model.primary` when provider auth is re-applied. Explicit default-setting commands such as `openclaw models auth login --provider <id> --set-default` and `openclaw models set <model>` still replace `agents.defaults.model.primary`.

交互式 provider 设置和 `openclaw configure --section model` 也将 provider 作用域的选择合并到现有允许列表中，因此添加 Codex、Ollama 或其他 provider 不会丢弃不相关的模型条目。当 provider 认证被重新应用时，Configure 保留现有的 `agents.defaults.model.primary`。显式默认设置命令如 `openclaw models auth login --provider <id> --set-default` 和 `openclaw models set <model>` 仍会替换 `agents.defaults.model.primary`。

## "Model is not allowed" (and why replies stop) / "模型不被允许"（以及为什么回复停止）

If `agents.defaults.models` is set, it becomes the allowlist for `/model` and for session overrides. When a user selects a model that isn't in that allowlist, OpenClaw returns:

如果 `agents.defaults.models` 被设置，它成为 `/model` 和 session 覆盖的允许列表。当用户选择不在该允许列表中的模型时，OpenClaw 返回：

```
Model "provider/model" is not allowed. Use /models to list providers, or /models <provider> to list models.
Add it with: openclaw config set agents.defaults.models '{"provider/model":{}}' --strict-json --merge
```

This happens before a normal reply is generated, so the message can feel like it "didn't respond." The fix is to either:

这发生在生成正常回复之前，所以消息可能感觉像"没有响应"。修复方法是：

When the rejected command included a runtime override such as `/model openai/gpt-5.5 --runtime codex`, fix the allowlist first, then retry the same `/model ... --runtime ...` command. For native Codex execution, the selected model is still `openai/gpt-5.5`; the `codex` runtime selects the harness and uses Codex auth separately.

当被拒绝的命令包含运行时覆盖如 `/model openai/gpt-5.5 --runtime codex` 时，先修复允许列表，然后重试相同的 `/model ... --runtime ...` 命令。对于原生 Codex 执行，选择的模型仍然是 `openai/gpt-5.5`；`codex` 运行时选择工具链并单独使用 Codex 认证。

For local/GGUF models, store the full provider-prefixed ref in the allowlist, for example `ollama/gemma4:26b`, `lmstudio/Gemma4-26b-a4-it-gguf`, or the exact provider/model shown by `openclaw models list --provider <provider>`. Bare local filenames or display names are not enough when the allowlist is active.

对于本地/GGUF 模型，在允许列表中存储完整的 provider 前缀 ref，例如 `ollama/gemma4:26b`、`lmstudio/Gemma4-26b-a4-it-gguf`，或 `openclaw models list --provider <provider>` 显示的确切 provider/model。当允许列表激活时，纯本地文件名或显示名称不够。

If you want to limit providers without manually listing every model, add `provider/*` entries to `agents.defaults.models`:

如果你想限制 provider 而不手动列出每个模型，将 `provider/*` 条目添加到 `agents.defaults.models`：

```
{
  agents: {
    defaults: {
      models: {
        "openai/*": {},
        "vllm/*": {},
      },
    },
  },
}
```

With that policy, `/model`, `/models`, and model pickers show the discovered catalog for those providers only. New models from the selected providers can appear without editing the allowlist. Exact `provider/model` entries can be mixed with `provider/*` entries when you need one specific model from another provider.

使用该策略，`/model`、`/models` 和模型选择器仅显示这些 provider 的发现目录。来自选定 provider 的新模型可以出现而不需要编辑允许列表。当你需要另一个 provider 的一个特定模型时，精确的 `provider/model` 条目可以与 `provider/*` 条目混合。

Example allowlist config:

示例允许列表配置：

```
{
  agents: {
    defaults: {
      model: { primary: "anthropic/claude-sonnet-4-6" },
      models: {
        "anthropic/claude-sonnet-4-6": { alias: "Sonnet" },
        "anthropic/claude-opus-4-6": { alias: "Opus" },
      },
    },
  },
}
```

## Switching models in chat (/model) / 在聊天中切换模型

You can switch models for the current session without restarting:

不重启即可为当前 session 切换模型：

```
/model
/model list
/model 3
/model openai/gpt-5.4
/model default
/model status
```

Full command behavior/config: Slash commands.

完整命令行为/配置：斜杠命令。

## CLI commands / CLI 命令

```
openclaw models list
openclaw models status
openclaw models set <provider/model>
openclaw models set-image <provider/model>
openclaw models aliases list
openclaw models aliases add <alias> <provider/model>
openclaw models aliases remove <alias>
openclaw models fallbacks list
openclaw models fallbacks add <provider/model>
openclaw models fallbacks remove <provider/model>
openclaw models fallbacks clear
openclaw models image-fallbacks list
openclaw models image-fallbacks add <provider/model>
openclaw models image-fallbacks remove <provider/model>
openclaw models image-fallbacks clear
```

`openclaw models` (no subcommand) is a shortcut for `models status`.

`openclaw models`（无子命令）是 `models status` 的快捷方式。

### models list / 模型列表

Shows configured/auth-available models by default. Useful flags:

默认显示已配置/认证可用的模型。有用的标志：

Full catalog. Includes bundled provider-owned static catalog rows before auth is configured, so discovery-only views can show models that are unavailable until you add matching provider credentials.

完整目录。在配置认证之前包含捆绑的 provider 自带静态目录行，因此仅发现视图可以显示在你添加匹配的 provider 凭证之前不可用的模型。

Local providers only.

仅本地 provider。

Filter by provider id, for example `moonshot`. Display labels from interactive pickers are not accepted.

按 provider id 过滤，例如 `moonshot`。不接受来自交互式选择器的显示标签。

One model per line.

每行一个模型。

Machine-readable output.

机器可读输出。

### models status / 模型状态

Shows the resolved primary model, fallbacks, image model, and an auth overview of configured providers. It also surfaces OAuth expiry status for profiles found in the auth store (warns within 24h by default). `--plain` prints only the resolved primary model.

显示已解析的主模型、后备模型、图像模型和已配置 provider 的认证概览。它还显示在认证存储中找到的 profile 的 OAuth 过期状态（默认在 24 小时内警告）。`--plain` 仅打印已解析的主模型。

Auth choice is provider/account dependent. For always-on gateway hosts, API keys are usually the most predictable; Claude CLI reuse and existing Anthropic OAuth/token profiles are also supported.

认证选择取决于 provider/账户。对于始终在线的 gateway 主机，API 密钥通常是最可预测的；也支持 Claude CLI 复用和现有的 Anthropic OAuth/token profile。

Example (Claude CLI):

示例（Claude CLI）：

```
claude auth login
openclaw models status
```

## Scanning (OpenRouter free models) / 扫描（OpenRouter 免费模型）

`openclaw models scan` inspects OpenRouter's free model catalog and can optionally probe models for tool and image support.

`openclaw models scan` 检查 OpenRouter 的免费模型目录，并可以选择性地探测模型的工具和图像支持。

Skip live probes (metadata only).

跳过实时探测（仅元数据）。

Set `agents.defaults.model.primary` to the first selection.

将 `agents.defaults.model.primary` 设置为第一个选择。

Set `agents.defaults.imageModel.primary` to the first image selection.

将 `agents.defaults.imageModel.primary` 设置为第一个图像选择。

The OpenRouter/models catalog is public, so metadata-only scans can list free candidates without a key. Probing and inference still require an OpenRouter API key (from auth profiles or `OPENROUTER_API_KEY`). If no key is available, `openclaw models scan` falls back to metadata-only output and leaves config unchanged. Use `--no-probe` to request metadata-only mode explicitly.

OpenRouter/models 目录是公共的，因此仅元数据扫描无需密钥即可列出免费候选。探测和推理仍需要 OpenRouter API 密钥（来自 auth profile 或 `OPENROUTER_API_KEY`）。如果没有可用密钥，`openclaw models scan` 回退到仅元数据输出并保持配置不变。使用 `--no-probe` 显式请求仅元数据模式。

Scan results are ranked by:

扫描结果按以下排序：

When live probes run in a TTY, you can select fallbacks interactively. In non-interactive mode, pass `--yes` to accept defaults. Metadata-only results are informational; `--set-default` and `--set-image` require live probes so OpenClaw does not configure an unusable keyless OpenRouter model.

当实时探测在 TTY 中运行时，你可以交互式选择后备模型。在非交互模式下，传递 `--yes` 接受默认值。仅元数据结果是信息性的；`--set-default` 和 `--set-image` 需要实时探测，以便 OpenClaw 不配置不可用的无密钥 OpenRouter 模型。

## Models registry (models.json) / 模型注册表

Custom providers in `models.providers` are written into `models.json` under the agent directory (default `~/.openclaw/agents/<agentId>/agent/models.json`). Provider-plugin catalogs are stored as generated plugin-owned catalog shards under the agent's plugin state and loaded automatically. This file is merged by default unless `models.mode` is set to `replace`.

`models.providers` 中的自定义 provider 被写入 agent 目录下的 `models.json`（默认 `~/.openclaw/agents/<agentId>/agent/models.json`）。Provider-plugin 目录作为生成的 plugin 自带目录分片存储在 agent 的插件状态下并自动加载。此文件默认合并，除非 `models.mode` 设置为 `replace`。

Merge mode precedence for matching provider IDs:

匹配 provider ID 的合并模式优先级：

Marker persistence is source-authoritative: OpenClaw writes markers from the active source config snapshot (pre-resolution), not from resolved runtime secret values. This applies whenever OpenClaw regenerates `models.json`, including command-driven paths like `openclaw agent`.

标记持久化是源权威的：OpenClaw 从活动源配置快照（预解析）写入标记，而非从已解析的运行时秘密值。这适用于 OpenClaw 重新生成 `models.json` 的任何时候，包括命令驱动的路径如 `openclaw agent`。

## Related / 相关

- [Agent runtimes](/concepts/agent-runtimes) — Agent 运行时
- [Models](/providers/models) — Provider 快速开始和配置
