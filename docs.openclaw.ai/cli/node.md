# `openclaw node`

## 架构精读

> 跳过不影响阅读翻译正文。

### 单节点管理——为什么需要专门的命令？

`openclaw node` 管理单个节点（设备上的运行时实例）：

- **`node get <id>`**：查看节点详情（工具可用性、连接状态）
- **`node invoke <id> <tool>`**：调用节点工具（如摄像头拍照、位置获取）
- **`node exec <id> <command>`**：在节点上执行命令

这跟 `kubectl exec` 是一个思路——在远程 Pod 上执行命令。`node invoke` 调用节点工具（摄像头、麦克风），`node exec` 执行命令行命令。

### 工具调用 vs 命令执行——为什么分开？

- **`node invoke`**：调用节点工具（结构化输入/输出，如摄像头返回图片）
- **`node exec`**：执行命令行命令（文本输入/输出，如 `ls -la`）

这跟 gRPC vs SSH 是一个思路——gRPC 是结构化的（protobuf 输入/输出），SSH 是文本的（命令行输入/输出）。工具调用适合"拍照"（返回图片数据），命令执行适合"查看文件列表"（返回文本）。

---

Manages single node (runtime instance on device): `node get <id>` (details), `node invoke <id> <tool>` (invoke node tool like camera/location), `node exec <id> <command>` (execute shell command). Tool invocation returns structured data; exec returns text output.

管理单个节点（设备上的运行时实例）：`node get <id>`（详情）、`node invoke <id> <tool>`（调用节点工具如摄像头/位置）、`node exec <id> <command>`（执行命令行命令）。工具调用返回结构化数据；命令执行返回文本输出。
