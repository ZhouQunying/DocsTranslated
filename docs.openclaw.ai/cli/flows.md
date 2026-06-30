# `openclaw flows`

## 架构精读

> 跳过不影响阅读翻译正文。

### 工作流管理——为什么需要专门的命令？

`openclaw flows` 管理工作流（多步骤自动化流程）：

- **`flows list`**：列出已定义工作流
- **`flows run <name>`**：执行工作流
- **`flows status <id>`**：查看工作流执行状态
- **`flows cancel <id>`**：取消执行中的工作流

这跟 Apache Airflow 的 DAG 管理是一个思路——定义工作流（DAG）、触发执行、查看状态、取消执行。工作流是"多步骤任务的编排"。

### 工作流 vs 任务——为什么分开？

- **任务**：单个操作（`openclaw message send`）
- **工作流**：多个操作的编排（步骤 A → 步骤 B → 步骤 C）

这跟命令行命令 vs 命令行脚本是一个思路——单个命令做一件事，脚本编排多件事。工作流适合"先做 X，然后根据结果做 Y"的复杂场景。

---

Manages workflows (multi-step automation): `flows list` (defined workflows), `flows run <name>` (execute), `flows status <id>` (execution state), `flows cancel <id>` (abort). Workflows orchestrate multiple steps; tasks are single operations.

管理工作流（多步骤自动化）：`flows list`（已定义工作流）、`flows run <name>`（执行）、`flows status <id>`（执行状态）、`flows cancel <id>`（取消）。工作流编排多个步骤；任务是单个操作。
