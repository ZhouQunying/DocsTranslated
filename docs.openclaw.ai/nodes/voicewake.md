# Voice Wake

Gateway 集中管理唤醒词（activation phrases），所有设备共享同一集合——单个设备不能有独立的唤醒词。修改通过任意接口保存后分发到所有已连接设备。Apple 设备因独立权限要求保持自己的"Voice Wake 启用/禁用"开关。Android 目前不支持，依赖手动麦克风激活。

> **类比：Siri "Hey Siri" + 集中配置管理。** 类似 Siri 的"嘿 Siri"唤醒词，但 OpenClaw 由 Gateway 集中管理而非设备本地。类似 etcd 配置分发——Gateway 存储配置，设备订阅变更事件同步。
>
> **架构要点：** 存储在 `~/.openclaw/settings/voicewake.json`（`{ triggers: [...], updatedAtMs }`）；RPC：`voicewake.get`/`voicewake.set`（字符串数组）、`voicewake.routing.get`/`voicewake.routing.set`（路由配置，target 可选 `current`/`agentId`/`sessionKey`）；事件广播：`voicewake.changed`、`voicewake.routing.changed` 到所有 WebSocket 连接和已连接节点；系统自动清理空白和空格，空输入恢复默认；长度和数量有安全限制。
