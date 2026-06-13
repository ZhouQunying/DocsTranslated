# Admin HTTP RPC 插件

## 架构精读

> 跳过不影响阅读翻译正文。

### 已经有 WebSocket RPC 了,为什么还要 HTTP？

WebSocket 需要保持长连接,但很多宿主机自动化工具（curl、cron、tailnet 脚本）是请求/响应模式。Admin HTTP RPC 在 Gateway 进程内加一个 HTTP 适配层,让不能用 WebSocket 客户端的受信宿主机工具也能调用控制平面方法。

安全模型非常严格：这**不是** REST API 的便利补充,而是完整的运维控制平面表面。任何通过 Gateway HTTP 认证的调用者都能调用允许列表中的方法。所以要求只在回环、tailnet 或受信私有入口后启用,绝不直接暴露到公网。

共享密钥 bearer auth 在这个表面被视为完整运维访问——不像 WebSocket 客户端那样可以声明窄权限范围。这是有意设计：HTTP 场景下持有 Gateway 密钥就等于持有完整运维权限。

---

内置 `admin-http-rpc` 插件在 HTTP 上暴露选定的 Gateway 控制平面方法,供无法使用正常 Gateway WebSocket RPC 客户端的受信宿主机自动化使用。

插件随 OpenClaw 发布,但默认关闭。禁用时路由不注册。启用时添加：

- `POST /api/v1/admin/rpc`
- 与 Gateway 相同监听器：`http://<gateway-host>:<port>/api/v1/admin/rpc`

仅对私有宿主机工具、tailnet 自动化或受信内部入口启用。不要将此路由直接暴露到公网。

## 启用前须知

Admin HTTP RPC 是完整运维控制平面表面。任何通过 Gateway HTTP 认证的调用者都能调用本页允许列表中的方法。

以下全部满足时使用：

- 调用者被信任操作 Gateway。
- 调用者无法使用 WebSocket RPC 客户端。
- 路由仅在回环、tailnet 或私有认证入口可达。
- 已审查允许方法且匹配计划运行的自动化。

可保持 Gateway WebSocket 连接的 OpenClaw 客户端和交互工具使用 WebSocket RPC 路径。

## 启用

启用内置插件：

**CLI**

```bash
openclaw plugins enable admin-http-rpc
openclaw gateway restart
```

**Config**

```json5
{
  plugins: {
    entries: {
      "admin-http-rpc": { enabled: true },
    },
  },
}
```

路由在插件启动期间注册。变更插件配置后重启 Gateway。

不再需要 HTTP 表面时禁用：

```bash
openclaw plugins disable admin-http-rpc
openclaw gateway restart
```

## 验证路由

用 `health` 作为最小安全请求：

```bash
curl -sS http://<gateway-host>:<port>/api/v1/admin/rpc \
  -H 'Authorization: Bearer <gateway-token>' \
  -H 'Content-Type: application/json' \
  -d '{"method":"health","params":{}}'
```

成功响应含 `ok: true`：

```json
{
  "id": "generated-request-id",
  "ok": true,
  "payload": {
    "status": "ok"
  }
}
```

插件禁用时路由返回 `404` 因为未注册。

## 认证

插件路由使用 Gateway HTTP 认证。

常见认证路径：

- 共享密钥认证（`gateway.auth.mode="token"` 或 `"password"`）：`Authorization: Bearer <token-or-password>`
- 受信身份承载 HTTP 认证（`gateway.auth.mode="trusted-proxy"`）：通过配置的身份感知代理路由,让其注入所需身份头
- 私有入口开放认证（`gateway.auth.mode="none"`）：无需认证头

## 安全模型

将此插件视为完整 Gateway 运维表面。

- 启用插件有意在 `/api/v1/admin/rpc` 提供允许列表管理 RPC 方法的访问。
- 插件声明保留的 `contracts.gatewayMethodDispatch: ["authenticated-request"]` 清单契约,其 Gateway 认证 HTTP 路由可在进程内分发控制平面方法。
- 共享密钥 bearer 认证证明持有 gateway 运维密钥。
- `token` 和 `password` 认证下,更窄的 `x-openclaw-scopes` 头被忽略并恢复正常的完整运维默认值。
- 受信身份承载 HTTP 模式在 `x-openclaw-scopes` 存在时遵循。
- `gateway.auth.mode="none"` 意味着启用插件时此路由无认证。仅在完全信任的私有入口后使用。
- 请求在插件路由认证通过后通过与 WebSocket RPC 相同的 Gateway 方法处理器和权限范围检查分发。
- 将此路由保持在回环、tailnet 或私有受信入口。不要直接暴露到公网。
- 插件清单契约不是沙箱。防止意外使用保留 SDK 辅助；受信插件仍在 Gateway 进程中运行。

调用者跨信任边界时使用独立 gateway。

## 请求

```http
POST /api/v1/admin/rpc
Authorization: Bearer <gateway-token>
Content-Type: application/json
```

```json
{
  "id": "optional-request-id",
  "method": "health",
  "params": {}
}
```

字段：

- `id`（字符串,可选）：复制到响应中。省略时生成 UUID。
- `method`（字符串,必需）：允许的 Gateway 方法名。
- `params`（任意,可选）：方法特定参数。

默认最大请求体大小 1 MB。

## 响应

成功响应使用 Gateway RPC 格式：

```json
{
  "id": "optional-request-id",
  "ok": true,
  "payload": {}
}
```

Gateway 方法错误使用：

```json
{
  "id": "optional-request-id",
  "ok": false,
  "error": {
    "code": "INVALID_REQUEST",
    "message": "bad params"
  }
}
```

HTTP 状态码在可能时跟随 Gateway 错误。例如 `INVALID_REQUEST` 返回 `400`,`UNAVAILABLE` 返回 `503`。

## 允许的方法

- 发现：`commands.list`
  返回此插件允许的 HTTP RPC 方法名。
- gateway：`health`、`status`、`logs.tail`、`usage.status`、`usage.cost`、`gateway.restart.request`
- 配置：`config.get`、`config.schema`、`config.schema.lookup`、`config.set`、`config.patch`、`config.apply`
- 频道：`channels.status`、`channels.start`、`channels.stop`、`channels.logout`
- web：`web.login.start`、`web.login.wait`
- 模型：`models.list`、`models.authStatus`
- agent：`agents.list`、`agents.create`、`agents.update`、`agents.delete`
- 审批：`exec.approvals.get`、`exec.approvals.set`、`exec.approvals.node.get`、`exec.approvals.node.set`
- cron：`cron.status`、`cron.list`、`cron.get`、`cron.runs`、`cron.add`、`cron.update`、`cron.remove`、`cron.run`
- 设备：`device.pair.list`、`device.pair.approve`、`device.pair.reject`、`device.pair.remove`
- 节点：`node.list`、`node.describe`、`node.pair.list`、`node.pair.approve`、`node.pair.reject`、`node.pair.remove`、`node.rename`
- 任务：`tasks.list`、`tasks.get`、`tasks.cancel`
- 诊断：`doctor.memory.status`、`update.status`

其他 Gateway 方法在被有意添加前被阻止。

## WebSocket 对比

正常 Gateway WebSocket RPC 路径仍是 OpenClaw 客户端的首选控制平面 API。仅对需要请求/响应 HTTP 表面的宿主机工具使用 admin HTTP RPC。

无受信设备身份的共享令牌 WebSocket 客户端在连接时不能自声明 admin 权限范围。Admin HTTP RPC 有意遵循已有受信 HTTP 运维模型：启用插件时共享密钥 bearer 认证被视为此 admin 表面的完整运维访问。

## 故障排查

`404 Not Found`

: 插件被禁用、启用后 Gateway 未重启、或请求发往不同 Gateway 进程。

`401 Unauthorized`

: 请求未满足 Gateway HTTP 认证。检查 bearer 令牌或受信代理身份头。

`400 INVALID_REQUEST`

: 请求体不是有效 JSON、缺少 `method` 字段、或方法不在插件允许列表中。

`503 UNAVAILABLE`

: Gateway 方法处理器不可用。检查 Gateway 日志并在 Gateway 完成启动后重试。

## 相关

- [Operator scopes](/gateway/operator-scopes)
- [Gateway security](/gateway/security)
- [Remote access](/gateway/remote)
- [Plugin manifest](/plugins/manifest#contracts)
- [SDK subpaths](/plugins/sdk-subpaths)
