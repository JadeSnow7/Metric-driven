已完成，仅写入：

- `supplemental_check.py`
- `tests/test_supplemental.py`
- `README.md`

实现内容：

- 校验冻结评分器 SHA256：`6ed1a9d09fd40871b8e4e0bfed7cb2d2f64a4a3eb9f5ff762bb0566cda6fe86b`
- 通过 `importlib` 加载真实评分器，复用 `check_row` 与 `STRATEGIES`
- 实现 ch07 精确 UTF-8/J(arguments) 估算
- 深拷贝并适配合法 tool 来源消息
- 校验完整 4×4 共 16 行结果
- 输出 run/data/evaluator hash 与具体失败 check ID
- 拒绝执行失败或超时记录
- 不修改 run、fixture 或其他目录

测试结果：

- `2` 个测试通过，退出码 `0`
- 原始输出已保存：
  - `/tmp/supplemental-tests.stdout`
  - `/tmp/supplemental-tests.stderr`
- 冻结评分器哈希再次校验一致。