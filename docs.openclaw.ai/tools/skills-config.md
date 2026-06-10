# Skills 配置

## 架构精读

> 跳过不影响阅读翻译正文。

### 为什么配一堆 skill 需要这么多层？

说白了,skill 配置要解决的核心问题是:**同一台机器上不同 agent 看到不同能力集**。

如果只有一个扁平列表,那要么全开要么全关。但实际场景是:写作 agent 只需要文档搜索,开发 agent 需要 GitHub + 天气,而安全审计 agent 什么 skill 都不该有。所以需要两层——全局 entries 控制"装没装、开没开",agent allowlist 控制"这个 agent 能不能看到"。

Install Policy 的设计特别有意思。为什么不把安装审批逻辑内建？因为每个组织的策略完全不同——有的按来源白名单,有的按签名验证,有的要走内部审批流。OpenClaw 选择了 Kubernetes Admission Webhook 的模式：stdin 进 JSON、stdout 出 allow/block,超时或异常一律拒绝。关键在于失败即拒绝——策略进程崩了不会变成"放行"。

符号链接信任边界也是防御性设计。workspace `skills/` 目录是隔离根,如果不检查符号链接指向,攻击者只需 `ln -s /etc/passwd skills/leak` 就能突破。`allowSymlinkTargets` 是显式放行,不在列表里的一律跳过。

---

> Most skills configuration lives under `skills` in `~/.openclaw/openclaw.json`...

多数 skill 配置在 `~/.openclaw/openclaw.json` 的 `skills` 下。Agent 级可见性在 `agents.defaults.skills` 和 `agents.list[].skills`。

```json5
{
  skills: {
    allowBundled: ["gemini", "peekaboo"],
    load: {
      extraDirs: ["~/Projects/agent-scripts/skills"],
      allowSymlinkTargets: ["~/Projects/manager/skills"],
      watch: true,
      watchDebounceMs: 250,
    },
    install: {
      preferBrew: true,
      nodeManager: "npm",
      allowUploadedArchives: false,
    },
    workshop: {
      autonomous: { enabled: false },
      approvalPolicy: "pending",
      maxPending: 50,
      maxSkillBytes: 40000,
    },
    entries: {
      "image-lab": {
        enabled: true,
        apiKey: { source: "env", provider: "default", id: "GEMINI_API_KEY" },
        env: { GEMINI_API_KEY: "GEMINI_KEY_HERE" },
      },
      peekaboo: { enabled: true },
      sag: { enabled: false },
    },
  },
}
```

> Note: For built-in image generation, use `agents.defaults.imageGenerationModel`...

注意：内置图片生成请用 `agents.defaults.imageGenerationModel` 加核心 `image_generate` 工具,而非 `skills.entries`。Skill entries 只用于自定义或第三方 skill 工作流。

## 加载（`skills.load`）

> Additional skill directories to scan...

`extraDirs`: 额外扫描的 skill 目录,优先级最低（在内置和插件 skill 之后）。路径支持 `~` 展开。

> Trusted real target directories that symlinked skill folders may resolve into...

`allowSymlinkTargets`: 符号链接 skill 文件夹可解析到的受信真实目标目录,即使符号链接本身在配置根之外。用于有意的兄弟仓库布局,如 `<workspace>/skills/manager -> ~/Projects/manager/skills`。保持列表精简——不要指向 `~` 或 `~/Projects` 这样的宽泛根。

> Watch skill folders and refresh the skills snapshot when `SKILL.md` files change...

`watch`: 监视 skill 文件夹,`SKILL.md` 变更时刷新 skill 快照。覆盖分组 skill 根下的嵌套文件。

> Debounce window for skill watcher events in milliseconds.

`watchDebounceMs`: Skill 监视器事件的防抖窗口,单位毫秒。

## 安装（`skills.install`）

> Prefer Homebrew installers when `brew` is available.

`preferBrew`: `brew` 可用时优先使用 Homebrew 安装器。

> Node package manager preference for skill installs...

`nodeManager`: Skill 安装的 Node 包管理器偏好。只影响 skill 安装——Gateway 运行时仍应使用 Node（不推荐 Bun 用于 WhatsApp/Telegram）。用 `openclaw setup --node-manager` 设置 npm、pnpm 或 bun；手动设 `"yarn"` 用于 Yarn 支持的 skill 安装。

> Allow trusted `operator.admin` Gateway clients to install private zip archives...

`allowUploadedArchives`: 允许受信 `operator.admin` Gateway 客户端安装通过 `skills.upload.*` 暂存的私有 zip 归档。正常 ClawHub 安装不需要此设置。

## 运营者安装策略（`security.installPolicy`）

> Use `security.installPolicy` when operators need a trusted local command to approve or block skill and plugin installs...

运营者需要受信本地命令来按主机策略审批或阻止 skill 和插件安装时,用 `security.installPolicy`。策略在 OpenClaw 暂存源材料之后、安装或更新继续之前运行。适用于 ClawHub skill、上传 skill、Git/本地 skill、skill 依赖安装器和插件安装/更新源。

```json5
{
  security: {
    installPolicy: {
      enabled: true,
      // 省略 targets 则覆盖所有支持的目标。
      targets: ["skill", "plugin"],
      exec: {
        source: "exec",
        command: "/usr/local/bin/openclaw-install-policy",
        args: ["--json"],
        timeoutMs: 10000,
        noOutputTimeoutMs: 10000,
        maxOutputBytes: 1048576,
        passEnv: ["OPENCLAW_STATE_DIR", "PATH"],
        env: { POLICY_MODE: "strict" },
        trustedDirs: ["/usr/local/bin"],
      },
    },
  },
}
```

> Enables operator-owned install policy. When enabled without a valid `exec` command, installs fail closed.

`enabled`: 启用运营者持有的安装策略。启用但无有效 `exec` 命令时,安装失败即拒绝。

> Optional target filter. When omitted, policy applies to every supported target...

`targets`: 可选目标过滤。省略时策略应用于所有支持目标,新安装不会意外变成放行。

> Absolute path to the trusted policy executable...

`exec.command`: 受信策略可执行文件的绝对路径。OpenClaw 不通过 shell 运行它,使用前验证路径。

> Static arguments passed after `command`.

`exec.args`: `command` 后追加的静态参数。

> Maximum wall-clock runtime for one policy decision.

`exec.timeoutMs`: 单次策略决策的最大挂钟时间。

> Maximum time without stdout or stderr output before the policy fails closed.

`exec.noOutputTimeoutMs`: 无 stdout 或 stderr 输出的最大时间,超时则失败即拒绝。

> Maximum combined stdout and stderr bytes accepted from the policy process.

`exec.maxOutputBytes`: 从策略进程接受的 stdout 和 stderr 最大合计字节数。

> Literal environment variables provided to the policy process.

`exec.env`: 提供给策略进程的字面环境变量。

> Environment variable names copied from the OpenClaw process into the policy process...

`exec.passEnv`: 从 OpenClaw 进程复制到策略进程的环境变量名。只传递命名的变量。

> Optional allowlist of directories that may contain the policy executable.

`exec.trustedDirs`: 可选,允许包含策略可执行文件的目录白名单。

> Bypasses command path ownership and permission checks...

`exec.skipPathChecks`: 绕过命令路径所有权和权限检查。仅在路径由其他机制保护时使用。

> Allows the configured command path to be a symlink...

`exec.allowSymlink`: 允许配置的命令路径为符号链接。解析目标仍须满足其他路径检查。解释器脚本参数必须是直接常规文件,非符号链接。

> The policy receives one JSON object on stdin...

策略在 stdin 收到一个 JSON 对象,含 `protocolVersion: 1`、`openclawVersion`、`targetType`、`targetName`、`sourcePath`、`sourcePathKind`、可选结构化 `source`、结构化 `origin` 和 `request`。必须在 stdout 写一个 JSON 对象：`{ "protocolVersion": 1, "decision": "allow" }` 或 `{ "protocolVersion": 1, "decision": "block", "reason": "..." }`。非零退出、超时、畸形 JSON、缺字段、不支持的协议版本均失败即拒绝。

> OpenClaw does not execute install policy during normal Gateway startup...

OpenClaw 正常 Gateway 启动时不执行安装策略。策略启用但不可用时安装失败即拒绝。`openclaw doctor` 执行静态验证,`openclaw doctor --deep` 对配置命令执行合成安装探测。

> Bulk updates apply policy per target...

批量更新按目标逐个应用策略：被阻止的 skill 或插件更新让该目标失败,不会禁用策略或跳过批次中后续目标。

示例 stdin：

```json
{
  "protocolVersion": 1,
  "openclawVersion": "2026.6.1",
  "targetType": "skill",
  "targetName": "weather",
  "sourcePath": "/var/folders/.../openclaw-skill-clawhub/root",
  "sourcePathKind": "directory",
  "source": {
    "kind": "clawhub",
    "authority": "openclaw",
    "mutable": false,
    "network": true
  },
  "origin": {
    "type": "clawhub",
    "registry": "https://clawhub.openclaw.ai",
    "slug": "weather",
    "version": "1.0.0"
  },
  "request": {
    "kind": "skill-install",
    "mode": "install",
    "requestedSpecifier": "clawhub:weather@1.0.0"
  },
  "skill": {
    "installId": "clawhub"
  }
}
```

最小策略命令：

```js
#!/usr/bin/env node

let input = "";
process.stdin.setEncoding("utf8");
process.stdin.on("data", (chunk) => {
  input += chunk;
});
process.stdin.on("end", () => {
  const request = JSON.parse(input);
  if (request.targetType === "plugin" && request.source?.kind === "local-path") {
    process.stdout.write(
      JSON.stringify({
        protocolVersion: 1,
        decision: "block",
        reason: "local plugin paths are not approved on this host",
      }),
    );
    return;
  }
  process.stdout.write(JSON.stringify({ protocolVersion: 1, decision: "allow" }));
});
```

## 内置 skill 白名单

> Optional allowlist for **bundled** skills only...

`allowBundled`: 可选,仅针对**内置** skill 的白名单。设置后只有列表中的内置 skill 有资格。受管、agent 级和工作区 skill 不受影响。

## 单 skill 条目（`skills.entries`）

> Keys under `entries` match the skill `name` by default...

`entries` 下的键默认匹配 skill `name`。若 skill 定义了 `metadata.openclaw.skillKey` 则用该键。连字符名需引号括起（JSON5 允许带引号键）。

> `false` disables the skill even when bundled or installed...

`<skill>.enabled`: `false` 禁用 skill,即使是内置或已安装。`coding-agent` 内置 skill 是 opt-in——设为 `true` 并确保安装且认证了 `claude`、`codex`、`opencode` 或其他支持的 CLI。

> Convenience field for skills that declare `metadata.openclaw.primaryEnv`...

`<skill>.apiKey`: 声明了 `metadata.openclaw.primaryEnv` 的 skill 的便捷字段。支持纯文本字符串或 SecretRef：`{ source: "env", provider: "default", id: "VAR_NAME" }`。

> Environment variables injected for the agent run...

`<skill>.env`: 为 agent 运行注入的环境变量。仅在进程中未设置该变量时注入。

> Optional bag for custom per-skill configuration fields.

`<skill>.config`: 可选,自定义单 skill 配置字段包。

## Agent 白名单（`agents`）

> Use agent config when you want the same machine/workspace skill roots but a different visible skill set per agent.

同一机器/工作区 skill 根但每个 agent 需要不同可见 skill 集时用 agent 配置。

```json5
{
  agents: {
    defaults: {
      skills: ["github", "weather"], // 共享基线
    },
    list: [
      { id: "writer" }, // 继承 github, weather
      { id: "docs", skills: ["docs-search"] }, // 完全替换 defaults
      { id: "locked-down", skills: [] }, // 无 skill
    ],
  },
}
```

> Shared baseline allowlist inherited by agents that omit `agents.list[].skills`...

`agents.defaults.skills`: 未指定 `agents.list[].skills` 的 agent 继承的共享基线白名单。完全省略则默认不限制 skill。

> Explicit final skill set for that agent...

`agents.list[].skills`: 该 agent 的显式最终 skill 集。显式列表**替换**继承的 defaults——不会合并。设为 `[]` 则该 agent 不暴露任何 skill。

## Workshop（`skills.workshop`）

> When `true`, agents can create pending proposals from durable conversation signals...

`autonomous.enabled`: 为 `true` 时,agent 可从成功轮次后的持久对话信号创建待定提案。用户主动触发的 skill 创建始终走 Skill Workshop,不受此设置影响。

> `pending` requires operator approval before agent-initiated apply, reject, or quarantine...

`approvalPolicy`: `pending` 要求 agent 发起 apply/reject/quarantine 前需运营者审批。`auto` 允许这些操作无需审批。

> Maximum pending and quarantined proposals retained per workspace.

`maxPending`: 每工作区保留的待定和隔离提案上限。

> Maximum proposal body size in bytes...

`maxSkillBytes`: 提案正文最大字节数。提案 description 硬限 160 字节,因为它出现在发现和列表输出中。

## 符号链接 skill 根

> By default, workspace, project-agent, extra-dir, and bundled skill roots are containment boundaries...

默认工作区、项目 agent、额外目录和内置 skill 根是隔离边界。`<workspace>/skills` 下解析到根之外的符号链接 skill 文件夹被跳过并记日志。

> To allow an intentional symlink layout, declare the trusted target:

允许有意的符号链接布局时,声明受信目标：

```json5
{
  skills: {
    load: {
      extraDirs: ["~/Projects/manager/skills"],
      allowSymlinkTargets: ["~/Projects/manager/skills"],
    },
  },
}
```

此配置下,`<workspace>/skills/manager -> ~/Projects/manager/skills` 在 realpath 解析后被接受。`extraDirs` 直接扫描兄弟仓库；`allowSymlinkTargets` 为已有布局保留符号链接路径。

> Managed `~/.openclaw/skills` and personal `~/.agents/skills` directories already accept...

受管 `~/.openclaw/skills` 和个人 `~/.agents/skills` 目录已接受 skill 目录符号链接（单 skill `SKILL.md` 隔离仍适用）。

## 沙箱 skill 和环境变量

> Warning: `skills.entries.<skill>.env` and `apiKey` apply to **host** runs only...

警告：`skills.entries.<skill>.env` 和 `apiKey` 仅对**宿主**运行生效。沙箱内无效——依赖 `GEMINI_API_KEY` 的 skill 将报 `apiKey not configured`,除非单独给沙箱该变量。

Docker 沙箱传密钥：

```json5
{
  agents: {
    defaults: {
      sandbox: {
        docker: {
          env: { GEMINI_API_KEY: "your-key-here" },
        },
      },
    },
  },
}
```

注意：有 Docker daemon 访问权的用户可通过 Docker 元数据检查 `sandbox.docker.env` 值。当这种暴露不可接受时,使用挂载密钥文件、自定义镜像或其他传递路径。

## 加载顺序提醒

```text
workspace/skills      （最高）
workspace/.agents/skills
~/.agents/skills
~/.openclaw/skills
bundled skills
skills.load.extraDirs （最低）
```

watcher 启用时,skill 和配置变更在下次新会话生效;watcher 检测到变更时在下个 agent 轮次生效。

## 相关

- [Skills](/tools/skills) —— skill 是什么、加载顺序、门控、SKILL.md 格式。
- [创建 skill](/tools/creating-skills) —— 编写自定义工作区 skill。
- [Skill Workshop](/tools/skill-workshop) —— agent 起草 skill 的提案队列。
- [斜杠命令](/tools/slash-commands) —— 原生斜杠命令目录和聊天指令。
