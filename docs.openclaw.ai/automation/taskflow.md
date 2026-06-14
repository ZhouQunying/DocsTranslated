# 任务流

## 架构精读

> 跳过不影响阅读翻译正文。

### 为什么需要流编排而非让 agent 自己链式调用？

agent 可以在一个会话中按顺序执行多个步骤，但问题是：Gateway 重启时会话中断，步骤间的状态丢失。任务流（Task Flow）将多步骤编排提取到**持久化的流层**——每个步骤是一个后台任务，流跟踪整体状态、修订版本和进度。这就像 Apache Airflow 的 DAG 与 Celery 任务的关系——Celery 执行单个任务，Airflow 编排多步骤 DAG 并持久化进度。好处是流可以跨 Gateway 重启存活。

第二个设计：两种同步模式。**托管模式**（managed）中流管理端到端生命周期——创建任务、驱动完成、自动推进状态。**镜像模式**（mirrored）中流观察外部创建的任务并保持状态同步，但不控制任务创建。这就像 Kubernetes 中 Deployment 管理 ReplicaSet（托管）vs HPA 观察外部指标（镜像）。好处是流可以统一视图，无论任务来自内部编排还是外部 cron/CLI。

第三个边界：修订版本跟踪用于并发冲突检测。每个流持久化自己的状态并跟踪修订版本，当多个来源试图同时推进同一流时检测冲突。这就像数据库的乐观并发控制（OCC）——每次更新携带版本号，冲突时拒绝而非覆盖。好处是并发安全无需全局锁。

---

任务流是位于[后台任务](/automation/tasks)之上的流编排基底。它管理具有自己状态、修订版本跟踪和同步语义的持久多步骤流，而单个任务仍是分离工作的单元。

## 何时使用任务流

当工作跨越多个顺序或分支步骤且需要跨 Gateway 重启的持久进度跟踪时使用任务流。对于单个后台操作，普通[任务](/automation/tasks)即可。

| 场景 | 使用 |
| --- | --- |
| 单个后台作业 | 普通任务 |
| 多步骤流水线（A 然后 B 然后 C） | 任务流（托管） |
| 观察外部创建的任务 | 任务流（镜像） |
| 一次性提醒 | Cron 作业 |

## 可靠的调度工作流模式

对于循环工作流（如市场情报简报），将调度、编排和可靠性检查视为独立层：

1. 使用[定时任务](/automation/cron-jobs)进行时间调度
2. 当工作流应基于先前上下文时使用持久 cron 会话
3. 使用确定性步骤、审批门控和恢复令牌
4. 使用任务流跨子任务、等待、重试和 Gateway 重启跟踪多步骤运行

在工作流内部，将可靠性检查放在 LLM 摘要步骤之前：

```yaml
name: market-intel-brief
steps:
  - id: preflight
    command: market-intel check --json
  - id: collect
    command: market-intel collect --json
    stdin: $preflight.json
  - id: summarize
    command: market-intel summarize --json
    stdin: $collect.json
  - id: approve
    command: market-intel deliver --preview
    stdin: $summarize.json
    approval: required
  - id: deliver
    command: market-intel deliver --execute
    stdin: $summarize.json
    condition: $approve.approved
```

## 同步模式

### 托管模式

任务流端到端管理生命周期。它在流步骤中创建任务，驱动完成，并自动推进流状态。

示例：周报流（1）收集数据，（2）生成报告，（3）交付。任务流将每个步骤创建为后台任务，等待完成，然后移至下一步。

```
Flow: weekly-report
  Step 1: gather-data     → task created → succeeded
  Step 2: generate-report → task created → succeeded
  Step 3: deliver         → task created → running
```

### 镜像模式

任务流观察外部创建的任务并保持流状态同步，不控制任务创建。当任务来自 cron 作业、CLI 命令或其他来源，且你希望统一视图跟踪其集体进度时很有用。

示例：三个独立 cron 作业共同构成"晨间运维"例行程序。镜像流跟踪其集体进度而不控制它们的运行时间或方式。

## 持久状态和修订版本跟踪

每个流持久化自己的状态并跟踪修订版本，使进度可在 Gateway 重启后存活。修订版本跟踪在多个来源试图同时推进同一流时启用冲突检测。

流注册表使用带有限预写日志维护的 SQLite，包括周期性和关闭检查点，使长期运行的 Gateway 不会保留无界的 `registry.sqlite-wal` 附属文件。

## 取消行为

`openclaw tasks flow cancel` 在流上设置粘性取消意图。流内的活跃任务被取消，不启动新步骤。取消意图跨重启持久化，因此即使 Gateway 在所有子任务终止前重启，已取消的流仍保持取消状态。

## CLI 命令

```bash
# 列出活跃和最近的流
openclaw tasks flow list

# 显示特定流的详情
openclaw tasks flow show <lookup>

# 取消运行中的流及其活跃任务
openclaw tasks flow cancel <lookup>
```

## 流与任务的关系

流协调任务，而非替代它们。单个流在其生命周期内可能驱动多个后台任务。使用 `openclaw tasks` 检查单个任务记录，使用 `openclaw tasks flow` 检查编排流。

## 相关

- [后台任务](/automation/tasks)——流协调的分离工作账本
- [CLI: tasks](/cli/tasks)——`openclaw tasks flow` CLI 命令参考
- [Automation 概览](/automation)——所有自动化机制一览
- [定时任务](/automation/cron-jobs)——可能流入流的调度作业
