# 消息展示

## 架构精读

> 跳过不影响阅读翻译正文。

### 为什么不直接用各平台的原生 UI 格式？

Discord 有 Components，Slack 有 Block Kit，Telegram 有 inline keyboards，Teams 有 Adaptive Cards——每个平台都有一套富消息格式。如果 agent 代码直接生成 Discord Components，换到 Slack 就得重写。消息展示（MessagePresentation）是语义层的 UI 描述——文本、上下文、分割线、按钮、选择菜单、卡片标题和色调。每个 channel 的渲染器负责映射到自己的原生格式。就像 CSS 媒体查询让同一内容适配不同屏幕尺寸——你描述想要什么，渲染器决定怎么呈现。好处是 agent 代码不用关心目标平台，坏处是表达能力受限于最弱平台的交集。

第二个关键：降级规则是渐进增强（progressive enhancement）。展示必须在有限 channel 上安全发送。不支持按钮的 channel 退化为文本标签，不支持选择的 channel 列出选项标签，URL 按钮退化为链接行。就像 Web 开发的核心原则——内容在 JavaScript 禁用时仍然可读。唯一的例外是 `delivery.pin.required: true`——如果置顶被要求为必需且 channel 无法置顶，交付报告失败。

第三个边界：Presentation 替换了旧的 InteractiveReply。InteractiveReply 是审批和交互辅助使用的旧内部子集，只支持文本、按钮和选择。Presentation 添加了标题、色调、上下文、分割线、纯 URL 按钮和通用交付元数据。旧代码可通过桥接辅助转换，新代码应直接接受或生成 Presentation。

---

消息展示是 OpenClaw 的共享富出站聊天 UI 契约。它让 agent、CLI 命令、审批流程和插件一次描述消息意图，每个 channel 插件渲染它能支持的最佳原生形态。

使用展示做可移植消息 UI：

- 文本段
- 小上下文/页脚文本
- 分割线
- 按钮
- 选择菜单
- 卡片标题和色调

不要向共享消息工具添加新的 provider 原生字段如 Discord `components`、Slack `blocks`、Telegram `buttons`、Teams `card` 或 Feishu `card`。那些是 channel 插件持有的渲染器输出。

## 契约

插件作者从以下路径导入公共契约：

```ts

  MessagePresentation,
  ReplyPayloadDelivery,
} from "openclaw/plugin-sdk/interactive-runtime";
```

形态：

```ts
type MessagePresentation = {
  title?: string;
  tone?: "neutral" | "info" | "success" | "warning" | "danger";
  blocks: MessagePresentationBlock[];
};

type MessagePresentationBlock =
  | { type: "text"; text: string }
  | { type: "context"; text: string }
  | { type: "divider" }
  | { type: "buttons"; buttons: MessagePresentationButton[] }
  | { type: "select"; placeholder?: string; options: MessagePresentationOption[] };

type MessagePresentationAction =
  | { type: "command"; command: string }
  | { type: "callback"; value: string };

type MessagePresentationButton = {
  label: string;
  action?: MessagePresentationAction;
  /** 遗留回调值。新控件优先使用 action。 */
  value?: string;
  url?: string;
  webApp?: { url: string };
  /** @deprecated 使用 webApp。仅为兼容旧 JSON 负载而接受。 */
  web_app?: { url: string };
  priority?: number;
  disabled?: boolean;
  reusable?: boolean;
  style?: "primary" | "secondary" | "success" | "danger";
};

type MessagePresentationOption = {
  label: string;
  action?: MessagePresentationAction;
  /** 遗留回调值。新控件优先使用 action。 */
  value?: string;
};

type ReplyPayloadDelivery = {
  pin?:
    | boolean
    | {
        enabled: boolean;
        notify?: boolean;
        required?: boolean;
      };
};
```

按钮语义：

- `action.type: "command"` 通过核心的命令路径运行原生命令。用于内置命令按钮和菜单。
- `action.type: "callback"` 通过 channel 的交互路径携带不透明插件数据。Channel 插件不得将回调数据重新解释为命令。
- `value` 是遗留的不透明回调值。新控件应使用 `action`，channel 插件可从文本映射命令和回调而无需猜测。
- `url` 是链接按钮。它可以独立于 `value` 存在。
- `webApp` 描述 channel 原生 web app 按钮。Telegram 将其渲染为 `web_app`，仅在私聊中支持。`web_app` 在松散 JSON 负载中仍被接受以保持兼容，但 TypeScript 生产者应使用 `webApp`。
- `label` 是必需的，也用于文本后备。
- `style` 是建议性的。渲染器应将不支持的样式映射到安全默认值，而非让发送失败。
- `priority` 是可选的。当 channel 声明操作限制且控件必须被丢弃时，核心保留高优先级按钮在前，并在等优先级按钮间保持原始顺序。所有控件都能放下时，保持编写顺序。
- `disabled` 是可选的。Channel 必须通过 `supportsDisabled` 加入；否则核心将禁用控件降级为非交互后备文本。
- `reusable` 是可选的。支持可复用原生回调的 channel 可在成功交互后保持操作可用。用于可重复或幂等操作如刷新、检查或更多详情；对普通一次性审批和破坏性操作保持未设置。

选择语义：

- `options[].action` 与按钮 `action` 有相同的命令/回调含义。
- `options[].value` 是遗留的已选择应用值。
- `placeholder` 是建议性的，没有原生选择支持的 channel 可能忽略它。
- 如果 channel 不支持选择，后备文本列出标签。

## 生产者示例

简单卡片：

```json
{
  "title": "Deploy approval",
  "tone": "warning",
  "blocks": [
    { "type": "text", "text": "Canary is ready to promote." },
    { "type": "context", "text": "Build 1234, staging passed." },
    {
      "type": "buttons",
      "buttons": [
        { "label": "Approve", "value": "deploy:approve", "style": "success" },
        { "label": "Decline", "value": "deploy:decline", "style": "danger" }
      ]
    }
  ]
}
```

纯 URL 链接按钮：

```json
{
  "blocks": [
    { "type": "text", "text": "Release notes are ready." },
    {
      "type": "buttons",
      "buttons": [{ "label": "Open notes", "url": "https://example.com/release" }]
    }
  ]
}
```

Telegram Mini App 按钮：

```json
{
  "blocks": [
    {
      "type": "buttons",
      "buttons": [{ "label": "Launch", "web_app": { "url": "https://example.com/app" } }]
    }
  ]
}
```

选择菜单：

```json
{
  "title": "Choose environment",
  "blocks": [
    {
      "type": "select",
      "placeholder": "Environment",
      "options": [
        { "label": "Canary", "value": "env:canary" },
        { "label": "Production", "value": "env:prod" }
      ]
    }
  ]
}
```

CLI 发送：

```bash
openclaw message send --channel slack \
  --target channel:C123 \
  --message "Deploy approval" \
  --presentation '{"title":"Deploy approval","tone":"warning","blocks":[{"type":"text","text":"Canary is ready."},{"type":"buttons","buttons":[{"label":"Approve","value":"deploy:approve","style":"success"},{"label":"Decline","value":"deploy:decline","style":"danger"}]}]}'
```

置顶交付：

```bash
openclaw message send --channel telegram \
  --target -1001234567890 \
  --message "Topic opened" \
  --pin
```

显式 JSON 置顶交付：

```json
{
  "pin": {
    "enabled": true,
    "notify": true,
    "required": false
  }
}
```

## 渲染器契约

Channel 插件在其出站适配器上声明渲染支持：

```ts
const adapter: ChannelOutboundAdapter = {
  deliveryMode: "direct",
  presentationCapabilities: {
    supported: true,
    buttons: true,
    selects: true,
    context: true,
    divider: true,
    limits: {
      actions: {
        maxActions: 25,
        maxActionsPerRow: 5,
        maxRows: 5,
        maxLabelLength: 80,
        maxValueBytes: 100,
        supportsStyles: true,
        supportsDisabled: false,
      },
      selects: {
        maxOptions: 25,
        maxLabelLength: 100,
        maxValueBytes: 100,
      },
      text: {
        maxLength: 2000,
        encoding: "characters",
        markdownDialect: "discord-markdown",
      },
    },
  },
  deliveryCapabilities: {
    pin: true,
  },
  renderPresentation({ payload, presentation, ctx }) {
    return renderNativePayload(payload, presentation, ctx);
  },
  async pinDeliveredMessage({ target, messageId, pin }) {
    await pinNativeMessage(target, messageId, { notify: pin.notify === true });
  },
};
```

能力布尔值描述渲染器能让什么变成交互的。可选 `limits` 描述核心在调用渲染器前可适配的通用信封：

```ts
type ChannelPresentationCapabilities = {
  supported?: boolean;
  buttons?: boolean;
  selects?: boolean;
  context?: boolean;
  divider?: boolean;
  limits?: {
    actions?: {
      maxActions?: number;
      maxActionsPerRow?: number;
      maxRows?: number;
      maxLabelLength?: number;
      maxValueBytes?: number;
      supportsStyles?: boolean;
      supportsDisabled?: boolean;
      supportsLayoutHints?: boolean;
    };
    selects?: {
      maxOptions?: number;
      maxLabelLength?: number;
      maxValueBytes?: number;
    };
    text?: {
      maxLength?: number;
      encoding?: "characters" | "utf8-bytes" | "utf16-units";
      markdownDialect?: "plain" | "markdown" | "html" | "slack-mrkdwn" | "discord-markdown";
      supportsEdit?: boolean;
    };
  };
};
```

核心在渲染前对语义控件应用通用限制。渲染器仍持有最终的 provider 特定验证和裁剪——原生块数、卡片大小、URL 限制和无法在通用契约中表达的 provider 特性。如果限制从块中移除了每个控件，核心将标签保留为非交互上下文文本，交付的消息仍有可见后备。

## 核心渲染流程

当 `ReplyPayload` 或消息操作包含 `presentation` 时，核心：

1. 归一化展示负载。
2. 解析目标 channel 的出站适配器。
3. 读取 `presentationCapabilities`。
4. 当适配器声明时应用通用能力限制如操作数、标签长度和选择选项数。
5. 当适配器能渲染负载时调用 `renderPresentation`。
6. 当适配器缺失或无法渲染时回退到保守文本。
7. 通过普通 channel 交付路径发送结果负载。
8. 在首次成功发送消息后应用交付元数据如 `delivery.pin`。

核心持有后备行为，生产者可保持 channel 无关。Channel 插件持有原生渲染和交互处理。

## 降级规则

展示必须在有限 channel 上安全发送。

后备文本包括：

- `title` 作为第一行
- `text` 块作为普通段落
- `context` 块作为紧凑上下文行
- `divider` 块作为视觉分隔符
- 按钮标签，包括链接按钮的 URL
- 选择选项标签

不支持的原生控件应降级而非让整个发送失败。示例：

- Telegram 禁用内联按钮时发送文本后备。
- 没有选择支持的 channel 将选择选项列为文本。
- 纯 URL 按钮变为原生命令按钮或后备 URL 行。
- 可选置顶失败不会让已交付消息失败。

主要例外是 `delivery.pin.required: true`；如果置顶被要求为必需且 channel 无法置顶已发送消息，交付报告失败。

## Provider 映射

当前捆绑渲染器：

| Channel | 原生渲染目标 | 备注 |
| --- | --- | --- |
| Discord | Components 和组件容器 | 为现有 provider 原生负载生产者保留遗留 `channelData.discord.components`，但新共享发送应使用 `presentation`。 |
| Slack | Block Kit | 为现有 provider 原生负载生产者保留遗留 `channelData.slack.blocks`，但新共享发送应使用 `presentation`。 |
| Telegram | 文本加内联键盘 | 按钮/选择需要目标表面的内联按钮能力；否则使用文本后备。 |
| Mattermost | 文本加交互属性 | 其他块降级为文本。 |
| Microsoft Teams | Adaptive Cards | 同时提供时，纯 `message` 文本包含在卡片中。 |
| Feishu | 交互卡片 | 卡片头部可使用 `title`；正文避免重复该标题。 |
| 纯 channel | 文本后备 | 没有渲染器的 channel 仍获得可读输出。 |

Provider 原生负载兼容是现有回复生产者的过渡辅助。它不是添加新共享原生字段的理由。

## Presentation 与 InteractiveReply

`InteractiveReply` 是审批和交互辅助使用的旧内部子集。它支持：

- 文本
- 按钮
- 选择

`MessagePresentation` 是标准共享发送契约。它添加：

- 标题
- 色调
- 上下文
- 分割线
- 纯 URL 按钮
- 通过 `ReplyPayload.delivery` 的通用交付元数据

桥接旧代码时使用 `openclaw/plugin-sdk/interactive-runtime` 的辅助：

```ts

  adaptMessagePresentationForChannel,
  applyPresentationActionLimits,
  interactiveReplyToPresentation,
  normalizeMessagePresentation,
  presentationPageSize,
  presentationToInteractiveControlsReply,
  presentationToInteractiveReply,
  renderMessagePresentationFallbackText,
} from "openclaw/plugin-sdk/interactive-runtime";
```

新代码应直接接受或生成 `MessagePresentation`。现有 `interactive` 负载是 `presentation` 的已弃用子集；运行时支持仍为旧生产者保留。

遗留 `InteractiveReply*` 类型和转换辅助在 SDK 中标记为 `@deprecated`：

- `InteractiveReply`、`InteractiveReplyBlock`、`InteractiveReplyButton`、`InteractiveReplyOption`、`InteractiveReplySelectBlock` 和 `InteractiveReplyTextBlock`
- `normalizeInteractiveReply(...)`
- `hasInteractiveReplyBlocks(...)`
- `interactiveReplyToPresentation(...)`
- `presentationToInteractiveReply(...)`
- `presentationToInteractiveControlsReply(...)`
- `resolveInteractiveTextFallback(...)`
- `reduceInteractiveReply(...)`

`presentationToInteractiveReply(...)` 和 `presentationToInteractiveControlsReply(...)` 仍可作为遗留 channel 实现的渲染器桥接。新生产者代码不应调用它们；发送 `presentation` 并让核心/channel 适配处理渲染。

审批辅助也有展示优先的替代品：

- 使用 `buildApprovalPresentationFromActionDescriptors(...)` 代替 `buildApprovalInteractiveReplyFromActionDescriptors(...)`
- 使用 `buildApprovalPresentation(...)` 代替 `buildApprovalInteractiveReply(...)`
- 使用 `buildExecApprovalPresentation(...)` 代替 `buildExecApprovalInteractiveReply(...)`

`renderMessagePresentationFallbackText(...)` 对没有文本后备的展示块返回空字符串，如纯分割线展示。需要非空发送体的传输可传递 `emptyFallback` 以加入最小正文，不改变默认后备契约。

## 交付置顶

置顶是交付行为，不是展示。使用 `delivery.pin` 而非 provider 原生字段如 `channelData.telegram.pin`。

语义：

- `pin: true` 置顶首次成功交付的消息。
- `pin.notify` 默认 `false`。
- `pin.required` 默认 `false`。
- 可选置顶失败降级并保持已发送消息完好。
- 必需置顶失败导致交付失败。
- 分块消息置顶首次交付的块，不是尾部块。

手动 `pin`、`unpin` 和 `pins` 消息操作仍存在，用于 provider 支持这些操作的现有消息。

## 插件作者检查清单

- 当 channel 能渲染或安全降级语义展示时从 `describeMessageTool(...)` 声明 `presentation`。
- 向运行时出站适配器添加 `presentationCapabilities`。
- 在运行时代码中实现 `renderPresentation`，不是控制面插件设置代码。
- 将原生 UI 库远离热设置/目录路径。
- 已知时在 `presentationCapabilities.limits` 上声明通用能力限制。
- 在渲染器和测试中保留最终平台限制。
- 为不支持的按钮、选择、URL 按钮、标题/文本重复和混合 `message` 加 `presentation` 发送添加后备测试。
- 仅当 provider 能置顶已发送消息 id 时通过 `deliveryCapabilities.pin` 和 `pinDeliveredMessage` 添加交付置顶支持。
- 不要通过共享消息操作 schema 暴露新的 provider 原生卡片/块/组件/按钮字段。

## 相关文档

- [Message CLI](/cli/message)
- [Plugin SDK Overview](/plugins/sdk-overview)
- [Plugin Architecture](/plugins/architecture-internals#message-tool-schemas)
- [Channel Presentation Refactor Plan](/plan/ui-channels)
