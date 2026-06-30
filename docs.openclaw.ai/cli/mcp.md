# `openclaw mcp`

## 架构精读

> 跳过不影响阅读翻译正文。

### MCP 管理——为什么需要专门的命令？

`openclaw mcp` 管理 Model Context Protocol 服务器：

- **`mcp list`**：列出已配置 MCP 服务器
- **`mcp add <name> <command>`**：添加 MCP 服务器
- **`mcp remove <name>`**：移除 MCP 服务器
- **`mcp test <name>`**：测试 MCP 服务器连通性

这跟 Docker 的 `docker ps` / `docker run` / `docker rm` 是一个思路——容器（MCP 服务器）的列表、启动、移除、测试。

### MCP vs 插件——为什么区分？

- **MCP 服务器**：独立进程（通过 stdio/HTTP 通信）
- **插件**：进程内代码（直接加载到网关进程）

这跟微服务 vs 单体是一个思路——微服务（MCP 服务器）独立部署和扩展，单体（插件）共享进程资源。MCP 适合"独立工具集"，插件适合"深度集成"。

---

Manages Model Context Protocol servers: `mcp list` (configured servers), `mcp add <name> <command>`, `mcp remove <name>`, `mcp test <name>` (connectivity). MCP servers are independent processes (stdio/HTTP); plugins are in-process code. MCP suits independent toolsets; plugins suit deep integration.

管理 Model Context Protocol 服务器：`mcp list`（已配置服务器）、`mcp add <name> <command>`、`mcp remove <name>`、`mcp test <name>`（连通性）。MCP 服务器是独立进程（stdio/HTTP）；插件是进程内代码。MCP 适合独立工具集；插件适合深度集成。
