# Skill Workshop

## 架构精读

> 跳过不影响阅读翻译正文。

### Agent 想创建新 skill——为什么不让它直接写 SKILL.md？

一个词：治理。让 agent 直接写文件等于给它无限创建"自定义指令"的权力,没有人类审查。这跟 PR 一个道理——代码不直接 push main,而是先开 PR,review 后 merge。

Skill Workshop 就是这个 PR 流程：agent 产出 `PROPOSAL.md`（等价于 diff）,人类决定是 apply（merge）还是 reject（close）。中间状态可以 revise（等价于"请修改"）。

安全设计的另一面是 hash 绑定：提案绑定了目标 skill 当前的 hash。如果你在提案 pending 期间手动改了 skill,提案自动变 过期——必须基于新版重新提案。防止"盲合并覆盖人工改动"。

扫描门控是最后一道闸：apply 前重新跑安全扫描,确保内容没在 revise 中被注入恶意内容。

---

> Skill Workshop is OpenClaw's governed path for creating and updating workspace skills.

Skill Workshop 是 OpenClaw 创建和更新工作区 skill 的治理路径。

> Agents and operators do not write active `SKILL.md` files directly through this path. They create a proposal first...

Agent 和运营者不通过此路径直接写活跃的 `SKILL.md` 文件。它们先创建**提案**。提案是包含拟议 skill 内容、目标绑定、扫描状态、hash、支撑文件元数据、回滚元数据的待定草案。只有 apply 后才变成活 skill。

> Skill Workshop writes workspace skills only...

Skill Workshop 只写工作区 skill。不变更内置、插件、ClawHub、额外根、受管、个人 agent、或系统 skill。

## 工作原理

> - Proposal first, Apply is the only live write, Workspace scoped, No clobber, Hash bound, Scanner gated, Recoverable, Consistent surfaces

- **提案优先:** 生成的 skill 内容存为 `PROPOSAL.md` 而非 `SKILL.md`。
- **Apply 是唯一活写入:** create、update、revise 不改活 skill。
- **工作区范围:** 创建目标是工作区 `skills/` 根。更新只允许对可写的工作区 skill。
- **不覆盖:** 目标 skill 已存在时 create 失败。
- **Hash 绑定:** 更新提案绑定当前目标 hash,活 skill 在 apply 前变了则提案变 过期。
- **扫描门控:** apply 前重跑扫描。
- **可恢复:** apply 在改活文件前写回滚元数据。
- **一致表面:** 聊天、CLI、Gateway 都调同一个 Skill Workshop 服务。

## 生命周期

```text
create/update -> pending
revise        -> pending
apply         -> applied
reject        -> rejected
quarantine    -> quarantined
target change -> 过期
```

只有 `pending` 提案能被 revise、apply、reject、或 quarantine。

## 聊天

> Ask the agent for the skill you want...

向 agent 要你想的 skill。agent 调 `skill_workshop` 返回提案 id。

创建:

```text
Make a skill called morning-catchup that runs my Monday inbox routine.
```

更新已有工作区 skill:

```text
Update trip-planning to also check seat maps before booking.
```

在待定提案上迭代:

```text
Show me the morning-catchup proposal.
Revise it to also flag anything marked urgent.
Apply the morning-catchup proposal.
```

> By default, agent-initiated `apply`, `reject`, and `quarantine` show an approval prompt...

默认 agent 发起的 `apply`、`reject`、`quarantine` 在执行前显示审批提示。受信环境中设 `skills.workshop.approvalPolicy` 为 `"auto"` 跳过提示。

## CLI

```bash
# 创建新 skill 提案
openclaw skills workshop propose-create \
  --name morning-catchup \
  --description "Daily inbox catch-up: triage, archive, surface, draft, plan" \
  --proposal ./PROPOSAL.md

# 为已有工作区 skill 创建更新提案
openclaw skills workshop propose-update trip-planning --proposal ./PROPOSAL.md

# 列出和检查
openclaw skills workshop list
openclaw skills workshop inspect <proposal-id>

# apply 前 revise
openclaw skills workshop revise <proposal-id> --proposal ./PROPOSAL.md

# 关闭提案
openclaw skills workshop apply <proposal-id>
openclaw skills workshop reject <proposal-id> --reason "Duplicate"
openclaw skills workshop quarantine <proposal-id> --reason "Needs security review"
```

## 提案内容

> While pending, the proposal is stored as `PROPOSAL.md` with proposal-only frontmatter:

待定时提案存为 `PROPOSAL.md`,有提案专属 frontmatter:

```markdown
---
name: "morning-catchup"
description: "Daily inbox catch-up: triage, archive, surface, draft, plan"
status: proposal
version: "v1"
date: "2026-05-30T00:00:00.000Z"
---
```

Apply 时 Skill Workshop 写活 `SKILL.md` 并移除提案专属字段:`status`、提案 `version`、提案 `date`。

## 支撑文件

> Use `--proposal-dir` when the proposed skill needs files beside `PROPOSAL.md`:

拟议 skill 需要 `PROPOSAL.md` 旁的文件时用 `--proposal-dir`:

```bash
openclaw skills workshop propose-create \
  --name weekly-update \
  --description "Friday wrap-up: stats, highlights, next week's top three" \
  --proposal-dir ./weekly-update-proposal
```

目录必须含 `PROPOSAL.md`。支撑文件必须在:

- `assets/`
- `examples/`
- `references/`
- `scripts/`
- `templates/`

> Skill Workshop scans, hashes, and stores support files with the proposal...

Skill Workshop 扫描、hash、存储支撑文件与提案一起。只在 apply 时写到活 `SKILL.md` 旁。

被拒绝的路径:绝对路径、隐藏段、路径遍历、重叠、提案目录可执行文件、非 UTF-8、null 字节、标准文件夹外。

## Agent 工具

> The model uses `skill_workshop`:

模型用 `skill_workshop`:

```text
action: create | update | revise | list | inspect | apply | reject | quarantine
```

> Agents must use `skill_workshop` for generated skill work...

Agent 必须用 `skill_workshop` 做生成的 skill 工作。不得通过 `write`、`edit`、`exec`、shell 命令、或直接文件系统操作来创建或改提案文件。

## 审批和自主性

```json5
{
  skills: {
    workshop: {
      autonomous: { enabled: false },
      approvalPolicy: "pending",
      maxPending: 50,
      maxSkillBytes: 40000,
    },
  },
}
```

- `autonomous.enabled`: 允许 OpenClaw 从成功轮次后的持久对话信号创建待定提案。默认 `false`。
- `approvalPolicy: "pending"`: agent 发起 `apply`/`reject`/`quarantine` 前需审批提示。
- `approvalPolicy: "auto"`: 跳过审批提示。agent 仍须调 action。
- `maxPending`: 每工作区限制待定和隔离提案数。
- `maxSkillBytes`: 限制提案正文大小。默认 `40000`。

提案 description 总是限 160 字节。

## Gateway 方法

```text
skills.proposals.list
skills.proposals.inspect
skills.proposals.create
skills.proposals.update
skills.proposals.revise
skills.proposals.apply
skills.proposals.reject
skills.proposals.quarantine
```

只读方法需 `operator.read`。变更方法需 `operator.admin`。

## 存储

```text
OPENCLAW_STATE_DIR/skill-workshop/
  proposals.json
  proposals/<proposal-id>/
    proposal.json
    PROPOSAL.md
    rollback.json
    assets/
    examples/
    references/
    scripts/
    templates/
```

默认 state 目录:`~/.openclaw`。

- `proposal.json`: 规范提案记录。
- `proposals.json`: 快速列表索引,可从提案文件夹重建。
- `PROPOSAL.md`: 待定 skill 提案。
- `rollback.json`: apply 改活文件前写的恢复元数据。

## 限制

- Description: 160 字节。
- 提案正文: `skills.workshop.maxSkillBytes`（默认 40,000）。
- 支撑文件: 每提案 64 个。
- 支撑文件大小: 每个 256 KB,总计 2 MB。
- 待定和隔离提案: 每工作区 `skills.workshop.maxPending`（默认 50）。

## 故障排查

| 问题                                   | 解决                                                  |
| -------------------------------------- | ----------------------------------------------------- |
| `Skill proposal description is too large` | 缩短 `description` 到 160 字节以下。                |
| `Skill proposal content is too large`  | 缩短提案正文或提高 `skills.workshop.maxSkillBytes`。 |
| `Target skill changed after proposal creation` | 基于当前目标 revise,或创建新提案。             |
| `Proposal scan failed`                 | 检查扫描发现,然后 revise 或 quarantine 提案。        |
| `Support file paths must be under...`  | 移动支撑文件到标准支撑文件夹下。                     |
| 提案不在列表中                         | 检查选中的 `--agent` 工作区和 `OPENCLAW_STATE_DIR`。 |

## 相关

- [Skills](/tools/skills) —— 加载顺序、优先级、可见性。
- [创建 skill](/tools/creating-skills) —— 手写 `SKILL.md` 基础。
- [Skills 配置](/tools/skills-config) —— 完整 `skills.workshop` schema。
- [Skills CLI](/cli/skills) —— `openclaw skills` 命令。
