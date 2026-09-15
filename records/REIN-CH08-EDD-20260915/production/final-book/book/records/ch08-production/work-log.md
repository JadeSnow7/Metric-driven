# Work log

## EVENT-001 — preparation

- 2026-09-15：确认 production HEAD 为 `1dfa82b9d90196c2294f61914d2017449e5548e3`；原书 worktree 为 `dirty_dependency_confirmed`。
- 读取冻结 skill、records/metrics-and-evidence/delegation references 及 `validate_task.py`、`integrate_boundary.py` 接口。
- 计算 common→production（排除 `node_modules` 与生成的 `docs/.vitepress/dist`）共 18 个产品差异；另保留 8 个 `fixtures/ch08-context/**` 只读路径。
- 当前未运行最终 acceptance；所有门槛保持 `undetermined`。本轮未回写原书、未 commit/push/deploy。
- 末次复核发现 `rust/tests/ch08_context.rs` 与 `scripts/ch08-verify.mjs` 相对草稿 source SHA 已漂移；保留草稿值并将其标为待最终稳定后重建，未覆盖来源。

## EVENT-002 — pre-final record correction

- 2026-09-15T10:54:06Z：将 `task-state.json` 的占位 `prepared_at` 替换为本次修订的实际 UTC 时间；旧值封存在 `history/task-state-pre-final-20260915.json`，不作为执行证据。
- 2026-09-15：生产源码修复缺失文件错误路径的 `selectedSources` 误报，并在同一测试中加入命中候选后正预算失败记录与零预算无调用断言；本变更等待主线程协调的终版 Cargo 验证，未在本代理运行 Cargo。
- 2026-09-15：源码与正文冻结后，重建 `production/delivery/manifest.json` 与 `file-hashes.json`，精确列出 26 个常规文件，所有源哈希均为当前值，目标不存在项明确记为 `absent`；只读预检通过，未执行整合。
