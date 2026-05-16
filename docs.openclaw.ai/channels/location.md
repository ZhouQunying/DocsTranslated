# Channel location parsing

> OpenClaw normalizes shared locations from chat channels into:
>
> * terse coordinate text appended to the inbound body, and
> * structured fields in the auto-reply context payload. Channel-provided labels, addresses, and captions/comments are rendered into the prompt by the shared untrusted metadata JSON block, not inline in the user body.

OpenClaw 把聊天通道里分享过来的位置信息归一为两种形态：

- 一段简短的坐标文本，追加到接收消息的正文上；
- 自动回复上下文负载里的结构化字段。通道带过来的标签、地址、说明 / 备注会通过共用的"不受信元数据 JSON 块"渲染进提示词，不直接嵌在用户正文里。

> Currently supported:
>
> * **Telegram** (location pins + venues + live locations)
> * **WhatsApp** (locationMessage + liveLocationMessage)
> * **Matrix** (`m.location` with `geo_uri`)

当前支持：

- **Telegram**（位置图钉 + venue + 实时位置）
- **WhatsApp**（locationMessage + liveLocationMessage）
- **Matrix**（带 `geo_uri` 的 `m.location`）

---

> ## Text formatting

## 文本格式

> Locations are rendered as friendly lines without brackets:

位置渲染成简洁的一行，不带括号：

> * Pin:
>   * `📍 48.858844, 2.294351 ±12m`
> * Named place:
>   * `📍 48.858844, 2.294351 ±12m`
> * Live share:
>   * `🛰 Live location: 48.858844, 2.294351 ±12m`

- 图钉：
  - `📍 48.858844, 2.294351 ±12m`
- 命名地点：
  - `📍 48.858844, 2.294351 ±12m`
- 实时共享：
  - `🛰 Live location: 48.858844, 2.294351 ±12m`

> If the channel includes a label, address, or caption/comment, it is preserved in the context payload and appears in the prompt as fenced untrusted JSON:

通道带了标签、地址或说明 / 备注时，这些信息会保留在上下文负载里，以围栏内的不受信 JSON 形式出现在提示词里：

> ````text
> Location (untrusted metadata):
> ```json
> {
>   "latitude": 48.858844,
>   "longitude": 2.294351,
>   "name": "Eiffel Tower",
>   "address": "Champ de Mars, Paris",
>   "caption": "Meet here"
> }
> ```
> ````

````text
Location (untrusted metadata):
```json
{
  "latitude": 48.858844,
  "longitude": 2.294351,
  "name": "Eiffel Tower",
  "address": "Champ de Mars, Paris",
  "caption": "Meet here"
}
```
````

---

> ## Context fields

## 上下文字段

> When a location is present, these fields are added to `ctx`:
>
> * `LocationLat` (number)
> * `LocationLon` (number)
> * `LocationAccuracy` (number, meters; optional)
> * `LocationName` (string; optional)
> * `LocationAddress` (string; optional)
> * `LocationSource` (`pin | place | live`)
> * `LocationIsLive` (boolean)
> * `LocationCaption` (string; optional)

带位置的消息会在 `ctx` 里加上这些字段：

- `LocationLat`（number）
- `LocationLon`（number）
- `LocationAccuracy`（number，单位米，可选）
- `LocationName`（string，可选）
- `LocationAddress`（string，可选）
- `LocationSource`（`pin | place | live`）
- `LocationIsLive`（boolean）
- `LocationCaption`（string，可选）

> The prompt renderer treats `LocationName`, `LocationAddress`, and `LocationCaption` as untrusted metadata and serializes them through the same bounded JSON path used for other channel context.

提示词渲染器把 `LocationName`、`LocationAddress`、`LocationCaption` 当作不受信元数据，走和其他通道上下文一样的、有边界的 JSON 序列化路径。

---

> ## Channel notes

## 各通道说明

> * **Telegram**: venues map to `LocationName/LocationAddress`; live locations use `live_period`.
> * **WhatsApp**: `locationMessage.comment` and `liveLocationMessage.caption` populate `LocationCaption`.
> * **Matrix**: `geo_uri` is parsed as a pin location; altitude is ignored and `LocationIsLive` is always false.

- **Telegram**：venue 映射到 `LocationName` / `LocationAddress`；实时位置用 `live_period`。
- **WhatsApp**：`locationMessage.comment` 和 `liveLocationMessage.caption` 写入 `LocationCaption`。
- **Matrix**：`geo_uri` 解析为图钉位置；海拔忽略，`LocationIsLive` 恒为 false。

---

> ## Related

## 相关

> * [Location command (nodes)](/nodes/location-command)
> * [Camera capture](/nodes/camera)
> * [Media understanding](/nodes/media-understanding)

- [位置命令（节点）](/nodes/location-command)
- [相机捕获](/nodes/camera)
- [媒体理解](/nodes/media-understanding)
