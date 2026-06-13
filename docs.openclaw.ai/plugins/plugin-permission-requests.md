# 插件权限请求

## 架构精读

> 跳过不影响阅读翻译正文。

### 插件审批、exec 审批和可选工具有什么区别？

三个门控作用于不同阶段。可选工具是发现时门控，决定模型能不能看到这个工具。插件权限请求是每次调用门控，在 `before_tool_call` 钩子中暂停等待用户审批。exec 审批是 host 持有策略，控制 shell 命令和安全操作。就像机场安检——可选工具是"这个通道是否open"，插件审批是"你确认带这个物品吗"，exec 审批是"安检扫描你的行李"。好处是每个门控作用于正确的时间点，坏处是需要理解三个门控的分工和独立配置。

另外，插件审批和 exec 审批使用独立配置（`approvals.plugin` vs `approvals.exec`），路由通道也独立。开了 exec 审批转发不会路由插件审批提示，开了插件审批转发也不会改变 host exec 策略。

---

插件权限请求让插件代码暂停工具调用或插件持有操作，直到用户批准或拒绝。它们使用 Gateway 的 `plugin.approval.*` 流程和相同的审批 UI 表面处理聊天审批按钮和 `/approve` 命令。

插件权限请求用于插件/应用权限。它们不替代 host exec 审批、可选工具允许列表或 Codex 的原生权限审查。

## 选择正确的门控

选择匹配你需要的决策点的门控：

| 门控                             | 何时使用                                                   | 控制什么                                                                                                            |
| -------------------------------- | ---------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------- |
| 可选工具                         | 工具在用户 opt-in 前不应对模型可见                          | 通过 `tools.allow` 控制工具暴露                                                                                     |
| 插件权限请求                     | 插件钩子或插件持有操作在执行一项操作前必须询问              | 通过 `plugin.approval.*` 的运行时审批                                                                               |
| Exec 审批                        | host 命令或类 shell 工具需要 operator 审批                  | Host exec 策略和持久 exec 允许列表                                                                                  |
| Codex 原生权限请求               | Codex 原生 shell、文件、MCP 或 app-server 操作前询问        | Codex app-server 或原生钩子审批处理，当 OpenClaw 持有 prompt 时通过插件审批路由                                     |
| MCP 审批请求                     | Codex MCP 服务器请求批准工具调用                            | 通过 OpenClaw 插件审批桥接的 MCP 审批响应                                                                           |

可选工具是发现时门控。插件权限请求是每次调用门控。当敏感工具需要显式 opt-in 后模型才能看见、且执行前需要审批时，同时使用两者。

## 在工具调用前请求审批

大多数插件编写的提示应在 `before_tool_call` 钩子中开始。该钩子在模型选择工具后、OpenClaw 执行前运行：

```typescript

export default definePluginEntry({
  id: "deploy-policy",
  name: "Deploy Policy",
  register(api) {
    api.on("before_tool_call", async (event) => {
      if (event.toolName !== "deploy_service") {
        return;
      }

      const environment =
        typeof event.params.environment === "string" ? event.params.environment : "unknown";

      return {
        requireApproval: {
          title: "Deploy service",
          description: `Deploy service to ${environment}.`,
          severity: environment === "production" ? "critical" : "warning",
          allowedDecisions:
            environment === "production"
              ? ["allow-once", "deny"]
              : ["allow-once", "allow-always", "deny"],
          timeoutMs: 120_000,
          timeoutBehavior: "deny",
          onResolution(decision) {
            console.log(`deploy approval resolved: ${decision}`);
          },
        },
      };
    });
  },
});
```

为将要审批该操作的人写提示文本：

- 保持 `title` 简短且以动作为中心。Gateway 接受最多 80 字符
- 保持 `description` 具体且有界。Gateway 接受最多 256 字符
- 包含操作、目标和风险。不要包含不应出现在聊天审批表面中的密钥、令牌或私有负载
- 仅在错误决策可能导致生产损坏或数据丢失的操作上使用 `severity: "critical"`
- 当持久信任对该操作不安全时使用 `allowedDecisions: ["allow-once", "deny"]`

## 决策行为

OpenClaw 创建带 `plugin:` ID 的待处理审批，投递到可用的审批表面并等待决策。

| 决策              | 结果                                                                |
| ----------------- | ------------------------------------------------------------------- |
| `allow-once`      | 当前调用继续                                                        |
| `allow-always`    | 当前调用继续，决策传递给插件                                        |
| `deny`            | 调用被阻断，返回拒绝的工具结果                                      |
| 超时              | 除非 `timeoutBehavior` 为 `"allow"`，否则调用被阻断                 |
| 取消              | 运行被中止时调用被阻断                                              |
| 无审批路由        | 没有任何连接的审批表面可解析时调用被阻断                            |

`allow-always` 仅在请求的插件或运行时实现了该持久化时才持久。对于普通的 `before_tool_call.requireApproval` 钩子，OpenClaw 将 `allow-once` 和 `allow-always` 都视为当前调用的审批决策，并将已解析值传递给 `onResolution`。如果插件提供 `allow-always`，需要记录并实现该信任具体覆盖了哪些未来调用。

如果钩子同时返回 `params`，OpenClaw 仅在审批成功后应用那些参数变更。更低优先级钩子仍可在更高优先级钩子请求审批后阻断。

`allowedDecisions` 限制显示给用户的按钮和命令。Gateway 拒绝未在请求中提供的任何决策的解析尝试。

## 路由审批提示

审批提示可在本地 UI 表面或支持审批处理的聊天 channel 中解析。要转发插件审批提示到显式的聊天目标，配置 `approvals.plugin`：

```json5
{
  approvals: {
    plugin: {
      enabled: true,
      mode: "targets",
      agentFilter: ["main"],
      targets: [{ channel: "slack", to: "U12345678" }],
    },
  },
}
```

`approvals.plugin` 独立于 `approvals.exec`。启用 exec 审批转发不会路由插件审批提示，启用插件审批转发也不会改变 host exec 策略。

当提示包含手动审批文本时，用提供的决策之一解析：

```text
/approve <id> allow-once
/approve <id> allow-always
/approve <id> deny
```

完整转发模型、同聊天审批行为、原生 channel 投递和 channel 专用审批规则见 [Advanced exec approvals](/tools/exec-approvals-advanced#plugin-approval-forwarding)。

## Codex 原生权限

Codex 原生权限提示也可通过插件审批传递，但它们与插件编写的钩子有不同的所有权。

- Codex app-server 审批请求在 Codex 审查后通过 OpenClaw 路由
- 原生钩子 `permission_request` 中继在该中继启用时可通过 `plugin.approval.request` 询问
- MCP 工具审批请求在 Codex 将 `_meta.codex_approval_kind` 标记为 `"mcp_tool_call"` 时通过插件审批路由

Codex 专用行为和回退规则见 [Codex harness runtime](/plugins/codex-harness-runtime#native-permissions-and-mcp-elicitations)。

## 疑难排查

**工具提示插件审批不可用。** 没有审批 UI 或配置的审批路由接受了该请求。连接审批能力客户端，使用支持同聊天 `/approve` 的 channel，或配置 `approvals.plugin`。

**`allow-always` 出现但下次调用再次提示。** 通用插件审批流程不会自动为任意钩子持久化信任。在 `onResolution("allow-always")` 后在插件中持久化插件持有的信任，或仅提供 `allow-once` 和 `deny`。

**`/approve` 拒绝了该决策。** 请求限制了 `allowedDecisions`。使用提示中打印的决策之一。

**Slack、Discord、Telegram 或 Matrix 提示的路由与 exec 审批不同。** 插件审批和 exec 审批使用单独配置，可能使用不同授权检查。验证 `approvals.plugin` 和 channel 的插件审批支持，而不是仅检查 `approvals.exec`。

## 相关

- [Plugin hooks](/plugins/hooks#tool-call-policy)
- [Building plugins](/plugins/building-plugins#registering-agent-tools)
- [Advanced exec approvals](/tools/exec-approvals-advanced#plugin-approval-forwarding)
- [Gateway protocol](/gateway/protocol)
- [Codex harness runtime](/plugins/codex-harness-runtime#native-permissions-and-mcp-elicitations)