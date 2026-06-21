# Operator scopes

## 架构精读

> 跳过不影响阅读翻译正文。

### 操作员作用域

**问题**: Gateway 操作员能做什么?

**方案**: 作用域定义操作员权限:
- `config:read`: 读配置
- `config:write`: 写配置
- `gateway:restart`: 重启 Gateway
- `logs:read`: 查看日志
- `session:read`: 查看会话

**洞察**: 作用域 = 限制操作员权限,减少误操作风险。

**权衡**:
- ✓ 安全: 最小权限原则
- ✗ 复杂: 需要管理不同操作员的 scopes

**模式**: AWS IAM 策略——定义"用户能做什么"。

### Control-plane guardrail

**问题**: 操作员作用域限制什么?

**方案**: **控制层面** (control plane),不是数据层面 (data plane):
- 控制层面: 管理 Gateway (配置、重启、日志)
- 数据层面: 处理用户消息 (agent 对话、工具执行)

**洞察**: 管理 Gateway 的人 (操作员) 和使用 Gateway 的人 (用户) 权限分开。

**权衡**:
- ✓ 分离: 操作员权限 ≠ 用户权限
- ✗ 复杂: 需要分别管理两种权限

**模式**: Kubernetes RBAC——cluster-scoped vs namespace-scoped。

### 作用域的定义

**问题**: 作用域在哪里定义?

**方案**: 在配置文件中:
```json
{
  gateway: {
    operators: [
      { user: "admin", scopes: ["config:read", "config:write", "gateway:restart"] },
      { user: "junior-ops", scopes: ["logs:read", "session:read"] }
    ]
  }
}
```

**洞察**: 配置文件 = 权威来源,可以版本控制、自动化。

**权衡**:
- ✓ 可审计: 配置在 Git 中
- ✗ 静态: 修改配置需要重启 Gateway

**模式**: Kubernetes ConfigMap——存储应用配置。

### 一个 Gateway,一个操作员 domain

**问题**: 不同操作员需要不同信任级别?

**方案**: 用多个 Gateway,每个 Gateway 有自己的操作员 domain。

**洞察**: 一个 Gateway 的所有操作员在同一个信任域内。

**权衡**:
- ✓ 简单: 不需要复杂的权限管理
- ✗ 资源: 多个 Gateway 消耗更多资源

**模式**: Kubernetes namespace——每个 namespace 有自己的 RBAC。

### 作用域的粒度

**问题**: 作用域是粗粒度还是细粒度?

**方案**: **粗粒度** (coarse-grained):
- ✓ `config:write` (能写所有配置)
- ✗ `config:write:agents.defaults.model` (能写特定字段)

**洞察**: 粗粒度 = 简单,大多数场景够用。

**权衡**:
- ✓ 简单: 不需要细粒度权限管理
- ✗ 不灵活: 不能限制到特定配置字段

**模式**: Linux 文件权限——读、写、执行,不是"只能读第 10-20 行"。
