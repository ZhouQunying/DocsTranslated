# Diagnostics export

## 架构精读

> 跳过不影响阅读翻译正文。

### Diagnostics zip——给开发者的 bug 报告包

OpenClaw 可以生成一个**诊断 zip 包**,用于提交 bug 报告:

```bash
openclaw diagnostics export
```

Zip 包包含:
- **Gateway 状态**: 运行时间、版本、配置
- **健康检查**: channel 连通性、node 状态
- **日志**: 最近的日志文件(脱敏后)
- **配置结构**: 配置的字段结构(不含值,只含字段名)
- **最近的事件**: 最近的操作记录(不含 payload,只含事件类型)

**为什么需要 diagnostics zip?** 因为用户报 bug 时,开发者需要大量信息:
- "你用的什么版本?" → zip 里有
- "配置是什么?" → zip 里有(结构)
- "日志有什么错误?" → zip 里有(脱敏后)
- "之前做了什么操作?" → zip 里有(事件记录)

如果用户手动收集这些信息,很麻烦(要跑多个命令、复制多个文件)。Diagnostics zip 一键生成,开发者直接看。

**这跟 Chrome 的 "Help > Report an issue" 是一个思路**——Chrome 的 bug 报告自动附带系统信息、版本、扩展列表,用户不需要手动收集。OpenClaw 的 diagnostics zip 也是同样: 自动收集诊断信息。

### Sanitization——脱敏处理

Diagnostics zip 经过**脱敏**(sanitization)处理:
- **不**包含 API key、OAuth token 等凭证
- **不**包含用户消息内容(payload)
- **不**包含文件内容(只含文件名和大小)

**为什么需要脱敏?** 因为 diagnostics zip 可能被:
- 上传到 GitHub issue(公开可见)
- 发送给 OpenClaw 团队(第三方)
- 分享给社区求助(公开可见)

如果 zip 包含敏感信息(如 API key、用户消息),就会泄露。脱敏保证: zip 可以安全分享,不会泄露敏感信息。

**这跟 Sentry 的 data scrubbing 是一个思路**——Sentry 的错误报告自动 scrub(擦洗)敏感数据(如密码、token),只保留非敏感信息。OpenClaw 的 diagnostics sanitization 也是同样: 自动脱敏,保护隐私。

### 把 diagnostics zip 当作 secrets——分享前审查

文档警告: **Treat diagnostics bundles like secrets until you have reviewed them**(在审查前,把 diagnostics zip 当作 secrets)。

**为什么?** 因为虽然 zip 经过脱敏,但:
- 脱敏可能不完善(某些敏感字段没被识别)
- 配置结构可能暴露信息(如"这个用户用了 X provider",可能被用于推断使用模式)
- 日志可能包含敏感信息(如用户消息的 fragment)

分享前应该:
1. 解压 zip
2. 检查每个文件,确认没有敏感信息
3. 如果有敏感信息,手动删除或编辑
4. 确认安全后再分享

**这跟 Git 的 .gitignore 是一个思路**——.gitignore 防止敏感文件被提交,但不能保证所有敏感文件都被忽略(如 .env 文件可能被误提交)。提交前应该检查 `git status`,确认没有敏感文件。OpenClaw 的 diagnostics zip 也是同样: 脱敏是自动的,但分享前应该手动审查。

### 自定义输出路径

Diagnostics zip 默认输出到当前目录,可以指定路径:

```bash
openclaw diagnostics export --output /tmp/openclaw-diagnostics.zip
```

**为什么需要自定义路径?** 因为:
- CI/CD 场景: 需要把 zip 输出到特定目录,方便上传
- 自动化场景: 需要把 zip 输出到固定路径,方便后续处理
- 权限场景: 当前目录可能没有写权限,需要输出到其他目录
