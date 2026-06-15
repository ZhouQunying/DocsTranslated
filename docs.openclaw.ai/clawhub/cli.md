# ClawHub CLI

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
