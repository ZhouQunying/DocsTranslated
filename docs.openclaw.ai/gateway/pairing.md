# Gateway-Owned Pairing——Gateway 主导的配对机制

## 架构精读

> 跳过不影响阅读翻译正文。

### Gateway 作为唯一权威——为什么 CLI 不能决定成员资格？

Gateway-owned pairing 把 Gateway 作为节点成员资格决策的唯一权威来源。CLI 和 UI 工具只是审批界面，不是权威来源。

这跟 K8s 的 apiserver 是一个思路——apiserver 是集群状态的唯一权威，kubectl 只是操作界面。多个工具（CLI、macOS 应用、未来前端）都能触发审批，但最终的成员资格决策由 Gateway 统一执行。集中权威防止多工具间的权限不一致。

### 令牌轮换策略——为什么每次重新配对都生成新令牌？

批准时颁发新令牌，每次重新配对都轮换：

```
首次配对: approve → token_A
重新配对: approve → token_B (token_A 失效)
```

这跟 OAuth2 刷新令牌轮换是一个思路——每次使用都生成新令牌，旧令牌立即失效。如果令牌泄露，下一次重新配对后旧令牌自动作废。

### Pending request 过期——为什么不永久保留？

Pending requests 5 分钟自动过期：

- 管理员忘记处理的请求不会永久占据队列
- 过期后节点需要重新发起配对，确保元数据是最新的

这跟 TCP SYN 超时是一个思路——半开连接不能无限等待，超时后释放资源。自动清理防止遗忘的请求积累。

### Node 命令 gating——为什么批准前禁用所有命令？

Node 命令在配对批准前保持禁用，排队的命令被丢弃而非延迟：

```
节点连接 → 自动请求配对 → 所有命令被过滤
                                    ↓
管理员批准 → 命令开始执行 (排队期间的命令已丢弃)
```

这跟 K8s `readinessProbe` 是一个思路——就绪检查通过前不接收流量。新连接的设备在获得授权前不能执行任何操作，丢弃而非延迟防止批准后涌入过期的操作。

### 本地判定的双重验证——为什么要同时检查 socket 和代理？

Loopback 判定需要 raw socket 来源和上游代理请求头都确认为本地连接。如果两者不一致，取消 loopback 声明，需要显式批准。

这跟双因素认证是一个思路——单一证据不可靠，需要两个独立来源一致才能确认。防止通过伪造代理请求头来冒充本地连接。

---

Gateway-owned pairing places the **Gateway** as the authoritative source for node membership decisions. Client interfaces (macOS app, CLI tools, future frontends) serve only as approval or rejection mechanisms for pending requests—they do not directly control membership. Two pairing mechanisms have a key distinction: **device pairing** (role `node`) happens during the WebSocket handshake and controls the connection itself; **node pairing** (`node.pair.*`) is a separate pairing store that does not control the WS handshake and only applies to clients that explicitly invoke this flow.

Gateway-owned pairing 把 **Gateway** 作为节点成员资格决策的权威来源。客户端界面仅作为待审批请求的批准或拒绝机制。两种配对机制有关键区别：**设备配对**（role `node`）在 WebSocket 握手时发生，控制连接本身。**节点配对**（`node.pair.*`）是独立的配对存储，不控制 WS 握手。

## 配对流程 / Pairing Flow

1. A node connects to the Gateway WS and initiates a pairing request
2. The Gateway creates a pending request record and broadcasts a `node.pair.requested` event
3. An administrator approves or rejects via CLI or UI
4. Upon approval, the Gateway issues a new token (tokens are rotated on each re-pairing)
5. The node reconnects with the token, reaching "paired" status

1. 节点连接 Gateway WS 并发起配对请求
2. Gateway 创建 pending request 记录并广播 `node.pair.requested` 事件
3. 管理员通过 CLI 或 UI 批准或拒绝
4. 批准后，Gateway 颁发新 token（每次重新配对时轮换）
5. 节点用 token 重连，达到 "paired" 状态

Pending requests automatically expire after **5 minutes**.

Pending requests 自动在 **5 分钟**后过期。

## CLI 接口 / CLI Interface

```bash
openclaw nodes pending          # 列出待审批请求
openclaw nodes approve <id>     # 批准请求
openclaw nodes reject <id>      # 拒绝请求
openclaw nodes status           # 显示已配对/已连接节点及能力
openclaw nodes remove --node <id|name|ip>
openclaw nodes rename --node <id|name|ip> --name "Living Room iPad"
```

## API 表面 / API Surface

### Events

- `node.pair.requested`: broadcast when a pending request is created
- `node.pair.resolved`: broadcast when approved, rejected, or expired

- `node.pair.requested`：pending request 创建时广播
- `node.pair.resolved`：批准、拒绝或过期时广播

### Methods

**`node.pair.request`**: Creates or retrieves an existing pending request. This method is **idempotent per node**—repeated calls return the same pending request. Repeated requests refresh stored node metadata and update the allowlisted command snapshot.

**`node.pair.request`**：创建或获取已有 pending request。此方法**按节点幂等**——重复调用返回同一 pending request。重复请求刷新存储的节点元数据并更新 allowlisted command 快照。

**`node.pair.list`**: Returns pending and paired nodes (requires the `operator.pairing` scope)

**`node.pair.list`**：返回 pending 和已配对节点（需要 `operator.pairing` 作用域）

**`node.pair.approve`**: Approves a pending request and issues a token. This method **always generates a new token** and never returns the token from the request phase. Approval enforces scope requirements based on declared commands:
- No commands requested: `operator.pairing`
- Non-exec commands: `operator.pairing` + `operator.write`
- System exec commands (`system.run`, `system.run.prepare`, `system.which`): `operator.pairing` + `operator.admin`

**`node.pair.approve`**：批准 pending request 并颁发 token。此方法**始终生成新 token**，永不返回请求阶段的 token。批准根据声明的 commands 强制作用域要求：
- 无 commands 请求：`operator.pairing`
- 非 exec commands：`operator.pairing` + `operator.write`
- System 执行 commands（`system.run`、`system.run.prepare`、`system.which`）：`operator.pairing` + `operator.admin`

**`node.pair.reject`**: Rejects a pending request

**`node.pair.reject`**：拒绝 pending request

**`node.pair.remove`**: Removes a paired node. For device-backed pairing, this **revokes the device's node role** by modifying `devices/paired.json` and invalidating node-role sessions. Mixed-role devices (e.g., those also holding an `operator` role) **retain their row but lose the node role**; device-only rows are deleted. Legacy gateway-owned node pairing entries that match are also removed.

**`node.pair.remove`**：移除已配对节点。对于设备支持的配对，这会通过修改 `devices/paired.json` 并失效 node-role sessions 来**撤销设备的 node role**。混合角色设备（如同时持有 `operator` role）**保留行但失去 node role**，仅 node 的设备行被删除。同时移除匹配的 legacy gateway-owned node pairing 条目。

**`node.pair.verify`**: Verifies a `{ nodeId, token }` pair

**`node.pair.verify`**：验证 `{ nodeId, token }` 对

Requests may include `silent: true` as a hint for auto-approval workflows.

请求可包含 `silent: true` 作为自动批准工作流的提示。

## 安全与信任边界 / Security and Trust Boundaries

### Node command gating (2026.3.31+)

**Breaking change**: Node commands remain **disabled until node pairing is approved**—device pairing alone no longer exposes declared commands. When a node first connects, it automatically requests pairing; **all pending node commands for that node are filtered** until approval. Commands queued before pairing approval are **discarded, not deferred**.

**Breaking change**：Node commands 在**节点配对批准前保持禁用**——设备配对本身不再暴露声明的 commands。节点首次连接时自动请求配对，**该节点的所有 pending node commands 都被过滤**直到批准。配对批准前排队的 commands 被**丢弃而非延迟**。

### Node event 信任边界 / Node Event Trust Boundary (2026.3.31+)

**Breaking change**: Node-initiated operations are confined to a **reduced trusted surface**. Node summary and session events are restricted to the expected trusted surface, preventing escalation beyond what the node trust boundary allows for host-level tool access.

**Breaking change**：节点发起的操作保持在**缩减的受信任表面内**。节点摘要和 session events 限制在预期的受信任表面，防止升级为超出节点信任边界允许的 host-level tool access。

`node.presence.alive` events are **only accepted from authenticated node device sessions**, and pairing metadata is only updated when the device/node identity is already paired. A self-declared `client.id` value is **insufficient to write last-seen status**.

`node.presence.alive` 事件**只从已认证的节点设备 session 接受**，只在设备/节点身份已配对时更新配对元数据。自行声明的 `client.id` 值**不足以写入 last-seen 状态**。

### 本地性和转发 headers / Locality and Forwarded Headers

Gateway pairing **only treats a connection as loopback when both the raw socket and upstream proxy evidence agree**. If a request arrives on loopback but carries `Forwarded`, `X-Forwarded-*`, or `X-Real-IP` header evidence, this **revokes the loopback locality claim** and requires explicit approval.

Gateway pairing **只在 raw socket 和上游 proxy 证据都一致时才把连接视为 loopback**。如果请求到达 loopback 但带有 `Forwarded`、`X-Forwarded-*` 或 `X-Real-IP` header 证据，这**取消 loopback 本地声明**，需要显式批准。

### Token 安全 / Token Security

Tokens are secrets; `paired.json` must be treated as a sensitive file. Token rotation requires re-approval or node entry deletion.

Token 是 secret，`paired.json` 必须被视为敏感文件。Token 轮换需要重新批准或节点条目删除。

## 自动批准机制 / Auto-Approval Mechanisms

### Silent approval (macOS app)

The macOS app can attempt silent approval when the request is marked as silent and the app can **verify an SSH connection to the gateway host using the same user**. A failed silent approval falls back to the standard prompt.

macOS 应用可以在请求标记为 silent 且应用能**验证到 gateway host 的 SSH 连接使用同一用户**时尝试 silent approval。失败的 silent approval 回退到标准提示。

### Trusted-CIDR 设备自动批准 / Trusted-CIDR Device Auto-Approval

For private networks where the Gateway **already trusts the network path**, auto-approval can be enabled via explicit CIDRs:

对于 Gateway **已信任网络路径**的私有网络，可以通过显式 CIDR 启用自动批准：

```json5
{
  gateway: {
    nodes: {
      pairing: {
        autoApproveCidrs: ["192.168.1.0/24"]
      }
    }
  }
}
```

Security constraints:
- `autoApproveCidrs` is disabled when unset
- **No whole-LAN or private-network auto-approval mode**
- Only **new role: node device pairings with no requested scopes qualify**
- Operator, browser, Control UI, and WebChat clients remain manual
- Role, scope, metadata, and public key upgrades remain manual
- Same-host loopback trusted-proxy paths **do not qualify, because that path can be forged by local callers**

安全约束：
- `autoApproveCidrs` 未设置时禁用
- **没有全 LAN 或私有网络自动批准模式**
- 只有**新 role: node 设备配对且无请求作用域才有资格**
- Operator、browser、Control UI、WebChat 客户端保持手动
- Role、作用域、元数据、公钥升级保持手动
- Same-host loopback trusted-proxy 路径**没有资格，因为该路径可被本地调用者伪造**

### 元数据升级自动批准 / Metadata-Upgrade Auto-Approval

When a paired device reconnects with **only non-sensitive metadata changes** (display name, platform hints), OpenClaw applies a `metadata-upgrade` classification. Silent auto-approval **only applies to trusted non-browser local reconnections that have proven possession of local or shared credentials**, including same-host native app reconnections after OS changes. Browser/Control UI and remote clients **still use the explicit re-approval flow**. Scope upgrades and public key changes **do not qualify** and require explicit re-approval.

已配对设备重连时**只有非敏感元数据变更**（显示名、平台提示），OpenClaw 应用 `metadata-upgrade` 分类。Silent 自动批准**只适用于已证明持有本地或共享凭证的受信任非浏览器本地重连**，包括 OS 变更后的同主机 native app 重连。Browser/Control UI 和远程客户端**仍使用显式重新批准流程**。作用域升级和公钥变更**没有资格**，保持显式重新批准。

## 配置与存储 / Configuration and Storage

Pairing state is stored under the Gateway state directory (default `~/.openclaw`):
- `~/.openclaw/nodes/paired.json`
- `~/.openclaw/nodes/pending.json`

配对状态存储在 Gateway state 目录下（默认 `~/.openclaw`）：
- `~/.openclaw/nodes/paired.json`
- `~/.openclaw/nodes/pending.json`

Set `OPENCLAW_STATE_DIR` to relocate the `nodes/` folder accordingly.

设置 `OPENCLAW_STATE_DIR` 相应移动 `nodes/` 文件夹。

### QR 配对 / QR Pairing

The `/pair qr` command renders the pairing payload as structured media, allowing mobile and browser clients to scan directly. Device removal also **cleans up any expired pending pairing requests**, preventing orphaned rows.

`/pair qr` 命令把配对 payload 渲染为结构化媒体，允许移动和浏览器客户端直接扫描。设备删除也**清理任何过期的 pending pairing requests**，防止孤立行。

## 传输层行为

The transport layer operates statelessly and does not store membership. If the Gateway is offline or pairing is disabled, **nodes cannot pair**. In remote mode, **pairing still occurs in the remote Gateway's store**.

传输层无状态运行，不存储成员资格。如果 Gateway 离线或配对禁用，**节点不能配对**。远程模式下，**配对仍在远程 Gateway 的存储中发生**。

## 重要说明 / Important Notes

Node pairing is a trust and identity flow with token issuance, but it **does not pin the real-time node command surface per node**. Real-time commands come from what the node declares at connection time, after gateway policy (`gateway.nodes.allowCommands` and `denyCommands`) is applied. Per-node `system.run` allow/ask policy lives under the node's `exec.approvals.node.*`, not in the pairing record.

Node pairing 是信任和身份流程加 token 颁发，但**不固定每个节点的实时 node command surface**。实时 commands 来自节点连接时声明的内容，经 gateway policy（`gateway.nodes.allowCommands` 和 `denyCommands`）应用后的结果。Per-node `system.run` allow/ask policy 存在于节点的 `exec.approvals.node.*`，不在配对记录中。
