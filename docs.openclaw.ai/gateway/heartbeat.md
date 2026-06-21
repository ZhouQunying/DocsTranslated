# Heartbeat

## 架构精读

> 跳过不影响阅读翻译正文。

### Heartbeat 的响应约定——为什么 idle 需要 SUCCESS token？

Heartbeat 的核心设计是响应约定：

- **idle**（无事发生）：返回 `HEARTBEAT_OK` success token，静默
- **alert**（有事发生）：返回 alert text，通知用户

这跟 Prometheus Alertmanager 的 silence 是一个思路——正常情况下静默，异常时才通知。Heartbeat 用 `HEARTBEAT_OK` token 作为"一切正常"的信号，Gateway 识别后静默处理，不骚扰用户。

如果 agent 返回任何非 `HEARTBEAT_OK` 的内容，Gateway 按 alert 处理（通知用户）。这防止了"agent 返回无关内容但 Gateway 静默丢弃"的问题。

### HEARTBEAT.md——为什么是 workspace file 不是 config？

Heartbeat 的 checklist 是 workspace 中的 `HEARTBEAT.md` 文件，而非 config 字段：

```markdown
# HEARTBEAT.md
- [ ] Check pending PR reviews (every 30 min)
- [ ] Review error logs (every hour)
- [ ] Monitor disk usage (every 4 hours)
```

这跟 CronJob 的 script 是一个思路——CronJob 执行的是脚本文件，Heartbeat 执行的是 markdown checklist。好处是 checklist 可以版本控制（Git）、可以协作编辑（PR review）、可以按 interval 分组（被 agent 解析为 `every N min` block）。

### 作用域层级——为什么 global → per-agent → per-channel？

Heartbeat 配置的作用域层级是：

1. global（`heartbeat`）：全局默认
2. per-agent（`agents.defaults.heartbeat`）：agent 级别覆盖
3. per-channel（`channels.<id>.heartbeat`）：channel 级别覆盖

这跟 CSS 的 specificity 是一个思路——global 是基准线，per-agent 覆盖 global，per-channel 覆盖 per-agent。越具体的配置优先级越高。

### Cost awareness——为什么推荐隔离 session + 轻量模型？

Heartbeat 是高频调用（每 15 分钟一次），成本控制关键：

- **隔离 session**：heartbeat 用独立 session 不污染主 session context
- **轻量模型**：heartbeat 用 `gpt-3.5-turbo` 而非 `gpt-4`（大幅降低 token 消耗）
- **HEARTBEAT_OK 快速终止**：agent 返回 `HEARTBEAT_OK` 后立即停止（不浪费 token）

这跟 AWS Spot Instance 是一个思路——高频调用用低成本资源（Spot），低频高质量调用用高性能资源（On-Demand）。

---

The system executes periodic agent turns within the primary session, allowing the AI to highlight important items without overwhelming the user.

系统在主 session 中执行周期性 agent turn——AI 主动巡检并报告重要事项，不骚扰用户。