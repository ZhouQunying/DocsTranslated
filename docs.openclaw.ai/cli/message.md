# `openclaw message`

## 架构精读

> 跳过不影响阅读翻译正文。

### 消息发送——为什么需要命令行发消息？

`openclaw message` 从命令行发送消息到指定通道：

```
openclaw message send --channel whatsapp --to "+1234567890" --text "Hello"
```

这跟 `twilio send` 和 `telegram-cli` 是一个思路——命令行发送消息，支持脚本集成（如 cron 定时通知、CI 构建完成通知）。

### 多通道统一——为什么一个命令覆盖所有通道？

统一的 `--channel` 参数覆盖所有支持的通道（WhatsApp/Telegram/Discord/Slack 等），无需为每个通道学不同命令。

这跟 `aws sns publish` 是一个思路——统一接口屏蔽底层通道差异（SMS/Email/Push）。用户只需要学一套命令。

---

Send messages from command line to any channel: `message send --channel whatsapp --to "+1234567890" --text "Hello"`. Unified `--channel` parameter covers all supported channels (WhatsApp/Telegram/Discord/Slack), enabling script integration (cron notifications, CI alerts).

从命令行发送消息到任意通道：`message send --channel whatsapp --to "+1234567890" --text "Hello"`。统一的 `--channel` 参数覆盖所有支持的通道（WhatsApp/Telegram/Discord/Slack），支持脚本集成（cron 通知、CI 告警）。
