# `openclaw config`

## 架构精读

> 跳过不影响阅读翻译正文。

### 配置管理——为什么需要专门的命令？

`openclaw config` 管理配置文件（JSON5 格式）：

- **`config get <key>`**：获取配置值
- **`config set <key> <value>`**：设置配置值
- **`config list`**：列出所有配置
- **`config validate`**：验证配置语法和类型

这跟 `git config` 是一个思路——键值对配置的 CRUD 操作。`config get/set` 操作单个键，`config list` 查看全部，`config validate` 检查语法。

### 热更新——为什么某些配置立即生效？

`config set` 修改后，策略类配置立即生效（热更新），基础设施类配置需要重启。

这跟 Nginx 的 `reload` vs `restart` 是一个思路——路由规则可以热更新（`nginx -s reload`），端口绑定需要重启。热更新让"改配置不中断服务"成为可能。

---

Manages configuration (JSON5 format): `config get <key>`, `config set <key> <value>`, `config list` (all), `config validate` (syntax and type check). Policy changes apply immediately (hot-reload); infrastructure changes require restart.

管理配置（JSON5 格式）：`config get <key>`、`config set <key> <value>`、`config list`（全部）、`config validate`（语法和类型检查）。策略变更立即生效（热更新）；基础设施变更需要重启。
