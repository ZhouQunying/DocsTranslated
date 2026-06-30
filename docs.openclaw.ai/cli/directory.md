# `openclaw directory`

## 架构精读

> 跳过不影响阅读翻译正文。

### 联系人目录——为什么需要专门的命令？

`openclaw directory` 查询通道联系人目录：

- **`directory search <query>`**：搜索联系人（按名称/号码）
- **`directory get <id>`**：获取联系人详情
- **`directory sync`**：同步本地缓存与 provider 目录

这跟 LDAP 的 `ldapsearch` 是一个思路——查询目录服务（联系人列表），搜索、获取详情、同步缓存。

### 缓存策略——为什么需要本地缓存？

联系人目录缓存在本地，避免每次查询都调用 provider API（减少延迟和 API 配额消耗）。`directory sync` 手动刷新缓存。

这跟 DNS 缓存是一个思路——本地缓存减少外部查询，手动刷新（`systemd-resolve --flush-caches`）更新过期数据。

---

Queries channel contact directory: `directory search <query>` (search by name/number), `directory get <id>` (contact details), `directory sync` (refresh local cache). Local caching reduces provider API calls and latency.

查询通道联系人目录：`directory search <query>`（按名称/号码搜索）、`directory get <id>`（联系人详情）、`directory sync`（刷新本地缓存）。本地缓存减少 provider API 调用和延迟。
