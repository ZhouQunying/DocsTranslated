# Gateway Protocol

Gateway WS 协议是 OpenClaw 的**单一控制平面加节点传输层**。所有客户端(CLI、Web UI、macOS 应用、iOS/Android 节点、无头节点)都通过 WebSocket 连接,并在握手时声明**角色**和**作用域**。

> **类比:K8s 控制平面 + kubelet 上报通道。** Gateway 相当于 apiserver(单一控制平面、策略入口、事件广播),节点相当于 kubelet(执行面、能力上报、设备动作)。所有客户端共用一条 WS 长连接,而不是 REST 加轮询。
>
> **类比:MQTT 加能力协商。** 客户端通过 connect 声明 caps(摄像头、屏幕、画布)、commands(可调用命令白名单)、permissions(细粒度开关)。Gateway 把这些当作**声明**而非信任凭证,在服务端用 allowlist 二次校验,这与 IoT 协议里设备上报能力再加服务端策略的模式一致。
>
> **架构要点:** 单一控制平面降低状态同步成本;role/scope 分层把身份与权限解耦;节点能力声明让异构设备(cordova、macOS、浏览器)共用一套协议;广播事件按作用域过滤避免节点会话被动收到敏感聊天内容。

## Transport

- WebSocket,文本帧承载 JSON
- 第一帧**必须**是 `connect` 请求
- 连接前帧大小上限 64 KiB。握手成功后,客户端遵守 `hello-ok.policy.maxPayload` 和 `hello-ok.policy.maxBufferedBytes` 限制
- 启用诊断时,超大的入站帧和缓慢的出站缓冲区会触发 `payload.large` 事件,然后网关才关闭或丢弃该帧。这些事件保留大小、限制、接口和安全原因码,不保留消息体、附件内容、原始帧体、token、cookie 或秘密值

## Handshake(connect)

Gateway → Client(连接前挑战):

```json
{
  "type": "event",
  "event": "connect.challenge",
  "payload": { "nonce": "…", "ts": 1737264000000 }
}
```

Client → Gateway:

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

Gateway 仍在完成启动 sidecar 时,`connect` 请求可能返回可重试的 `UNAVAILABLE` 错误,`details.reason` 为 `"startup-sidecars"`,并带 `retryAfterMs`。客户端应在整体连接预算内重试该响应,而不是作为终止握手失败抛出。

`server`、`features`、`snapshot`、`policy` 都是 schema 必填字段(`packages/gateway-protocol/src/schema/frames.ts`)。`auth` 同样必填,返回协商后的 role/scope。`pluginSurfaceUrls` 是可选的,将插件界面名(如 `canvas`)映射到带作用域的托管 URL。

带作用域的插件界面 URL 可能过期。节点可调用 `node.pluginSurface.refresh` 传入 `{ "surface": "canvas" }` 获取 `pluginSurfaceUrls` 中的新条目。实验性 Canvas 插件重构不再支持已废弃的 `canvasHostUrl`、`canvasCapability`、`node.canvas.capability.refresh` 兼容路径;当前原生客户端和网关必须使用 plugin surfaces。

未颁发设备 token 时,`hello-ok.auth` 返回协商后的权限且不带 token 字段:

```json
{
  "auth": {
    "role": "operator",
    "scopes": ["operator.read", "operator.write"]
  }
}
```

受信任的同进程后端客户端(`client.id: "gateway-client"`,`client.mode: "backend"`)在本地回环直连且使用共享网关 token 或密码认证时,可省略 `device`。这条路径仅供内部控制平面 RPC,避免过期的 CLI 或设备配对基线阻塞本地后端工作,如 subagent 会话更新。远程客户端、浏览器来源客户端、节点客户端、显式设备 token 或设备身份客户端仍使用正常的配对和作用域升级检查。

颁发设备 token 时,`hello-ok` 还包含:

```json
{
  "auth": {
    "deviceToken": "…",
    "role": "operator",
    "scopes": ["operator.read", "operator.write"]
  }
}
```

内置 QR 码或设置码引导是新的移动设备 handoff 路径。成功的基线设置码连接返回一个主节点 token 加一个受限的操作员 token:

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

操作员 handoff 被刻意限制,QR 引导不能授予 `operator.admin` 或 `operator.pairing`。它包含 `operator.talk.secrets`,让原生客户端在引导后能读取所需的 Talk 配置。更宽泛的 admin 和 pairing 作用域需要单独的已批准操作员配对或 token 流程。客户端仅在 connect 使用受信任传输(如 `wss://` 或回环或本地配对)的引导认证时,才持久化 `hello-ok.auth.deviceTokens`。

### Node example

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

- **Request**:`{type:"req", id, method, params}`
- **Response**:`{type:"res", id, ok, payload|error}`
- **Event**:`{type:"event", event, payload, seq?, stateVersion?}`

产生副作用的方法需要**幂等键**(参见 schema)。

## Roles + scopes

完整的操作员作用域模型、审批时检查和共享密钥语义,参见 [Operator scopes](/gateway/operator-scopes)。

### Roles

- `operator` = 控制平面客户端(CLI/UI/自动化)
- `node` = 能力宿主(摄像头/屏幕/画布/system.run)

### Scopes(operator)

常用作用域:

- `operator.read`
- `operator.write`
- `operator.admin`
- `operator.approvals`
- `operator.pairing`
- `operator.talk.secrets`

`talk.config` 传 `includeSecrets: true` 需要 `operator.talk.secrets`(或 `operator.admin`)。

插件注册的网关 RPC 方法可请求自己的操作员作用域,但保留的核心 admin 前缀(`config.*`、`exec.approvals.*`、`wizard.*`、`update.*`)始终解析为 `operator.admin`。

方法作用域只是第一道门。通过 `chat.send` 触发的部分斜杠命令会在方法作用域之上叠加更严格的命令级检查。例如,持久化的 `/config set` 和 `/config unset` 写入需要 `operator.admin`。

`node.pair.approve` 在基础方法作用域之上还有额外的审批时作用域检查:

- 无命令请求:`operator.pairing`
- 包含非 exec 节点命令的请求:`operator.pairing` 加 `operator.write`
- 包含 `system.run`、`system.run.prepare`、`system.which` 的请求:`operator.pairing` 加 `operator.admin`

### Caps/commands/permissions(node)

节点在 connect 时声明能力声明:

- `caps`:高层能力类别,如 `camera`、`canvas`、`screen`、`location`、`voice`、`talk`
- `commands`:invoke 的命令白名单
- `permissions`:细粒度开关(如 `screen.record`、`camera.capture`)

Gateway 把这些当作**声明**,在服务端强制 allowlist 校验。

## Presence

- `system-presence` 返回按设备身份键控的条目
- Presence 条目包含 `deviceId`、`roles`、`scopes`,UI 可以在每个设备显示一行,即使它同时以 **operator** 和 **node** 身份连接
- `node.list` 包含可选的 `lastSeenAtMs` 和 `lastSeenReason` 字段。已连接节点把当前连接时间报为 `lastSeenAtMs`,reason 为 `connect`;已配对节点也可在受信任节点事件更新其配对元数据时上报持久后台 presence

### Node background alive event

节点可调用 `node.event` 传入 `event: "node.presence.alive"`,记录已配对节点在后台唤醒期间存活,而不标记为已连接。

```json
{
  "event": "node.presence.alive",
  "payloadJSON": "{\"trigger\":\"silent_push\",\"sentAtMs\":1737264000000,\"displayName\":\"Peter's iPhone\",\"version\":\"2026.4.28\",\"platform\":\"iOS 18.4.0\",\"deviceFamily\":\"iPhone\",\"modelIdentifier\":\"iPhone17,1\",\"pushTransport\":\"relay\"}"
}
```

`trigger` 是闭包枚举:`background`、`silent_push`、`bg_app_refresh`、`significant_location`、`manual`、`connect`。未知 trigger 字符串在持久化前由网关归一化为 `background`。该事件仅在已认证节点设备会话持久化;无设备或未配对会话返回 `handled: false`。

成功的网关返回结构化结果:

```json
{
  "ok": true,
  "event": "node.presence.alive",
  "handled": true,
  "reason": "persisted"
}
```

旧版网关可能仍对 `node.event` 返回 `{ "ok": true }`;客户端应将其视为已确认的 RPC,而非持久化 presence。

## Broadcast event scoping

服务端推送的 WebSocket 广播事件按作用域过滤,仅配对作用域或节点会话不会被动收到会话内容。

- **聊天、agent、工具结果帧**(包括流式 `agent` 事件和工具调用结果)需要至少 `operator.read`。没有 `operator.read` 的会话完全跳过这些帧
- **插件定义的 `plugin.*` 广播**按插件注册方式门控为 `operator.write` 或 `operator.admin`
- **状态和传输事件**(`heartbeat`、`presence`、`tick`、连接或断开生命周期等)保持不受限,传输健康对所有已认证会话可观察
- **未知广播事件族**默认按作用域门控(失败关闭),除非注册处理程序显式放宽

每个客户端连接维护自己的每客户端序列号,即使不同客户端看到作用域过滤后的不同事件流子集,广播仍能在该套接字上保持单调顺序。

## Common RPC method families

公共 WS 接口比上述握手和认证示例更广。这不是自动生成——`hello-ok.features.methods` 是从 `src/gateway/server-methods-list.ts` 加已加载插件或通道方法导出构建的保守发现列表。应视为特性发现,而非 `src/gateway/server-methods/*.ts` 的完整枚举。

按职责分类的主要方法族:

- **系统与身份**:`health`、`diagnostics.stability`、`status`、`gateway.identity.get`、`system-presence`、`system-event`、`last-heartbeat`、`set-heartbeats`
- **模型与用量**:`models.list`、`usage.status`、`usage.cost`、`sessions.usage`、`sessions.usage.timeseries`、`sessions.usage.logs`
- **向量记忆与 Dreaming**:`doctor.memory.status`、`doctor.memory.dreamDiary`、`doctor.memory.backfillDreamDiary`、`doctor.memory.resetDreamDiary`、`doctor.memory.resetGroundedShortTerm`、`doctor.memory.repairDreamingArtifacts`、`doctor.memory.dedupeDreamDiary`、`doctor.memory.remHarness`
- **通道与登录辅助**:`channels.status`、`channels.logout`、`web.login.start`、`web.login.wait`、`push.test`、`voicewake.get`、`voicewake.set`
- **消息与日志**:`send`(直连出站投递 RPC)、`logs.tail`
- **Talk 与 TTS**:`talk.catalog`、`talk.config`、`talk.session.create`、`talk.session.join`、`talk.session.appendAudio`、`talk.session.startTurn`、`talk.session.endTurn`、`talk.session.cancelTurn`、`talk.session.cancelOutput`、`talk.session.submitToolResult`、`talk.session.steer`、`talk.session.close`、`talk.mode`、`talk.client.create`、`talk.client.toolCall`、`talk.client.steer`、`talk.event`、`talk.speak`、`tts.status`、`tts.providers`、`tts.enable`、`tts.disable`、`tts.setProvider`、`tts.convert`
- **Secrets、配置、更新、向导**:`secrets.reload`、`secrets.resolve`、`config.get`、`config.set`、`config.patch`、`config.apply`、`config.schema`、`config.schema.lookup`、`update.run`(带托管服务 handoff)、`update.status`、`wizard.start`、`wizard.next`、`wizard.status`、`wizard.cancel`
- **Agent 与工作区**:`agents.list`、`agents.create`、`agents.update`、`agents.delete`、`agents.files.list`、`agents.files.get`、`agents.files.set`、`tasks.list`、`tasks.get`、`tasks.cancel`、`artifacts.list`、`artifacts.get`、`artifacts.download`、`environments.list`、`environments.status`、`agent.identity.get`、`agent.wait`
- **会话控制**:`sessions.list`、`sessions.subscribe`、`sessions.unsubscribe`、`sessions.messages.subscribe`、`sessions.messages.unsubscribe`、`sessions.preview`、`sessions.describe`、`sessions.resolve`、`sessions.create`、`sessions.send`、`sessions.steer`、`sessions.abort`、`sessions.patch`、`sessions.reset`、`sessions.delete`、`sessions.compact`、`sessions.get`
- **聊天执行**:`chat.history`(显示归一化)、`chat.send`、`chat.abort`、`chat.inject`、`chat.message.get`(完整消息读取器)
- **设备配对与设备 token**:`device.pair.list`、`device.pair.approve`、`device.pair.reject`、`device.pair.remove`、`device.token.rotate`、`device.token.revoke`
- **节点配对、调用与待办工作**:`node.pair.request`、`node.pair.list`、`node.pair.approve`、`node.pair.reject`、`node.pair.remove`、`node.pair.verify`、`node.list`、`node.describe`、`node.rename`、`node.invoke`、`node.invoke.result`、`node.event`、`node.pending.pull`、`node.pending.ack`、`node.pending.enqueue`、`node.pending.drain`
- **审批族**:`exec.approval.request`、`exec.approval.get`、`exec.approval.list`、`exec.approval.resolve`、`exec.approval.waitDecision`、`exec.approvals.get`、`exec.approvals.set`、`exec.approvals.node.get`、`exec.approvals.node.set`、`plugin.approval.request`、`plugin.approval.list`、`plugin.approval.waitDecision`、`plugin.approval.resolve`
- **自动化、技能、工具**:`wake`、`cron.get`、`cron.list`、`cron.status`、`cron.add`、`cron.update`、`cron.remove`、`cron.run`(入队式 RPC)、`cron.runs`(支持按 `runId` 过滤)、技能与工具相关方法

## 相关

- [Operator scopes](/gateway/operator-scopes) — 完整作用域模型与审批时检查
- [Gateway security](/gateway/security) — 信任模型与加固基线
