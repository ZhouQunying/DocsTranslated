# Doctor

**总结：** `openclaw doctor` 是 OpenClaw 的修复和迁移工具——修复过期 config/state、检查健康、提供可操作的修复步骤。

> **类比：brew doctor + terraform validate + kubectl debug。** brew doctor 检查 Homebrew 环境并建议修复，terraform validate 校验 HCL 语法和 provider 兼容性，kubectl debug 诊断 pod 问题。OpenClaw doctor 类似——19 项检查（config normalize/legacy migration/state repair/OAuth 处理/service audit），支持 headless 模式（`--yes`/`--fix`/`--lint`/`--non-interactive`，CI/preflight 可用），read-only lint 模式不修改任何状态。
>
> **架构要点：** Quick start：基本命令 + 自动化模式（`--yes` 自动确认、`--fix` 自动修复、`--lint` 只检查、`--non-interactive` 无交互）；Read-only lint mode：CI/preflight 友好，结构化健康检查，不提示/不修复/不修改状态；What it does：分类概览（health check/config migration/state integrity/gateway service/auth+security/workspace operation）；Dreams UI backfill + reset：Control UI 的 grounded dreaming workflow action（gateway RPC method，与 CLI doctor 独立）；Detailed behavior：19 项 doctor 操作的详细说明和理由（config normalize/legacy migration/state repair/OAuth handle/service audit 等）。
