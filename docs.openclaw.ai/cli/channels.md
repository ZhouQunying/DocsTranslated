# `openclaw channels`

## 架构精读

> 跳过不影响阅读翻译正文。

### 通道管理——为什么需要专门的命令？

`openclaw channels` 管理聊天通道账户和运行时状态：

- **`channels list`**：列出已配置账户（状态标签）
- **`channels status`**：实时探测传输层状态
- **`channels add`**：交互式向导添加新通道
- **`channels remove`**：删除账户（先停止监听器再修改配置）

这跟 `kubectl get services` / `kubectl describe service` 是一个思路——资源列表 + 详情 + 生命周期管理。

### 能力探测——为什么需要按 provider 差异化？

`channels capabilities` 探测每个通道的 provider 特定能力：

- WhatsApp：意图、范围、静态功能支持
- Telegram：权限、令牌角色
- Discord：Bot 权限

这跟浏览器 capability detection（`navigator.geolocation` 是否可用）是一个思路——不同通道有不同能力，运行时探测而非硬编码。

### 名称解析——为什么需要 `resolve`？

`channels resolve <name>` 把用户名/通道名转换为 provider 目录标识符（如 WhatsApp 的 JID、Telegram 的 chat_id）。

这跟 DNS 解析是一个思路——人类友好的名字（"张三"）→ 机器标识（+8613800138000）。解析优先活跃匹配（重名时选在线的），降级返回而非失败（某些凭证不可访问时）。

---

Manages chat channel accounts: `channels list` (configured accounts with status tags), `channels status` (live transport state probe), `channels add` (interactive wizard), `channels remove` (stops listeners before config change). Capabilities probe detects provider-specific features (WhatsApp intents, Telegram permissions, Discord bot permissions). Name resolution translates human-friendly names to provider directory IDs.

管理聊天通道账户：`channels list`（已配置账户，含状态标签）、`channels status`（实时传输层状态探测）、`channels add`（交互式向导）、`channels remove`（先停止监听器再修改配置）。能力探测检测 provider 特定功能（WhatsApp 意图、Telegram 权限、Discord Bot 权限）。名称解析把人类友好名字转换为 provider 目录标识符。
