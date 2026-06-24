# Operator Scopes——操作员作用域

## 架构精读

> 跳过不影响阅读翻译正文。

### 控制面 vs 数据面——为什么操作员和用户权限分开？

操作员作用域限制管理网关的人（配置、重启、日志），不限制使用网关的人（对话、工具执行）。这跟 Kubernetes RBAC 是一个思路——cluster-scoped（管理员）和 namespace-scoped（应用）权限分离。管理网关的人和使用网关的人在不同层面操作。

### 作用域升级——为什么重连时触发升级请求？

WebSocket 连接以特定角色和权限建立。如果客户端重连时请求更宽的权限，系统不静默授予，而是创建"待审批升级请求"。这跟 OAuth 的 consent screen 是一个思路——应用请求新权限时必须重新授权。

### 自作用域 token——为什么非管理员不能批准超出自身权限的请求？

非管理员 session 只能批准自己已持有的权限范围内的请求。Admin 请求严格要求 admin 权限。这跟最小权限原则是一个思路——你不能给别人你没有的权限。

### 一个网关 = 一个信任域——为什么需要多网关做真正隔离？

一个网关的所有操作员在同一个信任域内。不同信任级别需要不同网关。这跟 Kubernetes namespace 是一个思路——每个 namespace 有自己的 RBAC，跨 namespace 需要显式配置。

---

### 概述 / Overview

These scopes dictate Gateway client permissions following authentication. They serve as a "control-plane guardrail" rather than hostile isolation. For strict separation, deploy distinct Gateways.

操作员作用域定义 Gateway 客户端认证后的权限。是"控制面防护栏"而非对抗性隔离。严格分离需要部署独立 Gateway。

### 角色 / Roles

WebSocket connections utilize specific roles:

- `operator`: Used by control-plane entities like UIs and CLIs.
- `node`: Applied to capability hosts exposing commands.

RPC methods demand the corresponding role.

WebSocket 连接使用特定角色：

- `operator`：控制面实体（UI、CLI）使用。
- `node`：暴露命令的能力宿主使用。

RPC 方法要求对应的角色。

### 作用域级别 / Scope Levels

| Scope | Description |
|---|---|
| `operator.read` | Permits non-mutating control-plane calls like viewing logs or status |
| `operator.write` | Allows standard mutating tasks and includes read permissions |
| `operator.admin` | Grants administrative control-plane access and satisfies all other scopes |
| `operator.pairing` | Manages device and node pairing records |
| `operator.approvals` | Handles plugin and execution approvals |
| `operator.talk.secrets` | Allows viewing Talk configurations containing secrets |

Unrecognized future scopes demand an exact match or admin privileges.

| 作用域 | 描述 |
|---|---|
| `operator.read` | 允许非变更的控制面调用（查看日志或状态） |
| `operator.write` | 允许标准变更操作，包含 read 权限 |
| `operator.admin` | 授予管理级控制面访问，满足所有其他作用域 |
| `operator.pairing` | 管理设备和节点配对记录 |
| `operator.approvals` | 处理插件和执行审批 |
| `operator.talk.secrets` | 允许查看包含密钥的 Talk 配置 |

未识别的未来作用域要求精确匹配或 admin 权限。

### 初始方法门控 / Initial Method Gates

Every RPC enforces a baseline least-privilege scope, but handlers may apply stricter approval-time checks depending on the action. For instance, approving an operator device restricts minted scopes to what the caller possesses, while persistent configuration changes via chat demand admin rights. This design enables low-risk pairing actions for lower-scope users.

每个 RPC 执行基线最小权限作用域，但 handler 可能根据操作应用更严格的审批时检查。例如，批准 operator 设备时，颁发的作用域限制为调用者已持有的；通过聊天做持久配置变更需要 admin 权限。这个设计让低权限用户也能做低风险的配对操作。

### 设备配对审批 / Device Pairing Approvals

Reconnecting with broader permissions triggers a pending upgrade request instead of silently granting access. Approval rules include:

- Non-operator roles demand admin rights.
- Requesting specific operator scopes requires the caller to already hold them or possess admin rights.
- Admin requests strictly require admin privileges.

Non-admin sessions can only approve requests within their own declared boundaries, and token sessions remain self-scoped unless the user is an admin.

以更宽权限重连会触发待审批升级请求，而非静默授予访问。审批规则：

- 非 operator 角色要求 admin 权限。
- 请求特定 operator 作用域要求调用者已持有或具备 admin 权限。
- Admin 请求严格要求 admin 权限。

非 admin session 只能批准自己声明边界内的请求，token session 保持自作用域（除非用户是 admin）。

### 节点配对审批 / Node Pairing Approvals

While legacy systems use a distinct store, WebSocket nodes leverage device pairing. The approval process derives extra requirements from the pending command list:

- Commandless or non-exec commands need pairing and write scopes.
- Execution commands like `system.run` require operator.pairing + operator.admin.

This process establishes trust but does not override the node's internal execution policies.

旧系统使用独立存储，WebSocket 节点利用设备配对。审批流程从待处理命令列表推导额外要求：

- 无命令或非执行命令需要 pairing + write 作用域。
- 执行命令（如 `system.run`）要求 operator.pairing + operator.admin。

此流程建立信任但不覆盖节点的内部执行策略。

### 共享密钥认证 / Shared-Secret Authentication

Token or password authentication is considered trusted operator access. HTTP endpoints restore the complete default scope set for shared-secret bearers. Conversely, identity-bearing modes respect explicitly declared scopes, so administrators should use separate Gateways for real trust boundary separation.

Token 或密码认证被视为可信操作员访问。HTTP 端点为共享密钥持有者恢复完整的默认作用域集。相反，身份承载模式尊重显式声明的作用域，所以管理员应使用独立 Gateway 实现真正的信任边界分离。
