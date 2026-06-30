# `openclaw plugins`

## 架构精读

> 跳过不影响阅读翻译正文。

### 插件管理——为什么需要专门的命令？

`openclaw plugins` 管理插件（扩展功能）：

- **`plugins list`**：列出已安装插件（名称 + 版本 + 状态）
- **`plugins install <name>`**：安装插件
- **`plugins uninstall <name>`**：卸载插件
- **`plugins enable/disable <name>`**：启用/禁用插件

这跟 `kubectl get deployments` / `kubectl apply` / `kubectl delete` 是一个思路——资源列表 + 安装 + 卸载 + 启用/禁用。

### 插件 vs 技能——为什么区分？

- **插件**：代码扩展（npm 包，运行时加载）
- **技能**：提示词扩展（Markdown 文件，静态注入）

这跟 VS Code extension vs snippet 是一个思路——extension 是代码（动态功能），snippet 是文本模板（静态快捷方式）。插件适合"添加新工具"，技能适合"预设行为模式"。

---

Manages plugins (code extensions): `plugins list` (installed with version/status), `plugins install <name>`, `plugins uninstall <name>`, `plugins enable/disable <name>`. Plugins are npm packages loaded at runtime; skills are Markdown prompt templates injected statically.

管理插件（代码扩展）：`plugins list`（已安装，含版本/状态）、`plugins install <name>`、`plugins uninstall <name>`、`plugins enable/disable <name>`。插件是运行时加载的 npm 包；技能是静态注入的 Markdown 提示词模板。
