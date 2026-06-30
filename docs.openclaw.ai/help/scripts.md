# Scripts

## 架构精读

> 跳过不影响阅读翻译正文。

### 脚本目录——为什么提供而非强制？

`scripts/` 目录包含运维和本地流程的工具脚本。文档建议"优先使用命令行界面"，除非任务明确需要这些自动化文件。

- **自由裁量**：这些工具通常是可选的，可能依赖特定机器
- **审查优先**：在陌生系统上执行前，先审查脚本内容
- **认证补充**：systemd 或 Termux 移动环境的认证监控补充

这跟 Linux 的 `/usr/local/bin` 是一个思路——存放"本地自定义工具"，不是系统核心，但特定场景下有用。脚本目录提供"高级用户"的扩展能力，不强制普通用户使用。

### GitHub 辅助脚本——为什么需要只读操作？

`scripts/gh-read` 工具通过应用安装令牌执行只读 GitHub 操作，同时保留标准写凭证。

- **只读分离**：读操作使用安装令牌（权限受限），写操作使用标准凭证（完整权限）
- **配置要求**：需要特定环境变量，通过显式标志、环境设置或 git remote 解析仓库

这跟数据库的"读写分离"是一个思路——读请求走只读副本（降低主库压力），写请求走主库（保证一致性）。只读操作分离让"频繁读取"不会"消耗写凭证配额"，同时降低"误操作风险"。

### 贡献指南——为什么要求"范围狭窄"？

新自动化应保持范围狭窄，并包含适当文档。

这跟 Unix 哲学是一个思路——"做一件事，做好它"（Do one thing and do it well）。狭窄范围让脚本"易于理解、易于测试、易于维护"，避免"大而全"导致的复杂性。

---

Scripts directory: utilities for operational duties and local processes. Recommendation: prefer CLI unless task explicitly requires automation files. General usage: discretionary, may be machine-dependent, review before execution on unfamiliar systems. Authentication: discretionary additions for systemd or Termux mobile environments. GitHub helper: `scripts/gh-read` utility allows read-only GitHub operations via application installation token while preserving standard write credentials, requires specific environment configurations, resolves repositories through explicit flags/env/git remotes. Contributing: new automation should remain narrow in scope with appropriate documentation.

脚本目录：运维和本地流程的工具脚本。建议：优先使用命令行界面，除非任务明确需要自动化文件。一般使用：自由裁量，可能依赖特定机器，在陌生系统上执行前先审查。认证：systemd 或 Termux 移动环境的认证监控补充。GitHub 辅助：`scripts/gh-read` 工具通过应用安装令牌执行只读 GitHub 操作，同时保留标准写凭证，需要特定环境配置，通过显式标志/环境/git remote 解析仓库。贡献：新自动化应保持范围狭窄，包含适当文档。
