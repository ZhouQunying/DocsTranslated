# `openclaw approvals`

## 架构精读

> 跳过不影响阅读翻译正文。

### 执行权限管理——为什么需要专门的命令？

`openclaw approvals` 管理跨环境的执行权限（本地、网关、节点）：

- **`exec-policy`**：同步请求配置与主机审批文件
- **`approvals get`**：查看有效策略（请求配置 + 主机强制规则合并）
- **`approvals set`**：从 JSON5 文件替换审批配置
- **`approvals allow`**：添加允许列表条目

这跟 Kubernetes RBAC 的 `kubectl auth can-i` 是一个思路——查看"我能做什么"（有效策略），设置"谁可以做什么"（审批配置）。

### 主机文件作为唯一真相源——为什么？

主机审批文件（`~/.openclaw/exec-policy.json5`）是执行权限的唯一真相源。网关和节点的配置都是"请求"，最终由主机文件决定。

这跟 sudoers 文件是一个思路——`/etc/sudoers` 是 sudo 权限的唯一真相源，其他配置（如 LDAP）只是"请求"，最终由 sudoers 合并决定。

### YOLO 模式——为什么提供"永不提示"选项？

`--yolo` 设置最大权限（跳过所有审批提示），适合开发环境快速迭代。

这跟 Docker 的 `--privileged` 是一个思路——开发时跳过所有安全限制（快速迭代），生产时启用细粒度控制。YOLO 模式明确标记为"开发用"，防止误用于生产。

---

Manages execution permissions across local/gateway/node environments: `exec-policy` (sync requested config with host approval file), `approvals get` (effective policy), `approvals set` (replace from JSON5), `approvals allow` (add allowlist entries). Host approval file is the single source of truth. YOLO mode (`--yolo`) bypasses all prompts for development speed.

管理跨环境执行权限（本地/网关/节点）。`exec-policy` 同步请求配置与主机审批文件。`approvals get` 查看有效策略。`approvals set` 从 JSON5 替换。`approvals allow` 添加允许列表条目。主机审批文件是唯一真相源。YOLO 模式（`--yolo`）跳过所有提示，适合开发速度。
