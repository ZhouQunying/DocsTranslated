# Webhooks 插件

## 架构精读

> 跳过不影响阅读翻译正文。

### 为什么不让外部系统直接调 Gateway WebSocket？

Gateway WebSocket 需要保持长连接,而 Zapier、n8n、CI 作业等外部自动化是请求/响应模式——发完就走。Webhooks 插件在 Gateway 进程内加一层 HTTP 适配,让外部系统用熟悉的 `POST` + `Bearer token` 驱动 TaskFlow,而不用实现 WebSocket 客户端。

安全模型也值得注意。每条路由被信任以配置 `sessionKey` 的 TaskFlow 权限行事——就像给了外部系统一把限定房间的钥匙。所以要求强唯一密钥、优先用 SecretRef 而非明文、绑定到最窄会话。插件还在上层叠加了请求体大小限制、速率限制和并发请求限制。

---

Webhooks 插件添加认证 HTTP 路由,将外部自动化绑定到 OpenClaw TaskFlow。

需要 Zapier、n8n、CI 作业或内部服务等受信系统创建和驱动受管 TaskFlow 而无需先写自定义插件时使用。

## 运行位置

Webhooks 插件在 Gateway 进程内运行。

Gateway 在另一台机器上运行时,在该 Gateway 宿主机上安装和配置插件,然后重启 Gateway。

## 配置路由

在 `plugins.entries.webhooks.config` 下设置配置：

```json5
{
  plugins: {
    entries: {
      webhooks: {
        enabled: true,
        config: {
          routes: {
            zapier: {
              path: "/plugins/webhooks/zapier",
              sessionKey: "agent:main:main",
              secret: {
                source: "env",
                provider: "default",
                id: "OPENCLAW_WEBHOOK_SECRET",
              },
              controllerId: "webhooks/zapier",
              description: "Zapier TaskFlow bridge",
            },
          },
        },
      },
    },
  },
}
```

路由字段：

- `enabled`：可选,默认 `true`
- `path`：可选,默认 `/plugins/webhooks/<routeId>`
- `sessionKey`：持有绑定 TaskFlow 的必需会话
- `secret`：必需共享密钥或 SecretRef
- `controllerId`：创建的受管流的可选控制器 id
- `description`：可选运维备注

支持的 `secret` 输入：

- 纯字符串
- `source: "env" | "file" | "exec"` 的 SecretRef

密钥支持的路由在启动时无法解析密钥时,插件跳过该路由并记录警告,而非暴露损坏的端点。

## 安全模型

每条路由被信任以配置 `sessionKey` 的 TaskFlow 权限行事。

这意味着路由可检查和变更该会话名下的 TaskFlow,所以应该：

- 每路由使用强唯一密钥
- 优先用密钥引用而非内联明文密钥
- 将路由绑定到适合工作流的最窄会话
- 仅暴露需要的特定 webhook 路径

插件应用：

- 共享密钥认证
- 请求体大小和超时限流
- 固定窗口速率限制
- 在途请求限制
- 通过 `api.runtime.tasks.managedFlows.bindSession(...)` 的 owner 绑定 TaskFlow 访问

## 请求格式

发送 `POST` 请求：

- `Content-Type: application/json`
- `Authorization: Bearer <secret>` 或 `x-openclaw-webhook-secret: <secret>`

示例：

```bash
curl -X POST https://gateway.example.com/plugins/webhooks/zapier \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer YOUR_SHARED_SECRET' \
  -d '{"action":"create_flow","goal":"Review inbound queue"}'
```

## 支持的动作

插件当前接受以下 JSON `action` 值：

- `create_flow`
- `get_flow`
- `list_flows`
- `find_latest_flow`
- `resolve_flow`
- `get_task_summary`
- `set_waiting`
- `resume_flow`
- `finish_flow`
- `fail_flow`
- `request_cancel`
- `cancel_flow`
- `run_task`

### `create_flow`

为路由绑定会话创建受管 TaskFlow。

示例：

```json
{
  "action": "create_flow",
  "goal": "Review inbound queue",
  "status": "queued",
  "notifyPolicy": "done_only"
}
```

### `run_task`

在已有受管 TaskFlow 内创建受管子任务。

允许的运行时：

- `subagent`
- `acp`

示例：

```json
{
  "action": "run_task",
  "flowId": "flow_123",
  "runtime": "acp",
  "childSessionKey": "agent:main:acp:worker",
  "task": "Inspect the next message batch"
}
```

## 响应格式

成功响应返回：

```json
{
  "ok": true,
  "routeId": "zapier",
  "result": {}
}
```

被拒绝请求返回：

```json
{
  "ok": false,
  "routeId": "zapier",
  "code": "not_found",
  "error": "TaskFlow not found.",
  "result": {}
}
```

插件有意从 webhook 响应中清除 owner/会话元数据。

## 相关文档

- [Plugin runtime SDK](/plugins/sdk-runtime)
- [Hooks and webhooks overview](/automation/hooks)
- [CLI webhooks](/cli/webhooks)
