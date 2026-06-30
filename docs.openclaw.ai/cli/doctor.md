# `openclaw doctor`

## 架构精读

> 跳过不影响阅读翻译正文。

### 自修复工具——为什么需要专门的诊断命令？

`openclaw doctor` 执行 19 项自动检查，发现问题时尝试自动修复：

- **配置校验**：JSON 语法、必填字段、类型匹配
- **权限检查**：文件权限、目录权限、socket 权限
- **连接测试**：AI provider API 连通性、通道连通性
- **依赖检查**：Node.js 版本、npm 包版本、系统依赖

这跟 `brew doctor` 和 `flutter doctor` 是一个思路——不是等用户报告问题，而是主动扫描常见问题并尝试修复。19 项检查覆盖"安装后常见问题"的 80% 场景。

### 修复 vs 报告——为什么默认尝试修复？

默认行为是"检查 + 尝试修复"，而非只报告问题。修复是安全的（不删除用户数据、不修改配置值），只修复"确定安全"的问题（如文件权限、缓存清理）。

这跟 `apt --fix-broken install` 是一个思路——自动修复已知的安全修复（依赖关系、文件权限），不触碰用户配置。

---

Runs 19 automated checks covering config validation, permission checks, connectivity tests, and dependency checks. Default behavior is check + auto-fix (safe fixes only — file permissions, cache cleanup). Does not delete user data or modify config values.

执行 19 项自动检查，覆盖配置校验、权限检查、连接测试和依赖检查。默认行为是检查 + 自动修复（仅安全修复——文件权限、缓存清理）。不删除用户数据，不修改配置值。
