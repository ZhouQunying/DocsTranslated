# `openclaw devices`

## 架构精读

> 跳过不影响阅读翻译正文。

### 设备管理——为什么需要专门的命令？

`openclaw devices` 管理已连接设备（手机、平板、桌面客户端）：

- **`devices list`**：列出已连接设备（名称 + 平台 + 在线状态）
- **`devices info <id>`**：查看设备详情（连接时长、最后活跃）
- **`devices disconnect <id>`**：断开设备连接

这跟 `adb devices` 是一个思路——列出已连接的 Android 设备，查看详情，断开连接。设备管理让用户知道"谁在连接我的网关"。

### 设备 vs 节点——为什么区分？

- **设备**：连接的硬件（手机、平板）
- **节点**：设备上的 OpenClaw 运行时实例

这跟 Docker 宿主机 vs 容器是一个思路——宿主机是物理机器，容器是运行在宿主机上的实例。一个设备可以有多个节点（如同时运行智能体和节点）。

---

Manages connected devices (phones, tablets, desktop clients): `devices list` (name, platform, online status), `devices info <id>` (connection duration, last active), `devices disconnect <id>`. Devices are physical hardware; nodes are OpenClaw runtime instances on devices.

管理已连接设备（手机、平板、桌面客户端）：`devices list`（名称、平台、在线状态）、`devices info <id>`（连接时长、最后活跃）、`devices disconnect <id>`。设备是物理硬件；节点是设备上的 OpenClaw 运行时实例。
