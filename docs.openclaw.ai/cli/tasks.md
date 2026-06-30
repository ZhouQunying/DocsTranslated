# `openclaw tasks`

## 架构精读

> 跳过不影响阅读翻译正文。

### 后台任务——为什么需要专门的命令？

`openclaw tasks` 管理后台任务（长时间运行的操作）：

- **`tasks list`**：列出活跃任务（名称 + 状态 + 进度）
- **`tasks get <id>`**：查看任务详情（日志、输出）
- **`tasks cancel <id>`**：取消任务
- **`tasks wait <id>`**：等待任务完成

这跟 `kubectl get jobs` / `kubectl logs job` 是一个思路——后台任务的列表、日志、取消操作。

### 任务 vs 会话——为什么分开？

- **会话**：交互式对话（用户 ↔ 智能体）
- **任务**：后台操作（智能体自主执行，无需用户交互）

这跟 SSH 会话 vs cron job 是一个思路——SSH 是交互式的（你输入命令，它返回结果），cron 是后台的（定时自动执行）。任务适合"帮我做这件事，做完了告诉我"。

---

Manages background tasks (long-running operations): `tasks list` (active tasks with status/progress), `tasks get <id>` (details/logs), `tasks cancel <id>` (abort), `tasks wait <id>` (block until complete). Separate from sessions (interactive) — tasks are autonomous background operations.

管理后台任务（长时间运行的操作）：`tasks list`（活跃任务，含状态/进度）、`tasks get <id>`（详情/日志）、`tasks cancel <id>`（取消）、`tasks wait <id>`（等待完成）。区别于会话（交互式对话）——任务是自主后台操作。
