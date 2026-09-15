# Codex 路由预检（非正式实验）

执行目录为 `/private/tmp/rein-ch08-route-preflight/empty`，仅要求 coder 执行 `pwd` 后结束。实际 argv、JSONL session 审计、stderr 和 usage 保存在 `/private/tmp/rein-ch08-route-preflight/run/`。

结果：退出码 0；session `01a0a31d-5005-7501-9104-1c68198096f6`；JSONL 显示唯一命令为 `/bin/zsh -lc pwd`，输出路径与执行 cwd 一致；终态为 `turn.completed`。usage 原样保留：input 39819、cached input 29184、cache write 0、output 99、reasoning output 27。argv 明确包含 `--ignore-user-config`、`--json`、`--approve-for-me`、`-m gpt-5.6-luna`、`model_reasoning_effort=medium`、`-C` 和 `-`，未使用 `--ephemeral`，未关闭 sandbox/rules。

这是启动路由与 session 审计预检，不属于正式 A/B/C，不计入成绩或正式成本。
