# Secrets apply plan contract

## 架构精读

> 跳过不影响阅读翻译正文。

### Plan contract

**问题**: 凭证迁移 (明文 → SecretRef) 是高风险操作,迁移错了可能导致 agent 无法连接 provider 或凭证泄露?

**方案**: `openclaw secrets apply` 遵循**严格的契约** (contract):
```bash
openclaw secrets apply --from plan.json
```
Plan 不符合规则 → 直接失败,**不修改任何配置**。

**洞察**: 不符合契约就拒绝,不会部分迁移。

**权衡**:
- ✓ 安全: 不会"迁移一半出错了"
- ✓ 可控: 迁移前检查规则

**模式**: 数据库 migration contract——Flyway/Liquibase 执行前检查,不符合规则直接拒绝。

### Targets array

**问题**: Plan 文件需要定义哪些凭证要迁移、迁移到哪里、怎么验证?

**方案**: `targets` 数组,每个 target 定义:
- **路径**: 凭证在配置里的位置 (如 `auth.apiKey`)
- **来源**: 迁移后的 SecretRef 来源 (如 `env:OPENAI_API_KEY`)
- **验证**: 迁移后的验证方式 (如检查环境变量是否存在)

**洞察**: 迁移前验证来源是否存在,避免"迁移成功但凭证获取失败"。

**权衡**:
- ✓ 完整: 定义迁移的所有细节
- ✓ 安全: 迁移前验证

### 幂等性

**问题**: CI/CD 可能多次执行 migration (如重试失败的 deployment),不是幂等的会报错或出错?

**方案**: `openclaw secrets apply` 是**幂等的** (idempotent): 多次执行同一个 plan,结果相同。

**洞察**: 如果基础设施已经是目标状态,就不做任何变更。

**权衡**:
- ✓ 安全: 多次执行不会出错
- ✓ 可重试: CI/CD 可以重试

**模式**: Terraform apply——幂等,多次执行同一个 plan 结果相同。

### 失败时不修改

**问题**: Plan 里的任何一个 target 不符合规则,部分修改会导致状态不一致?

**方案**: **原子性** (atomicity): 任何一个 target 不符合规则,整个 apply 失败,**不修改任何配置**。

**洞察**: 要么全部成功,要么全部失败,没有中间状态。

**权衡**:
- ✓ 一致: 不会"一半明文、一半 SecretRef"
- ✓ 可恢复: 失败后状态不变,可以修复后重试

**模式**: 数据库事务原子性——所有操作要么全部成功,要么全部回滚。
