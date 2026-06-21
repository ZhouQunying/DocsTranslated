# Secrets Management

## 架构精读

> 跳过不影响阅读翻译正文。

### SecretRef 的即时解析——为什么不延迟？

OpenClaw 的 SecretRef 在激活时即时解析到内存快照，而非请求路径上延迟解析：

```json5
{
  providers: {
    openai: {
      apiKey: { $env: "OPENAI_API_KEY" }  // 启动时解析，非每次请求解析
    }
  }
}
```

这跟 Vault Agent template 是一个思路——启动时一次性解析所有机密到内存，运行时从快照读取。好处是快速失败（启动时发现问题）和原子替换（热重载时无中间状态）。

代价是机密提供者挂了时，热重载进入降级状态（保留最后已知良好快照直到恢复）。但这比"每次请求都可能失败"好得多。

### Agent-access boundary——为什么 SecretRef 不是进程隔离？

SecretRef 保护的是配置文件中的凭证（不存明文），但不提供进程隔离——agent 仍然可以读取磁盘上的文件。

这跟 K8s Secret mount 是一个思路——Secret mount 到 pod 后，pod 内进程可以读取 mount 的文件。SecretRef 解决了"配置文件提交到 Git 泄露"的问题，但不解决"agent 运行时能读什么"的问题。

迁移完成的标志是：明文残留被清除 + 审计检查通过。预检检查确保迁移前状态正确。

### Active-surface filtering——为什么只校验活跃的？

只在生效的活跃面上校验 SecretRef——非活跃面上未解析的引用不阻止启动，只发非致命诊断代码。

这跟 K8s 探针的分级是一个思路——存活探针失败重启 pod（致命），就绪探针失败只从服务摘除（非致命）。非活跃面（如未启用的频道）的机密失败不应该阻止整个 Gateway 启动。

### Exec 提供者同意——为什么需要 `--allow-exec`？

基于执行的 SecretRef（如 `op read`、`vault kv get`）需要显式 `--allow-exec` 标志授权。`--dry-run` 默认跳过执行检查，写入模式严格拒绝。

这跟 Docker `--privileged` 是一个思路——执行外部命令是高风险操作（可以跑任意代码），必须显式授权。默认拒绝防止"应用计划时意外执行了恶意命令"。

### 单向安全策略——为什么不写回退备份？

系统故意不写包含历史明文的回退备份。预检和运行时激活必须在提交前成功。

这跟 Git 的理念是一个思路——一旦提交就不应该回滚到"更差的状态"（明文泄露）。如果应用失败，状态保持不变；如果成功，旧明文被清除。没有"回滚到明文"的路径。预检和运行时激活必须在提交前成功。

---

The system enables additive SecretRefs, allowing administrators to avoid keeping supported credentials as plaintext within configuration files.

系统支持 additive SecretRef，让管理员避免把受支持的凭证以明文形式保存在配置文件中。

Secrets are eagerly resolved into an in-memory snapshot during activation rather than lazily on request paths. This approach ensures fail-fast startup behavior and atomic swap reloads to keep provider outages off hot paths.

Secret 在 activation 时 eager resolve 到内存快照，而非在请求路径上 lazy resolve。这种方式确保 fail-fast 启动行为和原子替换重载，让 provider 故障不影响热路径。
