# `openclaw daemon`

## 架构精读

> 跳过不影响阅读翻译正文。

### 守护进程管理——为什么需要专门的命令而非 systemctl？

`openclaw daemon` 管理网关守护进程（启动/停止/重启/状态），封装了跨平台差异：

- **Linux**：封装 systemd（`systemctl start/stop/restart`）
- **macOS**：封装 launchd（`launchctl load/unload`）
- **Windows**：封装 Task Scheduler

这跟 Docker 的 `docker start/stop/restart` 是一个思路——用户不需要知道底层是 systemd 还是 launchd，统一接口屏蔽平台差异。

### 日志跟踪——为什么集成到 daemon 命令？

`openclaw daemon logs --follow` 实时跟踪守护进程日志，不需要手动找日志文件路径。

这跟 `kubectl logs -f` 是一个思路——不需要知道日志存在哪里（stdout/journald/文件），统一命令实时查看。

---

Manages gateway daemon process (start/stop/restart/status) with cross-platform abstraction: systemd on Linux, launchd on macOS, Task Scheduler on Windows. `daemon logs --follow` streams real-time logs without needing to find log file paths manually.

管理网关守护进程（启动/停止/重启/状态），跨平台封装：Linux 用 systemd，macOS 用 launchd，Windows 用 Task Scheduler。`daemon logs --follow` 实时跟踪日志，不需要手动找日志文件路径。
