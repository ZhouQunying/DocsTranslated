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

### 持久化卷——身份和产物分离

EasyRunner 用两个持久化卷：
- `openclaw-config`：`/home/node/.openclaw`，Gateway 的配置、凭证、状态
- `openclaw-workspace`：`/workspace`，agent 的项目数据

这两个卷的核心区别是**丢失后的恢复成本**。Config 丢了，Gateway 的身份、凭证、设置全没了，等于一个全新的 Gateway 要重新配置。Workspace 丢了，只是 agent 的工作产物没了，Gateway 本身还在。

这跟数据库的元数据和数据分离是一个思路。PostgreSQL 的 system catalog（`pg_catalog`）记录 schema 定义，用户表记录业务数据。Catalog 丢了，数据库不知道自己有什么表、什么索引，数据还在但没法访问。OpenClaw 的 config 就是它的 catalog——丢了它不知道自己是谁、连哪些 provider、信任哪些 node。

备份策略因此不同：config 必须高频备份（每次配置变更都该备份），workspace 按需备份。这跟 Terraform 的 state 文件是一个思路。Terraform 的 `.tfstate` 记录基础设施状态，丢了要重新 import 所有资源。Terraform 代码可以从 Git 恢复，但 state 丢了就是真丢了。OpenClaw 的 config 也是这样——代码（workspace）可以重建，身份（config）丢了就要重新配置。
