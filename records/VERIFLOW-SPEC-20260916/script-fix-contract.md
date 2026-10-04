# 最终脚本接入修正合同（VF-SPEC-1 不变）

写入者仅拥有 scripts/validate_task.py、scripts/record_execution.py；不得改 tests、spec_contract.py、模板或参考文档。

1. helper `receipt_paths(state)` 接收完整状态，两个调用点改正。`state.binding.receipt_paths` 是唯一正式字段。
2. revision_paths 对显式交付物不考虑 metadata/foreign/receipt 排除且包含缺失路径，fingerprint_entries 已有 deleted 标记。冲突由 validate_spec 拒绝。
3. check_execution_record 只有 current 证据与当前 Spec version/digest 比较；stale 保留原始结果/sha/旧绑定格式校验，不读旧输入也不比对当前Spec。旧1.2原始格式缺1.3字段仍按1.2审计；1.3中保留旧1.2 raw为stale允许，没有资格支撑当前条件。
4. 1.3 current 非execution证据必须有spec_version/spec_sha256与当前一致；execution以raw内字段绑定为准，outer存在却不一致也报错。不能刷新outerrevision冒充重跑。
5. record/implementation门槛返回明确spec_version/spec_sha256；implementation拒绝非空spec.open_items，但不要求交付物已生成。所有1.3 acceptance/sideeffect条件使用正确token；receipt路径从reviewcoverage的runtime脏文件排除。显式deliverables即使ignored、已提交或metadata内也需reviewed CHG覆盖。
6. 缺失历史authorization_snapshot：record/acceptance warning unknown，所有副作用门槛(local-commit,push,merge,deploy,action) error。有效快照后不再用当前source/adoption/scope追溯过去；新action检查当前授权。保留unknown/repeat/scope阻断。
7. recorder在运行前调用validate_spec拒绝畸形绑定；记录pre/post两个Spec摘要与版本（或从revision导出），前后变化不能用passed。不得命令后才发现不合法的Spec。输入身份对请求别名与canonical一致，仓库内和外的symlink alias都默认拒绝（规范化系统根/tmp→/private/tmp不误伤）。
8. 不增加复杂追踪或绕过失败。新CLI tests由另一coder维护；修代码让测试通过，发现测试违背合同立即回报，不自行弱化测试。

验证：Python3.11 + PYTHONDONTWRITEBYTECODE=1，先test_spec_binding/test_spec_model/test_evidence_history/test_authorization_snapshot，再现有test_scenarios/test_tools；新文件保存真实argv/cwd/start/end/exit/stdout/stderr，不覆盖失败。完成给实际diff和日志路径。

9. 保留已有 deferred 的公开语义：用户决定并有有效decision的延期项在acceptance/local-commit/push仍可部分交付，不把它标为Spec已满足；1.3逐条件检查不要另加无条件passed/当前evidence强制让既有规则失效。合并/部署/自定义动作照旧阻断延期强制项。gate输出可显式 `spec_satisfaction: partial` 与未满足条件列表，否则文档必须明确ok只代表对应阶段可推进。没有合法延期决定的mandatory不得靠stale/无证据绕过。
