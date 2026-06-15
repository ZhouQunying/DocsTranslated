# Troubleshooting / 故障排除

## `clawhub login` opens a browser but never completes / `clawhub login` 打开浏览器但从未完成

The CLI starts a short-lived local callback server during browser login.

CLI 在浏览器登录期间启动短暂存在的本地回调服务器。

- Make sure your browser can reach `http://127.0.0.1:<port>/callback`.
  
  确保你的浏览器可以访问 `http://127.0.0.1:<port>/callback`。

- Check local firewall, VPN, and proxy rules if the callback never arrives.
  
  如果回调从未到达,检查本地防火墙、VPN 和代理规则。

- In headless environments, create an API token in the ClawHub web UI and run:
  
  在无头环境中,在 ClawHub Web UI 中创建 API token 并运行:

```bash
clawhub login --token clh_...
```

## `whoami` or `publish` returns `Unauthorized` (401) / `whoami` 或 `publish` 返回 `Unauthorized`(401)

- Sign in again with `clawhub login`.
  
  使用 `clawhub login` 重新登录。

- If you use a custom config path, confirm `CLAWHUB_CONFIG_PATH` points at the file that contains your current token.
  
  如果使用自定义配置路径,确认 `CLAWHUB_CONFIG_PATH` 指向包含当前 token 的文件。

- If you use an API token, confirm it was not revoked in the web UI.
  
  如果使用 API token,确认它未在 Web UI 中被撤销。

## Search or install returns `Rate limit exceeded` (429) / 搜索或安装返回 `Rate limit exceeded`(429)

Read the retry information in the response:

读取响应中的重试信息:

- `Retry-After`: seconds to wait before retrying.
  
  重试前等待的秒数。

- `RateLimit-Remaining` and `RateLimit-Limit`: your current budget.
  
  你当前的预算。

- `RateLimit-Reset` or `X-RateLimit-Reset`: reset timing.
  
  重置时间。

If many users share one egress IP, anonymous IP limits can be hit even when each person only sends a few requests. Sign in where possible and retry after the reported delay.

如果许多用户共享一个出口 IP,即使每个人只发送几个请求也可能触发匿名 IP 限制。尽可能登录并在报告的延迟后重试。

## Search or install fails behind a proxy / 搜索或安装在代理后失败

The CLI respects standard proxy variables:

CLI 遵守标准代理变量:

```bash
export HTTPS_PROXY=http://proxy.example.com:3128
clawhub search "my query"
```

Supported names include `HTTPS_PROXY`, `HTTP_PROXY`, `https_proxy`, and `http_proxy`.

支持的名称包括 `HTTPS_PROXY`、`HTTP_PROXY`、`https_proxy`、`http_proxy`。

## A skill does not appear in search / 技能未出现在搜索中

- Check the exact slug or owner page if you know it.
  
  如果知道,检查确切的短名称或 owner 页面。

- Confirm the release is public and not held by scan or moderation.
  
  确认版本是公共的且未被扫描或审核保留。

- If you own the skill, sign in and inspect it:
  
  如果你持有该技能,登录并检查它:

```bash
clawhub inspect <skill-slug>
```

Owner-visible diagnostics may explain scan, upload-gate, or moderation state.

owner 可见的诊断可能解释扫描、上传门控或审核状态。

## Publish fails because required metadata is missing / 发布失败因为缺少必需元数据

For skills, check `SKILL.md` frontmatter. Required environment variables and tools should be declared so users and scanners can understand the package.

对于技能,检查 `SKILL.md` frontmatter。应声明必需的环境变量和工具,以便用户和扫描器理解包。

For plugins, check `package.json` compatibility metadata. Code-plugin publishes need OpenClaw compatibility fields such as `openclaw.compat.pluginApi` and `openclaw.build.openclawVersion`.

对于插件,检查 `package.json` 兼容性元数据。代码插件发布需要 OpenClaw 兼容性字段如 `openclaw.compat.pluginApi` 和 `openclaw.build.openclawVersion`。

Preview the publish payload first:

先预览发布有效载荷:

```bash
clawhub package publish <source> --family code-plugin --dry-run
```

## Publish fails with a GitHub owner or source error / 发布失败显示 GitHub owner 或源错误

ClawHub uses GitHub identity and source attribution to connect packages to their publishers.

ClawHub 使用 GitHub 身份和源归属将包连接到其发布者。

- Make sure you are signed in with the GitHub account that owns or can publish the package.
  
  确保你使用持有或可以发布该包的 GitHub 账户登录。

- Check that the source URL is public or accessible to ClawHub.
  
  检查源 URL 是公共的或对 ClawHub 可访问。

- For GitHub sources, use `owner/repo`, `owner/repo@ref`, or a full GitHub URL.
  
  对于 GitHub 源,使用 `owner/repo`、`owner/repo@ref` 或完整 GitHub URL。

## `sync` says no skills were found / `sync` 说未找到技能

`sync` looks for folders containing `SKILL.md` or `skill.md`.

`sync` 查找包含 `SKILL.md` 或 `skill.md` 的文件夹。

Point it at the roots you want to scan:

将其指向你想扫描的根目录:

```bash
clawhub sync --root /path/to/skills
```

Preview first if you are unsure what will publish:

如果不确定会发布什么,先预览:

```bash
clawhub sync --all --dry-run --no-input
```

## `update` refuses because of local changes / `update` 因本地更改而拒绝

The local files do not match any version ClawHub knows about. Choose one:

本地文件与 ClawHub 知道的任何版本都不匹配。选择一个:

- Keep local edits and skip the update.
  
  保留本地编辑并跳过更新。

- Overwrite with the published version:
  
  用已发布版本覆盖:

```bash
clawhub update <slug> --force
```

- Publish your edited copy as a new slug or fork.
  
  将编辑后的副本发布为新短名称或 fork。

## A plugin install fails in OpenClaw / 插件安装在 OpenClaw 中失败

- Use an explicit ClawHub source:
  
  使用显式 ClawHub 源:

```bash
openclaw plugins install clawhub:<package>
```

- Check the package detail page for scan status and compatibility metadata.
  
  检查包详情页的扫描状态和兼容性元数据。

- Confirm your OpenClaw version satisfies the package's advertised compatibility range.
  
  确认你的 OpenClaw 版本满足包宣传的兼容性范围。

- If the package is hidden, held, or blocked, it may not be installable until the owner resolves the issue.
  
  如果包被隐藏、保留或阻止,在 owner 解决问题前可能无法安装。

## Public API requests fail / 公共 API 请求失败

- Respect `429` retry headers and cache public list/search responses.
  
  遵守 `429` 重试头并缓存公共列表/搜索响应。

- Link users back to the canonical ClawHub listing.
  
  将用户链接回规范的 ClawHub 列表。

- Do not mirror hidden, private, held, or moderation-blocked content outside the public API surface.
  
  不要在公共 API 表面之外镜像隐藏、私有、保留或审核阻止的内容。

See [HTTP API](/clawhub/http-api) for endpoint details.

参见 [HTTP API](/clawhub/http-api) 了解端点详情。

## 相关 / Related

- [CLI](/clawhub/cli) — CLI 命令参考
- [Auth](/clawhub/auth) — 认证和 token 管理
- [HTTP API](/clawhub/http-api) — API 端点
