# ClawHub CLI

## 架构精读

> 跳过不影响阅读翻译正文。

### Skills vs Plugins——两种包的安装路径为什么不同？

`openclaw skills install <slug>` 安装到工作区的 `skills/` 目录——它们是**本地文本文件**，agent 在推理时读取。安装目标是文件系统路径。

`openclaw plugins install clawhub:<package>` 安装到 Node.js 模块路径——它们是**可执行代码包**，需要被 Gateway 加载和运行。安装目标是 Node.js 运行时。

这导致两种包的解析机制完全不同：
- Skills 通过 slug 解析到 ClawHub 注册表记录，下载文件到 `skills/`
- Plugins 通过 `clawhub:` 前缀识别安装源，走 npm 兼容的包解析流程

`clawhub:` 前缀是一个显式信号——告诉 OpenClaw"从 ClawHub 解析这个包，而不是从 npm 或其他源"。这避免了歧义：`openclaw plugins install foo` 可能指 npm 上的 `foo`，也可能指 ClawHub 上的 `foo`。`clawhub:foo` 消除歧义。

### `--global` vs 本地安装——作用域选择

技能安装默认到工作区 `skills/`（本地），加 `--global` 到共享托管目录（全局）。这跟 npm 的 `--global` 是一个思路：

- **本地安装**：只在当前工作区生效，不同工作区可以有不同版本的同一技能
- **全局安装**：所有工作区共享，适合通用技能（如通用编码助手）

全局 vs 本地的冲突解决策略跟 Node.js 的模块解析一样：本地优先。工作区的 `skills/` 目录里有同名技能时，全局版本被覆盖。

---

OpenClaw 为 ClawHub 提供两个命令行入口:

- `openclaw skills` 和 `openclaw plugins` 在 OpenClaw 内部安装和管理 ClawHub 包
- 独立的 `clawhub` CLI 处理发布者工作流,如登录、发布、转移和同步

## 发现和安装

当你需要为本地 OpenClaw agent 或 Gateway 安装或更新包时,使用 OpenClaw 命令。

```bash
openclaw skills search "calendar"
openclaw skills install <slug>
openclaw skills update <slug>
openclaw skills verify <slug>

openclaw plugins search "calendar"
openclaw plugins install clawhub:<package>
openclaw plugins update <id-or-npm-spec>
```

技能安装默认目标是活跃工作区的 `skills/` 目录。添加 `--global` 安装到共享的托管技能目录。

插件安装使用 `clawhub:` 前缀,当你需要 ClawHub 解析而不是 npm 或其他安装源时。

## 发布和维护

为发布者工作流安装独立的 ClawHub CLI:

```bash
npm i -g clawhub
clawhub login
```

使用 `clawhub package publish` 发布插件包:

```bash
clawhub package publish your-org/your-plugin --dry-run
clawhub package publish your-org/your-plugin
clawhub package publish your-org/your-plugin@v1.0.0
```

使用 `clawhub skill publish` 发布技能文件夹:

```bash
clawhub skill publish ./skills/review-helper
clawhub skill publish ./skills/review-helper --version 1.0.0
```

当本地技能扫描状态或包所有权需要维护时,使用相关的独立命令:

```bash
clawhub sync --all
clawhub package transfer @old-owner/package --to new-owner
```

## 相关

- [`openclaw skills`](/cli/skills) - 本地技能搜索、安装、更新和验证
- [`openclaw plugins`](/cli/plugins) - 插件搜索、安装、更新和检查
- [ClawHub 发布](/clawhub/publishing) - 所有者作用域、发布验证和审核流程
- [创建技能](/tools/creating-skills) - 技能编写和发布流程
- [构建插件](/plugins/building-plugins) - 插件包编写

---

# 在 ClawHub 上发布
