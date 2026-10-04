## 结果

TASK-008 已修复“库存归零仍保留商品”的问题，并在历史交付时完成本地提交 `b7a79dc`；未推送。旧摘要的“12 项通过”已标记为 `stale`：它没有原始输出和版本绑定，不能证明当前代码通过，也不能凭时间戳确定验证的是哪个版本。

以下验证均来自[当时整理的执行轨迹](../../../facts/case-6/raw/transcript.md.txt)，并非本轮重新运行；该轨迹不是完整工具原始日志。

## 改动

- `inventory.py`：将删除条件从 `remaining < 0` 改为 `remaining == 0`。库存不足会提前抛错，原删除分支不会触发，导致移除全部库存后留下 `{'apple': 0}`。
- 本次历史恢复没有修改既有测试内容；本地提交包含 `inventory.py` 和此前已有改动的 `tests/test_inventory.py`。[保留的代码与提交差异](../../../facts/case-6/raw/git_state.md.txt)

## 验证

| 检查 | 命令或方法 | 历史记录结果 |
| --- | --- | --- |
| 修复前完整测试 | `python3 -m unittest discover -s tests -t . -v` | failed：12 项中 `test_remove_item_to_zero_deletes` 失败，exit 1 |
| 修复后完整测试 | 同上；实际执行附带 `PYTHONDONTWRITEBYTECODE=1` | passed：12 项通过，exit 0 |
| 手动边界检查 | 剩 1 保留、归 0 删除、删除后再入库；不足、未知商品、数量 0 或 -1 | 记录显示符合预期；异常均抛 `ValueError` 且库存不变 |

在原项目根目录可复跑：`PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -t . -v`。

## 未完成与风险

未知商品和非正数量沿用 `ValueError`，这两类移除异常仅有历史手动检查，没有单元覆盖；本次历史修复未经独立审查。未取得远程 CI 验证证据。

## 交付动作

记录显示提交内容与被测内容一致；`origin/main` 仍停在 `de14e0b`，未推送。[历史 Git 状态](../../../facts/case-6/raw/git_state.md.txt)

已有摘要当时已更新为 `verified`、旧证据为 `stale`，但仍未跟踪、未纳入提交。本轮复用并更新为供审阅的 [task-summary.md](task-summary.md)，仅整理报告；无需重复提交。下一步是审阅修复，是否推送由用户决定。
