# Model failover / 模型故障转移

## 架构精读

> 跳过不影响阅读翻译正文。

### 运行时流程——7 步状态机的窄持久化设计

OpenClaw 的 failover 是一个精确的 7 步状态机：
1. **解析 session 状态**——确定当前活跃的模型和 auth profile
2. **构建候选链**——根据当前选择和 fallback 策略列出候选列表
3. **尝试当前 provider**——按 auth profile 轮换和冷却规则尝试
4. **遇到可 failover 的错误就前进**——当前 provider 用完了就切到下一个候选
5. **持久化 fallback 覆盖**——重试之前把选中的 fallback 写进 session
6. **失败时窄回滚**——只回滚 fallback 自己写入的字段
7. **全部耗尽时抛 FallbackSummaryError**——包含每次尝试的详情和最近的冷却到期时间

关键设计是**窄持久化**——只持久化 fallback 相关的 6 个字段（`providerOverride`、`modelOverride`、`modelOverrideSource`、`authProfileOverride`、`authProfileOverrideSource`、`authProfileOverrideCompactionCount`），而不是整个 session。这跟 Git 的 cherry-pick 是一个思路——只挑特定提交，而不是合并整个分支。如果 fallback 重试也失败了，窄回滚保证不会覆盖其他 session 变更（比如用户在尝试期间手动切换了模型）。

### Selection source 策略——模型是怎么选出来的，决定了能不能 fallback

OpenClaw 把"选了哪个模型"和"这个选择是怎么来的"分开记录。选择的来源决定了是否允许 fallback 链：
- **配置默认**（`agents.defaults.model.primary`）：可以用 fallback
- **Agent 主模型**（`agents.list[].model`）：不能用 fallback，除非该 agent 自己配了 fallbacks
- **自动 fallback 覆盖**：运行时自动切到 fallback 后写入 `modelOverrideSource: "auto"`，可以继续往下走 fallback 链
- **用户手动选择**（`/model`、模型选择器、`session_status(model=...)`）：写入 `modelOverrideSource: "user"`，严格锁定，不能 fallback
- **旧版 session 覆盖**：老 session 条目可能没有 `modelOverrideSource` 字段，按用户手动选择处理
- **Cron 任务模型**：cron 任务的 `payload.model` 是任务的主模型，不算用户手动选择

这跟 Linux 的文件权限是一个思路。文件权限不仅记录"谁能读"，还记录"这个权限从哪来"（用户级、组级、其他）。OpenClaw 的 selection source 也是这样——不仅记录"选了哪个模型"，还记录"这个选择是怎么来的"，从而决定 fallback 行为。

设计意图是**不让用户的精确选择被悄悄降级**。如果用户用 `/model ollama/qwen3.5:27b` 明确选了一个模型，但这个模型挂了，OpenClaw 会直接报错，而不是偷偷用一个不相关的 fallback 来回答。用户的意图必须被尊重。

### 冷却指数退避——1min → 5min → 25min → 1hr 封顶

Rate-limit 冷却采用指数退避：1 分钟 → 5 分钟 → 25 分钟 → 1 小时封顶。这跟 TCP 拥塞控制是一个思路——TCP 慢启动时窗口指数增长，检测到拥塞时窗口减半。OpenClaw 的冷却也是这样：每次失败都让等待时间指数增加，避免对已经过载的 provider 雪崩式重试。

关键区分是 **rate-limit vs billing**。Rate-limit 是暂时的（"你现在请求太多了"），所以用短冷却。Billing 是持久的（"你的钱用完了"），所以用长冷却（5 小时起步，翻倍增长，24 小时封顶）。这跟数据库连接池的健康检查分类是一个思路——暂时故障（超时）短暂重试，持久故障（认证失败）立即放弃。

Billing 冷却还有一个巧妙设计：24 小时没再失败就重置计数器。这就避免了"一次 billing 失败永远被影响"的问题——用户充值以后，24 小时后 profile 自动恢复。

### Session stickiness——为缓存友好固定 auth profile

OpenClaw **给每个 session 固定一个 auth profile**，不是每次请求都换。固定的 profile 一直用到：
- Session 重置（`/new`/`/reset`）
- 压缩完成（compaction count 递增）
- Profile 进入冷却或被禁用

这跟 HTTP 的 Keep-Alive 是一个思路。HTTP/1.0 每次请求都重新建 TCP 连接，开销巨大。HTTP/1.1 的 Keep-Alive 复用同一个连接，服务端缓存就能生效。OpenClaw 的 session stickiness 也是这样——固定 auth profile 让 provider 端缓存保持温热，避免每次请求都切 profile 导致缓存失效。

自动固定的 profile（session router 选的）只是**偏好**：优先用，但遇到 rate limit 或超时时 OpenClaw 可能换另一个 profile。用户手动固定的 profile（通过 `/model …@<profileId>` 选的）是**锁定**的：如果失败了且配了 model fallback，OpenClaw 会切到下一个模型而不是换 profile。

### 竞态条件预防——重试之前就写好 fallback 覆盖

OpenClaw 防的是一个经典竞态：
1. 主模型挂了
2. 内存里选了 fallback 候选
3. 但 session 里还写着旧的主模型
4. 实时 session reconciliation 读到的是旧状态
5. 重试还没开始就被拽回旧模型了

解决方案是**在重试之前就把选中的 fallback 字段写进 session**。这跟数据库的两阶段提交是一个思路——先写 prepare log，再执行实际变更。进程在中间崩了，prepare log 可以恢复。OpenClaw 的 fallback 覆盖持久化也是这样——先写 session，再开始重试，这样实时 session reconciliation 读到的就是正确的模型。

窄回滚保证：如果 fallback 尝试也失败了，runner 只回滚它自己写入的字段，而且只在字段值仍然匹配那个失败候选时才回滚。这样就不会覆盖掉其他更新的 session 变更（比如尝试期间用户手动执行了 `/model`，或者 session 轮换更新了）。

---

OpenClaw 分两个阶段处理失败：
- 当前 provider 内部的 **auth profile 轮换**。
- `agents.defaults.model.fallbacks` 中下一个模型的 **model fallback**。

本文档解释运行时规则和相关数据。

## Runtime flow / 运行时流程

对于正常的文本生成，OpenClaw 按以下顺序评估候选：

### 解析 session 状态

确定当前活跃的 session 模型和 auth profile。

### 构建候选链

根据当前模型选择和选择来源的 fallback 策略，构建候选链。配置默认值、cron 任务主模型、以及自动切过去的 fallback 模型都可以继续走 fallback 链；用户手动选的模型是锁定的，不走 fallback。

### 尝试当前 provider

按 auth profile 轮换和冷却规则尝试当前 provider。

### 遇到可 failover 的错误就前进

如果当前 provider 用完了（因为可 failover 的错误），就切到下一个候选。

### 持久化 fallback 覆盖

在重试之前就把选中的 fallback 写进 session，这样其他读 session 的地方也能看到 runner 即将使用的 provider/model。持久化的模型覆盖标记为 `modelOverrideSource: "auto"`。

### 失败时窄回滚

如果 fallback 候选也失败了，只回滚 fallback 自己写入的 session 字段——而且只在字段值仍然匹配那个失败候选时才回滚。

### 全部耗尽时抛 FallbackSummaryError

如果所有候选都失败了，抛出 `FallbackSummaryError`，包含每次尝试的详情和最近的冷却到期时间（如果有的话）。

这有意比"保存和恢复整个 session"做得更少。Reply runner 只持久化跟 fallback 相关的模型选择字段：
- `providerOverride`
- `modelOverride`
- `modelOverrideSource`
- `authProfileOverride`
- `authProfileOverrideSource`
- `authProfileOverrideCompactionCount`

这样就不会覆盖掉其他更新的 session 变更——比如尝试期间用户手动执行了 `/model`，或者 session 轮换更新了。

## Selection source policy / 选择来源策略

OpenClaw 把"选了哪个 provider/model"和"**这个选择是怎么来的**"分开记录。选择的来源决定了能不能走 fallback 链：

- **配置默认**：`agents.defaults.model.primary`，可以走 `agents.defaults.model.fallbacks`。
- **Agent 主模型**：`agents.list[].model` 是锁定的，除非该 agent 的 model 对象自己配了 `fallbacks`。用 `fallbacks: []` 可以显式表示"就是不要 fallback"，或者给一个非空列表让该 agent 走 fallback。
- **自动 fallback 覆盖**：运行时切到 fallback 后，会在重试前写入 `providerOverride`、`modelOverride`、`modelOverrideSource: "auto"` 和源模型。这个自动覆盖可以继续走 fallback 链，不需要每条消息都探测主模型——但 OpenClaw 会定期探测主模型是否恢复，恢复了就清除自动覆盖。`/new`、`/reset` 和 `sessions.reset` 也会清除自动覆盖。没有显式 `heartbeat.model` 的 heartbeat 运行，在源模型不再匹配当前配置默认值时，会直接清除自动覆盖。
- **用户手动覆盖**：`/model`、模型选择器、`session_status(model=...)` 和 `sessions.patch` 写入 `modelOverrideSource: "user"`。这是一个精确的 session 级选择。如果选的 provider/model 在生成回复之前就挂了，OpenClaw 直接报错，不会偷偷从不相关的 fallback 回答。
- **旧版 session 覆盖**：老 session 条目可能有 `modelOverride` 但没有 `modelOverrideSource`。OpenClaw 把它们当用户手动覆盖处理——这样老的显式选择就不会被悄悄变成 fallback 行为。
- **Cron 任务模型**：cron 任务的 `payload.model`/`--model` 是任务的主模型，不算用户手动覆盖。它走配置的 fallback，除非任务自己提供了 `payload.fallbacks`；`payload.fallbacks: []` 让 cron 运行不走 fallback。

自动 fallback 的主模型探测间隔是五分钟，不可配置。OpenClaw 按 session 和主模型记录最近的探测，避免失败的主模型在每轮都被重试。当 session 切到 fallback 时，OpenClaw 发一条通知；当主模型恢复切回来时，再发一条通知。粘性 fallback 轮次不会重复发通知。

## Auth failure skip cache / Auth 失败跳过缓存

默认情况下，每个新轮次都保持原有的 fallback 重试行为：OpenClaw 会再次尝试所有 fallback 候选，包括那些最近刚因为 `authorauth_permanent` 失败过的非主候选。

如果想抑制这些重复的 auth 失败，可以配置：

```
OPENCLAW_FALLBACK_SKIP_TTL_MS=60000
```

启用后，OpenClaw 会在 auth 类失败后，为非主 fallback 候选记录一个内存中的、session 级别的跳过标记。标记按 session id、provider 和模型键控。主候选永远不会被跳过，所以用户手动选的模型仍然会报出真正的 auth 错误。缓存是进程本地的，Gateway 重启后清空。

值是毫秒 TTL。`0` 或不设置表示禁用。正值被限制在 1 秒到 10 分钟之间。

## User-visible fallback notices / 用户可见的 fallback 通知

当 session 自动切到 fallback 时，OpenClaw 在同一回复界面发一条状态通知：

```
↪️ Model Fallback: <fallback> (selected <primary>; <reason>)
```

当主模型恢复、session 切回来时，OpenClaw 发：

```
↪️ Model Fallback cleared: <primary> (was <fallback>)
```

这些是运维消息，不是助手内容。每次状态变更时发一次，包括纯副作用的轮次（如果可行的话），但粘性 fallback 轮次不会重复发。传递时绕过正常的 source-reply 抑制机制，不占用线程频道的第一个助手回复槽位，也不会被文本转语音和 commitment 提取处理。

## Auth storage (keys + OAuth) / Auth 存储（密钥 + OAuth）

OpenClaw 把 API 密钥和 OAuth token 统一用 **auth profile** 管理。

- 密钥和运行时 auth 路由状态存在 `~/.openclaw/agents/<agentId>/agent/openclaw-agent.sqlite`。
- 配置文件中的 `auth.profiles`/`auth.order` 只是**元数据和路由信息**（不含密钥）。
- 旧版仅导入的 OAuth 文件：`~/.openclaw/credentials/oauth.json`（首次使用时导入到每个 agent 的 auth store）。
- 旧版的 `auth-profiles.json`、`auth-state.json` 和每个 agent 的 `auth.json` 文件由 `openclaw doctor --fix` 导入。

更多信息：OAuth

凭证类型：
- `type: "api_key"` → `{ provider, key }`
- `type: "oauth"` → `{ provider, access, refresh, expires, email? }`（某些 provider 还有 `projectId`/`enterpriseUrl`）

## Profile IDs / Profile ID

OAuth 登录会创建不同的 profile，这样多个账户可以共存。

- 默认：没有邮箱时用 `provider:default`。
- OAuth 带邮箱：`provider:<email>`（例如 `google-antigravity:user@gmail.com`）。

Profile 存在每个 agent 自己的 `openclaw-agent.sqlite` auth profile store 中。

## Rotation order / 轮换顺序

当一个 provider 有多个 profile 时，OpenClaw 按以下顺序选择：

### 显式配置

`auth.order[provider]`（如果设了的话）。

### 已配置 profile

`auth.profiles` 中按 provider 过滤出来的条目。

### 存储的 profile

每个 agent SQLite auth profile store 中该 provider 的条目。

如果没有配显式顺序，OpenClaw 用 round-robin 顺序：
- 主键：**profile 类型**（OAuth 排在 API 密钥前面）。
- 次键：`usageStats.lastUsed`（同类型内，最久没用的优先）。
- **冷却中或被禁用的 profile** 排到最后，按最早到期时间排序。

### Session stickiness（缓存友好）

OpenClaw **给每个 session 固定一个 auth profile**，保持 provider 缓存温热。**不**会每次请求都换。固定的 profile 一直用到：
- Session 重置（`/new`/`/reset`）
- 压缩完成（compaction count 递增）
- Profile 进入冷却或被禁用

通过 `/model …@<profileId>` 手动选择后，该 session 就**锁定**在这个 profile 上，新 session 开始前不会自动轮换。

自动固定的 profile（session router 选的）只是**偏好**：优先用，但遇到 rate limit 或超时时 OpenClaw 可能换另一个 profile。原 profile 恢复后，新的运行又可以优先用它，不需要改模型或运行时。用户手动固定的 profile 是**锁定**的：如果失败了且配了 model fallback，OpenClaw 切到下一个模型而不是换 profile。

### OpenAI Codex 订阅加 API 密钥后备

对于 OpenAI agent 模型，auth 和运行时是分开的。`openai/gpt-*` 始终走 Codex 工具链，但 auth 可以在 Codex 订阅 profile 和 OpenAI API 密钥后备之间轮换。

用 `auth.order.openai` 设置用户看到的顺序：

```
{
  auth: {
    order: {
      openai: ["openai:user@example.com", "openai:api-key-backup"],
    },
  },
}
```

ChatGPT/Codex OAuth profile 和 OpenAI API 密钥 profile 都用 `openai:*`。当订阅达到 Codex 使用限制时，OpenClaw 会记录 Codex 给出的精确重置时间（如果有的话），然后尝试下一个 auth profile，同时保持运行在 Codex 工具链内。重置时间过了以后，订阅 profile 就重新可用，下次自动选择时可以切回来。

只有当你想让某个 session 强制用一个账户或密钥时，才用 user-pinned profile。User-pinned profile 有意做得严格，不会偷偷跳到另一个 profile。

## Cooldowns / 冷却

当 profile 因为 auth/rate-limit 错误（或看起来像 rate limiting 的超时）失败时，OpenClaw 把它标记为冷却中，然后切到下一个 profile。

这里的 rate-limit 判定比纯 429 更广：还包括 provider 返回的消息如 `Too many concurrent requests`、`ThrottlingException`、`concurrency limit reached`、`workers_ai ... quota limit exceeded`、`throttled`、`resource exhausted`，以及周期性用量限制如 `weekly/monthly limit reached`。

格式错误或无效请求通常是致命的——重试同一个 payload 还是会报同样的错，所以 OpenClaw 直接报错而不是换 auth profile。已知的重试修复路径可以显式启用：比如 Cloud Code Assist 工具调用 ID 验证失败会被清理，然后通过 `allowFormatRetry` 策略重试一次。OpenAI 兼容的 stop-reason 错误如 `Unhandled stop reason: error`、`stop reason: error` 和 `reason: error` 被归类为超时/failover 信号。

通用服务器错误文本如果匹配已知的瞬态模式，也会进入超时桶。比如裸模型运行时 stream-wrapper 消息 `An unknown error occurred` 对所有 provider 都视为可 failover，因为共享模型运行时在 provider 流以 `stopReason: "aborted"` 或 `stopReason: "error"` 结束且没有具体细节时会发出这条消息。带瞬态服务器文本如 `internal server error`、`unknown error`、520、`upstream error` 或 `backend error` 的 JSON `api_error` payload 也被视为可 failover 超时。

OpenRouter 特有的通用上游文本如裸 `Provider returned error` 只在 provider 上下文确实是 OpenRouter 时才视为超时。通用内部 fallback 文本如 `LLM request failed with an unknown error.` 保持保守，本身不触发 failover。

某些 provider SDK 可能在把控制权还给 OpenClaw 之前，先睡一个很长的 Retry-After 窗口。对于基于 Stainless 的 SDK（如 Anthropic 和 OpenAI），OpenClaw 默认把 SDK 内部的 `retry-after-ms`/`retry-after` 等待限制在 60 秒以内，更长的可重试响应会立即返回，让 failover 路径能跑起来。用 `OPENCLAW_SDK_RETRY_MAX_WAIT_SECONDS` 调整或禁用这个上限；参见 Retry 行为。

Rate-limit 冷却也可以是模型维度的：
- 如果知道失败的模型 id，OpenClaw 会为 rate-limit 失败记录 `cooldownModel`。
- 如果冷却只针对某个模型，同一 provider 的其他模型仍然可以被尝试。
- Billing/禁用窗口仍然阻止整个 profile 跨所有模型。

冷却采用指数退避：
- 1 分钟
- 5 分钟
- 25 分钟
- 1 小时（封顶）

状态存在每个 agent SQLite auth state 的 `usageStats` 下：

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

Billing/credit 失败（比如 "insufficient credits" / "credit balance too low"）会触发 failover，但这类问题通常不是暂时的。OpenClaw 不会用短冷却，而是把 profile 标记为**禁用**（更长的退避时间），然后切到下一个 profile/provider。

不是所有 billing 类的响应都是 402，也不是所有 HTTP 402 都归到这里。OpenClaw 即使 provider 返回 401 或 403，也会把明确的 billing 文本归到 billing 通道——但 provider 特有的匹配器只在各自 provider 的作用域内生效（比如 OpenRouter 的 403 `Key limit exceeded`）。

另外，暂时性的 402 用量窗口错误和组织/workspace 消费上限错误，如果消息看起来可重试（比如 `weekly usage limit exhausted`、`daily limit reached, resets tomorrow` 或 `organization spending limit exceeded`），会被归类为 `rate_limit`。这些走短冷却/failover 路径，不走长的 billing 禁用路径。

状态存在每个 agent SQLite auth state 中：

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

默认值：
- Billing 退避从 **5 小时**起步，每次 billing 失败翻倍，上限 **24 小时**。
- 如果 profile 24 小时内（可配置）没有再失败，退避计数器重置。
- 过载重试允许 **1 次**同 provider profile 轮换，然后才走 model fallback。
- 过载重试默认使用 **0 ms 退避**。

## Model fallback / 模型 fallback

如果 provider 的所有 profile 都失败了，OpenClaw 切到 `agents.defaults.model.fallbacks` 中的下一个模型。这适用于 auth 失败、rate limit、以及 profile 轮换用尽后的超时（其他错误不触发 fallback）。没有足够细节的 provider 错误仍然会在 fallback 状态中精确标记。`empty_response` 表示 provider 没有返回任何可用消息或状态，`no_error_details` 表示 provider 明确返回了 `Unknown error (no error details in response)`，`unclassified` 表示 OpenClaw 保留了原始错误预览但没有分类器匹配。

过载和 rate-limit 错误的处理比 billing 禁用更激进。默认情况下，OpenClaw 允许一次同 provider auth profile 重试，然后不等直接切到下一个 model fallback。Provider 繁忙信号如 `ModelNotReadyException` 归入过载桶。用 `auth.cooldowns.overloadedProfileRotations`、`auth.cooldowns.overloadedBackoffMs` 和 `auth.cooldowns.rateLimitedProfileRotations` 调整。

如果运行是从配置默认主模型、cron 任务主模型、配了显式 fallback 的 agent 主模型、或自动 fallback 覆盖开始的，OpenClaw 可以走对应的 fallback 链。没有显式 fallback 的 agent 主模型和用户手动选择（比如 `/model ollama/qwen3.5:27b`、模型选择器、`sessions.patch`、或一次性的 CLI provider/model 覆盖）是锁定的。如果该 provider/model 不可达或在生成回复前失败，OpenClaw 直接报错，不会从不相关的 fallback 回答。

### 候选链规则

OpenClaw 根据当前请求的 `provider/model` 加上配置的 fallback 来构建候选列表。

- 请求的模型永远排第一。
- 显式配置的 fallback 会去重，但不按模型允许列表过滤——它们被视为运维人员的显式意图。
- 如果当前运行已经在同一 provider 系列的 fallback 上，OpenClaw 继续用完整的 fallback 链。
- 没有显式 fallback 覆盖时，配置的 fallback 会在主模型之前尝试——即使请求的模型来自不同 provider。
- 没有显式 fallback 覆盖时，配置的主模型会被追加到链的末尾，这样候选用尽后链可以回到正常默认。
- 调用者提供 `fallbacksOverride` 时，runner 只用请求的模型加该覆盖列表。空列表会禁用 model fallback，并阻止配置主模型被追加为隐藏的重试目标。

### 哪些错误会推进 fallback

#### 会推进

- auth 失败
- rate limit 和冷却耗尽
- overloaded/provider 繁忙错误
- 超时类 failover 错误
- billing 禁用
- `LiveSessionModelSwitchError`，被归一化为 failover 路径，避免陈旧的持久化模型造成外层重试循环
- 仍有剩余候选时的其他未识别错误

#### 不会推进

- 非超时/failover 类的显式中止
- 应该留在压缩/重试逻辑内处理的上下文溢出错误（比如 `request_too_large`、`INVALID_ARGUMENT: input exceeds the maximum number of tokens`、`input token count exceeds the maximum number of input tokens`、`The input is too long for the model` 或 `ollama error: context length exceeded`）
- 没有剩余候选时的最终未知错误

### 冷却跳过 vs 探测行为

当 provider 的所有 auth profile 都在冷却中时，OpenClaw 不会自动永远跳过该 provider。它对每个候选单独做决策：

- 持久性 auth 失败会立即跳过整个 provider。
- Billing 禁用通常跳过，但主候选在节流时仍可能被探测，这样恢复后不需要重启就能用。
- 主候选在冷却快到期时可能被探测，每个 provider 有节流控制。
- 同 provider 的 fallback 兄弟模型，如果失败看起来是暂时的（`rate_limit`、`overloaded` 或 `unknown`），即使有冷却也可能被尝试。这在 rate limit 是模型维度且兄弟模型可能立即恢复时特别有用。
- 瞬态冷却探测限制为每个 provider 每次 fallback 运行最多一次，避免单个 provider 卡住跨 provider fallback。

## Session 覆盖和实时模型切换

Session 模型变更是共享状态。正在运行的 runner、`/model` 命令、压缩/session 更新和实时 session reconciliation 都会读写同一个 session 条目的不同字段。

这意味着 fallback 重试必须跟实时模型切换协调好：

- 只有用户主动发起的模型变更才标记"待处理实时切换"。包括 `/model`、`session_status(model=...)` 和 `sessions.patch`。
- 系统发起的模型变更——如 fallback 轮换、heartbeat 覆盖或压缩——本身不标记"待处理实时切换"。
- 用户发起的模型覆盖在 fallback 策略中被视为精确选择，所以不可达的 provider 会直接报错，不会被 `agents.defaults.model.fallbacks` 掩盖。
- 在 fallback 重试之前，reply runner 把选中的 fallback 字段持久化到 session 条目中。
- 自动 fallback 覆盖在后续轮次保持生效，这样 OpenClaw 不需要每条消息都去探测已知挂了的主模型。OpenClaw 定期探测主模型是否恢复，恢复了就清除自动覆盖；`/new`、`/reset` 和 `sessions.reset` 立即清除自动覆盖。
- 用户回复中，fallback 切换和恢复通知每次状态变更只发一次。粘性 fallback 轮次不重复发通知。
- `/status` 显示当前选中的模型，如果 fallback 状态不同，还会显示活跃的 fallback 模型和原因。
- 实时 session reconciliation 优先读取持久化的 session 覆盖，而不是陈旧的运行时模型字段。
- 如果实时切换错误指向当前 fallback 链中的后续候选，OpenClaw 直接跳到那个模型，而不是先走无关的候选。
- 如果 fallback 尝试失败，runner 只回滚它自己写入的字段，而且只在字段值仍然匹配那个失败候选时才回滚。

这防止了一个经典竞态：

### 主模型失败

选中的主模型失败了。

### 内存里选了 fallback

Fallback 候选在内存中被选中。

### Session 里还是旧主模型

Session 里还写着旧主模型。

### 实时 reconciliation 读到旧状态

实时 session reconciliation 读到的是陈旧 session 状态。

### 重试被拽回去了

重试还没开始就被拽回旧模型了。

持久化的 fallback 覆盖堵住了这个窗口期，窄回滚保证更新的手动或运行时 session 变更不会丢失。

## Observability and failure summaries / 可观测性和失败摘要

`runWithModelFallback(...)` 记录每次尝试的详情，供日志和用户可见的冷却消息使用：

- 尝试的 provider/model
- 原因（`rate_limit`、`overloaded`、`billing`、`auth`、`model_not_found` 等 failover 原因）
- 可选的状态码/错误码
- 人类可读的错误摘要

结构化 `model_fallback_decision` 日志还包括候选失败、被跳过或后续 fallback 成功时的扁平 `fallbackStep*` 字段。这些字段让每次转换都清晰可见（`fallbackStepFromModel`、`fallbackStepToModel`、`fallbackStepFromFailureReason`、`fallbackStepFromFailureDetail`、`fallbackStepFinalOutcome`），即使最终的 fallback 也失败了，日志和诊断导出器也能重建主模型失败的过程。

当所有候选都失败时，OpenClaw 抛出 `FallbackSummaryError`。外层 reply runner 可以用它生成更具体的消息，比如 "all models are temporarily rate-limited"，并在有信息时附带最近的冷却到期时间。

冷却摘要是模型感知的：
- 与尝试的 provider/model 链无关的模型维度 rate limit 会被忽略
- 如果剩余的阻止原因是匹配当前模型的 rate limit，OpenClaw 报告的是仍然阻止该模型的最近到期时间

## Related config / 相关配置

参见 Gateway configuration 获取：

- `auth.profiles`/`auth.order`
- `auth.cooldowns.billingBackoffHours`/`auth.cooldowns.billingBackoffHoursByProvider`
- `auth.cooldowns.billingMaxHours`/`auth.cooldowns.failureWindowHours`
- `auth.cooldowns.overloadedProfileRotations`/`auth.cooldowns.overloadedBackoffMs`
- `auth.cooldowns.rateLimitedProfileRotations`
- `agents.defaults.model.primary`/`agents.defaults.model.fallbacks`
- `agents.defaults.imageModel` 路由

参见 Models 获取更全面的模型选择和 fallback 概览。
