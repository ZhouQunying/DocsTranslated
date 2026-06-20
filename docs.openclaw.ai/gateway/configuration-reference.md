# Configuration reference

## 架构精读

> 跳过不影响阅读翻译正文。

### 多实例隔离

**问题**: 同一台机器跑多个 Gateway,如何隔离?

**方案**: 每个 Gateway 独立:
- **配置目录**: `--config-dir` 参数
- **数据目录**: session、auth、workspace
- **监听端口**: 不同端口

**洞察**: 通过不同 `--config-dir` 启动,每个 Gateway 读自己的配置,互不干扰。

**权衡**:
- ✓ 隔离: 数据不共享
- ✗ 资源: 多个 Gateway 消耗更多资源

**模式**: Docker `--data-root`——多个 daemon 用不同 data root 目录隔离。

**场景**:
- 开发 vs 生产: 测试模型 vs 正式模型
- 多租户: 每个用户/团队一个 Gateway
- 不同用途: coding agent vs support agent

### gateway.tls

**问题**: Gateway 需要反向代理 (nginx) 来做 TLS 终结吗?

**方案**: Gateway 可以直接终结 TLS:
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

**洞察**: Gateway 自己终结 TLS = 一个进程搞定,不需要 nginx。

**权衡**:
- ✓ 简单: 不需要额外组件
- ✗ 功能少: 没有负载均衡、rate limiting、WAF

**何时不用 Gateway 终结 TLS**: 大规模部署,用反向代理 (Caddy、nginx、ALB)。

### gateway.reload

**问题**: 配置热更新的行为如何控制?

**方案**: `gateway.reload` 控制:
- **检测间隔**: 多久检查一次配置文件变更
- **自动 reload**: 检测到变更后是否自动热更新
- **reload 策略**: 哪些字段可热更新

**洞察**: 生产环境可能想手动 reload (改完确认无误再 reload),开发环境自动 reload 更方便。

**权衡**:
- ✓ 自动: 方便,改了立刻生效
- ✗ 风险: 可能误操作

**模式**: systemd `daemon-reload`——改了 unit 文件后需 `systemctl daemon-reload`。区别: OpenClaw 可自动 reload,systemd 必须手动。

### 配置 schema lookup

**问题**: 配置字段太多,文档覆盖不全?

**方案**: `openclaw config.schema.lookup` 查询字段文档:
```bash
openclaw config.schema.lookup agents.defaults.model.primary
```
返回: 类型、默认值、说明、示例。

**洞察**: Schema lookup 从代码直接提取字段定义,保证文档跟代码一致。

**权衡**:
- ✓ 准确: 文档 = 代码
- ✓ 完整: 所有字段都有文档

**模式**: IDE hover 提示——hover 到变量上,显示类型、文档、示例。
