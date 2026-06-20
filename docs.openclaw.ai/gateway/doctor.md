# Doctor

## 架构精读

> 跳过不影响阅读翻译正文。

### `openclaw doctor`——诊断 + 修复 + 迁移

`openclaw doctor` 是 OpenClaw 的**诊断和修复工具**,类似 `brew doctor`:

```bash
openclaw doctor
```

检查:
- 配置文件是否符合 schema(有没有拼写错误、字段缺失)
- 状态文件是否损坏(如 session 数据库、auth 数据库)
- 版本兼容性(配置是不是老版本的格式,需要迁移)
- 权限问题(如文件权限不对,进程无法读取)

修复:
- 自动修复简单问题(如添加缺失的默认字段)
- 提供修复建议(如"建议把明文 API key 改成 SecretRef")
- 迁移老版本配置到新版本格式

**为什么需要 doctor?** 因为 OpenClaw 的状态复杂(配置文件、数据库、auth 凭证、session 历史),手动检查太麻烦。Doctor 自动扫描,列出所有问题,提供修复方案。

**这跟 `brew doctor` 是一个思路**——Homebrew 的 doctor 检查系统状态(如权限、symlink、版本),列出问题,提供修复建议。OpenClaw 的 doctor 也是同样: 自动诊断 + 修复。

### `--yes`——自动确认所有修复

`--yes` 让 doctor 自动确认所有修复操作,不需要用户手动确认:

```bash
openclaw doctor --yes
```

**什么时候用?** CI/CD 或自动化脚本里,不能交互式确认。`--yes` 让 doctor 自动执行所有修复,不中断流程。

**风险**: 如果 doctor 的修复建议有问题(如误删配置),`--yes` 会自动执行,无法阻止。所以 `--yes` 适合**可信环境**(如 CI/CD 跑测试),不适合生产环境。

### `--fix`——应用推荐的修复

`--fix` 让 doctor 应用推荐的修复操作:

```bash
openclaw doctor --fix
```

**跟 `--yes` 的区别**:
- `--yes`: 确认所有操作(包括重启、删除文件)
- `--fix`: 只应用"推荐"的修复(如添加缺失字段、迁移格式),不执行危险操作(如删除文件)

`--fix` 更安全,适合日常使用。`--yes` 更激进,适合自动化场景。

### `--lint`——只检查,不修复

`--lint` 让 doctor 只检查问题,不修复:

```bash
openclaw doctor --lint
```

**什么时候用?** 想先看看有什么问题,再决定是否修复。`--lint` 是"只读"模式,不修改任何文件。

**这跟 ESLint 是一个思路**——ESLint 检查代码问题,列出错误,但不自动修复(除非用 `--fix`)。OpenClaw 的 doctor `--lint` 也是同样: 只检查,不修复。

### `--fix --force`——强制修复

`--fix --force` 让 doctor 强制应用修复,即使有风险:

```bash
openclaw doctor --fix --force
```

**什么时候用?** 配置文件严重损坏,普通 `--fix` 无法修复。`--force` 会做更激进的修复(如删除损坏的数据库、重建配置文件)。

**风险**: 可能丢失数据(如删除损坏的 session 数据库)。只在普通 `--fix` 失败时使用。

### `--non-interactive`——非交互模式

`--non-interactive` 让 doctor 不显示交互式提示(如"是否重启 Gateway?"):

```bash
openclaw doctor --non-interactive
```

**什么时候用?** CI/CD 或自动化脚本里,不能交互式回答。`--non-interactive` 让 doctor 跳过所有交互式提示,使用默认值。

**跟 `--yes` 的区别**:
- `--yes`: 自动确认所有操作
- `--non-interactive`: 跳过交互式提示,但不一定执行操作(如"是否重启"的默认值是"否",就不重启)

`--non-interactive` 更安全,适合不想自动执行危险操作的场景。

### Doctor 的输出——可操作的修复步骤

Doctor 的输出不是"有 X 个问题",而是"问题 X: 建议执行 Y 来修复":

```
[WARNING] config.auth.apiKey is plaintext
  Fix: Run `openclaw secrets apply` to migrate to SecretRef

[ERROR] sessions.db is corrupted
  Fix: Delete ~/.openclaw/sessions.db and restart Gateway
```

**为什么输出可操作的步骤?** 因为"有问题"不够,用户需要知道"怎么修复"。如果 doctor 只说"配置文件有问题",用户不知道怎么修。Doctor 提供具体的修复命令,用户可以直接复制粘贴执行。

**这跟 `npm audit` 是一个思路**——`npm audit` 不只说"有漏洞",还说"运行 `npm audit fix` 来修复"。OpenClaw 的 doctor 也是同样: 问题 + 修复建议。
