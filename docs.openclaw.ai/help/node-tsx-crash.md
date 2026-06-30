# Node + tsx crash

## 架构精读

> 跳过不影响阅读翻译正文。

### 崩溃场景——为什么 `__name is not a function`？

通过 Node + `tsx` 包执行 OpenClaw 时，初始化过程崩溃，抛出 `"__name is not a function"` 错误（出现在日志和认证模块）。

- **触发条件**：从 Bun 迁移开发命令后出现
- **受影响版本**：Node 25.3.0 和 22.22.0
- **疑似原因**：esbuild 的名称保留逻辑，所需工具函数在加载阶段不可用或被替换

这跟 JavaScript 的"变量提升"问题是一个思路——函数在声明前调用会报错（`ReferenceError`），但这里更隐蔽：工具函数"本应存在"但被打包工具替换或删除。打包工具的名称保留逻辑（如 esbuild 的 `--keep-names`）有时会"优化掉"看似无用的引用。

### 解决方案——为什么提供多种绕行路径？

文档提供多种绕行方案：

1. **切回 Bun**：本地开发工作流（Bun 不受影响）
2. **用 `tsgo` 验证类型**：然后直接执行编译后的 JavaScript 文件（绕过 tsx）
3. **禁用名称保留**：尝试在转换器中关闭名称保留功能（但当前工具链缺少此配置选项）
4. **隔离根因**：调查 LTS 环境是否也出现相同行为

这跟浏览器兼容性问题的"polyfill"是一个思路——当某个浏览器不支持某特性时，提供"降级方案"（polyfill）或"切换浏览器"（Chrome → Firefox）。多种绕行路径让"不同用户"（用 Bun 的、用 Node 的、用 LTS 的）都有可用方案。

---

Node + tsx crash: `"__name is not a function"` error in logging/auth modules when executing OpenClaw via Node with `tsx` package. Triggered after migrating dev commands from Bun, confirmed on Node 25.3.0 and 22.22.0. Suspected cause: esbuild's name-preservation logic where required utility becomes unavailable or replaced during loading phase. Resolutions: switch back to Bun for local dev workflows, use `tsgo` for type verification then execute compiled JS directly (bypass tsx), attempt to deactivate name-keeping in transformer (current tooling lacks this config option), investigate LTS environments for same behavior to isolate root cause.

Node + tsx 崩溃：通过 Node + `tsx` 包执行 OpenClaw 时，日志/认证模块抛出 `"__name is not a function"` 错误。从 Bun 迁移开发命令后触发，确认出现在 Node 25.3.0 和 22.22.0。疑似原因：esbuild 的名称保留逻辑，所需工具函数在加载阶段不可用或被替换。解决方案。切回 Bun 用于本地开发工作流。用 `tsgo` 验证类型然后直接执行编译后的 JS（绕过 tsx）。尝试在转换器中禁用名称保留（当前工具链缺少此配置选项）。调查 LTS 环境是否也出现相同行为以隔离根因。

架构精读：崩溃源于 esbuild 的名称保留逻辑"优化掉"看似无用的引用。多种绕行路径让不同用户（用 Bun/Node/LTS 的）都有可用方案。
