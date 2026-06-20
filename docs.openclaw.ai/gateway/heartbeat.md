# Heartbeat

## 架构精读

> 跳过不影响阅读翻译正文。

### Heartbeat vs Cron

**问题**: 定时任务需要上下文 (如"检查上次之后有没有新邮件") vs 不需要上下文 (如"生成今天的报告")?

**方案**: 两种:
- **Heartbeat**: 在主 session 执行,可访问对话历史
- **Cron**: 在独立 session 执行,不访问主 session 历史

**洞察**: Heartbeat 需要上下文,Cron 不需要。

**权衡**:
- ✓ Heartbeat: 有上下文,可访问历史
- ✗ Heartbeat: 对话历史越来越长,消耗 token
- ✓ Cron: 独立,不消耗主 session token
- ✗ Cron: 无上下文

**模式**: Linux cron vs systemd timer——cron 简单,systemd timer 可依赖其他 service。

### Heartbeat 的 cadence

**问题**: 不同场景的实时性要求不同 (邮件 5 分钟、监控 15 分钟、日报 24 小时)?

**方案**: Cadence (节奏) 可配置:
```json
{
  agents: {
    defaults: {
      heartbeat: {
        intervalMinutes: 15
      }
    }
  }
}
```

**洞察**: 每个场景用最合适的频率。

**权衡**:
- ✓ 灵活: 按需配置
- ✓ 节省: 不需要太实时的场景用低频率

### HEARTBEAT.md

**问题**: Heartbeat 的行为是用户自定义的,不同用户需要 heartbeat 做不同的事?

**方案**: Workspace 根目录放 `HEARTBEAT.md`:
```markdown
# Heartbeat

检查以下内容:
1. 有没有新邮件
2. 有没有新的 GitHub PR review request
3. 如果有任何需要关注的,告诉我
```

**洞察**: 用自然语言描述 heartbeat 应该做什么,agent 按描述执行。

**权衡**:
- ✓ 灵活: 用户自定义行为
- ✓ 简单: 用自然语言描述

**模式**: Crontab command——配置"每天凌晨 2 点执行 backup.sh"。

### Heartbeat 消息的去向

**问题**: 用户可能在多个 channel,heartbeat 输出应该发到用户最常看的 channel?

**方案**: 配置输出位置:
```json
{
  agents: {
    defaults: {
      heartbeat: {
        outputChannel: "slack"
      }
    }
  }
}
```

**洞察**: 输出到用户最常看的 channel,用户能及时看到通知。

**权衡**:
- ✓ 及时: 用户能看到通知
- ✓ 灵活: 按需配置

### Per-agent heartbeat

**问题**: 不同 agent 的实时性要求不同 (coding agent 5 分钟、support agent 30 分钟)?

**方案**: 每个 agent 独立配置:
```json
{
  agents: {
    list: [
      {
        name: "coding",
        heartbeat: { intervalMinutes: 5 }
      },
      {
        name: "support",
        heartbeat: { intervalMinutes: 30 }
      }
    ]
  }
}
```

**洞察**: 每个 agent 用最合适的频率。

**权衡**:
- ✓ 灵活: 按需配置
- ✓ 节省: 不需要太实时的 agent 用低频率

### Heartbeat 不创建 background task 记录

**问题**: 每次 heartbeat 都创建 task 记录,task 列表越来越长,分不清"哪些是真正的任务,哪些是 heartbeat"?

**方案**: Heartbeat **不创建** background task 记录,输出直接显示在主 session 的对话里。

**洞察**: Heartbeat 是"定期的、重复的",不是"一次性的任务",不需要 task 记录。

**权衡**:
- ✓ 清晰: task 列表只有真正的任务
- ✓ 简洁: 不创建额外记录

**模式**: 系统日志级别——INFO 记录所有操作,ERROR 只记录错误。Heartbeat 是 INFO 级别。
