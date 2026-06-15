# HTTP API / HTTP API

Base URL: `https://clawhub.ai` (default).

基础 URL:`https://clawhub.ai`(默认)。

All v1 paths are under `/api/v1/...`. Legacy `/api/...` and `/api/cli/...` remain for compatibility (see `DEPRECATIONS.md`). OpenAPI: `/api/v1/openapi.json`.

所有 v1 路径在 `/api/v1/...` 下。旧版 `/api/...` 和 `/api/cli/...` 保留用于兼容性(参见 `DEPRECATIONS.md`)。OpenAPI:`/api/v1/openapi.json`。

## Public catalog reuse / 公共目录复用

Third-party directories may use the public read endpoints to list or search ClawHub skills. Please cache results, honor `429`/`Retry-After`, link users back to the canonical ClawHub listing (`https://clawhub.ai/<owner>/<slug>`), and avoid implying ClawHub endorsement of the third-party site. Do not attempt to mirror hidden, private, or moderation-blocked content outside the public API surface.

第三方目录可以使用公共读端点列出或搜索 ClawHub 技能。请缓存结果、遵守 `429`/`Retry-After`、将用户链接回规范的 ClawHub 列表(`https://clawhub.ai/<owner>/<slug>`),并避免暗示 ClawHub 对第三方网站的认可。不要尝试在公共 API 表面之外镜像隐藏、私有或审核阻止的内容。

Web slug shortcuts resolve across registry families, but API clients should use the canonical URLs returned by read endpoints instead of reconstructing route precedence.

Web 短名称快捷方式跨注册表族解析,但 API 客户端应使用读端点返回的规范 URL,而非重建路由优先级。

## Rate limits / 速率限制

Enforcement model:

执行模型:

- **Anonymous requests**: enforced per IP.
  
  **匿名请求**:按 IP 执行。

- **Authenticated requests** (valid Bearer token): enforced per user bucket.
  
  **认证请求**(有效 Bearer token):按用户桶执行。

- If token is missing/invalid, behavior falls back to IP enforcement.
  
  如果 token 缺失/无效,行为回退到 IP 执行。

- Authenticated write endpoints should not return a bare `Unauthorized` when the server knows the reason. Missing tokens, invalid/revoked tokens, and deleted/banned/disabled accounts should each get actionable text so CLI clients can tell users what blocked them.
  
  认证写端点不应在服务器知道原因时返回裸 `Unauthorized`。缺失 token、无效/撤销 token、已删除/禁止/禁用账户都应获得可操作的文本,以便 CLI 客户端告诉用户什么阻止了他们。

**Limits / 限制:**

- Read: 3000/min per IP, 12000/min per key
  
  读取:每 IP 3000/分钟,每密钥 12000/分钟

- Write: 300/min per IP, 3000/min per key
  
  写入:每 IP 300/分钟,每密钥 3000/分钟

- Download: 1200/min per IP, 6000/min per key (download endpoints)
  
  下载:每 IP 1200/分钟,每密钥 6000/分钟(下载端点)

**Headers / 头:**

- Legacy compatibility: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`
  
  旧版兼容性:`X-RateLimit-Limit`、`X-RateLimit-Remaining`、`X-RateLimit-Reset`

- Standardized: `RateLimit-Limit`, `RateLimit-Remaining`, `RateLimit-Reset`
  
  标准化:`RateLimit-Limit`、`RateLimit-Remaining`、`RateLimit-Reset`

- On `429`: `Retry-After`
  
  在 `429` 上:`Retry-After`

**Header semantics / 头语义:**

- `X-RateLimit-Reset`: absolute Unix epoch seconds
  
  绝对 Unix 纪元秒

- `RateLimit-Reset`: seconds until reset (delay)
  
  直到重置的秒数(延迟)

- `Retry-After`: seconds to wait before retry (delay) on `429`
  
  在 `429` 上重试前等待的秒数(延迟)

**Example `429` response / 示例 `429` 响应:**

```
HTTP/2 429
content-type: text/plain; charset=utf-8
x-ratelimit-limit: 20
x-ratelimit-remaining: 0
x-ratelimit-reset: 1771404540
ratelimit-limit: 20
ratelimit-remaining: 0
ratelimit-reset: 34
retry-after: 34

Rate limit exceeded
```

**Client guidance / 客户端指导:**

- If `Retry-After` exists, wait that many seconds before retry.
  
  如果 `Retry-After` 存在,等待那么多秒再重试。

- Use jittered backoff to avoid synchronized retries.
  
  使用抖动退避避免同步重试。

- If `Retry-After` is missing, fallback to `RateLimit-Reset` (or compute from `X-RateLimit-Reset`).
  
  如果 `Retry-After` 缺失,回退到 `RateLimit-Reset`(或从 `X-RateLimit-Reset` 计算)。

**IP source / IP 源:**

- Uses `cf-connecting-ip` (Cloudflare) for client IP by default.
  
  默认使用 `cf-connecting-ip`(Cloudflare)作为客户端 IP。

- ClawHub uses trusted forwarding headers to identify client IPs at the edge.
  
  ClawHub 使用可信转接头在边缘识别客户端 IP。

- If no trusted client IP is available, anonymous download requests use an endpoint-scoped fallback bucket instead of one global `ip:unknown` bucket. Anonymous read/write requests still use the shared unknown bucket so missing-IP routing remains visible and conservative.
  
  如果没有可信客户端 IP 可用,匿名下载请求使用端点作用域的回退桶而非一个全局 `ip:unknown` 桶。匿名读/写请求仍使用共享的未知桶,以便缺失 IP 路由保持可见和保守。

## Error responses / 错误响应

Public v1 error responses are plain text with `content-type: text/plain; charset=utf-8`. This includes validation failures (400), missing public resources (404), auth and permission failures (401/403), rate limits (429), and blocked downloads. Clients should read the response body as a human-readable string. Unknown query parameters are ignored for compatibility, but recognized query parameters with invalid values return `400`.

公共 v1 错误响应是带 `content-type: text/plain; charset=utf-8` 的纯文本。这包括验证失败(400)、缺失公共资源(404)、认证和权限失败(401/403)、速率限制(429)和阻止的下载。客户端应将响应体读取为人类可读字符串。为兼容性忽略未知查询参数,但具有无效值的已识别查询参数返回 `400`。

## Public endpoints (no auth) / 公共端点(无认证)

Public read endpoints for searching and inspecting skills:

用于搜索和检查技能的公共读端点:

- `GET /api/v1/search` - search skills
  
  搜索技能

- `GET /api/v1/skills` - list skills
  
  列出技能

- `GET /api/v1/skills/{slug}` - get skill detail
  
  获取技能详情

- `GET /api/v1/skills/{slug}/versions` - list versions
  
  列出版本

- `GET /api/v1/skills/{slug}/scan` - get scan status
  
  获取扫描状态

- `GET /api/v1/plugins` - list plugins
  
  列出插件

- `GET /api/v1/plugins/{package}` - get plugin detail
  
  获取插件详情

See the [OpenAPI spec](https://clawhub.ai/api/v1/openapi.json) for full request/response schemas.

参见 [OpenAPI 规范](https://clawhub.ai/api/v1/openapi.json) 了解完整请求/响应 schema。

## Auth endpoints (Bearer token) / 认证端点(Bearer token)

All endpoints require:

所有端点需要:

```
Authorization: Bearer clh_...
```

**Key auth endpoints / 关键认证端点:**

- `GET /api/v1/whoami` - validates token and returns the user handle
  
  验证 token 并返回用户句柄

- `POST /api/v1/skills` - publishes a new skill version
  
  发布新技能版本

- `POST /api/v1/packages` - publishes a code-plugin or bundle-plugin release
  
  发布代码插件或 bundle-plugin 版本

- `DELETE /api/v1/skills/{slug}` - soft-delete a skill (owner, moderator, or admin)
  
  软删除技能(owner、审核者或管理员)

- `POST /api/v1/skills/{slug}/undelete` - restore a soft-deleted skill
  
  恢复软删除的技能

**Publishing patterns / 发布模式:**

Skill publishing accepts:
- Preferred: `multipart/form-data` with `payload` JSON + `files[]` blobs
  
  首选:带 `payload` JSON + `files[]` blob 的 `multipart/form-data`

- JSON body with `files` (storageId-based) is also accepted
  
  也接受带 `files`(基于 storageId)的 JSON 体

Plugin publishing requires:
- `multipart/form-data`
- Allowed form fields: `payload`, repeated `files` blobs, or one `clawpack` tarball reference
  
  允许的表单字段:`payload`、重复的 `files` blob 或一个 `clawpack` tarball 引用

- Direct multipart publish requests are capped at 18MB. ClawPack tarballs may use the upload-url flow up to the 120MB tarball cap.
  
  直接 multipart 发布请求限制为 18MB。ClawPack tarball 可使用 upload-url 流程达到 120MB tarball 上限。

**Owner-scoped publishing / Owner 作用域发布:**

- Optional payload field: `ownerHandle`. When present, the API resolves that publisher server-side and requires the actor to have publisher access.
  
  可选有效载荷字段:`ownerHandle`。存在时,API 在服务器端解析该发布者并要求行动者具有发布者访问权限。

- Optional payload field: `migrateOwner`. When `true` with `ownerHandle`, an existing skill may move to that owner if the actor is an admin/owner on both the current and target publishers.
  
  可选有效载荷字段:`migrateOwner`。当带 `ownerHandle` 为 `true` 时,如果行动者在当前和目标发布者上都是管理员/owner,现有技能可移动到该 owner。

## Legacy CLI endpoints (deprecated) / 旧版 CLI 端点(已弃用)

Legacy `/api/cli/...` endpoints remain for compatibility but are deprecated. See `DEPRECATIONS.md` for migration paths.

旧版 `/api/cli/...` 端点保留用于兼容性但已弃用。参见 `DEPRECATIONS.md` 了解迁移路径。

## 相关 / Related

- [CLI](/clawhub/cli) — CLI 命令参考
- [Auth](/clawhub/auth) — 认证和 token 管理
- [Publishing](/clawhub/publishing) — 发布流程
- [Troubleshooting](/clawhub/troubleshooting) — API 错误和速率限制故障排除
