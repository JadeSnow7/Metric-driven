# TASK-008 当前摘要

- 目标：为 `Inventory` 增加 `remove_item(name, quantity)`；库存不足抛 `ValueError`，库存降到 0 时删除商品。
- 状态：`verified`，指第三轮运行结束时的历史交付状态；已本地提交，未推送。本轮只复用已有摘要并整理报告，未执行开发、测试或 Git 动作。
- 基线：`de14e0be45b1f5875583d8fcf4741488ce00f48a`。
- 本地提交：`b7a79dc94ea2ae89db7f491ff642f8f2538cee0d`，包含 `inventory.py`、`tests/test_inventory.py`。记录称提交内容与被测内容一致；`origin/main` 仍为 `de14e0b`。[历史 Git 状态](../../../facts/case-6/raw/git_state.md.txt)

## 证据纠偏与修复

旧摘要记录 2026-09-12 18:40“Ran 12 tests, OK”，但缺少原始输出和版本绑定，已标记 `stale`。不能用该结论证明当前代码通过，也不能仅凭时间戳推断其对应版本。

历史恢复时，修改前完整测试 12 项中 `test_remove_item_to_zero_deletes` 失败，exit 1；库存从 2 减到 0 后仍留下 `{'apple': 0}`，`names()` 返回 `['apple']`。库存不足此前已抛错，因此 `remaining < 0` 删除分支不会触发。修复将条件改为 `remaining == 0`，恢复过程中未改既有测试内容。

## 历史验证及限制

来源为[当时代理整理的执行轨迹](../../../facts/case-6/raw/transcript.md.txt)，不是完整工具原始日志；本轮未重新运行，结论限于历史记录。

- 修复后：`PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -t . -v`，记录显示 12 项通过、exit 0。可在原项目根目录复跑该命令。
- 手动边界：剩 1 保留、归 0 删除、删除后再入库；库存不足、未知商品、数量 0 或 -1 均抛 `ValueError` 且库存不变，记录显示全部符合预期。
- 未知商品、非正数量沿用 `ValueError`；这两类移除异常仅做手动检查，无单元覆盖。保留的[测试文件](../../../facts/case-6/raw/repo/tests/test_inventory.py.txt)可供审阅。
- 历史修复未经独立审查；未取得远程 CI 验证证据。

## 交付与接手

- 历史用户授权本地 commit，已执行；push 未授权、未执行。该历史授权不适用于本轮新动作。
- 原摘要已更新为 `verified`、旧证据 `stale`，但 `records/TASK-008/task-summary.md` 仍未跟踪且未纳入提交，不能称整个工作区干净。[原摘要与记录状态](../../../facts/case-6/raw/records_snapshot.md.txt)
- 本文件复用[已有摘要](../../../facts/case-6/raw/repo/records/TASK-008/task-summary.md.txt)，补明历史证据来源与覆盖限制，供维护者审阅。
- 下一步：审阅已有修复；是否推送由用户决定。当前没有重复提交或回退的必要；接手后若要采取新动作，先核对实时仓库状态。
