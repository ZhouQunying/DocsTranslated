# Configuration — tools and custom providers

## 架构精读

> 跳过不影响阅读翻译正文。

### Tool profile

**问题**: 不同场景需要不同工具权限?

**方案**: `tools.profile` 设置基线工具集:
```json
{
  tools: {
    profile: "coding"
  }
}
```

内置 profile:
- **coding**: 代码相关 (shell、编辑文件、搜索代码)
- **minimal**: 最小 (基本操作,无危险操作)
- **full**: 所有 (包括危险操作)

**洞察**: Profile 是基线,不是最终权限。最终权限 = profile + allow + deny。

**权衡**:
- ✓ 安全: 不同场景用不同 profile
- ✓ 简单: 一个字段设置基线

### tools.allow / tools.deny

**问题**: 需要在 profile 基线上做细粒度控制?

**方案**: Allow/deny 叠加:
```json
{
  tools: {
    profile: "coding",
    allow: ["web_search"],
    deny: ["shell_exec"]
  }
}
```

**优先级**: deny > allow > profile

**洞察**: Deny 优先于 allow = 安全设计原则 (显式禁止 > 显式允许 > 默认允许)。

**权衡**:
- ✓ 灵活: 可以添加/禁止特定工具
- ✓ 安全: deny 优先,防止误配置

**模式**: 防火墙规则——iptables 的 DROP 优先于 ACCEPT。

### Tool groups

**问题**: 工具太多,逐个管理麻烦?

**方案**: 按功能分组:
```json
{
  tools: {
    groups: {
      web: ["web_search", "web_fetch", "web_scrape"],
      file: ["file_read", "file_write", "file_list"]
    }
  }
}
```

**洞察**: 分组后按组管理权限,批量允许/禁止。

**权衡**:
- ✓ 简单: 一次性管理一组工具
- ✓ 清晰: 按场景选择工具集

**模式**: Linux 用户组——`usermod -aG docker user` 加入 docker 组。

### MCP 和 plugin 工具在沙盒策略里

**问题**: MCP/plugin 工具不受 sandbox tool policy 控制?

**方案**: MCP/plugin 工具跟内置工具一样受 allow/deny 控制。

**洞察**: MCP/plugin 工具可能比内置工具更危险 (第三方提供,权限未知),必须纳入策略控制。

**权衡**:
- ✓ 安全: 防止恶意 plugin 绕过安全检查
- ✓ 一致: 所有工具受相同策略控制

### tools.codeMode

**问题**: Agent 的默认行为倾向 (代码操作 vs 对话)?

**方案**: `tools.codeMode` 控制:
- **true**: 默认执行代码操作 (coding agent)
- **false**: 默认对话模式 (support agent)

**洞察**: codeMode 影响默认行为倾向,不是限制能力 (那是 allow/deny 的职责)。

**权衡**:
- ✓ 灵活: 不同场景用不同默认行为
- ✓ 清晰: 明确 agent 的定位

### tools.byProvider

**问题**: 不同 LLM provider 对工具支持不同?

**方案**: 按 provider 配置:
```json
{
  tools: {
    byProvider: {
      openai: {
        parallelToolCalls: true
      },
      anthropic: {
        parallelToolCalls: false
      }
    }
  }
}
```

**洞察**: 不同 provider 的工具实现有差异,需要按 provider 做适配。

**权衡**:
- ✓ 兼容: 每个 provider 用最合适的配置
- ✗ 复杂: 需要为每个 provider 配置

**模式**: 浏览器兼容性——同一 web API,Chrome 支持,Safari 可能不支持。
