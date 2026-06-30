# `openclaw browser`

## 架构精读

> 跳过不影响阅读翻译正文。

### 浏览器自动化——为什么需要专门的命令？

`openclaw browser` 管理浏览器自动化（CDP 连接、页面操作）：

- **`browser status`**：查看浏览器连接状态（CDP 端口、活跃页面）
- **`browser navigate <url>`**：导航到指定 URL
- **`browser screenshot`**：截取当前页面
- **`browser evaluate <js>`**：执行 JavaScript

这跟 Puppeteer 的 CLI 是一个思路——命令行控制浏览器，不需要写代码。适合"帮我打开这个网页并截图"的场景。

### CDP 连接——为什么用 Chrome DevTools Protocol？

浏览器自动化基于 CDP（Chrome DevTools Protocol），而非 Selenium：

- **CDP**：直接连接浏览器（低延迟、全功能）
- **Selenium**：通过 WebDriver（中间层、兼容性更好但延迟更高）

这跟直接 SQL vs ORM 是一个思路——直接连接（CDP/SQL）性能更好、功能更全，但需要特定浏览器（Chrome）；中间层（Selenium/ORM）兼容性更好但有开销。

---

Manages browser automation (CDP connection, page operations): `browser status` (CDP port, active pages), `browser navigate <url>`, `browser screenshot`, `browser evaluate <js>`. Uses Chrome DevTools Protocol (direct connection, low latency) rather than Selenium (WebDriver middle layer).

管理浏览器自动化（CDP 连接、页面操作）：`browser status`（CDP 端口、活跃页面）、`browser navigate <url>`、`browser screenshot`、`browser evaluate <js>`。使用 Chrome DevTools Protocol（直接连接、低延迟），而非 Selenium（WebDriver 中间层）。
