# Configuration — tools and custom providers

## 架构精读

> 跳过不影响阅读翻译正文。

### Tool profile——预定义的工具集基线

`tools.profile` 设置一个**基线工具集**,决定 agent 默认能用哪些工具:

```json
{
  tools: {
    profile: "coding"
  }
}
```

内置 profile 包括:
- **coding**: 代码相关工具(执行 shell、编辑文件、搜索代码)
- **minimal**: 最小工具集(只允许基本操作,不允许危险操作)
- **full**: 所有工具(包括危险操作,如删除文件)

**为什么需要 profile?** 因为不同场景需要不同的工具权限:
- Coding agent: 需要执行 shell、编辑文件,但不能删除系统文件
- Customer support agent: 只需要搜索知识库,不需要执行任何系统命令
- 如果所有 agent 都有全部工具权限,一个被恶意 prompt 注入的 agent 可能执行危险操作

Profile 是**基线**,不是最终权限。最终权限 = profile(基线)+ allow(额外允许)+ deny(额外禁止)。

### tools.allow / tools.deny——在基线上叠加

`tools.allow` 和 `tools.deny` 在 profile 基线上叠加,做细粒度控制:

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
- Profile 允许 shell_exec,但 deny 禁止了 → 最终不能用
- Profile 不允许 web_search,但 allow 添加了 → 最终能用
- 如果 allow 和 deny 冲突(同一工具同时在两个列表里),deny 优先

**为什么 deny 优先于 allow?** 这是安全设计的原则——**显式禁止 > 显式允许 > 默认允许**。如果 allow 优先,一个不小心 allow 了危险工具,deny 就失效了。Deny 优先保证: 如果你明确禁止了某个工具,不管其他地方怎么配,它就是不能用。

这跟 **防火墙规则**是一个思路——iptables 的规则是按顺序匹配的,但 `DROP` 规则优先于 `ACCEPT`。OpenClaw 的 deny 优先也是同样: 安全规则(禁止)优先于功能规则(允许)。

### Tool groups——按功能分组

Tools 可以按功能分组,方便批量管理:

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

**为什么需要分组?** 因为工具太多,逐个管理麻烦。分组后可以:
- 一次性允许/禁止一组工具(如"禁止所有 web 工具")
- 按场景选择工具集(如"coding agent 用 file 组 + shell 组")
- 文档和沟通更清晰(如"这个 agent 只能用 file 组工具")

这跟 Linux 的用户组是一个思路——`usermod -aG docker user` 把用户加入 docker 组,自动获得 docker 相关权限。OpenClaw 的 tool groups 也是同样: 工具分组后,可以按组管理权限。

### MCP 和 plugin 工具在沙盒策略里的位置

MCP(Model Context Protocol,一种让 agent 调用外部工具的标准协议)和 plugin 工具也受 sandbox tool policy 控制:

**sandbox tool policy** 决定 agent 在沙盒(隔离环境)里能用哪些工具。MCP 工具和 plugin 工具不是"特殊"的,它们跟内置工具一样受策略控制。

**为什么这样设计?** 因为 MCP/plugin 工具可能比内置工具更危险:
- 内置工具的权限是已知的(如 shell_exec 需要 allowlist)
- MCP/plugin 工具是第三方提供的,可能有未知权限(如读取文件、网络请求)

如果 MCP/plugin 工具不受策略控制,攻击者可以写一个恶意 plugin,绕过所有安全检查。把它们纳入 sandbox tool policy,跟内置工具一样受 allow/deny 控制,保证安全一致性。

### tools.codeMode——代码模式 vs 对话模式

`tools.codeMode` 控制 agent 的行为模式:

- **codeMode: true**: agent 默认执行代码操作(如编辑文件、运行命令),适合 coding agent
- **codeMode: false**: agent 默认对话模式(如回答问题、搜索信息),适合 support agent

**为什么需要这个开关?** 因为不同场景下 agent 的"默认意图"不同:
- 用户说"帮我改一下这个文件",coding agent 应该直接改,support agent 应该问"你要改什么"
- 用户说"搜索一下",coding agent 可能想搜索代码,support agent 想搜索知识库

codeMode 不是限制 agent 能做什么(那是 allow/deny 的职责),而是影响 agent 的**默认行为倾向**。

### tools.byProvider——按 provider 配置工具

不同 LLM provider 对工具的支持不同,`tools.byProvider` 可以按 provider 配置:

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

**为什么需要按 provider 配置?** 因为不同 provider 的工具实现有差异:
- OpenAI 支持并行 tool call(同时调多个工具)
- Anthropic 的某些模型不支持并行 tool call
- 如果统一配置并行,Anthropic 调用会报错

这跟 **浏览器兼容性**是一个思路——同一个 web API,Chrome 支持,Safari 可能不支持。开发者需要按浏览器做适配。OpenClaw 的 `tools.byProvider` 也是同样: 按 provider 做工具适配。
