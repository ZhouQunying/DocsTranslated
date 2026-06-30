# `openclaw commitments`

## 架构精读

> 跳过不影响阅读翻译正文。

### 计划追踪——为什么需要专门的命令？

`openclaw commitments` 追踪智能体的计划（承诺执行的任务）：

- **列出活跃计划**：智能体承诺要做的任务
- **查看计划状态**：待执行/执行中/已完成/失败
- **取消计划**：中止未完成的计划

这跟 Jira 的 sprint backlog 是一个思路——追踪"承诺要做的事"（commitments），而非"所有可能做的事"（backlog）。计划追踪让智能体的行为可预测（"我说了要做 X，我就会做 X"）。

### 与 cron 的区别——为什么分开？

- **cron**：定时触发的周期性任务
- **commitments**：一次性承诺（智能体主动承诺的任务）

这跟 timer vs promise 是一个思路——cron 是"每到时间就做"，commitments 是"我说了要做就做"。两者独立管理。

---

Tracks agent commitments (promised tasks): list active, view status (pending/running/completed/failed), cancel pending. Separate from cron (periodic timer-based tasks). Commitments are one-time promises the agent actively made.

追踪智能体计划（承诺的任务）：列出活跃、查看状态（待执行/执行中/已完成/失败）、取消待执行。区别于 cron（周期性定时任务）。计划是智能体主动承诺的一次性任务。
