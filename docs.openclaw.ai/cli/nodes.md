# `openclaw nodes`

## 架构精读

> 跳过不影响阅读翻译正文。

### 多节点列表——为什么需要专门的列表命令？

`openclaw nodes` 列出所有已配对节点及其状态：

- **名称**：节点标识符
- **平台**：iOS/Android/macOS
- **状态**：在线/离线
- **工具**：可用工具列表（摄像头、麦克风、位置等）

这跟 `kubectl get nodes` 是一个思路——列表视图快速看到"有哪些节点、状态如何、能力如何"，不需要逐个查看详情。

### 能力广告——为什么节点需要声明能力？

每个节点声明自己支持的工具（如 iOS 节点声明摄像头、麦克风、位置）。网关根据能力路由请求（如"拍照"只发给有摄像头的节点）。

这跟 Kubernetes 节点的 `allocatable` 资源声明是一个思路——节点声明"我有多少 CPU/内存"，调度器根据声明分配 Pod。能力声明让网关智能路由（不发"拍照"给没有摄像头的节点）。

---

Lists all paired nodes with status (online/offline), platform (iOS/Android/macOS), and available tools (camera, microphone, location). Nodes advertise capabilities; gateway routes requests based on capability matching.

列出所有已配对节点及其状态（在线/离线）、平台（iOS/Android/macOS）和可用工具（摄像头、麦克风、位置）。节点声明能力；网关根据能力匹配路由请求。
