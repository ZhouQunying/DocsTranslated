# Sandbox vs tool policy vs elevated

## 架构精读

> 跳过不影响阅读翻译正文。

### 三个相关但不同的控制

**问题**: Sandbox、tool policy、elevated 有什么区别?

**方案**: 三个控制:
1. **Sandbox** (`agents.defaults.sandbox.*`): **在哪里运行** (sandbox backend vs host)
2. **Tool policy** (`tools.*`): **哪些工具可用/允许**
3. **Elevated** (`tools.elevated.*`): **exec-only escape hatch**,在沙箱外运行

**洞察**: 三个控制分别控制: 运行位置、工具可用性、exec 特权。

**权衡**:
- ✓ 分离: 三个控制独立,不混淆
- ✗ 复杂: 需要理解三个控制的区别

### Quick debug

**问题**: 如何调试 sandbox 和 tool policy?

**方案**: `openclaw sandbox explain`:
```bash
openclaw sandbox explain
openclaw sandbox explain --session agent:main:main
openclaw sandbox explain --agent work
openclaw sandbox explain --json
```

输出:
- Effective sandbox mode/scope/workspace access
- Session 是否被 sandboxed (main vs non-main)
- Effective sandbox tool allow/deny
- Elevated gates 和 fix-it key paths

**洞察**: 查看 OpenClaw **实际**在做什么。

**权衡**:
- ✓ 透明: 看到实际配置
- ✓ 诊断: 快速定位问题

### Sandbox: where tools run

**问题**: 工具在哪里运行 (host vs sandbox)?

**方案**: `agents.defaults.sandbox.mode`:
- `"off"`: 所有工具在 host 运行
- `"non-main"`: 只有 non-main sessions 被 sandboxed
- `"all"`: 所有工具在 sandbox 运行

**洞察**: `"non-main"` 模式下,group/channel keys 不是 main,会被 sandboxed。

**权衡**:
- ✓ Off: 简单,无 sandbox 开销
- ✓ Non-main: 只 sandbox 不信任的 session
- ✓ All: 最安全,所有工具都在 sandbox

### Bind mounts

**问题**: Bind mounts 如何影响 sandbox 安全?

**方案**: `docker.binds` **pierces** sandbox filesystem:
- 挂载的内容在 container 内可见
- 默认 read-write,建议 `:ro` for source/secrets
- `scope: "shared"` 忽略 per-agent binds
- OpenClaw 验证 bind sources 两次 (normalized path + resolved path)
- 绑定 `/var/run/docker.sock` 等于把 host 控制权交给 sandbox

**洞察**: Bind mounts 是安全关键点,需要谨慎配置。

**权衡**:
- ✓ 灵活: 可以挂载 host 目录
- ✗ 风险: 可能泄露敏感文件

### Tool policy: which tools exist/are callable

**问题**: 哪些工具可用/允许?

**方案**: 多层:
- **Tool profile**: `tools.profile` (base allowlist)
- **Provider tool profile**: `tools.byProvider[provider].profile`
- **Global/per-agent tool policy**: `tools.allow`/`tools.deny`
- **Provider tool policy**: `tools.byProvider[provider].allow/deny`
- **Sandbox tool policy**: `tools.sandbox.tools.allow/deny` (只适用于 sandboxed)

**规则**:
- `deny` 总是赢
- 如果 `allow` 非空,其他都被视为 blocked
- Tool policy 是硬限制: `/exec` 不能 override denied `exec` tool
- Tool policy 按名字过滤,不检查 `exec` 内的副作用

**洞察**: Tool policy 是工具可用性的硬限制。

**权衡**:
- ✓ 安全: deny 总是赢
- ✗ 复杂: 多层 policy 需要理解优先级

### Tool groups

**问题**: 如何批量管理工具?

**方案**: Tool groups (shorthands):
```json5
{
  tools: {
    sandbox: {
      tools: {
        allow: ["group:runtime", "group:fs", "group:sessions", "group:memory"]
      }
    }
  }
}
```

可用 groups:
- `group:runtime`: `exec`, `process`, `code_execution`
- `group:fs`: `read`, `write`, `edit`, `apply_patch`
- `group:sessions`: `sessions_list`, `sessions_history`, `sessions_send`
- `group:memory`: `memory_search`, `memory_get`
- `group:web`: `web_search`, `x_search`, `web_fetch`
- `group:ui`: `browser`, `canvas`
- `group:automation`: `heartbeat_respond`, `cron`, `gateway`
- `group:messaging`: `message`
- `group:nodes`: `nodes`
- `group:agents`: `agents_list`, `update_plan`
- `group:media`: `image`, `image_generate`, `music_generate`, `video_generate`, `tts`
- `group:openclaw`: 所有内置 OpenClaw 工具
- `group:plugins`: 所有加载的 plugin-owned 工具

**洞察**: 用 group 批量管理,而不是逐个列出工具。

**权衡**:
- ✓ 简单: 一个 group 包含多个工具
- ✓ 灵活: 可以组合多个 group

### Elevated: exec-only "run on host"

**问题**: 如何在 sandboxed 模式下在 host 运行 exec?

**方案**: **Elevated**——exec-only escape hatch:
- `/elevated on` 或 `exec` with `elevated: true`: 在 sandbox 外运行
- `/elevated full`: 跳过 exec approvals
- 如果已经是 direct,elevated 是 no-op
- Elevated **不授予额外工具**,只影响 `exec`
- Elevated **不 override tool allow/deny**

**洞察**: Elevated 只影响 exec,不授予额外权限。

**权衡**:
- ✓ 灵活: 可以在 sandbox 外运行 exec
- ✗ 限制: 只影响 exec,不影响其他工具

**Gates**:
- Enablement: `tools.elevated.enabled`
- Sender allowlists: `tools.elevated.allowFrom.<provider>`

### Common "sandbox jail" fixes

**问题**: "Tool X blocked by sandbox tool policy" 如何修复?

**方案**: Fix-it keys:
- 禁用 sandbox: `agents.defaults.sandbox.mode=off`
- 在 sandbox 内允许工具: 从 `tools.sandbox.tools.deny` 移除,或添加到 `tools.sandbox.tools.allow`
- 检查 `openclaw logs` 的 `agents/tool-policy` entry

**问题**: "I thought this was main, why is it sandboxed?"

**方案**: `"non-main"` 模式下,group/channel keys 不是 main。使用 main session key,或 switch mode to `"off"`。

**洞察**: 常见错误: 以为 session 是 main,实际上是 non-main。

**权衡**:
- ✓ 修复: 可以修复 sandbox jail
- ✗ 复杂: 需要理解 sandbox mode 和 session key
