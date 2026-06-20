# Troubleshooting

## 架构精读

> 跳过不影响阅读翻译正文。

### 按顺序执行诊断步骤——不要跳步

文档强调: **Run these first, in this order**(按这个顺序先执行这些):

1. **检查 Gateway 是否在运行**: `openclaw gateway status`
2. **检查配置是否正确**: `openclaw doctor --lint`
3. **检查日志**: 看最近的 ERROR 和 WARN 日志
4. **检查 channel 连通性**: `openclaw health`

**为什么强调顺序?** 因为问题可能有依赖关系:
- 如果 Gateway 没运行,检查配置和日志都没意义(先启动 Gateway)
- 如果配置错了,看日志也找不到问题(先修复配置)
- 如果 channel 断了,看 Gateway 状态也找不到问题(先检查 channel)

不按顺序排查 = 浪费时间。按顺序排查 = 快速定位问题。

**这跟医生的诊断流程**是一个思路——医生先问症状、再查体、再化验、再诊断。不是一上来就开 CT(可能没必要)。OpenClaw 的 troubleshooting 也是同样: 按顺序排查,从简单到复杂。

### Fix PATH——环境变量问题

常见问题: Gateway 启动失败,因为 `PATH` 环境变量不对,找不到 Node.js 或 openclaw CLI。

**为什么 PATH 会出问题?** 因为:
- **LaunchAgent**(macOS): LaunchAgent 的 PATH 可能跟用户 shell 的 PATH 不同
- **systemd service**(Linux): systemd service 的 PATH 是最小化的,可能不包含 `/usr/local/bin`
- **手动启动 vs 服务启动**: 手动启动时 PATH 完整,服务启动时 PATH 不完整

**修复方式**: 在 LaunchAgent plist 或 systemd unit 里显式设置 PATH:

```ini
# systemd unit
Environment=PATH=/usr/local/bin:/usr/bin:/bin
```

**这跟 cron 的 PATH 问题**是一个思路——cron job 的 PATH 通常只有 `/usr/bin:/bin`,不包含 `/usr/local/bin`。如果 cron job 需要执行 `/usr/local/bin` 下的命令,需要用绝对路径或显式设置 PATH。OpenClaw 的 Gateway 服务也是同样: 服务的 PATH 可能不完整,需要显式设置。

### Reinstall the gateway service——服务损坏

如果 Gateway 服务损坏(如 LaunchAgent plist 或 systemd unit 文件被修改),重新安装服务:

```bash
openclaw gateway install
```

**什么时候需要 reinstall?**
- 服务文件被手动修改,导致服务无法启动
- 升级 OpenClaw 后,服务文件没有更新
- 服务文件被删除或损坏

**这跟 `apt install --reinstall` 是一个思路**——如果包的文件损坏,重新安装包。OpenClaw 的 gateway install 也是同样: 重新生成服务文件,修复损坏的服务。

### Remove stale wrappers——清理旧的 wrapper 脚本

旧版本的 OpenClaw 可能留下了 wrapper 脚本(如 `/usr/local/bin/openclaw` 是一个 shell 脚本,不是真正的 CLI),需要删除:

```bash
rm /usr/local/bin/openclaw
openclaw gateway install
```

**为什么会有 stale wrappers?** 因为:
- 旧版本的 OpenClaw 用 wrapper 脚本启动 Gateway
- 新版本直接用二进制文件
- 升级时 wrapper 脚本没被删除,导致"openclaw" 命令还是调用旧版本的 wrapper

删除 stale wrappers,让系统用新版本的二进制文件。

### Use a standard context window——模型上下文窗口问题

如果 LLM 调用失败,报错"context window exceeded"(上下文窗口超出),可能是配置的 context window 太大:

```json
{
  agents: {
    defaults: {
      model: {
        contextWindow: 200000
      }
    }
  }
}
```

**修复方式**: 使用模型的**标准 context window**(如 GPT-4 是 128K,Claude 是 200K),不要配置过大的值。

**为什么用户会配置过大的值?** 因为用户可能以为"context window 越大越好",但实际上:
- 模型有固定的 context window,配置超过模型能力的值会报错
- 过大的 context window 会消耗更多 token,增加成本

### Configure fallback models——模型不可用时的后备

如果主模型不可用(如 rate limit、provider 挂了),配置 fallback models:

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

**为什么需要 fallback?** 因为 LLM provider 可能:
- Rate limit(请求太多,暂时拒绝)
- 服务中断(provider 挂了)
- Billing 问题(账户欠费)

没有 fallback = 主模型挂了,agent 完全不能用。有 fallback = 主模型挂了,自动切换到 fallback 模型,agent 继续工作。

**这跟 DNS 的 fallback 记录**是一个思路——DNS 可以配置多个 A 记录,主 IP 不可用时,自动切换到备用 IP。OpenClaw 的 model fallback 也是同样: 主模型不可用时,自动切换到 fallback 模型。
