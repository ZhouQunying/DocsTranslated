# Control UI

Browser-based Control UI 用于 Gateway (chat、activity、nodes、config)。

> **类比:K8s Dashboard + Grafana。** K8s Dashboard 让你从浏览器管理集群 (pods、deployments、logs),Grafana 可视化 metrics。Control UI 类似: 浏览器管理 Gateway (chat、sessions、config、exec approvals),可视化 activity (tool calls、logs)。区别: K8s Dashboard 是只读为主,Control UI 是读写兼备 (config.patch、exec approvals)。
>
> **架构要点:** Vite + Lit SPA,Gateway 同端口 (18789) 提供;直接连接 Gateway WebSocket (`chat.history`、`chat.send`、`chat.abort`、`chat.inject`);首次连接需 device pairing (一次性批准),`127.0.0.1`/`localhost` 自动批准,Tailscale Serve 可跳过;个人 identity (display name/avatar) 在 browser-local,不同步;runtime config 从 `/control-ui-config.json` 获取,受 gateway auth 保护;支持 19 种 locales,非英语 lazy-loaded;themes: 内置 Claw/Knot/Dash + tweakcn import slot (browser-local);capabilities: Chat/Talk、Channels/Instances/Sessions/Dreams、Cron/Skills/Nodes/Exec approvals、Config (Form + Raw JSON editor)、Debug/Logs/Update;MCP 专页用于 managed MCP servers 配置;Activity tab 是 ephemeral browser-local observer,从 `session.tool` events 派生;chat.history 有 size bounds,oversized 条目被 truncate 或占位符替换,`chat.message.get` 可按需获取完整条目。

## Quick Open (Local)

```bash
http://127.0.0.1:18789/
```

Auth 在 WebSocket handshake 时提供:
- `connect.params.auth.token`
- `connect.params.auth.password`
- Tailscale Serve identity headers (`gateway.auth.allowTailscale: true`)
- Trusted-proxy identity headers (`gateway.auth.mode: "trusted-proxy"`)

## Device Pairing (首次连接)

新 browser/device 连接时,Gateway 通常需要**一次性 pairing approval**。

```bash
openclaw devices list
openclaw devices approve <requestId>
```

**注意**:
- 直接本地 loopback (`127.0.0.1`/`localhost`) 自动批准
- Tailscale Serve 可跳过 (`gateway.auth.allowTailscale: true` + identity 验证 + device identity)
- 直接 Tailnet 绑定、LAN、无 device identity 的 browser profiles 仍需显式批准
- 每个 browser profile 生成唯一 device ID,切换 browser 或清理数据需重新 pairing

## 能力概览

### Chat 和 Talk
- Chat 经 Gateway WS (`chat.history`、`chat.send`、`chat.abort`、`chat.inject`)
- Talk 经 browser realtime sessions (OpenAI 直 WebRTC,Google 实时 API 受限 token,backend-only 用 Gateway relay)

### Channels, Instances, Sessions, Dreams
- Channels: 内置 + plugin channels 状态、QR login、per-channel config
- Instances: presence list + refresh
- Sessions: 列 agents sessions,per-session overrides (model/thinking/fast/verbose/trace/reasoning)
- Dreams: 状态、toggle、Dream Diary reader

### Cron, Skills, Nodes, Exec Approvals
- Cron: list/add/edit/run/enable/disable + history
- Skills: status、enable/disable、install、API key updates
- Nodes: list + caps
- Exec approvals: 编辑 gateway/node allowlists + ask policy

### Config
- 查看/编辑 `~/.openclaw/openclaw.json`
- MCP 专页用于 configured servers
- Apply + restart with validation
- Form + Raw JSON editor (snapshot 安全 round-trip 时)

### Debug, Logs, Update
- Debug: status/health/models snapshots + event log + manual RPC
- Logs: live tail with filter/export
- Update: package/git update + restart
