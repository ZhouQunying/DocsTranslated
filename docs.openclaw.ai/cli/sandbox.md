# `openclaw sandbox`

## 架构精读

> 跳过不影响阅读翻译正文。

### 沙箱管理——为什么需要专门的命令？

`openclaw sandbox` 管理代码执行沙箱（隔离环境）：

- **`sandbox status`**：查看沙箱状态（Docker 容器运行状态）
- **`sandbox restart`**：重启沙箱（清理状态）
- **`sandbox exec <command>`**：在沙箱内执行命令
- **`sandbox logs`**：查看沙箱日志

这跟 `docker exec` / `docker logs` 是一个思路——在容器内执行命令、查看日志。沙箱是"受限的容器"（资源限制、网络隔离、文件系统只读）。

### 沙箱 vs 直接执行——为什么隔离？

- **直接执行**：命令在主机上运行（完全权限）
- **沙箱执行**：命令在隔离环境中运行（受限权限）

这跟虚拟机 vs 容器是一个思路——虚拟机完全隔离（独立内核），容器轻量隔离（共享内核）。沙箱是"轻量隔离"（共享主机但限制权限），防止恶意代码破坏主机。

---

Manages code execution sandbox (isolated environment): `sandbox status` (Docker container state), `sandbox restart` (clean state), `sandbox exec <command>` (run inside sandbox), `sandbox logs` (view logs). Sandbox provides lightweight isolation (restricted permissions, network isolation, read-only filesystem) to prevent malicious code from damaging the host.

管理代码执行沙箱（隔离环境）：`sandbox status`（Docker 容器状态）、`sandbox restart`（清理状态）、`sandbox exec <command>`（在沙箱内执行）、`sandbox logs`（查看日志）。沙箱提供轻量隔离（受限权限、网络隔离、只读文件系统），防止恶意代码破坏主机。
