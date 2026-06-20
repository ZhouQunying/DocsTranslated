# Windows

## 架构精读

> 跳过不影响阅读翻译正文。

### 三种运行模式——Hub / CLI / WSL2

Windows 提供三种 OpenClaw 运行模式：
1. **Windows Hub**：原生 WinUI 桌面 app，带 tray icon、chat、Command Center
2. **Native CLI**：PowerShell 安装，终端优先
3. **WSL2**：在 WSL2 里跑 Linux Gateway，最兼容

这跟 Docker 在 Windows 上的策略是一个思路。Docker Desktop 提供 GUI，Docker CLI 提供命令行，Docker Engine in WSL2 提供最佳 Linux 兼容性。OpenClaw 也是这样：Hub 给普通用户，CLI 给开发者，WSL2 给需要完整 Linux 环境的场景。

Windows Hub 的 **first-run setup** 设计很巧妙：自动创建 app-owned WSL distro，在里面安装 Gateway，然后配对。用户不需要手动折腾 WSL2 环境。这跟 Visual Studio 的"开箱即用"理念一致——降低 Windows 用户的上手门槛。

### Windows Node Mode——能力声明 + 策略控制

Windows Hub 可以注册为 OpenClaw node，声明 Windows 特有能力：Canvas、Screen、Camera、Location、TTS、STT、`system.run`。Gateway 只转发 node 声明且策略允许的命令。

隐私敏感命令（`screen.record`、`camera.snap`、`camera.clip`）需要显式 `gateway.nodes.allowCommands` opt-in。这跟 Android/iOS 的权限模型是一个思路——能力存在是一回事，权限授予是另一回事。

### Local MCP Mode——桥接 MCP 生态

Windows Hub 可以把 Windows 能力暴露为本地 MCP server，让 Claude Desktop、Claude Code、Cursor 等 MCP 客户端直接调用 Windows 能力，不需要跑 OpenClaw Gateway。

这跟 Kubernetes 的 API aggregation 是一个思路。API aggregation 让外部服务注册到 Kubernetes API server，客户端用统一的 kubectl 访问。OpenClaw 的 local MCP mode 也是这样：Windows 能力注册为 MCP server，MCP 客户端用统一的 MCP 协议访问。

这个设计的战略意义是**生态桥接**——让 OpenClaw 的 Windows 能力被整个 MCP 生态复用，而不仅仅是 OpenClaw agent 能用。
