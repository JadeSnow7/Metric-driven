# evaluator-v4 交接

最终 evaluator 位于 `/private/tmp/rein-ch08-evaluator-v4/evaluator.py`，归档同目录 `evaluator.py`。接口为 `--repo --data --output`，可选 `--command-json`；默认 command 为 `npm run --silent ch08:compare --`，参数只按实际场景追加 `--data-root`、`--budget 0` 或 `--strategy summary`。

动态校准使用统一 toy command，真实执行并保存每次 argv、cwd、UTC epoch 起止时间、退出码、超时、原始 stdout/stderr、输入 hash 和 source hash。default、budget0、mutated 均完成 16 行；duplicate metadata 与 path escape 真实退出非零；missing doc-01 的 summary task-01 返回 error 行。输出目录拒绝覆盖；超时使用独立进程组并避免 partial bytes 重复写入。

验证 check IDs 包括 `CHECK_EXACT_4X4`、`CHECK_RULES_QUESTION_PRESERVED`、`CHECK_ESTIMATE`、`CHECK_CLAIM_GROUNDED`、`CHECK_QUALITY_EXACT`、`CHECK_UNKNOWN`、`CHECK_BUDGET_ZERO_EMPTY`、`CHECK_DUPLICATE_METADATA_REJECTED`、`CHECK_MISSING_ERROR_ROW`、`CHECK_PATH_ESCAPE_REJECTED`。失败会写 `summary.json` 的 `failed_checks`，不会以 traceback 代替审计结果。

TS/Rust 算法真实性、真实 StdioExecutor records、正文跟做与独立评审仍需正式产物评审；本 toy 仅校准 evaluator 外部协议和动态变异检查。
