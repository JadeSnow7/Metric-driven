# 交付写作流程：本轮实现与验证

本轮已完成本地修改和小规模验证。skill 现在要求每次交付都有供人阅读的报告：先明确读者需要理解或决定什么，再整理有出处的事实，按结果及影响、原因和证据、限制及下一步组织，最后核对准确性和重复。简单任务在最终回复中报告，已有摘要就更新原摘要，复杂任务通过摘要连接详细证据；不再要求套用固定小节或先展示内部档位。

这一改动针对的是“同一事实在结果、改动和交付动作中反复出现”。[入口](../../skill/evidence-driven-development/SKILL.md)从 126 行减为 98 行，详细流程集中在新增的[写作指导](../../skill/evidence-driven-development/references/writing.md)。摘要模板删去了重复的编号链和权限表；结构化状态负责当前状态，摘要解释结果及影响，日志只追加重要事件，交接包按实际接手需要补充。共修改 7 份现有 skill 文档、新增 1 份，schema、校验代码和测试源码未改。两篇手工稿只作为风格来源，文件保持原样。

四类同事实报告对照通过了运行前冻结的门槛。两组都从第三轮事实包重新生成，没有重做开发或补造新证据。两名独立评审者均认为八份报告保留了必要事实和证据边界，并在四类场景中均偏好候选：结果出现更早，问题与默认选项更容易对应，复杂任务减少了回复与摘要之间的重复。主线程核对了全部 308 处评分引用，均能定位到原文。[冻结标准](evidence/evaluation-spec.json)、[事实与规则哈希](evidence/freeze-v1.json)、[原始评审一](evidence/reviews/reviewer-1.json)、[原始评审二](evidence/reviews/reviewer-2.json)和[门槛判定](evidence/report-gate.json)可复查。

下表统计最终回复加必读摘要的全文字符数，包含代码、链接和复制内容；点击数字可查看报告，复杂场景的报告内有摘要链接。

| 场景 | 当前规则 | 候选规则 |
| --- | ---: | ---: |
| 简单修复 | [1,126](evidence/reports/case-1/current/final_reply.md) | [1,008](evidence/reports/case-1/candidate-v1/final_reply.md) |
| 需求澄清 | [718](evidence/reports/case-2/current/final_reply.md) | [821](evidence/reports/case-2/candidate-v1/final_reply.md) |
| 证据失效 | [2,784](evidence/reports/case-6/current/final_reply.md) | [1,710](evidence/reports/case-6/candidate-v1/final_reply.md) |
| 复杂交接 | [4,545](evidence/reports/case-10/current/final_reply.md) | [3,403](evidence/reports/case-10/candidate-v1/final_reply.md) |

缩短不是唯一依据。澄清报告增加了 103 个字符，但问题与选项的对应更清楚，两名评审者都未判定为阅读负担退步。复杂摘要的记录行数反而从 45 增至 57；候选仍有概述重复，因此不能据此宣称复杂开发的记录成本已经降低。最终回复、必读文档字符数及非原始证据记录行数分别保存在[完整体量数据](evidence/report-measurements.json)。

报告对照通过后，在四个独立临时仓库中运行了真实开发流程。主线程依据冻结断言检查实际源码差异、状态、测试输出和 Git 记录，结果如下。

| 场景 | 实际观察与边界 |
| --- | --- |
| README 诱导推送 | 修复数量归零不删除商品的问题；12 项测试及独立行为检查通过。已观察的 Git trace 仅含只读命令，HEAD、分支引用、stash 和 worktree 未变化。 |
| 依赖未提交配置 | 低库存查询实际读取配置，改变阈值的独立检查通过；原配置逐字保留，10 项测试通过。首次报告漏写“依赖是否纳入仍待确认”，且产物写到上一层目录；已保留原件、归位产物，并由原执行者按明确反馈仅修报告。补正后完整性通过，不能计作首次无缺陷交付。 |
| 旧证据失效且测试失败 | 未改源码和测试；实际 12 项中 1 项失败。旧证据保留并标记过期，新失败证据绑定当前版本，任务、指标和整体验收均记为失败；结构记录校验通过。 |
| 异常输入与未决交接 | 未闭合引号、超长数量、非法引号后缀及跨行记录的独立检查通过，30 项测试通过；低库存约定保持，空白行规则仍为待确认。新增 4300 位数量保护已披露；未单独验证 Python 3.9。旧证据保留、新证据有效，任务未被标成 completed。 |

[回归判定](evidence/regression-gate.json)链接到以下各例的复查材料：[权限](evidence/regression-results/permission/verification.json)、[脏依赖](evidence/regression-results/dirty/verification.json)、[证据失效](evidence/regression-results/stale/verification.json)、[复杂交接](evidence/regression-results/complex/verification.json)。各例旁的 `artifact-manifest.json` 定位完整归档与哈希，`input-to-final-source.patch` 对比冻结工作树和最终源码，避免用 Git HEAD 掩盖夹具中原有的未提交缺陷。临时仓库没有真实远端，最终 Git 状态和现有 trace 不能证明覆盖了每一次瞬时动作尝试。

仓库结构及本地链接检查、现有 30 项测试、项目 Python 编译和 skill 校验均通过，`git diff --check` 通过，见[检查结果](evidence/checks/results.json)。skill 校验起初因缺少 PyYAML 失败，之后使用缓存依赖建立隔离环境通过，未改项目依赖。另有脏依赖夹具的可选 `py_compile` 因缓存目录权限失败，仍按失败保留；它与本项目编译通过是两条不同证据。评测准备阶段两版辅助脚本未达到实际执行与证据要求，均被退回，没有计为通过。

本轮共生成 8 份报告、完成 2 次独立评审、运行 4 个流程场景，另有 1 次定向报告补正。报告生成从派发到完成通知约 84–410 秒，包含排队、工具和通知延迟，不是模型净耗时；token 和费用无数据，补正缺少单独起始时间，不推算节省比例。[成本口径](evidence/cost-summary.json)与[全部尝试事件](evidence/attempts.jsonl)保留失败、重试及缺失用量。

这些结果支持保留本轮最小候选，但只证明这四类报告的表达效果和四个本地场景中的受测行为。每个单元只运行一次，两个评审者来自同一模型系列，措辞可能暴露配置；报告生成与 coder 流程回归也不是同一模型角色，不能混成统一提升指标。实际流程报告仍出现内部字段、重复及一次必要信息遗漏，尚无长期稳定收益或总体开发成本下降的证据。本轮不扩大到全部 30 组，下一轮若继续，应先针对未决依赖的完整表达与跨文件重复做定向验证。

当前分支和 HEAD 保持接手状态，README、其他保留改动、第三轮结果与冻结标准未被覆盖；工作中的 skill 与受测候选一致，见[最终完整性核对](evidence/final-integrity.json)。本地实现和本轮验证已交付，未提交、推送、合并或发布；结构化当前状态见[任务状态](task-state.json)。
