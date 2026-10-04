# 写作风格与协作规则更新

已更新现有 skill 的写作、协作规则和配套模板。写作先判断文章类型，再采用适合读者的结构；已成立的贡献直接表达，必要条件在相关位置说明。每个子任务完成后即时汇报，受影响文档在同一子任务内同步，最终由主代理审查并汇总报告。

本轮修改 8 份现有文档，基线为 `1a10fca`，开始时本仓库工作区干净。源码、schema 和测试保持不变。

## 当前进度

| 子任务 | 结果 | 后续工作 |
| --- | --- | --- |
| 写作风格复核 | 已完成：重新读取已保存的 ch04 第 1–18 行与 ch03 第 1–47 行 | 教程手法按文体采用 |
| 协作与文档同步检查 | 已完成：补上逐项汇报与产品文档同步要求 | 规则已融入入口与执行流程 |
| skill 与模板修改 | 已完成：8 份文档相互对齐 | 主代理已审查实际 diff |
| 主代理审查与验证 | 已完成：三个写作场景、结构与链接、skill 校验及 30 项测试 | 检查结果见下文 |

## 融入方式

写作先分析文章类型、读者、用途和阅读方式，再决定结构与语气。教程带读者学习和实践，技术参考帮助查询契约，设计说明解释方案，进度与交付报告帮助判断结果。各类写作共同要求事实准确、表达直接、条件有用、阅读顺畅；教程样本中的具体叙事方法按教学场景采用。子任务完成后立即报告；代码或约定改变时，同步更新相关文档，主代理负责共享摘要和最终汇总。

- [写作指导](../../skill/evidence-driven-development/references/writing.md)：增加文体判断和类型参考，区分事实核验与正文表达，说明必要条件的取舍及实时同步时机。
- [skill 入口](../../skill/evidence-driven-development/SKILL.md)、[协作规则](../../skill/evidence-driven-development/references/delegation-and-handoffs.md)与[执行流程](../../skill/evidence-driven-development/references/workflow.md)：明确子任务逐项回报、主代理核查并更新进度、最终统一汇总的责任。
- [任务摘要模板](../../skill/evidence-driven-development/assets/templates/task-summary.md)、[交接模板](../../skill/evidence-driven-development/assets/templates/handoff.md)与[写作交接模板](../../skill/evidence-driven-development/assets/templates/writing-handoff.md)：纳入文体、进度和文档同步信息，空项空节省略。[README](../../README.md)同步能力说明。

实时同步以行为或约定变化为触发点：在该子任务结束、汇报或交接前完成受影响文档的更新。共享文档由指定所有者串行维护；实现随后变化时，关联说明和失效检查一起更新。

## 手工样本与写作结论

用户重新保存后，本轮重新读取 `/Users/huaodong/workspace/Agent-Learning/docs/chapters/04.md` 第 1–18 行，并补充 `docs/chapters/03.md` 第 1–47 行。此前读取的旧 ch04 开篇已退出风格分析。源文件只读。

| 写作习惯 | 样本依据 | 对 skill 的影响 |
| --- | --- | --- |
| 从熟悉场景进入 | ch04 第 14 行承接前三章；ch03 第 14 行从代码助手读文件切入 | 先让读者理解正在解决的问题 |
| 沿因果引入方案 | ch04 第 14–16 行从接口差异推到统一协议；ch03 第 43–47 行解释工具调用的必要性 | 解释为什么，再说明怎么做 |
| 直接说明贡献与目标 | ch04 第 18 行写明客户端和响应形式 | 用准确的目标、实现和验证状态组织表达 |
| 先观察再命名 | ch03 第 16–18 行从实验引出 Harness | 让术语解释读者已经看到的现象 |
| 带读者完成实践 | ch03 第 24–39 行给出目录、文件、请求和输出 | 将步骤与可观察结果连接起来 |
| 保留有用条件 | ch03 第 24、26 行分别处理缺依赖和同名文件 | 条件应对应具体判断或动作 |

上表的叙事特征来自教程类书籍，不是所有技术文档的通用结构。用户进一步明确：实际写作必须先分析文章类型。README 也应按入口、概览或快速上手等实际用途判断；混合文档按章节角色安排。

“显然”“必须”“只需要”不单独成为写作规则；借鉴其直接表达和因果推进，技术前提仍按事实核对。写作参考不构成可发布技术结论。

样本还提供了两个文档同步核对点：ch03 第 26 行创建 `hello.md`，第 36 行请求 `hello.txt`；ch04 第 18 行新增客户端及流式目标，需要与章节后文和实现对齐。它们用于说明同步检查应发现什么，本轮不修改 Agent-Learning。

## 检查结果

| 检查 | 结果与证据 |
| --- | --- |
| 文体、表达与进度场景 | 独立写作者完成教程开篇、进度与文档替换稿、命令参考；主代理逐项核对 [实际输出](evidence/forward-output.md) 与 [审查依据和结论](evidence/forward-review.md) |
| 仓库结构与本地链接 | 通过，见 [原始输出](evidence/repository-check.txt) |
| skill 格式校验 | 通过，见 [原始输出](evidence/skill-check.txt) |
| 现有测试 | 30 项通过，见 [原始输出](evidence/unit-tests.txt) |
| 最终 diff 与受测版本 | 主代理已审查 8 份文档；`git diff --check` 通过；隔离受测 skill 与工作区版本一致 |

写作检查使用虚构材料，验证文体选择与状态表达；真实开发中的持续同步效果需要在实际使用中观察。本轮没有把写作演练计作开发流程运行。

在仓库根目录可复跑：

```bash
python3 tools/validate_repository.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s skill/evidence-driven-development/tests -v
git diff --check
```

本机 skill 校验使用已有、包含 PyYAML 的隔离环境：

```bash
/private/tmp/edd-round4-validation-3dn2ce8c/venv/bin/python3 /Users/huaodong/.codex/skills/.system/skill-creator/scripts/quick_validate.py skill/evidence-driven-development
```

逐项完成与修订过程见 [工作日志](work-log.md)。本报告由主代理维护并汇总。
