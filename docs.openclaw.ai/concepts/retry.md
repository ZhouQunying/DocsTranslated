# Retry policy

> ## Goals

## 目标

> * Retry per HTTP request, not per multi-step flow.
> * Preserve ordering by retrying only the current step.
> * Avoid duplicating non-idempotent operations.

- 按 HTTP 请求重试，不按多步流程重试。
- 只重试当前步骤，保持顺序。
- 避免重复非幂等操作。

---

> ## Defaults

## 默认值

> * Attempts: 3
> * Max delay cap: 30000 ms
> * Jitter: 0.1 (10 percent)
> * Provider defaults:
>   * Telegram min delay: 400 ms
>   * Discord min delay: 500 ms

- 尝试次数：3
- 最大延迟上限：30000 ms
- 抖动：0.1（10%）
- provider 默认：
  - Telegram 最小延迟：400 ms
  - Discord 最小延迟：500 ms

---

> ## Behavior

## 行为

> ### Model providers

### 模型 provider

> * OpenClaw lets provider SDKs handle normal short retries.
> * For Stainless-based SDKs such as Anthropic and OpenAI, retryable responses (`408`, `409`, `429`, and `5xx`) can include `retry-after-ms` or `retry-after`. When that wait is longer than 60 seconds, OpenClaw injects `x-should-retry: false` so the SDK surfaces the error immediately and model failover can rotate to another auth profile or fallback model.
> * Override the cap with `OPENCLAW_SDK_RETRY_MAX_WAIT_SECONDS=<seconds>`. Set it to `0`, `false`, `off`, `none`, or `disabled` to let SDKs honor long `Retry-After` sleeps internally.

- 短的常规重试由 provider SDK 自己处理。
- Stainless 系 SDK（Anthropic、OpenAI 等）的可重试响应（`408`、`409`、`429`、`5xx`）可能带 `retry-after-ms` 或 `retry-after`。等待大于 60 秒时，OpenClaw 注入 `x-should-retry: false`，让 SDK 立刻把错误抛出来，模型 failover 才能切到另一个认证 profile 或回退模型。
- 用 `OPENCLAW_SDK_RETRY_MAX_WAIT_SECONDS=<秒>` 覆盖上限。设成 `0`、`false`、`off`、`none` 或 `disabled` 时，让 SDK 内部遵守长的 `Retry-After` sleep。

> ### Discord

### Discord

> * Retries on rate-limit errors (HTTP 429), request timeouts, HTTP 5xx responses, and transient transport failures such as DNS lookup failures, connection resets, socket closes, and fetch failures.
> * Uses Discord `retry_after` when available, otherwise exponential backoff.

- 在限速错误（HTTP 429）、请求超时、HTTP 5xx、瞬时传输失败（DNS 解析失败、连接重置、socket 关闭、fetch 失败）上重试。
- 有 Discord `retry_after` 时用它，没有就用指数退避。

> ### Telegram

### Telegram

> * Retries on transient errors (429, timeout, connect/reset/closed, temporarily unavailable).
> * Uses `retry_after` when available, otherwise exponential backoff.
> * Markdown parse errors are not retried; they fall back to plain text.

- 在瞬时错误（429、超时、connect / reset / closed、temporarily unavailable）上重试。
- 有 `retry_after` 时用它，没有就用指数退避。
- Markdown 解析错误不重试；回退到纯文本。

---

> ## Configuration

## 配置

> Set retry policy per provider in `~/.openclaw/openclaw.json`:
>
> ```json5
> {
>   channels: {
>     telegram: {
>       retry: {
>         attempts: 3,
>         minDelayMs: 400,
>         maxDelayMs: 30000,
>         jitter: 0.1,
>       },
>     },
>     discord: {
>       retry: {
>         attempts: 3,
>         minDelayMs: 500,
>         maxDelayMs: 30000,
>         jitter: 0.1,
>       },
>     },
>   },
> }
> ```

按 provider 在 `~/.openclaw/openclaw.json` 里设重试策略：

```json5
{
  channels: {
    telegram: {
      retry: {
        attempts: 3,
        minDelayMs: 400,
        maxDelayMs: 30000,
        jitter: 0.1,
      },
    },
    discord: {
      retry: {
        attempts: 3,
        minDelayMs: 500,
        maxDelayMs: 30000,
        jitter: 0.1,
      },
    },
  },
}
```

---

> ## Notes

## 说明

> * Retries apply per request (message send, media upload, reaction, poll, sticker).
> * Composite flows do not retry completed steps.

- 重试按请求生效（消息发送、媒体上传、反应、投票、贴纸）。
- 组合流程不会重试已完成的步骤。

---

> ## Related

## 相关

> * [Model failover](/concepts/model-failover)
> * [Command queue](/concepts/queue)

- [模型 failover](/concepts/model-failover)
- [命令队列](/concepts/queue)
