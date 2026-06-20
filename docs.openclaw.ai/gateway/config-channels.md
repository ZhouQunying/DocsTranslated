# Configuration — channels

## 架构精读

> 跳过不影响阅读翻译正文。

### DM 和群组访问控制

**问题**: 谁能通过 channel 跟 agent 对话?

**方案**:
- **DM** (私聊): 默认允许,可配 `allowFrom` 白名单
- **群组**: 默认不允许,需显式配置允许的群组 ID

**洞察**: DM 是 1 对 1,风险低。群组是 1 对多,风险高。

**权衡**:
- ✓ DM 默认允许: 方便
- ✓ 群组默认拒绝: 安全

**模式**: 防火墙默认拒绝——默认所有端口关闭,只开放需要的。

**群组风险**:
- 群里任何人都能跟 bot 说话
- 群里可能包含敏感信息
- 群里的 bot 可能被滥用

### Mention gating

**问题**: 群组里 agent 响应所有消息,噪音大?

**方案**: 只响应 mention (被 @ 的消息):
```json
{
  channels: {
    discord: {
      mentionGating: true
    }
  }
}
```

**洞察**: 用户明确想跟 agent 对话时才激活。

**权衡**:
- ✓ 减少噪音: 不干扰正常交流
- ✓ 节省资源: 不调用无关消息的 LLM
- ✓ 保护隐私: 不读取所有消息

**模式**: Slack bot 默认行为——只响应 @ 消息或特定 command。

### 多账户

**问题**: 不同 agent 需要不同 bot 身份?

**方案**: 同一 channel 配置多个账户:
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

**洞察**: 每个 agent 有自己的身份 (名字、头像),用户一眼就知道在跟谁对话。

**权衡**:
- ✓ 清晰: 用户知道在跟谁对话
- ✗ 复杂: 需要管理多个 bot token

### 每个 channel 独立的模型覆盖

**问题**: 不同 channel 使用场景不同,需要不同模型?

**方案**: Channel 级别模型覆盖:
```json
{
  channels: {
    whatsapp: {
      model: "gpt-3.5-turbo"
    }
  }
}
```

**洞察**: 每个场景用最合适的模型。

**权衡**:
- ✓ 优化: WhatsApp 用快/便宜模型,Slack 用强/贵模型
- ✗ 复杂: 需要为每个 channel 配置模型

**模式**: Kubernetes resource request/limit——每个 Pod 配自己的资源需求。

**场景**:
- WhatsApp: 手机、消息短、响应快 → GPT-3.5
- Slack: 工作、问题复杂 → GPT-4
- WebChat: 深度问题 → Claude

### 每个 channel 独立的心跳间隔

**问题**: 不同 channel 实时性要求不同?

**方案**: Channel 级别心跳间隔:
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

**洞察**: 每个场景用最合适的频率。

**权衡**:
- ✓ 优化: Slack 5 分钟 (工作场景),Discord 15 分钟 (社区场景)
- ✗ 复杂: 需要为每个 channel 配置间隔
