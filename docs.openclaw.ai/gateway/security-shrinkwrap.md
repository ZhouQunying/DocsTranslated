# Shrinkwrap

## 架构精读

> 跳过不影响阅读翻译正文。

### Dependency lockfile

**问题**: npm 包版本可能变化,导致"开发时版本 ≠ 用户安装时版本"?

**方案**: 依赖锁定文件:
- **pnpm-lock.yaml**: 源代码仓库用 (开发时)
- **npm-shrinkwrap.json**: 发布到 npm (用户安装时)

**洞察**: 锁定文件锁定确切版本,保证版本一致。

**权衡**:
- ✓ 一致: 开发版本 = 用户版本
- ✗ 更新慢: 需要手动更新锁定文件

**模式**: Docker image tag——`node:20` 可能变化,`node:20.1.0` 总是相同。

### 源代码用 pnpm-lock,发布用 shrinkwrap

**问题**: 开发用 pnpm,但 npm 不认 pnpm-lock.yaml?

**方案**: 
- 开发: `pnpm-lock.yaml` (pnpm 友好)
- 发布: 转换成 `npm-shrinkwrap.json` (npm 能认)

**洞察**: 不同包管理器,锁定文件格式不同,需要转换。

**权衡**:
- ✓ 开发友好: 用 pnpm (快、monorepo)
- ✓ 发布兼容: 转换成 npm 格式

**模式**: TypeScript → JavaScript——开发时用 TS,发布时编译成 JS。

### Publishable dependency lockfile

**问题**: `package-lock.json` 不会被发布到 npm?

**方案**: `npm-shrinkwrap.json` 会被发布:
- 普通 `package-lock.json`: 被 `.npmignore` 忽略
- `npm-shrinkwrap.json`: 即使被 `.npmignore` 忽略,也会发布

**洞察**: 可发布的锁定文件 = 用户安装时能读取锁定的版本。

**权衡**:
- ✓ 一致: 用户安装版本 = 发布时锁定版本
- ✗ 文件大: 锁定文件增加 npm 包大小

**模式**: Docker image digest——`node@sha256:abc123` 总是相同 image。

### 依赖锁定的安全意义

**问题**: 依赖升级可能引入缺陷或恶意代码?

**方案**: 锁定文件锁定版本:
- ✓ 防止供应链攻击
- ✓ 可审计: 检查所有依赖
- ✓ 可复现: 任何时候安装都相同

**洞察**: 供应链攻击 = 依赖被入侵,锁定文件锁定旧版本,不自动升级。

**权衡**:
- ✓ 安全: 防止恶意依赖
- ✗ 更新慢: 需要手动升级依赖

**模式**: 软件签名——保证"下载的软件 = 开发者发布的软件"。

### 什么时候更新 shrinkwrap?

**问题**: 锁定文件什么时候更新?

**方案**: 手动更新:
- 依赖升级时
- 安全补丁时
- 发布新版本时

**洞察**: 手动更新 + 测试 = 更可控,不自动升级。

**权衡**:
- ✓ 可控: 手动决定什么时候升级
- ✗ 慢: 不会自动获得新功能

**模式**: Kubernetes image 策略——Always (总是拉取) vs IfNotPresent (本地没有才拉取)。
