# Sandboxing——沙箱隔离

## 架构精读

> 跳过不影响阅读翻译正文。

### 三种隔离模式——为什么默认只隔离非主会话？

沙箱有三种模式：off（不隔离）、non-main（只隔离非主会话）、all（全部隔离）。默认 non-main 是因为主会话通常是可信的操作员交互，非主会话（群聊、公开频道）可能接收不可信输入。这跟 CORS 同源策略是一个思路——同源信任，跨源需要检查。

### 容器作用域粒度——为什么需要 agent/session/shared 三种？

agent 作用域给每个 agent 独立环境（agent A 看不到 agent B 的文件），session 作用域给每个会话独立环境，shared 所有会话共享一个环境。这跟 Docker Compose network 是一个思路——按隔离需求选择网络模式。

### Bind mount 安全——为什么挂载 Docker socket 等于交出宿主机？

Docker bind mount 穿透沙箱文件系统，把宿主机目录暴露给容器。默认 read-write，敏感数据建议 `:ro`。挂载 `/var/run/docker.sock` 等于把宿主机控制权交给沙箱——容器可以通过 Docker API 创建特权容器。系统验证 bind source 两次（归一化路径 + 解析路径）防止 symlink 逃逸。

### 不是完美安全边界——为什么沙箱是深度防御而非银弹？

Docker 有逃逸漏洞（如 CVE-2019-5736），SSH 服务器可能被入侵。沙箱增加攻击成本但不能完全阻止。这跟防火墙是一个思路——能阻止大部分攻击，不能阻止所有。高安全场景（公开 agent、不可信内容、生产环境）应该用沙箱，个人开发和性能敏感场景可以不用。

---

### 概述 / Overview

OpenClaw provides optional environmental isolation for tool execution to minimize AI errors and reduce blast radius. The primary gateway remains on the host machine, while individual operations execute within configured boundaries.

OpenClaw 为工具执行提供可选的环境隔离，最小化 AI 错误和爆炸半径。主网关保持在宿主机上，单个操作在配置的边界内执行。

### 隔离组件 / Isolated Components

- Standard operations including file modifications and process management.
- An optional web browsing environment.

The core gateway and specifically elevated commands bypass this isolation. Elevated commands utilize an escape path to operate directly on the host machine.

- 标准操作（文件修改和进程管理）。
- 可选的 Web 浏览环境。

核心网关和 elevated 命令绕过隔离。Elevated 命令使用逃逸路径直接在宿主机上运行。

### 执行模式 / Execution Modes

- Disabled: No isolation is applied.
- Non-main: Only secondary sessions are isolated, which is the standard setup for keeping primary chats on the host.
- All: Every single session operates within an isolated environment.

- 禁用：不隔离。
- Non-main：只隔离非主会话（标准设置），主聊天保持在宿主机上。
- All：每个会话都在隔离环境中运行。

### 容器作用域 / Container Scopes

- Agent: One environment per agent.
- Session: One environment per individual session.
- Shared: A single environment for all isolated sessions.

- Agent：每个 agent 一个环境。
- Session：每个会话一个环境。
- Shared：所有隔离会话共享一个环境。

### 运行时后端 / Runtime Backends

You can select the underlying technology providing the isolation.

| Feature | Local Containers | SSH Remote | Managed OpenShell |
|---|---|---|---|
| Execution Location | Local machine | Any SSH host | OpenShell environment |
| Configuration | Setup scripts | SSH keys | Plugin activation |
| File Handling | Mounts or copies | Seed once | Mirror or remote |
| Network Settings | Configurable | Host dependent | Platform dependent |
| Browser Support | Yes | No | Not yet |
| Ideal Use Case | Local development | Remote offloading | Managed sync setups |

可选择提供隔离的底层技术：

| 特性 | 本地容器 | SSH 远程 | 托管 OpenShell |
|---|---|---|---|
| 执行位置 | 本机 | 任意 SSH 主机 | OpenShell 环境 |
| 配置 | 设置脚本 | SSH 密钥 | 插件激活 |
| 文件处理 | 挂载或复制 | 一次性同步 | Mirror 或 remote |
| 网络设置 | 可配置 | 依赖主机 | 依赖平台 |
| 浏览器支持 | 是 | 否 | 尚未 |
| 理想场景 | 本地开发 | 远程卸载 | 托管同步 |

### 本地容器详情 / Local Container Details

When activated without a specific choice, the system defaults to local containers via the Docker socket. To pass GPU access to these environments, specific configuration flags are required.

无特定选择时系统默认使用 Docker socket 的本地容器。传递 GPU 访问需要特定配置标志。

Deploying the gateway itself inside a container introduces path mapping rules. Configuration files must reference absolute host paths rather than internal container paths. Furthermore, the gateway deployment requires identical volume mappings to maintain file system bridge parity. Native code modes are disabled during active isolation to prevent conflicts.

在容器内部署网关本身引入路径映射规则。配置文件必须引用宿主机绝对路径而非容器内部路径。网关部署需要相同的 volume 映射以保持文件系统中继一致性。活跃隔离期间禁用原生代码模式防止冲突。

### SSH 远程详情 / SSH Remote Details

This option routes file and execution tools to an arbitrary remote machine.

此选项把文件和执行工具路由到任意远程机器。

```json5
{
  agents: {
    defaults: {
      sandbox: {
        mode: "all",
        backend: "ssh",
        ssh: {
          target: "user@host:22",
          workspaceRoot: "/tmp/sandboxes"
        }
      }
    }
  }
}
```

The remote directory becomes the definitive state after an initial synchronization. Local modifications made afterward will not automatically appear remotely unless the environment is recreated.

初始同步后远程目录成为权威状态。之后的本地修改不会自动同步到远程，除非重建环境。

### OpenShell 详情 / OpenShell Details

This managed backend utilizes the same SSH transport but adds specific lifecycle commands and workspace synchronization options.

此托管后端使用相同的 SSH 传输，但增加了特定生命周期命令和 workspace 同步选项。

- Mirror: The local directory remains the source of truth, syncing back and forth around executions.
- Remote: The managed environment becomes the definitive source after an initial seed, eliminating per-turn synchronization overhead.

- Mirror：本地目录保持权威来源，每次执行前后双向同步。
- Remote：初始同步后托管环境成为权威来源，消除每轮同步开销。

### Workspace 可见性 / Workspace Visibility

- None: Tools only see a dedicated internal directory.
- Read-only: The agent directory is mounted without write permissions.
- Read-write: The agent directory is mounted with full modification capabilities.

- None：工具只能看到专用内部目录。
- Read-only：agent 目录以只读方式挂载。
- Read-write：agent 目录以完全修改权限挂载。

### 自定义目录挂载 / Custom Directory Mounts

Additional host directories can be exposed to the container. Global and agent-specific mounts are combined. The system actively blocks dangerous system paths and common credential directories to prevent security bypasses. Symlink resolution is strictly checked to prevent directory escape exploits.

可以把额外的宿主机目录暴露给容器。全局和 agent 特定挂载合并。系统主动阻止危险系统路径和常见凭证目录防止安全绕过。严格检查 symlink 解析防止目录逃逸。

### 环境镜像 / Environment Images

The standard image is based on a slim Debian distribution.

标准镜像基于精简 Debian 发行版。

```bash
docker build -t custom-sandbox:slim - <<'EOF'
FROM debian:bookworm-slim
RUN apt-get update && apt-get install -y python3
EOF
```

Specialized images are available for common tooling and browser automation. The browser image includes strict Chromium startup flags to limit resource usage and disable unnecessary features like 3D APIs and extensions. Network access is disabled by default.

提供常用工具和浏览器自动化的专用镜像。浏览器镜像包含严格的 Chromium 启动标志，限制资源使用并禁用 3D API 和扩展等不必要功能。默认禁用网络访问。

### 初始化命令 / Initialization Commands

A specific configuration key allows a script to run a single time immediately after container creation. This is useful for installing packages, provided network access is enabled and the root user is utilized.

特定配置键允许脚本在容器创建后立即运行一次。适合安装包，前提是启用网络访问并使用 root 用户。

### 策略和覆盖 / Policy and Overrides

Global tool restrictions take precedence over isolation rules. An explicit escape mechanism exists for elevated commands, allowing them to bypass the isolated environment entirely. Individual agents can override these default settings to customize their specific execution contexts.

全局工具限制优先于隔离规则。elevated 命令有显式逃逸机制，允许完全绕过隔离环境。单个 agent 可以覆盖这些默认设置来自定义执行上下文。
