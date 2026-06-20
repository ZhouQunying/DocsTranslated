# Icon

## 架构精读

> 跳过不影响阅读翻译正文。

### Menu bar icon 作为状态机——视觉反馈的即时性

macOS app 的 menu bar icon 有四种状态：
- **Idle**：默认状态，静止
- **Paused**：暂停，icon 变灰
- **Voice trigger**：语音触发，icon 变化
- **Working**：agent 工作中，icon 动画

这跟 Slack 的 status icon 是一个思路。Slack 用绿色/红色/黄色/灰色表示在线/忙碌/离开/离线，用户一眼就知道对方状态。OpenClaw 的 icon 也是这样：用户不需要打开 app，看 menu bar 就知道 agent 在不在工作。

### Ear scale animation——微交互的情感设计

文档提到了 "ear scale" 动画和 "leg wiggle"（腿抖）。这些微交互不是功能必需，但增强了**情感连接**。用户看到 icon 在"抖腿"，会觉得 agent 在"思考"或"等待"，而不是一个冷冰冰的进程。

这跟 Duolingo 的猫头鹰动画是一个思路。猫头鹰眨眼、跳跃、庆祝，这些动画不影响学习功能，但让用户觉得猫头鹰"活着"。OpenClaw 的 icon 动画也是这样：让 AI agent 从抽象概念变成"有生命的存在"。

### IconState enum——Swift 的类型安全

Icon 状态用 Swift enum 定义，确保状态转换的类型安全。这跟 TypeScript 的 discriminated union 是一个思路——用类型系统防止非法状态。IconState 不能从 Idle 直接跳到 Working 而不经过中间状态，编译器会报错。类型安全不是代码洁癖，而是**防止运行时 bug**。
