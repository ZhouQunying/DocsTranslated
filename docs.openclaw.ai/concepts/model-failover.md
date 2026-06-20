# Model failover / 模型故障转移

## 架构精读

> 跳过不影响阅读翻译正文。

### 运行时流程——7 步状态机的窄持久化设计

OpenClaw 的 failover 是一个精确的 7 步状态机：
1. **解析 session 状态**——获取当前活跃模型和 auth profile 偏好
2. **构建候选链**——从当前选择和 fallback 策略构建候选列表
3. **尝试当前 provider**——带 auth profile 轮换/冷却规则
4. **在可 failover 错误上前进**——provider 耗尽时移动到下一个候选
5. **持久化 fallback 覆盖**——重试开始前将选中的 fallback 写入 session
6. **失败时窄回滚**——仅回滚 fallback 写入的覆盖字段
7. **耗尽时抛 FallbackSummaryError**——带每尝试细节和最早冷却到期时间

关键设计是**窄持久化**——只持久化 fallback 负责的 6 个字段（`providerOverride`、`modelOverride`、`modelOverrideSource`、`authProfileOverride`、`authProfileOverrideSource`、`authProfileOverrideCompactionCount`），而非整个 session。这跟 Git 的 cherry-pick 是一个思路——只挑选特定提交，而非合并整个分支。如果 fallback 重试失败，窄回滚保证不会覆盖其他 session 变更（如用户在尝试期间手动切换模型）。

### Selection source 策略——为什么选这个模型决定了是否允许 fallback

OpenClaw 将"选了哪个模型"和"为什么选它"分开。source 控制是否允许 fallback 链：
- **Configured default**（`agents.defaults.model.primary`）：使用配置的 fallbacks
- **Agent primary**（`agents.list[].model`）：严格，除非该 agent model 对象包含自己的 fallbacks
- **Auto fallback override**：运行时 fallback 写入 `modelOverrideSource: "auto"`，可以继续走配置 fallback 链
- **User session override**（`/model`、模型选择器、`session_status(model=...)`）：写入 `modelOverrideSource: "user"`，严格精确选择
- **Legacy session override**：旧 session 条目可能没有 `modelOverrideSource`，视为 user override
- **Cron payload model**：cron 任务的 `payload.model` 是任务主模型，不是 user session override

这跟 Linux 的文件权限是一个思路。文件权限不仅记录"谁能读"，还记录"这个权限从哪来"（用户级、组级、其他）。OpenClaw 的 selection source 也是这样——不仅记录"选了哪个模型"，还记录"为什么选它"，从而决定 fallback 行为。

设计意图是**防止用户精确选择被静默降级**。如果用户显式用 `/model ollama/qwen3.5:27b` 选了模型，但该模型不可用，OpenClaw 报告失败而非用不相关的 fallback 回答。这保证了用户意图被尊重。

### 冷却指数退避——1min → 5min → 25min → 1hr cap

Rate-limit 冷却使用指数退避：1 分钟 → 5 分钟 → 25 分钟 → 1 小时（上限）。这跟 TCP 的拥塞控制是一个思路——TCP 慢启动时窗口指数增长，检测到拥塞时窗口减半。OpenClaw 的冷却也是这样：每次失败指数增加等待时间，避免对已经过载的 provider 雪崩式重试。

关键区分是**rate-limit vs billing**。Rate-limit 是暂时的（"你现在请求太多了"），用短冷却。Billing 是持久的（"你的钱用完了"），用长冷却（5 小时起步，翻倍增长，24 小时 cap）。这跟数据库连接池的健康检查分类是一个思路——暂时故障（超时）短暂重试，持久故障（认证失败）立即放弃。

Billing 冷却还有一个巧妙设计：24 小时无失败后计数器重置。这避免了"一次 billing 失败永远影响"的问题——如果用户充值了，24 小时后 profile 自动恢复。

### Session stickiness——为缓存友好固定 auth profile

OpenClaw **为每个 session 固定选择的 auth profile**，不在每次请求时轮换。固定的 profile 被复用直到：
- Session 重置（`/new`/`/reset`）
- 压缩完成（compaction count 递增）
- Profile 进入冷却/禁用

这跟 HTTP 的 Keep-Alive 是一个思路。HTTP/1.0 每次请求都重新建立 TCP 连接，开销巨大。HTTP/1.1 的 Keep-Alive 复用同一个连接，利用服务端缓存。OpenClaw 的 session stickiness 也是这样——固定 auth profile 让 provider 端缓存保持温暖，避免每次请求都切换 profile 导致缓存失效。

Auto-pinned profile（session router 选择）被视为**偏好**：优先尝试，但 OpenClaw 可能在 rate limit/超时时轮换到另一个 profile。User-pinned profile（用户通过 `/model …@<profileId>` 显式选择）是**严格**的：如果失败且配置了 model fallback，OpenClaw 移动到下一个模型而非切换 profile。

### 竞态条件预防——在重试开始前持久化 fallback 覆盖

OpenClaw 防止一个经典竞态：
1. 主模型失败
2. 内存中选择 fallback 候选
3. Session store 仍反映旧主模型
4. 实时 session reconciliation 读取陈旧 session 状态
5. 重试在 fallback 尝试开始前被拉回旧模型

解决方案是**在重试开始前持久化选中的 fallback 覆盖字段**到 session 条目。这跟数据库的两阶段提交是一个思路——先写 prepare log，再执行实际变更。如果进程在中间崩溃，prepare log 允许恢复。OpenClaw 的 fallback 覆盖持久化也是这样——先写入 session，再开始重试，保证实时 session reconciliation 看到正确的模型。

窄回滚保证：如果 fallback 尝试失败，runner 仅回滚它写入的覆盖字段，且仅当它们仍匹配该失败候选时。这防止了失败的 fallback 重试覆盖更新的无关 session 变更（如尝试期间发生的手动 `/model` 变更或 session 轮换更新）。

---

OpenClaw 分两个阶段处理失败：
- 当前 provider 内的 **auth profile 轮换**。
- `agents.defaults.model.fallbacks` 中下一个模型的 **model fallback**。

本文档解释运行时规则和支持它们的数据。

## Runtime flow / 运行时流程

对于正常文本运行，OpenClaw 按以下顺序评估候选：

### 解析 session 状态

解析活跃 session 模型和 auth profile 偏好。

### 构建候选链

从当前模型选择和该选择源的 fallback 策略构建模型候选链。配置默认、cron 任务主模型和自动选择的 fallback 模型可以使用配置的 fallback；显式用户 session 选择是严格的。

### 尝试当前 provider

用 auth profile 轮换/冷却规则尝试当前 provider。

### 在可 failover 错误上前进

如果该 provider 因可 failover 错误耗尽，移动到下一个模型候选。

### 持久化 fallback 覆盖

在重试开始前持久化选中的 fallback 覆盖，以便其他 session 读取器看到 runner 即将使用的相同 provider/model。持久化的模型覆盖标记为 `modelOverrideSource: "auto"`。

### 失败时窄回滚

如果 fallback 候选失败，仅回滚 fallback 负责的 session 覆盖字段，当它们仍匹配该失败候选时。

### 耗尽时抛 FallbackSummaryError

如果每个候选都失败，抛出 `FallbackSummaryError`，带每尝试细节和最早冷却到期时间（当已知时）。

这有意比"保存和恢复整个 session"更窄。Reply runner 仅持久化它为 fallback 负责的模型选择字段：
- `providerOverride`
- `modelOverride`
- `modelOverrideSource`
- `authProfileOverride`
- `authProfileOverrideSource`
- `authProfileOverrideCompactionCount`

这防止失败的 fallback 重试覆盖更新的无关 session 变更，如尝试期间发生的手动 `/model` 变更或 session 轮换更新。

## Selection source policy / 选择源策略

OpenClaw 将选中的 provider/model 与**为什么选它**分开。该 source 控制是否允许 fallback 链：

- **Configured default**：`agents.defaults.model.primary` 使用 `agents.defaults.model.fallbacks`。
- **Agent primary**：`agents.list[].model` 是严格的，除非该 agent model 对象包含自己的 `fallbacks`。使用 `fallbacks: []` 使严格行为显式，或提供非空列表使该 agent 选择加入 model fallback。
- **Auto fallback override**：运行时 fallback 在重试前写入 `providerOverride`、`modelOverride`、`modelOverrideSource: "auto"` 和选中的源模型。该自动覆盖可以继续走配置 fallback 链，而不在每条消息上探测主模型，但 OpenClaw 定期再次探测配置的源，并在恢复时清除自动覆盖。`/new`、`/reset` 和 `sessions.reset` 也清除自动源覆盖。没有显式 `heartbeat.model` 的 heartbeat 运行在其源不再匹配当前配置默认时清除直接自动覆盖。
- **User session override**：`/model`、模型选择器、`session_status(model=...)` 和 `sessions.patch` 写入 `modelOverrideSource: "user"`。这是精确 session 选择。如果选中的 provider/model 在生成回复前失败，OpenClaw 报告失败而非从不相关的配置 fallback 回答。
- **Legacy session override**：旧 session 条目可能有 `modelOverride` 但没有 `modelOverrideSource`。OpenClaw 将这些视为 user override，以便显式旧选择不被静默转换为 fallback 行为。
- **Cron payload model**：cron 任务的 `payload.model`/`--model` 是任务主模型，不是 user session override。它使用配置的 fallback，除非任务提供 `payload.fallbacks`；`payload.fallbacks: []` 使 cron 运行严格。

自动 fallback 主模型探测间隔是五分钟，不可配置。OpenClaw 按 session 和主模型记住最近的探测，以便失败的主模型不在每轮重试。当 session 移动到 fallback 时，OpenClaw 发送可见通知，当它返回选中的主模型时发送另一个通知；它不在每个粘性 fallback 轮次重复通知。

## Auth failure skip cache / Auth 失败跳过缓存

默认情况下，每个新轮次保持现有 fallback 重试行为：OpenClaw 将再次尝试每个配置的 fallback 候选，包括最近因 `authorauth_permanent` 失败的非主候选。

偏好抑制这些重复 auth 失败的 operator 可以用以下方式选择加入：

```
OPENCLAW_FALLBACK_SKIP_TTL_MS=60000
```

启用时，OpenClaw 在 auth 类失败后为非主 fallback 候选记录内存、session 作用域的跳过标记。该标记按 session id、provider 和模型键控。主候选永不被跳过，因此显式用户模型选择仍显示真实 auth 错误。缓存是进程本地的，Gateway 重启时清除。

值是毫秒 TTL。`0` 或未设置值禁用缓存。正值被限制在 1 秒到 10 分钟之间。

## User-visible fallback notices / 用户可见的 fallback 通知

当 session 移动到自动选择的 fallback 时，OpenClaw 在同一回复表面发送状态通知：

```
↪️ Model Fallback: <fallback> (selected <primary>; <reason>)
```

当后续探测成功且 session 返回选中的主模型时，OpenClaw 发送：

```
↪️ Model Fallback cleared: <primary> (was <fallback>)
```

这些是操作消息，不是助手内容。它们在每次状态变更时传递一次，包括可行时的纯副作用轮次，但粘性 fallback 轮次不重复它们。传递绕过正常 source-reply 抑制，通知不消耗线程频道的第一个助手回复槽，并从文本到语音和 commitment 提取中排除。

## Auth storage (keys + OAuth) / Auth 存储（密钥 + OAuth）

OpenClaw 对 API 密钥和 OAuth token 使用 **auth profile**。

- 秘密和运行时 auth 路由状态位于 `~/.openclaw/agents/<agentId>/agent/openclaw-agent.sqlite`。
- 配置 `auth.profiles`/`auth.order` 仅是**元数据 + 路由**（无秘密）。
- 遗留仅导入 OAuth 文件：`~/.openclaw/credentials/oauth.json`（首次使用时导入到每 agent auth store）。
- 遗留 `auth-profiles.json`、`auth-state.json` 和每 agent `auth.json` 文件由 `openclaw doctor --fix` 导入。

更多信息：OAuth

凭证类型：
- `type: "api_key"` → `{ provider, key }`
- `type: "oauth"` → `{ provider, access, refresh, expires, email? }`（某些 provider 加 `projectId`/`enterpriseUrl`）

## Profile IDs / Profile ID

OAuth 登录创建不同 profile，以便多个账户可以共存。

- 默认：无邮件时 `provider:default`。
- OAuth 带邮件：`provider:<email>`（例如 `google-antigravity:user@gmail.com`）。

Profile 位于每 agent `openclaw-agent.sqlite` auth profile store 中。

## Rotation order / 轮换顺序

当 provider 有多个 profile 时，OpenClaw 按如下顺序选择：

### 显式配置

`auth.order[provider]`（如果设置）。

### 已配置 profile

`auth.profiles` 按 provider 过滤。

### 存储 profile

每 agent SQLite auth profile 条目按 provider。

如果没有配置显式顺序，OpenClaw 使用 round-robin 顺序：
- 主键：**profile type**（OAuth 优先于 API 密钥）。
- 次键：`usageStats.lastUsed`（每种类型内最旧优先）。
- **冷却/禁用 profile** 移到最后，按最早到期排序。

### Session stickiness（缓存友好）

OpenClaw **为每个 session 固定选择的 auth profile** 以保持 provider 缓存温暖。它**不**在每次请求时轮换。固定的 profile 被复用直到：
- Session 重置（`/new`/`/reset`）
- 压缩完成（compaction count 递增）
- Profile 进入冷却/禁用

通过 `/model …@<profileId>` 的手动选择为该 session 设置 **user override**，不在新 session 开始前自动轮换。

Auto-pinned profile（session router 选择）被视为**偏好**：优先尝试，但 OpenClaw 可能在 rate limit/超时时轮换到另一个 profile。当原 profile 再次可用时，新运行可以再次偏好它，而不改变选中的模型或运行时。User-pinned profile 保持锁定到该 profile；如果失败且配置了 model fallback，OpenClaw 移动到下一个模型而非切换 profile。

### OpenAI Codex 订阅加 API 密钥后备

对于 OpenAI agent 模型，auth 和运行时是分开的。`openai/gpt-*` 保持在 Codex 工具链上，而 auth 可以在 Codex 订阅 profile 和 OpenAI API 密钥后备之间轮换。

使用 `auth.order.openai` 设置用户表面顺序：

```
{
  auth: {
    order: {
      openai: ["openai:user@example.com", "openai:api-key-backup"],
    },
  },
}
```

对 ChatGPT/Codex OAuth profile 和 OpenAI API 密钥 profile 都使用 `openai:*`。当订阅达到 Codex 使用限制时，OpenClaw 在 Codex 提供时记录精确重置时间，尝试下一个有序 auth profile，并保持运行在 Codex 工具链内。一旦重置时间过去，订阅 profile 再次符合条件，下一次自动选择可以返回它。

仅当你想为该 session 强制一个账户/密钥时使用 user-pinned profile。User-pinned profile 有意严格，不静默跳转到另一个 profile。

## Cooldowns / 冷却

当 profile 因 auth/rate-limit 错误（或看起来像 rate limiting 的超时）失败时，OpenClaw 将其标记为冷却并移动到下一个 profile。

该 rate-limit 桶比纯 429 更广：它还包括 provider 消息如 `Too many concurrent requests`、`ThrottlingException`、`concurrency limit reached`、`workers_ai ... quota limit exceeded`、`throttled`、`resource exhausted` 和周期性 usage-window 限制如 `weekly/monthly limit reached`。

格式/无效请求错误通常是终态的，因为重试相同 payload 会以相同方式失败，所以 OpenClaw 显示它们而非轮换 auth profile。已知的重试修复路径可以显式选择加入：例如 Cloud Code Assist 工具调用 ID 验证失败被清理并通过 `allowFormatRetry` 策略重试一次。OpenAI 兼容 stop-reason 错误如 `Unhandled stop reason: error`、`stop reason: error` 和 `reason: error` 被分类为超时/failover 信号。

通用服务器文本也可以在源匹配已知瞬态模式时落入该超时桶。例如，裸模型运行时 stream-wrapper 消息 `An unknown error occurred` 对每个 provider 都被视为可 failover，因为共享模型运行时在 provider 流以 `stopReason: "aborted"` 或 `stopReason: "error"` 结束且无特定细节时发出它。带瞬态服务器文本如 `internal server error`、`unknown error`、520、`upstream error` 或 `backend error` 的 JSON `api_error` payload 也被视为可 failover 超时。

OpenRouter 特有的通用上游文本如裸 `Provider returned error` 仅在 provider 上下文实际是 OpenRouter 时被视为超时。通用内部 fallback 文本如 `LLM request failed with an unknown error.` 保持保守，本身不触发 failover。

某些 provider SDK 可能在返回控制给 OpenClaw 前睡眠长 Retry-After 窗口。对于 Stainless-based SDK 如 Anthropic 和 OpenAI，OpenClaw 默认将 SDK 内部 `retry-after-ms`/`retry-after` 等待限制在 60 秒，并立即显示更长的可重试响应，以便此 failover 路径可以运行。用 `OPENCLAW_SDK_RETRY_MAX_WAIT_SECONDS` 调整或禁用上限；参见 Retry 行为。

Rate-limit 冷却也可以是模型作用域的：
- OpenClaw 在失败模型 id 已知时为 rate-limit 失败记录 `cooldownModel`。
- 当冷却作用域于不同模型时，同一 provider 的兄弟模型仍可以被尝试。
- Billing/禁用窗口仍阻止整个 profile 跨模型。

冷却使用指数退避：
- 1 分钟
- 5 分钟
- 25 分钟
- 1 小时（上限）

状态存储在每 agent SQLite auth state 的 `usageStats` 下：

```
{
  "usageStats": {
    "provider:profile": {
      "lastUsed": 1736160000000,
      "cooldownUntil": 1736160600000,
      "errorCount": 2
    }
  }
}
```

## Billing disables / Billing 禁用

Billing/credit 失败（例如 "insufficient credits" / "credit balance too low"）被视为可 failover，但它们通常不是瞬态的。OpenClaw 不采用短冷却，而是将 profile 标记为**禁用**（带更长退避）并轮换到下一个 profile/provider。

不是每个 billing 形状的响应都是 402，也不是每个 HTTP 402 都落入这里。OpenClaw 即使 provider 返回 401 或 403，也将显式 billing 文本保持在 billing 通道，但 provider 特有匹配器保持在其负责的 provider 作用域内（例如 OpenRouter 403 `Key limit exceeded`）。

同时暂时 402 usage-window 和 organization/workspace spend-limit 错误在消息看起来可重试时被分类为 `rate_limit`（例如 `weekly usage limit exhausted`、`daily limit reached, resets tomorrow` 或 `organization spending limit exceeded`）。那些保持在短冷却/failover 路径而非长 billing-禁用路径。

状态存储在每 agent SQLite auth state：

```
{
  "usageStats": {
    "provider:profile": {
      "disabledUntil": 1736178000000,
      "disabledReason": "billing"
    }
  }
}
```

默认：
- Billing 退避从 **5 小时**开始，每次 billing 失败翻倍，上限 **24 小时**。
- 如果 profile 24 小时（可配置）未失败，退避计数器重置。
- 过载重试允许 **1 次**同 provider profile 轮换，然后 model fallback。
- 过载重试默认使用 **0 ms 退避**。

## Model fallback / 模型 fallback

如果 provider 的所有 profile 都失败，OpenClaw 移动到 `agents.defaults.model.fallbacks` 中的下一个模型。这适用于 auth 失败、rate limit 和耗尽 profile 轮换的超时（其他错误不推进 fallback）。不暴露足够细节的 provider 错误仍在 fallback 状态中精确标记。`empty_response` 表示 provider 未返回可用消息或状态，`no_error_details` 表示 provider 显式返回 `Unknown error (no error details in response)`，`unclassified` 表示 OpenClaw 保留了原始预览但没有分类器匹配它。

过载和 rate-limit 错误比 billing 冷却更积极处理。默认情况下，OpenClaw 允许一次同 provider auth profile 重试，然后切换到下一个配置 model fallback 而不等待。Provider-busy 信号如 `ModelNotReadyException` 落入该过载桶。用 `auth.cooldowns.overloadedProfileRotations`、`auth.cooldowns.overloadedBackoffMs` 和 `auth.cooldowns.rateLimitedProfileRotations` 调整。

当运行从配置默认主模型、cron 任务主模型、带显式 fallback 的 agent 主模型或自动选择的 fallback 覆盖开始时，OpenClaw 可以走匹配的配置 fallback 链。没有显式 fallback 的 agent 主模型和显式用户选择（例如 `/model ollama/qwen3.5:27b`、模型选择器、`sessions.patch` 或一次性 CLI provider/model 覆盖）是严格的。如果该 provider/model 不可达或在生成回复前失败，OpenClaw 报告失败而非从不相关的 fallback 回答。

### 候选链规则

OpenClaw 从当前请求的 `provider/model` 加配置 fallback 构建候选列表。

- 请求的模型总是第一个。
- 显式配置 fallback 去重但不按模型允许列表过滤。它们被视为显式 operator 意图。
- 如果当前运行已经在同一 provider 系列的配置 fallback 上，OpenClaw 继续使用完整配置链。
- 当没有提供显式 fallback 覆盖时，配置 fallback 在配置主模型之前尝试，即使请求的模型使用不同 provider。
- 当没有向 fallback runner 提供显式 fallback 覆盖时，配置主模型追加到最后，以便链可以在早期候选耗尽后回到正常默认。
- 当调用者提供 `fallbacksOverride` 时，runner 使用精确请求的模型加该覆盖列表。空列表禁用 model fallback 并防止配置主模型被追加为隐藏重试目标。

### Which errors advance fallback / 哪些错误推进 fallback

#### 继续于

- auth 失败
- rate limit 和冷却耗尽
- overloaded/provider-busy 错误
- timeout 形状的 failover 错误
- billing 禁用
- `LiveSessionModelSwitchError`，归一化为 failover 路径，以便陈旧持久化模型不创建外部重试循环
- 仍有剩余候选时的其他未识别错误

#### 不继续于

- 不是 timeout/failover 形状的显式中止
- 应保持在压缩/重试逻辑内的上下文溢出错误（例如 `request_too_large`、`INVALID_ARGUMENT: input exceeds the maximum number of tokens`、`input token count exceeds the maximum number of input tokens`、`The input is too long for the model` 或 `ollama error: context length exceeded`）
- 没有剩余候选时的最终未知错误

### Cooldown skip vs probe behavior / 冷却跳过 vs 探测行为

当 provider 的每个 auth profile 都已在冷却中时，OpenClaw 不自动永远跳过该 provider。它做每候选决策：

- 持久 auth 失败立即跳过整个 provider。
- Billing 禁用通常跳过，但主候选仍可以在节流时被探测，以便无需重启即可恢复。
- 主候选可以在冷却到期附近被探测，带每 provider 节流。
- 同 provider fallback 兄弟可以在失败看起来瞬态（`rate_limit`、`overloaded` 或 `unknown`）时尽管冷却仍被尝试。这当 rate limit 是模型作用域且兄弟模型可能立即恢复时特别相关。
- 瞬态冷却探测限制为每 provider 每 fallback 运行一次，以便单个 provider 不阻塞跨 provider fallback。

## Session 覆盖和实时模型切换

Session 模型变更是共享状态。活跃 runner、`/model` 命令、压缩/session 更新和实时 session reconciliation 都读取或写入同一 session 条目的部分。

这意味着 fallback 重试必须与实时模型切换协调：

- 仅显式用户驱动的模型变更标记待处理实时切换。这包括 `/model`、`session_status(model=...)` 和 `sessions.patch`。
- 系统驱动的模型变更如 fallback 轮换、heartbeat 覆盖或压缩本身不标记待处理实时切换。
- 用户驱动的模型覆盖被视为 fallback 策略的精确选择，因此不可达的选中 provider 显示为失败而非被 `agents.defaults.model.fallbacks` 掩盖。
- 在 fallback 重试开始前，reply runner 将选中的 fallback 覆盖字段持久化到 session 条目。
- 自动 fallback 覆盖在后续轮次保持选中，以便 OpenClaw 不在每条消息上探测已知坏的主模型。OpenClaw 定期再次探测配置的源，并在恢复时清除自动覆盖；`/new`、`/reset` 和 `sessions.reset` 立即清除自动源覆盖。
- 用户回复宣布 fallback 转换和 fallback-cleared 恢复每次状态变更一次。粘性 fallback 轮次不重复通知。
- `/status` 显示选中的模型，当 fallback 状态不同时，显示活跃 fallback 模型和原因。
- 实时 session reconciliation 优先于持久化 session 覆盖而非陈旧运行时模型字段。
- 如果实时切换错误指向活跃 fallback 链中的后续候选，OpenClaw 直接跳转到该选中模型而非先走无关候选。
- 如果 fallback 尝试失败，runner 仅回滚它写入的覆盖字段，且仅当它们仍匹配该失败候选时。

这防止了经典竞态：

### 主模型失败

选中的主模型失败。

### 内存中选择 fallback

Fallback 候选在内存中选择。

### Session store 仍说旧主模型

Session store 仍反映旧主模型。

### 实时 reconciliation 读取陈旧状态

实时 session reconciliation 读取陈旧 session 状态。

### 重试被拉回

重试在 fallback 尝试开始前被拉回旧模型。

持久化的 fallback 覆盖关闭该窗口，窄回滚保持更新的手动或运行时 session 变更完整。

## Observability and failure summaries / 可观测性和失败摘要

`runWithModelFallback(...)` 记录每尝试细节，为日志和用户可见冷却消息提供信息：

- 尝试的 provider/model
- 原因（`rate_limit`、`overloaded`、`billing`、`auth`、`model_not_found` 和类似 failover 原因）
- 可选状态/代码
- 人类可读错误摘要

结构化 `model_fallback_decision` 日志还包括当候选失败、被跳过或后续 fallback 成功时的扁平 `fallbackStep*` 字段。这些字段使尝试的转换显式（`fallbackStepFromModel`、`fallbackStepToModel`、`fallbackStepFromFailureReason`、`fallbackStepFromFailureDetail`、`fallbackStepFinalOutcome`），以便日志和诊断导出器可以重建主模型失败，即使终端 fallback 也失败。

当每个候选都失败时，OpenClaw 抛出 `FallbackSummaryError`。外部 reply runner 可以用它构建更特定的消息如 "all models are temporarily rate-limited"，并在已知时包括最早冷却到期时间。

该冷却摘要是模型感知的：
- 无关模型作用域 rate limit 被忽略用于尝试的 provider/model 链
- 如果剩余阻止是匹配模型作用域 rate limit，OpenClaw 报告仍阻止该模型的最后匹配到期时间

## Related config / 相关配置

参见 Gateway configuration 获取：

- `auth.profiles`/`auth.order`
- `auth.cooldowns.billingBackoffHours`/`auth.cooldowns.billingBackoffHoursByProvider`
- `auth.cooldowns.billingMaxHours`/`auth.cooldowns.failureWindowHours`
- `auth.cooldowns.overloadedProfileRotations`/`auth.cooldowns.overloadedBackoffMs`
- `auth.cooldowns.rateLimitedProfileRotations`
- `agents.defaults.model.primary`/`agents.defaults.model.fallbacks`
- `agents.defaults.imageModel` 路由

参见 Models 获取更广泛的模型选择和 fallback 概览。
