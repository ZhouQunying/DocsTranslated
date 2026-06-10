# 多 Agent 沙箱和工具

## 架构精读

> 跳过不影响阅读翻译正文。

### 同一台机器多个 agent,凭什么隔离得开？

核心机制是**逐层收紧、不可回退**。工具过滤链从 profile → 全局策略 → agent 策略 → 沙箱策略 → 子 agent 策略逐级收窄。每层只能进一步限制,不能把上层拒绝的工具加回来。

沙箱作用域三档（session/agent/shared）决定容器复用粒度。`session` 每次对话一个容器,最强隔离但耗资源。`agent` 该 agent 所有会话共享容器,省资源但会话间不隔离。`shared` 多 agent 共享工作区,适合高信任协作。

`non-main` 模式的陷阱值得注意：它基于 session key 而非 agent id。群组/频道会话永远有自己的 key（非 main）,所以总是被沙箱化。想让某个 agent 永不沙箱只能显式设 `mode: "off"`。

---

> Each agent in a multi-agent setup can override the global sandbox and tool policy.

多 agent 设置中每个 agent 可覆盖全局沙箱和工具策略。本页覆盖 agent 级配置、优先级规则和示例。

- [Sandboxing](/gateway/sandboxing) —— 后端和模式,完整沙箱参考。
- [Sandbox vs tool policy vs elevated](/gateway/sandbox-vs-tool-policy-vs-elevated) —— 调试"为什么被阻止？"
- [Elevated mode](/tools/elevated) —— 受信发送者的提权执行。

警告：认证按 agent 隔离：每个 agent 在 `~/.openclaw/agents/<agentId>/agent/auth-profiles.json` 有自己的 `agentDir` 认证存储。不要跨 agent 复用 `agentDir`。Agent 无本地 profile 时可读取默认/主 agent 的认证 profile,但 OAuth 刷新令牌不会克隆到副 agent 存储。手动复制凭据时只复制可移植的静态 `api_key` 或 `token` profile。

---

## 配置示例

**示例 1：个人 + 受限家庭 agent**

```json
{
  "agents": {
    "list": [
      {
        "id": "main",
        "default": true,
        "name": "Personal Assistant",
        "workspace": "~/.openclaw/workspace",
        "sandbox": { "mode": "off" }
      },
      {
        "id": "family",
        "name": "Family Bot",
        "workspace": "~/.openclaw/workspace-family",
        "sandbox": {
          "mode": "all",
          "scope": "agent"
        },
        "tools": {
          "allow": ["read", "message"],
          "deny": ["exec", "write", "edit", "apply_patch", "process", "browser"],
          "message": {
            "crossContext": {
              "allowWithinProvider": false,
              "allowAcrossProviders": false
            }
          }
        }
      }
    ]
  },
  "bindings": [
    {
      "agentId": "family",
      "match": {
        "provider": "whatsapp",
        "accountId": "*",
        "peer": {
          "kind": "group",
          "id": "120363424282127706@g.us"
        }
      }
    }
  ]
}
```

**结果：**

- `main` agent：宿主运行,完全工具访问。
- `family` agent：Docker 运行（每 agent 一容器）,仅 `read` 和当前对话消息发送。

**示例 2：共享沙箱的工作 agent**

```json
{
  "agents": {
    "list": [
      {
        "id": "personal",
        "workspace": "~/.openclaw/workspace-personal",
        "sandbox": { "mode": "off" }
      },
      {
        "id": "work",
        "workspace": "~/.openclaw/workspace-work",
        "sandbox": {
          "mode": "all",
          "scope": "shared",
          "workspaceRoot": "/tmp/work-sandboxes"
        },
        "tools": {
          "allow": ["read", "write", "apply_patch", "exec"],
          "deny": ["browser", "gateway", "discord"]
        }
      }
    ]
  }
}
```

**示例 2b：全局编程 profile + 仅消息 agent**

```json
{
  "tools": { "profile": "coding" },
  "agents": {
    "list": [
      {
        "id": "support",
        "tools": { "profile": "messaging", "allow": ["slack"] }
      }
    ]
  }
}
```

**结果：**

- 默认 agent 获得编程工具。
- `support` agent 仅消息（+ Slack 工具）。

**示例 3：每 agent 不同沙箱模式**

```json
{
  "agents": {
    "defaults": {
      "sandbox": {
        "mode": "non-main",
        "scope": "session"
      }
    },
    "list": [
      {
        "id": "main",
        "workspace": "~/.openclaw/workspace",
        "sandbox": {
          "mode": "off"
        }
      },
      {
        "id": "public",
        "workspace": "~/.openclaw/workspace-public",
        "sandbox": {
          "mode": "all",
          "scope": "agent"
        },
        "tools": {
          "allow": ["read"],
          "deny": ["exec", "write", "edit", "apply_patch"]
        }
      }
    ]
  }
}
```

---

## 配置优先级

> When both global (`agents.defaults.*`) and agent-specific (`agents.list[].*`) configs exist:

全局（`agents.defaults.*`）和 agent 级（`agents.list[].*`）配置同时存在时：

### 沙箱配置

Agent 级设置覆盖全局：

```
agents.list[].sandbox.mode > agents.defaults.sandbox.mode
agents.list[].sandbox.scope > agents.defaults.sandbox.scope
agents.list[].sandbox.workspaceRoot > agents.defaults.sandbox.workspaceRoot
agents.list[].sandbox.workspaceAccess > agents.defaults.sandbox.workspaceAccess
agents.list[].sandbox.docker.* > agents.defaults.sandbox.docker.*
agents.list[].sandbox.browser.* > agents.defaults.sandbox.browser.*
agents.list[].sandbox.prune.* > agents.defaults.sandbox.prune.*
```

注意：`agents.list[].sandbox.{docker,browser,prune}.*` 为该 agent 覆盖 `agents.defaults.sandbox.{docker,browser,prune}.*`（沙箱作用域解析为 `"shared"` 时忽略）。

### 工具限制

过滤顺序：

1. **工具 profile** — `tools.profile` 或 `agents.list[].tools.profile`。
2. **提供商工具 profile** — `tools.byProvider[provider].profile` 或 `agents.list[].tools.byProvider[provider].profile`。
3. **全局工具策略** — `tools.allow` / `tools.deny`。
4. **提供商工具策略** — `tools.byProvider[provider].allow/deny`。
5. **Agent 级工具策略** — `agents.list[].tools.allow/deny`。
6. **Agent 提供商策略** — `agents.list[].tools.byProvider[provider].allow/deny`。
7. **沙箱工具策略** — `tools.sandbox.tools` 或 `agents.list[].tools.sandbox.tools`。
8. **子 agent 工具策略** — `tools.subagents.tools`（如适用）。

优先级规则：

- 每层可进一步限制工具,但不能把早期层拒绝的工具加回来。
- 设了 `agents.list[].tools.sandbox.tools` 则替换该 agent 的 `tools.sandbox.tools`。
- 设了 `agents.list[].tools.profile` 则覆盖该 agent 的 `tools.profile`。
- 提供商工具键接受 `provider`（如 `google-antigravity`）或 `provider/model`（如 `openai/gpt-5.4`）。

空白名单行为：链中任何显式白名单让运行无可调用工具时,OpenClaw 在提交提示给模型前停止。这是有意设计：配了缺失工具的 agent（如 `agents.list[].tools.allow: ["query_db"]`）应大声失败直到注册 `query_db` 的插件启用,而非继续作为纯文本 agent。

工具策略支持 `group:*` 简写,展开为多个工具。见 [Tool groups](/gateway/sandbox-vs-tool-policy-vs-elevated#tool-groups-shorthands)。

Agent 级提权覆盖（`agents.list[].tools.elevated`）可进一步限制特定 agent 的提权执行。见 [Elevated mode](/tools/elevated)。

---

## 从单 agent 迁移

**迁移前（单 agent）：**

```json
{
  "agents": {
    "defaults": {
      "workspace": "~/.openclaw/workspace",
      "sandbox": {
        "mode": "non-main"
      }
    }
  },
  "tools": {
    "sandbox": {
      "tools": {
        "allow": ["read", "write", "apply_patch", "exec"],
        "deny": []
      }
    }
  }
}
```

**迁移后（多 agent）：**

```json
{
  "agents": {
    "list": [
      {
        "id": "main",
        "default": true,
        "workspace": "~/.openclaw/workspace",
        "sandbox": { "mode": "off" }
      }
    ]
  }
}
```

注意：旧 `agent.*` 配置由 `openclaw doctor` 迁移；今后优先用 `agents.defaults` + `agents.list`。

---

## 工具限制示例

**只读 agent：**

```json
{
  "tools": {
    "allow": ["read"],
    "deny": ["exec", "write", "edit", "apply_patch", "process"]
  }
}
```

**Shell 执行但禁用文件系统工具：**

```json
{
  "tools": {
    "allow": ["read", "exec", "process"],
    "deny": ["write", "edit", "apply_patch", "browser", "gateway"]
  }
}
```

警告：此策略禁用 OpenClaw 文件系统工具,但 `exec` 仍是 shell,可在选定宿主或沙箱文件系统允许的任何位置写文件。只读 agent 应拒绝 `exec` 和 `process`,或将 shell 访问与沙箱文件系统控制结合,如 `agents.defaults.sandbox.workspaceAccess: "ro"` 或 `"none"`。

**仅通信：**

```json
{
  "tools": {
    "sessions": { "visibility": "tree" },
    "allow": ["sessions_list", "sessions_send", "sessions_history", "session_status"],
    "deny": ["exec", "write", "edit", "apply_patch", "read", "browser"]
  }
}
```

此 profile 中 `sessions_history` 仍返回有界、净化的召回视图而非原始转储。助手召回在截断前剥离 thinking 标签、脚手架、工具调用 XML、泄露的控制令牌等。

---

## 常见陷阱："non-main"

> `agents.defaults.sandbox.mode: "non-main"` is based on `session.mainKey`...

警告：`agents.defaults.sandbox.mode: "non-main"` 基于 `session.mainKey`（默认 `"main"`）,不是 agent id。群组/频道会话总有自己的 key,所以被视为 non-main 并被沙箱化。想让 agent 永不沙箱,设 `agents.list[].sandbox.mode: "off"`。

---

## 测试

配置多 agent 沙箱和工具后：

1. **检查 agent 解析：**

```bash
openclaw agents list --bindings
```

2. **验证沙箱容器：**

```bash
docker ps --filter "name=openclaw-sbx-"
```

3. **测试工具限制：** 发送需要受限工具的消息,验证 agent 不能用被拒绝的工具。

4. **监控日志：**

```bash
tail -f "${OPENCLAW_STATE_DIR:-$HOME/.openclaw}/logs/gateway.log" | grep -E "routing|sandbox|tools"
```

---

## 故障排查

**Agent 设了 `mode: 'all'` 但未沙箱化：**
- 检查是否有全局 `agents.defaults.sandbox.mode` 覆盖了它。
- Agent 级配置优先,所以设 `agents.list[].sandbox.mode: "all"`。

**deny 列表中的工具仍可用：**
- 检查工具过滤顺序：全局 → agent → 沙箱 → 子 agent。
- 每层只能进一步限制,不能加回。
- 用日志验证：`[tools] filtering tools for agent:${agentId}`。

**容器未按 agent 隔离：**
- 在 agent 级沙箱配置中设 `scope: "agent"`。
- 默认是 `"session"`,每会话创建一个容器。

---

## 相关

- [Elevated mode](/tools/elevated)
- [Multi-agent routing](/concepts/multi-agent)
- [Sandbox configuration](/gateway/config-agents#agentsdefaultssandbox)
- [Sandbox vs tool policy vs elevated](/gateway/sandbox-vs-tool-policy-vs-elevated) —— 调试"为什么被阻止？"
- [Sandboxing](/gateway/sandboxing) —— 完整沙箱参考（模式、作用域、后端、镜像）
- [Session management](/concepts/session)
