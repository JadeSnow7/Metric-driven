# 工程决策记录

## BOUNDARY-20261004：验证驱动编排的职责边界

来源：用户于 2026-10-04 要求按“Rein 单 Agent runtime、Veriflow 编排与验证、Web Studio 环境与观测”的分工同步两个公开仓库，优先文档与接口，不大搬代码。状态：本轮只改文档与契约；下表里的产品实现切片均未实施。

### 审查基线与公开接口

| 固定版本 | 当前事实 |
| --- | --- |
| Veriflow main `599c380a8dfeaadeff3a4d542b34071800996a29` | 没有根 DECISIONS / ADR 或独立编排引擎；`skill/evidence-driven-development/` 包含规则、交接模板与 schema 1.1。`validate_task.py` 接受 manifest、`--repo`、`--gate record / implementation / local-commit / push / merge / deploy`，输出 `ok / gate / current_revision / errors / warnings / limits`；退出 0/1/2 分别为无错误、门槛错误、运行错误。`--print-revision / --print-sha256` 为辅助读取 |
| Veriflow [PR #3](https://github.com/JadeSnow7/Veriflow/pull/3) `422f012822e91c0b7b34f87f7ed462698965e04a` | 已有新 skill 入口、schema 1.3 Spec 绑定、`record_execution.py`、`integrate_boundary.py` 与 Claude Code 包装。未合并，保持与 main 状态分开；记录器运行检查命令不等于跨 Agent 调度器 |
| Rein main `93fd7203428962ae741cc86b8d7e87657341df64` | 书与 Python/TS/Rust 教学接口，无统一产品 runtime port |
| Rein [PR #3](https://github.com/JadeSnow7/Rein/pull/3) `44e3454337c06f53f13880a2fe9e35336a387812` | 已有 R1a 的纯步进、SQLite/outbox、产物及固定 verifier；公开 CLI 为 `demo / show / resume / cancel / schema`，没有完整控制协议、Coordinator 或 DAG |

审查的两仓 main 与在途树未提供生效的根 AGENTS.md。Web Studio 本轮只定义边界，没有读取或修改其源码；不判断其 provider 当前实现程度。

### 决定与数据所有权

| 数据 / 行为 | 唯一权威 |
| --- | --- |
| 业务目标与验收条件的依据 | 用户与目标项目契约；Veriflow 保存来源及版本 |
| 工作流、任务依赖、资源选择、尝试分派、全局预算、重试/修复 | Veriflow |
| 单 Agent 的模型与上下文、工具执行、权限/批准执行、局部预算、取消与 effect 恢复 | Rein |
| VerificationPlan、证据有效性、失败诊断、EvidenceBundle、整体验收 | Veriflow；检查执行器与原始回执来自 Rein、CI 或环境 provider |
| run/session/effect 与执行事件 | Rein；Veriflow 保存引用和消费游标，不双写运行层存储 |
| Web/终端环境、CDP、预览、截图/日志/状态采样、diff/人工审阅 UI | Web Studio；通用工具宿主仍可在 Rein 调用 provider |

连接使用 [编排与验证契约候选](contracts/orchestration-v0.1.md) 引用的 Rein RuntimePort。独立 Rein 仍能执行一个有界任务或固定检查；这不赋予它跨任务验收或自动调度其他 Agent 的职责。

保留 EDD skill 与 schema 1.1 的已有功能和“没有自动创建执行器”的事实说明。未来编排能力属于产品范围，并在用户授权与宿主权限内工作；不把原来的能力描述误读为永久禁止调度。现有校验器通过只证明其实际检查的记录一致性，不能据此推断产品通过或授权真实。

### 在途变更与兼容

本轮从 main 建独立文档分支，不合并或重写 PR #3，不改 skill 文件、模板、validator 和 schema 版本。编排契约 `veriflow.orchestration/0.1-draft` 是新产品边界，**不是** `task-state.json` 1.1 的新字段规范。

PR #3 合并时保留更新后的 README 分工和本决定，同时承接其 `skill/veriflow/` 名称、schema 1.3 与 recorder 实现；不能因本轮 README 仍列 main 的旧目录而退回代码或旧记录格式。若需要投影，adapter 必须显式记录源 schema、Spec 与输入/候选摘要及实际规则版本；禁止给历史 1.1 记录补造未执行过的检查或授权。

Rein PR #3 的 D12–D14 与三产品整合设计目前仍把 Coordinator / DAG / 整体验收归 Rein、Veriflow 仅作方法和规则投影。该分工已由本轮用户指令替代：Veriflow 的 task 状态与 Rein 的 session 状态分别维护，通过尝试与回执绑定协作。底层局部验证与未知 effect 恢复保留在 Rein；无需现在搬迁源码。

### 后续最小切片（计划，不是交付清单）

| 切片 | 改动与依赖 | 验收条件 |
| --- | --- | --- |
| V1：纯规则内核 | 验收契约/任务图/尝试/证据的权威类型与版本；先不启动 Agent | 环、缺依赖/缺验收拒绝；失败/过期/无法判定证据不放行；旧 skill 命令可继续使用 |
| V2：串行 adapter | 消费 Rein RuntimePort 的一个实例，运行两个有依赖的只读任务；维护尝试绑定和事件游标 | 只有上游验收通过才启动下游；重复请求/事件不增加执行次数；runtime 完成不能直接通过 |
| V3：验证与有界修复 | 独立检查执行器、原始回执、诊断与 RepairRequest；可复用 PR #3 recorder，但不双跑检查 | 候选或 Spec 变化使证据 stale；工具故障为 undetermined；修复次数与预算有上限，旧证据不覆盖 |
| V4：跨 Agent 与 Web 场景 | 在 V2/V3 通过后，资源选择、文件写入所有权与全局预算；Web Studio provider 单独接入 | 两 Agent 写范围不冲突；取消/断连不重复副作用；网页业务断言与人工决定绑定同一候选 |

首个闭环只需串行任务与现有 CLI/进程适配，不要求并行调度、daemon、完整项目管理界面或部署平台。交付实现时分别报告本地检查、真实模型、跨 Agent 与 Web 原生界面的证据，不能用其中一种替代另一种。

## 合并后状态（2026-10-05）

以上版本表保留 2026-10-04 的审查事实。PR #3 已合并，当前实现采用 `skill/veriflow/`、schema 1.3、recorder、整合工具及 Claude Code 包装，并保持 1.1/1.2 历史兼容；不退回旧目录与旧格式。Rein PR #3 的离线运行时亦已合并，RuntimePort 与本仓编排契约仍是待实现候选。保留本决定的 Veriflow workflow / Rein runtime / Web Studio 环境分工；没有在此次合并中实现 V1–V4 或迁移源码。
