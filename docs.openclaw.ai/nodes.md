# Nodes

**Node** 是伴侣设备 (macOS/iOS/Android/headless),通过 `role: "node"` 连接到 Gateway **WebSocket** (与 operators 相同端口),经 `node.invoke` 暴露命令面 (如 `canvas.*`、`camera.*`、`device.*`、`notifications.*`、`system.*`)。Nodes 是 **peripherals**,不是 gateways,不运行 gateway service。Telegram/WhatsApp 等消息落在 **gateway** 上,不在 nodes 上。

> **类比:K8s 的 node + kubelet。** K8s 里 master 是控制平面,node 是工作节点,kubelet 在 node 上执行 master 的命令。OpenClaw nodes 类似: Gateway 是 master (接收消息、运行 model、路由 tool calls),node 是工作节点 (执行 `system.run`、`camera.snap` 等),node host 类似 kubelet (在 node 机器上执行命令)。区别: K8s node 运行多个 pod,OpenClaw node 暴露命令面供 Gateway 调用。
>
> **架构要点:** Node 是 peripherals,不运行 gateway;device pairing 在 WS `connect` 时发生,role 为 `node`;node host 用于跨机器执行 `system.run` (Gateway 转发 exec 调用);exec approvals **per node host** 存储在 `~/.openclaw/exec-approvals.json`;command policy 两门: node 声明 + gateway 平台策略允许;危险命令 (如 `camera.snap`、`screen.record`) 需要显式 `allowCommands` opt-in;`denyCommands` 始终胜出;canvas/camera/screen 需要 node **foreground**,后台返回 `NODE_BACKGROUND_UNAVAILABLE`;macOS 可运行在 node mode (menubar app 连接到 Gateway WS)。

## Pairing + Status

**WS nodes 使用 device pairing。** Nodes 在 `connect` 时呈现 device identity;Gateway 为 `role: node` 创建 device pairing request。通过 devices CLI (或 UI) 批准。

快速 CLI:

```bash
openclaw devices list
openclaw devices approve <requestId>
openclaw devices reject <requestId>
openclaw nodes status
openclaw nodes describe --node <idOrNameOrIp>
```

如果 node 用变更的 auth details (role/scopes/public key) 重试,之前的 pending request 被取代,创建新的 `requestId`。批准前重新运行 `openclaw devices list`。

注意:

- `nodes status` 在 device pairing role 包含 `node` 时标记 node 为 **paired**
- Device pairing record 是持久的 approved-role contract。Token rotation 保持在该 contract 内;它不能把 paired node 升级为 pairing approval 从未授予的不同 role
- `node.pair.*` (CLI: `openclaw nodes pending/approve/reject/remove/rename`) 是独立的 gateway-owned node pairing store;它**不控制** WS `connect` handshake
- `openclaw nodes remove --node <id|name|ip>` 移除 node pairing。对于 device-backed node,它**撤销设备的 `node` role** 在 `devices/paired.json` 中并断开该设备的 node-role sessions——混合 role 设备保留行只失去 `node` role,而 node-only 设备行被删除。它还清除独立的 gateway-owned node pairing store 中匹配的条目。`operator.pairing` 可移除非 operator node 行;device-token caller 在混合 role 设备上撤销自己的 node role 还需要 `operator.admin`
- Approval 作用域遵循 pending request 声明的 commands:
  - 无 commands 请求: `operator.pairing`
  - 非 exec node commands: `operator.pairing` + `operator.write`
  - `system.run` / `system.run.prepare` / `system.which`: `operator.pairing` + `operator.admin`

## Remote Node Host (system.run)

当 Gateway 运行在一台机器,你希望在另一台机器上执行命令时,使用 **node host**。Model 仍然与 **gateway** 对话;gateway 在 `host=node` 被选择时把 `exec` 调用转发给 **node host**。

### 什么运行在哪

- **Gateway host**: 接收消息,运行 model,路由 tool calls
- **Node host**: 在 node 机器上执行 `system.run`/`system.which`
- **Approvals**: 在 node host 上经 `~/.openclaw/exec-approvals.json` 强制

Approval 注意:

- Approval-backed node runs 绑定精确的请求上下文
- 对于直接 shell/runtime 文件执行,OpenClaw 还 best-effort 绑定一个具体的本地文件操作数,如果该文件在执行前变更则拒绝运行
- 如果 OpenClaw 不能为 interpreter/runtime 命令识别精确的一个具体本地文件,approval-backed 执行被拒绝,而不是假装完整的 runtime 覆盖。使用 sandboxing、独立 hosts 或显式 trusted allowlist/full workflow 用于更广的 interpreter 语义

### 启动 Node Host (前台)

在 node 机器上:

```bash
openclaw node run --host <gateway-host> --port 18789 --display-name "Build Node"
```

### Remote Gateway via SSH Tunnel (loopback bind)

如果 Gateway 绑定到 loopback (`gateway.bind=loopback`,local mode 默认),remote node hosts 不能直连。创建 SSH tunnel 并把 node host 指向 tunnel 的本地端。

示例 (node host -> gateway host):

```bash
# Terminal A (保持运行): 转发本地 18790 -> gateway 127.0.0.1:18789
ssh -N -L 18790:127.0.0.1:18789 user@gateway-host

# Terminal B: 导出 gateway token 并通过 tunnel 连接
export OPENCLAW_GATEWAY_TOKEN="<gateway-token>"
openclaw node run --host 127.0.0.1 --port 18790 --display-name "Build Node"
```

注意:

- `openclaw node run` 支持 token 或 password auth
- 优先使用 env vars: `OPENCLAW_GATEWAY_TOKEN` / `OPENCLAW_GATEWAY_PASSWORD`
- Config fallback 是 `gateway.auth.token` / `gateway.auth.password`
- Local mode 下,node host 故意忽略 `gateway.remote.token` / `gateway.remote.password`
- Remote mode 下,`gateway.remote.token` / `gateway.remote.password` 按 remote 优先级规则可用
- 如果活跃的本地 `gateway.auth.*` SecretRefs 已配置但未解析,node-host auth 失败关闭
- Node-host auth 解析只尊重 `OPENCLAW_GATEWAY_*` env vars

### 启动 Node Host (service)

```bash
openclaw node install --host <gateway-host> --port 18789 --display-name "Build Node"
openclaw node start
openclaw node restart
```

### Pair + Name

在 gateway host 上:

```bash
openclaw devices list
openclaw devices approve <requestId>
openclaw nodes status
```

如果 node 用变更的 auth details 重试,重新运行 `openclaw devices list` 并批准当前的 `requestId`。

命名选项:

- `--display-name` 在 `openclaw node run` / `openclaw node install` 上 (持久化在 node 上的 `~/.openclaw/node.json`)
- `openclaw nodes rename --node <id|name|ip> --name "Build Node"` (gateway override)

### Allowlist Commands

Exec approvals **per node host**。从 gateway 添加 allowlist 条目:

```bash
openclaw approvals allowlist add --node <id|name|ip> "/usr/bin/uname"
openclaw approvals allowlist add --node <id|name|ip> "/usr/bin/sw_vers"
```

Approvals 在 node host 上存储在 `~/.openclaw/exec-approvals.json`。

### 把 Exec 指向 Node

配置默认值 (gateway config):

```bash
openclaw config set tools.exec.host node
openclaw config set tools.exec.security allowlist
openclaw config set tools.exec.node "<id-or-name>"
```

或 per session:

```
/exec host=node security=allowlist node=<id-or-name>
```

设置后,任何 `exec` 调用 `host=node` 在 node host 上运行 (受 node allowlist/approvals 约束)。

`host=auto` 不会隐式自行选择 node,但显式的 per-call `host=node` 请求从 `auto` 允许。如果你希望 node exec 成为 session 默认,设置 `tools.exec.host=node` 或显式 `/exec host=node ...`。

相关:

- [Node host CLI](/cli/node)
- [Exec tool](/tools/exec)
- [Exec approvals](/tools/exec-approvals)

## 调用命令

底层 (raw RPC):

```bash
openclaw nodes invoke --node <idOrNameOrIp> --command canvas.eval --params '{"javaScript":"location.href"}'
```

存在更高层的 helpers 用于常见的"给 agent 一个 MEDIA 附件"工作流。

## Command Policy

Node commands 必须通过两道门才能被调用:

1. Node 必须在其 WebSocket `connect.commands` 列表中声明 command
2. Gateway 的平台策略必须允许声明的 command

Windows 和 macOS companion nodes 默认允许安全的声明 commands 如 `canvas.*`、`camera.list`、`location.get`、`screen.snapshot`。Trusted nodes 如果 advertise `talk` capability 或声明 `talk.*` commands,还默认允许声明的 push-to-talk commands (`talk.ptt.start`、`talk.ptt.stop`、`talk.ptt.cancel`、`talk.ptt.once`),独立于平台标签。危险或隐私重的 commands 如 `camera.snap`、`camera.clip`、`screen.record` 仍需要显式 opt-in 用 `gateway.nodes.allowCommands`。`gateway.nodes.denyCommands` 始终胜出默认值和额外 allowlist 条目。

Plugin-owned node commands 可添加 Gateway node-invoke policy。该 policy 在 allowlist 检查后、转发到 node 前运行,所以 raw `node.invoke`、CLI helpers 和专用 agent tools 共享同一 plugin 权限边界。危险的 plugin node commands 仍需要显式 `gateway.nodes.allowCommands` opt-in。

Node 变更声明的 command 列表后,拒绝旧的 device pairing 并批准新的 request,以便 gateway 存储更新的 command snapshot。

## Config (`openclaw.json`)

Node 相关设置位于 `gateway.nodes` 和 `tools.exec` 下:

```json5
{
  gateway: {
    nodes: {
      // Auto-approve 首次 node pairing 从 trusted networks (CIDR 列表)
      // 未设置时禁用。仅适用于首次 role:node 请求且无请求 scopes;
      // 不 auto-approve 升级
      pairing: {
        autoApproveCidrs: ["192.168.1.0/24"]
      },
      // Opt into 危险/隐私重的 node commands (camera.snap 等)
      allowCommands: ["camera.snap", "screen.record"],
      // 阻止精确的 command 名称,即使默认值或 allowCommands 包含它们
      denyCommands: ["camera.clip"]
    }
  },
  tools: {
    exec: {
      // 默认 exec host: "node" 路由所有 exec 调用到 paired node
      host: "node",
      // Node exec 的 security mode: 仅允许 approved/allowlisted commands
      security: "allowlist",
      // 把 exec 固定到特定 node (id 或 name)。省略则允许任何 node
      node: "build-node"
    }
  }
}
```

使用精确的 node command 名称。`denyCommands` 移除 command,即使平台默认值或 `allowCommands` 条目本来会允许它。详见 [Gateway configuration reference](/gateway/configuration-reference#gateway-field-details) 的 gateway node pairing 和 command-policy 字段详情。

Per-agent exec node override:

```json5
{
  agents: {
    list: [
      {
        id: "main",
        tools: { exec: { node: "build-node" } }
      }
    ]
  }
}
```

## Screenshots (Canvas Snapshots)

如果 node 正在展示 Canvas (WebView),`canvas.snapshot` 返回 `{ format, base64 }`。

CLI helper (写入临时文件并打印保存路径):

```bash
openclaw nodes canvas snapshot --node <idOrNameOrIp> --format png
openclaw nodes canvas snapshot --node <idOrNameOrIp> --format jpg --max-width 1200 --quality 0.9
```

### Canvas Controls

```bash
openclaw nodes canvas present --node <idOrNameOrIp> --target https://example.com
openclaw nodes canvas hide --node <idOrNameOrIp>
openclaw nodes canvas navigate https://example.com --node <idOrNameOrIp>
openclaw nodes canvas eval --node <idOrNameOrIp> --js "document.title"
```

注意:

- `canvas present` 接受 URLs 或本地文件路径 (`--target`),加可选的 `--x/--y/--width/--height` 用于定位
- `canvas eval` 接受 inline JS (`--js`) 或 positional arg

### A2UI (Canvas)

```bash
openclaw nodes canvas a2ui push --node <idOrNameOrIp> --text "Hello"
openclaw nodes canvas a2ui push --node <idOrNameOrIp> --jsonl ./payload.jsonl
openclaw nodes canvas a2ui reset --node <idOrNameOrIp>
```

注意:

- Mobile nodes 使用 bundled app-owned A2UI page 用于 action-capable rendering
- 仅支持 A2UI v0.8 JSONL (v0.9/createSurface 被拒绝)
- iOS 和 Android 渲染远程 Gateway Canvas pages,但 A2UI button actions 只从 bundled app-owned A2UI page dispatch。Gateway-hosted HTTP/HTTPS A2UI pages 在这些移动客户端上仅渲染

## Photos + Videos (Node Camera)

Photos (`jpg`):

```bash
openclaw nodes camera list --node <idOrNameOrIp>
openclaw nodes camera snap --node <idOrNameOrIp>            # 默认: 两个朝向 (2 MEDIA 行)
openclaw nodes camera snap --node <idOrNameOrIp> --facing front
```

Video clips (`mp4`):

```bash
openclaw nodes camera clip --node <idOrNameOrIp> --duration 10s
openclaw nodes camera clip --node <idOrNameOrIp> --duration 3000 --no-audio
```

注意:

- Node 必须**在 foreground** 才能使用 `canvas.*` 和 `camera.*` (后台调用返回 `NODE_BACKGROUND_UNAVAILABLE`)
- Clip duration 被 clamp (当前 `<= 60s`) 以避免过大的 base64 payloads
- Android 会在可能时提示 `CAMERA`/`RECORD_AUDIO` 权限;被拒绝的权限失败并返回 `*_PERMISSION_REQUIRED`

## Screen Recordings (Nodes)

支持的 nodes 暴露 `screen.record` (mp4)。示例:

```bash
openclaw nodes screen record --node <idOrNameOrIp> --duration 10s --fps 10
openclaw nodes screen record --node <idOrNameOrIp> --duration 10s --fps 10 --no-audio
```

注意:

- `screen.record` 可用性取决于 node 平台
- Screen recordings 被 clamp 到 `<= 60s`
- `--no-audio` 在支持的平台上禁用麦克风捕获
- 使用 `--screen <index>` 在多屏幕可用时选择显示器

## Location (Nodes)

Nodes 在设置中启用 Location 时暴露 `location.get`。

CLI helper:

```bash
openclaw nodes location get --node <idOrNameOrIp>
openclaw nodes location get --node <idOrNameOrIp> --accuracy precise --max-age 15000 --location-timeout 10000
```

注意:

- Location **默认关闭**
- "Always" 需要系统权限;background fetch 是 best-effort
- Response 包括 lat/lon、accuracy (米)、timestamp

## SMS (Android Nodes)

Android nodes 在用户授予 **SMS** 权限且设备支持电话功能时可暴露 `sms.send`。

底层 invoke:

```bash
openclaw nodes invoke --node <idOrNameOrIp> --command sms.send --params '{"to":"+15555550123","message":"Hello from OpenClaw"}'
```

注意:

- 权限提示必须在 Android 设备上接受后,capability 才会被 advertise
- 无电话功能的 Wi-Fi-only 设备不会 advertise `sms.send`

## Android Device + Personal Data Commands

Android nodes 在相应 capabilities 启用时可 advertise 额外 command families。

可用 families:

- `device.status`、`device.info`、`device.permissions`、`device.health`
- `device.apps` 在 Android Settings 中启用 Installed Apps sharing 时
- `notifications.list`、`notifications.actions`
- `photos.latest`
- `contacts.search`、`contacts.add`
- `calendar.events`、`calendar.add`
- `callLog.search`
- `sms.search`
- `motion.activity`、`motion.pedometer`

示例 invokes:

```bash
openclaw nodes invoke --node <idOrNameOrIp> --command device.status --params '{}'
openclaw nodes invoke --node <idOrNameOrIp> --command device.apps --params '{"limit":10}'
openclaw nodes invoke --node <idOrNameOrIp> --command notifications.list --params '{}'
openclaw nodes invoke --node <idOrNameOrIp> --command photos.latest --params '{"limit":1}'
```

注意:

- `device.apps` 是 opt-in,默认返回 launcher-visible apps
- Motion commands 由可用 sensors 进行 capability-gated

## System Commands (Node Host / Mac Node)

macOS node 暴露 `system.run`、`system.notify`、`system.execApprovals.get/set`。Headless node host 暴露 `system.run`、`system.which`、`system.execApprovals.get/set`。

示例:

```bash
openclaw nodes notify --node <idOrNameOrIp> --title "Ping" --body "Gateway ready"
openclaw nodes invoke --node <idOrNameOrIp> --command system.which --params '{"name":"git"}'
```

注意:

- `system.run` 在 payload 中返回 stdout/stderr/exit code
- Shell 执行现在经 `exec` tool `host=node` 走;`nodes` 保持显式 node commands 的 direct-RPC surface
- `nodes invoke` 不暴露 `system.run` 或 `system.run.prepare`;那些保持在 exec path 上
- Exec path 在 approval 前准备规范的 `systemRunPlan`。一旦 approval 被授予,gateway 转发存储的 plan,而不是任何后续 caller-edited command/cwd/session 字段
- `system.notify` 尊重 macOS app 上的 notification 权限状态
- 未识别的 node `platform` / `deviceFamily` 元数据使用保守的默认 allowlist,排除 `system.run` 和 `system.which`。如果你故意为未知平台需要这些 commands,经 `gateway.nodes.allowCommands` 显式添加它们
- `system.run` 支持 `--cwd`、`--env KEY=VAL`、`--command-timeout`、`--needs-screen-recording`
- 对于 shell wrappers (`bash|sh|zsh ... -c/-lc`),request-scoped `--env` 值被简化为显式 allowlist (`TERM`、`LANG`、`LC_*`、`COLORTERM`、`NO_COLOR`、`FORCE_COLOR`)
- 对于 allowlist mode 下的 allow-always 决策,已知的 dispatch wrappers (`env`、`flock`、`nice`、`nohup`、`stdbuf`、`timeout`) 持久化内部 executable paths 而不是 wrapper paths。如果 unwrapping 不安全,不自动持久化 allowlist 条目
- Windows node hosts 在 allowlist mode 下,shell-wrapper 经 `cmd.exe /c` 运行需要 approval (仅 allowlist 条目不自动允许 wrapper 形式)
- `system.notify` 支持 `--priority <passive|active|timeSensitive>` 和 `--delivery <system|overlay|auto>`
- Node hosts 忽略 `PATH` overrides 并剥离危险的启动/shell keys (`DYLD_*`、`LD_*`、`BASHOPTS`、`FPATH`、`KSH_ENV`、`NODE_OPTIONS`、`NODE_REDIRECT_WARNINGS`、`NODE_REPL_EXTERNAL_MODULE`、`NODE_REPL_HISTORY`、`NODE_V8_COVERAGE`、`PYTHON*`、`PERL*`、`RUBYOPT`、`SHELLOPTS`、`PS4`、`TCLLIBPATH`)。如果你需要额外的 PATH 条目,配置 node host service 环境 (或在标准位置安装工具),而不是经 `--env` 传递 `PATH`
- macOS node mode 下,`system.run` 在 macOS app 中受 exec approvals 约束 (Settings → Exec approvals)。Ask/allowlist/full 行为与 headless node host 相同;被拒绝的提示返回 `SYSTEM_RUN_DENIED`
- Headless node host 上,`system.run` 受 exec approvals 约束 (`~/.openclaw/exec-approvals.json`)

## Exec Node Binding

多个 nodes 可用时,你可以把 exec 绑定到特定 node。这为 `exec host=node` 设置默认 node (并可被 per-agent 覆盖)。

全局默认:

```bash
openclaw config set tools.exec.node "node-id-or-name"
```

Per-agent override:

```bash
openclaw config get agents.list
openclaw config set 'agents.list[0].tools.exec.node' "node-id-or-name"
```

取消设置以允许任何 node:

```bash
openclaw config unset tools.exec.node
openclaw config unset 'agents.list[0].tools.exec.node'
```

## Permissions Map

Nodes 可在 `node.list` / `node.describe` 中包含 `permissions` map,以 permission 名称 (如 `screenRecording`、`accessibility`) 为键,boolean 值 (`true` = granted)。

## Headless Node Host (跨平台)

OpenClaw 可运行 **headless node host** (无 UI),连接到 Gateway WebSocket 并暴露 `system.run` / `system.which`。这在 Linux/Windows 上或在服务器旁运行最小 node 时有用。

启动:

```bash
openclaw node run --host <gateway-host> --port 18789
```

注意:

- 仍需要 pairing (Gateway 会显示 device pairing 提示)
- Node host 把其 node id、token、display name、gateway 连接信息存储在 `~/.openclaw/node.json`
- Exec approvals 经 `~/.openclaw/exec-approvals.json` 在本地强制 (见 [Exec approvals](/tools/exec-approvals))
- macOS 上,headless node host 默认在本地执行 `system.run`。设置 `OPENCLAW_NODE_EXEC_HOST=app` 把 `system.run` 路由经 companion app exec host;添加 `OPENCLAW_NODE_EXEC_FALLBACK=0` 要求 app host,如果不可用则失败关闭
- Gateway WS 使用 TLS 时添加 `--tls` / `--tls-fingerprint`

## Mac Node Mode

- macOS menubar app 作为 node 连接到 Gateway WS server (所以 `openclaw nodes …` 对此 Mac 有效)
- Remote mode 下,app 为 Gateway 端口打开 SSH tunnel 并连接到 `localhost`
