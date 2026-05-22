# Personal agent benchmark pack（个人 Agent 基准测试包）

> The Personal Agent Benchmark Pack is a small repo-backed QA scenario pack for local personal assistant workflows. It is not a generic model benchmark and it does not require a new runner. The pack reuses the private QA stack described in [QA overview](/concepts/qa-e2e-automation), the synthetic [QA channel](/channels/qa-channel), and the existing `qa/scenarios` markdown catalog.

Personal Agent Benchmark Pack 是一个仓库内置的、专门针对**本地个人助手场景**的 QA 场景包。它不是一份通用模型评测榜单，也不需要再新写一个测试运行器（runner）。这个包直接复用三样已有的东西：[QA 总览](/concepts/qa-e2e-automation) 里讲的私有 QA 技术栈、合成通道 [QA channel](/channels/qa-channel)，以及 `qa/scenarios` 下已有的 markdown 场景目录。

> The first pack is intentionally narrow:
>
> * fake personal reminders through local cron delivery
> * fake DM and thread reply routing through `qa-channel`
> * fake preference recall from the temporary QA workspace memory files
> * fake secret no-echo checks
> * safe read-backed tool followthrough after a short approval-style turn
> * approval denial stop behavior for a sensitive local read request
> * proof-backed task status reporting that keeps pending, blocked, and done separate

第一版的覆盖范围刻意做得很窄：

- 通过本地 cron 投递的、模拟个人提醒（fake personal reminders）
- 通过 `qa-channel` 路由的、模拟私聊和话题回复
- 从临时 QA 工作区记忆文件中召回的、模拟用户偏好
- 模拟密码 / 密钥的"不回显"检查（不应该把敏感信息原样吐出来）
- 简短的"待批准"轮次之后，能基于读到的真实信息正确跟进的工具调用
- 对一个敏感的本地读请求，批准被拒绝时是否能正确停下
- 任务状态汇报必须有据可查，并把"待办（pending）/ 受阻（blocked）/ 已完成（done）"清晰区分开

---

> ## Scenarios

## 场景（Scenarios）

> The machine-readable pack metadata lives in `extensions/qa-lab/src/scenario-packs.ts`. Run the pack with `--pack personal-agent`:

机器可读的包元数据放在 `extensions/qa-lab/src/scenario-packs.ts`。用 `--pack personal-agent` 跑这个包：

> ```bash
> OPENCLAW_ENABLE_PRIVATE_QA_CLI=1 pnpm openclaw qa suite \
>   --provider-mode mock-openai \
>   --pack personal-agent \
>   --concurrency 1
> ```

```bash
OPENCLAW_ENABLE_PRIVATE_QA_CLI=1 pnpm openclaw qa suite \
  --provider-mode mock-openai \
  --pack personal-agent \
  --concurrency 1
```

> `--pack` is additive with repeated `--scenario` flags. Explicit scenarios run first, then the pack scenarios run in `QA_PERSONAL_AGENT_SCENARIO_IDS` order with duplicates removed.

`--pack` 可以和多个 `--scenario` 标志叠加使用。执行顺序是：先跑显式指定的场景，再按 `QA_PERSONAL_AGENT_SCENARIO_IDS` 里的顺序跑包里的场景，重复的去掉。

> The pack is designed for `qa-channel` with `mock-openai` or another local QA provider lane. It should not be pointed at live chat services or real personal accounts.

这个包是为 `qa-channel` + `mock-openai`（或其他本地 QA provider 通道）设计的，**不应该**指向真实的聊天服务或真实的个人账号。

---

> ## Privacy Model

## 隐私模型

> The scenarios use only fake users, fake preferences, fake secrets, and the temporary QA gateway workspace created by the suite. They must not read or write real OpenClaw user memory, sessions, credentials, launch agents, global configs, or live gateway state.

所有场景只使用虚拟用户、虚拟偏好、虚拟密钥，以及测试套件临时创建的 QA 网关工作区。绝不能读写真实的 OpenClaw 用户记忆、会话、凭证、launchd agent、全局配置或正在运行的网关状态。

> Artifacts stay under the existing QA suite artifact directory and should be treated like test output. Redaction checks use fake markers so failures are safe to inspect and file in issues.

测试产物放在已有的 QA 套件产物目录下，应当作为测试输出对待。脱敏检查使用虚假的标记词（fake markers），所以即使测试失败，把产物贴进 issue 也是安全的。

---

> ## Extending The Pack

## 扩展这个包

> Add new cases under `qa/scenarios/personal/`, then add the scenario id to `QA_PERSONAL_AGENT_SCENARIO_IDS`. Keep each case small, local, deterministic in `mock-openai`, and focused on one personal assistant behavior.

把新的测试用例放在 `qa/scenarios/personal/` 下，然后把场景 id 加到 `QA_PERSONAL_AGENT_SCENARIO_IDS` 里。每个用例要做到：小、本地、在 `mock-openai` 下确定可重现，且只聚焦一种个人助手行为。

> Good follow-up candidates:
>
> * redacted trajectory export checks
> * local-only plugin workflow checks

后续值得加的方向：

- 脱敏后的运行轨迹（trajectory）导出检查
- 仅本地的插件工作流检查

> Avoid adding a new runner, plugin, dependency, live transport, or model judge until the scenario catalog has enough stable cases to justify that surface.

在场景目录积累出足够多稳定用例之前，**不要**轻易引入新的测试运行器、插件、依赖、真实通道或"模型当评委"机制——这些扩展只在确实需要时才加。
