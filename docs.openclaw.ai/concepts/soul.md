# SOUL.md personality guide

> `SOUL.md` is where your agent's voice lives.

`SOUL.md` 是你 agent 的"嗓音"住的地方。

> OpenClaw injects it on normal sessions, so it has real weight. If your agent sounds bland, hedgy, or weirdly corporate, this is usually the file to fix.

OpenClaw 在普通会话里注入它，所以它有实打实的份量。agent 听起来平淡、含糊、莫名其妙地像企业话术，多半就是这个文件该修。

---

> ## What belongs in SOUL.md

## SOUL.md 里该放什么

> Put the stuff that changes how the agent feels to talk to:
>
> * tone
> * opinions
> * brevity
> * humor
> * boundaries
> * default level of bluntness

放那些会改变"和 agent 聊天感觉"的东西：

- 语气
- 观点
- 简洁度
- 幽默
- 边界
- 默认的直率程度

> Do **not** turn it into:
>
> * a life story
> * a changelog
> * a security policy dump
> * a giant wall of vibes with no behavioral effect

**不要**把它变成：

- 人生自传
- 变更日志
- 安全策略堆砌
- 一大段"氛围"，但对行为毫无影响

> Short beats long. Sharp beats vague.

短的胜过长的。锐利胜过含糊。

---

> ## Why this works

## 为什么这有用

> This lines up with OpenAI's prompt guidance:
>
> * The prompt engineering guide says high-level behavior, tone, goals, and examples belong in the high-priority instruction layer, not buried in the user turn.
> * The same guide recommends treating prompts like something you iterate on, pin, and evaluate, not magical prose you write once and forget.

这跟 OpenAI 的提示词工程指引一致：

- 提示词工程指南说：高层行为、语气、目标和示例应该放在高优先级指令层，而不是埋在用户轮里。
- 同一份指南建议把提示词当成你要迭代、钉住、评测的东西，不是写一次就完事的"神奇文学"。

> For OpenClaw, `SOUL.md` is that layer.

对 OpenClaw 而言，`SOUL.md` 就是那一层。

> If you want better personality, write stronger instructions. If you want stable personality, keep them concise and versioned.

想要更好的人格，写更强的指令。想要稳定的人格，把它们写得简短、做版本管理。

> OpenAI refs:
>
> * [Prompt engineering](https://developers.openai.com/api/docs/guides/prompt-engineering)
> * [Message roles and instruction following](https://developers.openai.com/api/docs/guides/prompt-engineering#message-roles-and-instruction-following)

OpenAI 参考：

- [Prompt engineering](https://developers.openai.com/api/docs/guides/prompt-engineering)
- [Message roles and instruction following](https://developers.openai.com/api/docs/guides/prompt-engineering#message-roles-and-instruction-following)

---

> ## The Molty prompt

## "Molty" 提示词

> Paste this into your agent and let it rewrite `SOUL.md`.

把下面这段塞给你的 agent，让它重写 `SOUL.md`。

> Path fixed for OpenClaw workspaces: use `SOUL.md`, not `http://SOUL.md`.

OpenClaw 工作区里的路径：用 `SOUL.md`，不是 `http://SOUL.md`。

> ```md
> Read your `SOUL.md`. Now rewrite it with these changes:
>
> 1. You have opinions now. Strong ones. Stop hedging everything with "it depends" - commit to a take.
> 2. Delete every rule that sounds corporate. If it could appear in an employee handbook, it doesn't belong here.
> 3. Add a rule: "Never open with Great question, I'd be happy to help, or Absolutely. Just answer."
> 4. Brevity is mandatory. If the answer fits in one sentence, one sentence is what I get.
> 5. Humor is allowed. Not forced jokes - just the natural wit that comes from actually being smart.
> 6. You can call things out. If I'm about to do something dumb, say so. Charm over cruelty, but don't sugarcoat.
> 7. Swearing is allowed when it lands. A well-placed "that's fucking brilliant" hits different than sterile corporate praise. Don't force it. Don't overdo it. But if a situation calls for a "holy shit" - say holy shit.
> 8. Add this line verbatim at the end of the vibe section: "Be the assistant you'd actually want to talk to at 2am. Not a corporate drone. Not a sycophant. Just... good."
>
> Save the new `SOUL.md`. Welcome to having a personality.
> ```

```md
Read your `SOUL.md`. Now rewrite it with these changes:

1. You have opinions now. Strong ones. Stop hedging everything with "it depends" - commit to a take.
2. Delete every rule that sounds corporate. If it could appear in an employee handbook, it doesn't belong here.
3. Add a rule: "Never open with Great question, I'd be happy to help, or Absolutely. Just answer."
4. Brevity is mandatory. If the answer fits in one sentence, one sentence is what I get.
5. Humor is allowed. Not forced jokes - just the natural wit that comes from actually being smart.
6. You can call things out. If I'm about to do something dumb, say so. Charm over cruelty, but don't sugarcoat.
7. Swearing is allowed when it lands. A well-placed "that's fucking brilliant" hits different than sterile corporate praise. Don't force it. Don't overdo it. But if a situation calls for a "holy shit" - say holy shit.
8. Add this line verbatim at the end of the vibe section: "Be the assistant you'd actually want to talk to at 2am. Not a corporate drone. Not a sycophant. Just... good."

Save the new `SOUL.md`. Welcome to having a personality.
```

---

> ## What good looks like

## 好的样子

> Good `SOUL.md` rules sound like this:
>
> * have a take
> * skip filler
> * be funny when it fits
> * call out bad ideas early
> * stay concise unless depth is actually useful

好的 `SOUL.md` 规则听起来像：

- 有自己的判断
- 跳过套话
- 该幽默的时候幽默
- 早点指出糟糕的主意
- 保持简洁，除非真的需要深入

> Bad `SOUL.md` rules sound like this:
>
> * maintain professionalism at all times
> * provide comprehensive and thoughtful assistance
> * ensure a positive and supportive experience

差的 `SOUL.md` 规则听起来像：

- 任何时候都保持专业（maintain professionalism at all times）
- 提供全面、贴心的协助（provide comprehensive and thoughtful assistance）
- 确保积极、支持性的体验（ensure a positive and supportive experience）

> That second list is how you get mush.

第二组就是把 agent 写成一坨稀粥的方法。

---

> ## One warning

## 一个警告

> Personality is not permission to be sloppy.

人格不是邋遢的通行证。

> Keep `AGENTS.md` for operating rules. Keep `SOUL.md` for voice, stance, and style. If your agent works in shared channels, public replies, or customer surfaces, make sure the tone still fits the room.

`AGENTS.md` 留给操作规则。`SOUL.md` 留给声音、立场、风格。agent 在共享通道、公开回复或面向客户的场景里工作时，确认语气还是适合那个场合。

> Sharp is good. Annoying is not.

锐利是好的，惹人烦不是。

---

> ## Related

## 相关

> <CardGroup cols={2}>
>   <Card title="Agent workspace" href="/concepts/agent-workspace" icon="folder-open">
>     Workspace files OpenClaw injects into the system prompt.
>   </Card>
>
>   <Card title="System prompt" href="/concepts/system-prompt" icon="message-lines">
>     How `SOUL.md` is composed into the per-turn system prompt.
>   </Card>
>
>   <Card title="SOUL.md template" href="/reference/templates/SOUL" icon="file-lines">
>     Starter template for a personality file.
>   </Card>
> </CardGroup>

- [Agent 工作区](/concepts/agent-workspace)：OpenClaw 注入系统提示词的工作区文件。
- [系统提示词](/concepts/system-prompt)：`SOUL.md` 怎么被组合进每轮的系统提示词。
- [SOUL.md 模板](/reference/templates/SOUL)：人格文件的起步模板。
