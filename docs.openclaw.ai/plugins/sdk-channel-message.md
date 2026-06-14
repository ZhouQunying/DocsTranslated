# Channel Message API

此页面已移至 [Channel outbound API](/plugins/sdk-channel-outbound)。

`openclaw/plugin-sdk/channel-message` 和 `openclaw/plugin-sdk/channel-message-runtime` 保持为旧插件的已弃用兼容子路径。新 channel 插件应使用 `openclaw/plugin-sdk/channel-outbound` 做消息生命周期、回执、持久发送和实时预览辅助。已弃用子路径是共享 channel 消息核心和聚焦 inbound/outbound SDK 表面的薄别名；不要在那里添加新辅助。

移除计划：在外部插件迁移窗口期间保持这些别名，然后在调用者迁移到 `channel-outbound` 后的下一次大版本 SDK 清理中移除。
