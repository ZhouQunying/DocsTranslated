# `openclaw gateway`

## 架构精读

> 跳过不影响阅读翻译正文。

### 前台 vs 后台——为什么提供两种启动方式？

`openclaw gateway` 支持两种启动方式：

- **前台启动**（默认）：进程在终端运行，Ctrl+C 停止
- **后台启动**（`--daemon`）：进程在后台运行，用 `openclaw daemon` 管理

这跟 Redis 的启动方式是一个思路——`redis-server` 前台运行（调试），`redis-server --daemonize yes` 后台运行（生产）。前台模式方便调试（直接看日志），后台模式适合长期运行。

### 配置覆盖——为什么支持命令行覆盖？

`--config` 和 `--port` 等标志覆盖配置文件中的值：

```
openclaw gateway --port 18790 --config /path/to/config.json5
```

这跟 Docker 的 `-e` 环境变量覆盖是一个思路——临时覆盖配置（如测试不同端口），不需要修改配置文件。适合"一次性测试"场景。

---

Two startup modes: foreground (default, Ctrl+C to stop) and background (`--daemon`, managed via `openclaw daemon`). Supports CLI overrides (`--port`, `--config`) for temporary config changes without editing the config file.

两种启动方式：前台（默认，Ctrl+C 停止）和后台（`--daemon`，通过 `openclaw daemon` 管理）。支持命令行覆盖（`--port`、`--config`）临时修改配置，不需要编辑配置文件。
