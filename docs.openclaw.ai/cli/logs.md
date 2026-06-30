# `openclaw logs`

## 架构精读

> 跳过不影响阅读翻译正文。

### 日志聚合——为什么需要统一命令而非直接看文件？

`openclaw logs` 聚合多个日志源（网关日志、节点日志、会话日志），统一输出：

```
openclaw logs --follow --level warn
```

这跟 `kubectl logs` 和 `journalctl` 是一个思路——不需要知道日志文件在哪（`/var/log/xxx.log`），统一命令按条件过滤（级别、时间、关键词）。

### 过滤能力——为什么需要级别和关键词过滤？

支持多种过滤方式：

- **`--level`**：按级别过滤（debug/info/warn/error）
- **`--since`**：按时间过滤（最近 N 分钟/小时）
- **`--grep`**：按关键词过滤

这跟 `journalctl -p err --since "1 hour ago" -g "timeout"` 是一个思路——多维度过滤快速定位问题日志，不需要在海量日志中手动搜索。

---

Aggregates multiple log sources (gateway, nodes, sessions) with unified output. Supports filtering by level (`--level warn`), time (`--since 1h`), and keyword (`--grep "timeout"`).

聚合多个日志源（网关、节点、会话），统一输出。支持按级别（`--level warn`）、时间（`--since 1h`）和关键词（`--grep "timeout"`）过滤。
