# Gateway Lock

## 架构精读

> 跳过不影响阅读翻译正文。

### Config-specific lock file——为什么不是全局锁？

Gateway lock 使用 config-specific 的 lock file，而非全局锁。不同配置文件的 gateway 实例可以共存（各自监听不同端口），不会互相阻塞。

这跟 Nginx 多实例是一个思路——每个 Nginx 实例有自己的 PID file（`/run/nginx-1.pid`、`/run/nginx-2.pid`），不同实例可以并行运行。全局锁会阻止这种合理的多实例部署。

### EADDRINUSE 快速失败——为什么不尝试自动恢复？

Bind 失败（`EADDRINUSE`）时，系统抛出特定异常并立即反馈冲突信息：

```
another gateway instance is already listening on ws://127.0.0.1:<port>
```

这跟 PostgreSQL 的启动策略是一个思路——`postmaster.pid` 已存在且进程仍活跃时，PostgreSQL 立即退出并告诉用户 PID。快速失败比"尝试杀死占用端口的进程"更安全——后者可能误杀无关进程。

### Abandoned lock reclaim——为什么需要自动清理旧锁？

进程异常终止（如 `kill -9`）时，lock file 残留在磁盘上。Gateway 启动时检测 lock file 对应的 PID 是否仍然存活：

- PID 存活 → 说明另一个实例正在运行，获取锁失败
- PID 不存在 → 说明 lock file 是遗留的，自动 reclaim

这跟 PostgreSQL 的 `postmaster.pid` 是一个思路——启动时检查 PID file 对应的进程是否还在运行。如果没有 reclaim 机制，每次异常终止都会留下过期的 lock file，需要用户手动删除。

### Port probe——为什么 bind 之前先探测端口？

Lock 机制的完整流程是：获取 config-specific lock file → probe port → reclaim abandoned lock → 独占 TCP 连接。

port probe 区分两种场景：

- lock file 存在 + 端口被占用 → 真正的实例冲突
- lock file 存在 + 端口空闲 → 过期的 lock（可安全 reclaim）

这跟 Redis 的 sentinel 故障检测是一个思路——先 probe 再决策。不做 port probe 的话，系统无法区分"真正冲突"和"过期的 lock"，只能笼统报"启动失败"。

### Exit code 78——为什么用 EX_CONFIG？

Gateway lock 失败时使用 exit code 78（`EX_CONFIG`），告诉 service manager 这是配置错误。

这跟 systemd 的 `RestartPreventExitStatus` 是一个思路——特定退出码表示"不应自动重启"。如果用通用错误码（如 exit code 1），service manager 会反复重启 gateway，造成无限重启循环。

---

Singleton protection mechanism prevents duplicate instances by binding a WebSocket listener with a config-specific lock file, port probe, abandoned lock reclaim, and exclusive TCP bind. On `EADDRINUSE` failure, a specific exception is thrown with immediate conflict feedback.

单例保护机制，通过 config-specific lock file、port probe、abandoned lock reclaim 和 exclusive TCP bind 组合，防止重复实例。`EADDRINUSE` 失败时抛出特定异常，立即反馈冲突信息。
