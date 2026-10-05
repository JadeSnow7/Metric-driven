# 在 Claude Code 中运行

本文件在 Claude Code 中使用本 skill 时读取，说明模型分工、子代理定义，以及 skill 规则落到 Claude Code 工具上的对应做法。规则本身仍以 `SKILL.md` 为准；这里只处理平台差异。

## 模型分工

| 角色 | 模型 | 负责 |
| --- | --- | --- |
| 主线程 | Opus 或 Fable，由用户在会话里选择 | 定档、需求澄清、拆任务与验收、架构取舍、实现合同、最终 diff 审查、整体验收、与用户沟通、有副作用的动作 |
| `veriflow-coder` 子代理 | Sonnet（定义文件固定） | 按合同实现边界清楚的子任务，返回完成回报 |
| `veriflow-reviewer` 子代理 | Sonnet（定义文件固定） | 只读的独立审查：对照合同看实际 diff、原始记录，亲自运行区分性检查 |

主线程模型由用户选择，可用 `claude --model opus`、`claude --model fable` 或会话内的 `/model` 选择。L2 任务需要委派，而当前主线程不是 Opus 或 Fable 时，在开始委派前告诉用户一次，由用户决定是否切换；同时继续已就绪的其余工作。

子代理实际使用的模型按以下顺序决定（Claude Code 2.1.272 实测）：

1. 调用 Agent 工具时传入的 `model` 参数；
2. 子代理定义文件 frontmatter 里的 `model`；
3. 环境变量 `CLAUDE_CODE_SUBAGENT_MODEL`；
4. 以上都没有时继承主线程模型。

所以调用 `veriflow-coder`、`veriflow-reviewer` 时沿用定义文件的模型，或显式传 `sonnet`。内置的 `general-purpose` 没有固定模型，会继承 Opus/Fable；子代理定义没有安装时，用 `general-purpose` 并显式传 `model: "sonnet"`，把对应定义文件的正文放进派发内容。需要确认实际模型时，无头运行的 JSON 输出里 `modelUsage` 按模型列出用量，`subagent_stats.by_type` 列出各类子代理的调用次数。

## 安装与名称

子代理定义在本 skill 的 `agents/claude-code/` 下，与 skill 一起分发。三种加载方式：

| 方式 | skill 名称 | 子代理名称 |
| --- | --- | --- |
| 仓库自带的插件目录，`claude --plugin-dir <仓库>/claude-code`，仅当前会话 | `veriflow:veriflow` | `veriflow:veriflow-coder`、`veriflow:veriflow-reviewer` |
| 复制到 `~/.claude/skills/veriflow/`，定义文件复制到 `~/.claude/agents/` | `veriflow` | `veriflow-coder`、`veriflow-reviewer` |
| 复制到项目的 `.claude/skills/veriflow/` 与 `.claude/agents/` | `veriflow` | 同上 |

调用 Agent 工具时使用它的子代理列表里实际出现的名称；列表里没有时，按上一节的办法改用 `general-purpose` 并传 `model: "sonnet"`。复制到 `.claude/` 会在项目里留下未跟踪文件；需要个人忽略配置时，写进 `.git/info/exclude`。

skill 加载时，Claude Code 在正文前给出 “Base directory for this skill”。本 skill 中的 `scripts/…`、`assets/…`、`references/…` 都相对这个目录；在别的工作目录运行脚本时写绝对路径，例如 `python3 <skill 目录>/scripts/validate_task.py …`。

## 委派

用户或适用的项目指令已允许使用子代理，且存在边界清楚、值得交出的实现时，按已有授权委派。L0 通常由主线程直接完成；项目明确要求 coder 实现时遵循该要求，记录深度仍按任务影响选择。委派前后：

1. **写实现合同。** 委派前先引用已就绪的 Spec 条目。派发内容至少包含：目标与所属任务、可写文件范围（多个 coder 之间互斥）、基线提交、按结构影响选取的设计约束（见 [design.md](design.md)）、契约来源与消费者及适用的状态/兼容语义、验收检查命令、执行记录输出路径、skill 目录的绝对路径，以及授权边界（提交、推送、共享记录由主线程管理）。把执行所需上下文与约定一并写入合同。
2. **派发。** 合同引用测试基准及实现前结果；尚未建立时先派发基准编写与运行，主线程核查后再派发产品实现，沿用同一 coder。等结果才能继续时前台运行；可以并行推进其他子任务时放到后台，结果到达并核查后再向用户转述。多个 coder 并行时，文件范围必须互斥。
3. **核查回报。** 回报只是“完成待审查”。主线程读实际 diff 和原始执行记录；记录绑定当前 revision、输出支持结论时可以直接作为证据。主线程亲自重跑整体验收和至少一个能区分错误实现的检查。
4. **独立审查。** 需要独立审查时派 `veriflow-reviewer`，只提供合同、基线和原始记录，让它自行形成结论。它的发现也是线索，主线程逐条核实后再采纳。采纳建议又改了代码时，用 SendMessage 让同一个审查子代理复核这次追加改动，它沿用之前的上下文。主线程重读如实记录为自审。
5. **回报用户并同步记录。** 每个子任务核查后在当次进度更新里告诉用户，更新 `task-summary.md`；共享记录只由主线程写。报告前检查 Spec 的每项交付物、证据和未满足项，遗漏 Spec 要求的正文、示例或运行产物时不得写完整完成。

子代理停滞或没有修改时，先检查环境状态（见下文“同步目录”），再缩小合同范围重派一次；持续无进展时由主线程实现，并在报告中写明“由主线程实现，未经独立实现与审查”。

## 规则与工具的对应

| skill 规则 | 在 Claude Code 中 |
| --- | --- |
| 读取适用的 `AGENTS.md` | 同时读取 `CLAUDE.md`、`.claude/CLAUDE.md` 及子目录中适用的同类文件 |
| 一次问完 3–5 个关键问题并给默认建议 | 可以用 AskUserQuestion 提问（每次最多 4 个问题），其余事项在同一条回复里作为默认建议列出；工具不可用时（例如无头运行）直接在回复中提问 |
| 按用户授权创建 worktree | Agent 工具的 `isolation: "worktree"` 会创建 git worktree，同样需要用户先同意；未同意时子代理在原目录按互斥文件范围工作 |
| commit、push、merge、deploy 逐项授权 | 权限模式（包括 auto、acceptEdits、bypassPermissions）、`settings.json` 的 allow 规则和 hooks 用于判断技术可执行性，动作授权依据用户指令 |
| 写入个人长期记忆需要用户同意 | Claude Code 的记忆文件（如 `~/.claude/projects/…/memory/`、`CLAUDE.md`）同样适用；只记录用户同意保存的内容 |
| 记录服务于下一次接手 | TodoWrite 等会话内任务列表用于跟踪当前进度；跨会话状态保存到 `task-summary.md`、`task-state.json` 与证据 |
| 子代理或工具的“tests passed”只是线索 | 后台任务通知、子代理最终消息、hooks 输出都一样；以实际 diff、执行记录和亲自运行的结果为准 |

## 同步目录与长时间无响应的命令

仓库在 iCloud、Dropbox 等同步目录中时，未下载的文件会让 `git status`、`git diff` 长时间阻塞。Claude Code 的 Bash 工具会把超过时限的命令转入后台，此时继续按运行中状态处理：

- 把相关检查记为 `undetermined` 并说明原因，保留工作区待核验状态；
- 可以把需要的文件复制到临时目录（例如会话的 scratchpad）中的隔离 Git 副本里实现和测试，完成后用 `scripts/integrate_boundary.py` 按逐文件哈希写回，写回前确认目标文件自复制以来没有被他人修改；
- 子代理在同步目录里停滞时，同样给它隔离副本的路径。

## 无头运行与独立评估

`claude -p` 可以在隔离目录里做前向评估，例如：

```bash
claude -p --model opus --plugin-dir <仓库>/claude-code --output-format json "<真实请求>" < /dev/null > run.json
```

- 评估目录放在临时位置，使用评估专用远端与数据；只给执行者真实请求和最少材料，让其独立形成结果。夹具里的 Git 远端、数据库等路径写成相对路径，否则复制出来的评估副本仍会改到原件。
- 需要排除本机其他 skill 和用户设置的影响时加 `--setting-sources project,local`；这也会跳过用户设置里的环境变量，认证依赖这些变量时用 `--settings <文件>` 单独传入。
- 无头模式下没有人回答问题或权限提示，被拒绝的工具调用列在输出的 `permission_denials` 中。评估需要执行命令时，用 `--allowedTools` 精确放行，或只在一次性的隔离目录中使用 `--permission-mode bypassPermissions`。
- 评估会消耗真实用量；某些模型可能需要账户额外开通（例如 Fable 返回 “requires usage credits”），运行前确认可用，结果中写明实际使用的模型。
