# 定时任务

## 架构精读

> 跳过不影响阅读翻译正文。

### 为什么 cron 运行在 Gateway 进程内而非独立调度器？

OpenClaw 的 cron 是 Gateway 内置的调度器——作业定义、运行时状态和运行历史都持久化在共享 SQLite 状态数据库中。这就像 PostgreSQL 的 pg_cron 扩展而非独立的 Airflow 调度器——调度逻辑与数据层共处一个进程。好处是 Gateway 重启不会丢失调度状态；坏处是调度器无法独立于 Gateway 扩展。

第二个设计：四种执行样式。cron 作业可以选择 main（主会话）、isolated（隔离会话）、current（当前会话）或 custom（自定义会话）。isolated 每次运行创建全新会话，适合报告和后台任务；custom 跨运行持久化上下文，适合每日站会等需要历史的工作。这就像容器编排中的 Pod 策略——每次新建 vs 复用有状态 Pod。好处是不同的工作负载可以选择合适的隔离级别。

第三个边界：调度与执行的分离。cron 只负责"何时唤醒 agent"，不负责"agent 做什么"。实际工作由 agent 的常驻命令或提示文本定义。这就像 Quartz 调度器与业务逻辑的分离——调度器触发 Job，Job 内部逻辑自行管理。好处是调度策略变更不影响业务逻辑，反之亦然。

---

Cron 是 Gateway 的内置调度器。它持久化作业、在正确时间唤醒 agent，并可将输出交付回聊天 channel 或 webhook 端点。

## 快速开始

```bash
# 添加一次性提醒
openclaw cron create "2026-02-01T16:00:00Z" \
  --name "Reminder" \
  --session main \
  --system-event "Reminder: check the cron docs draft" \
  --wake now \
  --delete-after-run

# 检查作业
openclaw cron list
openclaw cron get <job-id>

# 查看运行历史
openclaw cron runs --id <job-id>
```

## 工作原理

- Cron 运行在 **Gateway 进程内部**（不在模型内部）
- 作业定义、运行时状态和运行历史持久化在 OpenClaw 的共享 SQLite 状态数据库中，重启不会丢失调度
- 升级时运行 `openclaw doctor --fix` 将旧版 JSON 文件导入 SQLite
- 所有 cron 执行创建[后台任务](/automation/tasks)记录
- Gateway 启动时，逾期的隔离 agent 轮次作业会被重新调度出 channel 连接窗口，而非立即重放
- 一次性作业（`--at`）默认在成功后自动删除
- 隔离 cron 运行在完成后尽力关闭其 `cron:<jobId>` 会话跟踪的浏览器标签/进程，防止分离的浏览器自动化遗留孤儿进程
- 如隔离 agent 轮次达到 `timeoutSeconds`，cron 中止底层 agent 运行并给予短暂清理窗口

## 调度类型

| 类型 | CLI 标志 | 描述 |
| --- | --- | --- |
| `at` | `--at` | 一次性时间戳（ISO 8601 或相对时间如 `20m`） |
| `every` | `--every` | 固定间隔 |
| `cron` | `--cron` | 5 字段或 6 字段 cron 表达式，可选 `--tz` |

无时区的时间戳视为 UTC。添加 `--tz Asia/Shanghai` 进行本地挂钟调度。

循环的整点表达式会自动错开最多 5 分钟以减少负载峰值。使用 `--exact` 强制精确时间或 `--stagger 30s` 指定显式窗口。

### 月日和周日使用 OR 逻辑

当 cron 表达式的月日和周日字段都非通配符时，匹配条件为**任一**字段匹配——而非两者同时。这是标准 Vixie cron 行为。

```
# 意图："每月15号且是周一的上午9点"
# 实际："每月15号的上午9点，以及每周一的上午9点"
0 9 15 * 1
```

要同时要求两个条件，使用 Croner 的 `+` 周日修饰符（`0 9 15 * +1`）或在一个字段上调度并在作业的提示或命令中守卫另一个字段。

## 执行样式

| 样式 | `--session` 值 | 运行环境 | 适用场景 |
| --- | --- | --- | --- |
| 主会话 | `main` | 专用 cron 唤醒通道 | 提醒、系统事件 |
| 隔离 | `isolated` | 专用 `cron:<jobId>` | 报告、后台任务 |
| 当前会话 | `current` | 创建时绑定 | 上下文感知的循环工作 |
| 自定义会话 | `session:custom-id` | 持久命名会话 | 基于历史的工作流 |

**主会话**作业将系统事件排入 cron 管理的运行通道，并可选地唤醒心跳。它们不会将常规 cron 轮次追加到人类聊天通道。**隔离**作业用全新会话运行专用 agent 轮次。**自定义会话**（`session:xxx`）跨运行持久化上下文，支持基于之前摘要的每日站会等工作流。

对于隔离作业，"全新会话"指每次运行使用新的转录/会话 id。OpenClaw 可能携带安全偏好（如思考/快速/详细设置、标签和显式用户选择的模型/认证覆盖），但不继承旧 cron 行的环境对话上下文。

## 隔离作业的负载选项

| 选项 | 描述 |
| --- | --- |
| `--message` | 提示文本（隔离作业必填） |
| `--model` | 模型覆盖 |
| `--thinking` | 思考级别覆盖 |
| `--no-bootstrap` | 跳过工作区引导文件注入 |
| `--tools` | 限制作业可用工具，如 `--tools exec,read` |

隔离作业的模型选择优先级：

1. Gmail 钩子模型覆盖（当运行来自 Gmail 且该覆盖被允许时）
2. 每作业负载 `model`
3. 用户选择的存储 cron 会话模型覆盖
4. Agent/默认模型选择

## 交付和输出

| 模式 | 行为 |
| --- | --- |
| `announce` | 如 agent 未发送则将最终文本回退交付到目标 |
| `webhook` | 将完成事件负载 POST 到 URL |
| `none` | 无运行器回退交付 |

使用 `--announce --channel telegram --to "-1001234567890"` 进行 channel 交付。对于 Telegram 论坛主题，使用 `-1001234567890:topic:123`。

对于隔离作业，聊天交付是共享的。如聊天路由可用，agent 可使用 `message` 工具，即使作业使用 `--no-deliver`。如 agent 发送到配置的/当前目标，OpenClaw 跳过回退 announce。否则 `announce`、`webhook` 和 `none` 仅控制运行器在 agent 轮次后如何处理最终回复。

## 输出语言

Cron 作业不从 channel、区域设置或之前的消息推断回复语言。将语言规则放在调度消息或模板中：

```bash
openclaw cron edit <jobId> \
  --message "Summarize the updates. Respond in Chinese; keep URLs, code, and product names unchanged."
```

## 相关

- [Automation](/automation)——所有自动化机制概览
- [后台任务](/automation/tasks)——分离工作的活动账本
- [常驻命令](/automation/standing-orders)——cron 调度的授权边界
- [钩子](/automation/hooks)——事件驱动脚本
