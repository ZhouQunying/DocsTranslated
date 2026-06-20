# Configuration examples

## 架构精读

> 跳过不影响阅读翻译正文。

### 从最小配置到完整配置——渐进式复杂度

文档提供了几个递进的配置示例:
1. **Absolute minimum**(最小配置): 只有模型和 auth,其他全用默认值
2. **Recommended starter**(推荐起步配置): 加上常用功能(如 tool profile、channel 配置)
3. **完整配置**: 加上高级功能(如多 agent、自定义 skill、安全策略)

**为什么这样组织?** 因为配置文件的复杂度可以很高(几十上百个字段),如果一上来就看完整配置,用户会被吓到。渐进式复杂度让用户:
- 先用最小配置跑起来(5 分钟上手)
- 需要时加功能(按需学习)
- 高级功能只在需要时出现(不干扰普通用户)

这跟 **React 的学习曲线**是一个思路——先学 `<div>Hello</div>`,再学 state,再学 hooks,再学 context。不是一上来就讲 Fiber 架构。OpenClaw 的配置文档也是同样: 先最小配置,再逐步加功能。

### Symlinked sibling skill repo——共享 skill 仓库

示例展示了如何把 skill 目录 symlink 到相邻的 Git 仓库:

```json
{
  agents: {
    defaults: {
      skills: ["~/.agents/skills/manager"]
    }
  }
}
```

其中 `~/.agents/skills/manager` 是一个 Git 仓库的 symlink。

**为什么这样设计?** 因为 skill 可能需要版本控制和团队协作:
- Skill 放在 Git 仓库里,可以 code review、版本管理、多人协作
- 多个 agent 共享同一个 skill 仓库,改一次所有 agent 都生效
- Skill 的变更历史可追溯(谁改了什么、什么时候改的)

**这跟 monorepo 的包共享**是一个思路——monorepo 里多个包共享同一个工具库,通过 workspace link 关联。OpenClaw 的 symlinked skill 也是同样: skill 放在独立仓库,通过 symlink 关联到 agent。

### Shared skill baseline with one override——基线 + 覆盖

示例展示了多个 agent 共享同一组 skill,但某个 agent 覆盖其中一个:

```json
{
  agents: {
    list: [
      {
        name: "agent-a",
        skills: ["~/.agents/skills/common", "~/.agents/skills/agent-a-custom"]
      }
    ]
  }
}
```

**为什么这样设计?** 因为大部分 skill 是共享的(如搜索、文件操作),但某些 agent 需要特殊 skill(如 agent-a 需要特殊的 API 调用)。基线 + 覆盖让:
- 共享 skill 改一次,所有 agent 生效
- 特殊 skill 只影响特定 agent
- 如果共享 skill 和特殊 skill 同名,特殊 skill 优先(后加载覆盖先加载)

这跟 CSS 的继承和覆盖是一个思路——子元素继承父元素的样式,但可以覆盖特定属性。OpenClaw 的 skill 也是同样: agent 继承基线 skill,但可以覆盖特定 skill。

### Multi-platform setup——多平台配置

示例展示了同时配置多个 channel(Slack、Discord、WhatsApp):

```json
{
  channels: {
    slack: { botToken: "..." },
    discord: { botToken: "..." },
    whatsapp: { phoneNumber: "..." }
  }
}
```

**为什么需要多平台?** 因为用户可能在不同平台:
- 工作用 Slack
- 社区用 Discord
- 客户用 WhatsApp

如果只支持一个平台,就失去了其他平台的用户。多平台让同一个 agent 同时服务多个平台的用户。

### Trusted node network auto-approval——可信网络自动配对

示例展示了在可信网络(如公司内网)里,自动批准 node 配对请求:

```json
{
  gateway: {
    pairing: {
      autoApproveNetworks: ["192.168.1.0/24"]
    }
  }
}
```

**为什么需要自动批准?** 因为默认情况下,每个 node 连接都需要手动批准(安全考虑)。但在可信网络(如公司内网)里,手动批准太麻烦——每次新设备加入都要管理员点一下。自动批准让可信网络里的设备自动配对,减少管理员负担。

**这跟 WiFi 的 WPS 是一个思路**——WPS 允许在同一网络内的设备自动配对,不需要输入密码。OpenClaw 的 auto-approve 也是同样: 同一网络内的设备自动配对,不需要手动批准。

**安全风险**: 自动批准只在可信网络里安全。如果在公共网络(如咖啡店 WiFi)开启,任何人都能配对 node,安全风险极高。所以 auto-approve 必须配合网络白名单(只允许特定 IP 段)。
