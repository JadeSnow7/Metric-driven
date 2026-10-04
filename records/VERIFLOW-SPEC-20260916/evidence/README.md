# 验证证据导航与历史边界

本目录保留基线、失败、中间稿和最终验证，不把所有 exit 0 混为最终验收。

- `baseline-*`：修改前的工具回归和实测反例；`source-git-probes.json`、`baseline-manifest.json`、`preexisting-tools.patch`：现场基线。
- `interrupted-draft/`、`coder/`：首位实现者被中断前的中间稿与一次只到 record 的有限运行。不是最终实现，也不是 SC-07 全流程证据；保留原样。
- `docs-review-v2.md`、`auth-review-v1.json`：主线程发现的实际问题。后续通过不抹去这些失败。
- `auth-coder/test-output.txt`、`auth-coder/execution-log.json` 是代理最初整理的转录，不作为独立原始进程证据。`execution-v3.json` 是后续实际捕获；主线程另有 `primary-authorization-tests.json`。
- `auth-coder/tool-observed-v2-failure.json` 保留曾被执行者覆盖的 v2 失败内容，来源是主线程已经读取的工具输出；不是重新运行记录。
- `primary-history-probe.json`、`primary-fixture-probe.json`：工具初版的主线程实测，后者包含符号链接更换目标未被识别的反例，不能当作该问题已修复。

最终裁决以本轮 REPORT.md 指定的最终输入哈希与验证记录为准。日志中临时目录可能已清理；原始输入、可重跑测试和快照清单用于追溯。

`spec-coder/e2e.py` 与其 01–05 日志同样属于未通过主线程审查的初稿：无真实 acceptance/resume/action 闭环；其退出 0 不能代表本轮 E2E 成功。最终全流程改用 primary_e2e.py 的实际运行记录。
