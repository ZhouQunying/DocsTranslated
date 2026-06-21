# Configuration — Tools and Custom Providers

## 架构精读

> 跳过不影响阅读翻译正文。

### Tool profile 的层级——为什么需要 profile + allow + deny 三层？

Tool 权限控制用三层叠加：

1. **profile**（基线）：`minimal`/`coding`/`messaging`/`full` 四种预定义集合
2. **allow**（显式允许）：在 profile 基础上加 tool
3. **deny**（显式禁止）：从 profile 中减 tool

优先级：deny > allow > profile。

这跟 AWS IAM Policy 是一个思路——Managed Policy 提供基线，Inline Policy 做细粒度 allow/deny，deny 始终优先于 allow（安全设计：显式禁止 > 显式允许 > 默认）。

关键设计是**defense in depth**。即使 profile 是 `full`，deny 也能禁止危险 tool（如 `shell_exec`）。

### Sandbox tool policy——为什么 MCP/plugin tool 需要额外 gate？

MCP server 作为 plugin-owned tool 暴露在 `bundle-mcp` plugin 标识下。当 sandbox mode 是 `all` 或 `non-main` 时，`tools.sandbox.tools` 作为额外 gate 控制 sandbox session 的 MCP/plugin tool 可见性。

这跟 Docker 的 capability 限制是一个思路——即使容器有 network access，`--cap-drop` 也能禁止特定能力（如 `NET_RAW`）。Sandbox tool policy 防止 MCP server 绕过沙箱限制。

代价是配置稍复杂（需要在 sandbox tool allowlist 里加 MCP entry）。但这防止了"恶意 MCP server 在沙箱里执行危险操作"。

### tools.elevated——为什么需要"逃出沙箱"的机制？

`tools.elevated` 控制沙箱外的执行权限：

```json5
{
  tools: {
    elevated: {
      exec: true  // 允许在 host 上执行命令
    }
  }
}
```

这跟 Docker 的 `--privileged` 是一个思路——正常情况下容器隔离，但某些操作需要 host 权限（如挂载文件系统、访问硬件）。Elevated exec 完全绕过沙箱。

代价是安全风险（agent 可以在 host 上执行任意命令）。Per-agent override 只能进一步限制（不能放宽），`/elevated` command 按 session 存储状态。

### Custom provider base URL——为什么是网络信任决策？

配置 custom/local provider base URL 代表了对 model HTTP 请求的网络信任决策：

```json5
{
  providers: {
    custom: {
      baseUrl: "http://localhost:1234/v1",  // LM Studio
      adapter: "openai-completions"
    }
  }
}
```

这跟 CORS 的 trusted origin 是一个思路——允许特定 origin 通过 guarded fetch path。Custom base URL 自动信任其精确配置的 origin（除了 metadata 和 link-local 地址）。

设计原因是**安全边界**。默认情况下 OpenClaw 只访问已知 provider（OpenAI/Anthropic/Google），custom base URL 显式扩展信任边界。

---

Tool policy, experimental toggles, provider-backed tool config, and custom provider / base-URL setup.

Tool 策略、实验性功能开关、provider-backed tool 配置，以及 custom provider / base-URL 设置。