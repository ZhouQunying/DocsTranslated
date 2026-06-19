# Anthropic

## 架构精读

> 跳过不影响阅读翻译正文。

### API key vs Claude CLI——为什么两种认证路由？

Anthropic 是 OpenClaw 中少数提供两种完全不同认证路由的提供者：

- **API key**：直接访问 Anthropic API，按使用量计费
- **Claude CLI**：复用同一主机上已有的 Claude Code 登录

这跟 AWS 的"access key vs IAM role"是一个思路。两种认证方式服务于不同场景：API key 用于服务器到服务器的自动化，Claude CLI 用于开发者本地环境。

关键设计是**认证复用**。Claude CLI 后端以非交互打印模式（`claude -p`）运行已安装的 Claude Code CLI。用户不需要单独申请 API key——如果他们已经登录了 Claude Code，OpenClaw 直接复用那个认证。

代价是依赖 Claude Code CLI 的安装。但这降低了入门摩擦——用户不需要在两个系统分别配置认证。

### 订阅计划 vs API 计费——为什么分离额度？

从 2026 年 6 月 15 日起，订阅计划的 `claude -p` 使用从单独的月度 Agent SDK 额度扣除，而非正常 Claude 计划限额。

这跟 GitHub Copilot 的"个人 vs 企业"额度分离是一个思路。设计意图是**防止 agent 使用量挤占人工使用量**。如果 agent 的编程调用和人类的交互式使用共享同一个限额，agent 的高频调用会快速耗尽人类的使用配额。分离额度让两种使用模式互不干扰。

---

Anthropic builds the Claude model family. OpenClaw supports two auth routes:

Anthropic 构建 Claude 模型系列。OpenClaw 支持两种认证路由:

- **API key** — direct Anthropic API access with usage-based billing (`anthropic/*` models)
  
  **API 密钥** — 直接 Anthropic API 访问,按使用量计费(`anthropic/*` 模型)

- **Claude CLI** — reuse an existing Claude Code login on the same host
  
  **Claude CLI** — 在同一主机上复用现有的 Claude Code 登录

OpenClaw's Claude CLI backend runs the installed Claude Code CLI in non-interactive print mode. Anthropic's current Claude Code docs describe `claude -p` as Agent SDK/programmatic usage. Starting June 15, 2026, Anthropic says subscription-plan `claude -p` usage no longer draws from normal Claude plan limits; it draws from a separate monthly Agent SDK credit first, then from usage credits at standard API rates when those credits are enabled.

OpenClaw 的 Claude CLI 后端以非交互打印模式运行已安装的 Claude Code CLI。Anthropic 当前的 Claude Code 文档将 `claude -p` 描述为 Agent SDK/编程用法。从 2026 年 6 月 15 日起,Anthropic 表示订阅计划的 `claude -p` 使用不再从正常 Claude 计划限额中扣除。它首先从单独的月度 Agent SDK 额度中扣除,然后在启用使用额度时按标准 API 费率从使用额度中扣除。

Interactive Claude Code still draws from the signed-in Claude plan limits. API key auth is unaffected.

交互式 Claude Code 仍从已登录的 Claude 计划限额中扣除。API 密钥认证不受影响。

## Getting started / 入门

### API key / API 密钥

```bash
openclaw onboard
# Choose "Anthropic" and paste your API key
```

Or set directly:

或直接设置:

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

### Claude CLI / Claude CLI

```bash
openclaw onboard
# Choose "Claude CLI" - reuses existing Claude Code login
```

## Configuration / 配置

```json5
{
  agents: {
    defaults: {
      model: {
        primary: "anthropic/claude-opus-4-6"
      }
    }
  }
}
```

## Model routing / 模型路由

OpenClaw routes `anthropic/*` models through the Anthropic provider. Both API key and Claude CLI auth use the same model IDs.

OpenClaw 通过 Anthropic 提供者路由 `anthropic/*` 模型。API 密钥和 Claude CLI 认证使用相同的模型 ID。

## Related / 相关

- [Provider directory](/providers) — 所有提供者列表
- [Models](/providers/models) — 模型配置
- [OpenAI](/providers/openai) — OpenAI 提供者
