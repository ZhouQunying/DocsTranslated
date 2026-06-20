# Audit checks

## 架构精读

> 跳过不影响阅读翻译正文。

### Security audit

**问题**: 安全配置容易出错,手动检查容易遗漏?

**方案**: `openclaw security audit` 自动检查:
- 认证配置
- 网络暴露
- 工具权限
- 文件访问
- 依赖安全

**洞察**: 自动审计 = 系统性检查,不遗漏。

**权衡**:
- ✓ 自动化: 不依赖人工检查
- ✗ 误报: 可能产生 false positive

**模式**: 代码 lint——自动检查代码风格。

### Structured findings

**问题**: Audit 结果如何被工具处理?

**方案**: 结构化输出:
- **checkId**: 检查项唯一标识 (如 `auth-no-authentication`)
- **severity**: 严重程度 (critical、warning、info)
- **description**: 问题描述
- **remediation**: 修复建议

**洞察**: 结构化 = 可以被 CI/CD 处理、聚合、比较。

**权衡**:
- ✓ 可处理: CI/CD 可以检查 audit 结果
- ✗ 复杂: 需要定义结构化格式

**模式**: JUnit 测试报告——结构化,可以被 Jenkins 解析。

### CheckId

**问题**: 如何针对特定检查项配置例外?

**方案**: 每个检查项有唯一 checkId:
- `auth-no-authentication`: 没有启用认证
- `network-public-exposure`: Gateway 暴露在公网
- `tools-exec-unrestricted`: exec 工具没有限制

**洞察**: checkId = 可以针对性配置例外、跟踪修复进度。

**权衡**:
- ✓ 灵活: 可以忽略特定 checkId
- ✗ 复杂: 需要维护 checkId 列表

**模式**: ESLint rule ID——可以 `// eslint-disable-next-line no-unused-vars`。

### Audit 的自动化

**问题**: 如何防止不安全的配置上线?

**方案**: 集成到 CI/CD:
```bash
openclaw security audit --format json > audit.json
if jq -e '.findings[] | select(.severity == "critical")' audit.json; then
  exit 1
fi
```

**洞察**: CI/CD 集成 = 部署前自动检查,有 critical 则阻止部署。

**权衡**:
- ✓ 安全: 阻止不安全配置上线
- ✗ 慢: CI/CD 需要额外时间跑 audit

**模式**: 单元测试集成 CI/CD——测试失败则阻止部署。

### Audit 不是万能

**问题**: Audit 能检测所有安全问题吗?

**方案**: **不能**:
- ✗ 只能检测已知问题
- ✗ 可能误报
- ✗ 可能漏报

**洞察**: Audit 是辅助工具,需要人工审查 + 其他安全措施 (penetration testing、code review)。

**权衡**:
- ✓ 辅助: 自动检测已知问题
- ✗ 不完整: 不能检测所有问题

**模式**: 烟雾报警器——能检测火灾,不能检测煤气泄漏。
