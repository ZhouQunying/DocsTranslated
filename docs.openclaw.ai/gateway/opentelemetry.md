# OpenTelemetry export

## 架构精读

> 跳过不影响阅读翻译正文。

### OTLP/HTTP (protobuf)

**问题**: 自定义格式需要用户写解析器,不兼容现有可观测性平台?

**方案**: 用 **OTLP/HTTP (protobuf)** 标准协议:
- **OTLP**: OpenTelemetry 标准协议,传输 traces、metrics、logs
- **HTTP**: 基于 HTTP,兼容性好
- **protobuf**: 二进制格式,比 JSON 紧凑、快

**洞察**: 行业标准,几乎所有可观测性平台都支持 (Jaeger、Prometheus、ELK)。

**权衡**:
- ✓ 兼容: 直接导入现有平台,不需要适配
- ✓ 标准: 不需要写解析器

**模式**: JDBC——数据库访问标准协议,所有数据库都实现。

### Plugin 模式

**问题**: 不是所有用户都需要 OpenTelemetry 导出?

**方案**: 做成 **plugin**,不是核心功能:
```bash
openclaw plugins install diagnostics-otel
openclaw plugins enable diagnostics-otel
```

**洞察**: 按需安装,不需要的用户不安装 (不占资源、不增加复杂度)。

**权衡**:
- ✓ 灵活: 按需安装
- ✓ 轻量: 不需要时不占资源

**模式**: Kubernetes CSI——存储插件接口,按需安装。

### Logs 可以写成 stdout JSONL

**问题**: 容器化环境 (Docker、Kubernetes) 标准做法是应用把日志写到 stdout?

**方案**: 支持 **stdout JSONL** (标准输出的 JSON Lines 格式)。

**洞察**: 容器运行时直接收集 stdout 日志,不需要额外组件。

**权衡**:
- ✓ 容器化友好: 符合 12-factor app 日志原则
- ✓ 简单: 不需要额外 collector

**模式**: 12-factor app 日志原则——日志写到 stdout,不写文件。

### Model usage 和 message flow

**问题**: 问题可能出在任何一环 (LLM 调用、消息路由、工具调用)?

**方案**: 细粒度追踪:
- **Model usage**: provider、model、token 消耗、延迟、错误率
- **Message flow**: channel 来源、agent 路由、工具调用、响应 channel

**洞察**: 定位"问题出在哪一步",不是"Gateway 有问题"这种模糊信息。

**权衡**:
- ✓ 详细: 追踪所有环节
- ✓ 诊断: 快速定位问题

### Session liveness telemetry

**问题**: 需要知道 session 活跃度 (容量规划、异常检测、成本分析)?

**方案**: 导出 **session liveness** (会话活跃度):
- 每个 session 的最后活动时间
- 每个 session 的消息数量
- 每个 session 的 token 消耗

**洞察**: 容量规划、异常检测、成本分析。

**权衡**:
- ✓ 监控: 知道 session 活跃状态
- ✓ 分析: 可以分析使用模式

**模式**: Google Analytics session tracking——追踪页面浏览、停留时间、跳出率。
