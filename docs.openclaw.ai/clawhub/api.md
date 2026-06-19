# API v1 / API v1

## 架构精读

> 跳过不影响阅读翻译正文。

### 认证感知的速率限制——匿名按 IP、认证按用户

ClawHub 的速率限制是**认证感知**的：

- **匿名请求**：按 IP 限制（3000 读/分钟、300 写/分钟、1200 下载/分钟）
- **认证请求**（有效 Bearer token）：按用户 bucket 限制（12000 读/分钟、3000 写/分钟、6000 下载/分钟）
- **缺失/无效 token**：回退到 IP 限制

这跟 GitHub API 的速率限制模型一样。匿名用户共享 IP 级别的限制——所有从同一 NAT/代理出来的用户共享一个 bucket。认证用户有自己的 bucket，不受同一网络其他用户的影响。

设计意图：鼓励认证。认证用户的限额是匿名用户的 4 倍（读）到 10 倍（写），且不受同一网络其他用户的影响。这让 CLI 和脚本工具（总是认证的）获得稳定性能，同时防止匿名滥用。

### 公共只读 API——为什么对第三方目录开放？

ClawHub 暴露公共只读 API（搜索、技能详情、下载）给第三方目录。条件是：链接回权威 ClawHub 列表、尊重速率限制、不暗示认可。

这跟 Docker Hub 的 API 开放性一样——Portainer、Rancher 等第三方工具可以用 Docker Hub API 展示镜像列表，但必须链接回 Docker Hub。设计意图是**生态放大**——第三方目录带来流量和用户，ClawHub 提供数据源。两者互利。

限制是必要的。不镜像隐藏/私有/管理阻止的内容——防止绕过安全过滤。不暗示认可——防止第三方目录的恶意内容被误认为 ClawHub 官方推荐。

### 429 响应的重试策略——三个 header 的优先级

速率限制触发时返回 429，带三个相关 header：
- `Retry-After`：等待秒数（延迟）
- `RateLimit-Reset`：延迟秒数直到重置
- `X-RateLimit-Reset`：Unix 时间戳（绝对重置时间）

优先级：`Retry-After` > `RateLimit-Reset` > `X-RateLimit-Reset`。这跟 HTTP 规范的建议一致——`Retry-After` 是最标准的重试信号。

客户端应添加 jitter（随机延迟）防止重试风暴——当多个客户端同时收到 429 时，如果都在 `Retry-After` 秒后精确重试，会再次同时触发 429。jitter 打散重试时间。

---

Base: https://clawhub.ai

Base:https://clawhub.ai

OpenAPI: /api/v1/openapi.json

OpenAPI:/api/v1/openapi.json

## 公共目录复用

You can build a third-party catalog, directory, or search surface on top of ClawHub's public read APIs. Public skill metadata and skill files are published under ClawHub's skill license rules, while the API itself is rate-limited and should be consumed responsibly.

你可以在 ClawHub 的公共只读 API 上构建第三方目录、列表或搜索界面。公共技能元数据和技能文件按 ClawHub 的技能许可规则发布，而 API 本身有速率限制，应负责任地消费。

Guidelines:

指南：

- Use public read endpoints such as `GET /api/v1/skills`, `GET /api/v1/search`, and `GET /api/v1/skills/{slug}` for catalog listings.
  
  使用公共只读端点如 `GET /api/v1/skills`、`GET /api/v1/search` 和 `GET /api/v1/skills/{slug}` 做目录列表。

- Cache responses and respect `429`, `Retry-After`, and rate-limit headers instead of polling aggressively.
  
  缓存响应并尊重 `429`、`Retry-After` 和速率限制 header，而非激进轮询。

- Link back to the canonical ClawHub skill URL when displaying listings so users can inspect the source registry record.
  
  展示列表时链接回权威 ClawHub 技能 URL，以便用户检查源注册表记录。

- Use canonical page URLs in the form `https://clawhub.ai/<owner>/<slug>`.
  
  使用 `https://clawhub.ai/<owner>/<slug>` 形式的权威页面 URL。

- Do not imply that ClawHub endorses, verifies, or operates the third-party site.
  
  不要暗示 ClawHub 认可、验证或运营第三方站点。

- Do not mirror hidden, private, or moderation-blocked content by bypassing public API filters or auth boundaries.
  
  不要通过绕过公共 API 过滤器或认证边界来镜像隐藏、私有或管理阻止的内容。

## Auth / 认证

- Public read: no token required.
  
  公共只读：不需要 token。

- Write + account: `Authorization: Bearer clh_...`.
  
  写入 + 账户：`Authorization: Bearer clh_...`。

## Rate limits / 速率限制

Auth-aware enforcement:

认证感知执行：

- Anonymous requests: per IP.
  
  匿名请求：按 IP。

- Authenticated requests (valid Bearer token): per user bucket.
  
  认证请求（有效 Bearer token）：按用户 bucket。

- Missing/invalid token falls back to IP enforcement.
  
  缺失/无效 token 回退到 IP 执行。

- Read: 3000/min per IP, 12000/min per key
  
  读：每 IP 3000/分钟，每 key 12000/分钟

- Write: 300/min per IP, 3000/min per key
  
  写：每 IP 300/分钟，每 key 3000/分钟

- Download: 1200/min per IP, 6000/min per key
  
  下载：每 IP 1200/分钟，每 key 6000/分钟

Headers: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`, `RateLimit-Limit`, `RateLimit-Remaining`, `RateLimit-Reset`, `Retry-After` (on 429).

Header：`X-RateLimit-Limit`、`X-RateLimit-Remaining`、`X-RateLimit-Reset`、`RateLimit-Limit`、`RateLimit-Remaining`、`RateLimit-Reset`、`Retry-After`（在 429 上）。

Semantics:

语义：

- `X-RateLimit-Reset`: Unix epoch seconds (absolute reset time)
  
  `X-RateLimit-Reset`：Unix 纪元秒数（绝对重置时间）

- `RateLimit-Reset`: delay seconds until reset
  
  `RateLimit-Reset`：延迟秒数直到重置

- `Retry-After`: delay seconds to wait on 429
  
  `Retry-After`：在 429 上等待的延迟秒数

Client handling:

客户端处理：

- Prefer `Retry-After` when present.
  
  存在时优先使用 `Retry-After`。

- Otherwise use `RateLimit-Reset` or derive delay from `X-RateLimit-Reset`.
  
  否则使用 `RateLimit-Reset` 或从 `X-RateLimit-Reset` 推导延迟。

- Add jitter to retries.
  
  给重试添加 jitter。

## Errors / 错误

- v1 errors are plain text (`text/plain; charset=utf-8`), including `400`, `401`, `403`, `404`, `429`, and blocked-download responses.
  
  v1 错误是纯文本（`text/plain; charset=utf-8`），包括 `400`、`401`、`403`、`404`、`429` 和被阻止下载响应。

- Unknown query parameters are ignored for compatibility.
  
  未知查询参数被忽略以保持兼容性。

- Known query parameters with invalid values return `400`.
  
  已知查询参数带无效值返回 `400`。

## Endpoints / 端点

Public read:

公共只读：

- `GET /api/v1/search?q=...`
- `GET /api/v1/skills?limit=&cursor=&sort=`
- `GET /api/v1/skills/{slug}`
- `GET /api/v1/skills/{slug}/moderation`
- `GET /api/v1/skills/{slug}/versions?limit=&cursor=`
- `GET /api/v1/skills/{slug}/versions/{version}`
- `GET /api/v1/skills/{slug}/scan?version=&tag=`
- `GET /api/v1/skills/{slug}/file?path=&version=&tag=`
- `GET /api/v1/resolve?slug=&hash=`
- `GET /api/v1/download?slug=&version=&tag=`
- `GET /api/v1/packages?limit=&cursor=&sort=`
- `GET /api/v1/plugins?limit=&cursor=&sort=`
- `GET /api/v1/plugins/search?q=...`
- `GET /api/v1/packages/{name}/versions/{version}/artifact`
- `GET /api/v1/packages/{name}/versions/{version}/security`
- `GET /api/v1/packages/{name}/versions/{version}/artifact/download`
- `GET /api/npm/{package}`
- `GET /api/npm/{package}/-/{tarball}.tgz`

Auth required:

需要认证：

- `POST /api/v1/skills` (publish, multipart preferred)
  
  `POST /api/v1/skills`（发布，推荐 multipart）
