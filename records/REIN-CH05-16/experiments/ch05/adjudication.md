# ch05 首轮裁决

两组于首次正常final/turn.completed封存后，才进行去标签独立评审及主线程检查。package-17对应control（arm-a），package-42对应skill（arm-b）；两位评审均未取得映射、作者报告或skill。主线程知道分组，不称双盲。

**两组核心Loop能力通过独立离线行为检查；两组完整章节交付均为failed。** 两种语言与两篇正文都存在，但存在明确缺项，不能称交付完成，也不把正常结束的遗漏改记为资源中断。生产修复从skill首轮副本另行开始，原成绩不覆盖。

| 维度 | control首轮 | skill首轮 | 依据 |
| --- | --- | --- | --- |
| 核心功能 | passed（已验证范围） | passed（已验证范围） | 两评审各自两工作区，实际搜索→根据结果读取多文件→回传下一模型请求→内容相关回答；多调用配对、工具失败、模型失败、空回复及32/4轮上限 |
| 随包完整实验/真实入口 | failed | failed | 多文件教学入口不完整；无可直接运行的REIN_*真实Loop入口。仅API可限制4轮不等于入口已交付 |
| 双语言合同/行为一致 | failed | failed | Rust交付工具schema缺path/needle；skill新事件wire字段/状态值另有差异；skill同号练习和主演示顺序不一致 |
| 完整中文教程 | failed | failed | 四篇缺前置接线与逐步实现/语言机制走读，规定的多文件及失败实验不能只凭正文完整跟做 |
| 交付测试覆盖 | failed | failed | 缺实际后续请求和两套工作区等明确要求，skill Rust仅一个Loop成功用例；独立评审探针不冒充产品交付 |
| 事件与说明对应 | failed（重放主张） | failed（明确承诺超出数据） | 不同真实请求产生相同events，事件仍可核查顺序/ID/终态；不能单独重建原请求 |
| 额外运行缺陷 | 演示Rust总结误取搜索文件名 | Rust原Replay耗尽panic | 两份独立报告及原始反例均可复现 |
| 真实服务 | not_run | not_run | 第一轮明确仅离线，实际配置/服务可用性不能由此判断 |

主线程读取两组实际变化（a8路径、b10路径）及四篇正文，确认公共输入与00–04/导航未变；逐文件核验first清单a122/b123无差异。亲自复跑skill TS类型、3项本章测试、默认/single演示均exit0，并核查两评审原始探针输出、loopback升级复跑与Replay panic exit101。见 /private/tmp/rein-ch05-main-review、两份独立证据目录。不会把自带测试成功等同完整产品通过。

## 分歧裁决

- 评审1将package-17“单文件独立模式”判failed，评审2将其单文件搜索后读取判passed。共同规格未禁止单文件演示先搜索，采纳较窄的单文件读取能力/演示passed；两包多文件交付仍failed。
- events-state被一位按可观察顺序/ID/终态判passed，另一位按完整请求重放判failed。分开记录：顺序与终态passed，单独重建原请求failed。正文重放主张超出当前数据是两评审共同复现的缺陷；不要求ch13持久化恢复。
- 失败处理文字的一般错误码说明可以passed，但完整失败实验操作步骤仍failed；skill Rust回放耗尽说明与实测相反单列failed。避免把文字准确性与跟做完整性混成一项。
- 包装缺公共基线、共享Cargo目标旧缓存、受限loopback错误均属于准备/评审环境。副本补全后hash一致、每包独立target及相应监听检查升级复跑通过，不计产品缺陷。原始失败保留，不伪称所有检查在一次完整套件中通过。

## 成本与隔离限制

control墙钟571.2943205829943秒，skill546.9885164999869秒，均包含实现、写作和自主验证，不能可靠细分则保持合并。原usage字段：control input_tokens3510086/cached_input_tokens3406592/output_tokens20388/reasoning_output_tokens2926；skill input_tokens2932184/cached_input_tokens2831872/output_tokens20625/reasoning_output_tokens2264。cached为input的一部分，reasoning是否包含于output以CLI字段定义为准，不重复累加。原字段完整保留，未计算费用或假设节省比例。评审/准备/返工成本另外记录，无法取得token写null。

可观察日志中skill读取了冻结SKILL.md，未见读取references/writing.md；control未见skill加载命令。命令审计不证明隐藏上下文绝对不存在。control曾列出共同父目录，并误写3份材料到共同父目录的docs/rust，随后在指定目录另行完成；未观察到读取另一组文件正文的命令。该隔离偏离及附带文件另存，不把错误位置的稿件补算为已交付。两组也有自行改Cargo目标与过滤测试的行为，原始失败和选择均保留。本配对作为有限探索性观察，不能作严密因果或统计推广。

## 生产决定

批准custom coder仅在新的 /private/tmp/rein-production-20260914 修复skill首轮。以 handoffs/ch05-production-repair-draft.md 的已明确产品要求及两名评审具体缺陷为完整修复清单；保留两臂first。需完成双语言实际实验、真实入口、正确schema/shared event合同、共享验收样例、回放耗尽处理、完整测试和两篇完整教程。完成后主线程审查并复跑关键场景，再做已授权真实冒烟及冻结ch05。ch06不得在此前置验收前开始。
