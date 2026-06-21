# Multiple Gateways

**总结：** 通常单实例足够（同时管理多 agent + 多 channel），但需要强隔离或应急 bot 时需部署独立实例（独立 config + 独立 port）。

> **类比：K8s 多 cluster + Nginx 多 instance。** 生产环境多 K8s cluster 隔离（dev/staging/prod 或 per-tenant），多 Nginx instance 隔离流量（public CDN vs internal proxy）。OpenClaw multi-gateway 类似——每个实例独立 profile（config dir/data dir/port）、独立 auth credential、独立 channel token，rescue bot 用独立实例做应急备份，隔离 checklist 确保环境变量/端口/socket 不冲突。
>
> **架构要点：** Best recommended setup：emergency fallback 最佳配置（独立 profile + 独立 channel token + 间隔端口避免重叠）；Rescue-Bot Quickstart：CLI 命令部署独立应急实例（`--profile rescue` + 独立 socket）；Why this works：架构隔离保证备份系统始终可用（独立 directory/project/auth credential）；`--profile rescue onboard` 效果：设置文件/操作记录/supervised daemon 进入隔离目录；General multi-gateway setup：扩展到多 tenant/channel/admin task 的多长期运行实例；Isolation checklist：必须隔离的环境变量和配置参数（防 write conflict + port overlap）；Port mapping：secondary port（web UI/canvas serve）从 primary port 自动派生；Browser/CDP notes：禁止跨部署复制 Chrome DevTools Protocol 配置（需独立 management address + 远端 endpoint）；Manual env example：显式定义唯一环境变量（设置文件路径 + 状态目录）启动独立进程；Quick checks：诊断命令（系统健康/daemon 状态/连通性测试告警）。
