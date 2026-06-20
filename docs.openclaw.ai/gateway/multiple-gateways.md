# Multiple gateways

## 架构精读

> 跳过不影响阅读翻译正文。

### 大多数场景用一个 Gateway 就够了

文档强调: **Most setups should use one Gateway**(大多数设置应该用一个 Gateway),因为单个 Gateway 可以:
- 处理多个 messaging 连接(Slack、Discord、WhatsApp 同时连接)
- 运行多个 agent(coding agent、support agent 共存)
- 管理多个 session(每个 agent 的每个对话都有独立 session)

**为什么强调一个 Gateway?** 因为多 Gateway 会增加复杂度:
- **配置管理**: 每个 Gateway 有自己的配置,需要分别维护
- **资源消耗**: 每个 Gateway 占用内存和 CPU,多 Gateway 消耗更多资源
- **调试困难**: 问题可能出在 Gateway 之间的交互,比单 Gateway 更难调试

如果单个 Gateway 能满足需求,就不要用多 Gateway。过度工程 = 不必要的复杂度。

### 什么时候需要多 Gateway?

几个场景需要多 Gateway:

**强隔离**(stronger isolation):
- 不同租户的数据必须完全隔离(如 SaaS 场景,每个客户一个 Gateway)
- 一个 Gateway 崩溃不能影响其他 Gateway(如关键任务的 Gateway 跟实验性 Gateway 分开)

**资源限制**(resource limits):
- 一个 Gateway 的资源消耗不能影响其他 Gateway(如高负载的 Gateway 跟低负载的 Gateway 分开)
- 不同 Gateway 需要不同的资源配置(如一个 Gateway 用高配机器,另一个用低配机器)

**故障域**(failure domains):
- 一个 Gateway 挂了,另一个 Gateway 可以继续工作(如主 Gateway 跟备份 Gateway)

### Rescue bot——主 Gateway 挂了的后备

文档建议配置一个 **rescue bot**(救援机器人),当主 Gateway 挂时,rescue bot 可以:
- 诊断主 Gateway 的问题
- 应用配置修复
- 重启主 Gateway

**为什么需要 rescue bot?** 因为主 Gateway 挂了,用户无法通过主 Gateway 调试问题(因为 Gateway 不响应)。Rescue bot 是独立的 Gateway,不受主 Gateway 影响,可以用来修复主 Gateway。

**这跟 Kubernetes 的 control plane 高可用**是一个思路——多个 control plane 节点,一个挂了,其他的可以继续工作。OpenClaw 的 rescue bot 也是同样: 主 Gateway 挂了,rescue bot 可以继续工作,修复主 Gateway。

### 端口间隔——至少 20 个端口

多 Gateway 场景下,每个 Gateway 使用不同的端口,文档建议**至少间隔 20 个端口**:

```
Gateway A: 1455
Gateway B: 1475 (不是 1456)
Gateway C: 1495 (不是 1476)
```

**为什么间隔 20?** 因为:
- Gateway 可能使用多个端口(如主端口 + WebSocket 端口 + metrics 端口)
- 如果端口太近(如 1455 和 1456),可能冲突
- 间隔 20 保证每个 Gateway 有足够的端口空间

**这跟 Docker container 的端口映射**是一个思路——多个 container 映射到 host 的不同端口,需要避免冲突。OpenClaw 的多 Gateway 也是同样: 每个 Gateway 用不同的端口,间隔足够大,避免冲突。

### 配置目录隔离——每个 Gateway 独立的配置

多 Gateway 场景下,每个 Gateway 必须有独立的配置目录:

```bash
# Gateway A
openclaw gateway start --config-dir ~/.openclaw-instance-a

# Gateway B
openclaw gateway start --config-dir ~/.openclaw-instance-b
```

**为什么需要独立配置?** 因为:
- 每个 Gateway 可能有不同的模型配置(如一个用 GPT-4,另一个用 Claude)
- 每个 Gateway 可能有不同的 channel 配置(如一个连 Slack,另一个连 Discord)
- 每个 Gateway 可能有不同的 agent 配置(如一个跑 coding agent,另一个跑 support agent)

如果共享配置,两个 Gateway 会互相干扰(如一个 Gateway 修改了配置,另一个 Gateway 也受影响)。

**这跟 Docker 的 --data-root 是一个思路**——多个 Docker daemon 用不同的 data root 目录,隔离容器和镜像。OpenClaw 的多 Gateway 也是同样: 用不同的配置目录,隔离配置和状态。

### 状态隔离——每个 Gateway 独立的数据

多 Gateway 场景下,每个 Gateway 有独立的数据:
- **Session 数据库**: 每个 Gateway 存自己的 session
- **Auth 数据库**: 每个 Gateway 存自己的 auth profile
- **Workspace**: 每个 Gateway 有自己的工作目录

**为什么需要状态隔离?** 因为:
- 不同 Gateway 的 session 不应该共享(如 coding agent 的 session 不应该出现在 support agent 的 Gateway 里)
- 不同 Gateway 的 auth 可能不同(如一个用用户 A 的 API key,另一个用用户 B 的 API key)
- 不同 Gateway 的 workspace 可能不同(如一个处理项目 A,另一个处理项目 B)

状态隔离保证: 每个 Gateway 是独立的实体,不互相干扰。
