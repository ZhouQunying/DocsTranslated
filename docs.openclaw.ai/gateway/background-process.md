# Background Exec and Process Tool

## 架构精读

> 跳过不影响阅读翻译正文。

### 执行工具的双模式设计——为什么分 foreground 和 background？

执行工具提供配置选项和操作行为，分两种执行模式：

- **foreground**：同步执行，等待命令完成并返回结果
- **background**：异步执行，立即返回 会话 ID，后续用 进程工具 查询

这跟 `docker run` vs `docker run -d` 是一个思路——同步模式阻塞终端等结果（适合快速命令），异步模式立即返回容器 ID（适合长时间任务）。

关键设计是**stdin/stdout 重定向**。后台任务把 stdin/stdout 重定向到内部缓冲区，防止终端关闭时任务被杀死。

### Child process bridging——为什么外部创建的子进程需要特殊处理？

当执行工具创建的任务又创建了子进程（比如命令行脚本调用其他程序），bridging 机制确保 signal 正确转发：

- 父进程收到 SIGTERM → signal 转发给所有子进程
- 父进程异常退出 → 系统检测并清理孤儿进程

这跟 systemd 的 `KillMode=control-group` 是一个思路——停止 service 时，systemd 会杀死该 service 的所有子进程。bridging 防止"父进程死了但子进程还在跑"的孤儿进程问题。

### 进程工具的交互能力——为什么需要 send input？

进程工具管理后台 会话 的交互 action：

- **轮询状态**：查询后台任务的执行状态和输出
- **send input**：向正在运行的任务发送 stdin（支持 terminal-specific 输入）
- **terminate**：终止后台任务

这跟 `kubectl exec` 进入运行中的 pod 是一个思路——无需重启即可与正在运行的任务交互。JSON 负载让代理能结构化地解析任务输出。

---

The Background Exec and Process Tool executes shell commands via a dedicated utility, maintaining extended operations in memory — a separate process tool manages background sessions with foreground and background modes.

后台 Exec 和 Process Tool 通过专用 utility 执行 shell 命令，将扩展操作保留在内存中——独立的 process tool 管理后台 session，支持 foreground 和 background 两种模式。

Child process bridging attaches helpers to externally created tasks, ensuring proper signal forwarding and preventing orphaned processes. The process tool provides interactive actions for background sessions: poll status, send input, and terminate, all using JSON payloads.

child process bridging 将 helper 附加到外部创建的任务上，确保 signal 正确转发，防止孤儿进程。process tool 提供后台 session 的交互 action：查询状态、发送输入、终止，均使用 JSON payload。
