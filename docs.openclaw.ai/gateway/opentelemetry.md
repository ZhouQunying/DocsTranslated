# OpenTelemetry export

## 架构精读

> 跳过不影响阅读翻译正文。

### OTLP/HTTP (protobuf)——标准化的可观测性协议

OpenClaw 通过官方 `diagnostics-otel` plugin 导出诊断数据,使用 **OTLP/HTTP (protobuf)** 协议:

- **OTLP**(OpenTelemetry Protocol): OpenTelemetry 的标准协议,用于传输 traces、metrics、logs
- **HTTP**: 基于 HTTP 传输,兼容性好(能穿透防火墙)
- **protobuf**(Protocol Buffers): 二进制序列化格式,比 JSON 更紧凑、更快

**为什么用 OTLP 而不是自定义格式?** 因为 OTLP 是行业标准,几乎所有可观测性平台都支持:
- Jaeger、Zipkin(traces)
- Prometheus、Grafana(metrics)
- ELK、Loki(logs)

如果 OpenClaw 用自定义格式,用户需要写专门的解析器。用 OTLP,用户直接把 OpenClaw 的数据导入现有的可观测性平台,不需要额外适配。

**这跟 JDBC 是一个思路**——JDBC 是数据库访问的标准协议,所有数据库都实现 JDBC 接口,应用用统一的 API 访问。OpenClaw 的 OTLP 也是同样: 标准化的可观测性数据导出,兼容所有支持 OTLP 的平台。

### Plugin 模式——可选的导出功能

OpenTelemetry 导出是**plugin**,不是核心功能:

```bash
openclaw plugins install diagnostics-otel
openclaw plugins enable diagnostics-otel
```

**为什么做成 plugin?** 因为不是所有用户都需要 OpenTelemetry 导出:
- 本地开发: 不需要,看终端日志就够
- 小规模部署: 不需要,直接看文件日志
- 大规模生产: 需要,导入到 Jaeger/Prometheus/Grafana

做成 plugin,不需要的用户不安装(不占资源、不增加复杂度),需要的用户安装。

**这跟 Kubernetes 的 CSI 是一个思路**——CSI(Container Storage Interface)是存储插件接口,不是所有集群都需要所有存储后端,按需安装。OpenClaw 的 diagnostics-otel 也是同样: 按需安装的 plugin。

### Logs 可以写成 stdout JSONL——容器化友好

除了 OTLP 导出,logs 也可以写成 **stdout JSONL**(标准输出的 JSON Lines 格式):

**为什么支持 stdout JSONL?** 因为容器化环境(Docker、Kubernetes)的标准做法是:
- 应用把日志写到 stdout(不是文件)
- 容器运行时收集 stdout 日志
- 日志收集器(Fluentd、Filebeat)从容器运行时读取日志

如果 OpenClaw 只支持 OTLP 导出,容器化环境需要额外的 OTLP collector。支持 stdout JSONL,容器运行时直接收集,不需要额外组件。

**这跟 12-factor app 的日志原则**是一个思路——12-factor app 把日志写到 stdout,不写文件,让运行环境处理日志收集。OpenClaw 的 stdout JSONL 也是同样: 符合容器化的最佳实践。

### Model usage 和 message flow——细粒度的追踪

OpenTelemetry 导出包括细粒度的追踪:

**Model usage**(模型使用):
- 每次 LLM 调用的 provider、model、token 消耗
- 每次调用的延迟和错误率

**Message flow**(消息流):
- 用户消息从哪个 channel 进来
- 消息路由到哪个 agent
- Agent 调用了哪些工具
- 响应发送到哪个 channel

**为什么需要细粒度追踪?** 因为问题可能出在任何一环:
- LLM 调用慢 → 需要知道是哪个 provider、哪个 model
- 消息丢失 → 需要知道消息在哪个环节丢了
- 工具调用失败 → 需要知道调用了什么工具、传了什么参数

细粒度追踪让用户能定位"问题出在哪一步",不是"Gateway 有问题"这种模糊信息。

### Session liveness telemetry——会话活跃度监控

OpenTelemetry 还导出 **session liveness**(会话活跃度)数据:
- 每个 session 的最后活动时间
- 每个 session 的消息数量
- 每个 session 的 token 消耗

**为什么需要 session liveness?** 因为:
- **容量规划**: 知道有多少活跃 session,需要多少资源
- **异常检测**: 如果某个 session 突然不活跃了,可能有问题
- **成本分析**: 知道哪个 session 消耗最多 token,优化使用

**这跟 Google Analytics 的 session tracking 是一个思路**——GA 追踪每个 session 的页面浏览、停留时间、跳出率。OpenClaw 的 session liveness 也是同样: 追踪每个 session 的活跃度。
