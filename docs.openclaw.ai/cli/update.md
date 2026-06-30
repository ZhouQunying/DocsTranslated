# `openclaw update`

## 架构精读

> 跳过不影响阅读翻译正文。

### 自更新——为什么不用 npm update 直接升级？

`openclaw update` 封装了升级流程：

1. **检查更新**：比较本地版本和最新版本
2. **备份状态**：自动创建状态目录备份
3. **下载更新**：从 npm registry 下载新版本
4. **迁移数据**：运行数据迁移脚本（如有 schema 变更）
5. **重启服务**：重启网关 daemon

这跟 Chrome 的自动更新是一个思路——不是简单地替换文件，而是有备份（防止升级失败回滚）、迁移（数据格式升级）、重启（加载新代码）的完整流程。

### 版本锁定——为什么支持 `--version` 指定版本？

`--version 1.2.3` 升级到指定版本，而非最新版本。适合"生产环境不追新"的场景。

这跟 `apt install package=1.2.3` 是一个思路——生产环境需要版本锁定（避免新版本引入 bug），开发环境可以追新。

---

Self-update flow: check for updates → backup state → download from npm registry → run data migrations → restart daemon. Supports `--version` for pinning to specific versions (production stability).

自更新流程：检查更新 → 备份状态 → 从 npm registry 下载 → 运行数据迁移 → 重启 daemon。支持 `--version` 锁定到特定版本（生产稳定性）。
