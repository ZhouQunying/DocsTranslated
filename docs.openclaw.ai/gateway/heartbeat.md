# Heartbeat

## 架构精读

> 跳过不影响阅读翻译正文。

### Heartbeat vs Cron——两种定时任务的区别

OpenClaw 有两种定时任务机制:

**Heartbeat**(心跳):
- 定期在**主 session**里执行 agent turn(一轮对话)
- Agent 可以访问对话历史,知道"之前聊了什么"
- 适合"定期检查 + 报告"场景(如"检查邮件,有新邮件就告诉我")

**Cron**(定时任务):
- 在**独立的 session**里执行,不访问主 session 的对话历史
- 每次执行都是"全新的",不知道之前发生了什么
- 适合"独立任务"场景(如"每天生成报告"、"每小时备份数据库")

**为什么需要两种?** 因为场景不同:
- Heartbeat 需要上下文(如"检查上次 heartbeat 之后有没有新邮件")
- Cron 不需要上下文(如"生成今天的报告",不需要知道昨天的报告)

如果只有 Heartbeat,所有定时任务都在主 session 里,对话历史会越来越长,消耗 token。如果只有 Cron,需要上下文的任务做不到(如"检查新邮件",需要知道上次检查到哪了)。

**这跟 Linux 的 cron vs systemd timer 是一个思路**——cron 是简单的定时执行,systemd timer 可以依赖其他 service、访问环境变量。OpenClaw 的 Heartbeat vs Cron 也是同样的权衡: 简单 vs 有上下文。

### Heartbeat 的 cadence——执行频率

Heartbeat 的 cadence(节奏,执行频率)可配置:

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

**为什么频率可配置?** 因为不同场景的实时性要求不同:
- 邮件检查: 5 分钟(用户期望快速通知)
- 系统监控: 15 分钟(不需要太实时)
- 日报生成: 24 小时(每天一次)

如果统一 5 分钟,日报生成会浪费资源(每天执行 288 次,只需要 1 次)。如果统一 24 小时,邮件检查太慢(用户等不及)。

### HEARTBEAT.md——自定义 heartbeat 的行为

用户可以在 workspace 根目录放一个 `HEARTBEAT.md` 文件,定义 heartbeat 应该做什么:

```markdown
# Heartbeat

检查以下内容:
1. 有没有新邮件
2. 有没有新的 GitHub PR review request
3. 如果有任何需要关注的,告诉我
```

**为什么用 HEARTBEAT.md?** 因为 heartbeat 的行为是用户自定义的,不是固定的。不同用户需要 heartbeat 做不同的事:
- 开发者: 检查 GitHub、Jira、邮件
- 运维: 检查监控告警、日志错误
- 产品经理: 检查 Slack 消息、客户反馈

HEARTBEAT.md 让用户用自然语言描述 heartbeat 应该做什么,agent 按描述执行。

**这跟 crontab 的 command 是一个思路**——crontab 里配置"每天凌晨 2 点执行 backup.sh",heartbeat 里配置"每 15 分钟检查邮件"。都是"定时执行用户定义的任务"。

### Heartbeat 消息的去向——配置输出位置

Heartbeat 的输出(如"有 3 封新邮件")可以发送到不同位置:

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

**为什么需要配置输出位置?** 因为用户可能在多个 channel(Slack、Discord、WhatsApp),heartbeat 的输出应该发到用户最常看的 channel。

如果 heartbeat 输出到 WebChat,但用户很少打开 WebChat,就看不到通知。配置输出到 Slack(用户工作时常开),用户能及时看到。

### Per-agent heartbeat——每个 agent 独立的心跳

每个 agent 可以配置自己的 heartbeat:

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

**为什么需要 per-agent?** 因为不同 agent 的实时性要求不同:
- Coding agent: 5 分钟(开发者期望快速响应)
- Support agent: 30 分钟(客户问题不那么紧急)

如果统一 5 分钟,support agent 的 heartbeat 太频繁,浪费资源。Per-agent 让每个 agent 用最合适的频率。

### Heartbeat 不创建 background task 记录

Heartbeat 在主 session 里执行,**不**创建 background task(后台任务)记录:

**为什么不创建 task 记录?** 因为 heartbeat 是"定期的、重复的",不是"一次性的任务"。如果每次 heartbeat 都创建 task 记录:
- Task 列表会越来越长(每 15 分钟一个,一天 96 个)
- 用户分不清"哪些是真正的任务,哪些是 heartbeat"
- Task 管理 UI 变得混乱

Heartbeat 的输出直接显示在主 session 的对话里,不创建独立的 task 记录。

**这跟系统日志的级别**是一个思路——INFO 级别的日志记录所有操作,ERROR 级别只记录错误。Heartbeat 是"INFO"级别(定期执行,不需要特别关注),background task 是"ERROR"级别(一次性任务,需要用户关注)。
