# QA channel

> `qa-channel` is a bundled synthetic message transport for automated OpenClaw QA. It is not a production channel - it exists to exercise the same channel plugin boundary used by real transports while keeping state deterministic and fully inspectable.

`qa-channel` 是 OpenClaw 自动化 QA 用的合成消息传输通道，随产品一起发布。它不是生产用通道，作用是覆盖与真实传输通道相同的通道插件边界，同时保持状态确定、可完整审视。

---

> ## What it does

## 它做什么

> * Slack-class target grammar:
>   * `dm:<user>`
>   * `channel:<room>`
>   * `group:<room>`
>   * `thread:<room>/<thread>`
> * Shared `channel:` and `group:` conversations are surfaced to agents as group/channel room turns, so they exercise the same visible-reply and message-tool routing policy used by Discord, Slack, Telegram, and similar transports.
> * HTTP-backed synthetic bus for inbound message injection, outbound transcript capture, thread creation, reactions, edits, deletes, and search/read actions.
> * Host-side self-check runner that writes a Markdown report to `.artifacts/qa-e2e/`.

- Slack 风格的目标地址语法：
  - `dm:<user>`
  - `channel:<room>`
  - `group:<room>`
  - `thread:<room>/<thread>`
- 共享的 `channel:` 和 `group:` 对话会以群 / 频道房间轮次的形式给到 agent，触发的是和 Discord、Slack、Telegram 等真实通道一样的可见回复及消息工具路由策略。
- 基于 HTTP 的合成总线，支持注入接收消息、捕获发送记录、创建话题、表情回复、编辑、删除、搜索 / 读取动作。
- 宿主侧的自检 runner，把 Markdown 报告写到 `.artifacts/qa-e2e/`。

---

> ## Config

## 配置

> ```json
> {
>   "channels": {
>     "qa-channel": {
>       "baseUrl": "http://127.0.0.1:43123",
>       "botUserId": "openclaw",
>       "botDisplayName": "OpenClaw QA",
>       "allowFrom": ["*"],
>       "pollTimeoutMs": 1000
>     }
>   }
> }
> ```

```json
{
  "channels": {
    "qa-channel": {
      "baseUrl": "http://127.0.0.1:43123",
      "botUserId": "openclaw",
      "botDisplayName": "OpenClaw QA",
      "allowFrom": ["*"],
      "pollTimeoutMs": 1000
    }
  }
}
```

> Account keys:
>
> * `enabled` - master toggle for this account.
> * `name` - optional display label.
> * `baseUrl` - synthetic bus URL.
> * `botUserId` - Matrix-style bot user id used in target grammar.
> * `botDisplayName` - display name for outbound messages.
> * `pollTimeoutMs` - long-poll wait window. Integer between 100 and 30000.
> * `allowFrom` - sender allowlist (user ids or `"*"`). Direct messages and allowlisted group policy both use these synthetic sender ids.
> * `groupPolicy` - shared-room policy: `"open"` (default), `"allowlist"`, or `"disabled"`.
> * `groupAllowFrom` - optional shared-room sender allowlist. When omitted under `"allowlist"`, QA Channel falls back to `allowFrom`.
> * `groups.<room>.requireMention` - require a bot mention before replying in a specific group/channel room. `groups."*"` sets the default.
> * `defaultTo` - fallback target when none is supplied.
> * `actions.messages` / `actions.reactions` / `actions.search` / `actions.threads` - per-action tool gating.

账号字段：

- `enabled`：账号总开关。
- `name`：可选的显示名。
- `baseUrl`：合成总线 URL。
- `botUserId`：目标地址语法里用的 Matrix 风格机器人 user id。
- `botDisplayName`：发出消息的显示名。
- `pollTimeoutMs`：长轮询等待窗口。100 到 30000 之间的整数。
- `allowFrom`：发件人白名单（user id 列表或 `"*"`）。私聊和走白名单策略的群都使用这套合成 sender id。
- `groupPolicy`：共享房间策略：`"open"`（默认）、`"allowlist"` 或 `"disabled"`。
- `groupAllowFrom`：可选的共享房间发件人白名单。在 `"allowlist"` 下没设时，QA Channel 回退到 `allowFrom`。
- `groups.<room>.requireMention`：在某个具体群 / 频道房间里要求 @ 机器人才回。`groups."*"` 设默认值。
- `defaultTo`：没指定目标时用的回退目标。
- `actions.messages` / `actions.reactions` / `actions.search` / `actions.threads`：按动作单独控开关。

> Multi-account keys at the top level:
>
> * `accounts` - record of named per-account overrides keyed by account id.
> * `defaultAccount` - preferred account id when multiple are configured.

顶层的多账号字段：

- `accounts`：按账号 id 作 key 的命名账号覆盖记录。
- `defaultAccount`：配置了多个账号时优先使用的账号 id。

---

> ## Runners

## 运行器

> Host-side self-check (writes a Markdown report under `.artifacts/qa-e2e/`):

宿主侧自检（把 Markdown 报告写到 `.artifacts/qa-e2e/`）：

> ```bash
> pnpm qa:e2e
> ```

```bash
pnpm qa:e2e
```

> This routes through `qa-lab`, starts the in-repo QA bus, boots the bundled `qa-channel` runtime slice, and runs a deterministic self-check.

走 `qa-lab`，启动仓库内置的 QA 总线，引导起内置的 `qa-channel` 运行时切片，跑一遍确定性自检。

> Full repo-backed scenario suite:

完整的仓库级场景套件：

> ```bash
> pnpm openclaw qa suite
> ```

```bash
pnpm openclaw qa suite
```

> Runs scenarios in parallel against the QA gateway lane. See [QA overview](/concepts/qa-e2e-automation) for scenarios, profiles, and provider modes.

在 QA 网关 lane 上并行跑场景。场景、profile 和 provider 模式见 [QA 概览](/concepts/qa-e2e-automation)。

> Docker-backed QA site (gateway + QA Lab debugger UI in one stack):

基于 Docker 的 QA 站点（一套 stack 里同时跑 gateway + QA Lab 调试 UI）：

> ```bash
> pnpm qa:lab:up
> ```

```bash
pnpm qa:lab:up
```

> Builds the QA site, starts the Docker-backed gateway + QA Lab stack, and prints the QA Lab URL. From there you can pick scenarios, choose the model lane, launch individual runs, and watch results live. The QA Lab debugger is separate from the shipped Control UI bundle.

构建 QA 站点，启动 Docker 版的 gateway + QA Lab stack，并打印 QA Lab URL。从 UI 里挑场景、选模型 lane、单独发起运行、实时看结果。QA Lab 调试器跟随产品发布的 Control UI 包是分开的。

---

> ## Related

## 相关

> * [QA overview](/concepts/qa-e2e-automation) - overall stack, transport adapters, scenario authoring
> * [Matrix QA](/concepts/qa-matrix) - example live-transport runner that drives a real channel
> * [Pairing](/channels/pairing)
> * [Groups](/channels/groups)
> * [Channels overview](/channels)

- [QA 概览](/concepts/qa-e2e-automation)：整体技术栈、传输适配器、场景编写
- [Matrix QA](/concepts/qa-matrix)：驱动真实通道的实时传输 runner 示例
- [配对](/channels/pairing)
- [群组](/channels/groups)
- [通道总览](/channels)
