# Linux app / Linux 应用

## 架构精读

> 跳过不影响阅读翻译正文。

### OOM score 调整——Gateway 的生存策略

Linux 内核在内存不足时选择 OOM victim。OpenClaw 的巧妙设计是：**主动提高子进程的 `oom_score_adj` 到 1000**（最大值），让子进程优先被杀，保护 Gateway 进程。

这跟数据库的主从复制是一个思路。主数据库挂了损失巨大（数据丢失、服务中断），从数据库挂了可以重建。所以主库的资源优先级总是高于从库。OpenClaw 的 Gateway 就是"主库"——它持有长连接、session 状态、频道连接，被杀的代价远大于一个子进程。

实现方式是通过 `/bin/sh` wrapper，在 exec 真实命令前设置 `oom_score_adj`。这是**非特权操作**——子进程只能提高自己被杀的可能性，不能降低。覆盖的子进程包括：supervisor 命令、PTY shell、MCP stdio server、浏览器进程。

一个精妙细节：**Gateway 自己的 `oom_score_adj` 保持 0**。如果 Gateway 也提高分数，那内存不足时整个 OpenClaw 都会被杀，失去了保护的意义。只有子进程提高分数，Gateway 保持正常优先级。

### systemd user vs system service——开发 vs 生产

OpenClaw 默认安装 systemd **user** service（`~/.config/systemd/user/`）。对于共享或 always-on 服务器，应该用 **system** service。

这跟 Docker 的安装模式是一个思路。Docker Desktop 在 macOS/Windows 上用 user-level 进程，Docker Engine 在 Linux 服务器上用 system-level 服务。OpenClaw 也是这样：user service 适合个人开发机，system service 适合生产服务器。

`openclaw gateway install` 和 `openclaw onboard --install-daemon` 已经渲染了当前的规范 unit。只有在你需要自定义系统/服务管理器设置时才手动写。

### 没有原生 companion app——Linux 的"够用就好"哲学

Linux 没有原生 companion app（计划中），但 Gateway 完全受支持。这反映了 Linux 用户的使用模式：CLI-first，不需要 GUI 集成。macOS/Windows 用户需要 menu bar/tray icon，Linux 用户直接 `ssh` 进去 `openclaw gateway status` 就行。

这跟 Docker 的 Linux 策略是一个思路。Docker Desktop（macOS/Windows）有完整的 GUI，Docker Engine（Linux）只有 CLI。Linux 用户不需要 GUI，他们需要的是稳定、高效、可脚本化的命令行工具。OpenClaw 的 Linux 支持也是这样：Gateway 是核心，其他都是可选的。
