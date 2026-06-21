# Secrets Management

## 架构精读

> 跳过不影响阅读翻译正文。

### SecretRef 的 eager resolve——为什么不 lazy？

OpenClaw 的 SecretRef 在 activation 时 eager resolve 到内存快照，而非请求路径上 lazy resolve：

```json5
{
  providers: {
    openai: {
      apiKey: { $env: "OPENAI_API_KEY" }  // 启动时解析，非每次请求解析
    }
  }
}
```

这跟 Vault Agent template 是一个思路——启动时一次性解析所有 secret 到内存，运行时从快照读取。好处是 fail-fast（启动时发现问题）和 atomic swap（热重载时原子替换，无中间状态）。

代价是 secret provider 挂了时，热重载进入 degraded 状态（保留 last-known-good 快照直到恢复）。但这比"每次请求都可能失败"好得多。

### Agent-access boundary——为什么 SecretRef 不是进程隔离？

SecretRef 保护的是配置文件中的凭证（不存明文），但不提供进程隔离——agent 仍然可以读取磁盘上的文件。

这跟 K8s Secret mount 是一个思路——Secret mount 到 pod 后，pod 内进程可以读取 mount 的文件。SecretRef 解决了"配置文件提交到 Git 泄露"的问题，但不解决"agent 运行时能读什么"的问题。

迁移完成的标志是：明文残留被 scrub + audit check 通过。预检检查确保 migration 前状态正确。

### Active-surface filtering——为什么只校验活跃的？

只在 effective active surface 上校验 SecretRef——inactive surface 上未解析的 ref 不阻止启动，只发非致命诊断 code。

这跟 K8s probe 的分级是一个思路——liveness probe 失败重启 pod（致命），就绪 probe 失败只从 service 摘除（非致命）。Inactive surface（如未启用的 channel）的 secret 失败不应该阻止整个 Gateway 启动。

### Exec provider consent——为什么需要 `--allow-exec`？

exec-based SecretRef（如 `op read`、`vault kv get`）需要显式 `--allow-exec` flag 授权。`--dry-run` 默认跳过执行检查，write mode 严格拒绝。

这跟 Docker `--privileged` 是一个思路——执行外部命令是高风险操作（可以跑任意代码），必须显式授权。默认拒绝防止"apply plan 时意外执行了恶意命令"。

### One-way safety policy——为什么不写 rollback backup？

系统故意不写包含历史明文的 rollback backup。预检和运行时 activation 必须在 commit 前成功。

这跟 Git 的 philosophy 是一个思路——一旦 commit 就不应该回滚到"更差的状态"（明文泄露）。如果 apply 失败，状态保持不变；如果成功，旧明文被 scrub。没有"回滚到明文"的路径。预检和运行时 activation 必须在 commit 前成功。

---

The system enables additive SecretRefs, allowing administrators to avoid keeping supported credentials as plaintext within configuration files.

系统支持 additive SecretRef，让管理员避免把受支持的凭证以明文形式保存在配置文件中。

Secrets are eagerly resolved into an in-memory snapshot during activation rather than lazily on request paths. This approach ensures fail-fast startup behavior and atomic swap reloads to keep provider outages off hot paths.

Secret 在 activation 时 eager resolve 到内存快照，而非在请求路径上 lazy resolve。这种方式确保 fail-fast 启动行为和 atomic swap reload，让 provider 故障不影响热路径。
