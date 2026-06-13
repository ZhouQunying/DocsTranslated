# Google Meet 插件

## 架构精读

> 跳过不影响阅读翻译正文。

### 为什么要"显式 by design"？

Google Meet 插件的每一条设计决策都围绕一个核心：**不能让 agent 偷偷加入会议**。只接受显式 URL、不做自动同意播报、OAuth 只用于 API 创建而非替代 Chrome 加入路径。就像银行的"双重确认"——不是不信任 agent,而是不想让 agent 的误操作把用户拖进一个尴尬的会议场景。

三种模式（`agent`/`bidi`/`transcribe`）的分离也值得注意。这不是"一个模式三种配置",而是三条完全不同的数据流。`agent` 是 STT→agent→TTS 的完整管道（像翻译同传）,`bidi` 是实时语音模型直接回答（像直接对话）,`transcribe` 只听不说（像会议记录员）。每条路径的依赖、权限、失败面都不一样,混在一起就是灾难。

音频桥的设计也有讲究。`BlackHole 2ch` 是 macOS 虚拟音频设备,Chrome 以为它在和真实麦克风/扬声器通信,实际上音频流走的是 OpenClaw 控制的虚拟管道。就像给 Chrome 戴了一副"隐形耳机"——Chrome 不知道音频被截获和注入了。

---

OpenClaw 的 Google Meet 参与者支持——该插件设计上显式明确：

- 仅加入显式 `https://meet.google.com/...` URL。
- 可通过 Google Meet API 创建新 Meet 空间,然后加入返回的 URL。
- `agent` 是默认回话模式：实时转录监听,配置的 OpenClaw agent 回答,常规 OpenClaw TTS 在 Meet 中说话。
- `bidi` 仍可作为后备直接实时语音模型模式。
- Agent 用 `mode` 选择加入行为：`agent` 用于实时监听/回话,`bidi` 用于直接实时语音后备,`transcribe` 用于加入/控制浏览器但无回话桥。
- 认证从个人 Google OAuth 或已登录的 Chrome profile 开始。
- 无自动同意播报。
- 默认 Chrome 音频后端是 `BlackHole 2ch`。
- Chrome 可在本地或配对的节点宿主机运行。
- Twilio 接受拨入号码加可选 PIN 或 DTMF 序列；不能直接拨 Meet URL。
- CLI 命令是 `googlemeet`；`meet` 留给更广泛的 agent 电话会议工作流。

## 快速开始

安装本地音频依赖并配置实时转录提供商加常规 OpenClaw TTS。OpenAI 是默认转录提供商；Google Gemini 实时语音也可作为独立 `bidi` 语音后备使用,设置 `realtime.voiceProvider: "google"`：

```bash
brew install blackhole-2ch sox
export OPENAI_API_KEY=sk-...
# 仅 bidi 模式下 realtime.voiceProvider 为 "google" 时需要
export GEMINI_API_KEY=...
```

`blackhole-2ch` 安装 `BlackHole 2ch` 虚拟音频设备。Homebrew 的安装器需要重启后 macOS 才暴露该设备：

```bash
sudo reboot
```

重启后验证两部分：

```bash
system_profiler SPAudioDataType | grep -i BlackHole
command -v sox
```

启用插件：

```json5
{
  plugins: {
    entries: {
      "google-meet": {
        enabled: true,
        config: {},
      },
    },
  },
}
```

检查设置：

```bash
openclaw googlemeet setup
```

setup 输出面向 agent 可读且模式感知。报告 Chrome profile、节点绑定,以及实时 Chrome 加入时的 BlackHole/SoX 音频桥和延迟实时 intro 检查。仅观察加入时用 `--mode transcribe` 检查同一传输；该模式跳过实时音频前置条件,因为不通过桥监听或说话：

```bash
openclaw googlemeet setup --transport chrome-node --mode transcribe
```

配置了 Twilio 委派时,setup 还报告 `voice-call` 插件、Twilio 凭据和公共 webhook 暴露是否就绪。让 agent 加入前,将任何 `ok: false` 检查视为所检查传输和模式的阻断项。脚本或机器可读输出用 `openclaw googlemeet setup --json`。用 `--transport chrome`、`--transport chrome-node` 或 `--transport twilio` 在 agent 尝试前预检特定传输。

Twilio 场景下,默认传输为 Chrome 时始终显式预检：

```bash
openclaw googlemeet setup --transport twilio
```

这能在 agent 尝试拨号会议前捕获缺失的 `voice-call` 接线、Twilio 凭据或不可达的 webhook 暴露。

加入会议：

```bash
openclaw googlemeet join https://meet.google.com/abc-defg-hij
```

或让 agent 通过 `google_meet` 工具加入：

```json
{
  "action": "join",
  "url": "https://meet.google.com/abc-defg-hij",
  "transport": "chrome-node",
  "mode": "agent"
}
```

面向 agent 的 `google_meet` 工具在非 macOS 宿主机上仍可用,支持 artifact、calendar、setup、transcribe、Twilio 和 `chrome-node` 流程。本地 Chrome 回话操作在此被阻止,因为内置 Chrome 音频路径当前依赖 macOS `BlackHole 2ch`。Linux 上用 `mode: "transcribe"`、Twilio 拨入或 macOS `chrome-node` 宿主机参与 Chrome 回话。

创建新会议并加入：

```bash
openclaw googlemeet create --transport chrome-node --mode agent
```

API 创建房间时,想让房间的免敲门策略显式而非继承 Google 账号默认值,使用 Google Meet `SpaceConfig.accessType`：

```bash
openclaw googlemeet create --access-type OPEN --transport chrome-node --mode agent
```

`OPEN` 让持有 Meet URL 的任何人免敲门加入。`TRUSTED` 让宿主组织的受信用户、受邀外部用户和拨入用户免敲门加入。`RESTRICTED` 将免敲门入场限制为受邀者。这些设置仅适用于官方 Google Meet API 创建路径,所以需要配置 OAuth 凭据。

如果在该选项可用前已认证 Google Meet,添加 `meetings.space.settings` 权限范围到 Google OAuth 同意屏幕后重跑 `openclaw googlemeet auth login --json`。

仅创建 URL 不加入：

```bash
openclaw googlemeet create --no-join
```

`googlemeet create` 有两条路径：

- API 创建：配置了 Google Meet OAuth 凭据时使用。最确定性的路径,不依赖浏览器 UI 状态。
- 浏览器后备：无 OAuth 凭据时使用。OpenClaw 使用绑定的 Chrome 节点,打开 `https://meet.google.com/new`,等待 Google 重定向到真实会议代码 URL,然后返回该 URL。需要节点上的 OpenClaw Chrome profile 已登录 Google。浏览器自动化处理 Meet 自身的首次运行麦克风提示；该提示不被视为 Google 登录失败。加入和创建流程还会尝试复用已有 Meet 标签页再打开新的。匹配忽略无害 URL 查询字符串如 `authuser`,所以 agent 重试会聚焦已打开的会议而非创建第二个 Chrome 标签。

命令/工具输出包含 `source` 字段（`api` 或 `browser`）让 agent 解释使用了哪条路径。`create` 默认加入新会议并返回 `joined: true` 加入会话。仅生成 URL 时 CLI 用 `create --no-join` 或工具传 `"join": false`。

或告诉 agent："创建一个 Google Meet,用 agent 回话模式加入,把链接发给我。" Agent 应调用 `google_meet` 的 `action: "create"` 然后分享返回的 `meetingUri`。

```json
{
  "action": "create",
  "transport": "chrome-node",
  "mode": "agent"
}
```

仅观察/浏览器控制加入时设 `"mode": "transcribe"`。不启动双工实时语音桥,不需要 BlackHole 或 SoX,也不会在会议中回话。该模式的 Chrome 加入还避开 OpenClaw 的麦克风/摄像头权限授予和 Meet **使用麦克风**路径。Meet 显示音频选择过渡页时,自动化尝试无麦克风路径,否则报告手动操作而非打开本地麦克风。transcribe 模式下受管 Chrome 传输还安装尽力而为的 Meet 字幕观察器。`googlemeet status --json` 和 `googlemeet doctor` 暴露 `captioning`、`captionsEnabledAttempted`、`transcriptLines`、`lastCaptionAt`、`lastCaptionSpeaker`、`lastCaptionText` 和短 `recentTranscript` 尾部,让运维判断浏览器是否加入了通话且 Meet 字幕是否在产出文本。需要是/否探测时用 `openclaw googlemeet test-listen <meet-url> --transport chrome-node`：以 transcribe 模式加入,等待新字幕或转录变动,返回 `listenVerified`、`listenTimedOut`、手动操作字段和最新字幕健康状态。

实时会话期间,`google_meet` status 包含浏览器和音频桥健康状态,如 `inCall`、`manualActionRequired`、`providerConnected`、`realtimeReady`、`audioInputActive`、`audioOutputActive`、最后输入/输出时间戳、字节计数器和桥关闭状态。出现安全 Meet 页面提示时浏览器自动化尽可能处理。登录、宿主准入和浏览器/OS 权限提示报告为手动操作,附原因和消息供 agent 转达。受管 Chrome 会话仅在浏览器健康报告 `inCall: true` 后才发出 intro 或测试短语；否则 status 报告 `speechReady: false` 且说话尝试被阻止,而非假装 agent 已说话进会议。

本地 Chrome 通过已登录的 OpenClaw 浏览器 profile 加入。实时模式需要 `BlackHole 2ch` 作为 OpenClaw 使用的麦克风/扬声器路径。干净双工音频用独立虚拟设备或 Loopback 式路由图；单个 BlackHole 设备够做首次冒烟测试但可能回声。

### 本地 Gateway + Parallels Chrome

**不**需要在 macOS VM 内运行完整 OpenClaw Gateway 或模型 API key 来让 VM 持有 Chrome。在本地运行 Gateway 和 agent,然后在 VM 中运行节点宿主。在 VM 上一次性启用内置插件让节点广播 Chrome 命令：

运行位置分配：

- Gateway 宿主机：OpenClaw Gateway、agent 工作区、模型/API key、实时提供商和 Google Meet 插件配置。
- Parallels macOS VM：OpenClaw CLI/节点宿主、Google Chrome、SoX、BlackHole 2ch 和已登录 Google 的 Chrome profile。
- VM 内不需要：Gateway 服务、agent 配置、OpenAI/GPT key 或模型提供商设置。

安装 VM 依赖：

```bash
brew install blackhole-2ch sox
```

安装 BlackHole 后重启 VM 让 macOS 暴露 `BlackHole 2ch`：

```bash
sudo reboot
```

重启后验证 VM 能看到音频设备和 SoX 命令：

```bash
system_profiler SPAudioDataType | grep -i BlackHole
command -v sox
```

在 VM 中安装或更新 OpenClaw,然后启用内置插件：

```bash
openclaw plugins enable google-meet
```

在 VM 中启动节点宿主：

```bash
openclaw node run --host <gateway-host> --port 18789 --display-name parallels-macos
```

如果 `<gateway-host>` 是 LAN IP 且未使用 TLS,节点会拒绝明文 WebSocket,除非为该受信私有网络开启：

```bash
OPENCLAW_ALLOW_INSECURE_PRIVATE_WS=1 \
  openclaw node run --host <gateway-lan-ip> --port 18789 --display-name parallels-macos
```

将节点安装为 LaunchAgent 时用同一环境变量：

```bash
OPENCLAW_ALLOW_INSECURE_PRIVATE_WS=1 \
  openclaw node install --host <gateway-lan-ip> --port 18789 --display-name parallels-macos --force
openclaw node restart
```

`OPENCLAW_ALLOW_INSECURE_PRIVATE_WS=1` 是进程环境变量,不是 `openclaw.json` 设置。`openclaw node install` 在安装命令存在该变量时将其存入 LaunchAgent 环境。

从 Gateway 宿主机批准节点：

```bash
openclaw devices list
openclaw devices approve <requestId>
```

确认 Gateway 看到该节点且其广播 `googlemeet.chrome` 和 browser capability/`browser.proxy`：

```bash
openclaw nodes status
```

在 Gateway 宿主机上路由 Meet 到该节点：

```json5
{
  gateway: {
    nodes: {
      allowCommands: ["googlemeet.chrome", "browser.proxy"],
    },
  },
  plugins: {
    entries: {
      "google-meet": {
        enabled: true,
        config: {
          defaultTransport: "chrome-node",
          chrome: {
            guestName: "OpenClaw Agent",
            autoJoin: true,
            reuseExistingTab: true,
          },
          chromeNode: {
            node: "parallels-macos",
          },
        },
      },
    },
  },
}
```

然后从 Gateway 宿主机正常加入：

```bash
openclaw googlemeet join https://meet.google.com/abc-defg-hij
```

或让 agent 使用 `google_meet` 工具的 `transport: "chrome-node"`。

一条命令做冒烟测试——创建或复用会话、说已知短语、打印会话健康：

```bash
openclaw googlemeet test-speech https://meet.google.com/abc-defg-hij
```

实时加入期间 OpenClaw 浏览器自动化填写访客名、点击 Join/Ask to join 并接受 Meet 首次运行的"使用麦克风"选项。仅观察加入或仅浏览器创建会议时,该选项可用则无麦克风继续。浏览器 profile 未登录、Meet 等待宿主准入、Chrome 需要实时加入的麦克风/摄像头权限、或 Meet 卡在自动化无法解决的提示上时,join/test-speech 结果报告 `manualActionRequired: true` 附 `manualActionReason` 和 `manualActionMessage`。Agent 应停止重试加入、报告该确切消息加当前 `browserUrl`/`browserTitle`,仅在手动浏览器操作完成后重试。

`chromeNode.node` 省略时,OpenClaw 仅在恰好一个已连接节点同时广播 `googlemeet.chrome` 和 browser 控制时自动选择。多个能力节点已连接时,将 `chromeNode.node` 设为节点 id、显示名或远程 IP。

常见失败检查：

- `Configured Google Meet node ... is not usable: offline`：绑定节点 Gateway 已知但不可用。Agent 应将该节点视为诊断状态而非可用 Chrome 宿主机,报告设置阻断项而非回落其他传输,除非用户要求。
- `No connected Google Meet-capable node`：在 VM 中启动 `openclaw node run`、批准配对,并确保在 VM 中执行了 `openclaw plugins enable google-meet` 和 `openclaw plugins enable browser`。同时确认 Gateway 宿主机用 `gateway.nodes.allowCommands: ["googlemeet.chrome", "browser.proxy"]` 允许两个节点命令。
- `BlackHole 2ch audio device not found`：在被检查的宿主机上安装 `blackhole-2ch` 并重启后再用本地 Chrome 音频。
- `BlackHole 2ch audio device not found on the node`：在 VM 中安装 `blackhole-2ch` 并重启 VM。
- Chrome 打开但无法加入：在 VM 内登录浏览器 profile,或为访客加入保留 `chrome.guestName`。访客自动加入通过节点浏览器代理走 OpenClaw 浏览器自动化；确保节点浏览器配置指向想要的 profile,如 `browser.defaultProfile: "user"` 或命名的已有会话 profile。
- 重复 Meet 标签：保持 `chrome.reuseExistingTab: true` 启用。OpenClaw 在打开新标签前激活同一 Meet URL 的已有标签,浏览器会议创建在打开新标签前复用进行中的 `https://meet.google.com/new` 或 Google 账号提示标签。
- 无音频：在 Meet 中将麦克风/扬声器路由到 OpenClaw 使用的虚拟音频设备路径；用独立虚拟设备或 Loopback 式路由实现干净双工音频。

## 安装说明

Chrome 回话默认使用两个外部工具：

- `sox`：命令行音频工具。插件用显式 CoreAudio 设备命令驱动默认 24 kHz PCM16 音频桥。
- `blackhole-2ch`：macOS 虚拟音频驱动。创建 Chrome/Meet 可路由的 `BlackHole 2ch` 音频设备。

OpenClaw 不打包也不重新分发任一包。文档要求用户通过 Homebrew 将它们作为宿主机依赖安装。SoX 许可为 `LGPL-2.0-only AND GPL-2.0-only`；BlackHole 为 GPL-3.0。如果构建打包 BlackHole 和 OpenClaw 的安装器或设备,审查 BlackHole 的上游许可条款或从 Existential Audio 获取单独许可。

## 传输

### Chrome

Chrome 传输通过 OpenClaw 浏览器控制打开 Meet URL 并以已登录的 OpenClaw 浏览器 profile 加入。macOS 上插件在启动前检查 `BlackHole 2ch`。配置了的话还在打开 Chrome 前运行音频桥健康检查和启动命令。Chrome/音频在 Gateway 宿主机时用 `chrome`；Chrome/音频在配对节点（如 Parallels macOS VM）时用 `chrome-node`。本地 Chrome 用 `browser.defaultProfile` 选择 profile；`chrome.browserProfile` 传给 `chrome-node` 宿主机。

```bash
openclaw googlemeet join https://meet.google.com/abc-defg-hij --transport chrome
openclaw googlemeet join https://meet.google.com/abc-defg-hij --transport chrome-node
```

将 Chrome 麦克风和扬声器音频路由到本地 OpenClaw 音频桥。`BlackHole 2ch` 未安装时加入以设置错误失败,而非默默以无音频路径加入。

### Twilio

Twilio 传输是委派给 Voice Call 插件的严格拨号方案。不解析 Meet 页面获取电话号码。

Chrome 参与不可用或需要电话拨入后备时使用。Google Meet 必须暴露该会议的电话拨入号码和 PIN；OpenClaw 不从 Meet 页面发现这些。

在 Gateway 宿主机而非 Chrome 节点启用 Voice Call 插件：

```json5
{
  plugins: {
    allow: ["google-meet", "voice-call", "google"],
    entries: {
      "google-meet": {
        enabled: true,
        config: {
          defaultTransport: "chrome-node",
          // 或设 "twilio" 如果 Twilio 应为默认
        },
      },
      "voice-call": {
        enabled: true,
        config: {
          provider: "twilio",
          inboundPolicy: "allowlist",
          realtime: {
            enabled: true,
            provider: "google",
            instructions: "Join this Google Meet as an OpenClaw agent. Be brief.",
            toolPolicy: "safe-read-only",
            providers: {
              google: {
                silenceDurationMs: 500,
                startSensitivity: "high",
              },
            },
          },
        },
      },
      google: {
        enabled: true,
      },
    },
  },
}
```

通过环境或配置提供 Twilio 凭据。环境变量让密钥不进入 `openclaw.json`：

```bash
export TWILIO_ACCOUNT_SID=AC...
export TWILIO_AUTH_TOKEN=...
export TWILIO_FROM_NUMBER=+15550001234
export GEMINI_API_KEY=...
```

实时语音提供商为 OpenAI 时用 `realtime.provider: "openai"` 配 OpenAI 提供商插件和 `OPENAI_API_KEY`。

启用 `voice-call` 后重启或重载 Gateway；插件配置变更在已运行的 Gateway 进程重载前不生效。

然后验证：

```bash
openclaw config validate
openclaw plugins list | grep -E 'google-meet|voice-call'
openclaw googlemeet setup
```

Twilio 委派已接线时,`googlemeet setup` 包含成功的 `twilio-voice-call-plugin`、`twilio-voice-call-credentials` 和 `twilio-voice-call-webhook` 检查。

```bash
openclaw googlemeet join https://meet.google.com/abc-defg-hij \
  --transport twilio \
  --dial-in-number +15551234567 \
  --pin 123456
```

会议需要自定义序列时用 `--dtmf-sequence`：

```bash
openclaw googlemeet join https://meet.google.com/abc-defg-hij \
  --transport twilio \
  --dial-in-number +15551234567 \
  --dtmf-sequence ww123456#
```

## OAuth 和预检

OAuth 对创建 Meet 链接可选,因为 `googlemeet create` 可回落到浏览器自动化。需要官方 API 创建、空间解析或 Meet Media API 预检时配置 OAuth。

Google Meet API 访问使用用户 OAuth：创建 Google Cloud OAuth 客户端、请求所需权限范围、授权 Google 账号,然后将结果刷新令牌存入 Google Meet 插件配置或提供 `OPENCLAW_GOOGLE_MEET_*` 环境变量。

OAuth 不替代 Chrome 加入路径。Chrome 和 Chrome-node 传输仍通过已登录 Chrome profile、BlackHole/SoX 和使用浏览器参与时的已连接节点加入。OAuth 仅用于官方 Google Meet API 路径：创建会议空间、解析空间和运行 Meet Media API 预检。

### 创建 Google 凭据

在 Google Cloud Console：

1. 创建或选择 Google Cloud 项目。
2. 为该项目启用 **Google Meet REST API**。
3. 配置 OAuth 同意屏幕。
   - **内部** 对 Google Workspace 组织最简单。
   - **外部** 适用于个人/测试设置；app 处于测试阶段时,将每个要授权该 app 的 Google 账号添加为测试用户。
4. 添加 OpenClaw 请求的权限范围：
   - `https://www.googleapis.com/auth/meetings.space.created`
   - `https://www.googleapis.com/auth/meetings.space.readonly`
   - `https://www.googleapis.com/auth/meetings.space.settings`
   - `https://www.googleapis.com/auth/meetings.conference.media.readonly`
5. 创建 OAuth 客户端 ID。
   - 应用类型：**Web 应用**。
   - 授权重定向 URI：

     ```text
     http://localhost:8085/oauth2callback
     ```

6. 复制客户端 ID 和客户端密钥。

`meetings.space.created` 是 Google Meet `spaces.create` 所需。`meetings.space.readonly` 让 OpenClaw 将 Meet URL/代码解析为空间。`meetings.space.settings` 让 OpenClaw 在 API 房间创建时传递 `SpaceConfig` 设置如 `accessType`。`meetings.conference.media.readonly` 用于 Meet Media API 预检和媒体工作；Google 可能要求加入开发者预览才能使用实际 Media API。仅需要基于浏览器的 Chrome 加入时可完全跳过 OAuth。

### 生成刷新令牌

配置 `oauth.clientId` 和可选的 `oauth.clientSecret`,或作为环境变量传入,然后运行：

```bash
openclaw googlemeet auth login --json
```

命令打印带刷新令牌的 `oauth` 配置块。使用 PKCE、localhost 回调 `http://localhost:8085/oauth2callback` 和 `--manual` 手动复制/粘贴流程。

示例：

```bash
OPENCLAW_GOOGLE_MEET_CLIENT_ID="your-client-id" \
OPENCLAW_GOOGLE_MEET_CLIENT_SECRET="your-client-secret" \
openclaw googlemeet auth login --json
```

浏览器无法到达本地回调时用手动模式：

```bash
OPENCLAW_GOOGLE_MEET_CLIENT_ID="your-client-id" \
OPENCLAW_GOOGLE_MEET_CLIENT_SECRET="your-client-secret" \
openclaw googlemeet auth login --json --manual
```

JSON 输出包含：

```json
{
  "oauth": {
    "clientId": "your-client-id",
    "clientSecret": "your-client-secret",
    "refreshToken": "refresh-token",
    "accessToken": "access-token",
    "expiresAt": 1770000000000
  },
  "scope": "..."
}
```

将 `oauth` 对象存入 Google Meet 插件配置：

```json5
{
  plugins: {
    entries: {
      "google-meet": {
        enabled: true,
        config: {
          oauth: {
            clientId: "your-client-id",
            clientSecret: "your-client-secret",
            refreshToken: "refresh-token",
          },
        },
      },
    },
  },
}
```

不想刷新令牌出现在配置中时优先用环境变量。配置和环境值都存在时插件先解析配置再回落环境。

OAuth 同意包含 Meet 空间创建、Meet 空间读取访问和 Meet 会议媒体读取访问。如果在会议创建支持存在前已认证,重跑 `openclaw googlemeet auth login --json` 让刷新令牌持有 `meetings.space.created` 权限范围。

### 用 doctor 验证 OAuth

需要快速、非密钥健康检查时运行 OAuth doctor：

```bash
openclaw googlemeet doctor --oauth --json
```

不加载 Chrome 运行时也不需要已连接的 Chrome 节点。检查 OAuth 配置存在且刷新令牌能生成访问令牌。JSON 报告仅包含 `ok`、`configured`、`tokenSource`、`expiresAt` 和检查消息等状态字段；不打印访问令牌、刷新令牌或客户端密钥。

常见结果：

| 检查                 | 含义                                                        |
| -------------------- | ----------------------------------------------------------- |
| `oauth-config`       | `oauth.clientId` 加 `oauth.refreshToken` 或缓存访问令牌存在。 |
| `oauth-token`        | 缓存访问令牌仍有效,或刷新令牌生成了新访问令牌。             |
| `meet-spaces-get`    | 可选 `--meeting` 检查解析了已有 Meet 空间。                 |
| `meet-spaces-create` | 可选 `--create-space` 检查创建了新 Meet 空间。              |

同时证明 Google Meet API 启用和 `spaces.create` 权限范围时,运行有副作用的创建检查：

```bash
openclaw googlemeet doctor --oauth --create-space --json
openclaw googlemeet create --no-join --json
```

`--create-space` 创建一次性 Meet URL。需要确认 Google Cloud 项目已启用 Meet API 且授权账号持有 `meetings.space.created` 权限范围时使用。

证明已有会议空间的读取访问：

```bash
openclaw googlemeet doctor --oauth --meeting https://meet.google.com/abc-defg-hij --json
openclaw googlemeet resolve-space --meeting https://meet.google.com/abc-defg-hij
```

`doctor --oauth --meeting` 和 `resolve-space` 证明对已授权 Google 账号可访问的已有空间的读取访问。这些检查返回 `403` 通常意味着 Google Meet REST API 被禁用、同意的刷新令牌缺少所需权限范围、或 Google 账号无法访问该 Meet 空间。刷新令牌错误意味着重跑 `openclaw googlemeet auth login --json` 并保存新 `oauth` 块。

浏览器后备不需要 OAuth 凭据。该模式下 Google 认证来自所选节点上已登录的 Chrome profile,而非 OpenClaw 配置。

以下环境变量作为后备接受：

- `OPENCLAW_GOOGLE_MEET_CLIENT_ID` 或 `GOOGLE_MEET_CLIENT_ID`
- `OPENCLAW_GOOGLE_MEET_CLIENT_SECRET` 或 `GOOGLE_MEET_CLIENT_SECRET`
- `OPENCLAW_GOOGLE_MEET_REFRESH_TOKEN` 或 `GOOGLE_MEET_REFRESH_TOKEN`
- `OPENCLAW_GOOGLE_MEET_ACCESS_TOKEN` 或 `GOOGLE_MEET_ACCESS_TOKEN`
- `OPENCLAW_GOOGLE_MEET_ACCESS_TOKEN_EXPIRES_AT` 或 `GOOGLE_MEET_ACCESS_TOKEN_EXPIRES_AT`
- `OPENCLAW_GOOGLE_MEET_DEFAULT_MEETING` 或 `GOOGLE_MEET_DEFAULT_MEETING`
- `OPENCLAW_GOOGLE_MEET_PREVIEW_ACK` 或 `GOOGLE_MEET_PREVIEW_ACK`

通过 `spaces.get` 解析 Meet URL、代码或 `spaces/{id}`：

```bash
openclaw googlemeet resolve-space --meeting https://meet.google.com/abc-defg-hij
```

媒体工作前运行预检：

```bash
openclaw googlemeet preflight --meeting https://meet.google.com/abc-defg-hij
```

Meet 创建会议记录后列出会议 artifact 和参会情况：

```bash
openclaw googlemeet artifacts --meeting https://meet.google.com/abc-defg-hij
openclaw googlemeet attendance --meeting https://meet.google.com/abc-defg-hij
openclaw googlemeet export --meeting https://meet.google.com/abc-defg-hij --output ./meet-export
```

带 `--meeting` 时,`artifacts` 和 `attendance` 默认使用最新会议记录。需要该会议所有保留记录时传 `--all-conference-records`。

日历查找可在读取 Meet artifact 前从 Google Calendar 解析会议 URL：

```bash
openclaw googlemeet latest --today
openclaw googlemeet calendar-events --today --json
openclaw googlemeet artifacts --event "Weekly sync"
openclaw googlemeet attendance --today --format csv --output attendance.csv
```

`--today` 搜索今天 `primary` 日历中含 Google Meet 链接的日历事件。`--event <query>` 搜索匹配事件文本,`--calendar <id>` 用于非主日历。日历查找需要包含日历事件只读权限范围的新 OAuth 登录。`calendar-events` 预览匹配的 Meet 事件并标记 `latest`、`artifacts`、`attendance` 或 `export` 将选择的事件。

已知会议记录 id 时直接寻址：

```bash
openclaw googlemeet latest --meeting https://meet.google.com/abc-defg-hij
openclaw googlemeet artifacts --conference-record conferenceRecords/abc123 --json
openclaw googlemeet attendance --conference-record conferenceRecords/abc123 --json
```

通话结束后关闭 API 创建空间的活跃会议：

```bash
openclaw googlemeet end-active-conference https://meet.google.com/abc-defg-hij
```

调用 Google Meet `spaces.endActiveConference`,需要持有 `meetings.space.created` 权限范围的 OAuth,空间由授权账号管理。OpenClaw 接受 Meet URL、会议代码或 `spaces/{id}` 输入,在结束活跃会议前解析为 API 空间资源。与 `googlemeet leave` 不同：`leave` 停止 OpenClaw 的本地/会话参与,`end-active-conference` 让 Google Meet 结束该空间的活跃会议。

输出可读报告：

```bash
openclaw googlemeet artifacts --conference-record conferenceRecords/abc123 \
  --format markdown --output meet-artifacts.md
openclaw googlemeet attendance --conference-record conferenceRecords/abc123 \
  --format markdown --output meet-attendance.md
openclaw googlemeet attendance --conference-record conferenceRecords/abc123 \
  --format csv --output meet-attendance.csv
openclaw googlemeet export --conference-record conferenceRecords/abc123 \
  --include-doc-bodies --zip --output meet-export
openclaw googlemeet export --conference-record conferenceRecords/abc123 \
  --include-doc-bodies --dry-run
```

`artifacts` 返回会议记录元数据加参与者、录制、转录、结构化转录条目和智能笔记资源元数据（Google 为该会议暴露时）。大型会议用 `--no-transcript-entries` 跳过条目查找。`attendance` 将参与者展开为参与者会话行,含首次/末次看到时间、总会话时长、迟到/早退标记和按登录用户或显示名合并的重复参与者资源。`--no-merge-duplicates` 保留原始参与者资源分开,`--late-after-minutes` 调整迟到检测,`--early-before-minutes` 调整早退检测。

`export` 写入包含 `summary.md`、`attendance.csv`、`transcript.md`、`artifacts.json`、`attendance.json` 和 `manifest.json` 的文件夹。`manifest.json` 记录选择的输入、导出选项、会议记录、输出文件、计数、令牌源、使用时的日历事件和部分检索警告。`--zip` 在文件夹旁写入便携归档。`--include-doc-bodies` 通过 Google Drive `files.export` 导出关联的转录和智能笔记 Google Docs 文本；需要包含 Drive Meet 只读权限范围的新 OAuth 登录。无 `--include-doc-bodies` 时导出仅包含 Meet 元数据和结构化转录条目。Google 返回部分 artifact 失败（如智能笔记列表、转录条目或 Drive 文档正文错误）时,摘要和清单保留警告而非整个导出失败。`--dry-run` 获取相同 artifact/attendance 数据并打印清单 JSON 但不创建文件夹或 ZIP。在写入大型导出前或 agent 仅需计数、选定记录和警告时有用。

Agent 也可通过 `google_meet` 工具创建相同包：

```json
{
  "action": "export",
  "conferenceRecord": "conferenceRecords/abc123",
  "includeDocumentBodies": true,
  "outputDir": "meet-export",
  "zip": true
}
```

设 `"dryRun": true` 仅返回导出清单并跳过文件写入。

Agent 也可创建有显式访问策略的 API 房间：

```json
{
  "action": "create",
  "transport": "chrome-node",
  "mode": "agent",
  "accessType": "OPEN"
}
```

以及结束已知房间的活跃会议：

```json
{
  "action": "end_active_conference",
  "meeting": "https://meet.google.com/abc-defg-hij"
}
```

先听后验证时,agent 应在声明会议可用前用 `test_listen`：

```json
{
  "action": "test_listen",
  "url": "https://meet.google.com/abc-defg-hij",
  "transport": "chrome-node",
  "timeoutMs": 30000
}
```

对真实保留会议运行受保护的实时冒烟：

```bash
OPENCLAW_LIVE_TEST=1 \
OPENCLAW_GOOGLE_MEET_LIVE_MEETING=https://meet.google.com/abc-defg-hij \
pnpm test:live -- extensions/google-meet/google-meet.live.test.ts
```

对有人将说话且有 Meet 字幕可用的会议运行实时先听浏览器探测：

```bash
openclaw googlemeet setup --transport chrome-node --mode transcribe
openclaw googlemeet test-listen https://meet.google.com/abc-defg-hij --transport chrome-node --timeout-ms 30000
```

实时冒烟环境变量：

- `OPENCLAW_LIVE_TEST=1` 启用受保护的实时测试。
- `OPENCLAW_GOOGLE_MEET_LIVE_MEETING` 指向保留的 Meet URL、代码或 `spaces/{id}`。
- `OPENCLAW_GOOGLE_MEET_CLIENT_ID` 或 `GOOGLE_MEET_CLIENT_ID` 提供 OAuth 客户端 id。
- `OPENCLAW_GOOGLE_MEET_REFRESH_TOKEN` 或 `GOOGLE_MEET_REFRESH_TOKEN` 提供刷新令牌。
- 可选：`OPENCLAW_GOOGLE_MEET_CLIENT_SECRET`、`OPENCLAW_GOOGLE_MEET_ACCESS_TOKEN` 和 `OPENCLAW_GOOGLE_MEET_ACCESS_TOKEN_EXPIRES_AT` 使用去掉 `OPENCLAW_` 前缀的同名后备。

基础 artifact/attendance 实时冒烟需要 `https://www.googleapis.com/auth/meetings.space.readonly` 和 `https://www.googleapis.com/auth/meetings.conference.media.readonly`。日历查找需要 `https://www.googleapis.com/auth/calendar.events.readonly`。Drive 文档正文导出需要 `https://www.googleapis.com/auth/drive.meet.readonly`。

创建新 Meet 空间：

```bash
openclaw googlemeet create
```

命令打印新 `meeting uri`、源和加入会话。有 OAuth 凭据时用官方 Google Meet API。无 OAuth 凭据时用绑定 Chrome 节点的已登录浏览器 profile 作为后备。Agent 可用 `google_meet` 工具的 `action: "create"` 一步创建并加入。仅创建 URL 时传 `"join": false`。

浏览器后备的 JSON 输出示例：

```json
{
  "source": "browser",
  "meetingUri": "https://meet.google.com/abc-defg-hij",
  "joined": true,
  "browser": {
    "nodeId": "ba0f4e4bc...",
    "targetId": "tab-1"
  },
  "join": {
    "session": {
      "id": "meet_...",
      "url": "https://meet.google.com/abc-defg-hij"
    }
  }
}
```

浏览器后备在创建 URL 前遇到 Google 登录或 Meet 权限阻断时,Gateway 方法返回失败响应,`google_meet` 工具返回结构化详情而非纯字符串：

```json
{
  "source": "browser",
  "error": "google-login-required: Sign in to Google in the OpenClaw browser profile, then retry meeting creation.",
  "manualActionRequired": true,
  "manualActionReason": "google-login-required",
  "manualActionMessage": "Sign in to Google in the OpenClaw browser profile, then retry meeting creation.",
  "browser": {
    "nodeId": "ba0f4e4bc...",
    "targetId": "tab-1",
    "browserUrl": "https://accounts.google.com/signin",
    "browserTitle": "Sign in - Google Accounts"
  }
}
```

Agent 看到 `manualActionRequired: true` 时应报告 `manualActionMessage` 加浏览器节点/标签上下文,并在运维完成浏览器步骤前停止打开新 Meet 标签。

API 创建的 JSON 输出示例：

```json
{
  "source": "api",
  "meetingUri": "https://meet.google.com/abc-defg-hij",
  "joined": true,
  "space": {
    "name": "spaces/abc-defg-hij",
    "meetingCode": "abc-defg-hij",
    "meetingUri": "https://meet.google.com/abc-defg-hij"
  },
  "join": {
    "session": {
      "id": "meet_...",
      "url": "https://meet.google.com/abc-defg-hij"
    }
  }
}
```

创建 Meet 默认加入。Chrome 或 Chrome-node 传输仍需已登录 Google 的 Chrome profile 通过浏览器加入。Profile 已退出时 OpenClaw 报告 `manualActionRequired: true` 或浏览器后备错误并要求运维完成 Google 登录后重试。

确认 Cloud 项目、OAuth 主体和会议参与者已加入 Google Workspace 开发者预览计划的 Meet 媒体 API 后,才设 `preview.enrollmentAcknowledged: true`。

## 配置

常见 Chrome agent 路径仅需启用插件、BlackHole、SoX、实时转录提供商 key 和已配置的 OpenClaw TTS 提供商。OpenAI 是默认转录提供商；将 `realtime.voiceProvider` 设为 `"google"` 和 `realtime.model` 可将 Gemini 实时语音用于 `bidi` 模式,不影响默认 agent 模式转录提供商：

```bash
brew install blackhole-2ch sox
export OPENAI_API_KEY=sk-...
# 或
export GEMINI_API_KEY=...
```

在 `plugins.entries.google-meet.config` 下设置插件配置：

```json5
{
  plugins: {
    entries: {
      "google-meet": {
        enabled: true,
        config: {},
      },
    },
  },
}
```

默认值：

- `defaultTransport: "chrome"`
- `defaultMode: "agent"`（`"realtime"` 仅作为 `"agent"` 的遗留兼容别名接受；新工具调用应写 `"agent"`）
- `chromeNode.node`：可选节点 id/名称/IP,用于 `chrome-node`
- `chrome.audioBackend: "blackhole-2ch"`
- `chrome.guestName: "OpenClaw Agent"`：已退出 Meet 访客屏幕使用的名称
- `chrome.autoJoin: true`：尽力而为的访客名填写和 Join Now 点击,通过 `chrome-node` 上的 OpenClaw 浏览器自动化
- `chrome.reuseExistingTab: true`：激活已有 Meet 标签而非打开重复
- `chrome.waitForInCallMs: 20000`：等待 Meet 标签报告通话中再触发回话 intro
- `chrome.audioFormat: "pcm16-24khz"`：命令对音频格式。仅遗留/自定义命令对仍发出电话音频时用 `"g711-ulaw-8khz"`。
- `chrome.audioBufferBytes: 4096`：生成的 Chrome 命令对音频命令的 SoX 处理缓冲区。这是 SoX 默认 8192 字节缓冲区的一半,降低默认管道延迟同时留有空间在繁忙宿主机上提高。低于 SoX 最小值的值被钳制到 17 字节。
- `chrome.audioInputCommand`：从 CoreAudio `BlackHole 2ch` 读取并以 `chrome.audioFormat` 写入音频的 SoX 命令
- `chrome.audioOutputCommand`：以 `chrome.audioFormat` 读取音频并写入 CoreAudio `BlackHole 2ch` 的 SoX 命令
- `chrome.bargeInInputCommand`：可选本地麦克风命令,在助手播放活跃时写入有符号 16 位小端单声道 PCM 供人类打断检测。当前适用于 Gateway 承载的 `chrome` 命令对桥。
- `chrome.bargeInRmsThreshold: 650`：`chrome.bargeInInputCommand` 上算作人类打断的 RMS 级别
- `chrome.bargeInPeakThreshold: 2500`：`chrome.bargeInInputCommand` 上算作人类打断的峰值级别
- `chrome.bargeInCooldownMs: 900`：重复人类打断间的最小延迟
- `mode: "agent"`：默认回话模式。参与者语音由配置的实时转录提供商转录,发送到每会议子 agent 会话中配置的 OpenClaw agent,通过常规 OpenClaw TTS 运行时回话。
- `mode: "bidi"`：后备直接双向实时模型模式。实时语音提供商直接回答参与者语音,可调用 `openclaw_agent_consult` 获取更深/工具支持的回答。
- `mode: "transcribe"`：仅观察模式,无回话桥。
- `realtime.provider: "openai"`：下方作用域提供商字段未设置时使用的兼容后备。
- `realtime.transcriptionProvider: "openai"`：`agent` 模式用于实时转录的提供商 id。
- `realtime.voiceProvider`：`bidi` 模式用于直接实时语音的提供商 id。设为 `"google"` 使用 Gemini 实时语音同时保持 agent 模式转录在 OpenAI。
- `realtime.toolPolicy: "safe-read-only"`
- `realtime.instructions`：简短语音回复,用 `openclaw_agent_consult` 获取更深回答
- `realtime.introMessage`：实时桥连接时的简短语音就绪检查；设为 `""` 默默加入
- `realtime.agentId`：`openclaw_agent_consult` 的可选 OpenClaw agent id；默认 `main`

可选覆盖：

```json5
{
  defaults: {
    meeting: "https://meet.google.com/abc-defg-hij",
  },
  browser: {
    defaultProfile: "openclaw",
  },
  chrome: {
    guestName: "OpenClaw Agent",
    waitForInCallMs: 30000,
    bargeInInputCommand: [
      "sox",
      "-q",
      "-t",
      "coreaudio",
      "External Microphone",
      "-r",
      "24000",
      "-c",
      "1",
      "-b",
      "16",
      "-e",
      "signed-integer",
      "-t",
      "raw",
      "-",
    ],
  },
  chromeNode: {
    node: "parallels-macos",
  },
  defaultMode: "agent",
  realtime: {
    provider: "openai",
    transcriptionProvider: "openai",
    voiceProvider: "google",
    model: "gemini-2.5-flash-native-audio-preview-12-2025",
    agentId: "jay",
    toolPolicy: "owner",
    introMessage: "Say exactly: I'm here.",
    providers: {
      google: {
        speakerVoice: "Kore",
      },
    },
  },
}
```

ElevenLabs 同时用于 agent 模式监听和说话：

```json5
{
  messages: {
    tts: {
      provider: "elevenlabs",
      providers: {
        elevenlabs: {
          modelId: "eleven_v3",
          speakerVoiceId: "pMsXgVXv3BLzUgSXRplE",
        },
      },
    },
  },
  plugins: {
    entries: {
      "google-meet": {
        config: {
          realtime: {
            transcriptionProvider: "elevenlabs",
            providers: {
              elevenlabs: {
                modelId: "scribe_v2_realtime",
                audioFormat: "ulaw_8000",
                sampleRate: 8000,
                commitStrategy: "vad",
              },
            },
          },
        },
      },
    },
  },
}
```

持久 Meet 语音来自 `messages.tts.providers.elevenlabs.speakerVoiceId`。Agent 回复也可在 TTS 模型覆盖启用时用每回复 `[[tts:speakerVoiceId=... model=eleven_v3]]` 指令,但配置是会议的确定性默认。加入时日志应显示 `transcriptionProvider=elevenlabs`,每次语音回复应记录 `provider=elevenlabs model=eleven_v3 speakerVoiceId=<voiceId>`。

仅 Twilio 配置：

```json5
{
  defaultTransport: "twilio",
  twilio: {
    defaultDialInNumber: "+15551234567",
    defaultPin: "123456",
  },
  voiceCall: {
    gatewayUrl: "ws://127.0.0.1:18789",
  },
}
```

`voiceCall.enabled` 默认 `true`；Twilio 传输将实际 PSTN 通话、DTMF 和 intro 问候委派给 Voice Call 插件。Voice Call 在打开实时媒体流前播放 DTMF 序列,然后用保存的 intro 文本作为初始实时问候。`voice-call` 未启用时 Google Meet 仍可验证和记录拨号方案,但不能发起 Twilio 通话。

## 工具

Agent 可使用 `google_meet` 工具：

```json
{
  "action": "join",
  "url": "https://meet.google.com/abc-defg-hij",
  "transport": "chrome-node",
  "mode": "agent"
}
```

Chrome 在 Gateway 宿主机运行时用 `transport: "chrome"`。Chrome 在配对节点（如 Parallels VM）运行时用 `transport: "chrome-node"`。两种情况下模型提供商和 `openclaw_agent_consult` 都在 Gateway 宿主机运行,所以模型凭据留在那里。默认 `mode: "agent"` 下,实时转录提供商处理监听,配置的 OpenClaw agent 产出回答,常规 OpenClaw TTS 说进 Meet。想让实时语音模型直接回答时用 `mode: "bidi"`。原始 `mode: "realtime"` 仍作为 `mode: "agent"` 的遗留兼容别名接受,但不再在 agent 工具 schema 中公示。Agent 模式日志包含桥启动时解析的转录提供商/模型和每次合成回复后的 TTS 提供商、模型、语音、输出格式和采样率。

`action: "status"` 列出活跃会话或检查会话 ID。`action: "speak"` 带 `sessionId` 和 `message` 让实时 agent 立即说话。`action: "test_speech"` 创建或复用会话、触发已知短语,Chrome 宿主机可报告时返回 `inCall` 健康。`test_speech` 始终强制 `mode: "agent"` 并在要求以 `mode: "transcribe"` 运行时失败,因为仅观察会话有意不能发出语音。其 `speechOutputVerified` 结果基于该测试调用期间实时音频输出字节增加,所以复用会话的旧音频不算新鲜成功语音检查。`action: "leave"` 标记会话结束。

`status` 包含 Chrome 健康（可用时）：

- `inCall`：Chrome 似乎在 Meet 通话中
- `micMuted`：尽力而为的 Meet 麦克风状态
- `manualActionRequired` / `manualActionReason` / `manualActionMessage`：浏览器 profile 需要手动登录、Meet 宿主准入、权限或浏览器控制修复才能工作
- `speechReady` / `speechBlockedReason` / `speechBlockedMessage`：受管 Chrome 语音当前是否允许。`speechReady: false` 表示 OpenClaw 未将 intro/测试短语送入音频桥。
- `providerConnected` / `realtimeReady`：实时语音桥状态
- `lastInputAt` / `lastOutputAt`：桥最后一次看到音频输入或发送音频输出的时间
- `audioOutputRouted` / `audioOutputDeviceLabel`：Meet 标签的媒体输出是否活跃路由到桥使用的 BlackHole 设备
- `lastSuppressedInputAt` / `suppressedInputBytes`：助手播放活跃时被忽略的回环输入

```json
{
  "action": "speak",
  "sessionId": "meet_...",
  "message": "Say exactly: I'm here and listening."
}
```

## Agent 和 bidi 模式

Chrome `agent` 模式针对"我的 agent 在会议中"行为优化。实时转录提供商听到会议音频,最终参与者转录路由到配置的 OpenClaw agent,回答通过常规 OpenClaw TTS 运行时说出。想让实时语音模型直接回答时设 `mode: "bidi"`。相邻最终转录片段在 consult 前合并,这样一个说话轮次不会产生多个陈旧部分回答。实时输入还在排队的助手音频仍在播放时被抑制,最近的助手式转录回声在 agent consult 前被忽略,防止 BlackHole 回环让 agent 回答自己的话。

| 模式    | 谁决定回答              | 语音输出路径            | 适用场景                                |
| ------- | ----------------------- | ----------------------- | --------------------------------------- |
| `agent` | 配置的 OpenClaw agent   | 常规 OpenClaw TTS 运行时 | 想要"我的 agent 在会议中"行为           |
| `bidi`  | 实时语音模型            | 实时语音提供商音频响应   | 想要最低延迟的对话语音循环              |

`bidi` 模式下实时模型需要更深推理、实时信息或常规 OpenClaw 工具时,可调用 `openclaw_agent_consult`。

consult 工具在后台用近期会议转录上下文运行常规 OpenClaw agent 并返回简洁语音回答。`agent` 模式下 OpenClaw 将该回答直接发到 TTS 运行时；`bidi` 模式下实时语音模型可将 consult 结果说回会议。使用与 Voice Call 相同的共享 consult 机制。

默认 consult 对 `main` agent 运行。Meet 通道应 consult 专用 OpenClaw agent 工作区、模型默认值、工具策略、记忆和会话历史时设 `realtime.agentId`。

Agent 模式 consult 使用每会议 `agent:<id>:subagent:google-meet:<session>` 会话键,后续问题保持会议上下文同时继承配置 agent 的常规 agent 策略。

`realtime.toolPolicy` 控制 consult 运行：

- `safe-read-only`：暴露 consult 工具并将常规 agent 限制为 `read`、`web_search`、`web_fetch`、`x_search`、`memory_search` 和 `memory_get`。
- `owner`：暴露 consult 工具并让常规 agent 使用常规 agent 工具策略。
- `none`：不向实时语音模型暴露 consult 工具。

consult 会话键按 Meet 会话作用域,所以后续 consult 调用可在同一会议中复用先前 consult 上下文。

Chrome 完全加入通话后强制语音就绪检查：

```bash
openclaw googlemeet speak meet_... "Say exactly: I'm here and listening."
```

完整加入并说话冒烟：

```bash
openclaw googlemeet test-speech https://meet.google.com/abc-defg-hij \
  --transport chrome-node \
  --message "Say exactly: I'm here and listening."
```

## 实时测试检查清单

将会议交给无人值守 agent 前用此序列：

```bash
openclaw googlemeet setup
openclaw nodes status
openclaw googlemeet test-speech https://meet.google.com/abc-defg-hij \
  --transport chrome-node \
  --message "Say exactly: Google Meet speech test complete."
```

预期 Chrome-node 状态：

- `googlemeet setup` 全绿。
- `googlemeet setup` 包含 `chrome-node-connected`（Chrome-node 为默认传输或节点已绑定时）。
- `nodes status` 显示所选节点已连接。
- 所选节点广播 `googlemeet.chrome` 和 `browser.proxy`。
- Meet 标签加入通话且 `test-speech` 返回 `inCall: true` 的 Chrome 健康。

远程 Chrome 宿主机（如 Parallels macOS VM）场景下,更新 Gateway 或 VM 后的最短安全检查：

```bash
openclaw googlemeet setup
openclaw nodes status --connected
openclaw nodes invoke \
  --node parallels-macos \
  --command googlemeet.chrome \
  --params '{"action":"setup"}'
```

证明 Gateway 插件已加载、VM 节点用当前令牌已连接、Meet 音频桥可用,然后 agent 才打开真实会议标签。

Twilio 冒烟用暴露电话拨入详情的会议：

```bash
openclaw googlemeet setup
openclaw googlemeet join https://meet.google.com/abc-defg-hij \
  --transport twilio \
  --dial-in-number +15551234567 \
  --pin 123456
```

预期 Twilio 状态：

- `googlemeet setup` 包含绿色 `twilio-voice-call-plugin`、`twilio-voice-call-credentials` 和 `twilio-voice-call-webhook` 检查。
- Gateway 重载后 CLI 中可用 `voicecall`。
- 返回会话含 `transport: "twilio"` 和 `twilio.voiceCallId`。
- `openclaw logs --follow` 显示 DTMF TwiML 在实时 TwiML 前送达,然后实时桥排队初始问候。
- `googlemeet leave <sessionId>` 挂断委派语音通话。

## 故障排查

### Agent 看不到 Google Meet 工具

确认插件在 Gateway 配置中已启用并重载 Gateway：

```bash
openclaw plugins list | grep google-meet
openclaw googlemeet setup
```

刚编辑了 `plugins.entries.google-meet` 时重启或重载 Gateway。运行中的 agent 只看到当前 Gateway 进程注册的插件工具。

非 macOS Gateway 宿主机上面向 agent 的 `google_meet` 工具仍可见,但本地 Chrome 回话操作在到达音频桥前被阻止。本地 Chrome 回话音频当前依赖 macOS `BlackHole 2ch`,所以 Linux agent 应用 `mode: "transcribe"`、Twilio 拨入或 macOS `chrome-node` 宿主机替代默认本地 Chrome agent 路径。

### 无已连接的 Google Meet 能力节点

在节点宿主机运行：

```bash
openclaw plugins enable google-meet
openclaw plugins enable browser
OPENCLAW_ALLOW_INSECURE_PRIVATE_WS=1 \
  openclaw node run --host <gateway-lan-ip> --port 18789 --display-name parallels-macos
```

在 Gateway 宿主机批准节点并验证命令：

```bash
openclaw devices list
openclaw devices approve <requestId>
openclaw nodes status
```

节点必须已连接并列出 `googlemeet.chrome` 加 `browser.proxy`。Gateway 配置必须允许这些节点命令：

```json5
{
  gateway: {
    nodes: {
      allowCommands: ["browser.proxy", "googlemeet.chrome"],
    },
  },
}
```

`googlemeet setup` 失败 `chrome-node-connected` 或 Gateway 日志报告 `gateway token mismatch` 时用当前 Gateway 令牌重装或重启节点。LAN Gateway 场景通常意味着：

```bash
OPENCLAW_ALLOW_INSECURE_PRIVATE_WS=1 \
  openclaw node install \
  --host <gateway-lan-ip> \
  --port 18789 \
  --display-name parallels-macos \
  --force
```

然后重载节点服务并重跑：

```bash
openclaw googlemeet setup
openclaw nodes status --connected
```

### 浏览器打开但 agent 无法加入

仅观察加入跑 `googlemeet test-listen`,实时加入跑 `googlemeet test-speech`,然后检查返回的 Chrome 健康。任一探测报告 `manualActionRequired: true` 时向运维展示 `manualActionMessage` 并在浏览器操作完成前停止重试。

常见手动操作：

- 登录 Chrome profile。
- 从 Meet 宿主账号准入访客。
- Chrome 原生权限提示出现时授予 Chrome 麦克风/摄像头权限。
- 关闭或修复卡住的 Meet 权限对话框。

不要因为 Meet 显示"Do you want people to hear you in the meeting?"就报告"未登录"。那是 Meet 的音频选择过渡页；OpenClaw 在可用时通过浏览器自动化点击 **Use microphone** 并继续等待真实会议状态。仅创建的浏览器后备中 OpenClaw 可能点击 **Continue without microphone** 因为创建 URL 不需要实时音频路径。

### 会议创建失败

`googlemeet create` 配置了 OAuth 凭据时先用 Google Meet API `spaces.create` 端点。无 OAuth 凭据时回落到绑定 Chrome 节点浏览器。确认：

- API 创建：`oauth.clientId` 和 `oauth.refreshToken` 已配置,或匹配的 `OPENCLAW_GOOGLE_MEET_*` 环境变量存在。
- API 创建：刷新令牌在创建支持添加后生成。旧令牌可能缺少 `meetings.space.created` 权限范围；重跑 `openclaw googlemeet auth login --json` 并更新插件配置。
- 浏览器后备：`defaultTransport: "chrome-node"` 和 `chromeNode.node` 指向已连接且有 `browser.proxy` 和 `googlemeet.chrome` 的节点。
- 浏览器后备：该节点上的 OpenClaw Chrome profile 已登录 Google 且能打开 `https://meet.google.com/new`。
- 浏览器后备：重试在打开新标签前复用已有 `https://meet.google.com/new` 或 Google 账号提示标签。Agent 超时时重试工具调用而非手动打开另一个 Meet 标签。
- 浏览器后备：工具返回 `manualActionRequired: true` 时用返回的 `browser.nodeId`、`browser.targetId`、`browserUrl` 和 `manualActionMessage` 引导运维。在该操作完成前不要循环重试。
- 浏览器后备：Meet 显示"Do you want people to hear you in the meeting?"时保持标签打开。OpenClaw 应通过浏览器自动化点击 **Use microphone** 或仅创建后备时点击 **Continue without microphone** 并继续等待生成的 Meet URL。不能的话错误应提到 `meet-audio-choice-required` 而非 `google-login-required`。

### Agent 加入但不说话

检查实时路径：

```bash
openclaw googlemeet setup
openclaw googlemeet doctor
```

常规 STT -> OpenClaw agent -> TTS 回话路径用 `mode: "agent"`,直接实时语音后备用 `mode: "bidi"`。`mode: "transcribe"` 有意不启动回话桥。仅观察调试时,参与者说话后运行 `openclaw googlemeet status --json <session-id>` 并检查 `captioning`、`transcriptLines` 和 `lastCaptionText`。`inCall` 为 true 但 `transcriptLines` 停在 `0` 时,可能 Meet 字幕被禁用、自观察器安装后无人说话、Meet UI 变更、或该会议语言/账号不支持实时字幕。

`googlemeet test-speech` 始终检查实时路径并报告该调用期间是否观察到桥输出字节。`speechOutputVerified` 为 false 且 `speechOutputTimedOut` 为 true 时,实时提供商可能接受了话语但 OpenClaw 未看到新输出字节到达 Chrome 音频桥。

同时验证：

- Gateway 宿主机有实时提供商 key,如 `OPENAI_API_KEY` 或 `GEMINI_API_KEY`。
- Chrome 宿主机可见 `BlackHole 2ch`。
- Chrome 宿主机存在 `sox`。
- Meet 麦克风和扬声器路由到 OpenClaw 使用的虚拟音频路径。`doctor` 应对本地 Chrome 实时加入显示 `meet output routed: yes`。

`googlemeet doctor [session-id]` 打印会话、节点、通话中状态、手动操作原因、实时提供商连接和音频活跃度等信息。需要原始 JSON 时用 `googlemeet status [session-id] --json`。需要验证 Google Meet OAuth 刷新且不暴露令牌时用 `googlemeet doctor --oauth`；同时需要 Google Meet API 证明时加 `--meeting` 或 `--create-space`。

Agent 超时且可看到已有 Meet 标签打开时,检查该标签而不打开新的：

```bash
openclaw googlemeet recover-tab
openclaw googlemeet recover-tab https://meet.google.com/abc-defg-hij
```

等效工具动作是 `recover_current_tab`。聚焦并检查所选传输的已有 Meet 标签。`chrome` 用通过 Gateway 的本地浏览器控制；`chrome-node` 用配置的 Chrome 节点。不打开新标签也不创建新会话；报告当前阻断项,如登录、准入、权限或音频选择状态。CLI 命令与配置的 Gateway 通信,所以 Gateway 必须运行；`chrome-node` 还需 Chrome 节点已连接。

### Twilio 设置检查失败

`voice-call` 未被允许或未启用时 `twilio-voice-call-plugin` 失败。添加到 `plugins.allow`、启用 `plugins.entries.voice-call` 并重载 Gateway。

Twilio 后端缺少账号 SID、认证令牌或主叫号码时 `twilio-voice-call-credentials` 失败。在 Gateway 宿主机设置：

```bash
export TWILIO_ACCOUNT_SID=AC...
export TWILIO_AUTH_TOKEN=...
export TWILIO_FROM_NUMBER=+15550001234
```

`voice-call` 无公共 webhook 暴露或 `publicUrl` 指向回环或私有网络空间时 `twilio-voice-call-webhook` 失败。将 `plugins.entries.voice-call.config.publicUrl` 设为公共提供商 URL 或配置 `voice-call` 隧道/Tailscale 暴露。

回环和私有 URL 对运营商回调无效。不要用 `localhost`、`127.0.0.1`、`0.0.0.0`、`10.x`、`172.16.x`-`172.31.x`、`192.168.x`、`169.254.x`、`fc00::/7` 或 `fd00::/8` 作为 `publicUrl`。

稳定公共 URL：

```json5
{
  plugins: {
    entries: {
      "voice-call": {
        enabled: true,
        config: {
          provider: "twilio",
          fromNumber: "+15551234567",
          publicUrl: "https://voice.example.com/voice/webhook",
        },
      },
    },
  },
}
```

本地开发用隧道或 Tailscale 暴露替代私有宿主机 URL：

```json5
{
  plugins: {
    entries: {
      "voice-call": {
        config: {
          tunnel: { provider: "ngrok" },
          // 或
          tailscale: { mode: "funnel", path: "/voice/webhook" },
        },
      },
    },
  },
}
```

然后重启或重载 Gateway 并运行：

```bash
openclaw googlemeet setup --transport twilio
openclaw voicecall setup
openclaw voicecall smoke
```

`voicecall smoke` 默认仅就绪检查。干跑特定号码：

```bash
openclaw voicecall smoke --to "+15555550123"
```

仅在故意想发起真实出站通知通话时加 `--yes`：

```bash
openclaw voicecall smoke --to "+15555550123" --yes
```

### Twilio 通话开始但从未进入会议

确认 Meet 事件暴露电话拨入详情。传递精确拨入号码和 PIN 或自定义 DTMF 序列：

```bash
openclaw googlemeet join https://meet.google.com/abc-defg-hij \
  --transport twilio \
  --dial-in-number +15551234567 \
  --dtmf-sequence ww123456#
```

提供商需要在输入 PIN 前暂停时在 `--dtmf-sequence` 中用前导 `w` 或逗号。

电话通话已创建但 Meet 花名册从未显示拨入参与者：

- 运行 `openclaw googlemeet doctor <session-id>` 确认委派的 Twilio 通话 ID、DTMF 是否排队、intro 问候是否请求。
- 运行 `openclaw voicecall status --call-id <id>` 确认通话仍活跃。
- 运行 `openclaw voicecall tail` 检查 Twilio webhook 是否到达 Gateway。
- 运行 `openclaw logs --follow` 查找 Twilio Meet 序列：Google Meet 委派加入,Voice Call 存储并提供连接前 DTMF TwiML,Voice Call 为 Twilio 通话提供实时 TwiML,然后 Google Meet 用 `voicecall.speak` 请求 intro 语音。
- 重跑 `openclaw googlemeet setup --transport twilio`；绿色设置检查是必要条件但不证明会议 PIN 序列正确。
- 确认拨入号码与 PIN 属于同一 Meet 邀请和区域。
- Meet 应答慢或 pre-connect DTMF 已发送后通话转录仍显示要求输入 PIN 的提示时,将 `voiceCall.dtmfDelayMs` 从默认 12 秒增大。
- 参与者已加入但听不到问候时,检查 `openclaw logs --follow` 中 post-DTMF `voicecall.speak` 请求和媒体流 TTS 播放或 Twilio `Say` 后备。通话转录仍含"enter the meeting PIN"意味着电话腿尚未加入 Meet 房间,会议参与者不会听到语音。

Webhook 未到达时先调试 Voice Call 插件：提供商必须能到达 `plugins.entries.voice-call.config.publicUrl` 或配置的隧道。见 [Voice call troubleshooting](/plugins/voice-call#troubleshooting)。

## 说明

Google Meet 的官方媒体 API 以接收为导向,所以向 Meet 通话说话仍需参与者路径。该插件保持该边界可见：Chrome 处理浏览器参与和本地音频路由；Twilio 处理电话拨入参与。

Chrome 回话模式需要 `BlackHole 2ch` 加：

- `chrome.audioInputCommand` 加 `chrome.audioOutputCommand`：OpenClaw 持有桥并以 `chrome.audioFormat` 在这些命令和所选提供商之间管道传输音频。Agent 模式用实时转录加常规 TTS；bidi 模式用实时语音提供商。默认 Chrome 路径是 24 kHz PCM16,`chrome.audioBufferBytes: 4096`；8 kHz G.711 mu-law 仍可用于遗留命令对。
- `chrome.audioBridgeCommand`：外部桥命令持有整个本地音频路径,启动或验证其守护进程后必须退出。仅对 `bidi` 有效,因为 `agent` 模式需要直接命令对访问来驱动 TTS。

Agent 在 agent 模式调用 `google_meet` 工具时,会议 consult 会话在回答参与者语音前分叉调用者的当前转录。Meet 会话仍保持独立（`agent:<agentId>:subagent:google-meet:<sessionId>`）,会议后续不直接变更调用者转录。

干净双工音频将 Meet 输出和 Meet 麦克风路由到独立虚拟设备或 Loopback 式虚拟设备图。单个共享 BlackHole 设备可能将其他参与者的声音回传到通话中。

命令对 Chrome 桥下,`chrome.bargeInInputCommand` 可监听独立本地麦克风并在人类开始说话时清除助手播放。即使共享 BlackHole 回环输入在助手播放期间暂时被抑制,这仍保持人类语音先于助手输出。与 `chrome.audioInputCommand` 和 `chrome.audioOutputCommand` 一样是运维配置的本地命令。使用显式受信命令路径或参数列表,不要指向不受信位置的脚本。

`googlemeet speak` 触发 Chrome 会话的活跃回话音频桥。`googlemeet leave` 停止该桥。通过 Voice Call 插件委派的 Twilio 会话,`leave` 还挂断底层语音通话。同时想关闭 API 管理空间的活跃 Google Meet 会议时用 `googlemeet end-active-conference`。

## 相关

- [Voice call plugin](/plugins/voice-call)
- [Talk mode](/nodes/talk)
- [Building plugins](/plugins/building-plugins)
