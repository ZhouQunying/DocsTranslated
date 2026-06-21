# Dashboard

Gateway dashboard 是 browser-based Control UI,默认在 `/` 提供 (可经 `gateway.controlUi.basePath` 配置)。

> **类比:Router admin panel + CLI。** Router admin panel (如 192.168.1.1) 让你从浏览器配置 router,Wi-Fi、port forwarding、logs。Dashboard 类似: 浏览器配置 Gateway (auth、channels、sessions、exec approvals)。区别: Router admin panel 是静态 HTML forms,Dashboard 是动态 SPA (Lit),实时 WebSocket 更新。
>
> **架构要点:** 默认 `http://127.0.0.1:18789/` (TLS 时 `https://`);认证在 WebSocket handshake 强制: token/password/Tailscale identity/trusted-proxy;快速路径: `openclaw dashboard` 自动打开 + 复制链接 + 显示 SSH hint (如果 headless);token 存储在 sessionStorage (当前 tab session + 选定 gateway URL),不 persist 跨 reload;SecretRef-managed token 时 `openclaw dashboard` 打印/复制/打开非 tokenized URL (避免暴露 externally managed tokens);密码不 persist 跨 reload;identity-bearing modes (Tailscale Serve/trusted-proxy) 不需要 pasted shared secret;`unauthorized`/1008 时检查 gateway 可达性、token/password、token drift;UI language picker 在 **Overview → Gateway Access → Language**。

## Quick Open (Local Gateway)

```bash
http://127.0.0.1:18789/
```

TLS 激活时:
```bash
https://127.0.0.1:18789/
wss://127.0.0.1:18789  # WebSocket endpoint
```

## Fast Path (推荐)

- Onboarding 后,CLI 自动打开 dashboard 并打印 clean (非 tokenized) 链接
- 随时重新打开: `openclaw dashboard` (复制链接,可能打开 browser,headless 时显示 SSH hint)
- 如果 clipboard 和 browser 交付失败,`openclaw dashboard` 仍打印 clean URL 并指导使用 `OPENCLAW_GATEWAY_TOKEN` 或 `gateway.auth.token` 作为 URL fragment key `token`;token 值从不打印在 logs 中
- UI 提示 shared-secret auth 时,把配置的 token 或 password 粘贴到 Control UI settings

## Auth Basics (Local vs Remote)

- **Localhost**: 打开 `http://127.0.0.1:18789/`
- **Gateway TLS**: `gateway.tls.enabled: true` 时,dashboard/status 链接用 `https://`,Control UI WebSocket 用 `wss://`
- **Shared-secret token 来源**: `gateway.auth.token` (或 `OPENCLAW_GATEWAY_TOKEN`);`openclaw dashboard` 可经 URL fragment 一次性初始化
- **Identity-bearing modes**: Tailscale Serve (`gateway.auth.allowTailscale: true`) 或非 loopback identity-aware reverse proxy (`gateway.auth.mode: "trusted-proxy"`) 满足 Control UI/WebSocket auth,dashboard 不需要 pasted shared secret
- **非 localhost**: 使用 Tailscale Serve、non-loopback shared-secret bind、non-loopback identity-aware reverse proxy 或 SSH tunnel

## "Unauthorized" / 1008 处理

- 确保 gateway 可达:
  - 本地: `openclaw status`
  - 远程: SSH tunnel `ssh -N -L 18789:127.0.0.1:18789 user@host` 然后打开 `http://127.0.0.1:18789/`
- `AUTH_TOKEN_MISMATCH`: 客户端可用 cached device token 做一次 trusted retry;如果仍失败,手动 resolve token drift
- `AUTH_SCOPE_MISMATCH`: device token 被识别但不携带 dashboard 请求的作用域;重新 pair 或批准请求的作用域契约
- 从 gateway host 检索或提供 shared secret:
  - Token: `openclaw config get gateway.auth.token`
  - Password: resolve 配置的 `gateway.auth.password` 或 `OPENCLAW_GATEWAY_PASSWORD`
  - SecretRef-managed token: resolve 外部 secret provider 或在此 shell 导出 `OPENCLAW_GATEWAY_TOKEN`,然后重新运行 `openclaw dashboard`
  - 无 shared secret: `openclaw doctor --generate-gateway-token`
- Dashboard settings 中,把 token 或 password 粘贴到 auth field,然后连接
