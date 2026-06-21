# Secrets Apply Plan Contract

## 架构精读

> 跳过不影响阅读翻译正文。

### "Apply fails before mutating"——为什么先校验再变更？

`openclaw secrets apply` 的核心合约是：校验失败时立即中止，不提交任何变更。

这跟 Terraform 计划 + 应用是一个思路——计划生成变更计划，应用前做一致性校验（资源存在性、权限、依赖），任一失败则整个应用中止。区别是 Terraform 可以部分应用，OpenClaw 是全有或全无。

设计原因是**原子性**。如果计划有 10 个目标，第 5 个校验失败，前 4 个也不应该被应用——否则状态会不一致（部分机密更新了，部分没更新）。

### Plan file shape——为什么 target 必须包含 type + path + segments？

计划是 JSON 结构，包含 `targets` 数组。每个目标必须定义类型、路径、路径段和引用详情：

```json5
{
  targets: [
    {
      type: "env",
      path: "providers.openai.apiKey",
      segments: ["providers", "openai", "apiKey"],
      ref: { $env: "OPENAI_API_KEY" }
    }
  ]
}
```

这跟 Kubernetes 资源的 metadata/spec 结构是一个思路。类型决定处理逻辑，路径标明点号表示法位置。路径段是路径的数组形式，方便程序处理。引用则指向实际值。

限制是路径不能为空、不能包含 `__proto__`（防原型污染），ID 必须和路径中编码的 ID 精确匹配。

### Provider upserts/deletes——为什么在 target 处理前执行？

计划可选包含 `providerUpserts`（添加提供者定义）和 `providerDeletes`（删除别名）。这些在目标处理前执行，让新别名可以立即被目标引用：

```json5
{
  providerUpserts: [{ id: "vault", type: "exec", command: "vault kv get" }],
  targets: [{ type: "exec", provider: "vault", ... }]  // 引用刚 upsert 的 vault
}
```

这跟 SQL 的 DDL before DML 是一个思路——先 CREATE TABLE，再 INSERT。如果顺序反过来（先处理目标再创建/更新提供者），目标引用的提供者还不存在。

### Exec 提供者同意——为什么空运行和写入模式行为不同？

`--dry-run` 默认跳过执行检查（不真的跑执行命令），写入模式严格拒绝（除非 `--allow-exec`）。两种场景都需要显式标志授权基于执行的提供者。

这跟 `terraform plan` vs `terraform apply` 是一个思路——计划只生成执行计划不真的执行（安全），应用真的执行（需要授权）。区别是 OpenClaw 的空运行更宽松（默认跳过执行），写入模式更严格（默认拒绝执行）。

### 失败行为——为什么不部分应用？

任一 target 校验失败时，整个流程立即中止并显示错误信息。不提交任何变更。

这跟数据库事务是一个思路——全有或全无，要么全部成功，要么全部失败。区别是数据库可以回滚，OpenClaw 根本不提交（没有"回滚"的概念，因为什么都没发生）。

代价是"一个目标错误导致整个计划失败"。但这防止了"部分机密更新"导致的状态不一致。

---

This document outlines the strict validation rules and structural requirements that the "openclaw secrets apply" command enforces before altering any system configuration.

本文档概述了 `openclaw secrets apply` 命令在修改任何系统配置前强制执行的严格校验规则和结构要求。

When validation fails for any target, the process immediately halts and displays an error message. Crucially, no configuration changes are committed if the plan contains invalid data.

当任一目标校验失败时，流程立即中止并显示错误信息。关键的是，如果 plan 包含无效数据，不会提交任何配置变更。
