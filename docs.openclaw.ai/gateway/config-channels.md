# Configuration — channels

## 架构精读

> 跳过不影响阅读翻译正文。

### DM 和群组访问控制——谁能跟 bot 说话

Channel 配置控制谁可以通过这个 channel 跟 agent 对话:

- **DM**(Direct Message,私聊): 默认允许所有 DM,可以配置 `allowFrom` 白名单
- **群组**(Group chat): 默认不允许,需要显式配置允许的群组 ID

**为什么群组默认不允许?** 因为群组是多人环境,安全风险更高:
- 群里任何人都能跟 bot 说话,可能发送恶意指令
- 群里可能包含敏感信息(如内部讨论),bot 不应该看到所有消息
- 群里的 bot 可能被滥用(如大量请求,消耗 API 额度)

私聊是 1 对 1,风险较低,默认允许。群组是 1 对多,风险较高,默认拒绝。这跟 **防火墙的默认拒绝策略**是一个思路——默认所有端口关闭,只开放需要的端口。OpenClaw 的 channel 也是同样: 默认所有群组拒绝,只允许配置的群组。

### Mention gating——群组里只响应 @ 消息

在群组里,agent 默认只响应 **mention**(被 @ 的消息),不是所有消息:

```json
{
  channels: {
    discord: {
      mentionGating: true
    }
  }
}
```

**为什么这样设计?** 因为群组消息量大,如果 agent 响应每条消息:
- **噪音大**: 用户讨论时,agent 不断插话,干扰正常交流
- **资源浪费**: 每条消息都调 LLM,消耗 API 额度,但大部分消息跟 agent 无关
- **隐私问题**: agent 读取所有消息,可能看到用户不想让它看到的内容

Mention gating 让 agent 只在被 @ 时响应——用户明确想跟 agent 对话时才激活。这跟 Slack bot 的默认行为是一个思路——Slack bot 默认只响应 @ 消息或特定 command,不会对所有消息回复。

### 多账户——同一 channel 多个 bot

OpenClaw 支持同一 channel(如 Slack)配置多个账户(多个 bot):

```json
{
  channels: {
    slack: {
      accounts: {
        coding: { botToken: "xoxb-coding..." },
        support: { botToken: "xoxb-support..." }
      }
    }
  }
}
```

**为什么需要多账户?** 因为不同 agent 可能需要不同的 bot 身份:
- Coding bot: 名字叫"CodeHelper",头像是一个机器人,处理代码问题
- Support bot: 名字叫"SupportTeam",头像是公司 logo,处理客户问题

如果只有一个 bot,用户分不清"这是 coding bot 还是 support bot",体验混乱。多账户让每个 agent 有自己的身份,用户一眼就知道在跟谁对话。

### 每个 channel 独立的模型覆盖

每个 channel 可以配置自己的模型,覆盖全局默认:

```json
{
  channels: {
    whatsapp: {
      model: "gpt-3.5-turbo"
    }
  }
}
```

**为什么需要 channel 级别的模型覆盖?** 因为不同 channel 的使用场景不同:
- **WhatsApp**: 用户用手机,消息短,响应要快,用 GPT-3.5(便宜、快)
- **Slack**: 用户在工作,问题复杂,用 GPT-4(贵、准确)
- **WebChat**: 用户可能问深度问题,用 Claude(长上下文、推理强)

如果全局统一用 GPT-4,WhatsApp 用户觉得响应慢、费用高。Channel 级别覆盖让每个场景用最合适的模型。

**这跟 Kubernetes 的 resource request/limit 是一个思路**——每个 Pod 可以配置自己的资源需求,不依赖全局默认。OpenClaw 的 channel model override 也是同样: 每个 channel 配自己的模型,不依赖全局默认。

### 每个 channel 独立的心跳间隔

Heartbeat(心跳)是 agent 定期执行的检查(如检查邮件、监控 API),每个 channel 可以配不同的间隔:

```json
{
  channels: {
    slack: {
      heartbeat: { intervalMinutes: 5 }
    },
    discord: {
      heartbeat: { intervalMinutes: 15 }
    }
  }
}
```

**为什么需要不同间隔?** 因为不同 channel 的实时性要求不同:
- Slack 是工作场景,5 分钟检查一次(用户期望快速响应)
- Discord 是社区场景,15 分钟检查一次(用户不那么急)

如果统一 5 分钟,Discord 的 heartbeat 太频繁,浪费资源。Channel 级别间隔让每个场景用最合适的频率。
