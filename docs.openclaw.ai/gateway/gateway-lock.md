# Gateway Lock

**总结：** 单例保护机制——通过绑定 WebSocket listener 防止重复实例，避免端口冲突。

> **类比：PID file + flock + EADDRINUSE 检测。** PID file 防止 daemon 重复启动（如 nginx/redis），flock 文件锁保证进程互斥，EADDRINUSE 检测端口是否被占用。OpenClaw gateway lock 类似——config-specific lock file + port probe + abandoned lock reclaim + exclusive TCP bind，启动时获取锁 → probe port → reclaim 废弃锁 → 独占 TCP 连接，bind 失败（`EADDRINUSE`）时抛出特定异常并立即反馈冲突信息，不使用 stale file（避免 abrupt termination 遗留）。
>
> **架构要点：** Why：防止同端口重复实例、abrupt termination 不留 stale file、冲突时立即反馈；Mechanism：获取 config-specific lock file → probe port → reclaim abandoned lock → 独占 TCP 连接，`EADDRINUSE` 时抛出异常；Error surface：启动时特定异常（`"another gateway instance is already listening on ws://127.0.0.1:<port>"`、socket bind 失败）；Operational notes：端口冲突解决、service manager 配置（exit code 78 防止无限重启循环）、macOS PID 保护。
