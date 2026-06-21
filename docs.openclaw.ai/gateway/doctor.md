# Doctor

## 架构精读

> 跳过不影响阅读翻译正文。

### 19 项检查的分类——为什么分成 6 大类？

`openclaw doctor` 执行 19 项检查，分成 6 大类：

1. **Health check**：gateway 连通性、channel 状态
2. **Config migration**：旧格式迁移、新字段补全
3. **State integrity**：session 文件一致性、auth profile 完整性
4. **Gateway service**：daemon 状态、port 冲突检测
5. **Auth/security**：credential 有效性、OAuth token 过期
6. **Workspace**：目录权限、初始化文件完整性

这跟 `brew doctor` 的 diagnostic checklist 是一个思路——每次检查是独立的，发现问题时给出具体的修复建议（"Run `openclaw doctor --fix` to resolve"）。

关键设计是**可操作性**。每个检查输出"OK / WARNING / ERROR"三级状态，ERROR 附带修复命令（不是笼统的"check your config"）。

### Headless mode——为什么需要四种自动化模式？

`openclaw doctor` 支持四种自动化模式：

- `--yes`：自动确认所有提示（适合 CI）
- `--fix`：自动修复可修复的问题（适合脚本）
- `--lint`：只读模式，不修改任何状态（适合预检）
- `--non-interactive`：无交互，fail on error（适合 CI）

这跟 Ansible 的 check mode 是一个思路——`--check` 只读不执行（`--lint`），`--diff` 显示变更（`--fix` 的预演），`--yes` 自动确认。分层满足不同自动化场景。

### Read-only lint mode——为什么 CI 需要只读？

Read-only lint mode 是 CI/预检友好的模式——结构化健康检查，不提示、不修复、不修改状态。输出 JSON 格式供 CI 解析。

这跟 `terraform validate` 是一个思路——校验配置但不 apply。CI 需要确保"当前配置是健康的"，但不想在 CI pipeline 中修改任何东西。

---

`openclaw doctor` is the repair and migration tool for OpenClaw that fixes stale config/state, checks health, and provides actionable repair steps.

`openclaw doctor` 是 OpenClaw 的修复和迁移工具——修复过期 config/state、检查健康、提供可操作的修复步骤。