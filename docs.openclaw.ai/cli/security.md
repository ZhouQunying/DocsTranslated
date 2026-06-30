# `openclaw security`

## 架构精读

> 跳过不影响阅读翻译正文。

### 审计 vs 修复——为什么分开而非合并？

`openclaw security` 有两个子命令：

- **`audit`**：只读检查，发现安全问题但不修改（默认）
- **`audit --fix`**：检查并自动修复"安全的"问题

这跟 AWS Trusted Advisor 的"检查 + 修复"是一个思路——先检查（不改变任何东西），确认问题后再修复。分开设计防止"自动修复"做破坏性操作（如意外关闭安全功能）。

### --fix 的安全边界——为什么只修复"安全的"问题？

`--fix` 只应用"安全、确定性的修复"：

- **可以自动修复**：收紧群组策略、启用日志脱敏、收紧文件权限
- **不自动修复**：轮换凭证、禁用核心功能、修改网络暴露设置

这跟 `apt autoremove` 的安全策略是一个思路——自动删除"确定安全的"依赖包，不删除"可能还在用的"包。自动修复的范围严格控制，防止修复引入新问题。

### JSON 输出——为什么支持管道？

`--json` 输出结构化结果，可以管道到 CI 管道或策略验证器：

```
openclaw security audit --json | jq '.warnings | length'
```

这跟 `kubectl get pods -o json` 是一个思路——机器可读输出（JSON/YAML）支持自动化处理（CI 检查、策略验证、监控告警）。

---

Two subcommands: `audit` (read-only check, default) and `audit --fix` (check and auto-fix safe issues). `--fix` only applies safe, deterministic remediations (tighten group policies, enable log redaction, tighten file permissions) — it intentionally avoids rotating credentials, disabling core utilities, or modifying network exposure. JSON output supports piping to CI pipelines or policy validators.

两个子命令：`audit`（只读检查，默认）和 `audit --fix`（检查并自动修复安全的问题）。`--fix` 只应用安全、确定性的修复（收紧群组策略、启用日志脱敏、收紧文件权限）。故意不轮换凭证、不禁用核心功能、不修改网络暴露。JSON 输出支持管道到 CI 管道或策略验证器。
