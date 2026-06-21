# Camera Capture

OpenClaw 支持 **camera capture** 用于 agent workflows: iOS/Android nodes 和 macOS app 通过 `node.invoke` 捕获 **photo** (`jpg`) 或 **short video clip** (`mp4`,可选音频)。所有 camera 访问都在 **用户控制的设置** 之后。

> **类比:浏览器的 MediaDevices API。** 浏览器里 `navigator.mediaDevices.getUserMedia()` 请求摄像头权限,返回 MediaStream。OpenClaw camera capture 类似: agent 请求 `camera.snap` 或 `camera.clip`,node 检查权限和 foreground 状态,返回 base64 编码的 media。区别: 浏览器是实时 stream,OpenClaw 是按需 snapshot/clip,且需要经过 Gateway 转发。
>
> **架构要点:** Camera capture 经 `node.invoke` 调用,支持 `camera.list`、`camera.snap`、`camera.clip`;iOS/Android 需要 runtime 权限 (CAMERA、RECORD_AUDIO),macOS 默认关闭需要用户启用;所有平台需要 node **foreground**,后台返回 `NODE_BACKGROUND_UNAVAILABLE`;photos 重新压缩以保持 base64 payload 低于 5 MB;video clips 限制 `<= 60s` 以避免过大的 node payloads;CLI helper (`openclaw nodes camera snap/clip`) 写入临时文件并打印保存路径。

## iOS Node

### 用户设置 (默认开启)

- iOS Settings tab → **Camera** → **Allow Camera** (`camera.enabled`)
  - 默认: **on** (缺失的 key 被视为启用)
  - 关闭时: `camera.*` commands 返回 `CAMERA_DISABLED`

### Commands (经 Gateway `node.invoke`)

- `camera.list`
  - Response payload:
    - `devices`: `{ id, name, position, deviceType }` 数组

- `camera.snap`
  - Params:
    - `facing`: `front|back` (默认: `front`)
    - `maxWidth`: number (可选;iOS node 默认 `1600`)
    - `quality`: `0..1` (可选;默认 `0.9`)
    - `format`: 当前 `jpg`
    - `delayMs`: number (可选;默认 `0`)
    - `deviceId`: string (可选;来自 `camera.list`)
  - Response payload:
    - `format: "jpg"`
    - `base64: "<...>"`
    - `width`、`height`
  - Payload guard: photos 重新压缩以保持 base64 payload 低于 5 MB

- `camera.clip`
  - Params:
    - `facing`: `front|back` (默认: `front`)
    - `durationMs`: number (默认 `3000`,clamp 到最大 `60000`)
    - `includeAudio`: boolean (默认 `true`)
    - `format`: 当前 `mp4`
    - `deviceId`: string (可选;来自 `camera.list`)
  - Response payload:
    - `format: "mp4"`
    - `base64: "<...>"`
    - `durationMs`
    - `hasAudio`

### Foreground 要求

与 `canvas.*` 类似,iOS node 只允许 `camera.*` commands 在 **foreground**。后台调用返回 `NODE_BACKGROUND_UNAVAILABLE`。

### CLI Helper

获取 media 文件的最简单方式是通过 CLI helper,它把解码的 media 写入临时文件并打印保存路径。

示例:

```bash
openclaw nodes camera snap --node <id>               # 默认: 两个 front + back (2 MEDIA 行)
openclaw nodes camera snap --node <id> --facing front
openclaw nodes camera clip --node <id> --duration 3000
openclaw nodes camera clip --node <id> --no-audio
```

注意:

- `nodes camera snap` 默认**两个**朝向,给 agent 两个视角
- 输出文件是临时的 (在 OS temp 目录),除非你构建自己的 wrapper

## Android Node

### Android 用户设置 (默认开启)

- Android Settings sheet → **Camera** → **Allow Camera** (`camera.enabled`)
  - 默认: **on** (缺失的 key 被视为启用)
  - 关闭时: `camera.*` commands 返回 `CAMERA_DISABLED`

### 权限

- Android 需要 runtime 权限:
  - `CAMERA` 用于 `camera.snap` 和 `camera.clip`
  - `RECORD_AUDIO` 用于 `camera.clip` `includeAudio=true` 时

如果权限缺失,app 会在可能时提示;如果被拒绝,`camera.*` 请求失败并返回 `*_PERMISSION_REQUIRED` 错误。

### Android Foreground 要求

与 `canvas.*` 类似,Android node 只允许 `camera.*` commands 在 **foreground**。后台调用返回 `NODE_BACKGROUND_UNAVAILABLE`。

### Android Commands (经 Gateway `node.invoke`)

- `camera.list`
  - Response payload:
    - `devices`: `{ id, name, position, deviceType }` 数组

### Payload Guard

Photos 重新压缩以保持 base64 payload 低于 5 MB。

## macOS App

### 用户设置 (默认关闭)

macOS companion app 暴露一个 checkbox:

- **Settings → General → Allow Camera** (`openclaw.cameraEnabled`)
  - 默认: **off**
  - 关闭时: camera 请求返回 "Camera disabled by user"

### CLI Helper (Node Invoke)

使用主 `openclaw` CLI 在 macOS node 上调用 camera commands。

示例:

```bash
openclaw nodes camera list --node <id>            # 列出 camera ids
openclaw nodes camera snap --node <id>            # 打印保存路径
openclaw nodes camera snap --node <id> --max-width 1280
openclaw nodes camera snap --node <id> --delay-ms 2000
openclaw nodes camera snap --node <id> --device-id <id>
openclaw nodes camera clip --node <id> --duration 10s          # 打印保存路径
openclaw nodes camera clip --node <id> --duration-ms 3000      # 打印保存路径 (legacy flag)
openclaw nodes camera clip --node <id> --device-id <id>
openclaw nodes camera clip --node <id> --no-audio
```

注意:

- `openclaw nodes camera snap` 默认 `maxWidth=1600`,除非覆盖
- macOS 上,`camera.snap` 在 warm-up/exposure settle 后等待 `delayMs` (默认 2000ms) 再捕获
- Photo payloads 重新压缩以保持 base64 低于 5 MB

## 安全 + 实际限制

- Camera 和麦克风访问触发通常的 OS 权限提示 (并在 Info.plist 中需要 usage strings)
- Video clips 被限制 (当前 `<= 60s`) 以避免过大的 node payloads (base64 overhead + message limits)

## macOS Screen Video (OS 级)

对于 *screen* video (不是 camera),使用 macOS companion:

```bash
openclaw nodes screen record --node <id> --duration 10s --fps 15   # 打印保存路径
```

注意:

- 需要 macOS **Screen Recording** 权限 (TCC)

## 相关

- [Image and media support](/nodes/images)
- [Media understanding](/nodes/media-understanding)
- [Location command](/nodes/location-command)
