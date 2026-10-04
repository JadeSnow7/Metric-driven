# evaluator.py 最终修复记录

本次只修改 evaluator.py，并在 2026-09-15 完成 py_compile。修复五项：mutated 场景恢复精确 quality 与完整 `(taskId,strategy)` set 校验；只有 budget=0 才允许 `context_budget_exhausted`；output 已存在时 handler 不写入任何 summary，同时本调用新建目录的失败会写 summary；completed 行增加 list、rawAnswer、insufficientEvidence、真实 source ID 和逐行事实匹配检查。

bad-json 实际失败退出码 1，新增 output 中生成带 `CHECK_JSON_OUTPUT` 的 summary；预先存在的 summary sentinel 字节保持不变。

保留 check IDs：`CHECK_EXACT_4X4`、`CHECK_MUTATED_4X4_SET`、`CHECK_RULES_QUESTION_PRESERVED`、`CHECK_ESTIMATE`、`CHECK_CLAIM_GROUNDED`、`CHECK_CLAIM_CURRENT_SOURCE`、`CHECK_SOURCE_ID`、`CHECK_QUALITY_EXACT`、`CHECK_UNKNOWN`、`CHECK_BUDGET_ZERO_EMPTY`、`CHECK_EXHAUSTION_ONLY_ZERO_BUDGET`、`CHECK_ROW_LIST_TYPES`、`CHECK_DUPLICATE_METADATA_REJECTED`、`CHECK_MISSING_ERROR_ROW`、`CHECK_PATH_ESCAPE_REJECTED`。

当前 toy_cli 未由本任务修改；skill_update coder 需修正其 mutated quality 后，再用同一 evaluator 重新运行 positive/mutant calibration。正式组未启动。
