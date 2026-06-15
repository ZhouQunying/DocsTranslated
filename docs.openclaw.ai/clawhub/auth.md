# Auth / 认证

ClawHub uses GitHub for web sign-in. The CLI uses ClawHub API tokens created through that signed-in account.

ClawHub 使用 GitHub 进行 Web 登录。CLI 使用通过该已登录账户创建的 ClawHub API token。

## Web sign-in / Web 登录

Use GitHub to sign in at [clawhub.ai](https://clawhub.ai).

使用 GitHub 在 [clawhub.ai](https://clawhub.ai) 登录。

Deleted, banned, or disabled accounts cannot complete normal ClawHub sign-in. If sign-in returns you to a logged-out state, your account may not be in good standing. If your account was banned or disabled, use the [ClawHub appeal form](https://clawhub.ai/appeal) if you believe this is a mistake.

已删除、被禁止或禁用的账户无法完成正常的 ClawHub 登录。如果登录将你返回到未登录状态,你的账户可能状态不佳。如果你的账户被禁止或禁用,如果你认为这是错误,请使用 [ClawHub 申诉表单](https://clawhub.ai/appeal)。

## CLI login / CLI 登录

The default CLI login flow opens your browser:

默认 CLI 登录流程打开你的浏览器:

```bash
clawhub login
clawhub whoami
```

What happens:

发生什么:

1. The CLI starts a temporary callback server on `127.0.0.1`.
   
   CLI 在 `127.0.0.1` 上启动临时回调服务器。

2. Your browser opens the ClawHub sign-in page.
   
   你的浏览器打开 ClawHub 登录页面。

3. After GitHub sign-in, ClawHub creates an API token.
   
   GitHub 登录后,ClawHub 创建 API token。

4. The browser redirects back to the local callback.
   
   浏览器重定向回本地回调。

5. The CLI stores the token in your ClawHub config file.
   
   CLI 将 token 存储在你的 ClawHub 配置文件中。

If your browser cannot reach the local callback because of firewall, VPN, or proxy rules, use the headless token flow.

如果你的浏览器因防火墙、VPN 或代理规则无法到达本地回调,使用无头 token 流程。

## Headless login / 无头登录

Create a token in the ClawHub web UI, then pass it to the CLI:

在 ClawHub Web UI 中创建 token,然后传递给 CLI:

```bash
clawhub login --token clh_...
```

Use this flow for servers, CI jobs, or terminal-only environments.

对服务器、CI 作业或纯终端环境使用此流程。

For remote shells where you can open a browser elsewhere, run:

对于可以在其他地方打开浏览器的远程 shell,运行:

```bash
clawhub login --device
```

The CLI prints a one-time code and waits while you authorize it at `https://clawhub.ai/cli/device`.

CLI 打印一次性代码并等待你在 `https://clawhub.ai/cli/device` 授权它。

## Token storage / Token 存储

Default config paths:

默认配置路径:

- macOS: `~/Library/Application Support/clawhub/config.json`
- Linux/XDG: `$XDG_CONFIG_HOME/clawhub/config.json` or `~/.config/clawhub/config.json`
- Windows: `%APPDATA%\clawhub\config.json`

Override the path with:

覆盖路径:

```bash
export CLAWHUB_CONFIG_PATH=/path/to/config.json
```

Print the stored token for CI setup with:

打印存储的 token 用于 CI 设置:

```bash
clawhub token
```

## Revocation / 撤销

You can revoke API tokens in the ClawHub web UI.

你可以在 ClawHub Web UI 中撤销 API token。

Revoked, invalid, or missing tokens return `401 Unauthorized`. Sign in again with `clawhub login` or provide a fresh token with `clawhub login --token`.

已撤销、无效或缺失的 token 返回 `401 Unauthorized`。使用 `clawhub login` 重新登录或使用 `clawhub login --token` 提供新 token。

Deleted, banned, or disabled accounts cannot continue using existing API tokens. If your account was banned or disabled, use the [ClawHub appeal form](https://clawhub.ai/appeal) if you believe this is a mistake.

已删除、被禁止或禁用的账户无法继续使用现有 API token。如果你的账户被禁止或禁用,如果你认为这是错误,请使用 [ClawHub 申诉表单](https://clawhub.ai/appeal)。

## 相关 / Related

- [CLI](/clawhub/cli) — CLI 命令参考
- [Publishing](/clawhub/publishing) — 发布流程
- [HTTP API](/clawhub/http-api) — API 端点和认证
