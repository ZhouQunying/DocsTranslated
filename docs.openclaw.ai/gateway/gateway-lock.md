# Gateway Lock

## 架构精读

> 跳过不影响阅读翻译正文。

### 配置特定的锁定文件——为什么不是全局锁？

Gateway 锁定使用配置特定的锁定文件，而非全局锁。不同配置文件的 gateway 实例可以共存（各自监听不同端口），不会互相阻塞。

这跟 Nginx 多实例是一个思路——每个 Nginx 实例有自己的 PID file（`/run/nginx-1.pid`、`/run/nginx-2.pid`），不同实例可以并行运行。全局锁会阻止这种合理的多实例部署。

### EADDRINUSE 快速失败——为什么不尝试自动恢复？

绑定失败（`EADDRINUSE`）时，系统抛出特定异常并立即反馈冲突信息：

```
another gateway instance is already listening on ws://127.0.0.1:<port>
```

这跟 PostgreSQL 的启动策略是一个思路——`postmaster.pid` 已存在且进程仍活跃时，PostgreSQL 立即退出并告诉用户 PID。快速失败比"尝试杀死占用端口的进程"更安全——后者可能误杀无关进程。

### 废弃锁回收——为什么需要自动清理旧锁？

进程异常终止（如 `kill -9`）时，锁定文件残留在磁盘上。Gateway 启动时检测锁定文件对应的 PID 是否仍然存活：

- PID 存活 → 说明另一个实例正在运行，获取锁失败
- PID 不存在 → 说明锁定文件是遗留的，自动回收

这跟 PostgreSQL 的 `postmaster.pid` 是一个思路——启动时检查 PID 文件对应的进程是否还在运行。如果没有回收机制，每次异常终止都会留下过期的锁定文件，需要用户手动删除。

### 端口探测——为什么绑定之前先探测端口？

锁机制的完整流程是：获取配置特定的锁定文件 → 探测端口 → 回收遗留锁 → 独占 TCP 连接。

端口探测区分两种场景：

- lock file 存在 + 端口被占用 → 真正的实例冲突
- lock file 存在 + 端口空闲 → 过期的 lock（可安全回收）

这跟 Redis 的 Sentinel 故障检测是一个思路——先探测再决策。不做端口探测的话，系统无法区分"真正冲突"和"过期的锁"，只能笼统报"启动失败"。

### 退出码 78——为什么用 EX_CONFIG？

Gateway 锁定失败时使用退出码 78（`EX_CONFIG`），告诉服务管理器这是配置错误。

这跟 systemd 的 `RestartPreventExitStatus` 是一个思路——特定退出码表示"不应自动重启"。如果用通用错误码（如退出码 1），服务管理器会反复重启 gateway，造成无限重启循环。

---

Singleton protection mechanism prevents duplicate instances by binding a WebSocket listener with a config-specific lock file, port probe, abandoned lock reclaim, and exclusive TCP bind. On `EADDRINUSE` failure, a specific exception is thrown with immediate conflict feedback.

单例保护机制，通过 config-specific lock file、port probe、abandoned lock reclaim 和 exclusive TCP bind 组合，防止重复实例。`EADDRINUSE` 失败时抛出特定异常，立即反馈冲突信息。
