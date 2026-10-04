# 指标、证据与机械门槛

## 三类指标

| 类型 | 用途 | 失败影响 |
| --- | --- | --- |
| `mandatory_gate` | 必须满足的功能、安全、兼容或交付门槛 | 阻止相应阶段 |
| `improvement_target` | 希望相对基线改善的效果 | 未达成时回到假设/取舍，不自动伪装成功 |
| `non_regression` | 不得恶化的既有行为或资源约束 | 阻止相应阶段，除非用户明确变更需求 |

每项 `MET-*` 至少写：

- **基线**：已测值、现有行为，或“未知；先执行哪项测量”；
- **目标/门槛**：可观察条件；没有依据时用可复现的定性门槛，不编造百分比；
- **方法**：命令、步骤、比较方式或人工核验方法；
- **环境与数据**：版本、配置、fixture、样本范围；
- **证据**：`EVD-*` 与仓库内路径；
- **状态**：`passed`、`failed` 或 `undetermined`。

“可检测”不等于所有结果都必须数字化。视觉、可用性或需求一致性可用截图、审阅清单、结构化观察和人工签字，但必须能说明谁在什么环境看到了什么。

## 改善假设与停止条件

性能、算法和探索性改动用 `HYP-*` 写明机制：为什么这项改动应影响哪个指标。再写预算与退出条件，例如最多两轮实现、20 分钟基线测量、或样本达到某规模即停止。

若假设不成立：停止继续修补，保留失败证据，选择回退、缩小范围或重新决策。不要用新增复杂性掩盖没有收益。

## 证据要求

证据可以是测试输出、基准结果、截图、日志、审阅记录或远程回执。原始证据文件放在 `records/<TASK-ID>/evidence/`。每项至少包含：

- 证据 ID、路径、类型和观察时间；
- 支持的指标/改动；
- 结果 `passed` / `failed` / `undetermined`；
- 当前性 `current` / `stale`；
- 与当前仓库状态匹配的 revision token；
- 证据文件原始字节的 `sha256`，用于发现证据在记录后被改写。

放在 `evidence/` 目录外的证据（例如仓库内既有的基准报告）会计入 revision 指纹：新增或修改它会让其他证据一起过期，校验器会给出 `EVIDENCE_OUTSIDE_RECORD_DIR` 警告。

代理回复“tests passed”不是证据。主线程应检查命令、原始输出、退出码、环境和实际 diff。若无法复现，标记 `undetermined`。

## Revision token

`validate_task.py --print-revision` 从任务基线到当前工作树计算只读内容指纹（`revision-v2`）。它取基线以来发生变化的路径（含未跟踪文件，重命名按“删除原路径 + 新增新路径”处理），逐个记录路径、文件类型/可执行位，以及按 Git 清理过滤器和换行规则得到的内容哈希。因此：

- 暂存或提交改动不会改变 token，本地提交后证据仍保持当前；
- `diff.noprefix`、`diff.algorithm` 等本地 diff 配置和 CRLF/LF 检出差异不影响 token；
- 非记录内容的任何实际变化都会改变 token。

把 `task-state.json` 放在专用子目录（建议 `records/<TASK-ID>/`）时，为避免保存状态或新增证据使已有证据自我失效，它固定排除同目录的 `index.md`、`task-summary.md`、`work-log.md`、`handoffs/`、`evidence/` 和状态文件本身。若状态文件直接位于仓库根目录，则只排除状态文件，避免根目录真实交付物与保留名称撞名。

```bash
python3 scripts/validate_task.py records/TASK-001/task-state.json --repo . --print-revision
python3 scripts/validate_task.py records/TASK-001/task-state.json --repo . --print-sha256 records/TASK-001/evidence/unit-tests.txt
```

把 revision 输出写入相关 `evidence[].revision` 与 `changes[].revision`，把 sha256 输出写入 `evidence[].sha256`。验证后再修改代码或测试，应重新运行受影响检查并更新 token；证据文件被改写会导致 sha256 失配，需要重新执行产生该证据的检查。指纹基于工作树内容，提交前应确认暂存区与工作树一致，否则提交内容可能不同于被验证的内容。被排除的记录文件若要提交，仍必须出现在已审查的 `CHG-*.paths` 中；排除只影响证据指纹，不绕过实际 diff 范围检查。该指纹证明“所引用的非记录仓库内容没有改变”，不证明证据结论正确，也不取代最终提交 SHA/远程回执。

## 门槛检查

```bash
# 结构与引用
python3 scripts/validate_task.py records/TASK-001/task-state.json --repo . --gate record

# 是否可开始实现
python3 scripts/validate_task.py records/TASK-001/task-state.json --repo . --gate implementation

# 是否满足本地提交门槛
python3 scripts/validate_task.py records/TASK-001/task-state.json --repo . --gate local-commit

# 后续动作门槛
python3 scripts/validate_task.py records/TASK-001/task-state.json --repo . --gate push
python3 scripts/validate_task.py records/TASK-001/task-state.json --repo . --gate merge
python3 scripts/validate_task.py records/TASK-001/task-state.json --repo . --gate deploy
```

脚本从不执行 Git 写操作或外部动作。它只检查记录与本地状态的一致性：

- `implementation`：需求已就绪，主任务和指标已建立，基线为 `clean` 或已确认归属的 `dirty_dependency_confirmed`，记录中不再含模板占位符；
- `local-commit`：强制门槛、非退化约束、整体验收、当前证据（含 sha256）、改动审查与 commit 授权均满足；
- `push`：本地提交已记录完成、除任务记录文件外 worktree 干净且 push 已授权；
- `merge`：push 完成、远程 CI 实际通过且 merge 已授权；
- `deploy`：merge 完成、恢复策略存在且 deploy 已授权。

`local-commit` 还会把基线以来的实际变更路径与所有 `reviewed` 的 `CHG-*.paths` 对照；未被覆盖的文件会阻断提交。重命名的原路径和新路径都必须被覆盖。`paths` 使用仓库相对的精确文件或目录，不支持 glob。

恢复时，如果目标动作在 `delivery` 中已是 `completed`，或存在 `authorization_action` 相同且 `completed` 的 `ACT-*`，相应门槛会阻止重复执行并要求先核验实际状态。

部分检查的严重程度随门槛升高：

| 检查 | `record` | `implementation` | `local-commit` | `push` / `merge` / `deploy` |
| --- | --- | --- | --- | --- |
| 模板占位符 `PLACEHOLDER_VALUE` | 警告 | 错误 | 错误 | 错误 |
| 缺少 `evidence[].sha256` | 警告 | 警告 | 错误 | 错误 |
| 已执行却未授权的动作 `ACTION_UNAUTHORIZED` | 警告 | 警告 | 警告 | 错误 |

已执行却未授权的动作在早期只报警告，是为了让执行者如实记录已经发生的事；进入外部动作门槛前，必须先核验真实外部状态并与用户确认。

输出为 JSON。退出码 `0` 表示没有错误（可能有警告），`1` 表示记录或门槛错误，`2` 表示运行错误（例如 `--repo` 不是 Git 根目录或状态文件无法读取）。

机器门槛失败时保留具体错误。不得通过删除指标、改状态或修改测试来迎合脚本；只有真实需求变化可经来源和决策记录调整门槛。
# Actual execution records

For command evidence, run `python3 scripts/record_execution.py --output records/TASK/evidence/run.json --cwd . --source src/app.py --test tests/test_app.py --fixture tests/fixtures/input.json -- python3 -m unittest tests.test_app`. The record stores the exact argv, cwd, timestamps, exit code, raw output and input hashes; an empty stdout is valid unless `--require-stdout` is supplied.
