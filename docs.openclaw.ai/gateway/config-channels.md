# Configuration — Channels

## 架构精读

> 跳过不影响阅读翻译正文。

### 私信策略与群组策略——为什么默认策略相反？

频道访问控制有两个维度：

- **私信策略**：默认 `pairing`（需配对码），可选 `allowlist`/`open`/`disabled`
- **群组策略**：默认 `allowlist`（需显式允许），可选 `open`/`disabled`

这跟防火墙的默认拒绝与默认允许是一个思路——私信是 1 对 1（风险低，默认 `pairing` 方便但需验证），群组是 1 对多（风险高，默认 `allowlist` 严格）。

关键设计是**风险分级**。私信的配对码 1 小时过期、待处理请求上限 3 个（防滥用）。群组必须显式配置允许的群组 ID（防“群里任何人跟机器人说话”）。

### 提及门槛——为什么群组默认要求 @？

群组消息默认要求提及（原生平台 @ 或安全正则表达式模式），私信不要求。

这跟 Slack 机器人默认行为是一个思路——只响应 @ 消息或特定命令，不干扰正常交流。

设计原因是**噪音控制 + 隐私保护 + 成本**。群组里代理响应所有消息会产生噪音、浪费 LLM 调用、读取无关对话。提及门槛让用户明确想跟代理对话时才激活。

### 多账户——为什么同频道需要多机器人身份？

同一频道可以配置多个账户：

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

这跟 AWS 多角色是一个思路——不同代理用不同机器人身份（名字/头像），用户一眼就知道在跟谁对话。`accountId` 省略时用 `default`。

代价是需要管理多个机器人令牌。但这提升了用户体验——`coding` 机器人和 `support` 机器人各有独立身份。

### 每个频道独立模型覆盖——为什么？

`channels.modelByChannel` 可以按频道 ID 指定不同模型：

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

这跟 K8s 资源请求/限制的按 Pod 配置是一个思路——每个场景用最合适的模型。WhatsApp 用手机/短消息适合快/便宜模型，Slack 用工作/复杂问题适合强/贵模型。

---

Per-channel configuration keys under `channels.*`. Covers DM and group access, multi-account setups, mention gating, and per-channel keys for Slack, Discord, Telegram, WhatsApp, Matrix, iMessage, and the other bundled channel plugins.

`channels.*` 下的 per-channel 配置键。覆盖 DM 和 group 访问控制、多账户设置、mention gating，以及 Slack/Discord/Telegram/WhatsApp/Matrix/iMessage 和其他内置 channel 插件的 per-channel 键。

For agents, tools, gateway runtime, and other top-level keys, see the Configuration reference.

agents、tools、gateway 运行时和其他顶层键见 Configuration reference。