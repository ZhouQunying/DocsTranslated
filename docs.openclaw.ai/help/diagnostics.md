# Diagnostics flags

## 架构精读

> 跳过不影响阅读翻译正文。

### 诊断标志——为什么需要"针对性调试"？

诊断标志（Diagnostics flags）让你启用针对性调试日志，无需全局开启详细日志。

- **按需启用**：大小写不敏感的文本字符串，支持通配符模式
- **配置方式**：JSON 配置数组或环境变量
- **进程级禁用**：环境变量设为 0 时，抑制该次执行的所有活跃标志

这跟日志级别（DEBUG/INFO/WARN/ERROR）是一个思路——但更细粒度。日志级别是"全局开关"，诊断标志是"子系统开关"。针对性调试让"只开启关心的子系统的调试日志"成为可能，避免"全局详细日志"导致的信息过载。

### 性能分析——为什么需要专用选项？

专用性能分析器选项激活不同组件的计时跨度（如回复分发、Codex）。专用时间线选项将结构化运行时事件写入 JSONL 文件，供外部质量保证工具使用。

- **默认输出**：JSONL 记录写入每日临时文件
- **解析方式**：标准命令行过滤工具或原生日志追踪工具
- **注意事项**：全局日志阈值设为警告以上可能抑制这些针对性调试记录

这跟 APM（应用性能管理）的"链路追踪"是一个思路——每个请求记录"经过哪些服务、每段耗时多少"，可视化后一眼看出瓶颈。专用性能分析让"性能问题定位"从"猜测"变为"数据驱动"。

---

Diagnostics flags: targeted debug logs without global verbose logging. Opt-in, case-insensitive text strings with wildcard patterns, defined in JSON config array or environment variable. Setting env var to 0 acts as process-level disable override suppressing all active flags. Performance debugging: specialized profiler options activate timing spans for distinct components (reply dispatch, Codex), dedicated timeline option writes structured runtime events to JSONL file for external QA harnesses. Default output: JSONL records to daily temp file, parseable with standard CLI filtering tools or native log-following utility. Note: setting global logging threshold above warnings may suppress targeted debug records.

诊断标志：针对性调试日志，无需全局详细日志。按需启用、大小写不敏感的文本字符串，支持通配符模式，在 JSON 配置数组或环境变量中定义。环境变量设为 0 时作为进程级禁用覆盖，抑制所有活跃标志。性能调试：专用性能分析器选项激活不同组件的计时跨度（回复分发、Codex）。专用时间线选项将结构化运行时事件写入 JSONL 文件，供外部质量保证工具使用。

默认输出：JSONL 记录写入每日临时文件，可用标准命令行过滤工具或原生日志追踪工具解析。注意：全局日志阈值设为警告以上可能抑制针对性调试记录。

架构精读：诊断标志比日志级别更细粒度，是"子系统开关"而非"全局开关"。专用性能分析让"性能问题定位"从"猜测"变为"数据驱动"。
