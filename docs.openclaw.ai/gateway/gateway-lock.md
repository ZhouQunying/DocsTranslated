# Gateway lock

## 架构精读

> 跳过不影响阅读翻译正文。

### Gateway lock——防止多个 Gateway 实例同时运行

OpenClaw 使用 **lock file**(锁文件)防止同一台机器上运行多个 Gateway 实例:

```
~/.openclaw/gateway.lock
```

**为什么需要 lock?** 因为多个 Gateway 实例会冲突:
- **端口冲突**: 两个 Gateway 都想绑定 1455 端口,第二个会失败
- **状态不一致**: 两个 Gateway 各自维护自己的 session 数据库,数据不同步
- **命令路由混乱**: 用户发消息,不知道哪个 Gateway 会处理

Lock file 保证: 同一时间只有一个 Gateway 实例在运行。

**这跟数据库的 lock file 是一个思路**——PostgreSQL 启动时创建 `postmaster.pid`,防止多个 PostgreSQL 实例同时运行。OpenClaw 的 gateway.lock 也是同样: 防止多实例冲突。

### Lock file 的内容——记录持有者信息

Lock file 包含:
- **PID**(进程 ID): 持有 lock 的 Gateway 进程的 PID
- **启动时间**: Gateway 启动的时间戳
- **配置目录**: Gateway 使用的配置目录路径

**为什么记录这些信息?** 因为:
- **检测 stale lock**: 如果 PID 对应的进程不存在(已经崩溃或被杀),lock 是"stale"(过期的),可以被覆盖
- **诊断问题**: 如果 Gateway 启动失败(报"lock already held"),可以检查 lock file 里的 PID,看看是哪个进程持有 lock
- **多配置目录**: 如果同一台机器上有多个 Gateway(用不同的配置目录),每个有自己的 lock,不冲突

### Stale lock 检测——崩溃后自动清理

如果 Gateway 崩溃(没有正常退出),lock file 可能残留。新的 Gateway 启动时:

1. 读取 lock file 里的 PID
2. 检查这个 PID 对应的进程是否存在
3. 如果不存在,认为是 stale lock,删除并创建新 lock
4. 如果存在,报"lock already held",启动失败

**为什么需要 stale lock 检测?** 因为:
- Gateway 可能因为 bug 崩溃(没有正常退出,没删除 lock file)
- 系统可能意外关机(如断电,没机会删除 lock file)
- 如果没有 stale lock 检测,Gateway 崩溃后就无法重启(因为 lock 还在)

**这跟 MySQL 的 InnoDB crash recovery 是一个思路**——MySQL 崩溃后,InnoDB 检测未提交的事务,自动回滚或提交。OpenClaw 的 stale lock 检测也是同样: 检测崩溃后的残留 lock,自动清理。

### 多配置目录的隔离——每个 Gateway 有自己的 lock

如果同一台机器上运行多个 Gateway(用不同的 `--config-dir`),每个 Gateway 有自己的 lock file:

```
~/.openclaw-instance-a/gateway.lock
~/.openclaw-instance-b/gateway.lock
```

**为什么这样设计?** 因为多实例场景下,每个 Gateway 是独立的,不应该互相干扰。每个 Gateway 用自己的配置目录,有自己的 lock file,互不冲突。

**这跟 Docker 的 --data-root 是一个思路**——多个 Docker daemon 可以跑在同一台机器上,通过不同的 data root 目录隔离。OpenClaw 的多 Gateway 也是同样: 通过不同的配置目录隔离,每个有自己的 lock。

### Lock 的粒度——per-instance,不是 per-machine

Lock 是 **per-instance**(每个实例一个),不是 **per-machine**(每台机器一个):

- Per-machine: 一台机器只能运行一个 Gateway(太严格)
- Per-instance: 一台机器可以运行多个 Gateway,只要用不同的配置目录

**为什么 per-instance?** 因为多租户场景下,一台服务器可能需要运行多个 Gateway(每个租户一个)。Per-instance lock 允许多个 Gateway 共存,per-machine lock 不允许。

**这跟端口绑定是一个思路**——同一台机器上,多个进程可以绑定不同端口,但不能绑定同一端口。OpenClaw 的 lock 也是同样: 多个 Gateway 可以用不同配置目录,但不能用同一配置目录。
