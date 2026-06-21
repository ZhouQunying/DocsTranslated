# Configuration Reference

## 架构精读

> 跳过不影响阅读翻译正文。

### 配置域的分治——为什么拆成多页？

配置参考把配置域拆成多个独立页面：

- **频道** → config-channels 页
- **代理/会话/消息/对话** → config-agents 页
- **工具/自定义提供商** → config-tools 页
- **模型/MCP/技能/插件/浏览器/网关/钩子/密钥/日志/诊断/定时任务** → 本页

这跟 K8s API 参考的分组是一个思路——资源太多时按组/版本分页，不然一个页面 69KB 根本读不动。

关键设计是**关注点分离**。运维者配频道时不需要看代理字段，开发者配工具时不需要看网关字段。拆页后每页只聚焦一个域。

### `$include` 配置拆分——为什么支持多文件？

OpenClaw 支持 `$include` 把配置拆成多个文件：

```json5
{
  $include: ["channels.json5", "agents.json5"],
  gateway: { port: 18789 }
}
```

这跟 Helm 的 `values-*.yaml` 多文件覆盖是一个思路——大团队按职责分文件（运维管网关，开发管代理）。合并时深度合并（数组追加，对象递归合并）。

限制是最多嵌套 10 层（防无限递归），路径相对于主配置文件。

### SecretRef——为什么不让配置直接存明文？

`secrets` 域支持 SecretRef（`env`/`file`/`exec` 三种来源），把 API 密钥从配置明文中抽离：

```json5
{
  providers: {
    openai: {
      apiKey: { $env: "OPENAI_API_KEY" }
    }
  }
}
```

这跟 K8s Secret + Vault Agent 是一个思路——配置和凭证分离，凭证由专门系统管理（环境变量、文件、CLI 命令如 `op read`/`vault kv get`）。

代价是配置稍复杂。但这防止了“配置文件提交到 Git 泄露 API 密钥”的事故。

---

Core config reference for `~/.openclaw/openclaw.json`. The config format is JSON5 (comments + trailing commas allowed), and all fields are optional with safe defaults when omitted.

`~/.openclaw/openclaw.json` 核心配置参考。配置格式是 JSON5（允许注释 + 末尾逗号），所有字段可选，省略时使用安全默认值。