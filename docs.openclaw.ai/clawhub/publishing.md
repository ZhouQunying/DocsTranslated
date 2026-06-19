# Publishing / 发布

## 架构精读

> 跳过不影响阅读翻译正文。

### 发布验证管道——五层检查保证包质量

发布流程不是简单的"上传文件"。ClawHub 在存储版本前跑五层验证：

1. **认证检查**：token 是否可以为该 owner 发布
2. **元数据验证**：名称、版本、描述是否符合格式
3. **文件验证**：文件列表是否完整、大小是否超限
4. **源信息验证**：源归属是否声明、是否与已有包冲突
5. **安全检查**：自动化扫描是否通过

任何一层失败，整个发布被拒绝——**原子性验证**。这跟 Kubernetes 的 admission controller 是一个思路：pod 创建前必须通过所有 admission webhook（认证、配额、策略、安全），任一拒绝则 pod 不创建。

### "审核中"状态——为什么新版本可能不可安装？

新版本在审核完成前可能不会出现在正常的安装和下载界面。这是一个**软发布**机制——包已经存储，但不对公众可见，直到安全扫描和人工审核通过。

这跟 npm 的"unlisted"和 Apple App Store 的"审核中"是同一个设计意图：给平台时间检测恶意内容，但不阻止发布者的工作流。发布者可以立即看到自己的包（用于诊断），但消费者看不到——直到审核通过。

代价是发布到可用的延迟增加（几分钟到几小时）。但对于安全敏感的包注册表，这个延迟是必要的——防止恶意包在被检测前被大量安装。

---

Publishing sends a skill folder or plugin package to ClawHub under the owner you choose. ClawHub checks that your token can publish for that owner, validates the metadata, name, version, files, and source information, then stores the release and starts automated security checks.

发布将你选择的 owner 下的技能文件夹或插件包发送到 ClawHub。ClawHub 检查你的 token 是否可以为该 owner 发布,验证元数据、名称、版本、文件和源信息,然后存储版本并启动自动化安全检查。

If validation fails, nothing is published. New releases may also stay out of normal install and download surfaces until review finishes.

如果验证失败,不会发布任何内容。新版本在审核完成前也可能不会出现在正常的安装和下载界面。

## Skills / 技能

The simplest publishing path is the CLI. Sign in, then publish a local skill folder:

最简单的发布路径是 CLI。登录后发布本地技能文件夹:

```bash
clawhub login
clawhub skill publish ./my-skill \
  --slug my-skill \
  --name "My Skill" \
  --version 1.0.0 \
  --owner <owner>
```

Use `--owner <handle>` when publishing to an org owner. Omit it to publish as the authenticated user.

发布到组织 owner 时使用 `--owner <handle>`。省略则以已认证用户身份发布。

For catalog repos, use `sync` to scan folders containing `SKILL.md` and publish new or changed skills:

对于目录仓库,使用 `sync` 扫描包含 `SKILL.md` 的文件夹并发布新增或变更的技能:

```bash
clawhub sync --dry-run --owner <owner>
clawhub sync --all --owner <owner>
```

Use `--dry-run` first to see the plan without uploading.

先使用 `--dry-run` 查看计划而不上传。

### GitHub Actions for Skills / 技能的 GitHub Actions

If you want to run skill publishing from CI, call ClawHub's reusable `skill-publish.yml` workflow from a small workflow in your repo.

如果你想从 CI 运行技能发布,从你仓库中的小工作流调用 ClawHub 的可复用 `skill-publish.yml` 工作流。

The example below is shaped for a catalog repo: operators choose whether to preview the full catalog, publish one skill folder, or publish the whole catalog.

下面的示例针对目录仓库:操作员可以选择预览完整目录、发布单个技能文件夹或发布整个目录。

**GitHub Actions workflow example / GitHub Actions 工作流示例:**

```yaml
name: Publish Skills to ClawHub
on:
  workflow_dispatch:
    inputs:
      mode:
        description: What to run.
        type: choice
        required: true
        default: dry-run
        options:
          - dry-run
          - publish-single
          - publish-catalog
      skill_path:
        description: Skill folder for publish-single, for example skills/<slug>.
        type: string
        required: false
        default: ""
permissions:
  contents: read
  id-token: write
jobs:
  validate-single:
    if: github.event_name == 'workflow_dispatch' && inputs.mode == 'publish-single'
    runs-on: ubuntu-latest
    steps:
      - name: Validate single-skill input
        env:
          SKILL_PATH: ${{ inputs.skill_path }}
        run: |
          set -euo pipefail
          if [[ -z "${SKILL_PATH}" ]]; then
            echo "::error::skill_path is required when mode is publish-single."
            exit 1
          fi
          case "${SKILL_PATH}" in
            skills/*) ;;
            *)
              echo "::error::skill_path must point under skills/, for example skills/<slug>."
              exit 1
              ;;
          esac

  dry-run:
    if: github.event_name == 'workflow_dispatch' && inputs.mode == 'dry-run'
    uses: openclaw/clawhub/.github/workflows/skill-publish.yml@main
    with:
      owner: <owner>
      dry_run: true
    secrets:
      clawhub_token: ${{ secrets.CLAWHUB_TOKEN }}

  publish-single:
    if: github.event_name == 'workflow_dispatch' && inputs.mode == 'publish-single'
    needs: validate-single
    uses: openclaw/clawhub/.github/workflows/skill-publish.yml@main
    with:
      owner: <owner>
      skill_path: ${{ inputs.skill_path }}
      dry_run: false
    secrets:
      clawhub_token: ${{ secrets.CLAWHUB_TOKEN }}

  publish-catalog:
    if: github.event_name == 'workflow_dispatch' && inputs.mode == 'publish-catalog'
    uses: openclaw/clawhub/.github/workflows/skill-publish.yml@main
    with:
      owner: <owner>
      dry_run: false
    secrets:
      clawhub_token: ${{ secrets.CLAWHUB_TOKEN }}
```

Replace `<owner>` with your ClawHub owner handle. The called workflow defaults to scanning `skills/`; pass `skill_path` only when you want to process one folder.

将 `<owner>` 替换为你的 ClawHub owner 句柄。被调用的工作流默认扫描 `skills/`;仅在需要处理单个文件夹时传递 `skill_path`。

Before running a real publish, sign in as a ClawHub user that can publish to the selected owner, then store the current CLI token as a `CLAWHUB_TOKEN` repository secret:

运行真实发布前,以可以发布到选定 owner 的 ClawHub 用户登录,然后将当前 CLI token 存储为 `CLAWHUB_TOKEN` 仓库密钥:

```bash
clawhub login --label "Skills GitHub Actions"
gh secret set CLAWHUB_TOKEN \
  --repo OWNER/REPO \
  --body "$(clawhub token)"
```

Start with `dry-run`, then publish one skill with `publish-single`, and only then use `publish-catalog` for the full catalog.

先使用 `dry-run`,然后用 `publish-single` 发布单个技能,最后才用 `publish-catalog` 发布完整目录。

## Plugins / 插件

Plugins use npm-style package names. Scoped package names include the owner in the first part of the name:

插件使用 npm 风格的包名。作用域包名在名称的第一部分包含 owner:

```
@owner/package-name
```

The scope must match the selected publish owner. If your package is named `@openclaw/dronzer`, it can only be published as `@openclaw`. If you publish as `@vintageayu`, rename the package to `@vintageayu/dronzer`.

作用域必须匹配选定的发布 owner。如果你的包名为 `@openclaw/dronzer`,它只能以 `@openclaw` 发布。如果你以 `@vintageayu` 发布,将包重命名为 `@vintageayu/dronzer`。

This prevents a package from claiming an org namespace that the publisher does not control.

这防止包声称发布者不控制的组织命名空间。

### Before Publishing a Plugin / 发布插件前

- Pick an owner that matches the package scope.
  
  选择匹配包作用域的 owner。

- Include `openclaw.plugin.json`. Code plugins also need `package.json` with `openclaw.compat.pluginApi` and `openclaw.build.openclawVersion`.
  
  包含 `openclaw.plugin.json`。代码插件还需要带 `openclaw.compat.pluginApi` 和 `openclaw.build.openclawVersion` 的 `package.json`。

- Include source repository and exact commit metadata, or use the CLI from a GitHub-backed checkout so it can detect them.
  
  包含源仓库和精确的提交元数据,或从 GitHub 支持的 checkout 使用 CLI 以便它可以检测它们。

- Run `clawhub package validate <source>` before publishing. For package, manifest, SDK import, or artifact findings, see Plugin validation fixes.
  
  发布前运行 `clawhub package validate <source>`。对于包、清单、SDK 导入或构建产物问题,参见插件验证修复。

- Run `clawhub package publish <source> --dry-run` before creating a release.
  
  创建版本前运行 `clawhub package publish <source> --dry-run`。

- Expect new releases to stay out of public install surfaces until automated security checks and verification finish.
  
  预期新版本在自动化安全检查和验证完成前不会出现在公共安装界面。

### Trusted Publishing for Packages / 包的可信发布

Package trusted publishing is a two-step setup:

包的可信发布是两步设置:

1. Publish the package once through normal manual or token-authenticated `clawhub package publish`. This creates the package row and establishes the package managers who can change its trusted publisher config.
   
   通过正常手动或 token 认证的 `clawhub package publish` 发布一次包。这会创建包行并建立可以更改其可信发布者配置的管理员。

2. A package manager sets the GitHub Actions trusted publisher config:
   
   管理员设置 GitHub Actions 可信发布者配置:

```bash
clawhub package trusted-publisher set @owner/package-name \
  --repository owner/repo \
  --workflow-filename package-publish.yml
```

After config is set, future supported GitHub Actions publishes can use OIDC/trusted publishing without storing a long-lived ClawHub token in the repository. The configured repository and workflow filename must match the GitHub Actions OIDC claim. If you also pass `--environment <name>`, the GitHub Actions environment claim must match that name exactly.

配置设置后,未来支持的 GitHub Actions 发布可以使用 OIDC/可信发布,无需在仓库中存储长期有效的 ClawHub token。配置的仓库和工作流文件名必须匹配 GitHub Actions OIDC 声明。如果你还传递 `--environment <name>`,GitHub Actions 环境声明必须完全匹配该名称。

ClawHub verifies the configured GitHub repository when trusted publisher config is set. Public repositories can be verified through public GitHub metadata. Private repositories require ClawHub to have GitHub access to that repository, for example through a future ClawHub GitHub App installation or another authorized GitHub integration.

ClawHub 在设置可信发布者配置时验证配置的 GitHub 仓库。公共仓库可以通过公共 GitHub 元数据验证。私有仓库需要 ClawHub 对该仓库有 GitHub 访问权限,例如通过未来的 ClawHub GitHub App 安装或其他授权的 GitHub 集成。

The current reusable package publish workflow supports secretless trusted publishing for `workflow_dispatch` publishes when `id-token: write` is available. Tag-push real publishes still need `clawhub_token`, so keep `CLAWHUB_TOKEN` available for tag releases, first publishes, untrusted packages, or break-glass publishes.

当前的可复用包发布工作流支持在 `id-token: write` 可用时为 `workflow_dispatch` 发布提供无密钥可信发布。标签推送的真实发布仍需要 `clawhub_token`,因此保留 `CLAWHUB_TOKEN` 用于标签发布、首次发布、不受信任的包或紧急发布。

Inspect or remove the config with:

检查或移除配置:

```bash
clawhub package trusted-publisher get @owner/package-name
clawhub package trusted-publisher delete @owner/package-name
```

Deleting trusted publisher config is the rollback path. It disables future trusted publish token minting until a package manager sets config again.

删除可信发布者配置是回滚路径。它禁用未来的可信发布 token 铸造,直到管理员再次设置配置。

## FAQ / 常见问题

### 包作用域必须匹配选定 owner

If the package scope and selected owner do not match, ClawHub rejects the publish:

如果包作用域和选定 owner 不匹配,ClawHub 拒绝发布:

```
Package scope "@openclaw" must match selected owner "@vintageayu".
Publish as "@openclaw" or rename this package to "@vintageayu/dronzer".
```

To fix it, either choose the owner named by the package scope, or rename the package so the scope matches the owner you can publish as.

修复方法是选择包作用域命名的 owner,或重命名包使作用域匹配你可以发布的 owner。

If the package name already has the right scope but the package is owned by the wrong publisher, transfer ownership instead:

如果包名已有正确作用域但包被错误的发布者持有,改为转移所有权:

```bash
clawhub package transfer @opik/opik-openclaw --to opik
```

Use package or skill transfer only when you have admin access to both the current owner and the destination publisher. Package transfer does not let you publish into a scope you cannot manage.

仅当你对当前 owner 和目标发布者都有管理员访问权限时才使用包或技能转移。包转移不允许你发布到无法管理的作用域。

This protects org namespaces. A package named `@openclaw/dronzer` claims the `@openclaw` namespace, so only publishers with access to the `@openclaw` owner can publish it.

这保护组织命名空间。名为 `@openclaw/dronzer` 的包声称 `@openclaw` 命名空间,因此只有对 `@openclaw` owner 有访问权限的发布者可以发布它。

## 相关 / Related

- [CLI](/clawhub/cli) — ClawHub CLI 命令参考
- [Skill format](/clawhub/skill-format) — 技能文件夹格式
- [Auth](/clawhub/auth) — 登录和 token 管理
- [HTTP API](/clawhub/http-api) — 发布 API 端点
