# 真实序列化形状未覆盖，等待v3纠正

v2已通过其记录的测试和主线程snake_case手算样本，但真实共同Rust Message的Serde字段是toolCallId/toolCalls，v2仅计算内部snake_case。因此其对Quartz/Larch的CHECK_ESTIMATE不能作为最终产品判断；root-supplemental/default原始结果保留、暂不采纳。Slate无工具字段的结果也会统一按修正版本复核。

共同基线 rust/src/rein/mod.rs:18-24 是修正依据，不改变产品规格。v3在独立目录处理actual camelCase和仅tool来源的完整正例；原始评分器、v2、所有首轮产物保持不变。额外返工单列为主线程/评测准备负担。
