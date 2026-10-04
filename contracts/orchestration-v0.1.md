# Veriflow 编排与验证 0.1 候选

| 项目 | 内容 |
| --- | --- |
| 契约标识 | `veriflow.orchestration/0.1-draft` |
| 状态 | 文档设计，尚无编排引擎、RuntimePort adapter 或独立协议实现 |
| 所有者 | Veriflow：验收、任务依赖、尝试分派、验证、诊断、证据与整体验收 |
| 运行依赖 | [Rein RuntimePort 0.1 候选](https://github.com/JadeSnow7/Rein/blob/cf62ae829e7c57a219e3e82436ce1a3307917ac4/contracts/runtime-port-v0.1.md)；固定引用提交 `cf62ae8`，权威定义在 Rein，不复制其会话 DTO |
| 关联决定 | [BOUNDARY-20261004](../DECISIONS.md) |

本文规定语义与最小字段，不是现有 `task-state.json` 的 schema，也不声称 `validate_task.py` 已能读取这些对象。PR #3 已合并，当前记录 schema 为 1.3，并兼容历史 1.1/1.2；本编排契约仍需单独适配。正式实现须选一个权威类型源并生成 schema，再提供固定版本的映射；不能在 skill、调度器与 Rein 各维护一套相同状态。

## 1. 最小契约对象

以下字段为候选语义要求；带 `_ref` 的字段引用不可变 artifact 或版本化定义，不能只写可变的文件路径。外部引用必须同时包含可取回位置、版本/摘要与访问方式。Rein ArtifactRef 沿其权威 port；其他引用也以原始字节摘要核验，不从模型声明中生成“真实证据”。

| 对象 | 必需内容 | 使用边界 |
| --- | --- | --- |
| `AcceptanceContract` | `contract_id / version / spec_ref / source_refs / conditions / protected_refs`；每项条件有 ID、可观察预期、检查方式、必需/非回归/改进分类 | 用户/目标项目定义业务依据；Veriflow 冻结验收条件及验证器。执行者不能修改条件来放行自身 |
| `TaskGraph` | `workflow_id / revision / acceptance_ref / tasks`；任务含 `task_id / depends_on / input_refs / output_requirements / condition_ids / allowed_paths / budget` | 有限 DAG；每任务至少关联一个验收条件，依赖必须存在且无环。Veriflow 计算就绪与文件写入所有权 |
| `AttemptAssignment` | `workflow_id / task_id / attempt_id / executor_ref / runtime_contract_version / spec_ref / input_ref / verification_plan_ref / workspace_ref / execution_policy / request_id` | 一个 task 可有多次有界尝试；每次绑定一个 Rein/provider 实例，返回 `run_id / session_id` 后固定映射 |
| `VerificationPlan` | `plan_id / version / acceptance_ref / spec_ref / input_refs / checks`；检查含 `check_id / executor_ref / environment_ref / oracle_ref / expected / limits` | 执行前冻结检查与 oracle，不要求提前知道输出候选。实际验证请求另绑定 `candidate_ref` 与尝试身份，回执保存二者；不为新候选改写计划 |
| `VerificationReceipt` | `receipt_id / workflow_id / task_id / attempt_id / run_id / check_id / spec_ref / plan_ref / candidate_ref / input_refs / executor_ref / environment_ref / raw_refs / result / validity`；适用时记录命令、退出码及实际耗时 | 原始回执由实际检查执行器产生；Veriflow 校验全部绑定与证据有效性，缺失/未知值如实保留 |
| `FailureDiagnosis / RepairRequest` | `diagnosis_id / attempt_id / receipt_refs / category / hypothesis / repair_scope / preserved_gates / retry_budget / stop_condition` | 诊断假设与事实回执分开；修复另建 attempt，保持验收契约。改变需求必须新版本，不能伪装成修复 |
| `EvidenceBundle / ReviewDecision` | `bundle_id / acceptance_ref / graph_revision / spec_ref / candidate_ref / receipt_refs / change_refs / outstanding`；决定含 `decision_id / source_ref / bundle_ref / candidate_ref / outcome / scope` | evidence 包归 Veriflow；人工审阅界面可在 Web Studio。人工决定绑定具体证据/候选，不创造未发生的用户批准 |

首版的 `tasks` 可只有两个串行任务，`executor_ref` 可只有一个 Rein 实例。不要求自动拆任务、学习型规划器、并行资源池或新的 UI。

VerificationPlan 可在分派前创建；候选由运行结果产生。验证时使用 `plan_ref + candidate_ref + workflow/task/attempt/run` 绑定，避免把尚未生成的候选摘要写入 StartRequest。计划中的检查不足时需明确修订契约/计划版本，不能在执行后悄悄补条件或改 oracle。

## 2. 分派与生命周期

任务状态由 Veriflow 单独维护：`pending / ready / running / verifying / awaiting_review / accepted / failed / blocked / cancelled / outcome_unknown`。`ready` 必须满足依赖都已 accepted、输入版本有效、执行权限/能力满足、预算预留与写范围无冲突。下游不能仅凭上游 runtime 完成进入 ready。

runtime 状态、任务状态和验证结果是不同轴：运行完成后 task 进入 verifying；必要检查和适用人工条件全部通过才 accepted。`failed` 表示已运行的业务条件不满足；设施/证据问题先 blocked，副作用无法确认则 outcome_unknown。人工拒绝或停止按明确理由处理，不写成自动测试失败。

Veriflow 先落盘 AttemptAssignment 与稳定 request_id，再调用 `start`；返回后落盘 run/session 映射并消费事件。如果 start 已执行但响应丢失，重发相同 request_id 取回原 run，不能用新 ID 再启动。每个事件按 event_id 去重并保存游标；旧 attempt 的迟到事件仅归档，不推进新尝试。

`resume` 继续同一尝试，业务修复/换 Agent/改输入则产生新 attempt。未知副作用必须先用 runtime/provider 的 reconcile 核对，不能直接记失败后重试。已取消 task 的迟到结果留证，不再启动依赖任务；取消不承诺撤销已经执行的外部动作。

全局预算、修复次数、并行写入所有权及资源选择由 Veriflow 管理；单次工具/模型预算与权限由 Rein 执行。Veriflow 只能分配现有授权内的子范围，不能把自身计划、通过的 gate 或其他 Agent 建议当作新增授权。

## 3. 验证结果与证据有效性

每个检查的 `result` 为 `passed / failed / undetermined / not_run`，`validity` 独立为 `current / stale / invalid`。保存原始结果，不用 stale 覆盖历史 failed/passed。

| 可观察事实 | 结果 / 有效性 | 是否支持当前必需条件通过 |
| --- | --- | --- |
| 固定业务断言满足且回执绑定当前规格、输入、候选、计划与环境 | passed / current | 是；仍需其他必需条件及适用人工决定 |
| 检查正常执行但断言不满足 | failed / current | 否 |
| 检查器不可用、设施超时、证据不足或结果无法可信解释 | undetermined / current 或 invalid（按实际缺口） | 否 |
| 检查未执行 | not_run / current | 否 |
| Spec、输入、候选、oracle、执行器/环境绑定或验证计划变化 | 保留原 result / stale | 否；受影响项重验 |
| 原始字节摘要不匹配、错 attempt、伪造的身份或缺少必需绑定 | 保留原 result / invalid | 否 |

超时若本身是验收合同规定的业务时限，超限为 failed；执行设施故障造成超时则为 undetermined。改进目标若没有合同明确要求，不提升为必需门槛，也不绕过 mandatory/non_regression 条件。

工作流 accepted 要求当前整合候选满足所有必需条件与非回归条件、每项有可信且 current 的通过回执、所需人工条件已满足、无未核对的副作用。单任务各自通过不代表整合候选通过，整合后必须验证整体验收。模型消息、validator 的 `ok`、CI 绿色和 Rein 局部 `Accepted` 均不能单独满足这些条件。

实际检查只能由一个执行器运行一次：若用 PR #3 recorder，由 recorder 执行并留证；若由 Rein/CI/Web provider 执行，直接保存其回执，不能为了“补证据”再执行一次有副作用的命令。当前 main 的 `validate_task.py` 不执行检查，它的输出在 adapter 中仅映射成记录/gate 一致性结果；运行错误和无法解释的输出不能映射为产品通过。

## 4. Web Studio 与权限边界

Web Studio 提供受信 `workspace_ref`、浏览器/终端能力、候选预览、CDP 操作、截图、日志和运行时观测；具体 provider 工具 shape 与能力版本由环境侧后续定义。Veriflow 的 VerificationPlan 引用对应观测与 oracle；页面截图存在不证明页面业务断言满足。

人工决定由实际用户在受信交互入口提供并绑定候选/证据包；UI 显示“已批准”不是权限来源。Rein 执行批准对应的单次 effect，Veriflow 保存整体审阅语义。commit / push / merge / deploy 仍是分别授权的动作；通过验收不自动授予这些权限。浏览器 UI、Harness 控制台和任务图实现不在本轮交付范围。

## 5. 兼容与首轮验收

消费者必须引用固定 RuntimePort 版本/提交及实际 capabilities；不支持的能力明确阻塞，不直接读写 Rein SQLite，也不回退到未受约束的宿主操作。契约语义或必需字段变化需新版本；新产品 contract_version 与旧记录 schema_version 分别管理。

首轮应覆盖：DAG 环/缺依赖拒绝；上游未验收时下游不启动；重复分派与事件不重复运行；旧 attempt 结果不串入新尝试；局部 verifier/CI 成功但业务断言失败；候选变化导致 stale；损坏/缺失回执为 invalid 或 undetermined；未知副作用不盲重试；整合候选另行复验；人工决定版本错配；预算耗尽与取消保持可解释。这里列的是**待实现测试的条件**，不是已通过的结果。
