# Configuration — Tools and Custom Providers

## 架构精读

> 跳过不影响阅读翻译正文。

### 工具配置文件的层级——为什么需要配置文件 + 允许 + 禁止 三层？

工具权限控制用三层叠加：

1. **配置文件**（基线）：`minimal`/`coding`/`messaging`/`full` 四种预定义集合
2. **允许**（显式允许）：在配置文件基础上加工具
3. **禁止**（显式禁止）：从配置文件中减工具

优先级：禁止 > 允许 > 配置文件。

这跟 AWS IAM 策略是一个思路——托管策略提供基线。内联策略做细粒度允许/禁止，禁止始终优先于允许（安全设计：显式禁止 > 显式允许 > 默认）。

关键设计是**纵深防御**。即使配置文件是 `full`，禁止也能禁止危险工具（如 `shell_exec`）。

### 沙箱工具策略——为什么 MCP/插件工具需要额外关卡？

MCP 服务器作为插件所属的工具暴露在 `bundle-mcp` 插件标识下。当沙箱模式是 `all` 或 `non-main` 时，`tools.sandbox.tools` 作为额外关卡控制沙箱会话的 MCP/插件工具可见性。

这跟 Docker 的能力限制是一个思路——即使容器有网络访问，`--cap-drop` 也能禁止特定能力（如 `NET_RAW`）。沙箱工具策略防止 MCP 服务器绕过沙箱限制。

代价是配置稍复杂（需要在沙箱工具允许列表里加 MCP 条目）。但这防止了“恶意 MCP 服务器在沙箱里执行危险操作”。

### tools.elevated——为什么需要“逃出沙箱”的机制？

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

这跟 Docker 的 `--privileged` 是一个思路——正常情况下容器隔离，但某些操作需要宿主机权限（如挂载文件系统、访问硬件）。提升执行权限完全绕过沙箱。

代价是安全风险（代理可以在宿主机上执行任意命令）。按代理覆盖只能进一步限制（不能放宽），`/elevated` 命令按会话存储状态。

### 自定义提供商基础 URL——为什么是网络信任决策？

配置自定义/本地提供商基础 URL 代表了对模型 HTTP 请求的网络信任决策：

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

这跟 CORS 的可信来源是一个思路——允许特定来源通过受保护的请求路径。自定义基础 URL 自动信任其精确配置的来源（除了元数据和链路本地地址）。

设计原因是**安全边界**。默认情况下 OpenClaw 只访问已知提供商（OpenAI/Anthropic/Google），自定义基础 URL 显式扩展信任边界。

---

Tool policy, experimental toggles, provider-backed tool config, and custom provider / base-URL setup.

Tool 策略、实验性功能开关、provider-backed tool 配置，以及 custom provider / base-URL 设置。