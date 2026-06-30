# Node Troubleshooting

## 架构精读

> 跳过不影响阅读翻译正文。

### 命令阶梯——为什么先验证系统再验证设备？

节点故障排查的诊断流程是命令阶梯：

1. `openclaw status` → 验证系统（网关 + 节点连接状态）
2. `openclaw nodes` → 验证节点（配对 + 在线状态）
3. `openclaw doctor` → 深度诊断（权限 + 工具授权 + 日志）

这跟 PagerDuty 的升级策略是一个思路——逐层升级，从快速检查到深度排查。每层有明确的"什么情况下进入下一层"的判断标准。

### 前台要求——为什么摄像头和麦克风需要应用在前台？

摄像头（camera.snap/camera.clip）和麦克风工具只在应用**前台显示**时工作。后台运行时返回 `background_unavailable` 错误。

这跟 iOS/Android 的隐私权限模型是一个思路——操作系统要求摄像头/麦克风访问时应用必须可见（防止后台偷拍/偷录）。这是操作系统级的隐私保护，应用无法绕过。

### 权限矩阵——为什么需要平台级授权？

节点工具需要平台级权限：

| 工具 | iOS | Android | macOS |
|------|-----|---------|-------|
| 摄像头 | Camera 权限 | Camera 权限 | Camera 权限 |
| 麦克风 | Microphone 权限 | Microphone 权限 | Microphone 权限 |
| 位置 | Location 权限 | Location 权限 | Location 权限 |
| 屏幕录制 | Screen Recording 权限 | Screen Recording 权限 | Screen Recording 权限 |

这跟 Kubernetes RBAC 的权限矩阵是一个思路——每个操作需要特定的角色权限，权限缺失返回明确的错误码（如 `permission_denied_camera`）。

### 配对 vs 审批——为什么是三道安全门？

节点安全有三道独立的门：

1. **配对信任**（Pairing trust）：设备与网关的硬件连接信任
2. **网关命令策略**（Gateway command policy）：网关级的工具授权
3. **本地 shell 执行权限**（Local shell exec privilege）：本地操作系统的权限

这跟 SSH 的三道门是一个思路——网络可达（防火墙）→ SSH 认证（密钥/密码）→ sudo 权限（本地命令执行）。三道门独立，每道门可以单独诊断和修复。

### 常见错误码——为什么返回结构化错误？

节点返回结构化错误码（如 `background_unavailable`、`permission_denied_camera`、`pairing_expired`），而非模糊的错误消息。

这跟 HTTP 状态码的设计是一个思路——200/401/403/404/500 各有明确含义，客户端可以根据状态码自动处理（如 401 触发重新认证）。结构化错误码让自动化故障排查成为可能。

### 快速恢复循环——为什么是三步而非一步？

快速恢复循环是三步：

1. 运行诊断命令（识别问题）
2. 重新授权硬件（修复权限问题）
3. 重新打开应用（修复后台/状态问题）

这跟 IT helpdesk 的标准流程是一个思路——先诊断（不是直接重启），再针对性修复（不是盲目尝试），最后验证（确保问题解决）。

---

Troubleshoot node pairing, foreground requirements, permissions, and tool failures when connected hardware shows as active but specific tools refuse to work.

当连接的硬件显示为活跃但特定工具拒绝工作时，排查节点配对、前台要求、权限和工具故障。

The diagnostic command ladder verifies system → gateway → device health. Foreground requirements apply to camera and microphone tools (must be visible, not backgrounded). The permissions matrix maps tools to platform-level authorizations (iOS/Android/macOS) with specific error codes for missing privileges.

诊断命令阶梯验证系统 → 网关 → 设备健康。前台要求适用于摄像头和麦克风工具（必须可见，不能后台）。权限矩阵映射工具到平台级授权（iOS/Android/macOS），权限缺失返回特定错误码。

Three security gates operate independently: pairing trust (hardware connection), gateway command policy (tool authorization), and local shell exec privilege (OS permissions). Structured error codes (like `background_unavailable`, `permission_denied_camera`) enable automated troubleshooting. The fast recovery loop runs diagnostics, re-authorizes hardware, and reopens the app.

三道安全门独立运作：配对信任（硬件连接）、网关命令策略（工具授权）、本地 shell 执行权限（操作系统权限）。结构化错误码（如 `background_unavailable`、`permission_denied_camera`）支持自动化故障排查。快速恢复循环运行诊断、重新授权硬件、重新打开应用。
