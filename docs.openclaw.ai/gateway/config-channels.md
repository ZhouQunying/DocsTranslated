# Configuration — Channels

## 架构精读

> 跳过不影响阅读翻译正文。

### DM policy vs group policy——为什么默认策略相反？

Channel 访问控制有两个维度：

- **DM policy**：默认 `pairing`（需配对码），可选 `allowlist`/`open`/`disabled`
- **Group policy**：默认 `allowlist`（需显式允许），可选 `open`/`disabled`

这跟防火墙的 default-deny vs default-allow 是一个思路——DM 是 1 对 1（风险低，默认 pairing 方便但需验证），group 是 1 对多（风险高，默认 allowlist 严格）。

关键设计是**风险分级**。DM 的 pairing code 1 小时过期、pending 请求上限 3 个（防滥用）。Group 必须显式配置允许的 group ID（防"群里任何人跟 bot 说话"）。

### Mention gating——为什么群组默认要求 @？

Group messages 默认要求 mention（native platform @ 或 safe regex pattern），DM 不要求。

这跟 Slack bot 默认行为是一个思路——只响应 @ 消息或特定 command，不干扰正常交流。

设计原因是**噪音控制 + 隐私保护 + 成本**。群组里 agent 响应所有消息会产生噪音、浪费 LLM 调用、读取无关对话。Mention gating 让用户明确想跟 agent 对话时才激活。

### Multi-account——为什么同 channel 需要多 bot 身份？

同一 channel 可以配置多个 account：

```json5
{
  channels: {
    slack: {
      accounts: {
        coding: { botToken: "xoxb-coding..." },
        support: { botToken: "xoxb-support..." }
      }
    }
  }
}
```

这跟 AWS 多 role 是一个思路——不同 agent 用不同 bot 身份（名字/头像），用户一眼就知道在跟谁对话。`accountId` 省略时用 `default`。

代价是需要管理多个 bot token。但这提升了用户体验——coding bot 和 support bot 各有独立身份。

### 每个 channel 独立 model override——为什么？

`channels.modelByChannel` 可以按 channel ID 指定不同模型：

```json5
{
  channels: {
    modelByChannel: {
      whatsapp: "gpt-3.5-turbo",  // 手机、短消息、快响应
      slack: "gpt-4"              // 工作、复杂问题
    }
  }
}
```

这跟 K8s resource request/limit 的 per-pod 配置是一个思路——每个场景用最合适的模型。WhatsApp 用手机/短消息适合快/便宜模型，Slack 用工作/复杂问题适合强/贵模型。

---

Per-channel configuration keys under `channels.*`. Covers DM and group access, multi-account setups, mention gating, and per-channel keys for Slack, Discord, Telegram, WhatsApp, Matrix, iMessage, and the other bundled channel plugins.

`channels.*` 下的 per-channel 配置键。覆盖 DM 和 group 访问控制、多账户设置、mention gating，以及 Slack/Discord/Telegram/WhatsApp/Matrix/iMessage 和其他内置 channel 插件的 per-channel 键。

For agents, tools, gateway runtime, and other top-level keys, see the Configuration reference.

agents、tools、gateway 运行时和其他顶层键见 Configuration reference。