# Agent bootstrapping

> Bootstrapping is the **first-run** ritual that prepares an agent workspace and collects identity details. It happens after onboarding, when the agent starts for the first time.

引导（bootstrapping）是**首次运行**的仪式，用来准备 agent 工作区并收集身份信息。它在 onboarding 之后、agent 第一次启动时发生。

---

> ## What bootstrapping does

## 引导做什么

> On the first agent run, OpenClaw bootstraps the workspace (default `~/.openclaw/workspace`):
>
> * Seeds `AGENTS.md`, `BOOTSTRAP.md`, `IDENTITY.md`, `USER.md`.
> * Runs a short Q\&A ritual (one question at a time).
> * Writes identity + preferences to `IDENTITY.md`, `USER.md`, `SOUL.md`.
> * Removes `BOOTSTRAP.md` when finished so it only runs once.

agent 第一次运行时，OpenClaw 引导工作区（默认 `~/.openclaw/workspace`）：

- 播种 `AGENTS.md`、`BOOTSTRAP.md`、`IDENTITY.md`、`USER.md`。
- 跑一个简短的问答仪式（一次一个问题）。
- 把身份和偏好写到 `IDENTITY.md`、`USER.md`、`SOUL.md`。
- 完成后删掉 `BOOTSTRAP.md`，让它只跑一次。

> For embedded/local model runs, OpenClaw keeps `BOOTSTRAP.md` out of the privileged system context. On the primary interactive first run, it still passes the file contents in the user prompt so models that do not reliably call the `read` tool can complete the ritual. If the current run cannot safely access the workspace, the agent gets a limited bootstrap note instead of a generic greeting.

对嵌入式 / 本地模型运行，OpenClaw 不把 `BOOTSTRAP.md` 放进受保护的系统上下文。主交互首次运行时仍然把文件内容放在用户 prompt 里，让那些不能稳定调 `read` 工具的模型也能完成仪式。当前运行无法安全访问工作区时，agent 会收到一条受限的引导备注，而不是一句泛泛的问候。

---

> ## Skipping bootstrapping

## 跳过引导

> To skip this for a pre-seeded workspace, run `openclaw onboard --skip-bootstrap`.

预先种好的工作区想跳过这一步，跑 `openclaw onboard --skip-bootstrap`。

---

> ## Where it runs

## 在哪里运行

> Bootstrapping always runs on the **gateway host**. If the macOS app connects to a remote Gateway, the workspace and bootstrapping files live on that remote machine.

引导始终在 **Gateway 宿主机**上跑。macOS App 连接远程 Gateway 时，工作区和引导文件都在那台远程机器上。

> <Note>
>   When the Gateway runs on another machine, edit workspace files on the gateway host (for example, `user@gateway-host:~/.openclaw/workspace`).
> </Note>

> **提示**：Gateway 在另一台机器上跑时，工作区文件要在 Gateway 宿主机上编辑（例如 `user@gateway-host:~/.openclaw/workspace`）。

---

> ## Related docs

## 相关文档

> * macOS app onboarding: [Onboarding](/start/onboarding)
> * Workspace layout: [Agent workspace](/concepts/agent-workspace)

- macOS App 的 onboarding：[Onboarding](/start/onboarding)
- 工作区布局：[Agent 工作区](/concepts/agent-workspace)
