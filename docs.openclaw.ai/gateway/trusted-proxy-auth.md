# Trusted Proxy Auth

**总结：** 安全敏感功能——把所有认证责任交给反向 proxy（identity-aware proxy），配置不当会暴露 Gateway。

> **类比：Cloudflare Access + OAuth2 Proxy + 信任内网 IP。** Cloudflare Access 在 edge 做身份验证，后端服务信任 Access 传来的 identity header 而不再自己认证。OpenClaw trusted proxy auth 类似——反向 proxy（Caddy/nginx/Traefik/Cloudflare Tunnel）做 auth + 传 identity header（如 `X-Forwarded-User`），Gateway 信任 proxy header 不再二次认证，但必须限制 proxy 来源 IP（`trustedProxies`）+ 防止绕过（direct access 必须阻止）。
>
> **架构要点：** When to use：identity-aware proxy（Cloudflare Access/Okta Access Gate/Pomerium）场景、WebSocket 1008 auth error 需 proxy 解决；When NOT to use：无 proper proxy auth、有 direct Gateway access 路径；How it works：proxy 验证身份 → 传 identity header → Gateway 从 header 提取 identity（不再自己认证）；Control UI pairing：WebSocket session scope + device identity 要求；Configuration：`gateway.auth.mode: "trusted-proxy"` + `trustedProxies` IP 列表 + `identityHeaders` header 名列表；TLS termination：proxy 端终结 HTTPS，HSTS 逐步 rollout（先短 max-age 观察，再延长）；Proxy setup examples：Caddy/nginx/Traefik/Cloudflare Tunnel 配置示例；Mixed token config：禁止同时用多种 auth mode（trusted-proxy + token 冲突）；operator scopes header：HTTP header 可限制 user 权限（`X-Operator-Scopes`）；Security checklist：部署前验证（proxy auth 开启、direct access 阻止、trustedProxies 正确、TLS 配置、HSTS rollout）；Security audit：自动审计工具检查 trusted proxy 配置；Troubleshooting：source/header/connection 常见错误；Migration from token auth：从旧 token auth 迁移步骤。
