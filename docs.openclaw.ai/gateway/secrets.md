# Secrets management

## 架构精读

> 跳过不影响阅读翻译正文。

### SecretRef

**问题**: 凭证明文存储在 `openclaw.json`,可能被提交到 Git、被 agent 读取、被备份工具复制?

**方案**: SecretRef (Secret 引用),配置文件只包含"指针":
```json
{
  auth: {
    apiKey: { $ref: "env:OPENAI_API_KEY" }
  }
}
```

**洞察**: 配置文件不直接存储凭证,真正的凭证存在别处。

**权衡**:
- ✓ 安全: 凭证不明文,不会泄露
- ✗ 复杂: 需要配置凭证来源

**模式**: Kubernetes Secret——Pod 配置引用 Secret 对象,不直接写密码。

### 三种 SecretRef 来源

**问题**: 不同环境的凭证管理方式不同 (CI/CD 用环境变量、Docker 用 Secrets、云用 Secrets Manager)?

**方案**: 三种来源:
- **env**: 从环境变量读取 (CI/CD 场景)
- **file**: 从文件读取 (Docker Secrets)
- **exec**: 执行命令读取 (AWS Secrets Manager)

**洞察**: 三种来源覆盖三种场景,不强迫用户用特定方式。

**权衡**:
- ✓ 灵活: 适配不同环境
- ✓ 兼容: CI/CD、Docker、云都能用

### Plaintext 仍然支持

**问题**: 老配置文件是明文的,强制迁移太麻烦?

**方案**: 仍然支持明文凭证,SecretRef 是 opt-in (可选的)。

**洞察**: 向后兼容 + 渐进式迁移,简单场景用明文,安全敏感场景用 SecretRef。

**权衡**:
- ✓ 兼容: 老配置不需要改
- ✓ 灵活: 本地开发用明文,生产环境用 SecretRef

### Strict command paths

**问题**: `exec` 类型的 SecretRef 命令路径可以是相对路径或包含 shell 操作符,有安全风险?

**方案**: 命令路径必须是**绝对路径**,禁止 shell 操作符 (`|`、`&&`)。

**洞察**: 绝对路径 + 禁止 shell 操作符 = 只能执行指定的命令,防止命令注入。

**权衡**:
- ✓ 安全: 防止恶意命令
- ✗ 不灵活: 不能用相对路径

**模式**: sudoers command 限制——必须是绝对路径,防止通过修改 `$PATH` 执行恶意程序。

### Read-only command paths

**问题**: `exec` 命令可以修改系统状态 (如写文件、发网络请求)?

**方案**: 命令只能**读取**凭证,不能修改系统状态。

**洞察**: SecretRef 的目的是"获取凭证",不是"执行任意操作"。

**权衡**:
- ✓ 安全: 不能通过 SecretRef 修改系统
- ✗ 限制: 不能执行写操作

**模式**: 数据库 SELECT 权限——只能读取,不能修改。

### Audit current state

**问题**: 配置文件很大,手动检查哪些是明文凭证很麻烦?

**方案**: `openclaw secrets audit` 自动扫描:
```
auth.apiKey: plaintext (should be SecretRef)
auth.oauthToken: SecretRef (env:OAUTH_TOKEN)
```

**洞察**: 自动扫描,列出所有明文凭证,帮助用户识别安全风险。

**权衡**:
- ✓ 自动化: 不需要手动检查
- ✓ 清晰: 列出哪些是明文、哪些是 SecretRef

**模式**: `npm audit`——扫描 node_modules,列出有安全漏洞的包。
