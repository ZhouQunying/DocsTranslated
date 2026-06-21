# Sandbox vs tool policy vs elevated

## 架构精读

> 跳过不影响阅读翻译正文。

### 三个相关但不同的控制

**问题**: 沙箱、工具策略、elevated 有什么区别?

**方案**: 三个控制:
1. **沙箱** (`agents.defaults.sandbox.*`): **在哪里运行** (沙箱后端 vs 宿主机)
2. **工具策略** (`tools.*`): **哪些工具可用/允许**
3. **Elevated** (`tools.elevated.*`): **仅执行应急出口**,在沙箱外运行

**洞察**: 三个控制分别控制: 运行位置、工具可用性、执行特权。

**权衡**:
- ✓ 分离: 三个控制独立,不混淆
- ✗ 复杂: 需要理解三个控制的区别

### Quick debug

**问题**: 如何调试沙箱和工具策略?

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

**问题**: 工具在哪里运行 (宿主机 vs 沙箱)?

**方案**: `agents.defaults.sandbox.mode`:
- `"off"`: 所有工具在宿主机运行
- `"non-main"`: 只有 non-main 会话被沙箱化
- `"all"`: 所有工具在沙箱运行

**洞察**: `"non-main"` 模式下,组/频道密钥不是 main,会被沙箱化。

**权衡**:
- ✓ Off: 简单,无沙箱开销
- ✓ Non-main: 只沙箱化不信任的会话
- ✓ All: 最安全,所有工具都在沙箱

### Bind mounts

**问题**: Bind mounts 如何影响沙箱安全?

**方案**: `docker.binds` **穿透**沙箱文件系统:
- 挂载的内容在容器内可见
- 默认 read-write,建议 `:ro` for source/secrets
- `scope: "shared"` 忽略 per-agent 挂载
- OpenClaw 验证 bind sources 两次 (normalized path + resolved path)
- 绑定 `/var/run/docker.sock` 等于把宿主机控制权交给沙箱

**洞察**: Bind mounts 是安全关键点,需要谨慎配置。

**权衡**:
- ✓ 灵活: 可以挂载宿主机目录
- ✗ 风险: 可能泄露敏感文件

### Tool policy: which tools exist/are callable

**问题**: 哪些工具可用/允许?

**方案**: 多层:
- **Tool profile**: `tools.profile` (base allowlist)
- **Provider tool profile**: `tools.byProvider[provider].profile`
- **Global/per-agent tool policy**: `tools.allow`/`tools.deny`
- **Provider tool policy**: `tools.byProvider[provider].allow/deny`
- **Sandbox tool policy**: `tools.sandbox.tools.allow/deny` (只适用于被沙箱化的)

**规则**:
- `deny` 总是赢
- 如果 `allow` 非空,其他都被视为被阻止
- 工具策略是硬限制: `/exec` 不能覆盖被拒绝的 `exec` 工具
- 工具策略按名字过滤,不检查 `exec` 内的副作用

**洞察**: 工具策略是工具可用性的硬限制。

**权衡**:
- ✓ 安全: deny 总是赢
- ✗ 复杂: 多层策略需要理解优先级

### Tool groups

**问题**: 如何批量管理工具?

**方案**: 工具组(简写):
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

**洞察**: 用工具组批量管理,而不是逐个列出工具。

**权衡**:
- ✓ 简单: 一个工具组包含多个工具
- ✓ 灵活: 可以组合多个工具组

### Elevated: exec-only "run on host"

**问题**: 如何在被沙箱化的模式下在宿主机运行执行?

**方案**: **Elevated**——仅执行应急出口:
- `/elevated on` 或 `exec` with `elevated: true`: 在沙箱外运行
- `/elevated full`: 跳过执行审批
- 如果已经是直连,elevated 是空操作
- Elevated **不授予额外工具**,只影响 `exec`
- Elevated **不覆盖工具的允许/拒绝**

**洞察**: Elevated 只影响执行,不授予额外权限。

**权衡**:
- ✓ 灵活: 可以在沙箱外运行执行
- ✗ 限制: 只影响执行,不影响其他工具

**Gates**:
- Enablement: `tools.elevated.enabled`
- Sender allowlists: `tools.elevated.allowFrom.<provider>`

### 常见"沙箱监牢"修复

**问题**: "工具 X 被沙箱工具策略阻止" 如何修复?

**方案**: Fix-it keys:
- 禁用沙箱: `agents.defaults.sandbox.mode=off`
- 在沙箱内允许工具: 从 `tools.sandbox.tools.deny` 移除,或添加到 `tools.sandbox.tools.allow`
- 检查 `openclaw logs` 的 `agents/tool-policy` 条目

**问题**: "我以为这是 main,为什么它被沙箱化了?"

**方案**: `"non-main"` 模式下,组/频道密钥不是 main。使用主会话密钥,或将模式切换为 `"off"`。

**洞察**: 常见错误: 以为会话是 main,实际上是 non-main。

**权衡**:
- ✓ 修复: 可以修复沙箱监牢
- ✗ 复杂: 需要理解沙箱模式和会话密钥
