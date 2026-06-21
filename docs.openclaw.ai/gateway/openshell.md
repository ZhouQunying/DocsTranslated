# OpenShell

## 架构精读

> 跳过不影响阅读翻译正文。

### OpenShell backend

**问题**: 本地运行 Docker container 资源消耗大,或需要远程沙箱?

**方案**: **OpenShell**——managed sandbox backend:
- OpenClaw 把沙箱生命周期委托给 `openshell` CLI
- 在远程环境创建,通过 SSH 执行命令
- 复用 SSH 传输和远程文件系统 bridge

**洞察**: 不是本地 Docker,而是远程 SSH 沙箱。

**权衡**:
- ✓ 轻量: 不需要本地 Docker
- ✓ 远程: 可以在远程环境执行
- ✗ 依赖: 需要 OpenShell 账户和 CLI

### Workspace modes

**问题**: 本地 workspace 和远程 workspace 如何同步?

**方案**: 两种模式:
- **`mirror`**: 双向同步,每次 exec 前后 sync
- **`remote`**: 一次性初始化,之后直接操作远程

**洞察**: 选择哪个 workspace 是"权威来源"。

**权衡**:
- ✓ Mirror: 本地编辑可见,类似 Docker backend
- ✗ Mirror: 每次 exec 有 sync 开销
- ✓ Remote: 低 sync 开销,适合长时间运行的 agent
- ✗ Remote: 本地编辑不可见,直到 recreate

| | Mirror | Remote |
|---|---|---|
| **Canonical workspace** | Local host | Remote OpenShell |
| **Sync direction** | Bidirectional | One-time 初始化 |
| **Per-turn overhead** | Higher | Lower |
| **Local edits visible?** | Yes | No, until recreate |
| **Best for** | Development | Long-running agents, CI |

### Configuration

**问题**: 如何配置 OpenShell?

**方案**: `plugins.entries.openshell.config`:
```json5
{
  agents: {
    defaults: {
      sandbox: {
        mode: "all",
        backend: "openshell",
        scope: "session",
        workspaceAccess: "rw"
      }
    }
  },
  plugins: {
    entries: {
      openshell: {
        enabled: true,
        config: {
          from: "openclaw",
          mode: "remote"
        }
      }
    }
  }
}
```

**洞察**: 配置 sandbox backend 为 openshell,选择 workspace mode,配置作用域和 workspaceAccess。

**权衡**:
- ✓ 灵活: 可以配置 mode、作用域、workspaceAccess
- ✗ 复杂: 需要配置多个字段

### Lifecycle management

**问题**: 如何管理 OpenShell 沙箱的生命周期?

**方案**: 通过 sandbox CLI:
```bash
openclaw sandbox list
openclaw sandbox explain
openclaw sandbox recreate --all
```

**洞察**: `recreate` 删除远程 workspace,下次使用时重新初始化。

**权衡**:
- ✓ 管理: 可以 list、explain、recreate
- ✗ 风险: recreate 会删除远程 workspace

**何时 recreate**:
- 修改 `agents.defaults.sandbox.backend`
- 修改 `plugins.entries.openshell.config.from`
- 修改 `plugins.entries.openshell.config.mode`
- 修改 `plugins.entries.openshell.config.policy`

### Security hardening

**问题**: Symlink 替换或 remounted workspace 可能重定向读取?

**方案**: OpenShell pins workspace 根文件描述符,每次 read 前 recheck sandbox 身份。

**洞察**: 防止 symlink 替换或 remount 导致 reads 被重定向到意外的位置。

**权衡**:
- ✓ 安全: 防止 symlink 替换攻击
- ✓ 可靠: 每次 read 前验证

### Current limitations

**问题**: OpenShell backend 有哪些限制?

**方案**: 已知限制:
- ✗ Sandbox browser 不支持
- ✗ `sandbox.docker.binds` 不适用
- ✗ Docker-specific runtime knobs 只适用于 Docker backend

**洞察**: OpenShell 是 SSH backend,不是 Docker backend,某些 Docker 功能不适用。

**权衡**:
- ✓ 远程: 可以在远程环境执行
- ✗ 限制: 某些 Docker 功能不支持
