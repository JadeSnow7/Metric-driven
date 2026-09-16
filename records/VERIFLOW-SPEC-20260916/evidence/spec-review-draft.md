# 主线程对 Spec 初稿的实际审查

状态：未通过，尚未回写。所列问题由真实 diff/原始输出定位，不采信代理“64 tests 已完成”摘要替代场景证据。

1. 初始 `test_spec_binding.py` 只有 3 个辅助函数测试，未覆盖完整 1.3 CLI 正反例。最新测试代理一度将真实 `ValueError: schema 1.3 requires state.binding` 错误总结成文件不存在；原始 stderr 在 spec-tests/，主线程要求依契约直接编写新测试。
2. `check_execution_record` 对 stale 历史记录也比对当前 Spec digest，违背历史完整性与当前适用性分离。
3. `receipt_paths` 的正式模型应读 `state.binding`，脚本调用仍传 `state.spec`，需同步。
4. 显式交付文件仅存在时参与 fingerprint，missing 未入标记；外层 manual 证据缺少独立 Spec 绑定检查。
5. 初稿 E2E 并未完成验收、恢复、动作状态协作。由 primary_e2e.py 重新实际运行，不把初稿 exit 0 当成功。

所有失败和中间稿保留；最终报告引用修复后版本与真实复跑，不追改此审查记录。
