# Troubleshooting Nodes

如果系统显示已连接的 node,但相关 tools 故障,请查阅此指南。

> **类比:K8s 的 kubectl describe + logs。** K8s 里 pod 出问题时,先用 `kubectl describe` 看状态,再用 `kubectl logs` 看日志。OpenClaw node troubleshooting 类似: 先用 `openclaw nodes describe` 看 capabilities,再用 `openclaw logs --follow` 看实时日志,最后用 `openclaw approvals get` 看执行权限。区别: K8s pod 是容器,OpenClaw node 是设备,需要区分 pairing、command policy、exec approvals 三层。
>
> **架构要点:** 诊断顺序: `status` → `gateway status` → `logs` → `doctor` → `channels status` → `nodes status` → `nodes describe` → `approvals get`;canvas/camera/screen 需要 node **foreground**,后台返回 `NODE_BACKGROUND_UNAVAILABLE`;三层安全检查: device pairing (连接) → gateway command policy (RPC 允许) → exec approvals (本地 shell 执行);pairing 建立身份和信任,不是控制 individual approvals;system exec approvals 在特定 node 的 approval 文件中,与 gateway 的 pairing record 分离。

## 诊断命令序列

```bash
openclaw status
openclaw gateway status
openclaw logs --follow
openclaw doctor
openclaw channels status --probe
```

然后针对 node 进行检查:

```bash
openclaw nodes status
openclaw nodes describe --node <idOrNameOrIp>
openclaw approvals get --node <idOrNameOrIp>
```

健康状态的指标包括:

- 设备已链接并在 "node" role 下配对
- Description 输出包含你的目标 capability
- 执行 approvals 显示正确的 allowlist 或 mode

## Foreground 执行需求

Canvas、camera、screen 操作等 tools 需要应用在移动平台上处于前台活跃状态。

快速诊断和解决:

```bash
openclaw nodes describe --node <idOrNameOrIp>
openclaw nodes canvas snapshot --node <idOrNameOrIp>
openclaw logs --follow
```

如果日志显示 "NODE_BACKGROUND_UNAVAILABLE",只需在设备上打开应用并重试操作。

## 权限表

| 功能 | iOS | Android | macOS | 错误码 |
| --- | --- | --- | --- | --- |
| `camera.snap`、`camera.clip` | Camera (clips 需要 mic) | Camera (clips 需要 mic) | Camera (clips 需要 mic) | `*_PERMISSION_REQUIRED` |
| `screen.record` | Screen Recording (mic 可选) | Screen capture 提示 (mic 可选) | Screen Recording | `*_PERMISSION_REQUIRED` |
| `location.get` | While Using 或 Always | 基于 mode 的 Foreground/Background | Location 权限 | `LOCATION_PERMISSION_REQUIRED` |
| `system.run` | n/a (host path) | n/a (host path) | 需要 Exec approvals | `SYSTEM_RUN_DENIED` |

## 区分 Pairing 和 Approvals

这些代表不同的安全检查点:

1. **Device pairing**: Gateway 是否接受 node 的连接
2. **Gateway command policy**: RPC command 是否被平台默认值和 allow/deny lists 允许
3. **Exec approvals**: Node 是否能执行特定的本地 shell 命令

运行这些快速验证:

```bash
openclaw devices list
openclaw nodes status
openclaw approvals get --node <idOrNameOrIp>
openclaw approvals allowlist add --node <idOrNameOrIp> "/usr/bin/uname"
```

如果设备未配对,先授权它。如果 command 在 description 中缺失,验证 gateway 的 command policy 并确保 node 在连接时声明了它。如果配对正常但执行失败,调整本地执行 approvals。

Pairing 建立身份和信任,不是控制 individual approvals。对于系统执行,policies 在特定 node 的 approval 文件中,与 gateway 的 pairing record 分离。

运行批准的 host=node 任务时,gateway 把执行绑定到原始计划。如果任何 caller 在之前变更 command、目录或元数据,系统会拒绝它作为不匹配,而不是处理修改后的 payload。

## 常见 Node 错误标识符

- `NODE_BACKGROUND_UNAVAILABLE`: 应用被最小化;打开它
- `CAMERA_DISABLED`: Camera toggle 在设置中关闭
- `*_PERMISSION_REQUIRED`: OS 权限被拒绝或缺失
- `LOCATION_DISABLED`: Location services 被停用
- `LOCATION_PERMISSION_REQUIRED`: 请求的特定 location mode 未被授予
- `LOCATION_BACKGROUND_UNAVAILABLE`: 应用被最小化,但只授予了 foreground location 访问
- `SYSTEM_RUN_DENIED: approval required`: 执行请求缺少显式授权
- `SYSTEM_RUN_DENIED: allowlist miss`: Command 被当前 allowlist 配置阻止。Windows hosts 上,wrapper commands 如 "cmd.exe /c ..." 触发此错误,除非交互式批准

## 快速恢复流程

```bash
openclaw nodes status
openclaw nodes describe --node <idOrNameOrIp>
openclaw approvals get --node <idOrNameOrIp>
openclaw logs --follow
```

如果问题持续,尝试以下步骤:

- 重新授权 device pairing
- 在 foreground 启动 node 应用
- 重新授权 OS 权限
- 修改或重建执行 approval 规则

## 其他资源

- [Overview of Nodes](/nodes)
- [Camera Nodes](/nodes/camera)
- [Location Commands](/nodes/location-command)
- [Execution Approvals](/tools/exec-approvals)
- [Gateway Pairing](/gateway/pairing)
- [Gateway Troubleshooting](/gateway/troubleshooting)
- [Channel Troubleshooting](/channels/troubleshooting)
