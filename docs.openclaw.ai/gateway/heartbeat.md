# Heartbeat

## 架构精读

> 跳过不影响阅读翻译正文。

### 心跳的响应约定——为什么空闲需要成功令牌？

心跳的核心设计是响应约定：

- **空闲**（无事发生）：返回 `HEARTBEAT_OK` 成功令牌，静默
- **告警**（有事发生）：返回告警文本，通知用户

这跟 Prometheus Alertmanager 的 silence 是一个思路——正常情况下静默，异常时才通知。心跳用 `HEARTBEAT_OK` 令牌作为"一切正常"的信号，Gateway 识别后静默处理，不骚扰用户。

如果代理返回任何非 `HEARTBEAT_OK` 的内容，Gateway 按告警处理（通知用户）。这防止了"代理返回无关内容但 Gateway 静默丢弃"的问题。

### HEARTBEAT.md——为什么是工作区文件不是配置？

心跳的检查清单是工作区中的 `HEARTBEAT.md` 文件，而非配置字段：

```markdown
# HEARTBEAT.md
- [ ] Check pending PR reviews (every 30 min)
- [ ] Review error logs (every hour)
- [ ] Monitor disk usage (every 4 hours)
```

这跟 CronJob 的脚本是一个思路——CronJob 执行的是脚本文件，心跳执行的是 Markdown 检查清单。好处是检查清单可以版本控制（Git）、可以协作编辑（PR 审查）、可以按间隔分组（被代理解析为 `every N min` block）。

### 作用域层级——为什么 global → per-agent → per-channel？

Heartbeat 配置的作用域层级是：

1. global（`heartbeat`）：全局默认
2. per-agent（`agents.defaults.heartbeat`）：agent 级别覆盖
3. per-channel（`channels.<id>.heartbeat`）：channel 级别覆盖

这跟 CSS 的特异性是一个思路——global 是基准线，per-agent 覆盖 global，per-channel 覆盖 per-agent。越具体的配置优先级越高。

### 成本意识——为什么推荐隔离会话 + 轻量模型？

心跳是高频调用（每 15 分钟一次），成本控制关键：

- **隔离会话**：心跳用独立会话不污染主会话上下文
- **轻量模型**：心跳用 `gpt-3.5-turbo` 而非 `gpt-4`（大幅降低令牌消耗）
- **HEARTBEAT_OK 快速终止**：代理返回 `HEARTBEAT_OK` 后立即停止（不浪费令牌）

这跟 AWS Spot 实例是一个思路——高频调用用低成本资源（Spot），低频高质量调用用高性能资源（按需）。

---

The system executes periodic agent turns within the primary session, allowing the AI to highlight important items without overwhelming the user.

系统在主 session 中执行周期性 agent turn——AI 主动巡检并报告重要事项，不骚扰用户。