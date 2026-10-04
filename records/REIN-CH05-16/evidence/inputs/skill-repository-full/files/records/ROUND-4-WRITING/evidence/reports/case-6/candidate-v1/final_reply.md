库存归零后仍保留商品的问题已修复，并在当时完成本地提交 `b7a79dc`，包含 `inventory.py` 和 `tests/test_inventory.py`；未推送，`origin/main` 仍为 `de14e0b`。[历史提交状态](../../../facts/case-6/raw/git_state.md.txt)

旧摘要声称 12 项通过，却没有原始输出或版本绑定，不能证明当前代码通过，也不能靠时间戳判断它验证了哪个版本。当时重新检查发现 `test_remove_item_to_zero_deletes` 失败：扣完库存仍留下 `apple: 0`。原因是库存不足已提前抛错，原来的 `remaining < 0` 删除分支不会触发；恢复时将条件改成 `remaining == 0`，没有修改既有测试内容。[执行轨迹](../../../facts/case-6/raw/transcript.md.txt)

历史记录显示，修后完整 12 项测试通过，手动边界检查也符合预期；这些是导入的历史结果，本轮没有重新运行。移除未知商品和非正数量仍抛 `ValueError`，这两类仅有手动检查，没有单元覆盖，且未经独立审查。已复用更新 [任务摘要](task-summary.md)，保留验证范围、复跑命令和旧证据失效状态，供审阅；是否推送由用户决定。
