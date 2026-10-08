# 第二轮：headless 原生加载复跑计划

在首轮运行前冻结，冻结文件哈希见 [frozen.sha256](frozen.sha256)。第一轮计划与结果见 [../PLAN.md](../PLAN.md) 和 [../REPORT.md](../REPORT.md)。

## 目的

消除第一轮的执行方式偏差。第一轮由子代理执行，按指令用 Read 读取 SKILL.md。本轮改用 headless `claude -p`，Skill 安装在工作区 `.claude/skills/veriflow/`，由 `/veriflow` 原生加载；同时把样本量从每组每任务 2 次提高到 5 次。

## 与第一轮相同的部分

- 分组 A/B 的 Skill 版本，见 [../harness/arms.json](../harness/arms.json)。
- 夹具、请求原文、隐藏评分器（grade v2，已校准）、流程分析器（analyze v3，已校准）。

## 与第一轮不同的部分

| 项 | 第一轮 | 第二轮 |
| --- | --- | --- |
| 执行者 | Claude Code 子代理（general-purpose） | `claude -p` 独立会话 |
| 模型 | `sonnet` 别名 → `claude-sonnet-5-5` | 显式指定 `claude-sonnet-5-5`（CLI 的 `sonnet` 别名解析为 `claude-sonnet-5`，不用它） |
| Skill 加载 | 提示要求 Read SKILL.md | 提示以 `/veriflow ` 开头，原生加载 |
| 提示 | 模板说明工作目录与限制，见 `../harness/agent-prompt.txt` | 只有 `/veriflow ` 加请求原文；工作目录即进程 cwd |
| 限制 | 只靠指令 | 工具层面禁用 `WebFetch`、`WebSearch`、`Agent`、`Task`；允许 Read/Edit/Write/Glob/Grep/Bash/Skill，权限模式 `acceptEdits` |
| 设置来源 | 会话默认 | `--setting-sources project,local`，不加载用户级插件与设置 |
| 认证 | 会话自身 | CLI 的 OAuth 登录；子进程去掉桌面会话导出的 `ANTHROPIC_AUTH_TOKEN`、`ANTHROPIC_BASE_URL`、`ANTHROPIC_API_KEY` |
| 样本 | 每组每任务 2 次 | 每组每任务 5 次，共 20 次，最多 4 个并发 |
| 成本口径 | 子代理通知的 `subagent_tokens` 等 | CLI `result` 事件的 `total_cost_usd`、`usage`、`num_turns`、`duration_ms`，原样记录，不相加 |

## 连通性检查（不计入结果）

[attempts/SMOKE-H-B](attempts/SMOKE-H-B)：B 版 Skill，提示要求只回答 Skill 第一节表格有几个档位。结果：init 事件的 skills 列表含 `veriflow`；模型零工具调用答出"3 个档位"；实际模型为 `claude-sonnet-5-5`。

原生加载的 Skill 正文不出现在 stream-json 记录里，因此"是否加载"依据 init 列表与这次检查，不逐次判断。

## 评分与停止

- 评分规则同第一轮：Q1–Q5 由隐藏评分器判定；P1–P3 只看工具调用记录。
- 每次运行最多 80 轮，20 分钟超时；超时或出错记为未完成，不重跑首轮结果。
- 原始 stream-json 记录留在仓库外；仓库只存 `harness/redact.py` 产出的脱敏记录。

## 结论边界

每格 5 个样本，仍只报告观察到的频数差异，不作因果推断或普遍结论。
