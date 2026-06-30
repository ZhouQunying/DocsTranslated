# `openclaw memory`

## 架构精读

> 跳过不影响阅读翻译正文。

### 记忆管理——为什么需要专门的命令？

`openclaw memory` 管理智能体的长期记忆（跨会话持久化）：

- **`memory list`**：列出所有记忆条目
- **`memory add <text>`**：添加记忆
- **`memory remove <id>`**：删除记忆
- **`memory clear`**：清空所有记忆

这跟 Redis 的 `KEYS` / `SET` / `DEL` / `FLUSHDB` 是一个思路——键值存储的 CRUD 操作。记忆是智能体的"长期记忆"，需要显式管理（添加、查看、删除）。

### 记忆 vs 会话——为什么分开？

- **会话**：短期上下文（单次对话内）
- **记忆**：长期知识（跨所有会话）

这跟浏览器的 tab vs bookmark 是一个思路——tab 是临时状态（关闭就没了），bookmark 是持久化数据（跨会话保留）。记忆让智能体"记住"用户偏好、历史决策等长期信息。

---

Manages agent long-term memory (persisted across sessions): `memory list` (view all), `memory add <text>` (add entry), `memory remove <id>` (delete), `memory clear` (wipe all). Separate from session context (short-term, per-conversation).

管理智能体长期记忆（跨会话持久化）：`memory list`（查看全部）、`memory add <text>`（添加条目）、`memory remove <id>`（删除）、`memory clear`（清空）。区别于会话上下文（短期，单次对话内）。
