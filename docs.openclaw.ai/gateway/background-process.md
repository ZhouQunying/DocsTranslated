# Background Exec and Process Tool

**总结：** 通过专用 utility 执行 shell 命令并保留扩展操作在内存中——独立的 process tool 管理后台 session。

> **类比：tmux + systemd run + kubectl exec。** tmux 在后台创建 session 运行长时间任务并可 attach 回来查看，systemd run 在 transient unit 中执行命令并追踪状态，kubectl exec 进入运行中 pod 交互。OpenClaw background exec/process tool 类似——exec tool 执行 shell 命令（foreground/background 模式），child process bridging 确保外部 spawn 的任务正确转发 signal（防 orphan），process tool 管理后台 session（poll status/send input/terminate），支持 JSON payload 交互。
>
> **架构要点：** exec tool：配置选项 + 操作行为（foreground/background task 处理）；Child process bridging：attach helper 到外部 spawn 的任务，确保 signal 转发、防止 orphan 操作；process tool：后台 session 交互 action（poll status、send input、terminate）；Examples：JSON payload 示例（initiate task、inspect session、send stdin/terminal-specific input）。
