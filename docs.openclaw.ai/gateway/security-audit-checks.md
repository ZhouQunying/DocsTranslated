# Audit Checks——安全审计检查项

## 架构精读

> 跳过不影响阅读翻译正文。

### 结构化审计发现——为什么不是纯文本输出？

`openclaw security audit` 输出结构化数据（检查 ID + 严重程度 + 描述 + 修复建议），不是纯文本日志。这跟 JUnit 测试报告是一个思路——结构化格式可以被 CI/CD 处理、聚合、比较。纯文本只能给人看，结构化数据可以给机器处理。

### 检查 ID——为什么需要唯一标识？

每个检查项有唯一 ID（如 `auth-no-authentication`、`network-public-exposure`），可以针对性配置例外或跟踪修复进度。这跟 ESLint rule ID 是一个思路——可以 `eslint-disable-next-line no-unused-vars` 忽略特定规则。没有 ID 就只能全局开关，有了 ID 可以精细控制。

### CI/CD 集成——怎么阻止不安全配置上线？

审计输出 JSON，CI/CD 可以解析并阻止部署。严重问题直接 exit 1，阻止上线。这跟单元测试集成 CI/CD 是一个思路——测试失败就阻止部署。

### 审计的局限性——为什么不是万能？

审计只能检测已知问题，可能误报也可能漏报。它是辅助工具，需要配合渗透测试、代码审查等其他安全措施。这跟烟雾报警器是一个思路——能检测火灾，不能检测煤气泄漏。

---

### 概述 / Overview

The system generates structured alerts identified by specific codes during security evaluations. This document serves as a directory for those identifiers. For broader threat modeling and hardening advice, refer to the main security documentation.

系统在安全评估期间生成带特定代码的结构化告警。本文档是这些标识符的目录。更广泛的威胁建模和加固建议参考主安全文档。

Below are common identifiers found in production environments.

以下是生产环境中常见的标识符。

| Identifier | Impact | Rationale | Resolution Target | Automated |
|---|---|---|---|---|
| State folder globally writable | Critical | Anyone alters application data | Home folder permissions | Yes |
| State folder group writable | Warning | Group members alter application data | Home folder permissions | Yes |
| State folder readable | Warning | Outsiders view application data | Home folder permissions | Yes |
| State folder symlinked | Warning | Shifts trust boundaries | Layout adjustments | No |
| Configuration writable | Critical | Unauthorized policy modifications | Settings file permissions | Yes |
| Configuration symlinked | Warning | Unsupported write targets | Use standard files | No |
| Configuration group readable | Warning | Group members view tokens | Settings file permissions | Yes |
| Configuration globally readable | Critical | Token exposure risks | Settings file permissions | Yes |
| Included file writable | Critical | Unauthorized include edits | Include file permissions | Yes |
| Included file group readable | Warning | Group views included secrets | Include file permissions | Yes |
| Included file globally readable | Critical | Exposed included secrets | Include file permissions | Yes |
| Auth profiles writable | Critical | Credential injection risks | Profile permissions | Yes |
| Auth profiles readable | Warning | Credential viewing risks | Profile permissions | Yes |
| Credentials folder writable | Critical | Pairing state alterations | Credential permissions | Yes |
| Credentials folder readable | Warning | Credential state viewing | Credential permissions | Yes |
| Sessions readable | Warning | Transcript viewing risks | Session store permissions | Yes |
| Log file readable | Warning | Sensitive log viewing | Log file permissions | Yes |
| Synced directory used | Warning | Cloud sync exposure risks | Move away from sync | No |
| Bind lacking authentication | Critical | Unauthenticated remote binds | Bind and auth settings | No |
| Loopback lacking authentication | Critical | Unauthenticated proxy loopbacks | Auth and proxy setup | No |
| Missing trusted proxies | Warning | Untrusted proxy headers | Trusted proxy list | No |
| HTTP lacking authentication | Warn/Crit | Unauthenticated HTTP APIs | Auth mode and endpoints | No |
| Session key override active | Info | Callers override session keys | Allow override setting | No |
| Dangerous tools allowed | Warn/Crit | Risky tools enabled via HTTP | Tool allowlist | No |
| Dangerous node commands | Warn/Crit | High-impact commands enabled | Node command allowlist | No |
| Ineffective deny commands | Warning | Deny patterns fail | Node command denylist | No |
| Tailscale funnel active | Critical | Exposes system to internet | Tailscale mode | No |
| Tailscale serve active | Info | Tailnet exposure enabled | Tailscale mode | No |
| UI origins required | Critical | External UI lacks allowlist | UI allowed origins | No |
| UI wildcard origins | Warn/Crit | Wildcard disables allowlisting | UI allowed origins | No |
| UI host header fallback | Warn/Crit | DNS rebinding hardening lowered | UI fallback setting | No |
| UI insecure auth | Warning | Insecure auth toggle active | UI insecure auth setting | No |
| UI device auth disabled | Critical | Disables device verification | UI device auth setting | No |
| Real IP fallback active | Warn/Crit | IP spoofing via proxy | Real IP and proxy settings | No |
| Short token used | Warning | Brute force vulnerability | Auth token | No |
| No auth rate limit | Warning | Brute force risk increased | Auth rate limit | No |
| Trusted proxy auth | Critical | Proxy becomes auth boundary | Auth mode | No |
| No trusted proxies set | Critical | Unsafe proxy auth | Trusted proxy list | No |
| No user header set | Critical | Cannot resolve user identity | User header setting | No |
| No proxy allowlist | Warning | Accepts any upstream user | Allowed users list | No |
| Allow loopback proxy | Warning | Accepts loopback proxy sources | Allow loopback setting | No |
| SecretRef unavailable | Warning | Deep probe auth resolution failed | Auth source availability | No |
| Probe failed | Warn/Crit | Live probe unsuccessful | Reachability and auth | No |
| mDNS full mode | Warn/Crit | Metadata advertised locally | mDNS mode and bind | No |
| Insecure flags active | Warning | Debug flag active | Specific finding key | No |
| Suppressions active | Info | Output filtering applied | Suppression settings | No |
| Password in config | Warning | Password stored in plaintext | Auth password | No |
| Hooks token in config | Warning | Bearer token in plaintext | Hooks token | No |
| Hook token reuse | Critical | Hook token grants gateway access | Hook and auth tokens | No |
| Short hook token | Warning | Hook brute force risk | Hooks token | No |
| Default session unset | Warning | Fan-out generated sessions | Default session key | No |
| Unrestricted agent IDs | Warn/Crit | Callers route to any agent | Allowed agent IDs | No |
| Request session key | Warn/Crit | External caller chooses key | Allow request key | No |
| Missing key prefixes | Warn/Crit | No bounds on key shapes | Allowed key prefixes | No |
| Root hook path | Critical | Ingress collision risk | Hook path | No |
| Unpinned npm hooks | Warning | Mutable install records | Install metadata | No |
| Missing hook integrity | Warning | Lacks integrity checks | Install metadata | No |
| Hook version drift | Warning | Records mismatch packages | Install metadata | No |
| Redaction off | Warning | Sensitive data in logs | Redaction setting | Yes |
| Invalid browser config | Warning | Pre-runtime config error | Browser settings | No |
| Browser without auth | Critical | Unauthenticated browser control | Auth settings | No |
| Remote CDP HTTP | Warning | Unencrypted remote CDP | CDP URL | No |
| Private CDP host | Warning | Internal host targeted | CDP URL and SSRF policy | No |
| Docker config off | Warning | Inactive sandbox config | Sandbox mode | No |
| Non-absolute bind | Warning | Unpredictable relative mounts | Docker binds | No |
| Dangerous bind mount | Critical | Mounts restricted system paths | Docker binds | No |
| Dangerous network mode | Critical | Shares host network namespace | Docker network | No |
| Dangerous seccomp | Critical | Reduces container security | Security options | No |
| Dangerous AppArmor | Critical | Reduces container security | Security options | No |
| Unrestricted CDP bridge | Warning | Bridge lacks source limits | CDP source range | No |
| Non-loopback CDP publish | Critical | CDP published externally | Container publish config | No |
| Missing hash label | Warning | Container predates config hash | Recreate browser sandbox | No |
| Stale hash epoch | Warning | Container predates config epoch | Recreate browser sandbox | No |
| No sandbox defaults | Warning | Host sandbox fails closed | Exec host and sandbox mode | No |
| No sandbox agents | Warning | Agent sandbox fails closed | Agent exec and sandbox | No |
| Full security exec | Warn/Crit | Host exec runs fully | Exec security settings | No |
| FS disabled, exec enabled | Warning | Shell execution not read-only | Tool deny and workspace | No |
| Auto-allow skills | Warning | Implicit trust in skill bins | Host approvals | No |
| Allowlist without eval | Warning | Inline eval permitted | Strict inline eval | No |
| Unprofiled safe bins | Warning | Bins lack explicit profiles | Safe bins and profiles | No |
| Broad safe bins | Warning | Weakens low-risk trust model | Safe bins | No |
| Risky trusted dirs | Warning | Mutable directories included | Trusted directories | No |
| Symlink escape | Warning | Skills resolve outside root | Workspace filesystem | No |
| No plugin allowlist | Warning | Unrestricted plugin installs | Plugin allowlist | No |
| Unpinned npm plugins | Warning | Mutable plugin records | Install metadata | No |
| Missing plugin integrity | Warning | Lacks integrity checks | Install metadata | No |
| Plugin version drift | Warning | Records mismatch packages | Install metadata | No |
| Plugin code safety | Warn/Crit | Suspicious code patterns found | Plugin code source | No |
| Plugin entry path | Warning | Points to hidden locations | Plugin manifest entry | No |
| Plugin entry escape | Critical | Exits designated plugin folder | Plugin manifest entry | No |
| Plugin scan failed | Warning | Code scan incomplete | Scan environment | No |
| Skill code safety | Warn/Crit | Suspicious skill patterns | Skill install source | No |
| Skill scan failed | Warning | Skill scan incomplete | Scan environment | No |
| Open channels with exec | Warn/Crit | Public rooms reach exec agents | DM/group and exec policies | No |
| Open groups elevated | Critical | Prompt-injection via open groups | DM/group policies | No |
| Open groups runtime/fs | Crit/Warn | Open groups reach file tools | DM/group and tool policies | No |
| Multi-user heuristic | Warning | Personal model in multi-user setup | Trust boundaries | No |
| Minimal profile overridden | Warning | Bypasses global minimal profile | Agent tool profiles | No |
| Permissive plugin tools | Warning | Extension tools in permissive contexts | Tool profiles | No |
| Legacy models | Warning | Outdated model families used | Model selection | No |
| Weak tier models | Warning | Below recommended tiers | Model selection | No |
| Small model params | Crit/Info | Small models increase injection risk | Model and tool policies | No |
| Attack surface summary | Info | Overall posture roll-up | Multiple keys | No |

| 标识符 | 影响 | 原因 | 修复目标 | 自动修复 |
|---|---|---|---|---|
| State folder globally writable | 严重 | 任何人可修改应用数据 | Home 目录权限 | 是 |
| State folder group writable | 警告 | 组成员可修改应用数据 | Home 目录权限 | 是 |
| State folder readable | 警告 | 外部人员可查看应用数据 | Home 目录权限 | 是 |
| State folder symlinked | 警告 | 信任边界被转移 | 目录布局调整 | 否 |
| Configuration writable | 严重 | 未授权的策略修改 | 配置文件权限 | 是 |
| Configuration symlinked | 警告 | 不支持的写入目标 | 使用标准文件 | 否 |
| Configuration group readable | 警告 | 组成员可查看 token | 配置文件权限 | 是 |
| Configuration globally readable | 严重 | token 暴露风险 | 配置文件权限 | 是 |
| Included file writable | 严重 | 未授权的 include 编辑 | Include 文件权限 | 是 |
| Included file group readable | 警告 | 组可查看 include 中的密钥 | Include 文件权限 | 是 |
| Included file globally readable | 严重 | include 中的密钥暴露 | Include 文件权限 | 是 |
| Auth profiles writable | 严重 | 凭证注入风险 | Profile 权限 | 是 |
| Auth profiles readable | 警告 | 凭证查看风险 | Profile 权限 | 是 |
| Credentials folder writable | 严重 | 配对状态被篡改 | 凭证目录权限 | 是 |
| Credentials folder readable | 警告 | 凭证状态被查看 | 凭证目录权限 | 是 |
| Sessions readable | 警告 | 对话记录被查看 | Session 存储权限 | 是 |
| Log file readable | 警告 | 敏感日志被查看 | 日志文件权限 | 是 |
| Synced directory used | 警告 | 云同步暴露风险 | 移出同步目录 | 否 |
| Bind lacking authentication | 严重 | 远程绑定无认证 | 绑定和认证设置 | 否 |
| Loopback lacking authentication | 严重 | 代理回环无认证 | 认证和代理设置 | 否 |
| Missing trusted proxies | 警告 | 不受信的代理 header | 可信代理列表 | 否 |
| HTTP lacking authentication | 警告/严重 | HTTP API 无认证 | 认证模式和端点 | 否 |
| Session key override active | 信息 | 调用者可覆盖 session key | 允许覆盖设置 | 否 |
| Dangerous tools allowed | 警告/严重 | 危险工具通过 HTTP 启用 | 工具 allowlist | 否 |
| Dangerous node commands | 警告/严重 | 高影响命令被启用 | Node 命令 allowlist | 否 |
| Ineffective deny commands | 警告 | deny 模式无效 | Node 命令 denylist | 否 |
| Tailscale funnel active | 严重 | 系统暴露到公网 | Tailscale 模式 | 否 |
| Tailscale serve active | 信息 | Tailnet 暴露已启用 | Tailscale 模式 | 否 |
| UI origins required | 严重 | 外部 UI 缺少 allowlist | UI 允许来源 | 否 |
| UI wildcard origins | 警告/严重 | 通配符禁用了 allowlisting | UI 允许来源 | 否 |
| UI host header fallback | 警告/严重 | DNS 重绑定加固降低 | UI 回退设置 | 否 |
| UI insecure auth | 警告 | 不安全认证开关已启用 | UI 不安全认证设置 | 否 |
| UI device auth disabled | 严重 | 设备验证被禁用 | UI 设备认证设置 | 否 |
| Real IP fallback active | 警告/严重 | 代理 IP 伪造 | 真实 IP 和代理设置 | 否 |
| Short token used | 警告 | 暴力破解漏洞 | 认证 token | 否 |
| No auth rate limit | 警告 | 暴力破解风险增加 | 认证速率限制 | 否 |
| Trusted proxy auth | 严重 | 代理成为认证边界 | 认证模式 | 否 |
| No trusted proxies set | 严重 | 不安全的代理认证 | 可信代理列表 | 否 |
| No user header set | 严重 | 无法解析用户身份 | 用户 header 设置 | 否 |
| No proxy allowlist | 警告 | 接受任何上游用户 | 允许用户列表 | 否 |
| Allow loopback proxy | 警告 | 接受回环代理来源 | 允许回环设置 | 否 |
| SecretRef unavailable | 警告 | 深度探测认证解析失败 | 认证源可用性 | 否 |
| Probe failed | 警告/严重 | 实时探测失败 | 可达性和认证 | 否 |
| mDNS full mode | 警告/严重 | 元数据在本地广播 | mDNS 模式和绑定 | 否 |
| Insecure flags active | 警告 | 调试标志已启用 | 特定 finding key | 否 |
| Suppressions active | 信息 | 输出过滤已应用 | 抑制设置 | 否 |
| Password in config | 警告 | 明文存储密码 | 认证密码 | 否 |
| Hooks token in config | 警告 | 明文存储 Bearer token | Hooks token | 否 |
| Hook token reuse | 严重 | Hook token 可访问网关 | Hook 和认证 token | 否 |
| Short hook token | 警告 | Hook 暴力破解风险 | Hooks token | 否 |
| Default session unset | 警告 | 扇出生成 session | 默认 session key | 否 |
| Unrestricted agent IDs | 警告/严重 | 调用者可路由到任意 agent | 允许的 agent ID | 否 |
| Request session key | 警告/严重 | 外部调用者选择 key | 允许请求 key | 否 |
| Missing key prefixes | 警告/严重 | key 格式无边界限制 | 允许的 key 前缀 | 否 |
| Root hook path | 严重 | 入口冲突风险 | Hook 路径 | 否 |
| Unpinned npm hooks | 警告 | 可变的安装记录 | 安装元数据 | 否 |
| Missing hook integrity | 警告 | 缺少完整性检查 | 安装元数据 | 否 |
| Hook version drift | 警告 | 记录与包不匹配 | 安装元数据 | 否 |
| Redaction off | 警告 | 日志中含敏感数据 | 脱敏设置 | 是 |
| Invalid browser config | 警告 | 运行时前配置错误 | 浏览器设置 | 否 |
| Browser without auth | 严重 | 浏览器控制无认证 | 认证设置 | 否 |
| Remote CDP HTTP | 警告 | 未加密的远程 CDP | CDP URL | 否 |
| Private CDP host | 警告 | 指向内部主机 | CDP URL 和 SSRF 策略 | 否 |
| Docker config off | 警告 | 沙箱配置未激活 | 沙箱模式 | 否 |
| Non-absolute bind | 警告 | 不可预测的相对挂载 | Docker 绑定 | 否 |
| Dangerous bind mount | 严重 | 挂载了受限系统路径 | Docker 绑定 | 否 |
| Dangerous network mode | 严重 | 共享主机网络命名空间 | Docker 网络 | 否 |
| Dangerous seccomp | 严重 | 降低容器安全性 | 安全选项 | 否 |
| Dangerous AppArmor | 严重 | 降低容器安全性 | 安全选项 | 否 |
| Unrestricted CDP bridge | 警告 | Bridge 缺少来源限制 | CDP 来源范围 | 否 |
| Non-loopback CDP publish | 严重 | CDP 对外发布 | 容器发布配置 | 否 |
| Missing hash label | 警告 | 容器早于配置哈希 | 重建浏览器沙箱 | 否 |
| Stale hash epoch | 警告 | 容器早于配置 epoch | 重建浏览器沙箱 | 否 |
| No sandbox defaults | 警告 | 主机沙箱失败关闭 | Exec host 和沙箱模式 | 否 |
| No sandbox agents | 警告 | Agent 沙箱失败关闭 | Agent exec 和沙箱 | 否 |
| Full security exec | 警告/严重 | Host exec 完全运行 | Exec 安全设置 | 否 |
| FS disabled, exec enabled | 警告 | Shell 执行非只读 | 工具 deny 和 workspace | 否 |
| Auto-allow skills | 警告 | 隐式信任 skill bin | Host 审批 | 否 |
| Allowlist without eval | 警告 | 允许内联 eval | 严格内联 eval | 否 |
| Unprofiled safe bins | 警告 | Bin 缺少显式 profile | Safe bin 和 profile | 否 |
| Broad safe bins | 警告 | 削弱低风险信任模型 | Safe bin | 否 |
| Risky trusted dirs | 警告 | 包含可变目录 | 可信目录 | 否 |
| Symlink escape | 警告 | Skill 解析到根目录外 | Workspace 文件系统 | 否 |
| No plugin allowlist | 警告 | 无限制的插件安装 | 插件 allowlist | 否 |
| Unpinned npm plugins | 警告 | 可变的插件记录 | 安装元数据 | 否 |
| Missing plugin integrity | 警告 | 缺少完整性检查 | 安装元数据 | 否 |
| Plugin version drift | 警告 | 记录与包不匹配 | 安装元数据 | 否 |
| Plugin code safety | 警告/严重 | 发现可疑代码模式 | 插件代码来源 | 否 |
| Plugin entry path | 警告 | 指向隐藏位置 | 插件 manifest 入口 | 否 |
| Plugin entry escape | 严重 | 退出指定插件目录 | 插件 manifest 入口 | 否 |
| Plugin scan failed | 警告 | 代码扫描不完整 | 扫描环境 | 否 |
| Skill code safety | 警告/严重 | 可疑 skill 模式 | Skill 安装来源 | 否 |
| Skill scan failed | 警告 | Skill 扫描不完整 | 扫描环境 | 否 |
| Open channels with exec | 警告/严重 | 公开房间可达 exec agent | DM/群组和 exec 策略 | 否 |
| Open groups elevated | 严重 | 开放群组的 prompt 注入 | DM/群组策略 | 否 |
| Open groups runtime/fs | 严重/警告 | 开放群组可达文件工具 | DM/群组和工具策略 | 否 |
| Multi-user heuristic | 警告 | 多用户设置中的个人模型 | 信任边界 | 否 |
| Minimal profile overridden | 警告 | 绕过全局最小 profile | Agent 工具 profile | 否 |
| Permissive plugin tools | 警告 | 宽松上下文中的扩展工具 | 工具 profile | 否 |
| Legacy models | 警告 | 使用过时模型族 | 模型选择 | 否 |
| Weak tier models | 警告 | 低于推荐层级 | 模型选择 | 否 |
| Small model params | 严重/信息 | 小模型增加注入风险 | 模型和工具策略 | 否 |
| Attack surface summary | 信息 | 总体态势汇总 | 多个 key | 否 |

### 相关资源 / Associated Resources

- Core protection guidelines
- System setup details
- Proxy authentication trust

- 核心防护指南
- 系统配置详情
- 代理认证信任
