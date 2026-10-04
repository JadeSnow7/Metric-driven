# TASK-008 当前摘要

目标：为 Inventory 增加 `remove_item(name, quantity)`，库存不足抛 `ValueError`，降到 0 时删除商品。

状态：`verified`，指第三轮运行结束时的历史交付状态。本摘要依据[已有摘要](../../../facts/case-6/raw/repo/records/TASK-008/task-summary.md.txt)更新；本轮仅整理报告，未重新开发、测试或执行 Git 操作。[交付回复](final_reply.md)说明了修复行为及原因。

验证依据来自[当时代理整理的执行轨迹](../../../facts/case-6/raw/transcript.md.txt)，并非完整工具原始日志：

| 检查 | 历史结果与范围 |
| --- | --- |
| 旧摘要的通过结论 | `stale`；缺少原始输出与版本绑定，不能用于当前版本验收 |
| 修复前重新检查 | `failed`；12 项中 `test_remove_item_to_zero_deletes` 失败，退出码 1 |
| 修复后完整测试 | 记录为 `passed`；12 项通过，退出码 0 |
| 手动边界检查 | 记录为 `passed`；剩 1 保留、归 0 删除、删除后再入库；库存不足、未知商品、数量为 0 或 -1 均抛 `ValueError`，且库存不变 |

移除未知商品和非正数量没有单元覆盖；相关行为仅有上述手动检查。未经独立审查。远程 CI 未核实。

可在对应历史项目检出目录复跑完整测试（本轮未执行；关闭字节码写入）：

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -t . -v
```

基线为 `de14e0be45b1f5875583d8fcf4741488ce00f48a`，历史提交为 `b7a79dc94ea2ae89db7f491ff642f8f2538cee0d`。执行轨迹称，提交内容与被测内容一致；[历史 Git 状态](../../../facts/case-6/raw/git_state.md.txt)记录代码和测试已提交，但 `records/TASK-008/task-summary.md` 仍未跟踪、未纳入提交，不能称整个工作区干净。

当时用户授权了 commit，未授权 push；历史授权不适用于本轮执行。当前供用户审阅修复和更新后的摘要，推送与否待用户决定，无需重复提交已有修复。
