# 后台任务

## 架构精读

> 跳过不影响阅读翻译正文。

### 为什么 agent 系统需要"任务账本"而非仅仅会话日志？

传统 agent 系统将所有工作放在会话上下文中——会话结束，工作记录也丢失。OpenClaw 将后台工作与主会话分离：ACP 运行、子 agent 生成、隔离 cron 执行和 CLI 操作都创建**任务记录**，独立于会话生命周期。这就像操作系统的进程表——进程可以脱离终端独立运行，进程表记录所有活跃和已完成的进程状态。好处是工作不会因会话结束而不可追踪。

第二个设计：完成是推送驱动的。分离的工作完成时可直接通知或唤醒请求者会话/心跳，无需轮询状态。这就像 Webhook 回调而非 REST 轮询——服务端主动推送完成事件，客户端不需要反复检查。好处是消除了状态轮询循环带来的延迟和资源浪费。

第三个边界：任务是记录器而非调度器。Cron 和心跳决定*何时*运行工作，任务记录*发生了什么*。这是调度与审计的分离——就像 Kubernetes 中 CronJob 控制器创建 Job，Job 创建 Pod，而 Event 系统记录所有状态变化。好处是每个关注点可独立演进和查询。

---

后台任务跟踪在**主对话会话之外**运行的工作：ACP 运行、子 agent 生成、隔离 cron 作业执行和 CLI 发起的操作。

任务**不**替代会话、cron 作业或心跳——它们是记录分离工作发生了什么、何时发生以及是否成功的**活动账本**。

并非所有 agent 运行都创建任务。心跳轮次和普通交互式聊天不会。所有 cron 执行、ACP 生成、子 agent 生成和 CLI agent 命令会。

## 快速开始

```bash
# 列出所有任务（最新优先）
openclaw tasks list

# 按运行时或状态过滤
openclaw tasks list --runtime acp
openclaw tasks list --status running

# 显示特定任务详情
openclaw tasks show <lookup>

# 取消运行中的任务
openclaw tasks cancel <lookup>

# 运行健康审计
openclaw tasks audit
```

## 什么创建任务

| 来源 | 运行时类型 | 何时创建任务记录 | 默认通知策略 |
| --- | --- | --- | --- |
| ACP 后台运行 | `acp` | 生成子 ACP 会话 | `done_only` |
| 子 agent 编排 | `subagent` | 通过 `sessions_spawn` 生成子 agent | `done_only` |
| Cron 作业（所有类型） | `cron` | 每次 cron 执行 | `silent` |
| CLI 操作 | `cli` | 通过 Gateway 运行的 `openclaw agent` 命令 | `silent` |

## 任务生命周期

每个任务经历 `queued → running → terminal`（succeeded、failed、timed_out、cancelled 或 lost）。

Cron 任务在 cron 运行时仍持有该作业时保持活跃；如内存中运行时状态已消失，任务维护先检查持久化 cron 运行历史，然后才将任务标记为 lost。

终态记录保留 7 天，然后自动清理。

## 通知策略

| 策略 | 行为 |
| --- | --- |
| `silent` | 不发送通知 |
| `state_changes` | 在状态变化时通知 |
| `done_only` | 仅在完成时通知 |
| `always` | 每次状态变化都通知 |

完成通知直接交付到 channel 或排队等待下一次心跳。

## 相关

- [定时任务](/automation/cron-jobs)——cron 调度的调度器
- [任务流](/automation/taskflow)——协调多个任务的多步骤流编排
- [Automation](/automation)——所有自动化机制概览
