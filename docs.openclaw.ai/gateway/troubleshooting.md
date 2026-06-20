# Troubleshooting

## 架构精读

> 跳过不影响阅读翻译正文。

### 按顺序执行诊断步骤

**问题**: 问题可能有依赖关系,不按顺序排查浪费时间?

**方案**: **按顺序执行**:
1. 检查 Gateway 是否在运行: `openclaw gateway status`
2. 检查配置是否正确: `openclaw doctor --lint`
3. 检查日志: 看最近的 ERROR 和 WARN
4. 检查 channel 连通性: `openclaw health`

**洞察**: 按顺序排查 = 快速定位问题。

**权衡**:
- ✓ 高效: 从简单到复杂
- ✓ 系统: 不遗漏关键步骤

**模式**: 医生诊断流程——问症状、查体、化验、诊断。

### Fix PATH

**问题**: Gateway 启动失败,因为 `PATH` 环境变量不对,找不到 Node.js 或 openclaw CLI?

**方案**: 显式设置 PATH:
```ini
# systemd unit
Environment=PATH=/usr/local/bin:/usr/bin:/bin
```

**洞察**: 服务 (LaunchAgent、systemd) 的 PATH 可能不完整。

**权衡**:
- ✓ 明确: 显式设置 PATH
- ✗ 麻烦: 需要手动配置

**模式**: cron PATH 问题——cron job 的 PATH 通常只有 `/usr/bin:/bin`。

### Reinstall the gateway service

**问题**: Gateway 服务损坏 (LaunchAgent plist 或 systemd unit 文件被修改)?

**方案**: 重新安装服务:
```bash
openclaw gateway install
```

**洞察**: 重新生成服务文件,修复损坏的服务。

**权衡**:
- ✓ 修复: 恢复服务
- ✓ 简单: 一条命令

**模式**: `apt install --reinstall`——重新安装包。

**场景**:
- 服务文件被手动修改
- 升级 OpenClaw 后服务文件没有更新
- 服务文件被删除或损坏

### Remove stale wrappers

**问题**: 旧版本的 OpenClaw 留下了 wrapper 脚本,导致"openclaw" 命令调用旧版本?

**方案**: 删除 stale wrappers:
```bash
rm /usr/local/bin/openclaw
openclaw gateway install
```

**洞察**: 让系统用新版本的二进制文件。

**权衡**:
- ✓ 更新: 用新版本
- ✗ 风险: 删除前确认是 wrapper

### Use a standard context window

**问题**: LLM 调用失败,报错"context window exceeded",配置的 context window 太大?

**方案**: 使用模型的**标准 context window** (如 GPT-4 128K、Claude 200K),不要配置过大的值。

**洞察**: 模型有固定的 context window,配置超过模型能力的值会报错。

**权衡**:
- ✓ 兼容: 使用模型支持的 context window
- ✗ 限制: 不能使用超过模型能力的值

### Configure fallback models

**问题**: 主模型不可用 (rate limit、provider 挂了),agent 完全不能用?

**方案**: 配置 fallback models:
```json
{
  agents: {
    defaults: {
      model: {
        primary: "openai/gpt-4",
        fallbacks: ["anthropic/claude-opus-4-6", "google/gemini-pro"]
      }
    }
  }
}
```

**洞察**: 主模型挂了,自动切换到 fallback 模型。

**权衡**:
- ✓ 可用: 主模型挂了也能用
- ✓ 稳定: 不依赖单一 provider

**模式**: DNS fallback 记录——主 IP 不可用时自动切换到备用 IP。
