# `openclaw proxy`

## 架构精读

> 跳过不影响阅读翻译正文。

### 代理管理——为什么需要专门的命令？

`openclaw proxy` 管理网络代理配置（出站 HTTP/HTTPS 代理）：

- **`proxy get`**：查看当前代理配置
- **`proxy set <url>`**：设置代理 URL
- **`proxy clear`**：清除代理配置
- **`proxy test`**：测试代理连通性

这跟 `git config http.proxy` 是一个思路——管理出站代理（企业网络需要通过代理访问外网）。

### 代理 vs VPN——为什么区分？

- **代理**：应用层（只代理 HTTP/HTTPS 流量）
- **VPN**：网络层（代理所有流量）

这跟 SOCKS 代理 vs OpenVPN 是一个思路——SOCKS 是应用层代理（只代理特定应用），OpenVPN 是网络层 VPN（代理所有流量）。代理适合"只有网关需要代理"，VPN 适合"所有应用都需要代理"。

---

Manages network proxy configuration (outbound HTTP/HTTPS proxy): `proxy get` (current config), `proxy set <url>`, `proxy clear`, `proxy test` (connectivity). Proxy is application-layer (HTTP/HTTPS only); VPN is network-layer (all traffic).

管理网络代理配置（出站 HTTP/HTTPS 代理）：`proxy get`（当前配置）、`proxy set <url>`、`proxy clear`、`proxy test`（连通性）。代理是应用层（仅 HTTP/HTTPS）；VPN 是网络层（所有流量）。
