# 安装覆盖

## 架构精读

> 跳过不影响阅读翻译正文。

### 为什么需要安装覆盖而不是直接用 npm link？

`npm link` 可以测试本地包，但它绕过了 OpenClaw 的安装流程——不经过 manifest 验证、不写入安装记录、不触发 setup 流程。安装覆盖让设置时的插件安装走正常路径，只是把源从官方目录换成指定的 npm 包或本地 tarball。就像 Docker 的 `--build-arg`——构建流程不变，只是输入源不同。好处是 E2E 测试覆盖了真实的安装路径，坏处是需要显式启用环境变量，防止生产环境误用。

---

插件安装覆盖让维护者针对特定 npm 包或本地 npm 打包 tarball 测试设置时的插件安装。它们仅用于 E2E 和包验证。普通用户应用 [`openclaw plugins install`](/cli/plugins) 安装插件。

> **警告**：覆盖执行你提供的源的插件代码。仅在隔离状态目录或一次性测试机中使用。

## 环境

除非两个变量都设置，否则覆盖禁用：

```bash
export OPENCLAW_ALLOW_PLUGIN_INSTALL_OVERRIDES=1
export OPENCLAW_PLUGIN_INSTALL_OVERRIDES='{
  "codex": "npm-pack:/tmp/openclaw-codex-2026.5.8.tgz",
  "openclaw-web-search": "npm:@openclaw/web-search@2026.5.8"
}'
```

覆盖映射是按插件 id 索引的 JSON。值支持：

- `npm:<registry-spec>` 用于注册表包和精确版本或标签
- `npm-pack:<path.tgz>` 用于 `npm pack` 生成的本地 tarball

相对 `npm-pack:` 路径从当前工作目录解析。

## 行为

当设置时流程请求安装 id 出现在映射中的插件时，OpenClaw 使用覆盖源而不是目录、捆绑或默认 npm 源。这适用于入门和其他使用共享设置时插件安装器的流程。

覆盖仍强制执行预期的插件 id。映射到 `codex` 的 tarball 必须安装 manifest id 为 `codex` 的插件。

覆盖不继承官方受信源状态。即使目录条目通常代表 OpenClaw 持有的包，覆盖也被视为 operator 提供的测试输入。

工作区 `.env` 文件不能启用安装覆盖。在启动 OpenClaw 的受信 shell、CI 作业或远程测试命令中设置这些变量。

## 包 E2E

使用隔离状态目录，这样包安装和安装记录不会影响正常的 OpenClaw 状态：

```bash
npm pack extensions/codex --pack-destination /tmp

OPENCLAW_STATE_DIR="$(mktemp -d)" \
OPENCLAW_ALLOW_PLUGIN_INSTALL_OVERRIDES=1 \
OPENCLAW_PLUGIN_INSTALL_OVERRIDES='{"codex":"npm-pack:/tmp/openclaw-codex-2026.5.8.tgz"}' \
pnpm openclaw onboard --mode local
```

验证状态目录下已安装的包：

```bash
find "$OPENCLAW_STATE_DIR/npm/projects" -path '*/node_modules/@openclaw/codex/package.json' -print
grep -R '"@openclaw/codex"' "$OPENCLAW_STATE_DIR/npm/projects"/*/package-lock.json
```

实际 provider E2E 测试时，在启动测试命令前从受信 shell 或 CI 密钥获取真实 API 密钥。不要打印密钥；仅报告来源和密钥是否存在。
