# Anthropic

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
