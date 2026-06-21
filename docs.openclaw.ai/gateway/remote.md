# Remote Access

系统支持远程 gateway 访问,在专用主机(桌面或服务器)上运行单个 Gateway (master),客户端连接到它。macOS 应用用户在 gateway 可达时,直连 LAN 或 Tailnet WebSocket 最简单,SSH tunneling 作为通用 fallback。iOS/Android 等节点通过 LAN、tailnet 或 SSH tunnel 连接到 Gateway WebSocket。

> **类比:Git 的 remote + local 仓库。** 本地 Git 仓库是工作副本,remote 仓库是权威来源。OpenClaw 远程访问类似: Gateway 是权威来源(拥有 sessions、auth、channels、state),laptop/desktop/nodes 都是客户端连接到它。区别: Git 是分布式的,OpenClaw Gateway 是中心化的——只有一个 Gateway per host。
>
> **架构要点:** Gateway WebSocket 默认绑定 loopback (18789);暴露方式: Tailscale Serve (推荐)、trusted LAN/tailnet bind、SSH tunnel forwarding;Gateway host 是 agent 所在,拥有 sessions、auth profiles、channels、state;nodes 不运行 gateway service,只是 peripherals;明文 `ws://` 只对 loopback、LAN、link-local、`.local`、`.ts.net`、Tailscale CGNAT 接受;public remote 必须用 `wss://`。

## 核心架构

Gateway WebSocket 通常绑定 loopback,默认端口 **18789**。远程使用时通过以下方式暴露:
- **Tailscale Serve**: 推荐,保持 Gateway loopback-only
- **Trusted LAN/Tailnet bind**: `gateway.bind: "lan"` 或 `"tailnet"`
- **SSH tunnel**: 转发 loopback 端口

Gateway host 是 agent 所在,持有 sessions、认证 profiles、channels、state。你的 laptop、desktop、nodes 都连接到该 host。

## 常见部署模式

### Always-on Gateway in tailnet

在持久主机(VPS 或 home server)上运行 Gateway,通过 Tailscale 或 SSH 访问。

- **最佳 UX**: 保持 `gateway.bind: "loopback"`,用 Tailscale Serve 暴露 Control UI
- **Trusted LAN/Tailnet**: 绑定到私有接口,`gateway.remote.transport: "direct"` 直连
- **Fallback**: 保持 loopback + 从任何需要访问的机器建立 SSH tunnel

适合 laptop 经常睡眠但希望 agent 始终可用的场景。

### Home desktop 运行 Gateway

Laptop 不运行 agent,远程连接。用 macOS app 的 remote mode (Settings → General → OpenClaw runs)。Gateway 在 LAN 或 Tailnet 可达时直连,选 SSH 时 app 打开并管理 SSH tunnel。

### Laptop 运行 Gateway

保持 Gateway 本地,通过 SSH tunnel 安全暴露给其他机器,或 Tailscale Serve Control UI 同时保持 Gateway loopback-only。

## Command flow

单个 gateway service 持有 state 和 channels,nodes 作为 peripherals。

**Telegram → node 示例**:
1. Telegram 消息到达 Gateway
2. Gateway 运行 agent,决定是否调用 node tool
3. Gateway 通过 Gateway WebSocket 用 `node.*` RPC 调用 node
4. Node 返回结果,Gateway 回复 Telegram

关键: nodes 不运行 gateway service。每台主机只应运行一个 gateway(除非故意运行隔离 profiles)。

## SSH tunnel 配置

```bash
ssh -N -L 18789:127.0.0.1:18789 user@host
```

建立后:
- `openclaw health` 和 `openclaw status --deep` 通过 `ws://127.0.0.1:18789` 到达远程 gateway
- `openclaw gateway status` 等命令可通过 `--url` 指向转发的 URL

**注意**: 用 `--url` 时,CLI 不 fallback 到 config 或环境凭证,必须显式包含 `--token` 或 `--password`。

## CLI remote defaults

持久化远程目标,CLI 命令默认使用:

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

Gateway loopback-only 时,保持 URL 为 `ws://127.0.0.1:18789`,先打开 SSH tunnel。macOS app SSH tunnel 传输中,发现的 gateway hostname 放在 `gateway.remote.sshTarget`,`gateway.remote.url` 保持本地 tunnel URL。

直连模式(LAN/Tailnet 可达时):

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

Gateway 凭证解析在 call、probe、status 路径和 Discord exec-approval 监控间共享契约。

解析规则:
- **显式凭证** (`--token`、`--password`、tool `gatewayToken`) 始终优先
- **URL 覆盖安全**: CLI `--url` 覆盖永不复用隐式 config 或环境凭证;环境 `OPENCLAW_GATEWAY_URL` 覆盖只能用环境凭证
- **Local mode**: Token: `OPENCLAW_GATEWAY_TOKEN` → `gateway.auth.token` → `gateway.remote.token`(remote fallback 仅在 local auth token 未设置时)
- **Remote mode**: Token: `gateway.remote.token` → `OPENCLAW_GATEWAY_TOKEN` → `gateway.auth.token`
- **Node-host local-mode 例外**: `gateway.remote.token` 和 `gateway.remote.password` 被忽略

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

Tunnel 在登录时自动启动,崩溃时自动重启。

## 安全规则

简版: 保持 Gateway loopback-only,除非确定需要 bind。

- **Loopback + SSH 或 Tailscale Serve** 是最安全默认值,无公开暴露
- 明文 `ws://` 只对 loopback、LAN、link-local、`.local`、`.ts.net`、Tailscale CGNAT 接受。Public remote 必须用 `wss://`
- **Non-loopback binds** (lan、tailnet、custom、auto) 必须用 gateway auth (token、password、trusted-proxy)
- `gateway.remote.token`/`.password` 是客户端凭证源,本身不配置 server auth
- `gateway.remote.tlsFingerprint` 在用 `wss://` 时 pin 远程 TLS 证书,包括 macOS 直连模式
- **Tailscale Serve** 在 `gateway.auth.allowTailscale: true` 时可通过 identity headers 认证 Control UI 和 WebSocket。HTTP API endpoints 不用 Tailscale header auth
- **Trusted-proxy** auth 默认期望 non-loopback identity-aware proxy。Same-host loopback reverse proxy 需要显式 `gateway.auth.trustedProxy.allowLoopback = true`
- 把 browser control 视为 operator access: tailnet-only + deliberate node pairing
