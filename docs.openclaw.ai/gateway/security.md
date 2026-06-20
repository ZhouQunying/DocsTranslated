# Security

## 架构精读

> 跳过不影响阅读翻译正文。

### Personal assistant trust model

**问题**: Agent 用谁的凭证?访问谁的资源?

**方案**: Agent = 你的个人助手
- 用**你的** API key
- 访问**你的**文件
- 执行**你的**命令

**洞察**: OpenClaw 不是多租户平台。Agent 只服务你一个人,所有操作都算你做的。

**权衡**: 
- ✓ 简单: 不需要复杂的权限隔离
- ✗ 不适合: 企业级多用户场景

**模式**: SSH key 模型——你的 key,你的操作,你的责任。

### Deployment/host trust

**问题**: Gateway 运行在哪台机器,信任哪台机器?

**方案**: Host trust = Gateway 可以:
- 读取 host 文件
- 执行 host 命令
- 访问 host 网络

**洞察**: 你自己部署 Gateway,你信任 host。Host 被入侵 = Gateway 被入侵。

**权衡**:
- ✓ 简单: 不需要额外的 host 验证
- ✗ 风险: Host 安全 = Gateway 安全

**模式**: Docker daemon 模型——daemon 信任 host,host 被入侵则 container 危险。

### Secure file operations

**问题**: Agent 可能执行恶意文件操作(如 `rm -rf /`)?

**方案**: 限制 agent 只能操作特定目录:
- ✓ Workspace 目录
- ✓ 配置目录
- ✗ `/etc`、`/usr`、`/var` 等系统目录

**洞察**: 文件操作边界 = 把 agent 限制在安全目录内。

**权衡**:
- ✓ 安全: 防止恶意文件操作
- ✗ 限制: Agent 不能访问某些合法目录

**模式**: Chroot 模型——进程被限制在特定目录内。

### Shared Slack workspace risk

**问题**: Agent 连接共享 Slack 频道,频道里的任何人都能给 agent 发消息?

**方案**: 
- ✗ 生产环境不连接共享频道
- ✓ 或用 secure DM mode(只响应特定用户)

**洞察**: 你信任 agent,但不信任频道里的所有人。

**权衡**:
- ✓ 安全: 防止恶意用户 prompt injection
- ✗ 不便: 不能在共享频道里使用 agent

**模式**: 公共 WiFi 模型——你信任自己的设备,但不信任网络上的其他设备。

### Company-shared agent

**问题**: 多人共享同一 agent,session 和 workspace 可能包含敏感信息?

**方案**:
- ✓ 多 Gateway(每个用户一个)
- ✓ 或 secure DM mode(只响应特定用户)

**洞察**: 共享 agent = 共享 session 和 workspace,需要隔离。

**权衡**:
- ✓ 多 Gateway: 完全隔离,但资源消耗大
- ✓ Secure DM mode: 轻量隔离,但共享 workspace

**模式**: 共享邮箱模型——多人共用邮箱,所有人的邮件混在一起,需要隔离。

### Secure DM mode

**问题**: Agent 连接共享频道,但只想响应特定用户?

**方案**: Secure DM mode = agent 只响应特定用户的消息,忽略其他人。

**洞察**: 在共享频道里使用"私人 agent"。

**权衡**:
- ✓ 安全: 只响应信任的用户
- ✗ 限制: 其他用户不能使用 agent

**模式**: 手机勿扰模式——只响特定联系人的来电,其他人静音。
