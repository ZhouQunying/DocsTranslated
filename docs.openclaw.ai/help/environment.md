# Environment variables

## 架构精读

> 跳过不影响阅读翻译正文。

### 环境变量优先级——为什么"永不覆盖现有值"？

OpenClaw 从多个位置收集配置，但"永不覆盖现有值"：

- **配置来源**：环境变量、dotenv 文件、JSON 配置、默认值
- **优先级规则**：已设置的值不会被后续来源覆盖
- **安全限制**：本地工作空间 dotenv 文件被视为不可信，系统剥离认证密钥和受保护的运行时指令

这跟 CSS 层叠的 `!important` 是一个思路——一旦声明了 `!important`，后续规则无法覆盖。"永不覆盖"确保"显式设置的配置"不会被意外覆盖，安全限制确保"不可信来源"无法注入敏感配置。

### 核心变量——为什么需要这些？

关键变量及其用途：

- **`OPENCLAW_HOME`**：覆盖基础目录（替代 OS 主目录），用于内部路径计算
- **`OPENCLAW_STATE_DIR`**：指定自定义状态存储目录
- **`OPENCLAW_CONFIG_PATH`**：指定主 JSON 配置文件的替代位置
- **`OPENCLAW_LOG_LEVEL`**：修改日志详细程度（优先级高于内部设置）
- **`OPENCLAW_THEME`**：终端界面主题（浅色/深色）
- **`OPENCLAW_LOAD_SHELL_ENV`**：启用通过用户登录命令行检索缺失键
- **`NODE_EXTRA_CA_CERTS`**：修复 nvm 管理的 Node 安装的 HTTPS 证书错误

这跟 Linux 的 `PATH`/`HOME`/`LANG` 是一个思路——这些变量控制"基础行为"（搜索路径、主目录、语言），几乎所有程序都依赖它们。OpenClaw 的核心变量同样控制"基础行为"（状态位置、配置位置、日志级别）。

### 安全边界——为什么本地 dotenv 被视为不可信？

本地工作空间 dotenv 文件（如项目根目录的 `.env`）被视为不可信：

- **剥离认证密钥**：防止恶意项目注入 API 密钥
- **剥离受保护指令**：防止覆盖关键运行时配置
- **安全存储位置**：全局状态目录、主进程环境、JSON 配置块

这跟浏览器的同源策略是一个思路——不同来源的脚本无法访问彼此的 Cookie/LocalStorage，防止跨站攻击。本地 dotenv 被视为"外部来源"，防止"恶意项目"通过 `.env` 文件注入敏感配置。

### 遗留变量——为什么完全忽略？

子进程接收特定上下文标签（标识如何被生成）。过时的变量前缀（来自旧版本）被完全忽略。

这跟 Python 2 → Python 3 的迁移是一个思路——`print` 语句 vs `print()` 函数，旧语法不再支持。完全忽略遗留变量避免"旧配置"意外影响新行为，强制用户迁移到新变量名。

---

Environment variables configuration: multiple sources (env vars, dotenv files, JSON config, defaults) with "never override existing values" rule. Local workspace dotenv files treated as untrusted (auth secrets and protected runtime directives stripped). Key variables: `OPENCLAW_HOME` (base directory override), `OPENCLAW_STATE_DIR` (custom state folder), `OPENCLAW_CONFIG_PATH` (alternative config location), `OPENCLAW_LOG_LEVEL` (verbosity), `OPENCLAW_THEME` (light/dark), `OPENCLAW_LOAD_SHELL_ENV` (retrieve missing keys via login shell), `NODE_EXTRA_CA_CERTS` (fix HTTPS cert errors for nvm-managed Node). Secure credential storage locations: global state folder, primary process environment, JSON config block. Legacy variable prefixes completely ignored.

环境变量配置。多来源：环境变量、dotenv 文件、JSON 配置、默认值，"永不覆盖现有值"规则。本地工作空间 dotenv 文件被视为不可信（剥离认证密钥和受保护运行时指令）。

关键变量：`OPENCLAW_HOME`（覆盖基础目录）、`OPENCLAW_STATE_DIR`（自定义状态目录）、`OPENCLAW_CONFIG_PATH`（替代配置位置）、`OPENCLAW_LOG_LEVEL`（详细程度）、`OPENCLAW_THEME`（浅色/深色）。

`OPENCLAW_LOAD_SHELL_ENV`（通过登录命令行检索缺失键）、`NODE_EXTRA_CA_CERTS`（修复 nvm 管理的 Node 的 HTTPS 证书错误）。

安全凭证存储位置：全局状态目录、主进程环境、JSON 配置块。遗留变量前缀完全忽略。

架构精读："永不覆盖"确保显式配置不被意外覆盖。本地 dotenv 被视为"外部来源"，防止恶意项目注入敏感配置。核心变量控制"基础行为"（状态位置、配置位置、日志级别）。
