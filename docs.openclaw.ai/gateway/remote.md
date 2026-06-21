# Remote Access

## 架构精读

> 跳过不影响阅读翻译正文。

### 中心化 Gateway——为什么不是分布式？

Gateway 是唯一的权威节点，持有所有 sessions、认证、channels 和 state。
Node 不运行 gateway service，只作为外设连接。
这跟 Git remote 仓库类似——Gateway 是 remote（权威来源），笔记本和 node 是 local（工作副本）。
区别在于 Git 是分布式的，Gateway 是中心化的：每台主机只运行一个 gateway 实例。

### Loopback-first 安全模型——为什么默认只绑本地？

Gateway WebSocket 默认绑定 loopback（127.0.0.1:18789），不暴露到任何外部网络。
暴露方式分三种：Tailscale Serve（推荐）、LAN/Tailnet bind、SSH tunnel forwarding。
这跟最小权限原则是一个思路——先关闭一切，再按需开放。
默认绑定 loopback 保证即使忘记配置防火墙，Gateway 也不会意外暴露。

### Node 与 Gateway 的角色分离——为什么 node 不跑 gateway？

Gateway 负责 agent 逻辑、session 管理、认证和消息路由。
Node 只执行 tool 调用并返回结果。
这种分工避免了分布式状态同步的复杂性——所有 state 集中在一处管理。
每台主机只应运行一个 gateway（除非故意运行隔离配置文件）。

### 凭证安全链——为什么 URL 覆盖要隔离凭证？

凭证解析遵循严格的优先级链：显式凭证（CLI flag）始终优先。
CLI `--url` 覆盖 URL 时，强制不复用 config 或环境中的凭证，必须显式提供 `--token` 或 `--password`。
这防止了本地和远程凭证意外混用带来的安全风险。
环境变量 `OPENCLAW_GATEWAY_URL` 覆盖时，也只能配合环境凭证使用。

---

The system supports remote gateway access, running a single Gateway (master) on a dedicated host (desktop or server) with clients connecting to it. For macOS app users, direct LAN or Tailnet WebSocket is simplest when the gateway is reachable; SSH tunneling serves as a universal fallback. iOS/Android nodes connect to the Gateway WebSocket via LAN, tailnet, or SSH tunnel.

系统支持远程 gateway 访问。在专用主机（桌面或服务器）上运行单个 Gateway（master），客户端连接到它。macOS 应用用户可在 Gateway 可达时直连。LAN 或 Tailnet WebSocket 是最简单的方式，SSH tunneling 作为通用 fallback。iOS/Android 等节点可连接到 Gateway WebSocket。连接方式包括 LAN、tailnet 或 SSH tunnel。

## 核心架构

The Gateway WebSocket typically binds to loopback on port **18789**. Remote access is exposed via:

Gateway WebSocket 通常绑定 loopback，默认端口 **18789**。远程使用时通过以下方式暴露：

- **Tailscale Serve**: Recommended, keeps Gateway loopback-only
- **Tailscale Serve**：推荐，保持 Gateway loopback-only
- **Trusted LAN/Tailnet bind**: `gateway.bind: "lan"` or `"tailnet"`
- **受信任的 LAN/Tailnet 绑定**：`gateway.bind: "lan"` 或 `"tailnet"`
- **SSH tunnel**: Forward the loopback port
- **SSH tunnel**：转发 loopback 端口

The Gateway host is where the agent lives, holding sessions, auth profiles, channels, and state. Your laptop, desktop, and nodes all connect to this host.

Gateway host 是 agent 所在，持有 sessions、认证 profiles、channels 和 state。你的 laptop、desktop 和 nodes 都连接到该 host。

## 常见部署模式

### Always-on Gateway in tailnet

Run the Gateway on a persistent host (VPS or home server), accessed via Tailscale or SSH.

在长期运行的主机（VPS 或 home server）上运行 Gateway，通过 Tailscale 或 SSH 访问。

- **Best UX**: Keep `gateway.bind: "loopback"`, expose Control UI via Tailscale Serve
- **最佳 UX**：保持 `gateway.bind: "loopback"`，用 Tailscale Serve 暴露 Control UI
- **Trusted LAN/Tailnet**: Bind to private interface, `gateway.remote.transport: "direct"` for direct connection
- **受信任的 LAN/Tailnet**：绑定到私有接口，`gateway.remote.transport: "direct"` 直连
- **Fallback**: Keep loopback + SSH tunnel from any machine that needs access
- **Fallback**：保持 loopback + 从需要访问的机器建立 SSH tunnel

Best for scenarios where the laptop often sleeps but you want the agent always available.

适合 laptop 经常睡眠但希望 agent 始终可用的场景。

### Home desktop running Gateway

Laptop doesn't run the agent, connects remotely. Use the macOS app's remote mode (Settings → General → OpenClaw runs). Direct connection when Gateway is reachable on LAN or Tailnet; SSH mode where the app opens and manages the SSH tunnel.

Laptop 不运行 agent，远程连接。用 macOS app 的 remote mode（Settings → General → OpenClaw runs）。Gateway 在 LAN 或 Tailnet 可达时直连。选 SSH 时 app 打开并管理 SSH tunnel。

### Laptop running Gateway

Keep Gateway local, securely expose via SSH tunnel to other machines, or use Tailscale Serve for Control UI while keeping Gateway loopback-only.

保持 Gateway 本地，通过 SSH tunnel 安全暴露给其他机器。或用 Tailscale Serve 暴露 Control UI，同时保持 Gateway loopback-only。

## Command flow

A single gateway service holds state and channels; nodes act as peripherals.

单个 gateway service 持有 state 和 channels，nodes 作为 peripherals。

**Telegram → node example**:
**Telegram → node 示例**：
1. Telegram message arrives at Gateway
1. Telegram 消息到达 Gateway
2. Gateway runs the agent, decides whether to call a node tool
2. Gateway 运行 agent，决定是否调用 node tool
3. Gateway calls the node via `node.*` RPC over Gateway WebSocket
3. Gateway 通过 Gateway WebSocket 用 `node.*` RPC 调用 node
4. Node returns results, Gateway replies to Telegram
4. Node 返回结果，Gateway 回复 Telegram

Key: nodes don't run the gateway service. Each host should run only one gateway (unless deliberately running isolated profiles).

关键：nodes 不运行 gateway service。每台主机只应运行一个 gateway（除非故意运行隔离 profiles）。

## SSH tunnel 配置

```bash
ssh -N -L 18789:127.0.0.1:18789 user@host
```

Once established:
建立后：

- `openclaw health` and `openclaw status --deep` reach the remote gateway via `ws://127.0.0.1:18789`
- `openclaw health` 和 `openclaw status --deep` 通过 `ws://127.0.0.1:18789` 到达远程 gateway
- Commands like `openclaw gateway status` can use `--url` to point to the forwarded URL
- `openclaw gateway status` 等命令可通过 `--url` 指向转发的 URL

**Note**: With `--url`, the CLI does not fall back to config or environment credentials — you must explicitly include `--token` or `--password`.

**注意**：用 `--url` 时，CLI 不回退到 config 或环境凭证，必须显式包含 `--token` 或 `--password`。

## CLI remote defaults

To persist remote targets for CLI commands:

保存远程目标配置，让 CLI 命令默认使用：

```json5
{
  gateway: {
    mode: "remote",
    remote: {
      url: "ws://127.0.0.1:18789",
      token: "your-token"
    }
  }
}
```

When the Gateway is loopback-only, keep the URL as `ws://127.0.0.1:18789` and establish an SSH tunnel first. In the macOS app SSH tunnel mode, the discovered gateway hostname goes into `gateway.remote.sshTarget`, while `gateway.remote.url` stays as the local tunnel URL.

Gateway loopback-only 时，保持 URL 为 `ws://127.0.0.1:18789`，先打开 SSH tunnel。macOS app SSH tunnel 模式中，发现的 gateway hostname 放在 `gateway.remote.sshTarget`，`gateway.remote.url` 保持本地 tunnel URL。

For direct mode (when LAN/Tailnet is reachable):

直连模式（LAN/Tailnet 可达时）：

```json5
{
  gateway: {
    mode: "remote",
    remote: {
      transport: "direct",
      url: "ws://192.168.0.202:18789",
      token: "your-token"
    }
  }
}
```

## 凭证优先级

Gateway credential resolution shares a contract across call, probe, status paths, and Discord exec-approval monitoring.

Gateway 凭证解析在 call、probe、status 路径和 Discord exec-approval 监控间共享契约。

Resolution rules:
解析规则：

- **Explicit credentials** (`--token`, `--password`, tool `gatewayToken`) always take priority
- **显式凭证**（`--token`、`--password`、tool `gatewayToken`）始终优先
- **URL override security**: CLI `--url` override never reuses implicit config or environment credentials; environment `OPENCLAW_GATEWAY_URL` override can only use environment credentials
- **URL 覆盖安全**：CLI `--url` 覆盖不复用隐式 config 或环境凭证。环境 `OPENCLAW_GATEWAY_URL` 覆盖只能用环境凭证
- **Local mode**: Token: `OPENCLAW_GATEWAY_TOKEN` → `gateway.auth.token` → `gateway.remote.token` (remote fallback only when local auth token is unset)
- **Local mode**：Token：`OPENCLAW_GATEWAY_TOKEN` → `gateway.auth.token` → `gateway.remote.token`（remote fallback 仅在 local auth token 未设置时）
- **Remote mode**: Token: `gateway.remote.token` → `OPENCLAW_GATEWAY_TOKEN` → `gateway.auth.token`
- **Remote mode**：Token：`gateway.remote.token` → `OPENCLAW_GATEWAY_TOKEN` → `gateway.auth.token`
- **Node-host local-mode exception**: `gateway.remote.token` and `gateway.remote.password` are ignored
- **Node-host local-mode 例外**：`gateway.remote.token` 和 `gateway.remote.password` 被忽略

## macOS 持久 SSH tunnel (LaunchAgent)

```ssh
# ~/.ssh/config
Host remote-gateway
    HostName <REMOTE_IP>
    User <REMOTE_USER>
    LocalForward 18789 127.0.0.1:18789
    IdentityFile ~/.ssh/id_rsa
```

```bash
ssh-copy-id -i ~/.ssh/id_rsa <REMOTE_USER>@<REMOTE_IP>
openclaw config set gateway.remote.token "<your-token>"
```

LaunchAgent plist (`~/Library/LaunchAgents/ai.openclaw.ssh-tunnel.plist`):
```xml
<?xml version="1.0" encoding="UTF-8"?>
<plist version="1.0">
<dict>
    <key>Label</key><string>ai.openclaw.ssh-tunnel</string>
    <key>ProgramArguments</key>
    <array><string>/usr/bin/ssh</string><string>-N</string><string>remote-gateway</string></array>
    <key>KeepAlive</key><true/>
    <key>RunAtLoad</key><true/>
</dict>
</plist>
```

```bash
launchctl bootstrap gui/$UID ~/Library/LaunchAgents/ai.openclaw.ssh-tunnel.plist
```

The tunnel starts automatically at login and restarts on crash.

Tunnel 在登录时自动启动，崩溃时自动重启。

## 安全规则

Simple rule: keep Gateway loopback-only unless you're certain you need to bind.

简版：保持 Gateway loopback-only，除非确定需要 bind。

- **Loopback + SSH or Tailscale Serve** is the safest default — no public exposure
- **Loopback + SSH 或 Tailscale Serve** 是最安全默认值，无公开暴露
- Plaintext `ws://` is only accepted for loopback, LAN, link-local, `.local`, `.ts.net`, and Tailscale CGNAT. Public remote must use `wss://`
- 明文 `ws://` 只对 loopback、LAN、link-local、`.local`、`.ts.net`、Tailscale CGNAT 接受。Public remote 必须用 `wss://`
- **Non-loopback binds** (lan, tailnet, custom, auto) require gateway auth (token, password, trusted-proxy)
- **Non-loopback binds**（lan、tailnet、custom、auto）必须用 gateway auth（token、password、trusted-proxy）
- `gateway.remote.token`/`.password` are client-side credential sources; they do not configure server auth themselves
- `gateway.remote.token`/`.password` 是客户端凭证源，本身不配置 server auth
- `gateway.remote.tlsFingerprint` pins the remote TLS certificate when using `wss://`, including macOS direct mode
- `gateway.remote.tlsFingerprint` 在用 `wss://` 时 pin 远程 TLS 证书，包括 macOS 直连模式
- **Tailscale Serve** can authenticate Control UI and WebSocket via identity headers when `gateway.auth.allowTailscale: true`. HTTP API endpoints do not use Tailscale header auth
- **Tailscale Serve** 在 `gateway.auth.allowTailscale: true` 时可通过 identity headers 认证 Control UI 和 WebSocket。HTTP API endpoints 不用 Tailscale header auth
- **Trusted-proxy** auth expects a non-loopback identity-aware proxy by default. Same-host loopback reverse proxy requires explicit `gateway.auth.trustedProxy.allowLoopback = true`
- **Trusted-proxy** auth 默认期望 non-loopback identity-aware proxy。Same-host loopback reverse proxy 需要显式 `gateway.auth.trustedProxy.allowLoopback = true`
- Treat browser control as operator access: tailnet-only + deliberate node pairing
- 把 browser control 视为 operator access：tailnet-only + deliberate node pairing
