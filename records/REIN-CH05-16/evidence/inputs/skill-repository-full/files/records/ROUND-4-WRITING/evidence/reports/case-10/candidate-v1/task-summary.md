# 库存批量导入与低库存查询：当前摘要

截至第三轮运行结束，两个功能的历史状态为 **verified**。目标是让调用方批量入库、识别需补货的商品；五组边界决定仍为 proposed，已实现和测试通过不代表用户已确认，因此整体尚未 completed。[结构化状态存档](../../../facts/case-10/raw/repo/records/TASK-001/task-state.json.txt)

本文依据保留源码、测试输出、Git 采集记录及当时代理整理的执行轨迹更新。轨迹不是完整工具原始日志；下述验证均属历史记录，本轮仅撰写报告。

## 已实现的行为与待确认规则

[保留实现](../../../facts/case-10/raw/repo/inventory.py.txt)提供 `Inventory.import_csv(path) -> (imported, skipped)`：返回成功导入的行数与坏行行号列表，表头算第 1 行。`low_stock(threshold=5)` 返回数量严格小于阈值的商品名称，并排序。路径支持 `str` 和 `Path`，文件一次读入内存；同名行数量累加，`imported` 按行计数。

以下五组默认规则已体现在代码和测试中，仍需用户确认：

| 决定 | 当前实现 |
| --- | --- |
| 行与引号 | 每个物理行独立解析，坏行不吞后续合法行；不支持引号内换行的跨行 CSV。未加引号字段中出现双引号非法，引号后的多余字符非法；引号内逗号及双写引号可解析。 |
| 数据有效性 | 必须恰好两个字段；两侧空白裁去后，`name` 非空，数量为值大于零的 ASCII 整数字符串。拒绝 `3.0`、`+3`、`1_000`、非 ASCII 数字、零和负数；历史 Python 环境下超过 4300 位的数量跳过。名称未设长度上限。 |
| 空白行 | 忽略，不计入 `imported` 或 `skipped`，但仍占物理行号。 |
| 文件级错误 | 表头必须是区分大小写的 `name,quantity`，允许 BOM 和字段两侧空白。空文件或错误表头抛 `ValueError`；读文件及 UTF-8 解码错误原样抛出。这些错误均发生在任何行导入之前。 |
| 查询默认值与排序 | 默认阈值是字面量 `5`，没有读取未被使用的 `config.LOW_STOCK_THRESHOLD`；排序区分大小写，沿用 `names()` 的 `sorted()` 约定。阈值参数未增加校验。 |

当前实现仍是内存库存，不包括持久化或额外 CSV 列。整文件读入是当前处理方式，不能由单行耗时推断大文件内存表现。

## 为什么调整解析方式

[历史执行轨迹](../../../facts/case-10/raw/transcript.md.txt)记载：初版逐行 `csv.reader` 会把跨行记录 `"Widget\nlarge",3` 的下半行误当成合法商品 `large"` 导入。先前测试通过并没有覆盖这个错误。后续补测在旧实现上出现 4 个失败，才改为显式的两字段引号规则解析，并重新生成验证证据。这段失败经验解释了当前为何不直接换回宽松的 CSV 解析。

## 验证记录与适用范围

| 检查 | 历史结果与证据 |
| --- | --- |
| 单元测试 | 保留原有 9 项，新增 21 项，最终 **30/30 passed**，退出码 0。[原始输出](../../../facts/case-10/raw/repo/records/TASK-001/evidence/EVD-002-unit-tests.txt.txt) |
| 整体端到端 | **passed**，退出码 0；混合 CSV 导入后再查询，包含坏行、空行、重复名和跨行引号样本。导入结果为 `(5, [5, 6, 9, 10, 11, 13])`。[原始输出](../../../facts/case-10/raw/repo/records/TASK-001/evidence/EVD-004-e2e.txt.txt) |
| 变异检查 | 构造的 8 种错误实现均被测试捕获，只支持这 8 种变体的结论。[原始输出](../../../facts/case-10/raw/repo/records/TASK-001/evidence/EVD-003-mutation-check.txt.txt) |
| 构造输入计时 | 9 种约 20–40 万字符的行，单次测量最慢 19.32 ms，低于当时 1000 ms 门槛。只说明这些构造，不能推及普遍性能或其他慢输入。[原始输出](../../../facts/case-10/raw/repo/records/TASK-001/evidence/EVD-005-adversarial-timing.txt.txt) |

仅在 Python 3.14.6 验证，其他版本无法据此判定。历史轨迹记载提交前 `local-commit` 门槛通过，提交后 `push` 门槛因未授权而拦下；没有运行远程 CI，其状态未核实。改动由当时主线程阅读 diff，未经独立审查。

在实际项目根目录可复跑以下历史检查命令；本轮未执行。单元测试和 E2E 会创建临时 CSV，Python 可能写字节码缓存；E2E 数据写入系统临时目录，不改项目源码：

```sh
python3 -m unittest discover -s tests -t . -v
python3 records/TASK-001/e2e_check.py
```

## 提交回执与恢复顺序

[历史 Git 采集记录](../../../facts/case-10/raw/git_state.md.txt)显示：基线为 `547ce4e`，`6d1d31b` 提交代码、测试和记录，`6bf18c2` 提交记录回执。交付时工作区干净，`main` 领先 `origin/main` 两个提交，远端仍为 `547ce4e`；没有 push、merge 或 deploy。任务改动范围为 `inventory.py`、`tests/test_inventory.py` 和 `records/TASK-001/`。这些是历史回执，不构成本轮操作授权。

接手者先读本摘要，再核验实际 Git 状态和上述原始证据，不能把历史状态当成当前状态，也不要重复已有提交。可先在实际仓库执行只读检查：

```sh
git status --porcelain --untracked-files=all
git status -sb
git log --oneline -4
```

随后取得五组未决规则的结论；若用户要求修改，先更新行为约定和验收范围，再按影响调整实现及测试。受影响旧证据应失效，重新验证后更新记录；全部确认前保持 verified。任何后续提交、推送、合并或部署都应遵守恢复时最新用户指令，不能沿用历史提交授权。更详细的旧交接和动作记录已保留在[记录快照](../../../facts/case-10/raw/records_snapshot.md.txt)，无需重复生成状态或日志。
