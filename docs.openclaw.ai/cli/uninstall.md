# `openclaw uninstall`

## 架构精读

> 跳过不影响阅读翻译正文。

### 完整卸载——为什么需要专门的卸载命令？

`openclaw uninstall` 完整卸载：

- **停止进程**：停止网关 daemon 和所有子进程
- **删除包**：卸载 npm 全局包
- **清理数据**：删除状态目录、日志目录、缓存目录（可选）
- **移除配置**：删除配置文件（可选）

这跟 `brew uninstall --cleanup` 是一个思路——不仅卸载包，还清理相关数据（缓存、日志、配置）。手动卸载容易遗漏（状态目录还在，下次安装时冲突）。

### 数据保留——为什么默认保留用户数据？

默认保留用户数据（工作目录、自定义配置），只删除系统文件。需要 `--purge` 才删除所有数据。

这跟 `apt remove` vs `apt purge` 是一个思路——`remove` 保留配置（方便重装），`purge` 删除一切（彻底清理）。默认保留防止误删用户数据。

---

Complete uninstallation: stops daemon processes, removes npm packages, optionally cleans state/log/cache directories and config files. Default preserves user data (workspace, custom config); use `--purge` to remove everything.

完整卸载：停止 daemon 进程、移除 npm 包、可选清理状态/日志/缓存目录和配置文件。默认保留用户数据（工作目录、自定义配置）；用 `--purge` 删除一切。
