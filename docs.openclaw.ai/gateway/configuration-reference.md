# Configuration reference

## 架构精读

> 跳过不影响阅读翻译正文。

### 多实例隔离——同一台机器跑多个 Gateway

OpenClaw 支持在同一台机器上运行多个 Gateway 实例,每个实例有独立的:
- **配置目录**: 每个 Gateway 读自己的 `openclaw.json`
- **数据目录**: 每个 Gateway 存自己的 session、auth、workspace
- **监听端口**: 每个 Gateway 绑定不同端口,不冲突

**为什么需要多实例?** 几个常见场景:
- **开发 vs 生产**: 开发用的 Gateway 连测试模型,生产用的连正式模型,不能混
- **多租户**: 一台服务器上给多个用户/团队各跑一个 Gateway,数据隔离
- **不同用途**: 一个 Gateway 跑 coding agent,另一个跑 customer support agent,各自的配置和权限不同

**怎么隔离?** 通过不同的 `--config-dir` 参数启动。每个 Gateway 读自己的配置目录,互不干扰。这跟 Docker 的 `--data-root` 是一个思路——多个 Docker daemon 可以跑在同一台机器上,通过不同的 data root 目录隔离。

### gateway.tls——Gateway 自己终结 TLS

Gateway 可以直接配置 TLS(Transport Layer Security,HTTPS 的加密层),不需要额外的反向代理(如 nginx/Caddy)来做 TLS 终结:

```json
{
  gateway: {
    tls: {
      certFile: "/path/to/cert.pem",
      keyFile: "/path/to/key.pem"
    }
  }
}
```

**为什么 Gateway 自己终结 TLS?** 简化部署。传统架构是 nginx 终结 TLS → 转发明文到后端,需要两个进程。Gateway 直接终结 TLS,一个进程搞定。适合简单部署(单机、小规模),不需要引入 nginx 这个额外组件。

**什么时候不用 Gateway 终结 TLS?** 大规模部署时,用反向代理(如 Caddy、nginx、ALB)更好——反向代理可以做负载均衡、rate limiting、WAF,这些是 Gateway 不擅长的。文档的 EasyRunner 方案就是用 Caddy 终结 TLS,Gateway 不配 TLS。

### gateway.reload——热更新行为配置

`gateway.reload` 控制配置热更新的行为:
- **检测间隔**: 多久检查一次配置文件变更(默认几秒)
- **自动 reload**: 检测到变更后是否自动热更新(默认 true)
- **reload 策略**: 哪些字段可以热更新,哪些需要重启

**为什么需要配置 reload 行为?** 因为自动 reload 不一定适合所有场景:
- **生产环境**: 可能想手动 reload(改完配置后,确认无误再 reload),避免误操作
- **开发环境**: 自动 reload 更方便,改了配置立刻生效,不用手动操作
- **CI/CD 部署**: 配置文件由自动化工具管理,可能需要先跑测试再 reload

**这跟 systemd 的 `daemon-reload` 是一个思路**——改了 systemd unit 文件后,需要 `systemctl daemon-reload` 让 systemd 重新读取配置。OpenClaw 的 reload 也是同样: 配置文件改了,需要 reload 让 Gateway 重新读取。区别是 OpenClaw 可以自动 reload,systemd 必须手动。

### 配置 schema 的 lookup 机制——字段级文档

OpenClaw 的 `config.schema.lookup` 功能让你查询任意配置字段的文档:

```bash
openclaw config.schema.lookup agents.defaults.model.primary
```

返回这个字段的类型、默认值、说明、示例。

**为什么需要这个?** 因为配置文件有几十上百个字段,文档再详细也不可能覆盖所有字段的每个细节。Schema lookup 从代码里直接提取字段定义(类型、默认值、校验规则),保证文档跟代码一致。不会出现"文档说默认值是 A,但代码里默认值是 B"的不一致问题。

**这跟 IDE 的 hover 提示是一个思路**——IDE 在你 hover 到一个变量上时,显示类型、文档、示例。OpenClaw 的 schema lookup 也是同样: 查询一个字段,显示类型、默认值、说明。不用翻文档,直接问系统。
