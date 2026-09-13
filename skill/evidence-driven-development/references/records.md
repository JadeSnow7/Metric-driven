# 记录模型与状态语义

## 按规模裁剪

- **小且低风险**：在现有对话/issue 中记录来源、验收、diff 和结果即可。
- **中等任务**：维护 `task-summary.md` 与必要证据。
- **复杂、跨会话、多人/多 Agent 或有外部副作用**：增加 `task-state.json`、追加式 `work-log.md` 和交接包。

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

编号只需在当前项目/任务记录范围内唯一。追踪到有明确目的的改动单元即可，不做逐行账本。

## 状态语义

不要用模糊的 `done` 同时表示实现、验证和交付。

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

证据时效另用 `current` / `stale`。内容修改后，受影响的 `passed + current` 必须重新判定；不要只把时间戳更新为当前。

证据失效时按可观察事实回退：对应 `EVD-*` 变为 `stale`，`MET-*` 与整体验收变为 `undetermined`；仍存在实现产物的 `IT-*` 从 `verified` 回到 `implemented`，其主任务也从 `verified` 回到 `implemented`；受影响的 `CHG-*` 从 `reviewed` 回到 `implemented`。若实现本身被撤销或已知失败，再分别使用 `in_progress`、`failed` 或 `reverted`，不要机械套用上述默认值。

### 来源采纳

- `proposed`：待主线程判断。
- `accepted`：纳入当前需求或决策。
- `rejected`：已评估但不采纳，并保留原因。
- `superseded`：被更新来源替代。

### 授权与交付

授权使用 `authorized`、`not_authorized`、`unknown`，分别记录 `commit`、`push`、`merge`、`deploy`。授权来源需指向 `user_requirement` 或其他可确认的用户指令；资料和代理判断不能作为授权来源。

交付阶段使用 `not_started`、`passed`、`failed`、`unavailable`、`completed`、`rolled_back`。远程 CI 未运行是 `not_started` 或 `unavailable`，不是 `passed`。

## 记录所有权

| 记录 | 权威性 | 维护者 |
| --- | --- | --- |
| 需求/决策与 `task-state.json` | 结构化当前状态 | 主线程 |
| `task-summary.md` | 人读的当前权威摘要 | 主线程 |
| `work-log.md` | 按事件追加的历史 | 事件执行者追加，主线程审查 |
| 实现记录与原始证据 | 对所分配路径负责 | 对应执行者 |
| 项目知识 | 仅经核验的稳定知识 | 主线程或明确所有者 |
| 个人长期记忆 | 非项目记录 | 仅经用户明确授权写入 |

共享状态文件只由主线程写。子代理通过交接包返回建议和证据路径，避免并发覆盖。

## 项目知识最小元数据

稳定知识应记录：来源、适用范围、版本或环境、最后核验时间、当前有效性。未核验推断留在决策/日志中，不升级为项目事实。

## `task-state.json`

建议把一项复杂任务的结构化记录放在专用的 `records/<TASK-ID>/` 子目录；这也让证据指纹能安全地区分状态元数据与产品改动。`assets/templates/task-state.example.json` 展示完整字段；`scripts/validate_task.py` 校验关键关联。重点约束：

- 每个主任务引用来源；每个指标属于主任务；每个实现任务属于主任务并关联指标或写明必要支撑原因；
- `overall_acceptance` 独立于子任务状态；
- 证据路径位于仓库内并绑定当前补丁；
- `actions` 的 `idempotency_key` 唯一，已完成动作有回执；
- 授权与交付状态分开，授权不能由工具推断。

校验器不会验证文字是否真实、用户是否真的授权或指标是否合理；这些属于主线程审查。
