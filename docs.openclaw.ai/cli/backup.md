# `openclaw backup`

## 架构精读

> 跳过不影响阅读翻译正文。

### 备份范围——为什么只备份状态目录而非全量？

`openclaw backup` 只备份状态目录（会话数据、配置、配对信息），不备份工作目录（用户文件）：

```
openclaw backup create --output backup.tar.gz
```

这跟 etcd 的快照备份是一个思路——只备份元数据（key-value 存储），不备份应用数据。状态目录是网关的"大脑"（会话、配置、认证），工作目录是用户的"文件柜"（项目文件），备份优先级不同。

### 原子快照——为什么需要一致性保证？

备份创建原子快照（某一时刻的完整状态），而非增量备份。备份过程中网关暂停写入，确保快照一致性。

这跟数据库的 `pg_dump` 是一个思路——导出时锁定表（或用 MVCC 快照），确保导出的数据是某一时刻的一致状态，而非混合了新旧数据的脏快照。

### 恢复流程——为什么需要显式恢复命令？

恢复用 `openclaw backup restore`，而非手动解压覆盖。恢复命令验证备份完整性、清理旧状态、原子替换。

这跟 K8s 的 `etcd restore` 是一个思路——不是简单地把备份文件复制回去，而是有验证（checksum）、清理（旧数据）、替换（原子操作）的完整流程。

---

Creates atomic snapshots of the state directory (sessions, config, pairing data) — not the workspace (user files). Backup pauses writes for consistency. Restore uses `openclaw backup restore` with integrity verification, old state cleanup, and atomic replacement.

创建状态目录（会话、配置、配对数据）的原子快照——不备份工作目录（用户文件）。备份暂停写入保证一致性。恢复用 `openclaw backup restore`，包含完整性验证、旧状态清理和原子替换。
