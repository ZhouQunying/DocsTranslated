# Agent workspace

> The workspace is the agent's home. It is the only working directory used for file tools and for workspace context. Keep it private and treat it as memory.

工作区是 agent 的家。它是文件工具和工作区上下文用的唯一工作目录。保持它私有，把它当成记忆来对待。

> This is separate from `~/.openclaw/`, which stores config, credentials, and sessions.

它跟 `~/.openclaw/` 是分开的 ——`~/.openclaw/` 存配置、凭证和会话。

> <Warning>
>   The workspace is the **default cwd**, not a hard sandbox. Tools resolve relative paths against the workspace, but absolute paths can still reach elsewhere on the host unless sandboxing is enabled. If you need isolation, use [`agents.defaults.sandbox`](/gateway/sandboxing) (and/or per-agent sandbox config).
>
>   When sandboxing is enabled and `workspaceAccess` is not `"rw"`, tools operate inside a sandbox workspace under `~/.openclaw/sandboxes`, not your host workspace.
> </Warning>

> **警告**：工作区是**默认 cwd**，不是硬沙盒。工具按工作区解析相对路径，但绝对路径仍然可以触达宿主机其他位置 —— 除非启用沙盒。需要隔离时用 [`agents.defaults.sandbox`](/gateway/sandboxing)（以及 / 或者按 agent 的 sandbox 配置）。
>
> 启用沙盒且 `workspaceAccess` 不是 `"rw"` 时，工具在 `~/.openclaw/sandboxes` 下的沙盒工作区里干活，不是你宿主机的工作区。

---

> ## Default location

## 默认位置

> * Default: `~/.openclaw/workspace`
> * If `OPENCLAW_PROFILE` is set and not `"default"`, the default becomes `~/.openclaw/workspace-<profile>`.
> * Override in `~/.openclaw/openclaw.json`:

- 默认：`~/.openclaw/workspace`。
- 设了 `OPENCLAW_PROFILE` 且不是 `"default"` 时，默认值变成 `~/.openclaw/workspace-<profile>`。
- 在 `~/.openclaw/openclaw.json` 里覆盖：

> ```json5
> {
>   agents: {
>     defaults: {
>       workspace: "~/.openclaw/workspace",
>     },
>   },
> }
> ```

```json5
{
  agents: {
    defaults: {
      workspace: "~/.openclaw/workspace",
    },
  },
}
```

> `openclaw onboard`, `openclaw configure`, or `openclaw setup` will create the workspace and seed the bootstrap files if they are missing.

`openclaw onboard`、`openclaw configure` 或 `openclaw setup` 会在工作区缺失时创建它，并把引导文件填上去。

> <Note>
>   Sandbox seed copies only accept regular in-workspace files; symlink/hardlink aliases that resolve outside the source workspace are ignored.
> </Note>

> **提示**：沙盒种子复制只接受工作区内的常规文件；解析到源工作区外的符号链接 / 硬链接别名会被忽略。

> If you already manage the workspace files yourself, you can disable bootstrap file creation:
>
> ```json5
> { agents: { defaults: { skipBootstrap: true } } }
> ```

如果工作区文件你自己管，可以禁用引导文件创建：

```json5
{ agents: { defaults: { skipBootstrap: true } } }
```

---

> ## Extra workspace folders

## 多余的工作区目录

> Older installs may have created `~/openclaw`. Keeping multiple workspace directories around can cause confusing auth or state drift, because only one workspace is active at a time.

旧版安装可能创建过 `~/openclaw`。保留多个工作区目录会造成认证或状态漂移的混乱 —— 同时只有一个工作区是活动的。

> <Note>
>   **Recommendation:** keep a single active workspace. If you no longer use the extra folders, archive or move them to Trash (for example `trash ~/openclaw`). If you intentionally keep multiple workspaces, make sure `agents.defaults.workspace` points to the active one.
>
>   `openclaw doctor` warns when it detects extra workspace directories.
> </Note>

> **提示**：**建议**保留一个活动工作区。多余目录不再用就归档或丢到回收站（例如 `trash ~/openclaw`）。刻意保留多个工作区时，确认 `agents.defaults.workspace` 指向当前活动的那个。
>
> 检测到额外工作区目录时 `openclaw doctor` 会发警告。

---

> ## Workspace file map

## 工作区文件地图

> These are the standard files OpenClaw expects inside the workspace:

OpenClaw 在工作区里期望的标准文件：

> [展开: AGENTS.md - operating instructions]
>
> Operating instructions for the agent and how it should use memory. Loaded at the start of every session. Good place for rules, priorities, and "how to behave" details.

[展开：AGENTS.md —— 操作说明]

agent 的操作说明、它应该怎么用记忆。每个会话开始时加载。适合放规则、优先级、"该怎么行事"的细节。

> [展开: SOUL.md - persona and tone]
>
> Persona, tone, and boundaries. Loaded every session. Guide: [SOUL.md personality guide](/concepts/soul).

[展开：SOUL.md —— 人设和语气]

人设、语气和边界。每个会话都加载。指南：[SOUL.md 人设指南](/concepts/soul)。

> [展开: USER.md - who the user is]
>
> Who the user is and how to address them. Loaded every session.

[展开：USER.md —— 用户是谁]

用户是谁、怎么称呼。每个会话都加载。

> [展开: IDENTITY.md - name, vibe, emoji]
>
> The agent's name, vibe, and emoji. Created/updated during the bootstrap ritual.

[展开：IDENTITY.md —— 名字、气质、emoji]

agent 的名字、气质、emoji。在引导仪式期间创建 / 更新。

> [展开: TOOLS.md - local tool conventions]
>
> Notes about your local tools and conventions. Does not control tool availability; it is only guidance.

[展开：TOOLS.md —— 本地工具约定]

关于你本地工具和约定的笔记。不决定工具是否可用，只是给出指引。

> [展开: HEARTBEAT.md - heartbeat checklist]
>
> Optional tiny checklist for heartbeat runs. Keep it short to avoid token burn.

[展开：HEARTBEAT.md —— 心跳清单]

可选的、心跳运行用的小清单。保持简短，避免烧 token。

> [展开: BOOT.md - startup checklist]
>
> Optional startup checklist run automatically on gateway restart (when [internal hooks](/automation/hooks) are enabled). Keep it short; use the message tool for outbound sends.

[展开：BOOT.md —— 启动清单]

可选的启动清单，Gateway 重启时自动跑（启用 [内置钩子](/automation/hooks) 后）。保持简短；要发出去的内容用消息工具发。

> [展开: BOOTSTRAP.md - first-run ritual]
>
> One-time first-run ritual. Only created for a brand-new workspace. Delete it after the ritual is complete.

[展开：BOOTSTRAP.md —— 首次运行仪式]

一次性的首次运行仪式。只为全新工作区创建。仪式完成后删掉。

> [展开: memory/YYYY-MM-DD.md - daily memory log]
>
> Daily memory log (one file per day). Recommended to read today + yesterday on session start.

[展开：memory/YYYY-MM-DD.md —— 日常记忆日志]

每日记忆日志（一天一个文件）。推荐会话开始时读今天 + 昨天。

> [展开: MEMORY.md - curated long-term memory (optional)]
>
> Curated long-term memory: durable facts, preferences, decisions, and short summaries. Keep detailed logs in `memory/YYYY-MM-DD.md` so memory tools can retrieve them on demand without injecting them into every prompt. Only load `MEMORY.md` in the main, private session (not shared/group contexts). See [Memory](/concepts/memory) for the workflow and automatic memory flush.

[展开：MEMORY.md —— 精选的长期记忆（可选）]

精选的长期记忆：长期事实、偏好、决策、简短总结。详细日志放到 `memory/YYYY-MM-DD.md`，让记忆工具按需检索，不必每条 prompt 都注入。`MEMORY.md` 只在主、私有会话里加载（不要在共享 / 群上下文里）。流程和自动 memory flush 见 [记忆](/concepts/memory)。

> [展开: skills/ - workspace skills (optional)]
>
> Workspace-specific skills. Highest-precedence skill location for that workspace. Overrides project agent skills, personal agent skills, managed skills, bundled skills, and `skills.load.extraDirs` when names collide.

[展开：skills/ —— 工作区 skill（可选）]

工作区专属的 skill。该工作区里 skill 优先级最高的位置。重名时会覆盖 project agent skill、personal agent skill、managed skill、bundled skill 和 `skills.load.extraDirs`。

> [展开: canvas/ - Canvas UI files (optional)]
>
> Canvas UI files for node displays (for example `canvas/index.html`).

[展开：canvas/ —— Canvas UI 文件（可选）]

节点显示用的 Canvas UI 文件（比如 `canvas/index.html`）。

> <Note>
>   If any bootstrap file is missing, OpenClaw injects a "missing file" marker into the session and continues. Large bootstrap files are truncated when injected; adjust limits with `agents.defaults.bootstrapMaxChars` (default: 12000) and `agents.defaults.bootstrapTotalMaxChars` (default: 60000). `openclaw setup` can recreate missing defaults without overwriting existing files.
> </Note>

> **提示**：任何引导文件缺失时，OpenClaw 在会话里注入一条"缺失文件"标记并继续运行。大引导文件注入时会被截断；通过 `agents.defaults.bootstrapMaxChars`（默认 12000）和 `agents.defaults.bootstrapTotalMaxChars`（默认 60000）调上限。`openclaw setup` 可以在不覆盖现有文件的前提下重建缺失的默认文件。

---

> ## What is NOT in the workspace

## 哪些**不**在工作区里

> These live under `~/.openclaw/` and should NOT be committed to the workspace repo:
>
> * `~/.openclaw/openclaw.json` (config)
> * `~/.openclaw/agents/<agentId>/agent/auth-profiles.json` (model auth profiles: OAuth + API keys)
> * `~/.openclaw/agents/<agentId>/agent/codex-home/` (per-agent Codex runtime account, config, skills, plugins, and native thread state)
> * `~/.openclaw/credentials/` (channel/provider state plus legacy OAuth import data)
> * `~/.openclaw/agents/<agentId>/sessions/` (session transcripts + metadata)
> * `~/.openclaw/skills/` (managed skills)

下面这些放在 `~/.openclaw/` 下，**不要**提交到工作区仓库：

- `~/.openclaw/openclaw.json`（配置）
- `~/.openclaw/agents/<agentId>/agent/auth-profiles.json`（模型认证 profile：OAuth + API key）
- `~/.openclaw/agents/<agentId>/agent/codex-home/`（按 agent 的 Codex 运行时账号、配置、skill、插件、原生线程状态）
- `~/.openclaw/credentials/`（通道 / provider 状态 + 旧版 OAuth 导入数据）
- `~/.openclaw/agents/<agentId>/sessions/`（会话 transcript + 元数据）
- `~/.openclaw/skills/`（managed skill）

> If you need to migrate sessions or config, copy them separately and keep them out of version control.

要迁移会话或配置时，单独复制，让它们不进版本控制。

---

> ## Git backup (recommended, private)

## Git 备份（推荐，私有）

> Treat the workspace as private memory. Put it in a **private** git repo so it is backed up and recoverable.

把工作区当私有记忆来对待。放到一个**私有** git 仓库里做备份和可恢复。

> Run these steps on the machine where the Gateway runs (that is where the workspace lives).

在 Gateway 跑的那台机器上执行下面的步骤（工作区就在那）。

> [步骤 1: Initialize the repo]
>
> If git is installed, brand-new workspaces are initialized automatically. If this workspace is not already a repo, run:
>
> ```bash
> cd ~/.openclaw/workspace
> git init
> git add AGENTS.md SOUL.md TOOLS.md IDENTITY.md USER.md HEARTBEAT.md memory/
> git commit -m "Add agent workspace"
> ```

[步骤 1：初始化仓库]

装了 git 的话，全新工作区会自动初始化。这个工作区还没成为 repo 时跑：

```bash
cd ~/.openclaw/workspace
git init
git add AGENTS.md SOUL.md TOOLS.md IDENTITY.md USER.md HEARTBEAT.md memory/
git commit -m "Add agent workspace"
```

> [步骤 2: Add a private remote]

[步骤 2：加一个私有 remote]

> [标签页: GitHub web UI]
>
> 1. Create a new **private** repository on GitHub.
> 2. Do not initialize with a README (avoids merge conflicts).
> 3. Copy the HTTPS remote URL.
> 4. Add the remote and push:
>
> ```bash
> git branch -M main
> git remote add origin <https-url>
> git push -u origin main
> ```

[标签页：GitHub 网页]

1. 在 GitHub 新建一个**私有**仓库。
2. 不要勾初始化 README（避免合并冲突）。
3. 复制 HTTPS remote URL。
4. 加 remote 并 push：

```bash
git branch -M main
git remote add origin <https-url>
git push -u origin main
```

> [标签页: GitHub CLI (gh)]
>
> ```bash
> gh auth login
> gh repo create openclaw-workspace --private --source . --remote origin --push
> ```

[标签页：GitHub CLI（gh）]

```bash
gh auth login
gh repo create openclaw-workspace --private --source . --remote origin --push
```

> [标签页: GitLab web UI]
>
> 1. Create a new **private** repository on GitLab.
> 2. Do not initialize with a README (avoids merge conflicts).
> 3. Copy the HTTPS remote URL.
> 4. Add the remote and push:
>
> ```bash
> git branch -M main
> git remote add origin <https-url>
> git push -u origin main
> ```

[标签页：GitLab 网页]

1. 在 GitLab 新建一个**私有**仓库。
2. 不要勾初始化 README（避免合并冲突）。
3. 复制 HTTPS remote URL。
4. 加 remote 并 push：

```bash
git branch -M main
git remote add origin <https-url>
git push -u origin main
```

> [步骤 3: Ongoing updates]
>
> ```bash
> git status
> git add .
> git commit -m "Update memory"
> git push
> ```

[步骤 3：日常更新]

```bash
git status
git add .
git commit -m "Update memory"
git push
```

---

> ## Do not commit secrets

## 不要把密钥提交进去

> <Warning>
>   Even in a private repo, avoid storing secrets in the workspace:
>
>   * API keys, OAuth tokens, passwords, or private credentials.
>   * Anything under `~/.openclaw/`.
>   * Raw dumps of chats or sensitive attachments.
>
>   If you must store sensitive references, use placeholders and keep the real secret elsewhere (password manager, environment variables, or `~/.openclaw/`).
> </Warning>

> **警告**：即便是私有仓库，工作区里也不要存密钥：
>
> - API key、OAuth token、密码或私有凭证。
> - 任何在 `~/.openclaw/` 下的东西。
> - 聊天的原始 dump 或敏感附件。
>
> 必须留下敏感引用时，写占位符，把真正的密钥放在别处（密码管理器、环境变量或 `~/.openclaw/`）。

> Suggested `.gitignore` starter:
>
> ```gitignore
> .DS_Store
> .env
> **/*.key
> **/*.pem
> **/secrets*
> ```

`.gitignore` 起步建议：

```gitignore
.DS_Store
.env
**/*.key
**/*.pem
**/secrets*
```

---

> ## Moving the workspace to a new machine

## 把工作区搬到新机器

> [步骤 1: Clone the repo]
>
> Clone the repo to the desired path (default `~/.openclaw/workspace`).

[步骤 1：克隆 repo]

把 repo 克隆到目标路径（默认 `~/.openclaw/workspace`）。

> [步骤 2: Update config]
>
> Set `agents.defaults.workspace` to that path in `~/.openclaw/openclaw.json`.

[步骤 2：更新配置]

在 `~/.openclaw/openclaw.json` 里把 `agents.defaults.workspace` 设成这个路径。

> [步骤 3: Seed missing files]
>
> Run `openclaw setup --workspace <path>` to seed any missing files.

[步骤 3：填补缺失文件]

跑 `openclaw setup --workspace <path>` 把缺失文件填上。

> [步骤 4: Copy sessions (optional)]
>
> If you need sessions, copy `~/.openclaw/agents/<agentId>/sessions/` from the old machine separately.

[步骤 4：复制会话（可选）]

需要会话的话，单独把旧机器上的 `~/.openclaw/agents/<agentId>/sessions/` 拷过来。

---

> ## Advanced notes

## 高级说明

> * Multi-agent routing can use different workspaces per agent. See [Channel routing](/channels/channel-routing) for routing configuration.
> * If `agents.defaults.sandbox` is enabled, non-main sessions can use per-session sandbox workspaces under `agents.defaults.sandbox.workspaceRoot`.

- 多 agent 路由可以让每个 agent 用不同的工作区。路由配置见 [通道路由](/channels/channel-routing)。
- 启用 `agents.defaults.sandbox` 后，非 main 会话可以用 `agents.defaults.sandbox.workspaceRoot` 下按会话的沙盒工作区。

---

> ## Related

## 相关

> * [Heartbeat](/gateway/heartbeat) - HEARTBEAT.md workspace file
> * [Sandboxing](/gateway/sandboxing) - workspace access in sandboxed environments
> * [Session](/concepts/session) - session storage paths
> * [Standing orders](/automation/standing-orders) - persistent instructions in workspace files

- [Heartbeat](/gateway/heartbeat)：HEARTBEAT.md 工作区文件
- [沙盒](/gateway/sandboxing)：沙盒环境下的工作区访问
- [会话](/concepts/session)：会话存储路径
- [Standing orders](/automation/standing-orders)：工作区文件里的持久化指令
