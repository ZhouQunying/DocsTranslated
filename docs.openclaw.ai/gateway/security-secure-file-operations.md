# Secure File Operations——安全文件操作

## 架构精读

> 跳过不影响阅读翻译正文。

### 库防护 vs 沙箱——为什么不是完整沙箱？

Secure file operations 是库级别的防护，不是操作系统级沙箱。库防护在代码层面限制文件操作（路径检查、权限验证），沙箱在 OS 层面隔离进程（Docker、chroot）。

这跟 JavaScript 的 Promise 校验 vs Web Worker 隔离是一个思路——Promise 在代码层面校验输入，Worker 在浏览器层面隔离执行。库只能限制"用这个库的代码"，直接调用系统 API 则管不了。对抗本地恶意用户需要独立的 OS 账户或容器。

### 根目录限定读取——为什么把绝对路径当相对路径？

代理可能请求 `/etc/passwd` 或 `../../etc/passwd` 做路径遍历。解决方案是把所有路径当相对路径（相对于安全根目录），`/etc/passwd` 被解释为 `~/.openclaw/workspace/etc/passwd`（不存在）。

这跟 Web 服务器文档根目录是一个思路——请求 `/etc/passwd` 被解析为文档根目录下的文件，无法访问根目录外。安全根目录 + 路径归一化 = 防止路径遍历。

### 原子替换——为什么用 rename 而不是直接写？

文件替换过程中系统崩溃，直接写入可能导致文件损坏（写了一半）。原子替换先写临时文件，再用 `rename` syscall 原子性替换原文件。

这跟数据库事务是一个思路——要么完全提交，要么完全回滚，没有中间状态。`rename` 在 POSIX 上是原子操作，失败时原文件不受影响。

### Python helper 的 fd-relative 操作——为什么需要持久进程？

可选的 POSIX Python helper 维护一个持久进程，执行 fd-relative 操作（如 rename、mkdir）。这减少了竞态条件漏洞——另一个进程可能在操作过程中替换父目录。

这跟数据库连接池是一个思路——保持连接不关闭，避免每次操作都重新建立连接。helper 通过文件描述符相对操作，不受路径名变化影响。默认关闭 helper，因为大多数场景不需要。

### 归档解压安全——为什么需要限制大小和数量？

恶意归档可能包含 `../../etc/passwd`（路径遍历）或压缩炸弹（解压后 TB 级）。安全解压需要三层防护：路径检查防止遍历、大小限制防止炸弹、文件数量限制防止 inode 耗尽。

这跟邮件附件扫描是一个思路——检查附件路径、大小、文件数量，防止恶意附件。归档解压 = 信任边界入口，必须验证。

---

### 概述 / Overview

OpenClaw relies on a specific package for handling sensitive local file tasks like reading, writing, and extracting archives. This acts as a "library guardrail" for processing untrusted paths, though it isn't a full sandbox since OS permissions and containers dictate the actual security boundaries.

OpenClaw 依赖专用库处理敏感本地文件操作（读取、写入、归档解压）。这是处理不可信路径的"库级防护栏"，但不是完整沙箱——OS 权限和容器才是实际的安全边界。

### 默认：无 Python helper / Default: No Python Helper

The system disables the POSIX Python helper by default. This prevents the gateway from launching an unrequested sidecar, avoids unnecessary hardening for most setups, and ensures consistent behavior across various environments. Users can override this using environment variables:

系统默认禁用 POSIX Python helper。防止网关启动未请求的 sidecar，避免大多数场景的不必要加固，确保跨环境行为一致。用户可通过环境变量覆盖：

```bash
# Fallback to Node only
OPENCLAW_FS_SAFE_PYTHON_MODE=off
# Allow helper if present
OPENCLAW_FS_SAFE_PYTHON_MODE=auto
# Mandate the helper
OPENCLAW_FS_SAFE_PYTHON_MODE=require
# Set specific binary
OPENCLAW_FS_SAFE_PYTHON=/usr/bin/python3
```

Generic variable names are also supported.

也支持通用变量名。

### 无 Python 时的保护 / What Stays Protected Without Python

Even without the helper, the Node paths enforce several safeguards:

即使没有 helper，Node 路径也执行多项保护：

- Blocking "relative-path escapes" and unauthorized absolute paths.
- Using a trusted root handle for resolutions.
- Denying specific symlink and hardlink configurations.
- Performing identity checks on file contents.
- Executing "atomic sibling-temp writes" for configurations.
- Enforcing byte limits and private modes for sensitive data.

- 阻止"相对路径逃逸"和未授权的绝对路径。
- 使用可信根句柄做路径解析。
- 拒绝特定的 symlink 和 hardlink 配置。
- 对文件内容做身份检查。
- 配置写入使用"原子 sibling-temp write"。
- 对敏感数据强制字节限制和私有模式。

These measures adequately address the standard threat model of trusted code processing untrusted inputs.

这些措施足以应对标准威胁模型——可信代码处理不可信输入。

### Python helper 增加的能力 / What Python Adds

For POSIX systems, the optional helper maintains a persistent process to perform fd-relative operations like renaming or making directories. This reduces race condition vulnerabilities where another process might alter a parent directory mid-operation. If your environment faces this risk, enable the strict mode:

对 POSIX 系统，可选 helper 维护持久进程执行 fd-relative 操作（rename、mkdir）。减少竞态条件漏洞——另一个进程可能在操作过程中替换父目录。如果环境面临此风险，启用严格模式：

```bash
OPENCLAW_FS_SAFE_PYTHON_MODE=require
```

Choose strict mode over automatic fallback when this helper is critical to your security strategy.

当 helper 对安全策略至关重要时，选严格模式而非自动回退。

### 插件和核心操作指南 / Plugin and Core Guidance

- Plugins must use designated SDK helpers rather than raw filesystem calls when handling external inputs.
- Core operations should utilize local wrappers to maintain consistent policies.
- Archive extraction requires explicit limits on size, entries, and links.
- Sensitive data must use dedicated secret helpers instead of manual permission checks.
- For isolation against hostile local users, employ separate OS accounts or sandboxing rather than relying solely on this library.

- 插件处理外部输入时必须用指定 SDK helper，不能用原始文件系统调用。
- 核心操作应使用本地 wrapper 保持一致策略。
- 归档解压需要显式限制大小、条目数和链接数。
- 敏感数据必须用专用 secret helper，不能手动检查权限。
- 对抗本地恶意用户的隔离，用独立 OS 账户或沙箱，不能只靠这个库。

See also: Security, Sandboxing, Exec approvals, and Secrets.

另见：Security、Sandboxing、Exec approvals、Secrets。
