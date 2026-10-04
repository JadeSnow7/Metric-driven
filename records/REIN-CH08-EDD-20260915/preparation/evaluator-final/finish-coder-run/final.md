已完成校准。

修改：

- `toy_cli.py`
  - 修复 frozen mutant 在 budget0 `answer=None` 时崩溃。
  - 仅在真实 CBOR completed 行上修改 messages、claim、rawAnswer，并重算预算。
- `test_eval.py`
  - 真实调用同一 evaluator/toy。
  - 校验正例、unknown、window 低分、多来源、sentinel。
  - 校验 11 个 mutant 的指定 check ID。
  - 生成完整 `calibration-summary.json`，含 argv、时间、exit、stdout/stderr、run 路径及 hashes。
- `calibration-summary.json`
  - 已更新为完整 11 mutant 实际结果。

结果：

- `python3 -m unittest -v test_eval.py`
- 5 tests passed
- 11 mutants 全部实际退出码为 1，并命中指定 check ID。
- `evaluator.py` 未修改，SHA256 仍为：
  `6ed1a9d09fd40871b8e4e0bfed7cb2d2f64a4a3eb9f5ff762bb0566cda6fe86b`

所有历史失败校准目录均保留，未启动正式组。