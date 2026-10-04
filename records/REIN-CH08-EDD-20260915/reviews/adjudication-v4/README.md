# supplemental_check

这是冻结 ch08 评分器的只读裁决辅助包装器，不替换原评分结果，也不写入 `--run` 或资料目录。

```sh
python3 supplemental_check.py --run /path/to/run.json --data /path/to/data --budget 2400
python3 supplemental_check.py --run /path/to/run.json --data /path/to/data --budget 0
```

包装器先校验冻结 `evaluator.py` 的固定 SHA256，再通过 `importlib` 加载真实模块，复用其 `STRATEGIES` 和 `check_row`。唯一适配是使用 ch07 的 UTF-8/J(arguments) 估算，并在深拷贝中把带 `[来源:` 前缀的工具结果消息临时视为 `user`，以便冻结检查识别合法工具来源。其余字段和冻结检查均保持不变。

成功或失败均输出 JSON；失败以非零退出，并包含 `run_hash`、当前资料树 `data_hash`、`evaluator_hash` 和具体 `failed_checks[].check_id`。执行记录必须成功且未超时，结果必须是当前 `tasks.json` 的四任务×四策略完整集合。原始 run 文件哈希在检查前后必须一致。

测试：

```sh
python3 -m unittest discover -s tests -v
```
