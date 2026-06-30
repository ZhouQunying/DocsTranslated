# `openclaw voicecall`

## 架构精读

> 跳过不影响阅读翻译正文。

### 语音通话——为什么需要命令行发起？

`openclaw voicecall` 从命令行发起语音通话：

```
openclaw voicecall --channel whatsapp --to "+1234567890"
```

这跟 `twilio call` 是一个思路——命令行发起通话，支持脚本集成（如自动呼叫、定时提醒）。

### 通话转接——为什么支持转接到智能体？

通话可以转接到智能体处理（智能体接听并对话）：

```
openclaw voicecall --to "+1234567890" --agent customer-support
```

这跟 IVR（交互式语音应答）的"按 0 转人工"是一个思路——通话可以路由到不同处理方（人工/智能体）。智能体接听适合"自动客服"场景。

---

Initiates voice calls from command line: `openclaw voicecall --channel whatsapp --to "+1234567890"`. Supports call routing to agents (`--agent customer-support`) for automated customer service. Scriptable for automated calling and scheduled reminders.

从命令行发起语音通话：`openclaw voicecall --channel whatsapp --to "+1234567890"`。支持通话路由到智能体（`--agent customer-support`）用于自动客服。可脚本化用于自动呼叫和定时提醒。
