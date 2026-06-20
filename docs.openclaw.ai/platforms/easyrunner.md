# EasyRunner

## 架构精读

> 跳过不影响阅读翻译正文。

### Podman + Caddy——容器化 Gateway 的标准配方

EasyRunner 用 Podman 跑 OpenClaw 容器，Caddy 做反向代理和 TLS 终结。这跟 Cloud Foundry 的 Gorouter + Diego 是一个思路——容器运行时负责进程管理，反向代理负责路由和 TLS。

Podman 的选择很有意思——它跟 Docker 兼容但不需要 daemon，rootless 运行更安全。对 EasyRunner 这种多租户平台来说，rootless Podman 比 Docker 更适合——一个用户的容器出问题不会影响其他用户。

### Caddy Labels——声明式路由

Compose 文件里用 labels 声明路由规则：
```yaml
labels:
  caddy: openclaw.example.com
  caddy.reverse_proxy: "{{upstreams 1455}}"
```

这跟 Kubernetes Ingress annotations 是一个思路。Ingress annotations 声明路由规则，Ingress controller 读取并配置反向代理。EasyRunner 的 Caddy 也是这样：读 container labels，自动生成 Caddyfile，配置反向代理。

声明式的好处是**配置即代码**——路由规则跟 container 定义在一起，版本控制、code review、回滚都跟代码一样。不是手动编辑 Caddyfile，而是 container 起来时自动配置。

### Trusted Proxy 设置——不要把 auth 关了

文档强调：**不要禁用 auth checks**，而是配置 trusted proxy settings。这是很多部署犯的错——反向代理终结 TLS 后，Gateway 看到的源 IP 是 proxy IP，不是客户端 IP。简单粗暴的解决方案是关掉 IP 检查，但这会失去所有源 IP 相关的安全控制。

正确做法是配置 trusted proxy——告诉 Gateway "来自这个 IP 的请求是 proxy 转发的，读 X-Forwarded-For 头获取真实客户端 IP"。这跟 AWS ALB 的 trusted proxy 设置是一个思路。ALB 终结 TLS 后，后端实例需要配置信任 ALB 的 IP 段，才能正确解析 X-Forwarded-For。

### 持久化卷——config 和 workspace 分离

EasyRunner 用两个持久化卷：
- `openclaw-config`：`/home/node/.openclaw`，Gateway 配置和状态
- `openclaw-workspace`：`/workspace`，agent 的项目数据

这跟 Kubernetes PV 的分离策略是一个思路。Kubernetes 把 etcd 数据、应用数据、日志分别用不同 PV，备份策略不同（etcd 必须备份，日志可以丢弃）。OpenClaw 也是这样：config 必须备份（丢了要重新配置），workspace 按需备份（agent 的项目数据可能重要也可能不重要）。
