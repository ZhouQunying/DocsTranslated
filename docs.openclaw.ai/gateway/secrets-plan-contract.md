# Secrets Apply Plan Contract

**总结：** apply plan 的严格合约——"apply fails before mutating configuration"，校验失败阻止任何变更。

> **类比：Terraform plan + apply。** Terraform plan 生成变更计划（哪些 resource 创建/更新/删除），apply 执行计划前校验一致性。OpenClaw SecretRef apply plan contract 类似——plan 是 JSON 文件（target array + optional provider upsert/delete），apply 前逐 target 校验（path 格式、scope 合规、ID match、prohibited segment 检查），任一失败则整个 apply 中止，不产生任何变更。
>
> **架构要点：** Plan file shape：JSON，必须包含 `targets` array（apply 命令的目标列表）；provider upsert/delete：可选字段，随 plan 一起添加/删除 provider alias + individual target write；supported target scope：target 必须匹配 approved credential path（SecretRef surface 文档列出）；target type behavior：recognized type 必须匹配 normalized path structure（含 legacy alias）；path validation rules：每个 target 逐条检查（dot path 格式、prohibited segment 阻止、ID match 校验）；failure behavior：校验失败时 halt + 输出错误信息，不 commit 任何变更；exec provider consent：plan 包含 exec-based SecretRef 时必须显式 flag 同意；runtime + audit scope：reference-only profile entry 也纳入 runtime evaluation 和 audit scope；operator checks：CLI dry-run 校验 → apply 执行 → exec-containing plan 特殊处理。
