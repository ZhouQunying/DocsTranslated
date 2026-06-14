# 创建技能

## 架构精读

> 跳过不影响阅读翻译正文。

### 为什么 agent 的技能是声明式指令集而非可执行代码？

OpenClaw 的技能不是函数或脚本，而是 `SKILL.md`——一份 YAML 前置元数据加 Markdown 指令的文本文件。这就像 Terraform 的 `.tf` 文件——你声明"做什么"和"何时做"，运行时（agent）决定"怎么做"。好处是技能可以被 LLM 直接理解和推理；坏处是你无法单元测试技能的执行路径，因为"执行者"是模型而非解释器。

第二个设计：声明式门控。技能的 `metadata.openclaw.requires` 字段声明依赖条件——二进制、环境变量、配置路径、操作系统。加载时 Gateway 检查所有条件，不满足则跳过该技能。这就像 Kubernetes 的 nodeSelector 和 tolerations——Pod 声明运行条件，调度器匹配节点时才部署。好处是技能不会因为缺少依赖而在运行时失败；坏处是门控条件必须预先知道。

第三个边界：工具分发旁路。`command-dispatch: tool` 让斜杠命令直接路由到已注册工具，完全绕过模型。这是纯命令模式——用户输入 `/image-lab generate a cat` 时直接调用工具而非让模型决定。这就像 API Gateway 的直连路由——跳过中间件链直接转发到后端服务。好处是零延迟、零 token 成本；坏处是失去模型的意图理解和上下文注入能力。

---

技能教 agent 如何以及何时使用工具。每个技能是一个目录，包含 `SKILL.md` 文件，带有 YAML 前置元数据和 Markdown 指令。OpenClaw 从多个根目录按[优先级顺序](/tools/skills#loading-order)加载技能。

## 创建第一个技能

```bash
# 创建目录
mkdir -p ~/.openclaw/workspace/skills/hello-world

# 在目录中创建 SKILL.md
# 前置元数据定义元数据；正文给出 agent 指令
```

```markdown
---
name: hello-world
description: A simple skill that prints a greeting.
---

# Hello World

When the user asks for a greeting, use the `exec` tool to run:

```bash
echo "Hello from your custom skill!"
```
```

命名规则：`name` 使用小写字母、数字和连字符。保持目录名与前置元数据 `name` 一致。`description` 显示给 agent 和斜杠命令发现——保持一行且不超过 160 字符。

验证技能加载：

```bash
openclaw skills list
```

OpenClaw 默认监听技能根目录下的 `SKILL.md` 变更。如监听被禁用或你继续已有会话，开启新会话让 agent 获取刷新列表：

```bash
/new
```

## SKILL.md 参考

### 必填字段

| 字段 | 描述 |
| --- | --- |
| `name` | 使用小写字母、数字和连字符的唯一标识 |
| `description` | 显示给 agent 和发现输出的一行描述 |

### 可选前置元数据键

| 字段 | 默认值 | 描述 |
| --- | --- | --- |
| `user-invocable` | `true` | 将技能暴露为用户斜杠命令 |
| `disable-model-invocation` | `false` | 将技能排除出 agent 系统提示（仍可通过 `/skill` 运行） |
| `command-dispatch` | — | 设为 `tool` 将斜杠命令直接路由到工具，绕过模型 |
| `command-tool` | — | `command-dispatch: tool` 时要调用的工具名 |
| `command-arg-mode` | `raw` | 工具分发时，将原始参数字符串转发给工具 |
| `homepage` | — | macOS 技能 UI 中显示为"网站"的 URL |

### 使用 `{baseDir}`

在技能正文中使用 `{baseDir}` 引用技能目录内的文件，无需硬编码路径：

```markdown
Run the helper script at `{baseDir}/scripts/run.sh`.
```

## 添加条件激活

通过门控使技能仅在依赖可用时加载：

```markdown
---
name: gemini-search
description: Search using Gemini CLI.
metadata: { "openclaw": { "requires": { "bins": ["gemini"] }, "primaryEnv": "GEMINI_API_KEY" } }
---
```

| 门控键 | 描述 |
| --- | --- |
| `requires.bins` | 所有二进制必须存在于 `PATH` |
| `requires.anyBins` | 至少一个二进制必须存在于 `PATH` |
| `requires.env` | 每个环境变量必须存在于进程或配置中 |
| `requires.config` | 每个 `openclaw.json` 路径必须为真值 |
| `os` | 平台过滤：`["darwin"]`、`["linux"]`、`["win32"]` |
| `always` | 设为 `true` 跳过所有门控，始终包含技能 |

完整参考：[技能 — 门控](/tools/skills#gating)。

### 环境变量和 API 密钥

在 `openclaw.json` 中为技能条目配置 API 密钥：

```json5
{
  skills: {
    entries: {
      "gemini-search": {
        enabled: true,
        apiKey: { source: "env", provider: "default", id: "GEMINI_API_KEY" },
      },
    },
  },
}
```

密钥仅在该 agent 运行的宿主进程中注入。不会到达沙箱——参见[沙箱环境变量](/tools/skills-config#sandboxed-skills-and-env-vars)。

## 通过技能工坊提案

对于 agent 起草的技能或需要操作者审查后才能上线的技能，使用[技能工坊](/tools/skill-workshop)提案而非直接编写 `SKILL.md`。

```bash
# 提案创建全新技能
openclaw skills workshop propose-create \
  --name "hello-world" \
  --description "A simple skill that prints a greeting." \
  --proposal ./PROPOSAL.md

# 提案更新已有技能
openclaw skills workshop propose-update hello-world \
  --proposal ./PROPOSAL.md \
  --description "Updated greeting skill"
```

提案包含辅助文件时使用 `--proposal-dir`：

```bash
openclaw skills workshop propose-create \
  --name "hello-world" \
  --description "A simple skill that prints a greeting." \
  --proposal-dir ./hello-world-proposal/
```

目录必须包含 `PROPOSAL.md`。辅助文件可放在 `assets/`、`examples/`、`references/`、`scripts/` 或 `templates/`。

审查后：

```bash
openclaw skills workshop inspect <proposal-id>
openclaw skills workshop apply <proposal-id>
```

参见[技能工坊](/tools/skill-workshop)了解完整提案生命周期。

## 发布到 ClawHub

确保 `name`、`description` 和任何 `metadata.openclaw` 门控字段已设置。如有项目页面则添加 `homepage` URL。安装 ClawHub 技能然后发布：

```bash
openclaw skills install clawhub-publish
clawhub publish
```

参见 [ClawHub — 发布](/clawhub/publishing)了解完整流程。

## 最佳实践

- **简洁**——指导模型*做什么*，而非如何成为 AI
- **安全第一**——如技能使用 `exec`，确保提示不允许不受信任输入的任意命令注入
- **本地测试**——分享前使用 `openclaw agent --message "..."` 测试
- **使用 ClawHub**——从零构建前在 [clawhub.ai](https://clawhub.ai) 浏览社区技能

## 相关

- [技能参考](/tools/skills)：加载顺序、门控、白名单和 SKILL.md 格式
- [技能工坊](/tools/skill-workshop)：agent 起草技能的提案队列
- [技能配置](/tools/skills-config)：完整 `skills.*` 配置模式
- [ClawHub](https://clawhub.ai)：在公共注册表浏览和发布技能
- [构建插件](/plugins/building-plugins)：插件可随技能一起分发
