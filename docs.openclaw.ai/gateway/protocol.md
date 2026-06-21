# Gateway Protocol

## 架构精读

> 跳过不影响阅读翻译正文。

### 单一控制平面——为什么所有客户端都走一条 WebSocket？

OpenClaw 的网关承担控制平面、策略入口、事件广播三重职责。所有客户端（CLI、Web UI、macOS 应用、iOS/Android 节点、无头节点）共用一条 WebSocket 长连接接入同一个网关。

这跟 Kubernetes 的 apiserver 是一个思路——把所有状态收归单一入口，降低多服务间的一致性协商成本。也类似 MQTT 代理的做法：设备只连一个代理，由代理负责消息路由和策略执行。单一入口并不意味着单点故障：网关可以水平扩展，关键在于逻辑上的单一权威源，而非物理上的单进程。

### 能力声明——为什么让节点自报能力而非服务端配置？

节点在连接时声明自己的能力清单：高层能力类别（摄像头、屏幕、画布）、可调用命令白名单、细粒度权限开关。网关把这些当作声明而非信任凭证，在服务端用允许列表做二次校验。

这跟 IoT 协议里设备上报能力再由服务端策略裁决是一个思路——设备说"我有摄像头"，服务端决定"是否允许你用"。这种模式让异构设备（Cordova、macOS、浏览器）共用一套协议，而不需要为每种设备类型单独适配。恶意节点即使谎报能力，也无法绕过服务端的权限校验。

### 身份与权限分层——为什么要区分角色和作用域？

角色只有两种：操作员和节点，回答"你是谁"；作用域是一组细粒度权限字符串，回答"你能做什么"。两者在握手时分别协商。

这跟 Unix 的用户与权限分离是一个思路——用户身份决定你是谁，而文件读写执行权限是独立授予的。分层设计让新增权限不需要修改身份体系，提升角色也不需要重新分配所有作用域。审计时可以清晰区分"声明的身份"与"实际获得的权限"。

### 广播事件作用域隔离——为什么不能对所有连接广播所有事件？

操作员和节点共享同一个网关，但节点不应该被动接收聊天消息。网关对广播事件按作用域过滤：聊天和代理事件需要读权限，插件广播需要写或管理员权限。心跳和在线状态等传输健康事件不受限制。

这跟频道的订阅权限是一个思路——不是所有订阅者都能看到所有频道的内容，每条消息都有自己的访问控制列表。未知广播事件默认拒绝访问（失败关闭），只有注册处理程序显式声明放宽才放行，确保新增事件类型不会意外泄露敏感数据。

### 幂等键——为什么副作用操作需要防重保护？

产生副作用的方法（发送消息、创建会话、修改配置）要求携带幂等键。网关用幂等键做去重，确保同一操作即使因网络重试被多次提交也只执行一次。

这跟 HTTP 的 `Idempotency-Key` 头部是一个思路——客户端放心重试，不用担心重复扣费或消息重复投递。在网络不可靠的移动环境下，重试是常态而非异常，协议层的幂等保护让客户端逻辑大幅简化。

---

Gateway WS protocol is the **single control plane plus node transport layer** for OpenClaw. All clients (CLI, Web UI, macOS app, iOS/Android nodes, headless nodes) connect via WebSocket and declare their **role** and **scopes** during handshake.

Gateway WS 协议是 OpenClaw 的**单一控制平面加节点传输层**。所有客户端（CLI、Web UI、macOS 应用、iOS/Android 节点、无头节点）都通过 WebSocket 连接，并在握手时声明**角色**和**作用域**。

## Transport

- WebSocket, text frames carry JSON

- WebSocket，文本帧承载 JSON

- The first frame **must** be a `connect` request

- 第一帧**必须**是 `connect` 请求

- Pre-connect frame size limit is 64 KiB. After successful handshake, clients must respect `hello-ok.policy.maxPayload` and `hello-ok.policy.maxBufferedBytes` limits

- 连接前帧大小上限 64 KiB。握手成功后，客户端遵守 `hello-ok.policy.maxPayload` 和 `hello-ok.policy.maxBufferedBytes` 限制

- When diagnostics are enabled, oversized inbound frames and slow outbound buffers trigger a `payload.large` event before the gateway closes or drops the frame. These events retain size, limits, interface, and security reason codes, but never message bodies, attachment content, raw frame bodies, tokens, cookies, or secret values

- 启用诊断时，超大的入站帧和缓慢的出站缓冲区会触发 `payload.large` 事件，然后网关才关闭或丢弃该帧。这些事件保留大小、限制、接口和安全原因码，不保留消息体、附件内容、原始帧体、token、cookie 或秘密值

## Handshake (connect)

Gateway → Client (pre-connect challenge):

Gateway → 客户端（连接前挑战）：

```json
{
  "type": "event",
  "event": "connect.challenge",
  "payload": { "nonce": "…", "ts": 1737264000000 }
}
```

Client → Gateway:

客户端 → Gateway：

```json
{
  "type": "req",
  "id": "…",
  "method": "connect",
  "params": {
    "minProtocol": 3,
    "maxProtocol": 4,
    "client": {
      "id": "cli",
      "version": "1.2.3",
      "platform": "macos",
      "mode": "operator"
    },
    "role": "operator",
    "scopes": ["operator.read", "operator.write"],
    "caps": [],
    "commands": [],
    "permissions": {},
    "auth": { "token": "…" },
    "locale": "en-US",
    "userAgent": "openclaw-cli/1.2.3",
    "device": {
      "id": "device_fingerprint",
      "publicKey": "…",
      "signature": "…",
      "signedAt": 1737264000000,
      "nonce": "…"
    }
  }
}
```

Gateway → Client:

Gateway → 客户端：

```json
{
  "type": "res",
  "id": "…",
  "ok": true,
  "payload": {
    "type": "hello-ok",
    "protocol": 4,
    "server": { "version": "…", "connId": "…" },
    "features": { "methods": ["…"], "events": ["…"] },
    "snapshot": { "…": "…" },
    "auth": {
      "role": "operator",
      "scopes": ["operator.read", "operator.write"]
    },
    "policy": {
      "maxPayload": 26214400,
      "maxBufferedBytes": 52428800,
      "tickIntervalMs": 15000
    }
  }
}
```

While the Gateway is still starting up sidecars, `connect` requests may return a retryable `UNAVAILABLE` error with `details.reason` of `"startup-sidecars"` and a `retryAfterMs`. Clients should retry this response within their overall connection budget rather than throwing it as a terminal handshake failure.

Gateway 仍在完成启动 sidecar 时，`connect` 请求可能返回可重试的 `UNAVAILABLE` 错误，`details.reason` 为 `"startup-sidecars"`，并带 `retryAfterMs`。客户端应在整体连接预算内重试该响应，而不是作为终止握手失败抛出。

`server`, `features`, `snapshot`, and `policy` are all schema-required fields (`packages/gateway-protocol/src/schema/frames.ts`). `auth` is also required and returns the negotiated role/scope. `pluginSurfaceUrls` is optional and maps plugin surface names (e.g. `canvas`) to scoped hosted URLs.

`server`、`features`、`snapshot`、`policy` 都是 schema 必填字段（`packages/gateway-protocol/src/schema/frames.ts`）。`auth` 同样必填，返回协商后的角色/作用域。`pluginSurfaceUrls` 是可选的，将插件界面名（如 `canvas`）映射到带作用域的托管 URL。

Scoped plugin surface URLs may expire. Nodes can call `node.pluginSurface.refresh` with `{ "surface": "canvas" }` to obtain fresh entries in `pluginSurfaceUrls`. The experimental Canvas plugin refactor no longer supports the deprecated `canvasHostUrl`, `canvasCapability`, `node.canvas.capability.refresh` compatibility paths; current native clients and gateways must use plugin surfaces.

带作用域的插件界面 URL 可能过期。节点可调用 `node.pluginSurface.refresh` 传入 `{ "surface": "canvas" }` 获取 `pluginSurfaceUrls` 中的新条目。实验性 Canvas 插件重构不再支持已废弃的 `canvasHostUrl`、`canvasCapability`、`node.canvas.capability.refresh` 兼容路径；当前原生客户端和网关必须使用 plugin surfaces。

When no device token is issued, `hello-ok.auth` returns the negotiated permissions without a token field:

未颁发设备 token 时，`hello-ok.auth` 返回协商后的权限且不带 token 字段：

```json
{
  "auth": {
    "role": "operator",
    "scopes": ["operator.read", "operator.write"]
  }
}
```

Trusted same-process backend clients (`client.id: "gateway-client"`, `client.mode: "backend"`) connecting on local loopback with a shared gateway token or password auth may omit `device`. This path is reserved for internal control plane RPCs to prevent stale CLI or device pairing baselines from blocking local backend work like subagent session updates. Remote clients, browser-origin clients, node clients, explicit device token or device identity clients still use the normal pairing and scope upgrade checks.

受信任的同进程后端客户端（`client.id: "gateway-client"`，`client.mode: "backend"`）在本地回环直连且使用共享网关 token 或密码认证时，可省略 `device`。这条路径仅供内部控制平面 RPC，避免过期的 CLI 或设备配对基准线阻塞本地后端工作，如 subagent 会话更新。远程客户端、浏览器来源客户端、节点客户端、显式设备 token 或设备身份客户端仍使用正常的配对和作用域升级检查。

When a device token is issued, `hello-ok` also includes:

颁发设备 token 时，`hello-ok` 还包含：

```json
{
  "auth": {
    "deviceToken": "…",
    "role": "operator",
    "scopes": ["operator.read", "operator.write"]
  }
}
```

Built-in QR code or setup code bootstrap is the new mobile device handoff path. A successful baseline setup code connection returns a primary node token plus a restricted operator token:

内置 QR 码或设置码引导是新的移动设备移交路径。成功的基准线设置码连接返回一个主节点 token 加一个受限的操作员 token：

```json
{
  "auth": {
    "deviceToken": "…",
    "role": "node",
    "scopes": [],
    "deviceTokens": [
      {
        "deviceToken": "…",
        "role": "operator",
        "scopes": ["operator.approvals", "operator.read", "operator.talk.secrets", "operator.write"]
      }
    ]
  }
}
```

Operator handoff is deliberately restricted — QR bootstrap cannot grant `operator.admin` or `operator.pairing`. It includes `operator.talk.secrets` so native clients can read required Talk configuration after bootstrap. Broader admin and pairing scopes require a separate approved operator pairing or token flow. Clients only persist `hello-ok.auth.deviceTokens` when connect uses a trusted transport (e.g. `wss://` or loopback or local pairing) bootstrap auth.

操作员移交被刻意限制——QR 引导不能授予 `operator.admin` 或 `operator.pairing`。它包含 `operator.talk.secrets`，让原生客户端在引导后能读取所需的 Talk 配置。更宽泛的 admin 和 pairing 作用域需要单独的已批准操作员配对或 token 流程。客户端仅在 connect 使用受信任传输（如 `wss://` 或回环或本地配对）的引导认证时，才持久化 `hello-ok.auth.deviceTokens`。

### Node example

### 节点示例

```json
{
  "type": "req",
  "id": "…",
  "method": "connect",
  "params": {
    "minProtocol": 3,
    "maxProtocol": 4,
    "client": {
      "id": "ios-node",
      "version": "1.2.3",
      "platform": "ios",
      "mode": "node"
    },
    "role": "node",
    "scopes": [],
    "caps": ["camera", "canvas", "screen", "location", "voice"],
    "commands": ["camera.snap", "canvas.navigate", "screen.record", "location.get"],
    "permissions": { "camera.capture": true, "screen.record": false },
    "auth": { "token": "…" },
    "locale": "en-US",
    "userAgent": "openclaw-ios/1.2.3",
    "device": {
      "id": "device_fingerprint",
      "publicKey": "…",
      "signature": "…",
      "signedAt": 1737264000000,
      "nonce": "…"
    }
  }
}
```

## Framing

## 帧格式

- **Request**: `{type:"req", id, method, params}`
- **Response**: `{type:"res", id, ok, payload|error}`
- **Event**: `{type:"event", event, payload, seq?, stateVersion?}`

- **请求**：`{type:"req", id, method, params}`
- **响应**：`{type:"res", id, ok, payload|error}`
- **事件**：`{type:"event", event, payload, seq?, stateVersion?}`

Methods that produce side effects require an **idempotency key** (see schema).

产生副作用的方法需要**幂等键**（参见 schema）。

## Roles + scopes

## 角色与作用域

See [Operator scopes](/gateway/operator-scopes) for the full operator scope model, approval-time checks, and shared secret semantics.

完整的操作员作用域模型、审批时检查和共享密钥语义，参见 [Operator scopes](/gateway/operator-scopes)。

### Roles

### 角色

- `operator` = control plane client (CLI/UI/automation)
- `node` = capability host (camera/screen/canvas/system.run)

- `operator` = 控制平面客户端（CLI/UI/自动化）
- `node` = 能力宿主（摄像头/屏幕/画布/system.run）

### Scopes (operator)

### 作用域（操作员）

Common scopes:

常用作用域：

- `operator.read`
- `operator.write`
- `operator.admin`
- `operator.approvals`
- `operator.pairing`
- `operator.talk.secrets`

`talk.config` with `includeSecrets: true` requires `operator.talk.secrets` (or `operator.admin`).

`talk.config` 传 `includeSecrets: true` 需要 `operator.talk.secrets`（或 `operator.admin`）。

Plugin-registered gateway RPC methods may request their own operator scopes, but reserved core admin prefixes (`config.*`, `exec.approvals.*`, `wizard.*`, `update.*`) always resolve to `operator.admin`.

插件注册的网关 RPC 方法可请求自己的操作员作用域，但保留的核心 admin 前缀（`config.*`、`exec.approvals.*`、`wizard.*`、`update.*`）始终解析为 `operator.admin`。

Method scopes are only the first gate. Some slash commands triggered via `chat.send` layer stricter command-level checks on top of method scopes. For example, persisted `/config set` and `/config unset` writes require `operator.admin`.

方法作用域只是第一道门。通过 `chat.send` 触发的部分斜杠命令会在方法作用域之上叠加更严格的命令级检查。例如，持久化的 `/config set` 和 `/config unset` 写入需要 `operator.admin`。

`node.pair.approve` has additional approval-time scope checks on top of the base method scope:

`node.pair.approve` 在基础方法作用域之上还有额外的审批时作用域检查：

- No-command requests: `operator.pairing`
- Requests with non-exec node commands: `operator.pairing` + `operator.write`
- Requests with `system.run`, `system.run.prepare`, `system.which`: `operator.pairing` + `operator.admin`

- 无命令请求：`operator.pairing`
- 包含非 exec 节点命令的请求：`operator.pairing` 加 `operator.write`
- 包含 `system.run`、`system.run.prepare`、`system.which` 的请求：`operator.pairing` 加 `operator.admin`

### Caps/commands/permissions (node)

### 能力/命令/权限（节点）

Nodes declare capabilities at connect time:

节点在 connect 时声明能力：

- `caps`: high-level capability categories such as `camera`, `canvas`, `screen`, `location`, `voice`, `talk`
- `commands`: command whitelist for invoke
- `permissions`: fine-grained toggles (e.g. `screen.record`, `camera.capture`)

- `caps`：高层能力类别，如 `camera`、`canvas`、`screen`、`location`、`voice`、`talk`
- `commands`：invoke 的命令白名单
- `permissions`：细粒度开关（如 `screen.record`、`camera.capture`）

The Gateway treats these as **declarations** and enforces allowlist validation server-side.

Gateway 把这些当作**声明**，在服务端强制允许列表校验。

## Presence

## 在线状态

- `system-presence` returns entries keyed by device identity
- Presence entries include `deviceId`, `roles`, `scopes` — UIs can show one row per device even if it connects simultaneously as both **operator** and **node**
- `node.list` includes optional `lastSeenAtMs` and `lastSeenReason` fields. Connected nodes report the current connection time as `lastSeenAtMs` with reason `connect`; paired nodes can also report persistent background presence when trusted node events update their pairing metadata

- `system-presence` 返回按设备身份键控的条目
- 在线状态条目包含 `deviceId`、`roles`、`scopes`——UI 可以在每个设备显示一行，即使它同时以 **operator** 和 **node** 身份连接
- `node.list` 包含可选的 `lastSeenAtMs` 和 `lastSeenReason` 字段。已连接节点把当前连接时间报为 `lastSeenAtMs`，reason 为 `connect`；已配对节点也可在受信任节点事件更新其配对元数据时上报持久后台在线状态

### Node background alive event

### 节点后台存活事件

Nodes can call `node.event` with `event: "node.presence.alive"` to record that a paired node is alive during a background wake-up without marking it as connected.

节点可调用 `node.event` 传入 `event: "node.presence.alive"`，记录已配对节点在后台唤醒期间存活，而不标记为已连接。

```json
{
  "event": "node.presence.alive",
  "payloadJSON": "{\"trigger\":\"silent_push\",\"sentAtMs\":1737264000000,\"displayName\":\"Peter's iPhone\",\"version\":\"2026.4.28\",\"platform\":\"iOS 18.4.0\",\"deviceFamily\":\"iPhone\",\"modelIdentifier\":\"iPhone17,1\",\"pushTransport\":\"relay\"}"
}
```

`trigger` is a closed enum: `background`, `silent_push`, `bg_app_refresh`, `significant_location`, `manual`, `connect`. Unknown trigger strings are normalized to `background` by the gateway before persistence. This event is only persisted for authenticated node device sessions; no-device or unpaired sessions return `handled: false`.

`trigger` 是闭包枚举：`background`、`silent_push`、`bg_app_refresh`、`significant_location`、`manual`、`connect`。未知 trigger 字符串在持久化前由网关归一化为 `background`。该事件仅在已认证节点设备会话持久化；无设备或未配对会话返回 `handled: false`。

A successful gateway returns a structured result:

成功的网关返回结构化结果：

```json
{
  "ok": true,
  "event": "node.presence.alive",
  "handled": true,
  "reason": "persisted"
}
```

Legacy gateways may still return `{ "ok": true }` for `node.event`; clients should treat it as an acknowledged RPC rather than persisted presence.

旧版网关可能仍对 `node.event` 返回 `{ "ok": true }`；客户端应将其视为已确认的 RPC，而非持久化在线状态。

## Broadcast event scoping

## 广播事件作用域隔离

Server-pushed WebSocket broadcast events are scoped so that paired-scope-only or node sessions do not passively receive session content.

服务端推送的 WebSocket 广播事件按作用域过滤，仅配对作用域或节点会话不会被动收到会话内容。

- **Chat, agent, and tool result frames** (including streaming `agent` events and tool call results) require at least `operator.read`. Sessions without `operator.read` skip these frames entirely
- **Plugin-defined `plugin.*` broadcasts** are gated to `operator.write` or `operator.admin` per plugin registration
- **Status and transport events** (`heartbeat`, `presence`, `tick`, connect/disconnect lifecycle, etc.) remain unrestricted — transport health is observable by all authenticated sessions
- **Unknown broadcast event families** are scope-gated by default (fail-closed) unless a registered handler explicitly relaxes this

- **聊天、agent、工具结果帧**（包括流式 `agent` 事件和工具调用结果）需要至少 `operator.read`。没有 `operator.read` 的会话完全跳过这些帧
- **插件定义的 `plugin.*` 广播**按插件注册方式门控为 `operator.write` 或 `operator.admin`
- **状态和传输事件**（`heartbeat`、`presence`、`tick`、连接或断开生命周期等）保持不受限——传输健康对所有已认证会话可观察
- **未知广播事件族**默认按作用域门控（失败关闭），除非注册处理程序显式放宽

Each client connection maintains its own per-client sequence number, so even though different clients may see different subsets of the event stream after scope filtering, broadcasts still maintain monotonic ordering on that socket.

每个客户端连接维护自己的序列号。即使不同客户端看到作用域过滤后的不同事件子集，广播仍能在该套接字上保持单调顺序。

## Common RPC method families

## 公共 RPC 方法族

The public WS interface is broader than the handshake and auth examples above. This is not auto-generated — `hello-ok.features.methods` is a conservative discovery list built from `src/gateway/server-methods-list.ts` plus loaded plugin or channel method exports. It should be treated as feature discovery, not a complete enumeration of `src/gateway/server-methods/*.ts`.

公共 WS 接口比上述握手和认证示例更广。这不是自动生成——`hello-ok.features.methods` 是从 `src/gateway/server-methods-list.ts` 加已加载插件或通道方法导出构建的保守发现列表。应视为特性发现，而非 `src/gateway/server-methods/*.ts` 的完整枚举。

The main method families by responsibility:

按职责分类的主要方法族：

- **System & Identity**: `health`, `diagnostics.stability`, `status`, `gateway.identity.get`, `system-presence`, `system-event`, `last-heartbeat`, `set-heartbeats`
- **系统与身份**：`health`、`diagnostics.stability`、`status`、`gateway.identity.get`、`system-presence`、`system-event`、`last-heartbeat`、`set-heartbeats`

- **Models & Usage**: `models.list`, `usage.status`, `usage.cost`, `sessions.usage`, `sessions.usage.timeseries`, `sessions.usage.logs`
- **模型与用量**：`models.list`、`usage.status`、`usage.cost`、`sessions.usage`、`sessions.usage.timeseries`、`sessions.usage.logs`

- **Vector Memory & Dreaming**: `doctor.memory.status`, `doctor.memory.dreamDiary`, `doctor.memory.backfillDreamDiary`, `doctor.memory.resetDreamDiary`, `doctor.memory.resetGroundedShortTerm`, `doctor.memory.repairDreamingArtifacts`, `doctor.memory.dedupeDreamDiary`, `doctor.memory.remHarness`
- **向量记忆与 Dreaming**：`doctor.memory.status`、`doctor.memory.dreamDiary`、`doctor.memory.backfillDreamDiary`、`doctor.memory.resetDreamDiary`、`doctor.memory.resetGroundedShortTerm`、`doctor.memory.repairDreamingArtifacts`、`doctor.memory.dedupeDreamDiary`、`doctor.memory.remHarness`

- **Channels & Login Assist**: `channels.status`, `channels.logout`, `web.login.start`, `web.login.wait`, `push.test`, `voicewake.get`, `voicewake.set`
- **通道与登录辅助**：`channels.status`、`channels.logout`、`web.login.start`、`web.login.wait`、`push.test`、`voicewake.get`、`voicewake.set`

- **Messaging & Logs**: `send` (direct outbound delivery RPC), `logs.tail`
- **消息与日志**：`send`（直连出站投递 RPC）、`logs.tail`

- **Talk & TTS**: `talk.catalog`, `talk.config`, `talk.session.create`, `talk.session.join`, `talk.session.appendAudio`, `talk.session.startTurn`, `talk.session.endTurn`, `talk.session.cancelTurn`, `talk.session.cancelOutput`, `talk.session.submitToolResult`, `talk.session.steer`, `talk.session.close`, `talk.mode`, `talk.client.create`, `talk.client.toolCall`, `talk.client.steer`, `talk.event`, `talk.speak`, `tts.status`, `tts.providers`, `tts.enable`, `tts.disable`, `tts.setProvider`, `tts.convert`
- **Talk 与 TTS**：`talk.catalog`、`talk.config`、`talk.session.create`、`talk.session.join`、`talk.session.appendAudio`、`talk.session.startTurn`、`talk.session.endTurn`、`talk.session.cancelTurn`、`talk.session.cancelOutput`、`talk.session.submitToolResult`、`talk.session.steer`、`talk.session.close`、`talk.mode`、`talk.client.create`、`talk.client.toolCall`、`talk.client.steer`、`talk.event`、`talk.speak`、`tts.status`、`tts.providers`、`tts.enable`、`tts.disable`、`tts.setProvider`、`tts.convert`

- **Secrets, Config, Update & Wizard**: `secrets.reload`, `secrets.resolve`, `config.get`, `config.set`, `config.patch`, `config.apply`, `config.schema`, `config.schema.lookup`, `update.run` (with managed service handoff), `update.status`, `wizard.start`, `wizard.next`, `wizard.status`, `wizard.cancel`
- **Secrets、配置、更新、向导**：`secrets.reload`、`secrets.resolve`、`config.get`、`config.set`、`config.patch`、`config.apply`、`config.schema`、`config.schema.lookup`、`update.run`（带托管服务移交）、`update.status`、`wizard.start`、`wizard.next`、`wizard.status`、`wizard.cancel`

- **Agents & Workspaces**: `agents.list`, `agents.create`, `agents.update`, `agents.delete`, `agents.files.list`, `agents.files.get`, `agents.files.set`, `tasks.list`, `tasks.get`, `tasks.cancel`, `artifacts.list`, `artifacts.get`, `artifacts.download`, `environments.list`, `environments.status`, `agent.identity.get`, `agent.wait`
- **Agent 与工作区**：`agents.list`、`agents.create`、`agents.update`、`agents.delete`、`agents.files.list`、`agents.files.get`、`agents.files.set`、`tasks.list`、`tasks.get`、`tasks.cancel`、`artifacts.list`、`artifacts.get`、`artifacts.download`、`environments.list`、`environments.status`、`agent.identity.get`、`agent.wait`

- **Session Control**: `sessions.list`, `sessions.subscribe`, `sessions.unsubscribe`, `sessions.messages.subscribe`, `sessions.messages.unsubscribe`, `sessions.preview`, `sessions.describe`, `sessions.resolve`, `sessions.create`, `sessions.send`, `sessions.steer`, `sessions.abort`, `sessions.patch`, `sessions.reset`, `sessions.delete`, `sessions.compact`, `sessions.get`
- **会话控制**：`sessions.list`、`sessions.subscribe`、`sessions.unsubscribe`、`sessions.messages.subscribe`、`sessions.messages.unsubscribe`、`sessions.preview`、`sessions.describe`、`sessions.resolve`、`sessions.create`、`sessions.send`、`sessions.steer`、`sessions.abort`、`sessions.patch`、`sessions.reset`、`sessions.delete`、`sessions.compact`、`sessions.get`

- **Chat Execution**: `chat.history` (display normalization), `chat.send`, `chat.abort`, `chat.inject`, `chat.message.get` (full message reader)
- **聊天执行**：`chat.history`（显示归一化）、`chat.send`、`chat.abort`、`chat.inject`、`chat.message.get`（完整消息读取器）

- **Device Pairing & Device Tokens**: `device.pair.list`, `device.pair.approve`, `device.pair.reject`, `device.pair.remove`, `device.token.rotate`, `device.token.revoke`
- **设备配对与设备 token**：`device.pair.list`、`device.pair.approve`、`device.pair.reject`、`device.pair.remove`、`device.token.rotate`、`device.token.revoke`

- **Node Pairing, Invocation & Pending Work**: `node.pair.request`, `node.pair.list`, `node.pair.approve`, `node.pair.reject`, `node.pair.remove`, `node.pair.verify`, `node.list`, `node.describe`, `node.rename`, `node.invoke`, `node.invoke.result`, `node.event`, `node.pending.pull`, `node.pending.ack`, `node.pending.enqueue`, `node.pending.drain`
- **节点配对、调用与待办工作**：`node.pair.request`、`node.pair.list`、`node.pair.approve`、`node.pair.reject`、`node.pair.remove`、`node.pair.verify`、`node.list`、`node.describe`、`node.rename`、`node.invoke`、`node.invoke.result`、`node.event`、`node.pending.pull`、`node.pending.ack`、`node.pending.enqueue`、`node.pending.drain`

- **Approval Family**: `exec.approval.request`, `exec.approval.get`, `exec.approval.list`, `exec.approval.resolve`, `exec.approval.waitDecision`, `exec.approvals.get`, `exec.approvals.set`, `exec.approvals.node.get`, `exec.approvals.node.set`, `plugin.approval.request`, `plugin.approval.list`, `plugin.approval.waitDecision`, `plugin.approval.resolve`
- **审批族**：`exec.approval.request`、`exec.approval.get`、`exec.approval.list`、`exec.approval.resolve`、`exec.approval.waitDecision`、`exec.approvals.get`、`exec.approvals.set`、`exec.approvals.node.get`、`exec.approvals.node.set`、`plugin.approval.request`、`plugin.approval.list`、`plugin.approval.waitDecision`、`plugin.approval.resolve`

- **Automation, Skills & Tools**: `wake`, `cron.get`, `cron.list`, `cron.status`, `cron.add`, `cron.update`, `cron.remove`, `cron.run` (enqueue-style RPC), `cron.runs` (supports filtering by `runId`), skill and tool related methods
- **自动化、技能、工具**：`wake`、`cron.get`、`cron.list`、`cron.status`、`cron.add`、`cron.update`、`cron.remove`、`cron.run`（入队式 RPC）、`cron.runs`（支持按 `runId` 过滤）、技能与工具相关方法

## Related

## 相关

- [Operator scopes](/gateway/operator-scopes) — Full scope model and approval-time checks
- [Gateway security](/gateway/security) — Trust model and hardening baseline

- [Operator scopes](/gateway/operator-scopes) — 完整作用域模型与审批时检查
- [Gateway security](/gateway/security) — 信任模型与加固基准线
