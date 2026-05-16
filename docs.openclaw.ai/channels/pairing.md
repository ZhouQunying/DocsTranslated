# Pairing

> "Pairing" is OpenClaw's explicit access approval step.
> It is used in two places:
>
> 1. **DM pairing** (who is allowed to talk to the bot)
> 2. **Node pairing** (which devices/nodes are allowed to join the gateway network)

"配对（Pairing）"是 OpenClaw 显式批准访问的一步。两个地方会用到：

1. **私聊配对**（谁可以和机器人对话）
2. **节点配对**（哪些设备 / 节点可以加入 Gateway 网络）

> Security context: [Security](/gateway/security)

安全相关上下文：[安全](/gateway/security)

---

> ## 1) DM pairing (inbound chat access)

## 1）私聊配对（接收消息的访问权限）

> When a channel is configured with DM policy `pairing`, unknown senders get a short code and their message is **not processed** until you approve.

通道的 DM 策略配成 `pairing` 时，陌生发件人会收到一段短码，消息**不会被处理**，要等你批准之后才走。

> Default DM policies are documented in: [Security](/gateway/security)

各通道默认的 DM 策略写在：[安全](/gateway/security)。

> `dmPolicy: "open"` is public only when the effective DM allowlist includes `"*"`.
> Setup and validation require that wildcard for public-open configs. If existing state contains `open` with concrete `allowFrom` entries, runtime still admits only those senders, and pairing-store approvals do not widen `open` access.

`dmPolicy: "open"` 只有在有效的 DM 白名单里写了 `"*"` 时才真的对外开放。配置和校验流程会要求公开-open 模式必须有这个通配。如果现有状态是 `open` 但 `allowFrom` 里写了具体条目，运行时还是只放行这些发件人；配对存储里的批准也不会让 `open` 模式扩大访问范围。

> Pairing codes:
>
> * 8 characters, uppercase, no ambiguous chars (`0O1I`).
> * **Expire after 1 hour**. The bot only sends the pairing message when a new request is created (roughly once per hour per sender).
> * Pending DM pairing requests are capped at **3 per channel** by default; additional requests are ignored until one expires or is approved.

配对码的特征：

- 8 位大写字符，去掉了容易混的 `0O1I`。
- **1 小时后过期**。机器人只在生成新请求时发送配对消息（每个发件人大约一小时一次）。
- 每个通道默认最多保留 **3 个**待处理的私聊配对请求；之后的请求会被忽略，直到有请求过期或被批准。

---

> ### Approve a sender

### 批准一个发件人

> ```bash
> openclaw pairing list telegram
> openclaw pairing approve telegram <CODE>
> ```

```bash
openclaw pairing list telegram
openclaw pairing approve telegram <CODE>
```

> If no command owner is configured yet, approving a DM pairing code also bootstraps `commands.ownerAllowFrom` to the approved sender, such as `telegram:123456789`. That gives first-time setups an explicit owner for privileged commands and exec approval prompts. After an owner exists, later pairing approvals only grant DM access; they do not add more owners.

如果还没有配置命令所有者，批准一个 DM 配对码会同时把这个发件人写进 `commands.ownerAllowFrom`，比如 `telegram:123456789`。这样首次部署就有了一个明确的特权命令所有者，可以处理执行批准之类的提示。一旦有了所有者，后续的配对批准只给 DM 访问权限，不会再追加所有者。

> Supported channels: `discord`, `feishu`, `googlechat`, `imessage`, `irc`, `line`, `matrix`, `mattermost`, `msteams`, `nextcloud-talk`, `nostr`, `openclaw-weixin`, `signal`, `slack`, `synology-chat`, `telegram`, `twitch`, `whatsapp`, `zalo`, `zalouser`.

支持的通道：`discord`、`feishu`、`googlechat`、`imessage`、`irc`、`line`、`matrix`、`mattermost`、`msteams`、`nextcloud-talk`、`nostr`、`openclaw-weixin`、`signal`、`slack`、`synology-chat`、`telegram`、`twitch`、`whatsapp`、`zalo`、`zalouser`。

---

> ### Reusable sender groups

### 可复用的发件人组

> Use top-level `accessGroups` when the same trusted sender set should apply to multiple message channels or to both DM and group allowlists.

如果同一批受信发件人要在多个消息通道复用，或者要同时用在私聊和群白名单里，就用顶层的 `accessGroups`。

> Static groups use `type: "message.senders"` and are referenced with `accessGroup:<name>` from channel allowlists:

静态分组的 `type` 写 `"message.senders"`，在通道白名单里用 `accessGroup:<名字>` 引用：

> ```json5
> {
>   accessGroups: {
>     operators: {
>       type: "message.senders",
>       members: {
>         discord: ["discord:123456789012345678"],
>         telegram: ["987654321"],
>         whatsapp: ["+15551234567"],
>       },
>     },
>   },
>   channels: {
>     telegram: { dmPolicy: "allowlist", allowFrom: ["accessGroup:operators"] },
>     whatsapp: { groupPolicy: "allowlist", groupAllowFrom: ["accessGroup:operators"] },
>   },
> }
> ```

```json5
{
  accessGroups: {
    operators: {
      type: "message.senders",
      members: {
        discord: ["discord:123456789012345678"],
        telegram: ["987654321"],
        whatsapp: ["+15551234567"],
      },
    },
  },
  channels: {
    telegram: { dmPolicy: "allowlist", allowFrom: ["accessGroup:operators"] },
    whatsapp: { groupPolicy: "allowlist", groupAllowFrom: ["accessGroup:operators"] },
  },
}
```

> Access groups are documented in detail here: [Access groups](/channels/access-groups)

访问组的详细文档：[访问组](/channels/access-groups)。

---

> ### Where the state lives

### 状态存在哪里

> Stored under `~/.openclaw/credentials/`:
>
> * Pending requests: `<channel>-pairing.json`
> * Approved allowlist store:
>   * Default account: `<channel>-allowFrom.json`
>   * Non-default account: `<channel>-<accountId>-allowFrom.json`

存放在 `~/.openclaw/credentials/`：

- 待处理请求：`<channel>-pairing.json`
- 已批准的白名单：
  - 默认账号：`<channel>-allowFrom.json`
  - 非默认账号：`<channel>-<accountId>-allowFrom.json`

> Account scoping behavior:
>
> * Non-default accounts read/write only their scoped allowlist file.
> * Default account uses the channel-scoped unscoped allowlist file.

账号作用域规则：

- 非默认账号只读写它自己作用域下的白名单文件。
- 默认账号用通道级、不带账号作用域的那个白名单文件。

> Treat these as sensitive (they gate access to your assistant).

把这些文件当作敏感数据对待，它们决定谁能访问你的助手。

> <Note>
>   The pairing allowlist store is for DM access. Group authorization is separate. Approving a DM pairing code does not automatically allow that sender to run group commands or control the bot in groups. First-owner bootstrap is separate config state in `commands.ownerAllowFrom`, and group chat delivery still follows the channel's group allowlists (for example `groupAllowFrom`, `groups`, or per-group or per-topic overrides depending on the channel).
> </Note>

> **提示**：配对白名单只管私聊访问。群授权是另一回事。批准一个 DM 配对码，并不自动给这个发件人在群里运行命令或控制机器人的权限。首位所有者的引导信息单独写在 `commands.ownerAllowFrom` 里；群消息投递还是按通道自己的群白名单来（比如 `groupAllowFrom`、`groups`，或单个群、单个话题的覆盖配置，具体看通道）。

---

> ## 2) Node device pairing (iOS/Android/macOS/headless nodes)

## 2）节点设备配对（iOS / Android / macOS / 无头节点）

> Nodes connect to the Gateway as **devices** with `role: node`. The Gateway creates a device pairing request that must be approved.

节点以 `role: node` 的**设备**身份连到 Gateway。Gateway 会生成一条设备配对请求，必须经过批准。

> ### Pair via Telegram (recommended for iOS)

### 通过 Telegram 配对（iOS 推荐）

> If you use the `device-pair` plugin, you can do first-time device pairing entirely from Telegram:

如果装了 `device-pair` 插件，首次设备配对完全在 Telegram 里搞定：

> 1. In Telegram, message your bot: `/pair`
> 2. The bot replies with two messages: an instruction message and a separate **setup code** message (easy to copy/paste in Telegram).
> 3. On your phone, open the OpenClaw iOS app → Settings → Gateway.
> 4. Scan the QR code or paste the setup code and connect.
> 5. Back in Telegram: `/pair pending` (review request IDs, role, and scopes), then approve.

1. 在 Telegram 里给机器人发：`/pair`。
2. 机器人会回两条消息：一条说明，一条单独的**配置码**消息（方便在 Telegram 里直接复制粘贴）。
3. 在手机上打开 OpenClaw iOS App → 设置 → Gateway。
4. 扫描二维码或粘贴配置码，连接。
5. 回到 Telegram：`/pair pending`（查看请求 ID、role、scopes），然后批准。

> The setup code is a base64-encoded JSON payload that contains:
>
> * `url`: the Gateway WebSocket URL (`ws://...` or `wss://...`)
> * `bootstrapToken`: a short-lived single-device bootstrap token used for the initial pairing handshake

配置码是一段 base64 编码的 JSON，里面有：

- `url`：Gateway 的 WebSocket 地址（`ws://...` 或 `wss://...`）
- `bootstrapToken`：一个短期的单设备引导 token，用在第一次配对握手里

> That bootstrap token carries the built-in pairing bootstrap profile:
>
> * the built-in setup profile allows only the `node` role
> * after approval, the handed-off `node` token stays `scopes: []`
> * the built-in setup-code flow does not hand off an `operator` token
> * operator access requires a separate approved operator pairing or token flow
> * later token rotation/revocation remains bounded by both the device's approved role contract and the caller session's operator scopes

这个引导 token 自带内置的配对引导 profile：

- 内置的配置 profile 只允许 `node` 角色
- 批准之后下发的 `node` token 仍然是 `scopes: []`
- 内置的配置码流程不会下发 `operator` token
- 要拿到 operator 权限，得走另一条专门批准过的 operator 配对或 token 流程
- 后续的 token 轮换 / 吊销会同时受设备已批准的角色约束和调用方会话的 operator scopes 限制

> Treat the setup code like a password while it is valid.

配置码在有效期内当成密码看待。

> For Tailscale, public, or other remote mobile pairing, use Tailscale Serve/Funnel or another `wss://` Gateway URL. Plaintext `ws://` setup codes are accepted only for loopback, private LAN addresses, `.local` Bonjour hosts, and the Android emulator host. Tailnet CGNAT addresses, `.ts.net` names, and public hosts still fail closed before QR/setup-code issuance.

要走 Tailscale、公网或其他远程方式给手机配对，用 Tailscale Serve/Funnel，或者别的 `wss://` Gateway 地址。明文 `ws://` 的配置码只允许在本地回环、私有局域网地址、`.local` Bonjour 主机和 Android 模拟器主机里使用。Tailnet 的 CGNAT 地址、`.ts.net` 域名和公网主机在生成二维码 / 配置码之前就会被拦下。

---

> ### Approve a node device

### 批准一个节点设备

> ```bash
> openclaw devices list
> openclaw devices approve <requestId>
> openclaw devices reject <requestId>
> ```

```bash
openclaw devices list
openclaw devices approve <requestId>
openclaw devices reject <requestId>
```

> When an explicit approval is denied because the approving paired-device session was opened with pairing-only scope, the CLI retries the same request with `operator.admin`. This lets an existing admin-capable paired device recover a new Control UI/browser pairing without editing `devices/paired.json` by hand. The Gateway still validates the retried connection; tokens that cannot authenticate with `operator.admin` remain blocked.

如果一次显式批准因为发起方的已配对设备会话只有 pairing-only 作用域而被拒，CLI 会用 `operator.admin` 把同一请求再发一次。这样一台具备管理员权限的已配对设备就能恢复一个新的 Control UI / 浏览器配对，不必手动改 `devices/paired.json`。Gateway 还是会校验重发的连接；用 `operator.admin` 也认证不通过的 token，照样会被拒。

> If the same device retries with different auth details (for example different role/scopes/public key), the previous pending request is superseded and a new `requestId` is created.

同一设备如果换了认证信息（比如改了 role / scopes / 公钥）再来一次，先前那条待处理请求会被替换掉，生成新的 `requestId`。

> <Note>
>   An already paired device does not get broader access silently. If it reconnects asking for more scopes or a broader role, OpenClaw keeps the existing approval as-is and creates a fresh pending upgrade request. Use `openclaw devices list` to compare the currently approved access with the newly requested access before you approve.
> </Note>

> **提示**：已配对的设备不会悄悄拿到更大的权限。如果它重连时申请更多 scopes 或更高 role，OpenClaw 会保留原有的批准状态，另外生成一条新的待批准升级请求。批准前用 `openclaw devices list` 对比一下当前已批准的权限和新申请的权限。

---

> ### Optional trusted-CIDR node auto-approve

### 可选：受信 CIDR 节点自动批准

> Device pairing remains manual by default. For tightly controlled node networks, you can opt in to first-time node auto-approval with explicit CIDRs or exact IPs:

设备配对默认还是人工批准。如果节点所在的网络管控严格，可以选择性地开启首次节点自动批准，列出明确的 CIDR 或精确 IP：

> ```json5
> {
>   gateway: {
>     nodes: {
>       pairing: {
>         autoApproveCidrs: ["192.168.1.0/24"],
>       },
>     },
>   },
> }
> ```

```json5
{
  gateway: {
    nodes: {
      pairing: {
        autoApproveCidrs: ["192.168.1.0/24"],
      },
    },
  },
}
```

> This only applies to fresh `role: node` pairing requests with no requested scopes. Operator, browser, Control UI, and WebChat clients still require manual approval. Role, scope, metadata, and public-key changes still require manual approval.

这个只对全新的、没有申请额外 scopes 的 `role: node` 配对请求生效。Operator、浏览器、Control UI 和 WebChat 客户端仍然要人工批准。改 role、scope、metadata、公钥也仍然要人工批准。

---

> ### Node pairing state storage

### 节点配对状态存储

> Stored under `~/.openclaw/devices/`:
>
> * `pending.json` (short-lived; pending requests expire)
> * `paired.json` (paired devices + tokens)

存在 `~/.openclaw/devices/` 下：

- `pending.json`（短期文件，待处理请求会过期）
- `paired.json`（已配对的设备和 token）

---

> ### Notes

### 说明

> * The legacy `node.pair.*` API (CLI: `openclaw nodes pending|approve|reject|remove|rename`) is a separate gateway-owned pairing store. WS nodes still require device pairing.
> * The pairing record is the durable source of truth for approved roles. Active device tokens stay bounded to that approved role set; a stray token entry outside the approved roles does not create new access.

- 老的 `node.pair.*` API（CLI：`openclaw nodes pending|approve|reject|remove|rename`）是 Gateway 自己维护的另一套配对存储。WebSocket 节点仍然要走设备配对。
- 配对记录是已批准 role 的长期权威。活跃的设备 token 都被限制在已批准的 role 集合内；有一条游离在批准 role 之外的 token，并不会产生新的访问权限。

---

> ## Related docs

## 相关文档

> * Security model + prompt injection: [Security](/gateway/security)
> * Updating safely (run doctor): [Updating](/install/updating)
> * Channel configs:
>   * Telegram: [Telegram](/channels/telegram)
>   * WhatsApp: [WhatsApp](/channels/whatsapp)
>   * Signal: [Signal](/channels/signal)
>   * iMessage: [iMessage](/channels/imessage)
>   * Discord: [Discord](/channels/discord)
>   * Slack: [Slack](/channels/slack)

- 安全模型 + 提示词注入：[安全](/gateway/security)
- 安全升级（跑 doctor）：[更新](/install/updating)
- 各通道配置：
  - Telegram：[Telegram](/channels/telegram)
  - WhatsApp：[WhatsApp](/channels/whatsapp)
  - Signal：[Signal](/channels/signal)
  - iMessage：[iMessage](/channels/imessage)
  - Discord：[Discord](/channels/discord)
  - Slack：[Slack](/channels/slack)
