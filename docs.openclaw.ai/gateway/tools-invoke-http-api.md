# Tools Invoke API

## 架构精读

> 跳过不影响阅读翻译正文。

### 直接工具调用——为什么不用完整 agent 循环？

Tools Invoke API 允许直接调用单个工具，而不启动完整的 agent 推理循环：

```
POST /tools/invoke → 单个 tool 执行 → 返回结果
POST /v1/chat/completions → agent 推理 → 可能调用 tool → 继续推理 → 返回结果
```

这跟 AWS Lambda 的 InvokeFunction API 是一个思路——不是启动整个 Lambda 函数（完整 agent 循环），而是直接调用特定函数（单个工具）。适合自动化场景：你只需要工具执行，不需要 agent 决定"要不要调用"和"调用后做什么"。

关键设计是**最小执行单元**。完整 agent 循环包含推理、工具调用、结果整合、再推理。Tools Invoke 跳过所有推理步骤，直接执行工具并返回结果。延迟更低、令牌消耗为零、行为可预测。

### 完整操作员访问——为什么持有者就是所有者？

`POST /tools/invoke` 的持有者认证不是窄的每用户作用域模型，有效凭证等同于所有者/操作员凭证：

- 共享密钥认证（令牌/密码）：忽略 `x-openclaw-scopes`，恢复完整操作员默认值
- 可信身份模式：尊重 `x-openclaw-scopes`，仅在显式缩小且省略 `operator.admin` 时失去所有者语义

这跟 AWS IAM 的完全访问密钥（root access key）是一个思路——持有它就等于掌握账户全部权限，不是某个特定用户的受限权限。所以关键约束是**网络边界**：只在回环、tailnet、私有入口使用，绝不暴露到公网。

### 策略链 + 硬拒绝列表——为什么需要双重防线？

工具可用性经过两层过滤：

1. **策略链**（与 Gateway agent 相同）：`tools.profile` → `tools.allow` → `agents.<id>.tools.allow` → 组策略 → 子代理策略
2. **硬拒绝列表**：即使策略链允许，HTTP 端点仍然默认阻止执行、shell、fs_write 等危险工具

这跟防火墙 + WAF 是一个思路——防火墙（策略链）控制哪些端口可达，WAF（硬拒绝列表）在应用层阻止已知危险模式。两层独立执行，一层通过不代表另一层也通过。即使你在策略中显式允许 `exec`，HTTP 端点的硬拒绝列表仍然会阻止它。

### gateway.tools.allow——为什么是暴露覆盖而非作用域升级？

`gateway.tools.allow` 从默认拒绝列表中移除工具，但不改变调用者的身份作用域：

- 共享密钥模式：完全遵循可信操作员规则（允许中的工具变为可达）
- 身份模式：`cron`、`gateway`、`nodes` 对没有 `operator.admin` 的调用者仍然不可用，即使在 `允许` 中

这跟 Linux 文件权限 + ACL 是一个思路——修改权限（chmod/allow）让文件可读，但如果用户不在 ACL 的作用域内，修改权限也无法让该用户访问。允许调整的是"什么被暴露"，而非"谁能访问"。

### 执行可达 = 可变更的命令行表面——为什么阻止 fs_write 不够？

如果 `exec` 通过策略链变为可达（被加入 `gateway.tools.allow`），那么：

- `exec` 可以执行任意 shell 命令
- shell 命令可以读写任意文件
- 阻止 `fs_write` 不会让 shell 执行变成只读

这跟给一个人 sudo 权限却试图通过限制 `vi` 来防止文件修改是一个思路——绕过方式太多了。正确的做法是：如果需要信任分离，运行独立 Gateway，而不是试图在同一个 Gateway 中做精细的工具级别隔离。

---

OpenClaw's Gateway exposes a simple HTTP endpoint for invoking a single tool directly. It is always enabled and uses Gateway auth plus tool policy. Like the OpenAI-compatible `/v1/*` surface, shared-secret bearer auth is treated as trusted operator access for the whole gateway.

OpenClaw 的 Gateway 暴露了一个简单的 HTTP endpoint，用于直接调用单个 tool。它始终处于启用状态，使用 Gateway 认证加工具策略。与 OpenAI 兼容的 `/v1/*` surface 一样，共享密钥 bearer 认证被视为对整个 gateway 的可信操作员访问。

- `POST /tools/invoke`
- Same port as the Gateway (WS + HTTP multiplex): `http://<host>:<port>/tools/invoke`
- Default max payload size is 2 MB.

- `POST /tools/invoke`
- 与 Gateway 共享端口（WS + HTTP 复用）：`http://<host>:<port>/tools/invoke`
- 默认最大 payload 大小为 2 MB。

## Authentication

## 认证

Uses the Gateway auth configuration. Common HTTP auth paths:

使用 Gateway 认证配置。常见 HTTP 认证路径：

- Shared-secret auth (`gateway.auth.mode="token"` or `"password"`): `Authorization: Bearer <token>`
- Trusted identity-bearing HTTP auth (`gateway.auth.mode="trusted-proxy"`): route through the configured identity-aware proxy and let it set the required identity headers
- Private-ingress open auth (`gateway.auth.mode="none"`): no auth header required

- 共享密钥认证（`gateway.auth.mode="token"` 或 `"password"`）：`Authorization: Bearer <token>`
- 可信身份 HTTP 认证（`gateway.auth.mode="trusted-proxy"`）：通过已配置的感知身份代理路由，让它设置所需的身份头
- 私有入口开放认证（`gateway.auth.mode="none"`）：无需认证头

Notes:

说明：

- When `gateway.auth.mode="token"`, use `gateway.auth.token` (or `OPENCLAW_GATEWAY_TOKEN`).
- When `gateway.auth.mode="password"`, use `gateway.auth.password` (or `OPENCLAW_GATEWAY_PASSWORD`).
- When `gateway.auth.mode="trusted-proxy"`, the HTTP request must come from a configured trusted proxy source; same-host loopback proxies require explicit `gateway.auth.trustedProxy.allowLoopback = true`.
- Internal same-host callers that bypass the proxy can use `gateway.auth.password` / `OPENCLAW_GATEWAY_PASSWORD` as a local direct fallback.
- If `gateway.auth.rateLimit` is configured and too many auth failures occur, the endpoint returns `429` with `Retry-After`.

- 当 `gateway.auth.mode="token"` 时，使用 `gateway.auth.token`（或 `OPENCLAW_GATEWAY_TOKEN`）。
- 当 `gateway.auth.mode="password"` 时，使用 `gateway.auth.password`（或 `OPENCLAW_GATEWAY_PASSWORD`）。
- 当 `gateway.auth.mode="trusted-proxy"` 时，HTTP 请求必须来自已配置的可信代理源；同主机回环代理需要显式设置 `gateway.auth.trustedProxy.allowLoopback = true`。
- 绕过代理的内部同主机调用者可以使用 `gateway.auth.password` / `OPENCLAW_GATEWAY_PASSWORD` 作为本地直接回退。
- 如果配置了 `gateway.auth.rateLimit` 且认证失败过多，endpoint 返回带 `Retry-After` 的 `429`。

## Security boundary (important)

## 安全边界（重要）

Treat this endpoint as a **full operator-access** surface for the gateway instance.

将此 endpoint 视为 gateway 实例的**完整操作员访问** surface。

- HTTP bearer auth here is not a narrow per-user scope model.
- A valid Gateway token/password for this endpoint should be treated like an owner/operator credential.
- For shared-secret auth modes (`token` and `password`), the endpoint restores the normal full operator defaults even if the caller sends a narrower `x-openclaw-scopes` header.
- Shared-secret auth also treats direct tool invokes on this endpoint as owner-sender turns.
- Trusted identity-bearing HTTP modes (for example trusted proxy auth or `gateway.auth.mode="none"` on a private ingress) honor `x-openclaw-scopes` when present and otherwise fall back to the normal operator default scope set.
- Keep this endpoint on loopback/tailnet/private ingress only; do not expose it directly to the public internet.

- 此处的 HTTP bearer 认证不是窄的每用户作用域模型。
- 此 endpoint 的有效 Gateway token/password 应被视为 owner/operator 凭证。
- 对于共享密钥认证模式（`token` 和 `password`），即使调用者发送更窄的 `x-openclaw-scopes` 头，endpoint 也恢复正常的完整操作员默认值。
- 共享密钥认证还将此 endpoint 上的直接 tool 调用视为 owner-sender turns。
- 可信身份 HTTP 模式（例如可信代理认证或私有入口上的 `gateway.auth.mode="none"`）当 `x-openclaw-scopes` 存在时尊重它，否则回退到正常操作员默认作用域集。
- 仅在回环/tailnet/私有入口上保留此 endpoint；不要直接暴露到公网。

Auth matrix:

认证矩阵：

- `gateway.auth.mode="token"` or `"password"` + `Authorization: Bearer ...`
  - Proves possession of the shared gateway operator secret
  - Ignores narrower `x-openclaw-scopes`
  - Restores the full default operator scope set: `operator.admin`, `operator.approvals`, `operator.pairing`, `operator.read`, `operator.talk.secrets`, `operator.write`
  - Treats direct tool invokes on this endpoint as owner-sender turns

- Trusted identity-bearing HTTP modes (for example trusted proxy auth, or `gateway.auth.mode="none"` on private ingress)
  - Authenticate some outer trusted identity or deployment boundary
  - Honor `x-openclaw-scopes` when the header is present
  - Fall back to the normal operator default scope set when the header is absent
  - Only lose owner semantics when the caller explicitly narrows scopes and omits `operator.admin`

- `gateway.auth.mode="token"` 或 `"password"` + `Authorization: Bearer ...`
  - 证明持有共享 gateway 操作员密钥
  - 忽略更窄的 `x-openclaw-scopes`
  - 恢复完整默认操作员作用域集：`operator.admin`、`operator.approvals`、`operator.pairing`、`operator.read`、`operator.talk.secrets`、`operator.write`
  - 将此 endpoint 上的直接 tool 调用视为 owner-sender turns

- 可信身份 HTTP 模式（例如可信代理认证，或私有入口上的 `gateway.auth.mode="none"`）
  - 认证外部可信身份或部署边界
  - 当 `x-openclaw-scopes` 头存在时尊重它
  - 当头不存在时回退到正常操作员默认作用域集
  - 仅在调用者显式缩小作用域且省略 `operator.admin` 时失去 owner 语义

## Request body

## 请求体

```json
{
  "tool": "sessions_list",
  "action": "json",
  "args": {},
  "sessionKey": "main",
  "dryRun": false
}
```

Fields:

字段：

| Field | Required | Description |
|-------|----------|-------------|
| `tool` | Yes | Tool name to invoke |
| `action` | No | Mapped into args if the tool schema supports it and the args payload omitted it |
| `args` | No | Tool-specific arguments |
| `sessionKey` | No | Target session key (defaults to main, honors `session.mainKey`) |
| `dryRun` | No | Reserved for future use; currently ignored |

| 字段 | 必填 | 说明 |
|-------|----------|-------------|
| `tool` | 是 | 要调用的 tool 名称 |
| `action` | 否 | 如果 tool schema 支持且 args 中省略了它，则映射到 args |
| `args` | 否 | tool 特定参数 |
| `sessionKey` | 否 | 目标 session key（默认 main，遵循 `session.mainKey`） |
| `dryRun` | 否 | 保留供未来使用；当前忽略 |

To help group policies resolve context, you can optionally set:

为帮助 group policies 解析上下文，你可以可选地设置：

- `x-openclaw-message-channel: <channel>` (example: `slack`, `telegram`)
- `x-openclaw-account-id: <id>` (when multiple accounts exist)

- `x-openclaw-message-channel: <channel>`（例如：`slack`、`telegram`）
- `x-openclaw-account-id: <id>`（当存在多个账户时）

## Policy + routing behavior

## 策略 + 路由行为

Tool availability is filtered through the same policy chain used by Gateway agents:

tool 可用性通过与 Gateway agent 相同的策略链过滤：

1. `tools.profile` / `tools.byProvider.profile`
2. `tools.allow` / `tools.byProvider.allow`
3. `agents.<id>.tools.allow` / `agents.<id>.tools.byProvider.allow`
4. Group policies (if the session key maps to a group or channel)
5. Subagent policy (when invoking with a subagent session key)

If a tool is not allowed by policy, the endpoint returns **404**.

如果 tool 不被策略允许，endpoint 返回 **404**。

Important boundary notes:

重要边界说明：

- Exec approvals are operator guardrails, not a separate authorization boundary for this HTTP endpoint. If a tool is reachable here via Gateway auth + tool policy, `/tools/invoke` does not add an extra per-call approval prompt.
- If `exec` is reachable here, treat it as a mutating shell surface. Denying `write`, `edit`, `apply_patch`, or HTTP filesystem-write tools does not make shell execution read-only.
- Do not share Gateway bearer credentials with untrusted callers. If you need separation across trust boundaries, run separate gateways (and ideally separate OS users/hosts).

- exec approvals 是操作员防护栏，不是此 HTTP endpoint 的独立授权边界。如果 tool 通过 Gateway 认证 + 工具策略在此可达，`/tools/invoke` 不会添加额外的逐次调用审批提示。
- 如果 `exec` 在此可达，将其视为**可变更的 shell surface**。阻止 `write`、`edit`、`apply_patch` 或 HTTP 文件系统写入工具不会让 shell 执行变成只读。
- 不要与不可信调用者共享 Gateway bearer 凭证。如果需要跨信任边界分离，运行独立 Gateway（理想情况下使用独立操作系统用户/主机）。

## Default hard deny list

## 默认硬拒绝列表

Gateway HTTP also applies a hard deny list by default (even if session policy allows the tool):

Gateway HTTP 还默认应用硬拒绝列表（即使 session 策略允许该 tool）：

| Tool | Reason |
|------|--------|
| `exec` | Direct command execution (RCE surface) |
| `spawn` | Arbitrary child process creation (RCE surface) |
| `shell` | Shell command execution (RCE surface) |
| `fs_write` | Arbitrary file mutation on the host |
| `fs_delete` | Arbitrary file deletion on the host |
| `fs_move` | Arbitrary file move/rename on the host |
| `apply_patch` | Patch application can rewrite arbitrary files |
| `sessions_spawn` | Session orchestration; creating agents remotely is RCE |
| `sessions_send` | Cross-session message delivery |
| `cron` | Persistent automation control plane |
| `gateway` | Gateway control plane; prevents reconfiguration via HTTP |
| `nodes` | Node command relay can reach system.run on paired hosts |
| `whatsapp_login` | Interactive setup requiring terminal QR scan; hangs on HTTP |

| Tool | 原因 |
|------|--------|
| `exec` | 直接命令执行（RCE surface） |
| `spawn` | 任意子进程创建（RCE surface） |
| `shell` | Shell 命令执行（RCE surface） |
| `fs_write` | 主机上任意文件变更 |
| `fs_delete` | 主机上任意文件删除 |
| `fs_move` | 主机上任意文件移动/重命名 |
| `apply_patch` | 补丁应用可重写任意文件 |
| `sessions_spawn` | session 编排；远程创建 agent 等同于 RCE |
| `sessions_send` | 跨 session 消息投递 |
| `cron` | 持久化自动化控制平面 |
| `gateway` | gateway 控制平面；防止通过 HTTP 重配置 |
| `nodes` | 节点命令中继可到达已配对主机上的 system.run |
| `whatsapp_login` | 需要终端 QR 扫描的交互式设置；在 HTTP 上会挂起 |

## Customization

## 自定义

You can customize this deny list via `gateway.tools`:

你可以通过 `gateway.tools` 自定义此拒绝列表：

```json5
{
  gateway: {
    tools: {
      // Additional tools to block over HTTP /tools/invoke
      deny: ["browser"],
      // Remove tools from the default deny list for owner/admin callers
      allow: ["gateway"]
    }
  }
}
```

`gateway.tools.allow` is an **exposure override, not a scope upgrade**. In identity-bearing HTTP modes, `cron`, `gateway`, and `nodes` remain unavailable to callers that do not have owner/admin identity (`operator.admin`) even when they are listed in `gateway.tools.allow`. Shared-secret bearer auth still follows the full trusted-operator rule above.

`gateway.tools.allow` 是**暴露覆盖，不是作用域升级**。在身份 HTTP 模式下，`cron`、`gateway`、`nodes` 对没有 owner/admin 身份（`operator.admin`）的调用者仍然不可用，即使它们列在 `gateway.tools.allow` 中。共享密钥 bearer 认证仍然遵循上述完整的可信操作员规则。

## Responses

## 响应

- `200` → `{ ok: true, result }`
- `400` → `{ ok: false, error: { type, message } }` (invalid request or tool input error)
- `401` → unauthorized
- `429` → auth rate-limited (`Retry-After` set)
- `404` → tool not available (not found or not allowlisted)
- `405` → method not allowed
- `500` → `{ ok: false, error: { type, message } }` (unexpected tool execution error; sanitized message)

## Example

## 示例

```bash
curl -sS http://127.0.0.1:18789/tools/invoke \
  -H 'Authorization: Bearer secret' \
  -H 'Content-Type: application/json' \
  -d '{
    "tool": "sessions_list",
    "action": "json",
    "args": {}
  }'
```

## Related

## 相关

- Gateway protocol — `/gateway/protocol`
- Tools and plugins — `/tools`

- Gateway 协议 — `/gateway/protocol`
- 工具与插件 — `/tools`
