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
- **验证方式** `verification`：`execution`（默认，由命令执行记录判定）或 `manual`（截图、审阅清单、人工观察等）；
- **环境与数据**：版本、配置、fixture、样本范围；
- **证据**：`EVD-*` 与仓库内路径；
- **状态**：`passed`、`failed`、`undetermined`，或经用户决定的 `deferred`（见下文）。

“可检测”不等于所有结果都必须数字化。视觉、可用性或需求一致性可以用 `manual`，但必须能说明谁在什么环境看到了什么；报告里要写明这是人工判定。

### 过程与边界证据

测试基准在产品实现前建立，具体步骤见 [workflow.md](workflow.md) 的“先写测试基准”。实现前后分别保存原始记录，关联相同的 Spec 条目、用例和测量口径；实现前的失败是现状证据，不能充当实现后的通过证据。产品变化后，旧记录按既有规则标为 `stale` 并保留用于比较，不刷新其 revision 冒充当前验收。只有真实需求变化或已证实的测试方法缺陷才调整预期、断言或阈值，记录原因、影响并重验；不能为让实现通过而降低标准。性能比较还须保持环境、数据和采样方法可比，无法保持时明确比较限制。

#### L2 实现前证据的记录方式

`MET-*.baseline` 只写起点描述，可引用实现前证据的 `EVD-*`；原始结果放在执行证据里，不另建字段或状态体系：

1. 在未修改的产品上用 `record_execution.py --state` 运行基准，把记录登记为 `evidence` 条目：`supports` 指向对应指标，`result` 按实测填写（缺陷复现通常是 `failed`）。
2. 实现前证据**不放进**指标、`IT-*`、`CHG-*` 或 `overall_acceptance` 的 `evidence_ids`。这些列表只引用支持当前判定的证据。
3. 产品改动后，把该条目改为 `status: stale`，`stale_reason` 写明“实现前基准”，原文件与 sha256 保持不变。
4. 实现后用同一命令重新记录，新证据进入 `evidence_ids` 并支持判定。

把实现前证据列入 `evidence_ids` 会触发 `METRIC_EVIDENCE_NOT_CURRENT`，指标已判 `passed` 时还会触发 `METRIC_EVIDENCE_RESULT`。校验器不判断基准是否早于实现；审查者对比实现前证据的 revision 与产品改动，确认预期、断言和阈值没有在实现后放宽。

```json
{"id": "EVD-PRE-001", "path": "records/TASK-001/evidence/pre-met-001.json", "kind": "execution",
 "supports": ["MET-001"], "status": "stale", "stale_reason": "实现前基准；产品已修改",
 "result": "failed", "observed_at": "2026-01-01T00:00:00Z", "sha256": "<记录文件的 sha256>"}
```

当成功条件涉及“触发、拒绝、隔离、回退”或流程质量时，先证明输入到达被测入口，再证明实际走过的分支；只看到最终产物或提示文本不能反推过程。转录可以作为来源明确的二手过程材料，但不能冒充原始日志，结论按证据强度限缩。记录观察对象（调用、事件、日志、状态或资源）、样本是否非空且有效，并把执行者主动运行、主线程补做和系统自动触发分开标注。对高风险或复杂行为，正向样本应配合负向对照或反例；拒绝/隔离检查要覆盖异常残余之后紧接的合法记录，避免残余被误当成下一条输入。缺少这些材料时限缩结论或记为 `undetermined`，不补造时序或工具日志。

单个输入只支持该输入在该环境下的观察，不能概括所有输入、分支或运行路径。例如空错误集合上的 `all(...)` 即使通过，也不能证明故障被触发；只运行包装层不能证明真实子进程路径。对报告中的概括性行为断言，选择针对输入核实，结论限于实际覆盖范围。

## 改善假设与停止条件

性能、算法和探索性改动用 `HYP-*` 写明机制：为什么这项改动应影响哪个指标。再写预算与退出条件，例如最多两轮实现、20 分钟基线测量、或样本达到某规模即停止。

若假设不成立：停止继续修补，保留失败证据，选择回退、缩小范围或重新决策。不要用新增复杂性掩盖没有收益。

## 环境不可用与延后验证

缺环境、缺数据或看不懂结果时，检查就是 `undetermined`，不能算通过。`undetermined` 的强制门槛会阻止验收和提交。

只有用户明确决定“先交付、稍后验证”时，才把指标改为 `deferred`，并用 `decision_id` 指向记录该决定的 `DEC-*`。校验器的处理：

| 门槛 | `deferred` 的 `mandatory_gate` / `non_regression` | `deferred` 的 `improvement_target` |
| --- | --- | --- |
| `acceptance`、`local-commit`、`push` | 警告 `METRIC_DEFERRED`，不阻断 | 警告 |
| `merge`、`deploy`、`action` | 错误 `METRIC_DEFERRED_BLOCKS` | 警告 |

`action` 门槛用于可能先于验收发生的自定义动作（例如为验证而做的预发布迁移），因此不检查指标是否已通过，`undetermined` 或 `failed` 的强制指标不阻断它。`deferred` 表示用户已决定在验证前交付，所以强制和非退化指标一旦延期，就阻断这类难以撤销的动作，直到补验完成。

## 完整完成与部分验收

本节是整体验收、部分验收与完整完成判定的权威说明，其他文件只引用这里。

- **整体验收不能延期。** `overall_acceptance` 只用 `passed`、`failed`、`undetermined`。原定整体端到端场景须有当前通过证据；无法验证时保持 `undetermined` 并阻断验收，不能借延期指标、隐藏场景或缩小 Spec 填为 `passed`。schema 1.3 的 `overall_acceptance.metric_ids` 只列整体场景实际依赖的指标，引用 `deferred` 指标时报 `OVERALL_METRIC_DEFERRED`。
- **部分验收。** 整体场景通过、另有经用户决定延期的指标时，报告为部分验收；延期指标仍是“未验证”，写明原因与验证计划。
- **范围调整。** 用户真实调整范围时，记录决定、更新 Spec 与绑定并重验受影响内容，不追认旧证据。
- **机械判定（schema 1.3）。** `--gate acceptance` 无错误时才评估 `spec_satisfaction`：条件关联指标全部 `passed` 为 `satisfied`；未通过的条件关联指标全部为关联有效决定的 `deferred` 时为 `partial`；其他未满足情况为 `unsatisfied`。有错误或使用其他 gate 时为 `not_assessed`。条件关联的每个未延期指标都须有当前通过证据，否则报 `SPEC_METRIC_EVIDENCE_MISSING`，因此 `ok=true` 时实际只会得到 `satisfied` 或 `partial`。这条要求也适用于 `improvement_target`：即使未达成已有决定，只要它绑定在 Spec 条件上，验收仍会阻断。允许未达成的改善目标不要绑进条件，或经用户决定改为 `deferred`。
- **完整完成。** L2 任务声明完整完成须同时取得 `--gate acceptance` 的 `ok=true` 与 `spec_satisfaction=satisfied`，再由主线程逐项核对实际行为、证据支持关系和交付物内容。仍有约定未满足项时不能宣称完整完成；模板占位检查和机械字段、引用、路径放行都不替代语义验收。

## 证据要求

证据可以是执行记录、基准结果、截图、日志、审阅记录或远程回执。原始证据文件放在 `records/<TASK-ID>/evidence/`。每项至少包含：

- 证据 ID、路径、类型 `kind` 和观察时间；
- 支持的指标；
- 结果 `passed` / `failed` / `undetermined`；
- 当前性 `current` / `stale`；
- 标为 `stale` 时必须保留非空 `stale_reason`。历史证据只审计原件哈希、记录结构和结果自洽，不要求当年输入仍存在；stale 证据永远不能满足指标的 current 条件。
- 证据文件原始字节的 `sha256`，用于发现证据在记录后被改写；
- 非执行类证据还要写与当前仓库状态匹配的 `revision`。

代理回复“tests passed”不是证据。主线程检查命令、原始输出、退出码、环境和实际 diff；无法复现时标记 `undetermined`。

### 执行记录

命令类证据用 `scripts/record_execution.py` 运行并生成，`kind` 写 `execution`：

```bash
python3 scripts/record_execution.py \
  --output records/TASK-001/evidence/unit-tests.json \
  --repo . --state records/TASK-001/task-state.json \
  --cwd . --source src/app.py --test tests/test_app.py \
  -- python3 -m unittest tests.test_app
```

记录保存实际 argv、cwd、起止时间、退出码、是否超时、原始 stdout/stderr（含 base64 原始字节）、输入文件哈希，以及执行前后的 revision token。它拒绝覆盖已有输出文件，包括命令运行期间新出现的同名文件；发布记录失败时返回错误，已有文件保持原样。

| 字段 | 含义 |
| --- | --- |
| `revision_before` / `revision_after` | 命令开始前、结束后的 revision token |
| `revision` | 前后相同时为该 token；命令运行期间内容变化时为 `null` |
| `revision_changed_paths` | 运行期间内容发生变化的路径（最多 50 个），用于找出生成物 |
| `result` | 按优先级取 `timeout` > `revision_changed` > `missing_output` > `passed` / `failed` |

`inputs` 使用 mapping，key 就是输入路径，value 保存 `kind`、`sha256`、非空 `identity` 与 `reproduction`。仓库内 key 用规范相对路径。带有 `--repo` 与 `--state` 的 Veriflow recorder/validator 对外部输入要求 `baseline.external_inputs` 中精确列出的规范化绝对文件且 `kind: fixture`；独立运行、未绑定 repo/state 的 recorder 只是通用原始执行记录，不适用这条任务绑定规则。source/test 必须在仓库内；符号链接 alias 不满足身份要求。

退出码：超时 `124`；`revision_changed` 和 `missing_output` 返回 `1`；找不到命令 `127`、无权执行 `126`；其余沿用命令本身的退出码。只给 `--repo` 或只给 `--state`、或无法计算 revision 时，命令不会运行，退出码 `2`。

检查会生成仓库内的非忽略文件时（例如 Python 测试生成的 `__pycache__/`、构建输出），结果会是 `revision_changed`，记录和 stderr 会列出这些路径；把生成物加入 `.gitignore` 或写到证据目录后重跑。

校验器对执行记录的检查：

- 字段类型：命令参数、输出文本、退出码和布尔标志须符合记录类型，否则 `EXECUTION_RECORD_TYPE`；字符串 `"false"` 不能充当布尔值，布尔值也不能充当退出码；
- 记录自洽：`result` 与退出码、超时、输出缺失、revision 是否变化一致，否则 `EXECUTION_RESULT_MISMATCH`；
- 外层证据标 `passed` 时，记录本身必须是 `passed`；标 `failed` 或 `undetermined` 时，超时、空输出等诚实记录不报错；
- 证据标 `current` 时，记录内的 `revision` 必须等于当前 token，否则 `EXECUTION_REVISION_STALE`。只刷新外层字段而不重跑检查，过不了这一项；
- 外层 `revision` 可以省略，写了就必须与记录内一致，否则 `EXECUTION_REVISION_MISMATCH`；
- 1.3 执行 raw 记录包含 `spec_version` 与 `spec_sha256`；非执行证据也必须带这两个字段。`current` 证据须与当前版本/摘要匹配；`stale` 证据保留原字段和非空 `stale_reason`，不补造缺失的绑定。当前证据会核对原记录声明、允许项和真实哈希；未声明、路径逃逸、符号链接逃逸或哈希变化报错。带 repo/state 的 `record_execution` 在命令前拒绝未授权外部输入，并在结束时重读 revision 和所有输入；运行期间输入变化（包括 ignored fixture）会产生 `revision_changed`，不能记为 passed。

`verification: execution` 的强制门槛标为 `passed` 时，必须至少有一项当前、通过的执行记录，否则 `METRIC_EVIDENCE_UNVERIFIED`。

## Revision token

对 1.1/1.2，`validate_task.py --print-revision` 从任务基线到当前工作树计算只读基础内容指纹（`revision-v2`）。1.3 在该产品指纹之外增加 Spec digest 和显式路径绑定；不能用旧的 ignored/记录目录排除规则绕过显式交付物或契约。因此：

- 暂存或提交改动不会改变 token，本地提交后证据仍保持当前；
- `diff.noprefix`、`diff.algorithm` 等本地 diff 配置和 CRLF/LF 检出差异不影响 token；
- 非记录内容的任何实际变化都会改变 token；
- 1.1/1.2 基础 token 的 `.gitignore` 规则仍按旧语义适用；1.3 的显式交付物即使位于 ignored/metadata 目录或尚未生成，也必须进入绑定（尚未生成时记录 `missing`，验收单独拒绝缺失）。

1.1/1.2 基础指纹固定排除两类记录路径：

- 状态文件所在目录中的 `index.md`、`task-summary.md`、`work-log.md`、`handoffs/`、`evidence/` 和状态文件本身（状态文件直接位于仓库根目录时只排除它自己）；
- `baseline.foreign_paths` 列出的他人无关改动，所以别人继续修改这些文件不会让本任务证据过期。

1.3 另行处理：契约文件按独立字节哈希进入 Spec digest；`state.binding.receipt_paths` 只接受精确 receipt 文件并作为回执排除项。receipt 无需产品 review，但若进入提交，仍须作为提交路径单独审查并满足 push gate；不能靠 `.gitignore` 避免交付物、契约或 receipt 的绑定检查。

```bash
python3 scripts/validate_task.py records/TASK-001/task-state.json --repo . --print-revision
python3 scripts/validate_task.py records/TASK-001/task-state.json --repo . --print-sha256 records/TASK-001/evidence/review.md
```

非执行类证据把 revision 输出写入 `evidence[].revision`；所有证据把 sha256 输出写入 `evidence[].sha256`；`changes[].revision` 同样写当前 token。验证后再修改代码或测试，要重新运行受影响检查。提交前确认暂存区与工作树一致，否则提交内容可能不同于被验证的内容。被排除的记录文件若要提交，仍必须出现在已审查的 `CHG-*.paths` 中。该指纹证明“非记录仓库内容没有改变”，不证明证据结论正确，也不取代提交 SHA 或远程回执。

所有 git 调用有超时（默认 60 秒，环境变量 `VERIFLOW_GIT_TIMEOUT` 可调）。确认仓库根目录时超时是运行错误（退出码 `2`）；计算 revision 或读取改动路径时超时报 `REVISION_UNAVAILABLE`、`CHANGED_PATHS_UNAVAILABLE` 等错误（退出码 `1`），消息含 `timed out`。两种情况下相关检查都记为 `undetermined`，不能当作工作区干净。

## 门槛检查

```bash
python3 scripts/validate_task.py records/TASK-001/task-state.json --repo . --gate record
python3 scripts/validate_task.py records/TASK-001/task-state.json --repo . --gate implementation
python3 scripts/validate_task.py records/TASK-001/task-state.json --repo . --gate acceptance
python3 scripts/validate_task.py records/TASK-001/task-state.json --repo . --gate local-commit
python3 scripts/validate_task.py records/TASK-001/task-state.json --repo . --gate push --target origin/feature-x
python3 scripts/validate_task.py records/TASK-001/task-state.json --repo . --gate merge
python3 scripts/validate_task.py records/TASK-001/task-state.json --repo . --gate deploy --target production
python3 scripts/validate_task.py records/TASK-001/task-state.json --repo . --gate action --action migrate --target db:staging
```

脚本从不执行 Git 写操作或外部动作。各门槛逐级包含前一级的检查（`action` 除外）：

| 门槛 | 检查内容 |
| --- | --- |
| `record` | 字段、ID 引用、状态取值、证据文件与哈希、执行记录、授权来源 |
| `implementation` | 需求已就绪，主任务和指标已建立，基线为 `clean` 或 `dirty_dependency_confirmed`，无模板占位符；有既不在 `file_scope` 也不在 `foreign_paths` 的未提交改动时警告 `BASELINE_UNLISTED_CHANGES` |
| `acceptance` | 强制门槛与非退化约束通过（或已延后）、执行验证方式满足、证据当前、实现任务与主任务已验证、基线以来的改动路径被已审查 `CHG-*` 覆盖、整体验收通过；不要求 commit 授权 |
| `local-commit` | `acceptance` 加上 commit 授权；同一 revision 已完成提交时阻断 |
| `push` | 存在对应当前 revision 的已完成提交；`base..HEAD` 中提交的路径都经过审查且不含 foreign 路径；除记录文件和 foreign 路径外没有未提交改动；push 授权与范围 |
| `merge` | 当前 HEAD 已完成推送；`delivery.remote_ci` 为 `passed` 且 `remote_ci_revision` 等于该 HEAD；merge 授权与范围 |
| `deploy` | 已完成合并（推送与远程 CI 的版本已在 `merge` 门槛核对）、恢复策略完整、deploy 授权与范围 |
| `action` | 自定义动作（如 `migrate`）的授权与范围、恢复策略、未决与重复动作；不要求产品验收，因为预发布环境的迁移可能是验收的前提 |

`local-commit` 的覆盖检查把基线以来的实际变更路径（排除 foreign 路径）与所有 `reviewed` 的 `CHG-*.paths` 对照；重命名的原路径和新路径都必须被覆盖。`paths` 使用仓库相对的精确文件或目录，不支持 glob。有 foreign 改动时给出警告 `FOREIGN_CHANGES_PRESENT`，报告要说明检查时这些改动存在。

`find_placeholders` / `PLACEHOLDER_VALUE` 只检查任务记录中的模板占位值，不分析产品代码是否为空实现或实际接入。主线程按 [design.md](design.md) 审查实际路径与契约效果，并核对区分性证据。

### 副作用防重

有副作用的门槛（`local-commit`、`push`、`merge`、`deploy`、`action`）对“待执行动作”做三项检查：

1. **结果不明的动作先核验。** 同一授权动作存在 `in_progress` 或 `unknown` 的 `ACT-*` 时报 `ACTION_OUTCOME_UNKNOWN`。先查外部真实状态，把它改成 `completed` 或 `failed` 并写回执；`failed` 不阻止重试。
2. **同一版本不重复执行。** 已有 `completed` 的同类动作，且其 `revision` 等于待执行版本（`--target` 给出时 target 也相同）时报 `DELIVERY_ALREADY_COMPLETED`。待执行版本默认取当前 revision token（`local-commit`）或 `HEAD`（其余门槛），可用 `--revision` 指定。版本不同则放行，所以审查后的追加提交和推送可以正常进行。
3. **授权与范围。** 未授权报 `AUTH_COMMIT` / `AUTH_PUSH` / `AUTH_MERGE` / `AUTH_DEPLOY` / `AUTH_ACTION`。授权带 `scope` 时必须给 `--target`（否则 `AUTH_SCOPE_TARGET_REQUIRED`），且 target 要在范围内（否则 `AUTH_SCOPE`）。

执行前先写一条 `status: planned` 的 `ACT-*`（含 `target` 和 `revision`）并运行门槛，通过后改为 `in_progress` 再执行，执行后更新为 `completed` 或 `failed` 并写回执。门槛把 `in_progress` 当作结果不明，所以要在门槛通过之后才改。这样中途中断时，恢复者看到的是“结果不明”，而不是“从未执行”。

### 严重程度

| 检查 | `record` | `implementation` | `acceptance` / `local-commit` | `push` / `merge` / `deploy` / `action` |
| --- | --- | --- | --- | --- |
| 模板占位符 `PLACEHOLDER_VALUE` | 警告 | 错误 | 错误 | 错误 |
| 缺少 `evidence[].sha256` | 警告 | 警告 | 错误 | 错误 |
| 已执行却未授权或超出范围 `ACTION_UNAUTHORIZED` / `ACTION_OUT_OF_SCOPE` | 警告 | 警告 | 警告 | 错误 |

已执行却未授权的动作在早期只报警告，是为了让执行者如实记录已经发生的事；进入外部动作门槛前，必须先核验真实外部状态并与用户确认。

输出为 JSON。退出码 `0` 表示没有错误（可能有警告），`1` 表示记录或门槛错误，`2` 表示运行错误（例如 `--repo` 不是 Git 根目录、状态文件无法读取、确认仓库时 git 超时，或 `--gate action` 缺少 `--action`）。

`delivery.remote_ci` 与 `remote_ci_revision` 由执行者填写，校验器只检查一致性，不会访问远程 CI；填写前要实际查看流水线结果。机器门槛失败时保留具体错误。不得通过删除指标、改状态或修改测试来迎合脚本；只有真实需求变化可经来源和决策记录调整门槛。
