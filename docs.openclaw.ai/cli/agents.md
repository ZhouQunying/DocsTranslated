# `openclaw agents`

## 架构精读

> 跳过不影响阅读翻译正文。

### 多智能体列表——为什么需要专门的列表命令？

`openclaw agents` 列出所有已配置的智能体及其状态：

- **名称**：智能体标识符
- **模型**：使用的 AI 模型
- **状态**：活跃/空闲/错误
- **会话数**：当前活跃会话数量

这跟 `kubectl get deployments` 是一个思路——列表视图快速看到"有哪些资源、状态如何"，不需要逐个查看详情。

### 过滤和排序——为什么支持多种视图？

支持按状态过滤（`--status active`）、按模型过滤（`--model gpt-4`）、按会话数排序（`--sort sessions`）。

这跟 `kubectl get pods --field-selector status.phase=Running` 是一个思路——多维度过滤快速定位"哪些智能体在跑、哪些有问题"。

---

Lists all configured agents with status (active/idle/error), model, and session count. Supports filtering by status (`--status active`), model (`--model gpt-4`), and sorting by session count.

列出所有已配置的智能体及其状态（活跃/空闲/错误）、模型和会话数。支持按状态（`--status active`）、模型（`--model gpt-4`）过滤和按会话数排序。
