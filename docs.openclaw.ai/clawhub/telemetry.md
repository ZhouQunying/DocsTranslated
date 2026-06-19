# Telemetry / 遥测

## 架构精读

> 跳过不影响阅读翻译正文。

### 安装计数——为什么需要遥测？

ClawHub 的遥测只做一件事：计算**聚合安装计数**。这跟 npm 的下载统计、Docker Hub 的 pull count、PyPI 的下载统计一样——给发布者和用户提供"这个包有多流行"的信号。

但 ClawHub 的遥测比 npm 更克制：
- **只在 CLI 登录时收集**——匿名用户不发送遥测
- **只在 `clawhub install` 时发送**——`openclaw skills install` 不发送
- **只发送包 slug**——不发送用户身份、机器信息、安装路径

这是隐私优先的设计。npm 的遥测更宽泛（所有 npm 命令都发送），ClawHub 只在最必要的时机收集最少数据。代价是安装计数可能偏低（只统计通过 `clawhub install` 安装的、已登录用户的安装），但这是隐私 vs 准确性的合理取舍。

---

ClawHub uses minimal CLI telemetry to compute aggregate install counts.

ClawHub 使用最小化的 CLI 遥测计算聚合安装计数。

## When telemetry is collected / 何时收集遥测

Telemetry is only sent when:

遥测仅在以下情况发送:

- You are logged in in the CLI.
  
  你在 CLI 中已登录。

- You run `clawhub install <slug>`.
  
  你运行 `clawhub install <slug>`。

- Telemetry is not disabled (see "How to disable" below).
  
  遥测未被禁用(参见下方"如何禁用")。

If you are not logged in, nothing is reported.

如果你未登录,不会报告任何内容。

## What we collect / 我们收集什么

On each reported `clawhub install`, the CLI sends one best-effort install event.

每次报告的 `clawhub install`,CLI 发送一个尽力而为的安装事件。

The event includes:

事件包括:

- `rootId`: a SHA-256 hash of the canonical root path (server never sees the raw path).
  
  规范根路径的 SHA-256 哈希(服务器永远看不到原始路径)。

- `rootLabel`: a short label derived from the last two path segments (home paths are shown with `~`).
  
  从最后两个路径段派生的短标签(主路径用 `~` 显示)。

- `slug`: the installed skill slug.
  
  已安装的技能短名称。

- `version`: the installed version, when known.
  
  已安装的版本(已知时)。

### What we do not collect / 我们不收集什么

- No raw absolute folder paths (only hashed `rootId` + a short display label).
  
  没有原始绝对文件夹路径(只有哈希的 `rootId` + 短显示标签)。

- No file contents.
  
  没有文件内容。

- No per-run logs, prompts, or other CLI output.
  
  没有每次运行的日志、提示或其他 CLI 输出。

## Install counts / 安装计数

ClawHub maintains aggregate counters per skill:

ClawHub 维护每个技能的聚合计数器:

- `installsAllTime`: unique users who have reported at least one CLI install for the skill.
  
  报告了至少一次该技能 CLI 安装的唯一用户。

- `installsCurrent`: unique users who have reported an install and have not deleted their telemetry.
  
  报告了安装且未删除其遥测的唯一用户。

## Transparency + user controls / 透明度 + 用户控制

ClawHub provides a private "Installed" tab on your own profile:

ClawHub 在你自己的个人资料上提供私有的"已安装"标签:

- Shows install telemetry associated with your account.
  
  显示与你账户关联的安装遥测。

- Includes a JSON export view.
  
  包含 JSON 导出视图。

- Includes a Delete telemetry action to remove all stored telemetry for your account.
  
  包含删除遥测操作以移除你账户的所有存储遥测。

Everyone else only sees aggregated install counters.

其他所有人只看到聚合安装计数器。

Deleting your account also deletes your telemetry data.

删除你的账户也会删除你的遥测数据。

## How to disable telemetry / 如何禁用遥测

Set the environment variable:

设置环境变量:

```bash
export CLAWHUB_DISABLE_TELEMETRY=1
```

With this set, the CLI will not send install telemetry.

设置后,CLI 不会发送安装遥测。

## 相关 / Related

- [CLI](/clawhub/cli) — CLI 命令参考
- [Auth](/clawhub/auth) — 登录和 token 管理
