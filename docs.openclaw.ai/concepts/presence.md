# Presence

> OpenClaw "presence" is a lightweight, best-effort view of:
>
> * the **Gateway** itself, and
> * **clients connected to the Gateway** (mac app, WebChat, CLI, etc.)

OpenClaw 的 "presence" 是一个轻量、best-effort 的视图，包括：

- **Gateway** 本身，以及
- **连接到 Gateway 的客户端**（mac App、WebChat、CLI 等）。

> Presence is used primarily to render the macOS app's **Instances** tab and to provide quick operator visibility.

presence 主要用来渲染 macOS App 的 **Instances** 标签，以及给运维一个快速可见的视图。

---

> ## Presence fields (what shows up)

## Presence 字段（显示什么）

> Presence entries are structured objects with fields like:
>
> * `instanceId` (optional but strongly recommended): stable client identity (usually `connect.client.instanceId`)
> * `host`: human-friendly host name
> * `ip`: best-effort IP address
> * `version`: client version string
> * `deviceFamily` / `modelIdentifier`: hardware hints
> * `mode`: `ui`, `webchat`, `cli`, `backend`, `probe`, `test`, `node`, ...
> * `lastInputSeconds`: "seconds since last user input" (if known)
> * `reason`: `self`, `connect`, `node-connected`, `periodic`, ...
> * `ts`: last update timestamp (ms since epoch)

presence 条目是带这些字段的结构化对象：

- `instanceId`（可选但强烈推荐）：稳定的客户端身份（通常是 `connect.client.instanceId`）
- `host`：方便人看的主机名
- `ip`：best-effort 的 IP 地址
- `version`：客户端版本字符串
- `deviceFamily` / `modelIdentifier`：硬件提示
- `mode`：`ui`、`webchat`、`cli`、`backend`、`probe`、`test`、`node`……
- `lastInputSeconds`：距离上次用户输入多少秒（已知时）
- `reason`：`self`、`connect`、`node-connected`、`periodic`……
- `ts`：最后一次更新时间戳（毫秒）

---

> ## Producers (where presence comes from)

## 来源（presence 从哪儿来）

> Presence entries are produced by multiple sources and **merged**.

presence 条目由多个来源产生，然后**合并**。

> ### 1) Gateway self entry

### 1）Gateway 自身条目

> The Gateway always seeds a "self" entry at startup so UIs show the gateway host even before any clients connect.

Gateway 启动时总会播一条"自身"条目，让 UI 在还没有客户端连上来之前就能显示 Gateway 主机。

> ### 2) WebSocket connect

### 2）WebSocket connect

> Every WS client begins with a `connect` request. On successful handshake the Gateway upserts a presence entry for that connection.

每个 WebSocket 客户端从一个 `connect` 请求开始。握手成功后，Gateway 给这个连接 upsert 一条 presence 条目。

> #### Why one-off CLI commands do not show up

#### 为什么一次性 CLI 命令不显示

> The CLI often connects for short, one-off commands. To avoid spamming the Instances list, `client.mode === "cli"` is **not** turned into a presence entry.

CLI 经常为短的、一次性命令连一下。为了避免刷屏 Instances 列表，`client.mode === "cli"` **不会**生成 presence 条目。

> ### 3) `system-event` beacons

### 3）`system-event` 心跳

> Clients can send richer periodic beacons via the `system-event` method. The mac app uses this to report host name, IP, and `lastInputSeconds`.

客户端可以通过 `system-event` 方法发更丰富的周期性心跳。mac App 用它来上报主机名、IP 和 `lastInputSeconds`。

> ### 4) Node connects (role: node)

### 4）节点连接（role: node）

> When a node connects over the Gateway WebSocket with `role: node`, the Gateway upserts a presence entry for that node (same flow as other WS clients).

节点带 `role: node` 通过 Gateway WebSocket 连上来时，Gateway 给该节点 upsert 一条 presence 条目（流程跟其他 WebSocket 客户端一样）。

---

> ## Merge + dedupe rules (why `instanceId` matters)

## 合并 + 去重规则（为什么 `instanceId` 重要）

> Presence entries are stored in a single in-memory map:
>
> * Entries are keyed by a **presence key**.
> * The best key is a stable `instanceId` (from `connect.client.instanceId`) that survives restarts.
> * Keys are case-insensitive.

presence 条目存在一个内存 map 里：

- 条目按 **presence key** 索引。
- 最好的 key 是稳定的 `instanceId`（来自 `connect.client.instanceId`），重启后仍然有效。
- key 不区分大小写。

> If a client reconnects without a stable `instanceId`, it may show up as a **duplicate** row.

客户端没带稳定 `instanceId` 重连时，可能显示为**重复**行。

---

> ## TTL and bounded size

## TTL 和大小上限

> Presence is intentionally ephemeral:
>
> * **TTL:** entries older than 5 minutes are pruned
> * **Max entries:** 200 (oldest dropped first)

presence 刻意是短暂的：

- **TTL**：超过 5 分钟的条目会被清理
- **最大条目数**：200（最旧的先丢）

> This keeps the list fresh and avoids unbounded memory growth.

这样列表保持新鲜，且避免内存无限增长。

---

> ## Remote/tunnel caveat (loopback IPs)

## 远程 / 隧道注意事项（回环 IP）

> When a client connects over an SSH tunnel / local port forward, the Gateway may see the remote address as `127.0.0.1`. To avoid overwriting a good client-reported IP, loopback remote addresses are ignored.

客户端通过 SSH 隧道 / 本地端口转发连接时，Gateway 可能看到远端地址是 `127.0.0.1`。为了不覆盖客户端上报的真实 IP，回环远端地址会被忽略。

---

> ## Consumers

## 消费者

> ### macOS Instances tab

### macOS Instances 标签

> The macOS app renders the output of `system-presence` and applies a small status indicator (Active/Idle/Stale) based on the age of the last update.

macOS App 渲染 `system-presence` 的输出，根据最后一次更新的年龄给出小状态指示（Active / Idle / Stale）。

---

> ## Debugging tips

## 调试小贴士

> * To see the raw list, call `system-presence` against the Gateway.
> * If you see duplicates:
>   * confirm clients send a stable `client.instanceId` in the handshake
>   * confirm periodic beacons use the same `instanceId`
>   * check whether the connection-derived entry is missing `instanceId` (duplicates are expected)

- 查原始列表，调 Gateway 的 `system-presence`。
- 看到重复时：
  - 确认客户端在握手里发了稳定的 `client.instanceId`
  - 确认周期性心跳用了同一个 `instanceId`
  - 检查是否有连接派生的条目缺 `instanceId`（这种情况预期会重复）

---

> ## Related

## 相关

> <CardGroup cols={2}>
>   <Card title="Typing indicators" href="/concepts/typing-indicators" icon="ellipsis">
>     When typing indicators are sent and how to tune them.
>   </Card>
>
>   <Card title="Streaming and chunking" href="/concepts/streaming" icon="bars-staggered">
>     Outbound streaming, chunking, and per-channel formatting.
>   </Card>
>
>   <Card title="Gateway architecture" href="/concepts/architecture" icon="diagram-project">
>     Gateway components and the WebSocket protocol that drives presence updates.
>   </Card>
>
>   <Card title="Gateway protocol" href="/gateway/protocol" icon="plug">
>     The wire protocol for `connect`, `system-event`, and `system-presence`.
>   </Card>
> </CardGroup>

- [输入中状态](/concepts/typing-indicators)：输入状态什么时候发、怎么调。
- [流式和分片](/concepts/streaming)：发送侧的流式、分片、按通道格式化。
- [Gateway 架构](/concepts/architecture)：Gateway 组件和驱动 presence 更新的 WebSocket 协议。
- [Gateway 协议](/gateway/protocol)：`connect`、`system-event`、`system-presence` 的 wire 协议。
