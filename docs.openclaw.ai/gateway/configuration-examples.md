# Configuration examples

## 架构精读

> 跳过不影响阅读翻译正文。

### 渐进式复杂度

**问题**: 配置文件复杂度高,用户被吓到?

**方案**: 递进示例:
1. **最小配置**: 只有模型和 auth
2. **推荐起步**: 加常用功能 (tool profile、channel)
3. **完整配置**: 加高级功能 (多 agent、自定义 skill)

**洞察**: 先用最小配置跑起来 (5 分钟上手),需要时加功能 (按需学习)。

**权衡**:
- ✓ 易上手: 不被复杂度吓到
- ✓ 渐进: 高级功能只在需要时出现

**模式**: React 学习曲线——先 `<div>Hello</div>`,再 state,再 hooks,再 context。

### Symlinked sibling skill repo

**问题**: Skill 需要版本控制和团队协作?

**方案**: Skill 目录 symlink 到 Git 仓库:
```json
{
  agents: {
    defaults: {
      skills: ["~/.agents/skills/manager"]
    }
  }
}
```

**洞察**: Skill 放在 Git 仓库 = code review、版本管理、多人协作、变更可追溯。

**权衡**:
- ✓ 协作: 多人可编辑 skill
- ✓ 版本控制: skill 变更有历史

**模式**: Monorepo 包共享——多个包共享工具库,通过 workspace link 关联。

### Shared skill baseline with one override

**问题**: 多个 agent 共享大部分 skill,但某些 agent 需要特殊 skill?

**方案**: 基线 + 覆盖:
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

**洞察**: 共享 skill 改一次所有 agent 生效,特殊 skill 只影响特定 agent。

**权衡**:
- ✓ DRY: 共享 skill 不重复
- ✓ 灵活: 特殊 skill 可覆盖

**模式**: CSS 继承和覆盖——子元素继承父元素样式,可覆盖特定属性。

### Multi-platform setup

**问题**: 用户在不同平台 (Slack、Discord、WhatsApp)?

**方案**: 同时配置多个 channel:
```json
{
  channels: {
    slack: { botToken: "..." },
    discord: { botToken: "..." },
    whatsapp: { phoneNumber: "..." }
  }
}
```

**洞察**: 同一 agent 同时服务多个平台的用户。

**权衡**:
- ✓ 覆盖广: 不失去任何平台的用户
- ✗ 复杂: 需要为每个平台配置

### Trusted node network auto-approval

**问题**: 可信网络 (公司内网) 里,手动批准 node 配对太麻烦?

**方案**: 自动批准可信网络:
```json
{
  gateway: {
    pairing: {
      autoApproveNetworks: ["192.168.1.0/24"]
    }
  }
}
```

**洞察**: 可信网络自动配对,减少管理员负担。

**权衡**:
- ✓ 方便: 不需要手动批准
- ✗ 风险: 公共网络开启则任何人都能配对

**模式**: WiFi WPS——同一网络内设备自动配对。

**安全**: 必须配合网络白名单,只在可信网络使用。
