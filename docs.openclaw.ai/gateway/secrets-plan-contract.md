# Secrets apply plan contract

## 架构精读

> 跳过不影响阅读翻译正文。

### Plan contract——凭证迁移的严格契约

`openclaw secrets apply` 命令把明文凭证迁移到 SecretRef,但它遵循一个**严格的契约**(contract):

```bash
openclaw secrets apply --from plan.json
```

`plan.json` 定义了要迁移哪些凭证、迁移到哪里、怎么迁移。

**为什么需要严格的契约?** 因为凭证迁移是高风险操作:
- 迁移错了 → agent 无法连接 provider(凭证丢失)
- 迁移到错误的位置 → 凭证泄露(安全风险)
- 迁移不完整 → 部分明文、部分 SecretRef,状态混乱

契约确保: 如果迁移计划不符合规则,命令直接失败,**不会**修改任何配置。这比"迁移一半出错了"安全得多。

**这跟数据库 migration 的 contract 是一个思路**——数据库 migration 工具(如 Flyway、Liquibase)在执行 migration 前检查: 如果 migration 脚本不符合规则(如缺少版本号、SQL 语法错误),直接拒绝执行,不会部分执行。OpenClaw 的 secrets apply 也是同样: 不符合契约就拒绝,不会部分迁移。

### Targets array——迁移目标的列表

Plan 文件包含一个 `targets` 数组,每个 target 定义:
- **路径**: 要迁移的凭证在配置里的位置(如 `auth.apiKey`)
- **来源**: 迁移后的 SecretRef 来源(如 `env:OPENAI_API_KEY`)
- **验证**: 迁移后的验证方式(如检查环境变量是否存在)

**为什么需要验证?** 因为迁移后如果 SecretRef 指向的来源不存在(如环境变量没设置),agent 就无法获取凭证,直接报错。验证在迁移前检查来源是否存在,避免"迁移成功了但凭证获取失败"的问题。

### 幂等性——重复执行不会出错

`openclaw secrets apply` 是**幂等的**(idempotent): 多次执行同一个 plan,结果相同,不会重复迁移或报错。

**为什么需要幂等?** 因为 CI/CD 可能多次执行 migration(如重试失败的 deployment)。如果 migration 不是幂等的,第二次执行会报错(如"凭证已经迁移过了")或出错(如重复迁移导致配置混乱)。

**这跟 Terraform 的 apply 是一个思路**——`terraform apply` 是幂等的,多次执行同一个 plan,结果相同(如果基础设施已经是目标状态,就不做任何变更)。OpenClaw 的 secrets apply 也是同样: 多次执行,结果相同。

### 失败时不修改——原子性

如果 plan 里的任何一个 target 不符合规则(如路径不存在、来源无效),整个 apply 失败,**不修改任何配置**。

**为什么需要原子性?** 因为部分修改会导致状态不一致:
- 一半凭证是明文,一半是 SecretRef
- 用户不知道"哪些迁移了、哪些没迁移"
- 恢复困难(需要手动把 SecretRef 改回明文,或者继续迁移剩下的)

原子性保证: 要么全部成功,要么全部失败,没有中间状态。

**这跟数据库事务的原子性**是一个思路——事务里的所有操作要么全部成功,要么全部回滚,没有部分成功。OpenClaw 的 secrets apply 也是同样: 所有 target 要么全部迁移,要么全部不迁移。
