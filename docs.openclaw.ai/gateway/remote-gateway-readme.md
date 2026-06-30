# Remote Gateway Setup

## 架构精读

> 跳过不影响阅读翻译正文。

### 两种部署模式——为什么有 cloud 和 headless？

远程网关有两种部署模式：

- **Cloud 实例**：托管 VM（AWS EC2/DigitalOcean Droplet），完全控制，需要自己管理 TLS/防火墙
- **Headless 服务器**：Docker 容器或 systemd 服务，无 GUI，适合长期运行的自托管环境

这跟 K8s 的托管 vs 自建是一个思路——EKS/GKE 是托管（provider 管理基础设施），kubeadm 是自建（你管理一切）。选择取决于运维能力和控制需求。

### 网络暴露策略——为什么默认只绑定 loopback？

网关默认绑定 `127.0.0.1:18789`，只接受本地连接。远程访问需要显式配置：

1. **Tailscale Serve**：零配置内网穿透，最安全
2. **反向代理**（Caddy/nginx）：集中 TLS + 认证
3. **直接暴露**（不推荐）：绑定 `0.0.0.0`，需要自己处理安全

这跟 MongoDB 的默认绑定策略是一个思路——默认只监听 localhost，防止意外暴露到公网。远程访问需要显式配置网络层（Tailscale/反向代理），而非直接暴露端口。

### 凭证管理——为什么用 SecretRef 而非环境变量？

远程部署的凭证管理用 SecretRef（环境变量/文件/命令执行提供者），而非直接写环境变量：

```json5
{
  auth: {
    apiKey: { $ref: "env:ANTHROPIC_API_KEY" }
  }
}
```

这跟 Vault 的 secret reference 是一个思路——配置文件里存引用（`$ref`），实际值从外部源（环境变量/文件/命令执行）动态获取。好处是配置文件可以安全提交到 Git（不含明文密钥），凭证轮换不需要改配置文件。

### 进程守护——为什么推荐 systemd 而非 nohup？

远程部署推荐 systemd（Linux）或 launchd（macOS）做进程守护，而非 `nohup &`：

- **自动重启**：进程崩溃后自动拉起
- **日志管理**：journalctl 集中查看日志
- **启动顺序**：依赖网络就绪后再启动
- **优雅停止**：SIGTERM → 等待 → SIGKILL

这跟 Docker 的 restart 策略 是一个思路——`--restart=always` 比 `docker run -d` 更可靠。nohup 没有自动重启，进程挂了不会自动恢复。

---

This guide covers deploying OpenClaw gateway on a remote server (cloud VM or headless server). The default binding is `127.0.0.1:18789` (loopback only) — remote access requires explicit network configuration.

本指南覆盖在远程服务器（云 VM 或 headless 服务器）上部署 OpenClaw 网关。默认绑定 `127.0.0.1:18789`（仅 loopback）——远程访问需要显式网络配置。

Two deployment modes: cloud instance (full control, self-managed TLS/firewall) and headless server (Docker or systemd, no GUI, for long-running self-hosted environments). Network exposure options: Tailscale Serve (safest), reverse proxy (Caddy/nginx with centralized TLS), or direct binding (not recommended).

两种部署模式：云实例（完全控制，自管理 TLS/防火墙）和 headless 服务器（Docker 或 systemd，无 GUI，适合长期运行的自托管环境）。网络暴露选项：Tailscale Serve（最安全）、反向代理（Caddy/nginx 集中 TLS）、或直接绑定（不推荐）。

Credential management uses SecretRef (env/file/exec 提供者s) rather than plaintext in config — config files can be safely committed to Git. Process supervision uses systemd (Linux) or launchd (macOS) for auto-restart, log management, and graceful shutdown — not `nohup &`.

凭证管理用 SecretRef（环境变量/文件/命令执行提供者）而非配置文件中的明文——配置文件可以安全提交到 Git。进程守护用 systemd（Linux）或 launchd（macOS）实现自动重启、日志管理和优雅停止——不用 `nohup &`。
