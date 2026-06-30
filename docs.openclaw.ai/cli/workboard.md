# `openclaw workboard`

## 架构精读

> 跳过不影响阅读翻译正文。

### 任务看板——为什么需要专门的命令？

`openclaw workboard` 管理任务看板（智能体任务队列）：

- **`workboard list`**：列出看板上的任务
- **`workboard add <task>`**：添加任务到看板
- **`workboard assign <id> <agent>`**：分配任务给智能体
- **`workboard complete <id>`**：标记任务完成

这跟 Trello 和 Jira 看板是一个思路——任务卡片（待办/进行中/完成）的可视化管理。看板让"智能体应该做什么"变得明确。

### 看板 vs 直接指令——为什么用看板？

- **直接指令**：实时告诉智能体"做这件事"（同步）
- **看板**：把任务放入队列，智能体自主领取（异步）

这跟 Kanban vs Scrum 是一个思路——Kanban 是持续流（任务随时加入），Scrum 是迭代（每个 sprint 计划）。看板适合"持续有新任务"的场景。

---

Manages task board (agent task queue): `workboard list` (tasks on board), `workboard add <task>`, `workboard assign <id> <agent>`, `workboard complete <id>`. Board uses async queue (agents pull tasks) rather than sync commands (real-time instructions).

管理任务看板（智能体任务队列）：`workboard list`（看板上的任务）、`workboard add <task>`、`workboard assign <id> <agent>`、`workboard complete <id>`。看板用异步队列（智能体领取任务），而非同步指令（实时告诉）。
