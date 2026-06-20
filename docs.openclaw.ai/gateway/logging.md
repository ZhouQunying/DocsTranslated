# Gateway logging

## 架构精读

> 跳过不影响阅读翻译正文。

### 两个日志 surface

**问题**: 本地开发直接看终端,生产环境远程查看不方便?

**方案**: 两个日志 surface:
- **CLI 日志**: 终端输出,纯文本,适合本地开发
- **Control UI 日志**: web 界面,结构化 JSON,适合远程查看

**洞察**: 覆盖 CLI 用户和 GUI 用户。

**权衡**:
- ✓ 灵活: 不同场景用不同方式
- ✓ 方便: 不需要 SSH 到服务器

**模式**: Docker logs 命令 vs Docker Desktop GUI——CLI 用户用命令,GUI 用户用界面。

### 启动日志

**问题**: 用户需要确认"Gateway 用的是哪个模型、监听哪个端口"?

**方案**: 启动时输出关键配置:
```
[INFO] Default agent model: anthropic/claude-opus-4-6
[INFO] Session mode: persistent
[INFO] Workspace: ~/.openclaw/workspace
[INFO] Listening on: 0.0.0.0:1455
```

**洞察**: 确认配置、诊断问题、审计。

**权衡**:
- ✓ 透明: 用户知道 Gateway 的配置
- ✓ 诊断: 配置错了立刻显示

**模式**: nginx 启动日志——输出"listening on port 80"、"worker processes: 4"。

### 日志级别

**问题**: 不同场景需要不同详细程度 (生产只看 ERROR、开发看 INFO、调试看 DEBUG)?

**方案**: 四个级别:
- **INFO**: 正常操作 (如"session created")
- **WARN**: 警告,不影响功能 (如"API key 快过期了")
- **ERROR**: 错误,影响功能 (如"auth failed")
- **DEBUG**: 调试信息 (如"request payload: {...}")

**洞察**: 按级别过滤,控制详细程度。

**权衡**:
- ✓ 灵活: 按需过滤
- ✓ 清晰: 不同级别不同含义

**模式**: log4j 日志级别——TRACE、DEBUG、INFO、WARN、ERROR、FATAL。

### WS log style

**问题**: WebSocket 是长连接,只显示"连接建立"和"连接断开"看不到中间的消息交换?

**方案**: WebSocket 日志特殊格式:
```
[WS] client connected: 192.168.1.100:54321
[WS] message received: {"type": "chat", "content": "hello"}
[WS] message sent: {"type": "chat", "content": "hi there"}
[WS] client disconnected: 192.168.1.100:54321
```

**洞察**: 显示每条消息的发送和接收,看到完整的通信过程。

**权衡**:
- ✓ 详细: 看到所有消息
- ✓ 调试: 可以调试 WebSocket 通信

**模式**: HTTP access log——记录每个 HTTP 请求,不只显示连接状态。

### 日志轮转

**问题**: 日志文件越来越大,打开慢、备份慢、占磁盘空间?

**方案**: 自动轮转 (rotate):
- 达到大小 (如 10MB) 自动切到新文件
- 保留最近 N 个 (如 5 个),删除更老的
- 文件名带时间戳 (如 `gateway-2026-06-20.log`)

**洞察**: 自动轮转,防止文件过大。

**权衡**:
- ✓ 管理: 文件小,打开快
- ✓ 节省: 保留最近 N 个,不占太多空间

**模式**: logrotate——Linux 工具,自动轮转日志文件。
