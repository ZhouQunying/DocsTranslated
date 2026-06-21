# Doctor

## 架构精读

> 跳过不影响阅读翻译正文。

### 19 项检查的分类——为什么分成 6 大类？

`openclaw doctor` 执行 19 项检查，分成 6 大类：

1. **健康检查**：gateway 连通性、频道状态
2. **配置迁移**：旧格式迁移、新字段补全
3. **状态完整性**：会话文件一致性、认证配置完整性
4. **Gateway 服务**：daemon 状态、port 冲突检测
5. **认证/安全**：凭证有效性、OAuth 令牌过期
6. **工作区**：目录权限、初始化文件完整性

这跟 `brew doctor` 的诊断清单是一个思路——每次检查是独立的，发现问题时给出具体的修复建议（"运行 `openclaw doctor --fix` 来修复"）。

关键设计是**可操作性**。每个检查输出"正常 / 警告 / 错误"三级状态，错误附带修复命令（不是笼统的"检查你的配置"）。

### 无头模式——为什么需要四种自动化模式？

`openclaw doctor` 支持四种自动化模式：

- `--yes`：自动确认所有提示（适合 CI）
- `--fix`：自动修复可修复的问题（适合脚本）
- `--lint`：只读模式，不修改任何状态（适合预检）
- `--non-interactive`：无交互，遇错即停（适合 CI）

这跟 Ansible 的检查模式是一个思路——`--check` 只读不执行（`--lint`），`--diff` 显示变更（`--fix` 的预演），`--yes` 自动确认。分层满足不同自动化场景。

### 只读静态检查模式——为什么 CI 需要只读？

只读静态检查模式是 CI/预检友好的模式——结构化健康检查，不提示、不修复、不修改状态。输出 JSON 格式供 CI 解析。

这跟 `terraform validate` 是一个思路——校验配置但不应用。CI 需要确保"当前配置是健康的"，但不想在 CI 流水线中修改任何东西。

---

`openclaw doctor` is the repair and migration tool for OpenClaw that fixes stale config/state, checks health, and provides actionable repair steps.

`openclaw doctor` 是 OpenClaw 的修复和迁移工具——修复过期 config/state、检查健康、提供可操作的修复步骤。