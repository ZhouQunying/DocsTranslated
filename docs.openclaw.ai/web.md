# Web Interfaces

OpenClaw 的 web 层是一个轻量 browser interface (Vite + Lit),托管在与 WebSocket 相同的端口上。标准访问使用端口 18789 (HTTP,或 TLS 激活时 HTTPS)。可通过配置定义自定义前缀。Webhooks 和 Admin HTTP RPC 在同一 HTTP server 上暴露。

> **类比:单端口 SPA + WebSocket。** 类似 Next.js 的 API routes + pages 在同一端口: HTTP 请求返回静态 SPA assets,WebSocket 升级到同一端口处理实时通信。区别: Next.js 是 SSR,OpenClaw 是纯静态 SPA (Lit Web Components),所有状态在 browser 端。
>
> **架构要点:** Gateway 单端口 (18789) 同时提供 HTTP (静态 assets) 和 WebSocket;Control UI 是 Vite + Lit SPA,默认 `/` 可配 `gateway.controlUi.basePath`;Webhooks 在主 HTTP server 上启用;Admin HTTP RPC 用于特定 control-plane 操作 (POST 请求,需 plugin 激活);Tailscale Serve 推荐 (保持 loopback),Funnel 需密码认证;非 loopback 绑定强制 gateway auth;setup wizard 自动生成 shared-secret token;identity-based setups 依赖 request headers;public 部署需显式 origin 配置;TLS 激活时 helpers 自动切换到安全协议。

## Config

Interface 在 built assets 存在时自动激活。Config 允许 toggle 和设置 base path:

```json5
{
  gateway: {
    controlUi: { enabled: true, basePath: "/openclaw" }
  }
}
```

## Tailscale Access

### Integrated Serve (推荐)

保持 service 在 loopback,Tailscale 代理:

```json5
{
  gateway: {
    bind: "loopback",
    tailscale: { mode: "serve" }
  }
}
```

### Tailnet Bind + Token

直连 tailnet,shared-secret 认证:

```json5
{
  gateway: {
    bind: "tailnet",
    controlUi: { enabled: true },
    auth: { mode: "token", token: "your-token" }
  }
}
```

### Public Internet (Funnel)

Funnel 暴露,loopback 绑定 + 密码认证:

```json5
{
  gateway: {
    bind: "loopback",
    tailscale: { mode: "funnel" },
    auth: { mode: "password" }
  }
}
```

## Security Notes

- 认证强制 out-of-the-box
- 非 loopback 设置**需要** gateway auth
- Setup wizard 自动生成 shared-secret token
- Identity-based setups 依赖 request headers 用于 WebSocket 验证
- Public 部署需显式 origin 配置
- Tailscale Serve 在 `gateway.auth.allowTailscale: true` 时可通过 identity headers 满足认证
- Funnel mode 强制要求密码认证

## Building the UI

静态 assets 从 distribution 目录交付,可用指定 package manager script 编译:

```bash
pnpm ui:build
```
