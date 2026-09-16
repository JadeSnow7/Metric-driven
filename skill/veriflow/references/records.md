# 记录模型与状态语义

## 按档位裁剪

档位定义见 `SKILL.md` 第 1 节。

- **L0 轻量**：不建记录文件；在最终汇报中写清改动、检查与结果即可。
- **L1 标准**：在对话或 `task-summary.md` 中写明目标、范围、验收方法、基线提交与证据。
- **L2 完整**（需求模糊或多结果、跨会话、多人/多 Agent、难以撤销的动作）：在 `records/<TASK-ID>/` 增加 `task-state.json` 和追加式 `work-log.md`；只有确实需要另一位执行者继续时才增加交接包。

模板位于 `assets/templates/`。它们是可裁剪起点，不是每项任务的文档配额。

## 稳定编号

| 前缀 | 对象 | 例子 |
| --- | --- | --- |
| `SRC-` | 来源 | `SRC-001` |
| `MT-` | 独立主任务 | `MT-002` |
| `MET-` | 指标或约束 | `MET-004` |
| `IT-` | 实现子任务 | `IT-006` |
| `CHG-` | 有明确目的的改动单元 | `CHG-003` |
| `EVD-` | 证据 | `EVD-008` |
| `DEC-` | 决策 | `DEC-002` |
| `HYP-` | 改善假设 | `HYP-001` |
| `ACT-` | 具有副作用或需防重的动作 | `ACT-005` |
| `EVENT-` | 工作日志事件（仅用于 `work-log.md`） | `EVENT-004` |

编号只需在当前项目/任务记录范围内唯一。追踪到有明确目的的改动单元即可，不做逐行账本。

## 状态语义

不要用模糊的 `done` 同时表示实现、验证和交付。

### 任务整体

`task.status` 描述整项任务，可使用下文的需求发现状态（`needs_clarification`、`exploring`、`ready`）与执行状态（`in_progress`、`blocked`、`implemented`、`verified`、`failed`、`cancelled`），另有两个仅用于任务整体的状态：

- `paused`：按记录的原因暂停；恢复前按 `workflow.md` 的“恢复执行”核验。
- `completed`：本次授权范围内的交付动作已完成并核验，且没有待用户确认的决定。还有待确认项时，任务停在 `verified` 或 `blocked`，并在摘要里把“已交付”和“待确认”分开列出。

暂停是任务整体的状态；主任务与实现任务保持暂停前的实际状态。`task.mode` 为 `new`（首次执行）或 `resume`（恢复既有任务）。

### 需求发现

- `needs_clarification`：缺失信息会改变实现决策，尚不可实施。
- `exploring`：在预算内验证明确不确定性，尚不可声称产品完成。
- `ready`：足以确定主任务、指标和范围。

### 主任务与实现任务

- `proposed`：候选边界，尚未审查。
- `defined` / `planned`：边界与依赖已写明，可进入实施准备。
- `in_progress`：正在执行。
- `blocked`：存在明确阻塞项。
- `implemented`：代码或内容已产生，尚未完成独立核验。
- `verified`：关联门槛和证据已核验。
- `failed`：实现或验收失败。
- `cancelled`：经记录的决策停止，不等于失败。

主任务使用 `defined`，实现任务使用 `planned`；其余共享。

### 验证

- `passed`：当前证据支持门槛通过。
- `failed`：当前证据表明门槛未通过。
- `undetermined`：缺证据、环境不可用或结果无法判定；永远不算通过。
- `deferred`（仅指标，1.2）：用户决定先交付、稍后验证；必须用 `decision_id` 关联决策。可以通过本地提交和推送，不能通过合并、部署或自定义动作门槛；整体验收不能延后。

证据时效另用 `current` / `stale`。验证后内容又变了，校验器会直接报出过期证据（`EVIDENCE_STALE` 或 `EXECUTION_REVISION_STALE`），不需要手工逐项回退状态。处理方式是重跑受影响检查、换上新证据；旧证据改为 `stale` 保留。只有实现被撤销或已知失败时，才相应把 `IT-*`、`CHG-*`、指标改为 `cancelled`、`reverted` 或 `failed`。

### 基线

`baseline.worktree_status` 使用：

- `clean`：任务从明确提交开始，本任务相关路径没有他人改动。
- `dirty_dependency_confirmed`：任务依赖的未提交改动已确认归属与纳入方式，并写入 `baseline.ownership`；这些路径在提交前同样必须被已审查的 `CHG-*` 覆盖。
- `unknown`：尚未核验，阻止进入实现。

`baseline.foreign_paths`（1.2，可选）列出已确认与本任务无关的他人未提交改动。它们不计入 revision token、不参与改动覆盖检查、不阻止推送，但不能与任何 `file_scope` 或 `CHG-*.paths` 重叠（`FOREIGN_PATH_OVERLAP`）。任务依赖的改动不属于 foreign，应使用 `dirty_dependency_confirmed`。同一文件里混有他人改动时，先问用户。

### 来源采纳

- `proposed`：尚未评估的建议，或仍需用户决定的事项。已授权范围内的实现细节与可回退默认可由主线程核查后采纳；涉及范围、权限或难以回退的用户行为变化且缺少现有依据时，等待用户决定。
- `accepted`：经有权作出该决定的人核查后纳入当前需求或决策，记录依据。采纳 `agent_inference` 不会使其成为用户授权。
- `rejected`：已评估但不采纳，并保留原因。
- `superseded`：被更新来源替代。

### 授权与交付

授权使用 `authorized`、`not_authorized`、`unknown`，必须记录 `commit`、`push`、`merge`、`deploy` 四项；1.2 可以增加其他难以撤销的动作，例如 `migrate`（名称为小写字母、数字、`-`、`_`）。每项可带 `scope`：允许的目标列表，例如 `["origin/feature-x"]`、`["db:staging"]`。授权来源需指向采纳状态为 `accepted` 的 `user_requirement` 或 `user_feedback`；已被 `rejected` 或 `superseded` 的指令不再构成授权，资料和代理判断也不能作为授权来源。

`ACT-*` 记录一次有副作用的动作：

| 字段 | 含义 |
| --- | --- |
| `authorization_action` | 消耗哪一项授权；防重复与授权核对都按它判断，`kind` 只作描述 |
| `target`（1.2） | 作用对象，例如 `origin/feature-x`、`production`、`db:staging`；本地提交可写 `local` |
| `revision`（1.2） | 作用的内容：提交写当前 revision token，推送、合并、部署写提交 SHA |
| `status` | `planned`、`in_progress`、`completed`、`failed`、`unknown` |
| `receipt` | `completed` 与 `failed` 必填：提交 SHA、远端引用、迁移版本或失败输出位置 |
| `idempotency_key` | 记录内唯一 |

执行前先写 `planned` 并运行门槛，通过后改为 `in_progress` 再执行，执行后改为 `completed` 或 `failed`。中断后结果不明的写 `unknown`；校验器会在核验前阻止同类动作再次执行。

`delivery`（1.2）只保留 `local_validation`、`remote_ci` 和可选的 `remote_ci_revision`；提交、推送、合并、部署的进度只记在 `actions` 里。交付状态取值为 `not_started`、`passed`、`failed`、`unavailable`、`completed`、`rolled_back`。远程 CI 未运行是 `not_started` 或 `unavailable`，不是 `passed`；`remote_ci_revision` 写实际查看过的流水线所对应的提交。

## 记录所有权与报告载体

| 记录 | 权威性 | 维护者 |
| --- | --- | --- |
| 需求/决策与 `task-state.json` | 结构化当前状态 | 主线程 |
| `task-summary.md` | 人读的当前权威摘要 | 主线程 |
| `work-log.md` | 按事件追加的历史 | 事件执行者追加，主线程审查 |
| 实现记录与原始证据 | 对所分配路径负责 | 对应执行者 |
| 项目知识 | 仅经核验的稳定知识 | 主线程或明确所有者 |
| 个人长期记忆 | 非项目记录 | 仅经用户明确授权写入 |

`task-summary.md` 是当前人读摘要，不是日志或证据副本：说明当前结果、影响、关键依据、限制和下一步，链接详细记录即可。`task-state.json` 是结构化状态的权威来源；`work-log.md` 只追加重要事件；`evidence/` 保存原始输出。交接包只记录下一位执行者确实需要的上下文，并优先引用当前摘要，避免复制状态、权限表和完整日志。简单任务可以不创建这些文件，直接在最终回复中报告。

共享状态文件只由主线程写。子代理通过交接包返回建议和证据路径，避免并发覆盖。

## 项目知识最小元数据

稳定知识应记录：来源、适用范围、版本或环境、最后核验时间、当前有效性。未核验推断留在决策/日志中，不升级为项目事实。

## `task-state.json`

当前新记录格式为 `schema_version: "1.3"`。建议把一项复杂任务的结构化记录放在专用子目录；这也让证据指纹能安全地区分状态元数据与产品改动：

### 1.3 Spec 绑定

`state.spec` 是当前 Spec 的结构化索引：`version` 必须非空，`authority` 为 `state.spec` 或仓库内契约文件（后者必须同时列在 `spec.contracts`）。`source_ids` 必须指向 `sources` 中 `adoption: accepted` 的来源；`goal_ref` 与 `scope_ref` 分别复用 `discovery.expected_outcome` 和 `discovery.scope` 等现有字段。`constraints`、`exceptions`、`open_items` 必须是列表，未决项存在时实现门槛不能就绪。

每个 `conditions` 条目都必须独立列出非空 `metric_ids`、至少一个强制或非退化指标，以及具体仓库相对交付文件。`contracts` 是必须存在的精确文件，按字节计算哈希；交付物可以在实现前缺失。运行回执只放在顶层 `state.binding.receipt_paths`，必须是精确文件路径，并且不得与交付物或契约冲突；`baseline.foreign_paths` 也不得覆盖交付物或契约。

1.3 的 revision 是产品指纹与 Spec digest 的组合。digest 包含完整 Spec、全部 `main_tasks` 和 `metrics` 的规范字段、契约字节哈希、discovery 引用值、回执分类及 foreign/external 输入声明；只在对象自身的精确位置排除 `status`、`evidence_ids` 和 `implementation_task_ids`。旧 1.1/1.2 记录继续按旧语义审计，缺少绑定时不能通过修改外层字段冒充 1.3 重跑。

1.3 仍保留 1.2 的 `deferred` 指标语义：它表示用户明确决定稍后验证，不能作为当前 Spec 已满足或整体验收通过的证据。历史记录迁移只保留原始 raw 和 `stale_reason`，缺少绑定、快照或当前支持关系时记为未知/过期，不补造历史 Spec 或授权快照。

```text
records/<TASK-ID>/
├── task-state.json    # 结构化当前状态
├── index.md           # 可选：本任务记录的导航，恢复时先读
├── task-summary.md    # 人读的当前权威摘要
├── work-log.md        # 追加式事件日志
├── handoffs/          # 交接包
└── evidence/          # 原始证据文件
```

`assets/templates/task-state.example.json` 展示完整字段；`scripts/validate_task.py` 校验关键关联。重点约束：

- 每个主任务引用来源；每个指标属于主任务；每个实现任务属于主任务并关联指标或写明必要支撑原因；
- `overall_acceptance` 独立于子任务状态；
- 证据路径位于仓库内，带有 `sha256`；执行记录自带运行时的 revision，其他证据用 `revision` 字段绑定当前内容；
- `actions` 的 `idempotency_key` 唯一，已完成和失败的动作有回执，已执行动作有对应授权且在范围内；
- 授权与交付状态分开，授权不能由工具推断，且须引用已采纳的用户指令。

### 版本迁移

历史格式 `1.1` 继续按原语义审计并给出 `SCHEMA_LEGACY`；`1.2` 继续按旧语义审计并给出 `SPEC_UNBOUND_LEGACY`；新记录使用 `1.3`。旧记录不能通过补写外层字段伪造历史 Spec、绑定或授权快照。

从 1.1 迁移到 1.2：

1. `schema_version` 改为 `"1.2"`；
2. 每个 `ACT-*` 补 `target` 和 `revision`（历史动作按回执填写提交 SHA 或当时的 token），`failed` 动作补回执；
3. `delivery` 删去 `local_commit`、`push`、`merge`、`deploy`，这些进度已在 `actions` 中；远程 CI 已通过的补 `remote_ci_revision`；
4. 命令类证据用 `record_execution.py --repo --state` 重跑，或保持文本证据并把相关指标的 `verification` 设为 `manual`；
5. 有他人无关改动时补 `baseline.foreign_paths`。

从 1.2 迁移到 1.3：

1. 新建 `state.spec`，写入非空 `version`、authority、accepted `source_ids`、现有 `discovery` 引用、条件、契约与未决项；不要复制一套新的目标/方法权威。
2. 将运行回执路径放入顶层 `state.binding.receipt_paths`，按精确文件记录；旧回执缺少绑定时保留 raw 并写 `stale_reason`，不能刷新外层字段冒充重跑。
3. 重新计算产品与 Spec digest；正文、契约字节、规范指标或交付分类改变后必须重跑受影响检查。
4. 对外置 fixture 补精确允许路径、sha256、identity 与 reproduction；不符合声明的历史输入只做完整性审计。

### 授权执行快照

执行有副作用的动作前运行：

```bash
git rev-parse HEAD
python3 skill/veriflow/scripts/authorization_snapshot.py \
  --state records/TASK-001/task-state.json \
  --action push --target origin/feature-x \
  --revision <COMMIT_SHA_FROM_PREVIOUS_COMMAND>
```

CLI stdout 是 JSON 对象；将解析后的对象原样嵌入对应 `actions[].authorization_snapshot`，与 `authorization_action`、`target`、`revision` 同一动作记录。`push`、`merge`、`deploy` 使用实际提交 SHA；`local-commit` 使用 `validate_task.py --print-revision` 输出的 revision token。对象包含执行前的 `source`、`source_id`、授权范围、`captured_at`、`source_content` 和 `content_sha256`。当前动作使用当前有效且已采纳的来源；历史动作只在存在执行前快照时可关联，缺失快照记为 `unknown`。快照是执行时事实记录，不是用户密码学签名；主线程仍需核实来源真实性。用户后来撤销来源不会改写历史快照，但会阻止未来动作。

从 1.0 迁移：先按 1.1 的要求为每项证据补上 `sha256`（`--print-sha256`），证据文件建议移入 `evidence/`。1.0 的 revision token 与新算法不兼容：把受影响证据先标为 `stale`，重跑检查后再写入新 token，不要直接改写旧 token。

校验器不会验证文字是否真实、用户是否真的授权或指标是否合理；这些属于主线程审查。
