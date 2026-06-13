# Workboard 插件

## 架构精读

> 跳过不影响阅读翻译正文。

### 为什么不直接用 Jira/Linear？

Workboard 有意收窄：它只追踪单个 OpenClaw Gateway 的本地运维工作,不是 GitHub Issues、Linear、Jira 或其他团队项目管理系统的替代品。就像便利贴板和项目管理软件的区别——前者贴在显示器边上看一眼就知道状态,后者需要打开浏览器登录。

卡片认领模型也值得注意。Agent 认领一张卡片后,其他 agent 的工具调用被拒绝——除非持有认领令牌。这和 Kubernetes Pod 的 ownerReference 一个思路：谁在干活,谁就持有,别人不能抢。Dashboard 运维仍走正常 Gateway RPC 表面,可以恢复或重新分配卡片。

Dispatch 有意限制在 Gateway 本地。不派生任意操作系统进程；正常 OpenClaw 子 agent 会话持有执行。Dispatch 只做三件事：提升依赖就绪的卡片、清理陈旧认领、启动一小批 worker。这避免了"调度器比干活的人还复杂"的反模式。

---

Workboard 插件为 [Control UI](/web/control-ui) 添加可选看板式面板。用来收集 agent 大小的工作卡片、分配给 agent、从一张卡片追踪关联的后台任务、运行和 dashboard 会话。

Workboard 有意做小。追踪单个 OpenClaw Gateway 的本地运维工作；不是 GitHub Issues、Linear、Jira 或其他团队项目管理系统的替代品。

## 默认状态

Workboard 是内置插件,默认禁用,除非在插件配置中启用。

启用方式：

```bash
openclaw plugins enable workboard
openclaw gateway restart
```

然后打开 dashboard：

```bash
openclaw dashboard
```

Workboard 标签出现在 dashboard 导航中。标签可见但插件被禁用或被 `plugins.allow` / `plugins.deny` 阻止时,视图显示插件不可用状态而非本地卡片数据。

## 卡片包含什么

每张卡片存储：

- 标题和笔记
- 状态：`triage`、`backlog`、`todo`、`scheduled`、`ready`、`running`、`review`、`blocked` 或 `done`
- 优先级：`low`、`normal`、`high` 或 `urgent`
- 标签
- 可选 agent id
- 可选关联任务、运行、会话或源 URL
- 从卡片启动的 Codex 或 Claude 运行的可选执行元数据
- 紧凑元数据：尝试、评论、链接、证明、artifact、自动化、附件、worker 日志、worker 协议状态、认领、诊断、通知、模板、归档状态和陈旧会话检测
- 近期卡片事件：创建、移动、关联、认领、心跳、尝试、证明、artifact、诊断、通知、分发、归档、陈旧或 agent 更新变更

卡片存储在插件的 Gateway 状态中。位于 Gateway 状态目录本地,随该 Gateway 的其他 OpenClaw 状态一起移动。

Workboard 保持每卡片紧凑元数据,运维无需打开关联会话即可看到卡片在看板上的移动轨迹。事件、尝试摘要、证明片段、相关链接、评论、归档标记和陈旧会话标记有意作为本地元数据；不替代会话转录或 GitHub issue 历史。

## 卡片执行和任务

未关联卡片可从卡片启动工作。自主启动使用 Gateway 的任务追踪 agent 运行路径,然后 Workboard 将结果任务、运行 id 和会话键关联回卡片。启动使用 Gateway 配置的默认 agent 和模型。Codex 和 Claude 动作是可选的显式模型选择：

- Run Codex 或 Run Claude 启动任务支持的 agent 运行,发送卡片提示,将卡片标记为 `running`。
- Open Codex 或 Open Claude 创建关联 dashboard 会话但不发送卡片提示也不移动卡片,可在保持附着看板的同时手动工作。

执行元数据在卡片上存储所选引擎、模式、模型 ref、会话键、运行 id、可用时的任务 id 和生命周期状态。Codex 执行用 `openai/gpt-5.5`；Claude 执行用 `anthropic/claude-sonnet-4-6`。

每次关联执行还在同一卡片记录上记录尝试摘要。尝试摘要保留引擎、模式、模型、运行 id、时间戳、状态和滚动失败计数,重复失败在看板上保持可见。

Dashboard 从 Gateway 任务账本刷新任务状态并按任务 id、运行 id 或关联会话键将任务匹配回卡片。任务排队或运行时,卡片生命周期显示活跃任务状态。任务完成、失败、超时或取消时,卡片生命周期使用和关联会话相同的生命周期同步移向 review 或 blocked 状态。

## Agent 协调

Workboard 还暴露可选 agent 工具供看板感知工作流使用：

- `workboard_list` 列出紧凑卡片含认领和诊断状态,可选看板过滤。
- `workboard_read` 返回单张卡片加有界 worker 上下文,由笔记、尝试、评论、链接、证明、artifact、父级结果、近期分配工作和活跃诊断构建。
- `workboard_create` 创建卡片,可选父级、租户、skill、看板、工作区元数据、幂等键、运行时限制和重试预算。
- `workboard_link` 将父卡片关联到子卡片。子卡片保持 `todo` 直到每个父级到达 `done`；然后分发提升将其移到 `ready`。
- `workboard_claim` 为调用 agent 认领卡片并将 backlog、todo 或 ready 卡片移入 `running`。
- `workboard_heartbeat` 在较长运行期间刷新认领心跳。
- `workboard_release` 在完成、暂停或交接后释放认领,可将卡片移到下一状态。
- `workboard_complete` 和 `workboard_block` 是结构化生命周期工具,用于最终摘要、证明、artifact、已创建卡片清单和阻断原因。已创建卡片清单必须引用关联回已完成卡片的卡片,防止幽灵子卡片进入摘要。
- `workboard_attachment_add`、`workboard_attachment_read` 和 `workboard_attachment_delete` 在插件 SQLite 状态中存储小卡片附件,在卡片上索引,并在 worker 上下文中暴露。
- `workboard_worker_log` 和 `workboard_protocol_violation` 记录 worker 日志行,并在自动化工人未调用 `workboard_complete` 或 `workboard_block` 就停止时阻断卡片。
- `workboard_board_create`、`workboard_board_archive` 和 `workboard_board_delete` 管理持久化看板元数据如显示名、描述、归档状态和默认工作区。
- `workboard_runs` 返回卡片上存储的持久化运行尝试历史。
- `workboard_specify` 将粗略 triage 或 backlog 卡片转化为澄清的 `todo` 卡片并在卡片上记录规格摘要。
- `workboard_decompose` 将父编排卡片扇出为关联子级,继承看板和租户元数据,可用已创建卡片清单完成父级。
- `workboard_notify_subscribe`、`workboard_notify_list`、`workboard_notify_events`、`workboard_notify_advance` 和 `workboard_notify_unsubscribe` 在插件状态中管理通知订阅。事件读取可重放；advance 工具移动持久游标,调用者可恢复而不丢失或重复读取已完成、失败或陈旧卡片事件。
- `workboard_boards`、`workboard_stats`、`workboard_promote`、`workboard_reassign`、`workboard_reclaim`、`workboard_comment`、`workboard_proof`、`workboard_unblock` 和 `workboard_dispatch` 让 agent 检查看板命名空间、查看队列统计、恢复卡住的工作、添加交接笔记、附着证明或 artifact 引用、将受阻工作移回 `todo`、推动依赖提升或陈旧认领清理。

已认领卡片拒绝来自其他 agent 的 agent 工具变更,除非调用者持有 `workboard_claim` 返回的认领令牌。Dashboard 运维仍使用正常 Gateway RPC 表面,可恢复或重新分配卡片。

Workboard 在 OpenClaw 状态目录下的插件持有的关系 SQLite 数据库中存储持久化看板数据。看板、卡片、标签、生命周期事件、运行尝试、评论等均在 Workboard 表中持久化,而非插件键值条目。卡片导出仍保留看板叙事而不内联附件 blob 内容。

`.28` 版本使用过 Workboard 的安装可运行 `openclaw doctor --fix` 将发布的遗留插件状态命名空间（`workboard.cards`、`workboard.boards` 和 `workboard.notify`）迁移到关系数据库。存在遗留 `workboard.attachments` 命名空间时,doctor 也迁移那些附件 blob。

Workboard 诊断从本地卡片元数据计算。内置检查标记等待过久的已分配卡片、无近期心跳的运行中卡片、需要关注的受阻卡片。还标记重复失败、无证明的已完成卡片和仅有松散会话关联的运行中卡片。

分发有意限制在 Gateway 本地。不派生任意操作系统进程；正常 OpenClaw 子 agent 会话持有执行。分发操作提升依赖就绪的卡片、在 ready 卡片上记录分发元数据、阻止过期认领或超时运行。还将看板配置的 triage 卡片标记为编排候选,然后认领一小批 ready 卡片并通过 Gateway 子 agent 运行时启动 worker 运行。已分配卡片使用 `agent:<id>:subagent:workboard-*` worker 会话键；未分配卡片使用无作用域 `subagent:workboard-*` 键,Gateway 仍解析配置的默认 agent。Worker 获得有界卡片上下文加通过 Workboard 工具心跳、完成或阻止卡片所需的认领令牌。

### 分发 worker 选择

每次分发默认最多启动三个 worker。Ready 卡片按优先级、位置和创建时间排序,然后过滤避免重复活跃所有权。一次分发在同一 pass 中对给定 owner 或 agent 只启动一张卡片,跳过在看板上已有运行或 review 工作的 owner。

已归档卡片、有活跃认领的卡片和非 `ready` 状态的卡片不被选为 worker 启动。它们仍可能受分发数据侧影响——陈旧认领、依赖提升或超时清理适用时。

### Worker 提示和生命周期

Worker 提示包含卡片标题、有界笔记和上下文、分配的看板和 Workboard worker 协议。还包含认领 owner 和认领令牌,worker 可调用 `workboard_heartbeat`、`workboard_complete` 或 `workboard_block` 而不被其他参与者接管卡片。

Worker 成功启动时 Workboard 在卡片上存储会话键、运行 id、引擎、模式、模型标签、状态和 worker 日志。会话键对看板和卡片确定,重复分发路由回同一 worker 通道而非创建无关会话。

卡片认领后 worker 无法启动时 Workboard 阻止卡片、清除认领、记录运行启动失败并追加 worker 日志行。该失败在 dashboard、CLI JSON、agent 工具和卡片诊断中可见。

### 分发入口

Ready 卡片 worker 启动可从以下入口发生：

- Dashboard 分发操作
- `openclaw workboard dispatch`
- 命令能力频道上的 `/workboard dispatch`

三个入口在 Gateway 可用时都使用 Gateway 子 agent 运行时。CLI 有一个额外运维后备：Gateway 离线或不暴露 Workboard 分发方法且未提供显式 `--url` 或 `--token` 目标时,对本地 SQLite 状态运行仅数据分发。该后备可提升依赖、清理陈旧认领和阻止超时运行,但不能启动 worker。

看板元数据可包含编排设置如 `autoDecompose`、`autoDecomposePerDispatch`、`defaultAssignee` 和 `orchestratorProfile`。OpenClaw 记录编排意图并在 worker 上下文中暴露；实际规格和分解仍通过正常 Workboard 工具发生。

## CLI 和斜杠命令

插件注册根 CLI 命令：

```bash
openclaw workboard list
openclaw workboard create "Fix stale card lifecycle" --priority high --labels bug,workboard
openclaw workboard show <card-id>
openclaw workboard dispatch
```

`openclaw workboard dispatch` 调用运行中的 Gateway,worker 启动使用和 dashboard 相同的子 agent 运行时。Gateway 不可用时回落到仅数据分发,依赖提升、陈旧认领清理和超时阻止仍可运行。认证、权限和验证失败仍作为命令错误浮现,显式 `--url` 或 `--token` 目标的失败也是。

`/workboard` 斜杠命令支持相同紧凑运维路径：`/workboard list`、`/workboard show <card-id>`、`/workboard create <title>` 和 `/workboard dispatch`。List 和 show 是授权命令发送者的读操作。Create 和 dispatch 需要聊天表面上的 owner 状态或持有 `operator.write` 或 `operator.admin` 的 Gateway 客户端。

命令标志、JSON 输出、Gateway 后备行为、无歧义 id 前缀处理、分发选择规则和故障排查见 [Workboard CLI](/cli/workboard)。

## 会话生命周期同步

卡片可关联到已有 dashboard 会话或从卡片启动工作时创建的会话。关联卡片内联显示会话生命周期：运行中、陈旧、关联空闲、已完成、失败或缺失。

关联会话缺失时卡片保持关联提供上下文,仍提供启动控制,可重启工作进入新 dashboard 会话。活跃关联会话停止报告近期活动时 Workboard 将卡片标记陈旧并存储标记为卡片元数据,直到生命周期清除。

也可从 Sessions 标签用 Add to Workboard 捕获已有 dashboard 会话。卡片关联到该会话,使用会话标签或近期用户提示作为标题,从近期用户提示加聊天历史可用时的最新助手响应播种笔记。

Workboard 在卡片仍处于活跃工作状态时跟踪关联会话：

- 活跃关联会话 -> `running`
- 已完成关联会话 -> `review`
- 失败、终止、超时或中止的关联会话 -> `blocked`

手动 review 状态优先。将卡片移到 `review`、`blocked` 或 `done` 后 Workboard 停止自动移动该卡片,直到移回 `todo` 或 `running`。

## Dashboard 工作流

1. 在 Control UI 中打开 Workboard 标签。
2. 创建卡片,含标题、笔记、优先级、标签、可选 agent 和可选关联会话。
3. 或打开 Sessions 选择 Add to Workboard 用于已有会话。
4. 在列间拖动卡片或聚焦卡片上的紧凑状态控件并使用其菜单或 ArrowLeft/ArrowRight。
5. 从卡片启动工作以创建或复用 dashboard 会话。
6. Agent 工作时从卡片打开关联会话。
7. 让生命周期同步将运行中的工作移入 review 或 blocked,接受后手动移到 done。

启动卡片使用正常 Gateway 会话。Workboard 插件仅存储卡片元数据和关联；对话转录、模型选择和运行生命周期由常规会话系统持有。

活跃关联卡片上用 Stop 中止活跃会话运行。Workboard 将该卡片标记 `blocked` 保持可见以便后续跟进。

新卡片可从 Workboard 模板开始,用于 bug 修复、文档、发布、PR review 或插件工作。模板预填标题、笔记、标签和优先级,所选模板 id 存储为卡片元数据。

## 权限

插件在 `workboard.*` 命名空间下注册 Gateway RPC 方法：

- `workboard.cards.list` 需要 `operator.read`
- `workboard.cards.export` 需要 `operator.read`
- `workboard.cards.diagnostics` 需要 `operator.read`
- `workboard.cards.diagnostics.refresh` 需要 `operator.write`
- 附件 list/get 和通知事件读取需要 `operator.read`
- 通知游标推进需要 `operator.write`
- create、update、move、delete、comment、link、依赖 link、proof、artifact、attachment add/delete、worker log、protocol violation、认领、heartbeat、release、complete、block、unblock、dispatch、bulk 和归档方法需要 `operator.write`

以只读运维访问连接的浏览器可检查看板但不能变更卡片。

## 配置

Workboard 当前无插件专属配置。用标准插件条目启用或禁用：

```json5
{
  plugins: {
    entries: {
      workboard: {
        enabled: true,
        config: {},
      },
    },
  },
}
```

再次禁用：

```bash
openclaw plugins disable workboard
openclaw gateway restart
```

## 故障排查

### 标签显示 Workboard 不可用

检查插件策略：

```bash
openclaw plugins inspect workboard --runtime --json
```

配置了 `plugins.allow` 时将 `workboard` 加入该允许列表。`plugins.deny` 包含 `workboard` 时在启用插件前移除。

### 卡片不保存

确认浏览器连接有 `operator.write` 访问。只读运维会话可列出卡片但不能创建、编辑、移动或删除。

### 启动卡片未打开预期会话

Workboard 创建到正常 dashboard 会话的关联。检查卡片的 agent id 和关联会话,然后打开 Sessions 或 Chat 视图检查实际运行状态。

### 分发未启动 worker

确认至少有一张无活跃认领的 `ready` 卡片：

```bash
openclaw workboard list --status ready
```

CLI 报告仅数据分发时启动或重启 Gateway 后重试。仅数据分发更新本地看板状态但不能启动子 agent worker 运行。

同一 owner 或 agent 的另一张卡片已在运行或等待 review 时卡片也可能被跳过。分发同一 owner 的更多工作前完成、阻止或释放该活跃工作。

## 相关

- [Control UI](/web/control-ui)
- [Workboard CLI](/cli/workboard)
- [Plugins](/tools/plugin)
- [Manage plugins](/plugins/manage-plugins)
- [Sessions](/concepts/session)
