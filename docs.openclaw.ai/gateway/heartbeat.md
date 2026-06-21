# Heartbeat

**总结：** 在主 session 中执行周期性 agent turn——AI 主动巡检并报告重要事项，不骚扰用户。

> **类比：CronJob + Prometheus Alertmanager + 值班巡检。** CronJob 按时间表触发任务，Alertmanager 按规则静默/聚合/发送告警，值班巡检定期检查系统状态只在异常时通知。OpenClaw heartbeat 类似——按 interval 触发 agent turn（默认 15 分钟），agent 按 prompt 巡检后台职责（HEARTBEAT.md checklist），idle 时返回 success token 静默，有事时输出 alert text 通知用户，支持 per-agent/per-channel 配置、active hours 限制、cost 控制（隔离 session + 轻量模型）。
>
> **架构要点：** Quick start：设 interval、创建 HEARTBEAT.md checklist、路由消息到 channel；Defaults：interval 15 分钟、默认 prompt 文本、timeout、active hours 限制；Heartbeat prompt：引导 AI 巡检后台职责 + casual check-in；Response contract：idle 返回 `HEARTBEAT_OK` success token，有事返回 alert text；Config：JSON5 配置（interval/prompt/model/delivery target/active hours），scope 层级（global → per-agent → per-channel）；Per-agent heartbeat：仅对 `agents.list` 中特定 agent 启用；Active hours：限制每日执行时间窗口；24/7 setup：持续执行 + 避免配置错误；Multi-account：路由到同 channel 不同 account；Field notes：interval/model/delivery target 等属性定义；Delivery behavior：session routing/visibility/scheduled run 对 session lifecycle 影响；Visibility controls：channel-level toggle（success ack/alert/status indicator 显示控制）；HEARTBEAT.md：workspace markdown checklist，支持 interval-based task block；Manual wake：CLI 命令手动触发（`openclaw heartbeat wake`）；Reasoning delivery：可选输出 AI 内部思考过程；Cost awareness：隔离 session + 轻量模型减少 token 消耗；Context overflow：heartbeat model 与主 model 切换时 context limit 问题。
