# OAuth

> OpenClaw supports "subscription auth" via OAuth for providers that offer it (notably **OpenAI Codex (ChatGPT OAuth)**). For Anthropic, the practical split is now:
>
> * **Anthropic API key**: normal Anthropic API billing
> * **Anthropic Claude CLI / subscription auth inside OpenClaw**: Anthropic staff told us this usage is allowed again

OpenClaw 对支持 OAuth 的 provider 提供"订阅认证"（最显著的是 **OpenAI Codex（ChatGPT OAuth）**）。Anthropic 这边目前的实际分法是：

- **Anthropic API key**：走正常的 Anthropic API 计费
- **OpenClaw 里的 Anthropic Claude CLI / 订阅认证**：Anthropic 员工告诉我们这种用法又被允许了

> OpenAI Codex OAuth is explicitly supported for use in external tools like OpenClaw. This page explains:

OpenAI Codex OAuth 明确支持在 OpenClaw 这类外部工具里使用。本页讲：

> For Anthropic in production, API key auth is the safer recommended path.

生产环境下的 Anthropic，API key 认证是更稳妥的推荐路径。

> * how the OAuth **token exchange** works (PKCE)
> * where tokens are **stored** (and why)
> * how to handle **multiple accounts** (profiles + per-session overrides)

- OAuth **token 交换**怎么工作（PKCE）
- token **存在哪**（以及为什么）
- 怎么处理**多账号**（profile + 按会话覆盖）

> OpenClaw also supports **provider plugins** that ship their own OAuth or API-key flows. Run them via:
>
> ```bash
> openclaw models auth login --provider <id>
> ```

OpenClaw 也支持自带 OAuth 或 API key 流程的**provider 插件**。通过这条命令运行：

```bash
openclaw models auth login --provider <id>
```

---

> ## The token sink (why it exists)

## token sink（它为什么存在）

> OAuth providers commonly mint a **new refresh token** during login/refresh flows. Some providers (or OAuth clients) can invalidate older refresh tokens when a new one is issued for the same user/app.

OAuth provider 在登录 / 刷新流程里通常会铸造一个**新的 refresh token**。有些 provider（或 OAuth 客户端）会在给同一个用户 / 应用发出新 token 时让旧的 refresh token 失效。

> Practical symptom:
>
> * you log in via OpenClaw *and* via Claude Code / Codex CLI → one of them randomly gets "logged out" later

实际症状：

- 你既在 OpenClaw 登录，*又*在 Claude Code / Codex CLI 登录 → 其中一个之后会随机"被登出"。

> To reduce that, OpenClaw treats `auth-profiles.json` as a **token sink**:
>
> * the runtime reads credentials from **one place**
> * we can keep multiple profiles and route them deterministically
> * external CLI reuse is provider-specific: Codex CLI can bootstrap an empty `openai-codex:default` profile, but once OpenClaw has a local OAuth profile, the local refresh token is canonical. If that local refresh token is rejected, OpenClaw can use a usable same-account Codex CLI token as a runtime-only fallback; other integrations can remain externally managed and re-read their CLI auth store
> * status and startup paths that already know the configured provider set scope external CLI discovery to that set, so an unrelated CLI login store is not probed for a single-provider setup

为减少这种情况，OpenClaw 把 `auth-profiles.json` 当作 **token sink**：

- 运行时**只从一个地方**读凭证。
- 可以保留多个 profile 并确定性地路由它们。
- 外部 CLI 复用按 provider 区别对待：Codex CLI 可以引导出一个空的 `openai-codex:default` profile，但一旦 OpenClaw 有了本地 OAuth profile，本地的 refresh token 就是权威。本地 refresh token 被拒绝时，OpenClaw 可以拿同账号下 Codex CLI 里可用的 token 作为运行时回退；其他集成可以保持由外部管理、重新读它们的 CLI auth 存储。
- 已经知道配置好的 provider 集合的 status 和启动路径，会把外部 CLI 发现限制在这个集合内 —— 单 provider 部署里不会去探测无关 CLI 的登录存储。

---

> ## Storage (where tokens live)

## 存储（token 放在哪）

> Secrets are stored in agent auth stores:
>
> * Auth profiles (OAuth + API keys + optional value-level refs): `~/.openclaw/agents/<agentId>/agent/auth-profiles.json`
> * Legacy compatibility file: `~/.openclaw/agents/<agentId>/agent/auth.json` (static `api_key` entries are scrubbed when discovered)

密钥存放在 agent 的认证存储里：

- 认证 profile（OAuth + API key + 可选的值级 ref）：`~/.openclaw/agents/<agentId>/agent/auth-profiles.json`
- 旧版兼容文件：`~/.openclaw/agents/<agentId>/agent/auth.json`（发现里面的静态 `api_key` 条目会被清掉）

> Legacy import-only file (still supported, but not the main store):
>
> * `~/.openclaw/credentials/oauth.json` (imported into `auth-profiles.json` on first use)

旧版的、只用作导入源的文件（仍支持，但不是主存储）：

- `~/.openclaw/credentials/oauth.json`（首次使用时导入到 `auth-profiles.json`）

> All of the above also respect `$OPENCLAW_STATE_DIR` (state dir override). Full reference: [/gateway/configuration](/gateway/configuration-reference#auth-storage)

上面这些都尊重 `$OPENCLAW_STATE_DIR`（状态目录覆盖）。完整参考：[/gateway/configuration](/gateway/configuration-reference#auth-storage)。

> For static secret refs and runtime snapshot activation behavior, see [Secrets Management](/gateway/secrets).

静态密钥 ref 和运行时快照激活行为见 [密钥管理](/gateway/secrets)。

> When a secondary agent has no local auth profile, OpenClaw uses read-through inheritance from the default/main agent store. It does not clone the main agent's `auth-profiles.json` on read. OAuth refresh tokens are especially sensitive: normal copy flows skip them by default because some providers rotate or invalidate refresh tokens after use. Configure a separate OAuth login for an agent when it needs an independent account.

二级 agent 没有本地认证 profile 时，OpenClaw 从默认 / 主 agent 存储 read-through 继承。读取时不会克隆主 agent 的 `auth-profiles.json`。OAuth refresh token 特别敏感：常规复制流程默认会跳过它，因为有些 provider 在使用后会轮换或失效 refresh token。某个 agent 需要独立账号时，给它单独配 OAuth 登录。

---

> ## Anthropic legacy token compatibility

## Anthropic 旧 token 兼容

> <Warning>
>   Anthropic's public Claude Code docs say direct Claude Code use stays within Claude subscription limits, and Anthropic staff told us OpenClaw-style Claude CLI usage is allowed again. OpenClaw therefore treats Claude CLI reuse and `claude -p` usage as sanctioned for this integration unless Anthropic publishes a new policy.
>
>   For Anthropic's current direct-Claude-Code plan docs, see [Using Claude Code with your Pro or Max plan](https://support.claude.com/en/articles/11145838-using-claude-code-with-your-pro-or-max-plan) and [Using Claude Code with your Team or Enterprise plan](https://support.anthropic.com/en/articles/11845131-using-claude-code-with-your-team-or-enterprise-plan/).
>
>   If you want other subscription-style options in OpenClaw, see [OpenAI Codex](/providers/openai), [Qwen Cloud Coding Plan](/providers/qwen), [MiniMax Coding Plan](/providers/minimax), and [Z.AI / GLM Coding Plan](/providers/glm).
> </Warning>

> **警告**：Anthropic 公开的 Claude Code 文档说直接使用 Claude Code 在 Claude 订阅限制内；Anthropic 员工告诉我们 OpenClaw 风格的 Claude CLI 用法又被允许了。在 Anthropic 没出新政策之前，OpenClaw 认为 Claude CLI 复用和 `claude -p` 用法对本集成是被认可的。
>
> Anthropic 当前直接使用 Claude Code 的 plan 文档见 [Pro / Max plan 的 Claude Code 用法](https://support.claude.com/en/articles/11145838-using-claude-code-with-your-pro-or-max-plan) 和 [Team / Enterprise plan 的 Claude Code 用法](https://support.anthropic.com/en/articles/11845131-using-claude-code-with-your-team-or-enterprise-plan/)。
>
> OpenClaw 里其他订阅风格选项见 [OpenAI Codex](/providers/openai)、[Qwen Cloud Coding Plan](/providers/qwen)、[MiniMax Coding Plan](/providers/minimax) 和 [Z.AI / GLM Coding Plan](/providers/glm)。

> OpenClaw also exposes Anthropic setup-token as a supported token-auth path, but it now prefers Claude CLI reuse and `claude -p` when available.

OpenClaw 也把 Anthropic setup-token 当作受支持的 token 认证路径，但现在可用时它优先 Claude CLI 复用和 `claude -p`。

---

> ## Anthropic Claude CLI migration

## Anthropic Claude CLI 迁移

> OpenClaw supports Anthropic Claude CLI reuse again. If you already have a local Claude login on the host, onboarding/configure can reuse it directly.

OpenClaw 又支持 Anthropic Claude CLI 复用了。宿主机上已经有本地 Claude 登录时，onboarding / configure 可以直接复用它。

---

> ## OAuth exchange (how login works)

## OAuth 交换（登录怎么工作）

> OpenClaw's interactive login flows are implemented in `@earendil-works/pi-ai` and wired into the wizards/commands.

OpenClaw 的交互式登录流程实现在 `@earendil-works/pi-ai` 里，接进了向导和命令。

> ### Anthropic setup-token

### Anthropic setup-token

> Flow shape:
>
> 1. start Anthropic setup-token or paste-token from OpenClaw
> 2. OpenClaw stores the resulting Anthropic credential in an auth profile
> 3. model selection stays on `anthropic/...`
> 4. existing Anthropic auth profiles remain available for rollback/order control

流程形态：

1. 在 OpenClaw 启动 Anthropic setup-token 或粘贴 token。
2. OpenClaw 把得到的 Anthropic 凭证存到一个认证 profile 里。
3. 模型选择保持在 `anthropic/...`。
4. 已有的 Anthropic 认证 profile 仍然可用，方便回滚 / 排序控制。

> ### OpenAI Codex (ChatGPT OAuth)

### OpenAI Codex（ChatGPT OAuth）

> OpenAI Codex OAuth is explicitly supported for use outside the Codex CLI, including OpenClaw workflows.

OpenAI Codex OAuth 明确支持在 Codex CLI 外使用，包括 OpenClaw 工作流。

> Flow shape (PKCE):
>
> 1. generate PKCE verifier/challenge + random `state`
> 2. open `https://auth.openai.com/oauth/authorize?...`
> 3. try to capture callback on `http://127.0.0.1:1455/auth/callback`
> 4. if callback can't bind (or you're remote/headless), paste the redirect URL/code
> 5. exchange at `https://auth.openai.com/oauth/token`
> 6. extract `accountId` from the access token and store `{ access, refresh, expires, accountId }`

流程形态（PKCE）：

1. 生成 PKCE verifier / challenge + 随机 `state`。
2. 打开 `https://auth.openai.com/oauth/authorize?...`。
3. 尝试在 `http://127.0.0.1:1455/auth/callback` 捕获回调。
4. 回调绑不上端口（或者远程 / 无头）时，把重定向 URL / code 粘贴进去。
5. 在 `https://auth.openai.com/oauth/token` 交换。
6. 从 access token 里取出 `accountId`，存 `{ access, refresh, expires, accountId }`。

> Wizard path is `openclaw onboard` → auth choice `openai-codex`.

向导路径是 `openclaw onboard` → 认证选 `openai-codex`。

---

> ## Refresh + expiry

## 刷新 + 过期

> Profiles store an `expires` timestamp.

profile 里存了一个 `expires` 时间戳。

> At runtime:
>
> * if `expires` is in the future → use the stored access token
> * if expired → refresh (under a file lock) and overwrite the stored credentials
> * if a secondary agent reads an inherited main-agent OAuth profile, refresh writes back to the main agent store instead of copying the refresh token into the secondary agent store
> * exception: some external CLI credentials stay externally managed; OpenClaw re-reads those CLI auth stores instead of spending copied refresh tokens. Codex CLI bootstrap is intentionally narrower: it seeds an empty `openai-codex:default` profile, then OpenClaw-owned refreshes keep the local profile canonical. If the local Codex refresh fails and Codex CLI has a usable token for the same account, OpenClaw may use that token for the current runtime request without writing it back to `auth-profiles.json`.

运行时：

- `expires` 在未来 → 用已存的 access token。
- 已过期 → 在文件锁下刷新，并覆盖已存的凭证。
- 二级 agent 读到继承自主 agent 的 OAuth profile 时，刷新会写回到主 agent 存储，不会把 refresh token 复制到二级 agent 存储。
- 例外：有些外部 CLI 凭证仍由外部管理；OpenClaw 重新读那些 CLI auth 存储，而不是花掉复制来的 refresh token。Codex CLI 的引导刻意更窄：它只播一个空的 `openai-codex:default` profile，之后 OpenClaw 拥有的刷新让本地 profile 保持权威。本地 Codex 刷新失败、且 Codex CLI 同账号有可用 token 时，OpenClaw 可以把那个 token 用于当前运行时请求，但不会把它写回 `auth-profiles.json`。

> The refresh flow is automatic; you generally don't need to manage tokens manually.

刷新流程是自动的，一般不用手动管理 token。

---

> ## Multiple accounts (profiles) + routing

## 多账号（profile）+ 路由

> Two patterns:

两种模式：

> ### 1) Preferred: separate agents

### 1）推荐：用独立的 agent

> If you want "personal" and "work" to never interact, use isolated agents (separate sessions + credentials + workspace):

希望"个人"和"工作"永不交互时，用隔离的 agent（独立的会话 + 凭证 + 工作区）：

> ```bash
> openclaw agents add work
> openclaw agents add personal
> ```

```bash
openclaw agents add work
openclaw agents add personal
```

> Then configure auth per-agent (wizard) and route chats to the right agent.

然后给每个 agent 各自配认证（向导），把聊天路由到对应的 agent。

> ### 2) Advanced: multiple profiles in one agent

### 2）进阶：一个 agent 里多个 profile

> `auth-profiles.json` supports multiple profile IDs for the same provider.

`auth-profiles.json` 对同一个 provider 支持多个 profile ID。

> Pick which profile is used:
>
> * globally via config ordering (`auth.order`)
> * per-session via `/model ...@<profileId>`

选哪个 profile 用：

- 通过配置 ordering 全局选（`auth.order`）。
- 通过 `/model ...@<profileId>` 按会话选。

> Example (session override):
>
> * `/model Opus@anthropic:work`

例子（按会话覆盖）：

- `/model Opus@anthropic:work`

> How to see what profile IDs exist:
>
> * `openclaw channels list --json` (shows `auth[]`)

怎么看有哪些 profile ID：

- `openclaw channels list --json`（显示 `auth[]`）。

> Related docs:
>
> * [Model failover](/concepts/model-failover) (rotation + cooldown rules)
> * [Slash commands](/tools/slash-commands) (command surface)

相关文档：

- [模型故障转移](/concepts/model-failover)（轮换 + 冷却规则）
- [斜杠命令](/tools/slash-commands)（命令面）

---

> ## Related

## 相关

> * [Authentication](/gateway/authentication) - model provider auth overview
> * [Secrets](/gateway/secrets) - credential storage and SecretRef
> * [Configuration Reference](/gateway/configuration-reference#auth-storage) - auth config keys

- [认证](/gateway/authentication)：模型 provider 认证总览
- [密钥](/gateway/secrets)：凭证存储和 SecretRef
- [配置参考](/gateway/configuration-reference#auth-storage)：认证配置 key
