# OpenShell——托管沙箱后端

## 架构精读

> 跳过不影响阅读翻译正文。

### Mirror vs Remote 同步策略——如何选择权威来源？

OpenShell 有两种 workspace 同步策略：mirror（双向同步，本地目录是权威来源，每次执行前后同步）和 remote（一次性上传，远程环境成为权威来源）。这跟 Git 的 push/pull 模型是一个思路——mirror 类似频繁 fetch + push，remote 类似 push 一次后在远端工作。

mirror 适合需要在本地看到文件变化的场景（编码任务），remote 适合长时间运行的 agent（减少每轮同步开销）。但 remote 模式下本地修改不会自动同步到远端，需要 rebuild 刷新。

### SSH 传输复用——为什么不用独立的传输协议？

OpenShell 复用标准 SSH 传输和远程文件系统中继，跟普通 SSH 后端共享基础设施。这跟 HTTP/2 多路复用是一个思路——在同一个连接上传输多个流，减少连接建立开销。额外的生命周期命令（list/explain/recreate）和同步选项是在 SSH 之上添加的。

### Rebuild 触发器——为什么修改配置后必须重建？

修改后端选择、同步策略或安全规则后，远端 workspace 的状态可能跟新配置不一致。rebuild 删除远端目录，下次使用时重新初始化。这跟 Docker image rebuild 是一个思路——改了 Dockerfile 必须 rebuild，旧的 container 不会自动更新。

### fd-relative 安全——为什么 pin 根文件描述符？

OpenShell pin 根目录的文件描述符，每次 read 前验证环境身份。防止 symlink 替换或 remount 目录把读取重定向到意外位置。这跟 chroot + fd-relative 操作是一个思路——通过文件描述符而非路径名访问，不受路径名变化影响。

---

### 概述 / Overview

This guide details utilizing the OpenShell system as a controlled, cloud-based execution environment for OpenClaw bots. Rather than executing local Docker instances, this system assigns environment management to a specific command-line interface. It establishes distant workspaces utilizing secure shell protocols.

本指南介绍如何使用 OpenShell 系统作为 OpenClaw bot 的受控云端执行环境。不执行本地 Docker 实例，而是把环境管理交给专用 CLI。通过 SSH 协议建立远程 workspace。

The plugin leverages the identical foundational secure shell transport and distant file system connection found in the standard secure shell setup, while introducing specialized lifecycle commands and an optional synchronization approach.

插件复用标准 SSH 设置中的 SSH 传输和远程文件系统中继，同时引入专用生命周期命令和可选同步策略。

### 前提条件 / Requirements

- The specific plugin must be installed via the package manager.
- The command-line tool needs to be accessible in your system path or configured explicitly.
- A valid account possessing environment permissions is required.
- The primary Gateway service must be active on your machine.

- 必须通过包管理器安装专用插件。
- CLI 工具需要在系统 PATH 中可访问或显式配置。
- 需要有效的环境权限账户。
- 主机上主 Gateway 服务必须运行中。

### 初始设置 / Initial Setup

1. Add the extension and configure the execution environment:

1. 安装扩展并配置执行环境：

```bash
openclaw plugins install @openclaw/openshell-sandbox
```

```json5
{
  agents: {
    defaults: {
      sandbox: {
        mode: "all",
        backend: "openshell",
        scope: "session",
        workspaceAccess: "rw"
      }
    }
  },
  plugins: {
    entries: {
      openshell: {
        enabled: true,
        config: {
          from: "openclaw",
          mode: "remote"
        }
      }
    }
  }
}
```

2. Reboot the Gateway service. During the subsequent agent interaction, the system generates a distant environment and directs tool operations through it.

2. 重启 Gateway 服务。下次 agent 交互时，系统创建远程环境并把工具操作路由到其中。

3. Confirm the setup:

3. 确认设置：

```bash
openclaw sandbox list
openclaw sandbox explain
```

### 同步策略 / Synchronization Strategies

#### 双向同步 / Bidirectional Sync (Mirror)

Select the `mirror` configuration when your local directory must remain the primary source of truth.

本地目录必须保持权威来源时选 `mirror`。

- Prior to execution, the system uploads local files to the distant environment.
- Following execution, it downloads modifications back to your machine.
- File operations utilize the bridge, yet your local directory stays authoritative between interactions.

- 执行前系统上传本地文件到远程环境。
- 执行后下载修改回本机。
- 文件操作使用中继，但交互间本地目录保持权威。

Ideal scenarios:

理想场景：

- You modify files externally and need those updates reflected automatically.
- You desire behavior closely matching the local container setup.
- You need your host directory to display distant writes after every step.

- 外部修改文件后需要自动同步。
- 希望行为接近本地容器设置。
- 需要每步后本机目录显示远程写入。

Drawback: Increased transfer overhead surrounding every execution.

缺点：每次执行前后的传输开销增加。

#### 远端为主 / Distant Primary (Remote)

Choose the `remote` configuration when the cloud environment should serve as the authoritative source.

云环境应作为权威来源时选 `remote`。

- Upon initial creation, the system uploads your local directory exactly once.
- Subsequently, all file operations interact directly with the cloud environment.
- The system will not download cloud modifications back to your machine.
- Media retrieval during prompting continues functioning via the bridge.

- 初始创建时系统只上传一次本地目录。
- 之后所有文件操作直接与云环境交互。
- 系统不会把云端修改下载回本机。
- 提示期间的媒体获取继续通过中继工作。

Modifying host files externally after the initial upload means the cloud environment will ignore those updates. Run the recreate command to refresh the seed.

初始上传后在外部修改主机文件意味着云环境会忽略这些更新。运行 recreate 命令刷新种子。

#### 策略对比 / Strategy Comparison

| Feature | Bidirectional Sync | Distant Primary |
|---|---|---|
| Authoritative Source | Local machine | Cloud environment |
| Transfer Flow | Two-way (per step) | Single initial upload |
| Step Overhead | Elevated (up/down) | Reduced (direct cloud) |
| Local Updates Seen? | Yes, next step | No, requires refresh |
| Optimal Use | Coding tasks | Extended bots, automation |

| 特性 | 双向同步 | 远端为主 |
|---|---|---|
| 权威来源 | 本机 | 云环境 |
| 传输流 | 双向（每步） | 一次性初始上传 |
| 每步开销 | 较高（上/下） | 较低（直接云端） |
| 本地更新可见？ | 是，下一步 | 否，需要刷新 |
| 最佳用途 | 编码任务 | 长时间 bot、自动化 |

### 配置字典 / Settings Dictionary

| Parameter | Type | Default | Purpose |
|---|---|---|---|
| `mode` | Sync strategy | mirror | Defines file transfer behavior |
| `command` | String | CLI name | Location of the executable |
| `from` | String | System name | Origin for initial creation |
| `gateway` | String | None | Target gateway identifier |
| `gatewayEndpoint` | String | None | Target gateway web address |
| `policy` | String | None | Security rules identifier |
| `providers` | String[] | Empty | Attached service providers |
| `gpu` | Boolean | False | Requests graphics processing |
| `autoProviders` | Boolean | True | Enables automatic provider attachment |
| `remoteWorkspaceDir` | String | Default path | Main writable cloud directory |
| `remoteAgentWorkspaceDir` | String | Agent path | Read-only agent mount location |
| `timeoutSeconds` | Number | 120 | Maximum wait time for operations |

| 参数 | 类型 | 默认值 | 用途 |
|---|---|---|---|
| `mode` | 同步策略 | mirror | 文件传输行为 |
| `command` | 字符串 | CLI 名称 | 可执行文件位置 |
| `from` | 字符串 | 系统名 | 初始创建来源 |
| `gateway` | 字符串 | 无 | 目标网关标识 |
| `gatewayEndpoint` | 字符串 | 无 | 目标网关地址 |
| `policy` | 字符串 | 无 | 安全规则标识 |
| `providers` | 字符串数组 | 空 | 附加的 service provider |
| `gpu` | 布尔 | False | 请求图形处理 |
| `autoProviders` | 布尔 | True | 自动附加 provider |
| `remoteWorkspaceDir` | 字符串 | 默认路径 | 主可写云目录 |
| `remoteAgentWorkspaceDir` | 字符串 | Agent 路径 | 只读 agent 挂载位置 |
| `timeoutSeconds` | 数字 | 120 | 最大操作等待时间 |

### 环境控制 / Environment Control

```bash
# Display all active runtimes
openclaw sandbox list

# Review applied security rules
openclaw sandbox explain

# Rebuild instances (clears cloud data, re-uploads on next use)
openclaw sandbox recreate --all
```

```bash
# 显示所有活跃运行时
openclaw sandbox list

# 查看应用的安全规则
openclaw sandbox explain

# 重建实例（清除云端数据，下次使用时重新上传）
openclaw sandbox recreate --all
```

For distant primary setups, rebuilding is critical because it eradicates the authoritative cloud directory. The subsequent interaction triggers a fresh upload. For bidirectional setups, rebuilding simply refreshes the execution context since your local machine remains authoritative.

远端为主设置中 rebuild 很关键，因为它清除权威云目录。下次交互触发全新上传。双向设置中 rebuild 只刷新执行上下文，因为本机保持权威。

#### Rebuild 触发条件 / Rebuild Triggers

Rebuild instances after modifying these parameters:

- Backend selection
- Origin source
- Sync strategy
- Security rules

修改以下参数后重建实例：

- 后端选择
- 来源
- 同步策略
- 安全规则

### 安全加固 / Safety Enhancements

The system secures the primary directory file descriptor and verifies environment identity prior to every read operation. This prevents symbolic link manipulation or remounted directories from redirecting data access outside the designated area.

系统 pin 根目录文件描述符，每次 read 前验证环境身份。防止 symlink 替换或 remount 目录把数据访问重定向到指定区域外。

### 已知限制 / Known Restrictions

- The environment web viewer is incompatible with this backend.
- Local container bind mounts do not function here.
- Container-specific runtime adjustments only affect the local container backend.

- 环境 Web 查看器与此后端不兼容。
- 本地容器 bind mount 在此不可用。
- 容器特定的运行时调整只影响本地容器后端。
