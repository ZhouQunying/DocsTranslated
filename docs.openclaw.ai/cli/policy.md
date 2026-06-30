# `openclaw policy`

## 架构精读

> 跳过不影响阅读翻译正文。

### 策略管理——为什么需要专门的命令？

`openclaw policy` 管理安全策略（工具权限、访问控制）：

- **`policy get`**：查看当前策略
- **`policy set <key> <value>`**：修改策略
- **`policy reset`**：恢复默认策略

这跟 AWS IAM 权限策略是一个思路——查看/修改/重置权限策略。策略决定"谁能做什么"（如"WhatsApp 通道只能发消息，不能执行命令"）。

### 策略层级——为什么有多层？

策略有多层（从宽松到严格）：

1. **全局策略**：所有通道和智能体共享
2. **通道策略**：特定通道的覆盖
3. **智能体策略**：特定智能体的覆盖

这跟 CSS 层叠是一个思路——全局样式 → 组件样式 → 内联样式，越具体优先级越高。多层策略让"全局宽松 + 特定严格"成为可能。

---

Manages security policies (tool permissions, access control): `policy get` (view current), `policy set <key> <value>` (modify), `policy reset` (restore defaults). Multi-layer policies: global → channel → agent (more specific = higher priority, like CSS cascade).

管理安全策略（工具权限、访问控制）：`policy get`（查看当前）、`policy set <key> <value>`（修改）、`policy reset`（恢复默认）。多层策略：全局 → 通道 → 智能体（越具体优先级越高，类似 CSS 层叠）。
