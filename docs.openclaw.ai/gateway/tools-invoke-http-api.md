# Tools Invoke API

> **类比:AWS Lambda 的 InvokeFunction API。** 不是启动完整的 agent turn(类似启动整个 Lambda 函数),而是直接调用单个 tool(类似直接 invoke 一个特定函数)。适合自动化场景: 需要 tool policy enforcement,但不需要完整 agent 推理循环。
>
> **架构要点:** 始终 enabled(不需要显式启用);完整 operator-access surface;复用 Gateway 完整 policy chain;默认硬拒绝列表阻止危险 tools(exec、spawn、shell、fs_write 等);`gateway.tools.allow` 是 exposure override 而非 scope upgrade;exec approvals 是 operator guardrails 不是授权层——如果 exec 可达,它是 mutating shell surface。

## 端点

`POST /tools/invoke`,与 Gateway multiplexed port 共享,默认最大 payload 2 MB。

```bash
curl -sS http://127.0.0.1:18789/tools/invoke \
  -H 'Authorization: Bearer secret' \
  -H 'Content-Type: application/json' \
  -d '{ "tool": "sessions_list", "action": "json", "args": {} }'
```

## 安全边界

**完整 operator-access surface**。Bearer auth 不是窄的每用户作用域,有效凭证等同于 owner/operator credential。

**Shared-secret auth** (`token`/`password`):
- 证明持有 operator secret
- 忽略 `x-openclaw-scopes` header
- 恢复完整 operator scopes
- 视为 owner-sender turns

**Identity-bearing modes** (trusted-proxy/`none`):
- 认证外部可信身份
- 尊重 `x-openclaw-scopes`
- 仅在显式缩小 scopes 且省略 `operator.admin` 时失去 owner 语义

只在 loopback、tailnet、private ingress 使用。信任分离场景运行独立 Gateway。

## Request body

```json
{
  "tool": "sessions_list",
  "action": "json",
  "args": {},
  "sessionKey": "main",
  "dryRun": false
}
```

| Field | Required | Description |
|-------|----------|-------------|
| `tool` | Yes | Tool 名 |
| `action` | No | 映射到 args(如果 tool schema 支持) |
| `args` | No | Tool-specific 参数 |
| `sessionKey` | No | 目标 session key(默认 main,尊重 `session.mainKey`) |
| `dryRun` | No | 保留,当前忽略 |

可选 context headers: `x-openclaw-message-channel`(如 `slack`、`telegram`)、`x-openclaw-account-id`(多账户)。

## Policy chain

Tool 可用性通过与 Gateway agent 相同的 policy chain 过滤:

1. `tools.profile` / `tools.byProvider.profile`
2. `tools.allow` / `tools.byProvider.allow`
3. `agents.<id>.tools.allow` / `agents.<id>.tools.byProvider.allow`
4. Group policies(session key 映射到 group/channel 时)
5. Subagent policy(subagent session key 时)

Policy 不允许返回 **404**。

## 默认硬拒绝列表

即使 session policy 允许,HTTP endpoint 默认阻止:

| Tool | Reason |
|------|--------|
| `exec` | 命令执行 (RCE) |
| `spawn` | 子进程创建 (RCE) |
| `shell` | Shell 执行 (RCE) |
| `fs_write` | 文件变更 |
| `fs_delete` | 文件删除 |
| `fs_move` | 文件移动 |
| `apply_patch` | 可重写任意文件 |
| `sessions_spawn` | 远程 agent 创建 = RCE |
| `sessions_send` | 跨 session 消息注入 |
| `cron` | 持久化自动化控制平面 |
| `gateway` | 防止 HTTP 重配置 |
| `nodes` | 节点 relay 可达 system.run |
| `whatsapp_login` | 交互式 QR scan,HTTP 会挂起 |

## 自定义

```json5
{
  gateway: {
    tools: {
      deny: ["browser"],   // 额外阻止
      allow: ["gateway"]   // 从默认 deny list 移除 (owner/admin)
    }
  }
}
```

**关键**: `gateway.tools.allow` 是 **exposure override,不是作用域升级**。Identity-bearing modes 下,`cron`、`gateway`、`nodes` 对没有 `operator.admin` 的调用者仍然不可用,即使在 `allow` 中。Shared-secret bearer auth 遵循完整 trusted-operator 规则。

## 重要边界

- Exec approvals 是 operator guardrails,不是这个 endpoint 的额外授权层。可达的 tool 直接调用,不需要 per-call approval
- 如果 `exec` 可达,视为 **mutating shell surface**——阻止文件写入 tool 不会让 shell 执行变成只读
- 不要共享 Gateway bearer credentials 给不可信调用者。信任分离用独立 Gateway
