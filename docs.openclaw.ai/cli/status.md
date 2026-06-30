# `openclaw status`

## 架构精读

> 跳过不影响阅读翻译正文。

### 全景状态——为什么需要统一的状态视图？

`openclaw status` 提供系统全景：

- **网关状态**：进程 PID、运行时长、内存使用
- **通道状态**：每个通道的连接状态（在线/离线/错误）
- **节点状态**：已配对节点列表、在线状态、工具可用性
- **会话统计**：活跃会话数、总消息数
- **资源使用**：CPU、内存、磁盘

这跟 `kubectl get all` 是一个思路——一个命令看到所有资源的状态，不需要分别查 pods/services/deployments。全景视图帮助快速定位"哪里有问题"。

### 实时刷新——为什么支持 `--watch`？

`--watch` 模式每 2 秒刷新状态，适合监控部署过程中的变化。

这跟 `watch kubectl get pods` 是一个思路——持续观察状态变化，不需要手动重复运行命令。

---

Provides system panorama: gateway process (PID, uptime, memory), channel connections (online/offline/error), paired nodes (status, tool availability), session statistics (active count, total messages), and resource usage (CPU, memory, disk). `--watch` mode refreshes every 2 seconds.

提供系统全景。网关进程（PID、运行时长、内存）、通道连接（在线/离线/错误）、已配对节点（状态、工具可用性）。会话统计（活跃数、总消息数）、资源使用（CPU、内存、磁盘）。`--watch` 模式每 2 秒刷新。
