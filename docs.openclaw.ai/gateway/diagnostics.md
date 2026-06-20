# Diagnostics export

## 架构精读

> 跳过不影响阅读翻译正文。

### Diagnostics zip

**问题**: 用户报 bug 时,开发者需要大量信息 (版本、配置、日志、操作记录),手动收集很麻烦?

**方案**: `openclaw diagnostics export` 生成诊断 zip 包:
```bash
openclaw diagnostics export
```

包含:
- **Gateway 状态**: 运行时间、版本、配置
- **健康检查**: channel 连通性、node 状态
- **日志**: 最近的日志 (脱敏后)
- **配置结构**: 字段结构 (不含值)
- **最近的事件**: 操作记录 (不含 payload)

**洞察**: 一键生成,开发者直接看。

**权衡**:
- ✓ 方便: 不需要手动收集
- ✓ 完整: 包含所有诊断信息

**模式**: Chrome "Help > Report an issue"——自动附带系统信息、版本、扩展列表。

### Sanitization

**问题**: Diagnostics zip 可能被上传到 GitHub issue、发送给 OpenClaw 团队,包含敏感信息会泄露?

**方案**: **脱敏** (sanitization) 处理:
- ✗ 不包含 API key、OAuth token
- ✗ 不包含用户消息内容
- ✗ 不包含文件内容 (只含文件名和大小)

**洞察**: 自动脱敏,保护隐私。

**权衡**:
- ✓ 安全: 可以安全分享
- ✓ 隐私: 不泄露敏感信息

**模式**: Sentry data scrubbing——自动 scrub 敏感数据。

### 把 diagnostics zip 当作 secrets

**问题**: 脱敏可能不完善 (某些敏感字段没被识别),配置结构可能暴露信息?

**方案**: **在审查前,把 diagnostics zip 当作 secrets**。

分享前应该:
1. 解压 zip
2. 检查每个文件
3. 手动删除敏感信息
4. 确认安全后再分享

**洞察**: 脱敏是自动的,但分享前应该手动审查。

**权衡**:
- ✓ 安全: 手动审查防止泄露
- ✗ 麻烦: 需要手动检查

**模式**: Git .gitignore——防止敏感文件被提交,但提交前应该检查 `git status`。

### 自定义输出路径

**问题**: CI/CD 场景需要把 zip 输出到特定目录,方便上传?

**方案**: 指定路径:
```bash
openclaw diagnostics export --output /tmp/openclaw-diagnostics.zip
```

**洞察**: 适配 CI/CD、自动化、权限场景。

**权衡**:
- ✓ 灵活: 可以指定路径
- ✓ 自动化: 方便后续处理
