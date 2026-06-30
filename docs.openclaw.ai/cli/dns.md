# `openclaw dns`

## 架构精读

> 跳过不影响阅读翻译正文。

### DNS 管理——为什么需要专门的命令？

`openclaw dns` 管理本地 DNS 解析（mDNS/Bonjour 服务发现）：

- **`dns browse`**：浏览局域网内的 OpenClaw 实例
- **`dns resolve <name>`**：解析实例名称到 IP 地址
- **`dns register`**：注册当前实例到局域网

这跟 `dns-sd -B` / `dns-sd -L` 是一个思路——mDNS 服务发现（浏览、解析、注册）。DNS 管理让"找到局域网内的其他网关"变得简单。

### mDNS vs 传统 DNS——为什么用 mDNS？

- **传统 DNS**：需要 DNS 服务器（企业网络）
- **mDNS**：无需服务器，设备直接广播（家庭/小型网络）

这跟 AirPrint vs 网络打印是一个思路——AirPrint 用 mDNS 自动发现打印机（无需配置），网络打印需要手动输入 IP。mDNS 适合"即插即用"场景。

---

Manages local DNS resolution (mDNS/Bonjour service discovery): `dns browse` (discover local instances), `dns resolve <name>` (name to IP), `dns register` (advertise current instance). mDNS requires no DNS server (peer-to-peer broadcast), ideal for home/small networks.

管理本地 DNS 解析（mDNS/Bonjour 服务发现）：`dns browse`（发现局域网实例）、`dns resolve <name>`（名称到 IP）、`dns register`（广播当前实例）。mDNS 无需 DNS 服务器（对等广播），适合家庭/小型网络。
