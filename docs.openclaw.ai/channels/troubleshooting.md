# Channel troubleshooting

> Use this page when a channel connects but behavior is wrong.

通道连上了但行为不对劲时翻这页。

---

> ## Command ladder

## 命令排查阶梯

> Run these in order first:

先按顺序跑这几条：

> ```bash
> openclaw status
> openclaw gateway status
> openclaw logs --follow
> openclaw doctor
> openclaw channels status --probe
> ```

```bash
openclaw status
openclaw gateway status
openclaw logs --follow
openclaw doctor
openclaw channels status --probe
```

> Healthy baseline:
>
> * `Runtime: running`
> * `Connectivity probe: ok`
> * `Capability: read-only`, `write-capable`, or `admin-capable`
> * Channel probe shows transport connected and, where supported, `works` or `audit ok`

健康状态的基线：

- `Runtime: running`
- `Connectivity probe: ok`
- `Capability: read-only`、`write-capable` 或 `admin-capable`
- 通道探测显示传输已连，且在支持的通道上看到 `works` 或 `audit ok`

---

> ## After an update

## 升级之后

> Use this when Telegram, iMessage, BlueBubbles-era configs, or another plugin channel disappears after updating.

升级之后 Telegram、iMessage、BlueBubbles 时代的配置或其他插件通道莫名其妙不见了，按这里走。

> ```bash
> openclaw status --all
> openclaw doctor --fix
> openclaw gateway restart
> openclaw status --all
> ```

```bash
openclaw status --all
openclaw doctor --fix
openclaw gateway restart
openclaw status --all
```

> Look for `plugin load failed: dependency tree corrupted; run openclaw doctor --fix` in `openclaw status --all`. That means the channel is configured, but the plugin setup/load path hit a corrupt dependency tree instead of registering the channel. `openclaw doctor --fix` removes stale plugin dependency staging directories and stale auth shadows, then `openclaw gateway restart` reloads the clean state.

`openclaw status --all` 输出里找一下 `plugin load failed: dependency tree corrupted; run openclaw doctor --fix`。看到这条说明通道是配好了的，但插件的安装 / 加载路径碰到了损坏的依赖树，没能注册通道。`openclaw doctor --fix` 会清掉过期的插件依赖暂存目录和过期的认证影子文件，再用 `openclaw gateway restart` 重新加载干净的状态。

---

> ## WhatsApp

## WhatsApp

> ### WhatsApp failure signatures

### WhatsApp 故障特征

> | Symptom                             | Fastest check                                       | Fix                                                                                                                              |
> | ----------------------------------- | --------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------- |
> | Connected but no DM replies         | `openclaw pairing list whatsapp`                    | Approve sender or switch DM policy/allowlist.                                                                                    |
> | Group messages ignored              | Check `requireMention` + mention patterns in config | Mention the bot or relax mention policy for that group.                                                                          |
> | QR login times out with 408         | Check gateway `HTTPS_PROXY` / `HTTP_PROXY` env      | Set a reachable proxy; use `NO_PROXY` only for bypasses.                                                                         |
> | Random disconnect/relogin loops     | `openclaw channels status --probe` + logs           | Recent reconnects are flagged even when currently connected; watch logs, restart the gateway, then relink if flapping continues. |
> | Replies arrive seconds/minutes late | `openclaw doctor --fix`                             | Doctor stops verified stale local TUI clients when they are degrading the Gateway event loop.                                    |

| 现象                              | 最快确认                                            | 修法                                                                                                                              |
| --------------------------------- | --------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------- |
| 连上了但私聊没回复                | `openclaw pairing list whatsapp`                    | 批准发件人；或调整 DM 策略 / 白名单。                                                                                             |
| 群消息被忽略                      | 看配置里的 `requireMention` 和 mention 模式         | @ 一下机器人；或者放松那个群的 @ 策略。                                                                                           |
| QR 登录 408 超时                  | 看 Gateway 的 `HTTPS_PROXY` / `HTTP_PROXY` 环境变量 | 配一个可达的代理；`NO_PROXY` 只用来配置例外。                                                                                     |
| 随机断线 / 反复重新登录           | `openclaw channels status --probe` + 日志           | 即便当前连上，最近的重连仍然会标出来。盯日志、重启 Gateway；持续抖动就重新链接。                                                  |
| 回复延迟几秒到几分钟              | `openclaw doctor --fix`                             | doctor 会在确认本地 TUI 客户端拖慢 Gateway 事件循环时把它们停掉。                                                                 |

> Full troubleshooting: [WhatsApp troubleshooting](/channels/whatsapp#troubleshooting)

完整排查：[WhatsApp 故障排查](/channels/whatsapp#troubleshooting)。

---

> ## Telegram

## Telegram

> ### Telegram failure signatures

### Telegram 故障特征

> | Symptom                              | Fastest check                                    | Fix                                                                                                                        |
> | ------------------------------------ | ------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------- |
> | `/start` but no usable reply flow    | `openclaw pairing list telegram`                 | Approve pairing or change DM policy.                                                                                       |
> | Bot online but group stays silent    | Verify mention requirement and bot privacy mode  | Disable privacy mode for group visibility or mention bot.                                                                  |
> | Send failures with network errors    | Inspect logs for Telegram API call failures      | Fix DNS/IPv6/proxy routing to `api.telegram.org`.                                                                          |
> | Startup reports `getMe returned 401` | Check configured token source                    | Re-copy or regenerate the BotFather token and update `botToken`, `tokenFile`, or default-account `TELEGRAM_BOT_TOKEN`.     |
> | Polling stalls or reconnects slowly  | `openclaw logs --follow` for polling diagnostics | Upgrade; if restarts are false positives, tune `pollingStallThresholdMs`. Persistent stalls still point to proxy/DNS/IPv6. |
> | `setMyCommands` rejected at startup  | Inspect logs for `BOT_COMMANDS_TOO_MUCH`         | Reduce plugin/skill/custom Telegram commands or disable native menus.                                                      |
> | Upgraded and allowlist blocks you    | `openclaw security audit` and config allowlists  | Run `openclaw doctor --fix` or replace `@username` with numeric sender IDs.                                                |

| 现象                                | 最快确认                                            | 修法                                                                                                          |
| ----------------------------------- | --------------------------------------------------- | ------------------------------------------------------------------------------------------------------------- |
| `/start` 但没有可用的回复流         | `openclaw pairing list telegram`                    | 批准配对；或改 DM 策略。                                                                                      |
| 机器人在线但群里安静                | 确认 @ 要求和机器人 privacy mode                    | 关掉 privacy mode 让机器人能看群消息；或者 @ 一下机器人。                                                     |
| 发送失败、报网络错误                | 看日志里的 Telegram API 调用失败                    | 修一下到 `api.telegram.org` 的 DNS / IPv6 / 代理路由。                                                        |
| 启动时报 `getMe returned 401`       | 检查 token 来源                                     | 在 BotFather 里重新复制或重新生成 token，更新 `botToken`、`tokenFile`，或默认账号的 `TELEGRAM_BOT_TOKEN`。     |
| Polling 卡住或重连缓慢              | `openclaw logs --follow` 看 polling 诊断信息        | 升级；如果重启是误报，调一下 `pollingStallThresholdMs`。持续卡住一般是代理 / DNS / IPv6 问题。                |
| 启动时 `setMyCommands` 被拒         | 看日志里有没有 `BOT_COMMANDS_TOO_MUCH`              | 减少插件 / skill / 自定义 Telegram 命令，或关掉原生菜单。                                                     |
| 升级后白名单把你拦了                | `openclaw security audit` 和配置白名单              | 跑 `openclaw doctor --fix`，或者把 `@username` 换成数字 sender ID。                                           |

> Full troubleshooting: [Telegram troubleshooting](/channels/telegram#troubleshooting)

完整排查：[Telegram 故障排查](/channels/telegram#troubleshooting)。

---

> ## Discord

## Discord

> ### Discord failure signatures

### Discord 故障特征

> | Symptom                                   | Fastest check                                                          | Fix                                                                                                                                                                     |
> | ----------------------------------------- | ---------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
> | Bot online but no guild replies           | `openclaw channels status --probe`                                     | Allow guild/channel and verify message content intent.                                                                                                                  |
> | Group messages ignored                    | Check logs for mention gating drops                                    | Mention bot or set guild/channel `requireMention: false`.                                                                                                               |
> | Typing/token usage but no Discord message | Session log shows assistant text with `didSendViaMessagingTool: false` | The model answered privately instead of calling the message tool. Use a tool-call-reliable model, or set `messages.groupChat.visibleReplies: "automatic"` to auto-post. |
> | DM replies missing                        | `openclaw pairing list discord`                                        | Approve DM pairing or adjust DM policy.                                                                                                                                 |

| 现象                                       | 最快确认                                                                  | 修法                                                                                                                                       |
| ------------------------------------------ | ------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| 机器人在线但 guild 里没回复                | `openclaw channels status --probe`                                        | 放行 guild / 频道，并确认 message content intent。                                                                                         |
| 群消息被忽略                               | 看日志里有没有 @ 触发被丢弃                                               | @ 一下机器人；或者把 guild / 频道的 `requireMention` 设成 `false`。                                                                        |
| 看到 typing / token 消耗但 Discord 没消息 | 会话日志显示 assistant 有文本，但 `didSendViaMessagingTool: false`        | 模型私下回复了，没调消息工具。换一个调工具靠谱的模型；或把 `messages.groupChat.visibleReplies` 设成 `"automatic"` 让它自动可见回复。       |
| 私聊没回复                                 | `openclaw pairing list discord`                                           | 批准 DM 配对；或调 DM 策略。                                                                                                               |

> Full troubleshooting: [Discord troubleshooting](/channels/discord#troubleshooting)

完整排查：[Discord 故障排查](/channels/discord#troubleshooting)。

---

> ## Slack

## Slack

> ### Slack failure signatures

### Slack 故障特征

> | Symptom                                | Fastest check                             | Fix                                                                                                                                                  |
> | -------------------------------------- | ----------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------- |
> | Socket mode connected but no responses | `openclaw channels status --probe`        | Verify app token + bot token and required scopes; watch for `botTokenStatus` / `appTokenStatus = configured_unavailable` on SecretRef-backed setups. |
> | DMs blocked                            | `openclaw pairing list slack`             | Approve pairing or relax DM policy.                                                                                                                  |
> | Channel message ignored                | Check `groupPolicy` and channel allowlist | Allow the channel or switch policy to `open`.                                                                                                        |

| 现象                              | 最快确认                                | 修法                                                                                                                                             |
| --------------------------------- | --------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------ |
| Socket mode 连上但没响应          | `openclaw channels status --probe`      | 检查 app token + bot token 和需要的 scope；用 SecretRef 时留意 `botTokenStatus` / `appTokenStatus = configured_unavailable`。                    |
| 私聊被拦                          | `openclaw pairing list slack`           | 批准配对；或放宽 DM 策略。                                                                                                                       |
| 频道消息被忽略                    | 检查 `groupPolicy` 和频道白名单         | 把频道加进白名单；或者把策略改成 `open`。                                                                                                        |

> Full troubleshooting: [Slack troubleshooting](/channels/slack#troubleshooting)

完整排查：[Slack 故障排查](/channels/slack#troubleshooting)。

---

> ## iMessage

## iMessage

> ### iMessage failure signatures

### iMessage 故障特征

> | Symptom                              | Fastest check                                           | Fix                                                                   |
> | ------------------------------------ | ------------------------------------------------------- | --------------------------------------------------------------------- |
> | `imsg` missing or fails on non-macOS | `openclaw channels status --probe --channel imessage`   | Run OpenClaw on the Messages Mac or use an SSH wrapper for `cliPath`. |
> | Can send but no receive on macOS     | Check macOS privacy permissions for Messages automation | Re-grant TCC permissions and restart channel process.                 |
> | DM sender blocked                    | `openclaw pairing list imessage`                        | Approve pairing or update allowlist.                                  |

| 现象                                   | 最快确认                                                         | 修法                                                                              |
| -------------------------------------- | ---------------------------------------------------------------- | --------------------------------------------------------------------------------- |
| `imsg` 缺失或在非 macOS 上失败         | `openclaw channels status --probe --channel imessage`            | 在 Messages 所在的 Mac 上跑 OpenClaw；或者给 `cliPath` 加一个 SSH 包装。          |
| macOS 上能发但收不到                   | 检查 macOS 给 Messages 自动化的隐私权限                          | 重新授权 TCC，再重启通道进程。                                                    |
| 私聊发件人被拦                         | `openclaw pairing list imessage`                                 | 批准配对；或更新白名单。                                                          |

> Full troubleshooting:
>
> * [iMessage troubleshooting](/channels/imessage#troubleshooting)

完整排查：

- [iMessage 故障排查](/channels/imessage#troubleshooting)

---

> ## Signal

## Signal

> ### Signal failure signatures

### Signal 故障特征

> | Symptom                         | Fastest check                              | Fix                                                      |
> | ------------------------------- | ------------------------------------------ | -------------------------------------------------------- |
> | Daemon reachable but bot silent | `openclaw channels status --probe`         | Verify `signal-cli` daemon URL/account and receive mode. |
> | DM blocked                      | `openclaw pairing list signal`             | Approve sender or adjust DM policy.                      |
> | Group replies do not trigger    | Check group allowlist and mention patterns | Add sender/group or loosen gating.                       |

| 现象                          | 最快确认                                | 修法                                                          |
| ----------------------------- | --------------------------------------- | ------------------------------------------------------------- |
| daemon 能连但机器人没声音     | `openclaw channels status --probe`      | 检查 `signal-cli` daemon 的 URL / 账号和接收模式。            |
| 私聊被拦                      | `openclaw pairing list signal`          | 批准发件人；或调整 DM 策略。                                  |
| 群回复触发不了                | 检查群白名单和 mention 模式             | 把发件人 / 群加进去；或放宽 @ 触发规则。                      |

> Full troubleshooting: [Signal troubleshooting](/channels/signal#troubleshooting)

完整排查：[Signal 故障排查](/channels/signal#troubleshooting)。

---

> ## QQ Bot

## QQ Bot

> ### QQ Bot failure signatures

### QQ Bot 故障特征

> | Symptom                         | Fastest check                               | Fix                                                             |
> | ------------------------------- | ------------------------------------------- | --------------------------------------------------------------- |
> | Bot replies "gone to Mars"      | Verify `appId` and `clientSecret` in config | Set credentials or restart the gateway.                         |
> | No inbound messages             | `openclaw channels status --probe`          | Verify credentials on the QQ Open Platform.                     |
> | Voice not transcribed           | Check STT provider config                   | Configure `channels.qqbot.stt` or `tools.media.audio`.          |
> | Proactive messages not arriving | Check QQ platform interaction requirements  | QQ may block bot-initiated messages without recent interaction. |

| 现象                         | 最快确认                                       | 修法                                                                     |
| ---------------------------- | ---------------------------------------------- | ------------------------------------------------------------------------ |
| 机器人回复 "gone to Mars"    | 确认配置里的 `appId` 和 `clientSecret`         | 写凭证，或重启 Gateway。                                                 |
| 没有收到消息                 | `openclaw channels status --probe`             | 在 QQ 开放平台核对凭证。                                                 |
| 语音没被转写                 | 检查 STT provider 配置                         | 配 `channels.qqbot.stt` 或 `tools.media.audio`。                         |
| 主动消息发不出去             | 检查 QQ 平台对互动的要求                       | 用户最近没互动时，QQ 可能拦截机器人主动发起的消息。                      |

> Full troubleshooting: [QQ Bot troubleshooting](/channels/qqbot#troubleshooting)

完整排查：[QQ Bot 故障排查](/channels/qqbot#troubleshooting)。

---

> ## Matrix

## Matrix

> ### Matrix failure signatures

### Matrix 故障特征

> | Symptom                             | Fastest check                          | Fix                                                                       |
> | ----------------------------------- | -------------------------------------- | ------------------------------------------------------------------------- |
> | Logged in but ignores room messages | `openclaw channels status --probe`     | Check `groupPolicy`, room allowlist, and mention gating.                  |
> | DMs do not process                  | `openclaw pairing list matrix`         | Approve sender or adjust DM policy.                                       |
> | Encrypted rooms fail                | `openclaw matrix verify status`        | Re-verify the device, then check `openclaw matrix verify backup status`.  |
> | Backup restore is pending/broken    | `openclaw matrix verify backup status` | Run `openclaw matrix verify backup restore` or rerun with a recovery key. |
> | Cross-signing/bootstrap looks wrong | `openclaw matrix verify bootstrap`     | Repair secret storage, cross-signing, and backup state in one pass.       |

| 现象                                | 最快确认                                | 修法                                                                                      |
| ----------------------------------- | --------------------------------------- | ----------------------------------------------------------------------------------------- |
| 登录上了但忽略房间消息              | `openclaw channels status --probe`      | 检查 `groupPolicy`、房间白名单和 @ 触发。                                                 |
| 私聊不处理                          | `openclaw pairing list matrix`          | 批准发件人；或调整 DM 策略。                                                              |
| 加密房间报错                        | `openclaw matrix verify status`         | 重新校验设备，然后看 `openclaw matrix verify backup status`。                             |
| 备份恢复一直 pending 或坏掉         | `openclaw matrix verify backup status`  | 跑 `openclaw matrix verify backup restore`；或者带恢复 key 重新跑。                       |
| 交叉签名 / 引导看起来不对           | `openclaw matrix verify bootstrap`      | 一次修好 secret storage、交叉签名和备份状态。                                             |

> Full setup and config: [Matrix](/channels/matrix)

完整安装和配置：[Matrix](/channels/matrix)。

---

> ## Related

## 相关

> * [Pairing](/channels/pairing)
> * [Channel routing](/channels/channel-routing)
> * [Gateway troubleshooting](/gateway/troubleshooting)

- [配对](/channels/pairing)
- [通道路由](/channels/channel-routing)
- [Gateway 故障排查](/gateway/troubleshooting)
