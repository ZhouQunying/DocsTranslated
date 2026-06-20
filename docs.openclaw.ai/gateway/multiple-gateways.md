# Multiple gateways

## 架构精读

> 跳过不影响阅读翻译正文。

### 大多数场景用一个 Gateway 就够了

**问题**: 多 Gateway 增加复杂度 (配置管理、资源消耗、调试困难)?

**方案**: **大多数场景用一个 Gateway**,单个 Gateway 可以:
- 处理多个 messaging 连接 (Slack、Discord、WhatsApp)
- 运行多个 agent (coding、support)
- 管理多个 session

**洞察**: 如果单个 Gateway 能满足需求,就不要用多 Gateway。过度工程 = 不必要的复杂度。

**权衡**:
- ✓ 简单: 一个配置、一个进程、一个状态
- ✗ 限制: 不适合强隔离、资源限制、故障域场景

### 什么时候需要多 Gateway?

**问题**: 什么场景需要多 Gateway?

**方案**: 三个场景:
- **强隔离**: 不同租户数据必须完全隔离 (SaaS),一个 Gateway 崩溃不能影响其他
- **资源限制**: 一个 Gateway 的资源消耗不能影响其他
- **故障域**: 一个 Gateway 挂了,另一个可以继续工作

**洞察**: 多 Gateway = 隔离,但也 = 复杂度。

**权衡**:
- ✓ 隔离: 数据、资源、故障域隔离
- ✗ 复杂: 配置管理、资源消耗、调试困难

### Rescue bot

**问题**: 主 Gateway 挂了,用户无法通过主 Gateway 调试问题?

**方案**: 配置 **rescue bot** (救援机器人),独立的 Gateway:
- 诊断主 Gateway 的问题
- 应用配置修复
- 重启主 Gateway

**洞察**: Rescue bot 不受主 Gateway 影响,可以用来修复主 Gateway。

**权衡**:
- ✓ 可用: 主 Gateway 挂了也能诊断
- ✗ 资源: 需要额外的 Gateway

**模式**: Kubernetes control plane 高可用——多个 control plane 节点,一个挂了其他的可以继续工作。

### 端口间隔

**问题**: 多 Gateway 场景下,每个 Gateway 使用不同的端口,端口太近可能冲突?

**方案**: **至少间隔 20 个端口**:
```
Gateway A: 1455
Gateway B: 1475
Gateway C: 1495
```

**洞察**: Gateway 可能使用多个端口 (主端口 + WebSocket + metrics),间隔 20 保证有足够的端口空间。

**权衡**:
- ✓ 安全: 防止端口冲突
- ✗ 浪费: 占用更多端口

**模式**: Docker container 端口映射——多个 container 映射到不同端口,需要避免冲突。

### 配置目录隔离

**问题**: 多 Gateway 共享配置会互相干扰?

**方案**: 每个 Gateway 必须有**独立的配置目录**:
```bash
openclaw gateway start --config-dir ~/.openclaw-instance-a
openclaw gateway start --config-dir ~/.openclaw-instance-b
```

**洞察**: 每个 Gateway 可能有不同的模型、channel、agent 配置,共享会互相干扰。

**权衡**:
- ✓ 隔离: 配置不共享
- ✓ 灵活: 每个 Gateway 配不同的模型、channel、agent

**模式**: Docker `--data-root`——多个 daemon 用不同 data root 目录隔离。

### 状态隔离

**问题**: 多 Gateway 共享状态会数据不一致?

**方案**: 每个 Gateway 有**独立的数据**:
- **Session 数据库**: 每个 Gateway 存自己的 session
- **Auth 数据库**: 每个 Gateway 存自己的 auth profile
- **Workspace**: 每个 Gateway 有自己的工作目录

**洞察**: 每个 Gateway 是独立的实体,不互相干扰。

**权衡**:
- ✓ 隔离: 数据不共享
- ✓ 一致: 每个 Gateway 自己的状态
