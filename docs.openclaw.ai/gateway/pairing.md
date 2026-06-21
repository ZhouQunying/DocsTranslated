# Gateway-Owned Pairing

Gateway-owned pairing 把 **Gateway** 作为节点成员资格决策的权威来源。客户端界面(macOS 应用、CLI 工具、未来前端)仅作为待审批请求的批准或拒绝机制,不直接控制成员资格。两种配对机制的关键区别: **设备配对** (role `node`) 在 WebSocket 握手时发生,控制连接本身;**节点配对** (`node.pair.*`) 是独立的配对存储,不控制 WS 握手,只对显式调用此流程的客户端生效。

> **类比:K8s 的 RBAC + ServiceAccount 颁发。** K8s 里 apiserver 是成员资格的唯一权威,ServiceAccount token 由 apiserver 颁发和轮换。Gateway-owned pairing 类似: Gateway 是节点成员资格的唯一权威,token 在批准时颁发,每次重新配对都轮换。CLI/UI 只是审批界面,不是权威来源。
>
> **架构要点:** Gateway 是权威来源,客户端只是审批机制;pending request 5 分钟自动过期;批准时颁发新 token(每次重新配对轮换);node command gating 在配对批准前禁用;node event 限制在 reduced trusted surface;loopback 判定需要 raw socket 和 proxy evidence 都一致;token 是 secret,`paired.json` 必须被视为敏感文件。

## 配对流程

1. 节点连接 Gateway WS 并发起配对请求
2. Gateway 创建 pending request 记录并广播 `node.pair.requested` 事件
3. 管理员通过 CLI 或 UI 批准或拒绝
4. 批准后,Gateway 颁发新 token(token 在每次重新配对时轮换)
5. 节点用 token 重连,达到 "paired" 状态

Pending requests 自动在 **5 分钟**后过期。

## CLI 接口

```bash
openclaw nodes pending          # 列出待审批请求
openclaw nodes approve <id>     # 批准请求
openclaw nodes reject <id>      # 拒绝请求
openclaw nodes status           # 显示已配对/已连接节点及能力
openclaw nodes remove --node <id|name|ip>
openclaw nodes rename --node <id|name|ip> --name "Living Room iPad"
```

## API surface

### Events

- `node.pair.requested`: pending request 创建时广播
- `node.pair.resolved`: 批准、拒绝或过期时广播

### Methods

**`node.pair.request`**: 创建或获取已有 pending request。此方法**按节点幂等**,重复调用返回同一 pending request。重复请求刷新存储的节点元数据并更新 allowlisted command 快照。

**`node.pair.list`**: 返回 pending 和 paired 节点(需要 `operator.pairing` 作用域)

**`node.pair.approve`**: 批准 pending request 并颁发 token。此方法**始终生成新 token**,永不返回请求阶段的 token。批准根据声明的 commands 强制作用域要求:
- 无 commands 请求: `operator.pairing`
- 非 exec commands: `operator.pairing` + `operator.write`
- System 执行 commands (`system.run`、`system.run.prepare`、`system.which`): `operator.pairing` + `operator.admin`

**`node.pair.reject`**: 拒绝 pending request

**`node.pair.remove`**: 移除已配对节点。对于设备支持的配对,这会通过修改 `devices/paired.json` 并失效 node-role sessions 来**撤销设备的 node role**。混合角色设备(如同时持有 `operator` role)**保留行只失去 node role**,仅 node 的设备行被删除。同时移除匹配的 legacy gateway-owned node pairing 条目。

**`node.pair.verify`**: 验证 `{ nodeId, token }` 对

请求可包含 `silent: true` 作为自动批准工作流的提示。

## 安全与信任边界

### Node command gating (2026.3.31+)

**Breaking change**: Node commands 在**节点配对批准前保持禁用**——设备配对本身不再暴露声明的 commands。节点首次连接时自动请求配对,**该节点的所有 pending node commands 都被过滤**直到批准。配对批准前排队的 commands 被**丢弃而非延迟**。

### Node event 信任边界 (2026.3.31+)

**Breaking change**: 节点发起的操作保持在 **reduced trusted surface**。节点摘要和 session events 限制在预期的 trusted surface,防止升级为超出节点信任边界允许的 host-level tool access。

`node.presence.alive` 事件**只从已认证的节点设备 session 接受**,只在设备/节点身份已配对时更新配对元数据。自声明的 `client.id` 值**不足以写入 last-seen 状态**。

### Locality 和 forwarded headers

Gateway pairing **只在 raw socket 和上游 proxy evidence 都一致时才把连接视为 loopback**。如果请求到达 loopback 但带有 `Forwarded`、`X-Forwarded-*` 或 `X-Real-IP` header evidence,这**取消 loopback locality 声明**,需要显式批准。

### Token 安全

Token 作为 secret,`paired.json` 必须被视为敏感文件。Token 轮换需要重新批准或节点条目删除。

## 自动批准机制

### Silent approval (macOS app)

macOS 应用可以在请求标记为 silent 且应用能**验证到 gateway host 的 SSH 连接使用同一用户**时尝试 silent approval。失败的 silent approval fallback 到标准提示。

### Trusted-CIDR 设备自动批准

对于 Gateway **已信任网络路径**的私有网络,可以通过显式 CIDRs 启用自动批准:

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

安全约束:
- `autoApproveCidrs` 未设置时禁用
- **没有全 LAN 或 private-network 自动批准模式**
- 只有**新 role: node 设备配对且无请求作用域才有资格**
- Operator、browser、Control UI、WebChat 客户端保持手动
- Role、作用域、元数据、公钥升级保持手动
- Same-host loopback trusted-proxy 路径**没有资格,因为该路径可被本地调用者伪造**

### 元数据升级自动批准

已配对设备重连时**只有非敏感元数据变更**(显示名、平台提示),OpenClaw 应用 `metadata-upgrade` 分类。Silent 自动批准**只适用于已证明持有本地或共享凭证的受信任非浏览器本地重连**,包括 OS 变更后的同主机 native app 重连。Browser/Control UI 和远程客户端**仍使用显式重新批准流程**。作用域升级和公钥变更**没有资格**,保持显式重新批准。

## 配置与存储

配对状态存储在 Gateway state 目录下(默认 `~/.openclaw`):
- `~/.openclaw/nodes/paired.json`
- `~/.openclaw/nodes/pending.json`

设置 `OPENCLAW_STATE_DIR` 相应移动 `nodes/` 文件夹。

### QR 配对

`/pair qr` 命令把配对 payload 渲染为结构化媒体,允许移动和浏览器客户端直接扫描。设备删除也**清扫任何过期的 pending pairing requests**,防止孤立行。

## 传输行为

传输层无状态运行,不存储成员资格。如果 Gateway 离线或配对禁用,**节点不能配对**。远程模式下,**配对仍在远程 Gateway 的 store 发生**。

## 重要说明

Node pairing 是信任和身份流程加 token 颁发,但**不固定每个节点的实时 node command surface**。实时 commands 来自节点连接时声明的内容,经 gateway policy (`gateway.nodes.allowCommands` 和 `denyCommands`) 应用后的结果。Per-node `system.run` allow/ask policy 存在于节点的 `exec.approvals.node.*`,不在配对记录中。
