# Menu bar

## 架构精读

> 跳过不影响阅读翻译正文。

### Menu bar 作为控制面板——macOS 的 UI 范式

macOS app 的核心 UI 是 menu bar，不是传统窗口。这跟 Docker Desktop、1Password、Bartender 是一个思路——menu bar 是 macOS 的"系统托盘"，常驻显示、快速操作、不打断工作流。OpenClaw 选择 menu bar 而不是 dock icon，是因为 agent 是**后台服务**，不需要全屏窗口。

Menu bar 包含：
- Agent 工作状态（idle/working）
- Health 状态（三色）
- Context 子菜单（当前 session 的上下文）
- 快速操作（暂停/恢复、切换 session）

### IconState enum 和 ActivityKind——Swift 的状态管理

Menu bar 的 icon 状态用 Swift enum 管理，activity kind 用另一个 enum 表示当前活动类型（voice、text、tool call 等）。这跟 React 的 useReducer 是一个思路——用 state + action 管理 UI 状态，状态转换可预测、可测试。

enum 的好处是**穷举匹配**——Swift 的 switch 语句要求覆盖所有 case，漏了编译报错。这防止了"处理了 idle 和 working 但忘了 paused"的 UI bug。状态管理不是代码风格，而是**正确性保证**。

### Context 子菜单——把 agent 上下文暴露给用户

Context 子菜单显示当前 session 的上下文（如"正在编辑 file.md"、"正在搜索 web"）。这跟 GitHub Copilot 的 status bar 是一个思路——Copilot 显示"正在生成"或"正在读取上下文"，用户知道 agent 在干什么。OpenClaw 的 Context 子菜单更详细，显示了 agent 的**工作上下文**，让用户知道 agent 不是黑盒。
