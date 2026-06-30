# `openclaw sessions`

## 架构精读

> 跳过不影响阅读翻译正文。

### 会话管理——为什么需要专门的命令？

`openclaw sessions` 管理对话会话：

- **`sessions list`**：列出活跃会话（通道 + 对端 + 消息数）
- **`sessions get <id>`**：查看会话详情（历史消息、上下文）
- **`sessions close <id>`**：关闭会话（释放资源）
- **`sessions archive <id>`**：归档会话（保留历史但释放上下文）

这跟 `kubectl get pods` / `kubectl describe pod` / `kubectl delete pod` 是一个思路——资源的列表、详情、删除操作。

### 归档 vs 关闭——为什么有两种结束方式？

- **关闭**：彻底删除会话（历史消息 + 上下文）
- **归档**：保留历史消息，释放上下文窗口（新对话重新开始）

这跟 Gmail 的"删除"vs"归档"是一个思路——删除不可恢复，归档可以查看历史但不占活跃空间。归档适合"对话结束了但可能还想看历史"。

---

Manages conversation sessions: `sessions list` (active sessions with channel, peer, message count), `sessions get <id>` (details), `sessions close <id>` (delete), `sessions archive <id>` (preserve history, release context).

管理对话会话：`sessions list`（活跃会话，含通道、对端、消息数）、`sessions get <id>`（详情）、`sessions close <id>`（删除）、`sessions archive <id>`（保留历史，释放上下文）。
