# TASK-001 当前摘要（历史交付时点）

本摘要更新自[原摘要](../../../facts/case-10/raw/repo/records/TASK-001/task-summary.md.txt)，描述第三轮运行结束时的状态。本轮仅核对归档材料并写报告，没有重新运行测试或核验实时 Git。原始执行轨迹为当时代理整理，不能等同完整工具日志。

**状态：verified，非 completed。** 目标是批量入库并报告坏行，以及识别低库存；两项实现及本地验收有记录支持，下面五组决定仍为 proposed，测试通过不等于用户已确认。

## 范围与交付基点

- 原请求为两项功能、对应测试、跨会话记录、本地提交且不推送，见[请求记录](../../../facts/case-10/raw/eval_metadata.json)。
- 原仓库 main 从 `547ce4e` 开始，历史改动归属为 `inventory.py`、`tests/test_inventory.py`、`records/TASK-001/`。批量入库为 MT-001/IT-001/CHG-001，低库存为 MT-002/IT-002/CHG-002，记录为 CHG-003。源码只用标准库；原有 `add_item`、`count`、`names` 行为保留。
- [Git 采集](../../../facts/case-10/raw/git_state.md.txt)：`6d1d31b` 是代码、测试与记录提交，`6bf18c2` 是记录回执；当时工作区干净，main 领先 origin/main 2 个提交，远端仍为 `547ce4e`。未 push、merge、deploy，勿重复提交。

## 已实现契约与待确认规则

`Inventory.import_csv(path)` 接受 `str` 或 `Path`，返回成功导入行数和跳过行号列表；表头是第 1 行，同名行数量累加，`imported` 按行计。文件一次读入内存，库存仍在内存中。`low_stock(threshold=5)` 返回严格小于阈值的名称列表。

以下五组默认行为均已实现，但仍为 **proposed**，以[保留源码](../../../facts/case-10/raw/repo/inventory.py.txt)及[历史状态的 decisions](../../../facts/case-10/raw/repo/records/TASK-001/task-state.json.txt)为依据：

1. **空行**：空或仅空白的行忽略，不计入 imported 或 skipped，但占物理行号。
2. **字段与数量**：恰好两个字段；裁去两侧空白后 name 非空，quantity 必须是正 ASCII 整数字符串。拒绝 `0`、负数、`3.0`、`+3`、`1_000`、非 ASCII 数字，以及历史 Python 默认 4300 位转换上限之外的数字。name 未设长度上限。
3. **引号与隔离**：每个物理行独立解析，坏行不吞后续合法行；不支持引号内换行。未加引号字段内的双引号、闭合引号后的多余字符非法；加引号字段允许逗号，内部双引号需双写。跨行引号记录样本的两半均跳过。
4. **文件级错误**：表头必须为区分大小写的 `name,quantity`，允许 BOM 和字段两侧空白。空文件或错误表头抛 `ValueError`；读文件和 UTF-8 解码错误原样抛出。这些错误均发生在任何行导入之前，不留下部分入库。
5. **低库存默认值与排序**：默认值是字面量 `5`，不读取未被使用的 `config.LOW_STOCK_THRESHOLD`；沿用 `sorted()`，排序区分大小写。不新增 threshold 参数校验。

## 验证依据及限制

下表均为历史记录结果，环境仅 Python 3.14.6，未经独立审查。

| 检查 | 结果与证据 |
| --- | --- |
| 单元与回归 | passed：既有 9 项、新增 21 项，合计 30/30。[原始输出](../../../facts/case-10/raw/repo/records/TASK-001/evidence/EVD-002-unit-tests.txt.txt) |
| 整体端到端 | passed：混合 CSV 导入后核对计数及低库存结果。[原始输出](../../../facts/case-10/raw/repo/records/TASK-001/evidence/EVD-004-e2e.txt.txt) |
| 变异检查 | 8 种错误实现均被测试捕获，只覆盖这 8 种。[原始输出与脚本](../../../facts/case-10/raw/repo/records/TASK-001/evidence/EVD-003-mutation-check.txt.txt) |
| 构造输入计时 | 9 种约 20–40 万字符行单次测量最慢 19.32 ms，低于当时 1000 ms 门槛；不代表普遍性能或不存在其他慢输入。[原始输出与脚本](../../../facts/case-10/raw/repo/records/TASK-001/evidence/EVD-005-adversarial-timing.txt.txt) |
| 提交及推送门槛 | [执行轨迹](../../../facts/case-10/raw/transcript.md.txt)记载：提交前 local-commit 通过；提交后 push 门槛因未授权被拦下。远程 CI 没有运行。 |

可在原开发仓库根目录复跑 `python3 -m unittest discover -s tests -t . -v` 和 `python3 records/TASK-001/e2e_check.py`；样本写入临时目录，Python 可能生成字节码缓存。归档的 `.txt` 文件用于阅读，不能直接当作完整开发仓库运行。

必要失败经验：[执行轨迹](../../../facts/case-10/raw/transcript.md.txt)记载，初版逐行 `csv.reader` 会错误导入跨行记录下半行，`strict=True` 也未拦住。因此改用显式两字段引号规则解析并补测；旧实现上的新增检查出现 4 个失败后，最终实现才取得上述 30/30 结果。不要拿初版的通过记录覆盖最终契约。

## 下次接手

先读本摘要，再核验实际仓库、Git 提交和工作区、[原始证据及版本绑定](../../../facts/case-10/raw/repo/records/TASK-001/task-state.json.txt)，对照历史回执，避免重复提交。详细历史见[归档交接](../../../facts/case-10/raw/repo/records/TASK-001/handoffs/HANDOFF-001.md.txt)及[记录快照](../../../facts/case-10/raw/records_snapshot.md.txt)。

下一步是获得五组未决规则的结论：确认后才记为 accepted；若用户要求改变行为，先更新范围和验收，按影响修改测试与实现，使受影响旧证据失效，再重验和更新记录。全部决定解决且交付状态核清后，才能改为 completed。后续操作遵守恢复时最新用户指令；历史 commit 授权不延伸为新提交、push、merge 或 deploy 的授权。
