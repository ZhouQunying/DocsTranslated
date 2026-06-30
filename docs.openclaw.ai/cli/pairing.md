# `openclaw pairing`

## 架构精读

> 跳过不影响阅读翻译正文。

### 配对管理——为什么需要专门的命令？

`openclaw pairing` 管理设备配对（信任建立）：

- **`pairing list`**：列出待审批和已批准的配对
- **`pairing approve <id>`**：批准配对请求
- **`pairing reject <id>`**：拒绝配对请求
- **`pairing revoke <id>`**：撤销已批准的配对

这跟 SSH 的 `ssh-copy-id` + `~/.ssh/authorized_keys` 是一个思路——建立信任（配对批准）→ 持久化信任（已批准列表）→ 撤销信任（删除 authorized_keys 条目）。

### 配对过期——为什么待审批配对有过期时间？

待审批配对 5 分钟后自动过期，防止"忘记审批导致永久等待"。

这跟 OAuth 授权码的过期机制是一个思路——授权码 10 分钟过期，防止被窃取后长期使用。配对请求过期防止"僵尸请求"占用审批队列。

---

Manages device pairing (trust establishment): `pairing list` (pending/approved), `pairing approve <id>` (accept), `pairing reject <id>` (deny), `pairing revoke <id>` (remove approved). Pending pairings expire after 5 minutes to prevent stale requests.

管理设备配对（信任建立）：`pairing list`（待审批/已批准）、`pairing approve <id>`（批准）、`pairing reject <id>`（拒绝）、`pairing revoke <id>`（撤销已批准）。待审批配对 5 分钟后过期，防止僵尸请求。
