# Debugging

## 架构精读

> 跳过不影响阅读翻译正文。

### 调试命令——为什么用 `/debug` 而非改配置？

`/debug` 命令在内存中临时修改配置，无需重启网关：

- **即时生效**：修改立即应用，无需等待重启
- **会话隔离**：仅影响当前会话，不影响其他用户
- **快速迭代**：改配置 → 重启 → 测试的循环缩短为"改 → 测试"

这跟 Chrome DevTools 的实时编辑是一个思路——在浏览器中修改 CSS/JS，立即看到效果，无需刷新页面。`/debug` 适合"试错式调试"，配置文件适合"永久设置"。

### 追踪与性能分析——为什么需要多层可见性？

文档提供多层调试工具：

1. **`/trace`**：会话级调试日志（插件诊断）
2. **生命周期追踪环境变量**：慢插件阶段分解
3. **启动基准测试**：命令启动时间分析
4. **CPU 性能分析变量**：热点函数定位
5. **原始流日志**：模型输出未过滤视图（检测推理泄露）

这跟 APM（应用性能管理）是一个思路——链路追踪（Trace）→ 指标（Metrics）→ 日志（Logs），三层可见性覆盖不同调试场景。多层工具让"快速定位"和"深度分析"都成为可能。

### 开发配置——为什么需要隔离环境？

开发配置（development configuration）将应用数据分离到临时目录，生成基础工作空间，支持安全实验。

这跟 Docker 的 `--rm` 是一个思路——容器退出后自动删除（不留痕迹），适合"一次性实验"。开发配置让"试错"无副作用，避免污染生产数据。

---

Developer debugging tools: `/debug` command modifies config in memory (no restart), `/trace` reveals session-level debug lines, lifecycle trace env var breaks down slow plugin phases, startup benchmarks analyze command latency, CPU profiling variables locate hotspots, raw stream logging inspects unfiltered model output. Development profile isolates app data in temp folder for safe experimentation. VS Code integration requires source maps for TypeScript debugging.

开发者调试工具：`/debug` 命令在内存中修改配置（无需重启），`/trace` 显示会话级调试日志。生命周期追踪环境变量分解慢插件阶段，启动基准测试分析命令延迟。CPU 性能分析变量定位热点，原始流日志检查未过滤模型输出。开发配置将应用数据隔离到临时目录，支持安全实验。VS Code 集成需要源映射（source maps）支持 TypeScript 调试。
