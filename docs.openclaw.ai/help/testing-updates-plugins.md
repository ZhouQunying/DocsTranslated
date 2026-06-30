# Testing: updates and plugins

## 架构精读

> 跳过不影响阅读翻译正文。

### 插件更新测试——为什么强调"无变化时保持稳定"？

测试框架验证插件更新在无底层变化时保持稳定：

- **保持不变**：安装记录、解析源、已安装依赖布局、启用状态在更新期间"保持不变"
- **容器化测试**：确认未更改的插件不触发不必要的重新安装或丢失元数据
- **依赖隔离**：插件依赖在托管 npm 项目内隔离，卸载时彻底清除（防止残留提升包）

这跟 npm 的 `package-lock.json` 是一个思路——锁定依赖版本，避免"意外升级"导致的行为变化。"无变化时保持稳定"确保"插件更新"不会"意外破坏现有配置"，让更新操作可预测。

### 升级路径测试——为什么不直接覆盖？

升级测试证明：从旧发布版本迁移到新候选版本不会破坏用户配置、会话或工作空间。

- **真实环境模拟**：在"脏旧用户测试数据"或已知发布基线上安装新 tarball
- **更新后修复**：专用 doctor 命令处理遗留修复和清理
- **目标**：确保"启动不应增长隐藏的兼容性迁移"来处理陈旧状态

这跟数据库迁移是一个思路——从旧版本迁移到新版本时，迁移脚本确保"旧数据"被正确转换为"新格式"。应用启动时不需要"隐藏的兼容性检查"。升级测试让"版本迁移"成为"显式、可验证"的过程。

### 验证层次——为什么需要三层？

验证通过三层执行：

1. **本地检查**：快速反馈（开发时）
2. **容器化 Docker 环境**：产品级验证（CI 时）
3. **GitHub 原生工作流**：评估精确发布 tarball（发布时）

这跟软件发布的"开发 → 测试 → 生产"是一个思路——每个阶段用不同验证层次，逐步增加真实性。三层验证让"本地快速迭代"和"发布前完整验证"都成为可能。

---

Plugin update testing: verifies stability when no underlying changes occur (install records, resolved source, dependency layout, enabled state stay intact), containerized tests confirm unchanged plugins don't trigger unnecessary reinstalls or lose metadata, plugin dependencies isolated within managed npm projects and purged during uninstallation. Upgrade path testing: proves migration from older published release to new candidate preserves user configs/sessions/workspaces, simulates real-world environments by installing new tarballs over "dirty old-user fixture" or known baseline, post-update doctor command handles legacy repairs/cleanup. Validation layers: local checks (fast feedback), containerized Docker (product-level verification), GitHub-native workflows (exact release tarballs).

插件更新测试：验证无底层变化时的稳定性。安装记录、解析源、依赖布局、启用状态保持不变。容器化测试确认未更改的插件不触发不必要的重新安装或丢失元数据。插件依赖在托管 npm 项目内隔离，卸载时彻底清除。

升级路径测试：证明从旧发布版本迁移到新候选版本保留用户配置/会话/工作空间。通过在"脏旧用户测试数据"或已知基线上安装新 tarball 模拟真实环境。更新后 doctor 命令处理遗留修复/清理。

验证层次：本地检查（快速反馈）、容器化 Docker（产品级验证）、GitHub 原生工作流（精确发布 tarball）。

架构精读："无变化时保持稳定"确保插件更新不会意外破坏现有配置。升级测试让版本迁移成为显式、可验证的过程。三层验证让"本地快速迭代"和"发布前完整验证"都成为可能。
