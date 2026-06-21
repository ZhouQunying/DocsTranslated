# Multiple Gateways

## 架构精读

> 跳过不影响阅读翻译正文。

### Profile namespace 隔离——为什么每个实例需要独立 profile？

多实例部署的核心是 profile 隔离。每个 gateway 实例具备独立的：

- config dir（配置文件目录）
- data dir（数据目录）
- port（监听端口）
- 认证凭证（认证凭证）
- channel token（频道令牌）

这跟 K8s 多 cluster 隔离是一个思路——每个 cluster 有自己的 API endpoint、etcd 存储、RBAC 策略。`--profile` 参数是 namespace 边界，隔离每个实例的全部配置空间。

### 应急 bot 独立实例——为什么应急系统不能共享资源？

主 gateway 挂掉时，备份系统必须完全独立才能正常工作。如果共享配置目录或认证凭证，主实例的故障可能级联到备份实例。

Rescue bot 用 `--profile rescue` 部署独立实例：

- 独立的配置文件和操作记录
- 独立的 supervised daemon 进程
- 独立的 socket 和端口

这跟 AWS 多 region failover 是一个思路——backup region 必须完全独立，主 region 的故障不会影响 backup region。

关键设计是**故障隔离**。rescue 实例运行在隔离目录中，即使主实例崩溃，备份系统不受影响。

### 端口派生规则——为什么辅助端口自动计算？

辅助端口（web UI、canvas serve）从主端口自动派生，避免手动计算端口冲突。

比如主端口 18789 → canvas 端口 18790。多实例并行时需要间隔端口：实例 A 用 18789/18790，实例 B 用 19789/19790。

这跟 Prometheus 的端口约定是一个思路——Prometheus 默认 9090，Grafana 默认 3000，Alertmanager 默认 9093。约定俗成的端口偏移避免多服务端口冲突。

### Isolation checklist——哪些配置必须隔离？

多实例部署的隔离清单：

| 配置项 | 隔离原因 |
|--------|----------|
| 环境变量 | 防止写冲突 |
| 配置文件路径 | 防止覆盖其他实例的配置 |
| 状态目录 | 防止 session/auth 数据冲突 |
| 端口 | 防止端口重叠 |
| Socket | 防止 Unix socket 冲突 |

这跟 Docker 的 volume 隔离是一个思路——每个容器挂载独立的 volume，防止多个容器写同一个目录导致数据损坏。

### Browser CDP 隔离——为什么禁止跨实例复制？

每个实例需要独立的 Chrome DevTools Protocol 配置：

- 独立的 DevTools management address
- 独立的 remote endpoint

跨部署复制 CDP 配置会导致浏览器 session 冲突——两个 gateway 实例争夺同一个浏览器进程的控制权。

这跟 Chrome profile 隔离是一个思路——每个 Chrome profile 有独立的 DevTools 端口，多个 profile 不能共享同一个 debugging port。

### 手动环境变量启动——为什么需要显式定义？

手动启动多实例时，显式定义唯一的环境变量（配置文件路径 + 状态目录），确保每个进程使用独立的配置空间。

这跟 Redis 多实例是一个思路——每个 Redis 实例用不同的配置文件（`redis-6379.conf`、`redis-6380.conf`）指定独立的端口和数据目录。

---

A single instance is usually sufficient, managing multiple agents and channels simultaneously. Deploy independent instances (with separate config, data directory, and port) only when strong isolation or an emergency rescue bot is needed.

通常单实例足够，可同时管理多 agent 和多 channel。需要强隔离或应急 bot 时，部署独立实例（独立 config、独立数据目录、独立 port）。

Rescue bot uses `--profile rescue` to deploy an independent emergency instance with its own config files, operation records, and supervised daemon running in isolated directories.

Rescue bot 用 `--profile rescue` 部署独立应急实例——独立的配置文件、操作记录、supervised daemon 运行在隔离目录中。

General multi-gateway setup extends to multiple tenants, channels, or admin tasks, each requiring its own profile, port, and credentials. The isolation checklist ensures unique environment variables, config paths, state directories, ports, and sockets per instance to prevent write conflicts and port overlaps.

通用多 gateway 部署扩展到多 tenant、多 channel 或多管理任务，每个实例需要独立的 profile、port 和 credential。隔离清单确保每个实例使用唯一的环境变量、配置路径、状态目录、端口和 socket，防止 write conflict 和 port overlap。

Secondary ports (web UI, canvas serve) are auto-derived from the primary port. When running multiple instances in parallel, assign port offsets to avoid conflicts.

secondary port（web UI、canvas serve）从 primary port 自动派生。多实例并行时需分配端口偏移量，避免冲突。

Browser automation (CDP) configurations must never be copied across deployments — each instance needs its own DevTools management address and remote endpoint. Manual environment startup requires explicitly defining unique environment variables (config file path and state directory) for each process.

浏览器自动化（CDP）配置禁止跨部署复制——每个实例需要独立的 DevTools management address 和 remote endpoint。手动环境变量启动需显式定义唯一的环境变量（配置文件路径 + 状态目录）来启动每个进程。

After deployment, run diagnostic commands to verify system health, daemon status, and connectivity — catching configuration isolation issues early.

部署后运行诊断命令（系统健康、daemon 状态、连通性测试），及时发现配置隔离问题。
