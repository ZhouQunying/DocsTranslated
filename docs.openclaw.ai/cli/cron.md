# `openclaw cron`

## 架构精读

> 跳过不影响阅读翻译正文。

### 定时任务——为什么需要专门的命令？

`openclaw cron` 管理定时任务（周期性执行的操作）：

- **`cron list`**：列出所有定时任务（表达式 + 状态 + 下次执行）
- **`cron add <expr> <command>`**：添加定时任务
- **`cron remove <id>`**：删除定时任务
- **`cron enable/disable <id>`**：启用/禁用定时任务

这跟 Linux 的 `crontab -e` 是一个思路——管理定时任务（添加、删除、启用、禁用）。但 OpenClaw cron 是智能体级别的（任务由智能体执行），而非系统级别的。

### Cron 表达式——为什么用标准格式？

使用标准 cron 表达式（`*/5 * * * *` = 每 5 分钟），而非自定义语法。

这跟 Kubernetes CronJob 是一个思路——复用标准 cron 表达式（用户已经熟悉），不引入新语法。标准格式降低学习成本。

---

Manages scheduled tasks (periodic operations): `cron list` (expression, status, next run), `cron add <expr> <command>`, `cron remove <id>`, `cron enable/disable <id>`. Uses standard cron expressions (like Linux crontab), agent-level execution (not system-level).

管理定时任务（周期性操作）：`cron list`（表达式、状态、下次执行）、`cron add <expr> <command>`、`cron remove <id>`、`cron enable/disable <id>`。使用标准 cron 表达式（类似 Linux crontab），智能体级别执行（非系统级别）。
