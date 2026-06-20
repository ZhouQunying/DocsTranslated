# Gateway lock

## 架构精读

> 跳过不影响阅读翻译正文。

### Gateway lock

**问题**: 多个 Gateway 实例同时运行会冲突 (端口冲突、状态不一致、命令路由混乱)?

**方案**: **Lock file** (锁文件) 防止多实例:
```
~/.openclaw/gateway.lock
```

**洞察**: 同一时间只有一个 Gateway 实例在运行。

**权衡**:
- ✓ 安全: 防止多实例冲突
- ✗ 限制: 不能同时运行多个实例

**模式**: 数据库 lock file——PostgreSQL `postmaster.pid` 防止多实例。

### Lock file 的内容

**问题**: 如何检测 stale lock (过期的锁)?

**方案**: Lock file 包含:
- **PID**: 持有 lock 的 Gateway 进程 ID
- **启动时间**: Gateway 启动的时间戳
- **配置目录**: Gateway 使用的配置目录路径

**洞察**: PID 用于检测 stale lock,配置目录用于多实例隔离。

**权衡**:
- ✓ 诊断: 可以检查哪个进程持有 lock
- ✓ 检测: 可以检测 stale lock

### Stale lock 检测

**问题**: Gateway 崩溃 (没有正常退出),lock file 残留,新的 Gateway 无法启动?

**方案**: **Stale lock 检测**:
1. 读取 lock file 里的 PID
2. 检查 PID 对应的进程是否存在
3. 如果不存在,删除 stale lock,创建新 lock
4. 如果存在,报"lock already held",启动失败

**洞察**: 检测崩溃后的残留 lock,自动清理。

**权衡**:
- ✓ 自动: 不需要手动删除 lock
- ✓ 可靠: 崩溃后可以重启

**模式**: MySQL InnoDB crash recovery——崩溃后检测未提交事务,自动回滚或提交。

### 多配置目录的隔离

**问题**: 同一台机器运行多个 Gateway (用不同的 `--config-dir`),如何隔离?

**方案**: 每个 Gateway 有自己的 lock file:
```
~/.openclaw-instance-a/gateway.lock
~/.openclaw-instance-b/gateway.lock
```

**洞察**: 每个 Gateway 用自己的配置目录,有自己的 lock file,互不冲突。

**权衡**:
- ✓ 隔离: 多实例不冲突
- ✓ 灵活: 一台机器可以运行多个 Gateway

**模式**: Docker `--data-root`——多个 daemon 用不同 data root 目录隔离。

### Lock 的粒度

**问题**: Lock 是 per-instance (每个实例一个) 还是 per-machine (每台机器一个)?

**方案**: **Per-instance**,不是 per-machine:
- Per-machine: 一台机器只能运行一个 Gateway (太严格)
- Per-instance: 一台机器可以运行多个 Gateway,只要用不同的配置目录

**洞察**: 多租户场景下,一台服务器可以运行多个 Gateway (每个租户一个)。

**权衡**:
- ✓ 灵活: 多 Gateway 可以共存
- ✗ 复杂: 需要管理多个配置目录

**模式**: 端口绑定——多个进程可以绑定不同端口,但不能绑定同一端口。
