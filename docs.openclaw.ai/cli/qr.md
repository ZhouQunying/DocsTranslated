# `openclaw qr`

## 架构精读

> 跳过不影响阅读翻译正文。

### QR 码配对——为什么用 QR 而非手动输入？

`openclaw qr` 生成 QR 码用于设备配对：

```
openclaw qr --channel whatsapp
```

手机扫描二维码即可完成配对，无需手动输入长配对码。

这跟 WhatsApp Web 的 QR 配对是一个思路——扫码比手动输入 30 位配对码方便得多（且不容易出错）。QR 码包含配对令牌和网关地址，手机扫码后自动完成连接。

### 二维码有效期——为什么会过期？

QR 码 60 秒后过期，需要重新生成。

这跟 Google Authenticator 的 TOTP 是一个思路——时间窗口限制防止 QR 码被拍照后长期使用。过期机制确保"扫码的人是当前在终端前的人"。

---

Generates QR codes for device pairing: `openclaw qr --channel whatsapp`. QR codes expire after 60 seconds (time-window security, like TOTP). Scanning is faster and less error-prone than manual pairing code entry.

生成 QR 码用于设备配对：`openclaw qr --channel whatsapp`。QR 码 60 秒后过期（时间窗口安全，类似 TOTP）。扫码比手动输入配对码更快且不易出错。
