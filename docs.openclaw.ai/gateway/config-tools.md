# Tools and Custom Providers

**总结：** Tool 策略（profile/group/sandbox/access restriction）+ 自定义 provider 和 base URL 配置。agents 和 channels 参数见各自文档。

> **类比：AWS IAM Policy + API Gateway Custom Authorizer。** IAM Policy 用 allow/deny 控制权限基线（Managed Policy 预定义、Inline Policy 自定义），API Gateway Custom Authorizer 接入外部认证服务。OpenClaw tools 类似——`tools.profile` 设基线（`coding`/`minimal`/`full`），`allow`/`deny` 叠加细粒度控制（deny > allow > profile 优先级），group 按功能分组批量管理，sandbox/plugin policy 控制隔离环境和第三方 tool 可见性，custom provider 接入本地或第三方 LLM（指定 endpoint/auth/model catalog）。
>
> **架构要点：** `tools.profile`：基线 tool 集合（`coding` 代码相关、`minimal` 最小无危险、`full` 全量含危险）；`tools.allow`/`tools.deny`：叠加控制，优先级 deny > allow > profile（安全设计：显式禁止 > 显式允许 > 默认）；`tools.groups`：按功能分组（如 `web: [web_search, web_fetch]`），按组批量允许/禁止；sandbox policy：MCP/plugin tool 与内置 tool 受相同 allow/deny 控制，防止恶意 plugin 绕过；`tools.codeMode`：控制默认行为倾向（`true` 倾向代码操作、`false` 倾向对话），不是能力限制；access restriction：按全局规则/specific provider/sender identity/elevated privilege 过滤 tool 可用性；execution + loop detection：background timeout、循环检测防止重复操作；web + media：web search/fetch 参数、inbound audio/image/video 处理参数；session + subagent：跨 session tool 可见性、子进程管理；`tools.byProvider`：按 provider 适配（如 `parallelToolCalls` OpenAI true/Anthropic false）；custom provider：connection protocol、transport override、model catalog attribute、endpoint + auth 配置，支持本地 LLM（Ollama/vLLM）和第三方服务。
