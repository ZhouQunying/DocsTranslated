# Progress drafts

> Progress drafts make long-running agent turns feel alive in chat without turning the conversation into a stack of temporary status replies.

进度草稿让长时 agent 轮次在聊天里保持活跃，又不会把对话堆成一摞临时状态回复。

> When progress drafts are enabled, OpenClaw creates one visible work-in-progress message only after the turn proves it is doing real work, updates it while the agent reads, plans, calls tools, or waits for approval, and then turns that draft into the final answer when the channel can do that safely.

启用进度草稿后，OpenClaw 只在轮次确实开始干活时才创建一条可见的"工作中"消息。agent 读、规划、调工具或等批准时持续更新它。通道能安全转换时，这条草稿会直接变成最终答案。

> ```text
> Shelling...
> 📖 from docs/concepts/progress-drafts.md
> 🔎 Web Search: for "discord edit message"
> 🛠️ Bash: run tests
> ```

```text
Shelling...
📖 from docs/concepts/progress-drafts.md
🔎 Web Search: for "discord edit message"
🛠️ Bash: run tests
```

> Use progress drafts when you want one tidy status message during tool-heavy work and the final answer when the turn is done.

工具密集型工作期间想要一条整洁的状态消息、轮次结束时再给最终答案 —— 用进度草稿。

---

> ## Quick start

## 快速上手

> Enable progress drafts per channel with `streaming.mode: "progress"`:

按通道用 `streaming.mode: "progress"` 启用进度草稿：

> ```json5
> {
>   channels: {
>     discord: {
>       streaming: {
>         mode: "progress",
>       },
>     },
>   },
> }
> ```

```json5
{
  channels: {
    discord: {
      streaming: {
        mode: "progress",
      },
    },
  },
}
```

> That is usually enough. OpenClaw will pick an automatic one-word label, wait until work lasts at least five seconds or emits a second work event, add compact progress lines while useful work happens, and suppress duplicate standalone progress chatter for that turn.

通常够用。OpenClaw 会自动选一个一词标签，等到工作持续满 5 秒或发出第二条工作事件后才显示。有实际工作时追加紧凑进度行，同时抑制该轮次重复的独立进度消息。

---

> ## What users see

## 用户看到什么

> A progress draft has two parts:

进度草稿有两部分：

> | Part           | Purpose                                                                               |
> | -------------- | ------------------------------------------------------------------------------------- |
> | Label          | A short starter/status line such as `Working` or `Shelling`.                          |
> | Progress lines | Compact run updates using the same tool icons and detail formatter as verbose output. |

| 部分      | 作用                                                                                |
| --------- | ----------------------------------------------------------------------------------- |
| 标签      | 一行简短的开场/状态文字，如 `Working` 或 `Shelling`。                               |
| 进度行    | 紧凑的运行更新，用与 verbose 输出相同的工具图标和详情格式化器。                     |

> The label appears after the agent starts meaningful work and either remains busy for five seconds or emits a second work event. It is part of the rolling progress line list, so the starter status scrolls away once enough concrete work appears. Plain text-only replies do not show a progress draft. Progress lines are added only when the agent emits useful work updates, for example `🛠️ Bash: run tests`, `🔎 Web Search: for "discord edit message"`, or `✍️ Write: to /tmp/file`. By default they use the same compact explain mode as `/verbose`; set `agents.defaults.toolProgressDetail: "raw"` when debugging and you also want raw commands/details appended. The final answer replaces the draft when possible; otherwise OpenClaw sends the final answer normally and cleans up or stops updating the draft according to the channel's transport.

标签在 agent 开始有意义的工作后出现，且要么忙了 5 秒、要么发出第二条工作事件。它是滚动进度行列表的一部分，所以足够多的具体工作出现后，开场状态会滚走。纯文本回复不显示进度草稿。只有在 agent 发出有用的工作更新时才追加进度行，比如 `🛠️ Bash: run tests`、`🔎 Web Search: for "discord edit message"`、`✍️ Write: to /tmp/file`。默认用与 `/verbose` 同款的紧凑 explain 模式；调试时如果还想附原始命令 / 明细，把 `agents.defaults.toolProgressDetail` 设成 `"raw"`。最终答案在可能时替换草稿；否则 OpenClaw 正常发最终答案，按通道传输清理或停止更新草稿。

---

> ## Choose a mode

## 选模式

> `channels.<channel>.streaming.mode` controls the visible in-progress behavior:

`channels.<channel>.streaming.mode` 控制可见的"进行中"行为：

> | Mode       | Best for                         | What appears in chat                              |
> | ---------- | -------------------------------- | ------------------------------------------------- |
> | `off`      | Quiet channels                   | Only the final answer.                            |
> | `partial`  | Watching answer text appear      | One draft edited with the latest answer text.     |
> | `block`    | Larger answer-preview chunks     | One preview updated or appended in bigger chunks. |
> | `progress` | Tool-heavy or long-running turns | One status draft, then the final answer.          |

| 模式       | 适合场景                              | 聊天里看到什么                                  |
| ---------- | ------------------------------------- | ----------------------------------------------- |
| `off`      | 安静的通道                            | 只有最终答案。                                  |
| `partial`  | 想看答案文本逐步出现                  | 一条草稿，被最新答案文本编辑。                  |
| `block`    | 较大的答案预览块                      | 一条预览，按更大块更新或追加。                  |
| `progress` | 工具密集或长时轮次                    | 一条状态草稿，然后是最终答案。                  |

> Choose `progress` when users care more about "what is happening" than watching the answer text stream token by token.

用户更在意"正在发生什么"而不是逐 token 看答案流时，选 `progress`。

> Choose `partial` when the answer itself is the progress signal.

答案本身就是进度信号时，选 `partial`。

> Choose `block` when you want draft preview updates in larger text chunks. On Discord and Telegram, `streaming.mode: "block"` is still preview streaming, not normal block delivery. Use `streaming.block.enabled` or legacy `blockStreaming` when you want normal block replies.

想要更大文本块的草稿预览更新时选 `block`。在 Discord 和 Telegram 上，`streaming.mode: "block"` 仍然是预览流式，不是常规 block 投递。要常规 block 回复用 `streaming.block.enabled` 或旧版 `blockStreaming`。

---

> ## Configure labels

## 配置标签

> Progress labels live under `channels.<channel>.streaming.progress`.

进度标签放在 `channels.<channel>.streaming.progress` 下。

> The default label is `auto`, which chooses from OpenClaw's built-in single-word label pool:

默认标签是 `auto`，从 OpenClaw 内置的单词标签池里选：

> ```text
> Working
> Shelling
> Scuttling
> Clawing
> Pinching
> Molting
> Bubbling
> Tiding
> Reefing
> Cracking
> Sifting
> Brining
> Nautiling
> Krilling
> Barnacling
> Lobstering
> Tidepooling
> Pearling
> Snapping
> Surfacing
> ```

```text
Working
Shelling
Scuttling
Clawing
Pinching
Molting
Bubbling
Tiding
Reefing
Cracking
Sifting
Brining
Nautiling
Krilling
Barnacling
Lobstering
Tidepooling
Pearling
Snapping
Surfacing
```

> Use a fixed label:
>
> ```json5
> {
>   channels: {
>     discord: {
>       streaming: {
>         mode: "progress",
>         progress: {
>           label: "Investigating",
>         },
>       },
>     },
>   },
> }
> ```

用固定标签：

```json5
{
  channels: {
    discord: {
      streaming: {
        mode: "progress",
        progress: {
          label: "Investigating",
        },
      },
    },
  },
}
```

> Use your own automatic label pool:
>
> ```json5
> {
>   channels: {
>     discord: {
>       streaming: {
>         mode: "progress",
>         progress: {
>           label: "auto",
>           labels: ["Checking", "Reading", "Testing", "Finishing"],
>         },
>       },
>     },
>   },
> }
> ```

用你自己的自动标签池：

```json5
{
  channels: {
    discord: {
      streaming: {
        mode: "progress",
        progress: {
          label: "auto",
          labels: ["Checking", "Reading", "Testing", "Finishing"],
        },
      },
    },
  },
}
```

> Hide the label and show only progress lines:
>
> ```json5
> {
>   channels: {
>     discord: {
>       streaming: {
>         mode: "progress",
>         progress: {
>           label: false,
>         },
>       },
>     },
>   },
> }
> ```

隐藏标签、只显示进度行：

```json5
{
  channels: {
    discord: {
      streaming: {
        mode: "progress",
        progress: {
          label: false,
        },
      },
    },
  },
}
```

---

> ## Control progress lines

## 控制进度行

> Progress lines are enabled by default in progress mode. They come from real run events: tool starts, item updates, task plans, approvals, command output, patch summaries, and similar agent activity.

`progress` 模式下进度行默认开。它们来自真实运行事件：工具启动、项目更新、任务计划、批准、命令输出、补丁摘要、以及类似的 agent 活动。

> Tools can also emit typed progress while a single tool call is still running. That is how a slow fetch or search can update the visible draft before the tool returns its final result. The progress update is a partial tool result with empty model content and explicit public channel metadata:

工具在单次调用仍在运行期间也可以发出带类型的进度信息。慢速请求或搜索就是靠这个在工具返回最终结果之前更新可见草稿的。进度更新是一种部分工具结果，模型内容为空，带显式的公开通道元数据：

> ```json
> {
>   "content": [],
>   "progress": {
>     "text": "Fetching page content...",
>     "visibility": "channel",
>     "privacy": "public",
>     "id": "web_fetch:fetching"
>   }
> }
> ```

```json
{
  "content": [],
  "progress": {
    "text": "Fetching page content...",
    "visibility": "channel",
    "privacy": "public",
    "id": "web_fetch:fetching"
  }
}
```

> OpenClaw renders only the `progress.text` in the channel progress UI. The normal tool result still arrives later as `content` and `details`, and is the only part returned to the model.

OpenClaw 只把 `progress.text` 渲染到通道进度 UI 里。正常的工具结果稍后仍然以 `content` 和 `details` 到达，那才是返回给模型的部分。

> When adding progress to a tool, use a short, generic message and delay it until the operation has been pending long enough to be useful:

给工具加进度时，用简短通用的消息，等操作挂起够久再发：

> ```typescript
> const clearProgressTimer = scheduleToolProgress(
>   onUpdate,
>   { text: "Fetching page content...", id: "web_fetch:fetching" },
>   5_000,
>   { signal },
> );
>
> try {
>   return await runToolWork();
> } finally {
>   clearProgressTimer();
> }
> ```

```typescript
const clearProgressTimer = scheduleToolProgress(
  onUpdate,
  { text: "Fetching page content...", id: "web_fetch:fetching" },
  5_000,
  { signal },
);

try {
  return await runToolWork();
} finally {
  clearProgressTimer();
}
```

> This pattern means fast calls do not show a progress line, long calls show one while they are still pending, and canceled calls clear the timer before stale progress can appear. Progress text is a public UI side channel, so it must not include secrets, raw arguments, fetched content, command output, or page text.

这个模式的效果是：快的调用不显示进度行，慢的调用在挂起期间显示一条，取消的调用在过期进度出现前清掉计时器。进度文本是公开的 UI 旁路通道，不能包含密钥、原始参数、抓取内容、命令输出或页面文本。

> OpenClaw uses the same formatter for progress drafts and `/verbose`:
>
> ```json5
> {
>   agents: {
>     defaults: {
>       toolProgressDetail: "explain", // explain | raw
>     },
>   },
> }
> ```

OpenClaw 给进度草稿和 `/verbose` 用同一个格式化器：

```json5
{
  agents: {
    defaults: {
      toolProgressDetail: "explain", // explain | raw
    },
  },
}
```

> `"explain"` is the default and keeps drafts stable with concise labels like `🛠️ check JS syntax for /tmp/app.js`. `"raw"` appends the underlying command/detail when available, which is useful while debugging but noisier in chat.

`"explain"` 是默认，用 `🛠️ check JS syntax for /tmp/app.js` 这种简短标签让草稿稳定。`"raw"` 在可用时附上底层命令 / 明细，调试好用但聊天里更吵。

> For example, the same command appears differently depending on the detail mode:
>
> | Mode      | Progress line                                                   |
> | --------- | --------------------------------------------------------------- |
> | `explain` | `🛠️ check JS syntax for /tmp/app.js`                           |
> | `raw`     | `🛠️ check JS syntax for /tmp/app.js, node --check /tmp/app.js` |

例子：同一条命令按明细模式显示不一样：

| 模式      | 进度行                                                            |
| --------- | ----------------------------------------------------------------- |
| `explain` | `🛠️ check JS syntax for /tmp/app.js`                              |
| `raw`     | `🛠️ check JS syntax for /tmp/app.js, node --check /tmp/app.js`    |

> Limit how many lines stay visible:
>
> ```json5
> {
>   channels: {
>     discord: {
>       streaming: {
>         mode: "progress",
>         progress: {
>           maxLines: 4,
>         },
>       },
>     },
>   },
> }
> ```

限制可见行数：

```json5
{
  channels: {
    discord: {
      streaming: {
        mode: "progress",
        progress: {
          maxLines: 4,
        },
      },
    },
  },
}
```

> Progress lines are compacted automatically to reduce chat-bubble reflow while the draft is edited.

进度行会自动紧凑化，减少草稿编辑时聊天气泡的重排。

> OpenClaw truncates long progress lines by default so repeated draft edits do not wrap differently on every update. The default per-line budget is 120 characters. Prose cuts at a word boundary, while long details such as paths or raw commands are shortened with a middle ellipsis so the suffix remains visible.

OpenClaw 默认截断长进度行，避免反复编辑草稿时每次换行位置不同。默认单行预算 120 字符。正文在词边界处截断，长详情（如路径或原始命令）用中间省略号截短，后缀仍然可见。

> Tune the per-line budget:
>
> ```json5
> {
>   channels: {
>     discord: {
>       streaming: {
>         mode: "progress",
>         progress: {
>           maxLineChars: 160,
>         },
>       },
>     },
>   },
> }
> ```

调整单行预算：

```json5
{
  channels: {
    discord: {
      streaming: {
        mode: "progress",
        progress: {
          maxLineChars: 160,
        },
      },
    },
  },
}
```

> Slack can render progress lines as structured Block Kit fields instead of a single text body:
>
> ```json5
> {
>   channels: {
>     slack: {
>       streaming: {
>         mode: "progress",
>         progress: {
>           render: "rich",
>         },
>       },
>     },
>   },
> }
> ```

Slack 可以把进度行渲染成结构化的 Block Kit 字段，而不是单一文本：

```json5
{
  channels: {
    slack: {
      streaming: {
        mode: "progress",
        progress: {
          render: "rich",
        },
      },
    },
  },
}
```

> Rich rendering keeps the same plain-text fallback so channels and clients that do not support the richer shape can still show the compact progress text.

丰富渲染仍带同样的纯文本回退——不支持这种格式的通道和客户端仍能显示紧凑进度文本。

> Keep the single progress draft but hide tool and task lines:
>
> ```json5
> {
>   channels: {
>     discord: {
>       streaming: {
>         mode: "progress",
>         progress: {
>           toolProgress: false,
>         },
>       },
>     },
>   },
> }
> ```

保留单一进度草稿但隐藏工具和任务行：

```json5
{
  channels: {
    discord: {
      streaming: {
        mode: "progress",
        progress: {
          toolProgress: false,
        },
      },
    },
  },
}
```

> With `toolProgress: false`, OpenClaw still suppresses the older standalone tool-progress messages for that turn. The channel stays visually quiet until the final answer, except for the label if one is configured.

`toolProgress: false` 时，OpenClaw 仍然抑制该轮的旧版独立工具进度消息。通道在最终答案之前保持安静（如果配了标签则有标签）。

---

> ## Channel behavior

## 通道行为

> Each channel uses the cleanest transport it supports:

每个通道用它支持的最干净的传输：

> | Channel         | Progress transport                     | Notes                                                                 |
> | --------------- | -------------------------------------- | --------------------------------------------------------------------- |
> | Discord         | Send one message, then edit it.        | Final text edits in place when it fits one safe preview message.      |
> | Matrix          | Send one event, then edit it.          | Account-level streaming config controls account-level drafts.         |
> | Microsoft Teams | Native Teams stream in personal chats. | `streaming.mode: "block"` maps to Teams block delivery.               |
> | Slack           | Native stream or editable draft post.  | Thread availability affects whether native streaming can be used.     |
> | Telegram        | Send one message, then edit it.        | Older visible drafts may be replaced so final timestamps stay useful. |
> | Mattermost      | Editable draft post.                   | Tool activity is folded into the same draft-style post.               |

| 通道            | 进度传输                            | 说明                                                                    |
| --------------- | ----------------------------------- | ----------------------------------------------------------------------- |
| Discord         | 发一条消息，然后编辑。             | 最终文本能塞进一条安全预览消息时原地 edit。                             |
| Matrix          | 发一条 event，然后编辑。           | 账号级流式配置控制账号级草稿。                                          |
| Microsoft Teams | 个人聊天里用 Teams 原生流。         | `streaming.mode: "block"` 映射到 Teams block 投递。                     |
| Slack           | 原生流或可编辑草稿 post。           | thread 可用性影响是否能用原生流。                                       |
| Telegram        | 发一条消息，然后编辑。             | 旧的可见草稿可能被替换，让最终时间戳更有用。                            |
| Mattermost      | 可编辑草稿 post。                   | 工具活动折进同一条草稿风格消息。                                       |

> Channels without safe edit support usually fall back to typing indicators or final-only delivery.

不支持安全编辑的通道通常回退到输入中状态或仅最终投递。

---

> ## Finalization

## 收尾

> When the final answer is ready, OpenClaw tries to keep the chat clean:
>
> * If the draft can safely become the final answer, OpenClaw edits it in place.
> * If the channel uses native progress streaming, OpenClaw finalizes that stream when the native transport accepts the final text.
> * If the final answer has media, an approval prompt, an explicit reply target, too many chunks, or a failed edit/send, OpenClaw sends the final answer through the normal channel delivery path.

最终答案就绪时，OpenClaw 尽量保持聊天干净：

- 草稿能安全变成最终答案时，OpenClaw 原地编辑。
- 通道用原生 progress 流式时，原生传输接受最终文本时 OpenClaw 收尾该流。
- 最终答案带媒体、批准提示、显式回复目标、块太多或 edit / send 失败时，OpenClaw 走通道常规投递路径。

> The fallback path is intentional. It is better to send a fresh final answer than to lose text, mis-thread a reply, or overwrite a draft with a payload the channel cannot represent safely.

回退路径是有意为之。发一条新的最终答案，比丢文本、错 thread、或用通道无法安全表示的载荷覆盖草稿更好。

---

> ## Troubleshooting

## 故障排查

> **I only see the final answer.**

**我只看到最终答案。**

> Check that `channels.<channel>.streaming.mode` is set to `progress` for the account or channel that handled the message. Some group or quote-reply paths may disable draft previews for a turn when the channel cannot safely edit the right message.

确认处理这条消息的账号或通道的 `channels.<channel>.streaming.mode` 设成了 `progress`。某些群或引用回复路径，在通道没法安全编辑正确消息时，会让该轮次禁用草稿预览。

> **I see the label but no tool lines.**

**只看到标签、没有工具行。**

> Check `streaming.progress.toolProgress`. If it is `false`, OpenClaw keeps the single draft behavior but hides tool and task progress lines.

检查 `streaming.progress.toolProgress`。设成 `false` 时，OpenClaw 保留单一草稿行为但隐藏工具和任务进度行。

> **I see a fresh final message instead of an edited draft.**

**看到一条新的最终消息，而不是编辑过的草稿。**

> That is a safety fallback. It can happen for media replies, long answers, explicit reply targets, old Telegram drafts, missing Slack thread targets, deleted preview messages, or failed native stream finalization.

那是安全回退。媒体回复、长答案、显式回复目标、过老的 Telegram 草稿、缺失的 Slack thread 目标、被删的预览消息、原生流收尾失败时都可能发生。

> **I still see standalone progress messages.**

**仍然看到独立的进度消息。**

> Progress mode suppresses default standalone tool-progress messages when a draft is active. If standalone messages still appear, verify that the turn is actually using progress mode and not `streaming.mode: "off"` or a channel path that cannot create a draft for that message.

草稿激活时，progress 模式抑制默认的独立工具进度消息。仍然出现独立消息时，确认该轮次确实用的是 progress 模式，不是 `streaming.mode: "off"`、也不是无法为该消息建草稿的通道路径。

> **Teams behaves differently from Discord or Telegram.**

**Teams 行为跟 Discord 或 Telegram 不一样。**

> Microsoft Teams uses a native stream in personal chats instead of the generic send-and-edit preview transport. Teams also treats `streaming.mode: "block"` as Teams block delivery because it does not have the same draft-preview block mode used by Discord and Telegram.

Microsoft Teams 在个人聊天里用原生流，不用通用的 send + edit 预览传输。Teams 还把 `streaming.mode: "block"` 当作 Teams block 投递，因为它没有 Discord 和 Telegram 那种草稿预览 block 模式。

---

> ## Related

## 相关

> * [Streaming and chunking](/concepts/streaming)
> * [Messages](/concepts/messages)
> * [Channel configuration](/gateway/config-channels)
> * [Discord](/channels/discord)
> * [Matrix](/channels/matrix)
> * [Microsoft Teams](/channels/msteams)
> * [Slack](/channels/slack)
> * [Telegram](/channels/telegram)

- [流式和分片](/concepts/streaming)
- [消息](/concepts/messages)
- [通道配置](/gateway/config-channels)
- [Discord](/channels/discord)
- [Matrix](/channels/matrix)
- [Microsoft Teams](/channels/msteams)
- [Slack](/channels/slack)
- [Telegram](/channels/telegram)
