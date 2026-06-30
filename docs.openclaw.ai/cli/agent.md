# `openclaw agent`

## 架构精读

> 跳过不影响阅读翻译正文。

### 单智能体管理——为什么需要专门的命令？

`openclaw agent` 管理单个智能体的生命周期：

- **`agent get <name>`**：查看智能体配置和状态
- **`agent set <name> <key> <value>`**：修改智能体配置
- **`agent restart <name>`**：重启智能体进程

这跟 `kubectl get pod` / `kubectl set` / `kubectl rollout restart` 是一个思路——单个资源的 CRUD 操作，不需要编辑整个配置文件。

### 实时配置修改——为什么不需要重启？

`agent set` 修改配置后立即生效（热更新），不需要重启智能体。只有"基础设施类"配置（如模型切换）需要重启。

这跟 Nginx 的 `reload` vs `restart` 是一个思路——策略类配置（路由规则）可以热更新，基础设施类配置（端口绑定）需要重启。

---

Manages single agent lifecycle: `agent get <name>` (view config/status), `agent set <name> <key> <value>` (modify config with hot-reload), `agent restart <name>` (restart process). Policy changes apply immediately; infrastructure changes require restart.

管理单个智能体生命周期：`agent get <name>`（查看配置/状态）、`agent set <name> <key> <value>`（修改配置，热更新）、`agent restart <name>`（重启进程）。策略变更立即生效；基础设施变更需要重启。
