# Veriflow Skill

一个面向 Codex 与 Claude Code 的工程方法 skill：把模糊或复杂的软件开发请求整理成可交付链条，并用真实 diff、可复查证据、明确权限和停止条件约束执行。

项目仓库：[JadeSnow7/Veriflow](https://github.com/JadeSnow7/Veriflow)

它连接需求就绪、设计边界、指标验收和恢复执行：明确模块职责与 API 契约，用原始证据核验代理产物，并追踪有副作用的动作。

## 仓库结构

```text
skill/veriflow/
├── SKILL.md                         # 精简入口与强约束
├── agents/openai.yaml               # Codex 展示与默认调用信息
├── agents/claude-code/              # Claude Code 子代理定义：veriflow-coder、veriflow-reviewer（Sonnet）
├── references/                      # 按需读取的详细流程；claude-code.md 说明 Claude Code 下的模型分工与工具对应
├── assets/templates/                # 可复制、可裁剪的任务与交接模板
├── scripts/validate_task.py         # 只读任务记录/门槛校验器
├── scripts/record_execution.py      # 运行一条检查命令并写入绑定 revision 的执行记录
├── scripts/integrate_boundary.py    # 交接整合前的逐文件哈希与路径检查
├── tests/test_scenarios.py          # 隔离临时仓库中的门槛反例与放行路径
└── tests/test_tools.py              # 执行记录器与整合工具的行为测试
claude-code/                         # Claude Code 插件包装：plugin.json，skills/、agents/ 为指向 skill 的符号链接
tools/validate_repository.py         # 仓库级结构、内部链接与 Claude Code 定义检查
.github/workflows/ci.yml             # 在 Python 3.11–3.13 上运行仓库已有检查
```

## 安装

Skill 本体是 `skill/veriflow/`。

### Codex

复制或链接到 Codex 的 skills 目录：

```bash
mkdir -p "${CODEX_HOME:-$HOME/.codex}/skills"
cp -R skill/veriflow "${CODEX_HOME:-$HOME/.codex}/skills/veriflow"
```

开发时也可建立符号链接：

```bash
ln -s "$(pwd)/skill/veriflow" "${CODEX_HOME:-$HOME/.codex}/skills/veriflow"
```

### Claude Code

主线程使用 Opus 或 Fable，编码与独立审查子代理固定使用 Sonnet（定义在 `skill/veriflow/agents/claude-code/`）。只在当前会话试用时，从仓库根目录加载插件包装：

```bash
claude --model opus --plugin-dir ./claude-code
```

此时 skill 名为 `veriflow:veriflow`，子代理为 `veriflow:veriflow-coder`、`veriflow:veriflow-reviewer`。长期使用时复制到用户目录，名称为 `veriflow`、`veriflow-coder` 和 `veriflow-reviewer`：

```bash
mkdir -p ~/.claude/skills ~/.claude/agents
cp -R skill/veriflow ~/.claude/skills/veriflow
cp skill/veriflow/agents/claude-code/*.md ~/.claude/agents/
```

也可以复制到项目的 `.claude/skills/` 与 `.claude/agents/`。主线程模型用 `--model fable`、`--model opus` 或会话内 `/model` 切换；子代理模型由定义文件决定，调用时沿用定义文件或显式传 `sonnet`。细节见 [claude-code.md](skill/veriflow/references/claude-code.md)。

上述复制命令用于空目标目录；目标位置已存在时，先核对身份、备份内容，再决定更新方式。

仓库保留 `skill/evidence-driven-development` 到 `skill/veriflow` 的兼容符号链接，用于维持历史记录中的旧路径链接；新的安装和调用名称统一使用 `veriflow`。

## 依赖

- 使用 skill：支持本地 skills 的 Codex，或 Claude Code（2.1.272 上验证）；无强制 MCP 或外部服务依赖。Claude Code 的模型分工需要账户能使用 Opus 或 Fable，以及 Sonnet。
- 运行校验器：Python 3.11+ 与 Git。
- 运行 CI：GitHub Actions 的 `checkout` 和 `setup-python`；远程仓库与发布流程按用户授权配置。

## 调用

显式调用示例：

```text
Use $veriflow to implement this feature and leave verifiable evidence.
```

中文示例：

```text
使用 $veriflow 接手这个已有任务，先核验当前状态，交付范围为实现、本地验证与本地提交。
```

Claude Code 中用 `/veriflow`（插件方式为 `/veriflow:veriflow`）显式调用，或直接描述任务由自动发现加载：

```text
/veriflow 为 todo 工具增加 CSV 导入，用子代理实现并独立审查，交付到本地提交。
```

自动发现保持开启。Skill 每次先判断档位：**L0 轻量**（目标和验收都明确的小改动，可含已授权的本地提交，指明复验所用检查（缺陷先复现），实现后复验，证据留在简短回报中）、**L1 标准**（多个可观察结果或分散改动，先写明目标、验收和基线）、**L2 完整**（跨会话恢复、多人或多 Agent、迁移或部署等难以撤销的动作，使用结构化任务状态、校验器与交接模板）。先澄清需求，再按任务影响选择档位。

工作区里已有的无关未提交改动会被保留：不重叠时直接在原目录继续，提交只加入本任务审查过的路径；只有路径重叠或存在依赖时才询问。

写教程、README、设计/接口说明或报告时，先分析文体、读者、用途和阅读方式，再选择组织方式；教程采用教学叙事，其他文体按各自阅读目的组织。已划分子任务完成后立即回报并由主线程核查、更新进度，相关文档在同一子任务内同步。

## 设计方法

需求与验收就绪后，按结构影响完成设计，再拆实现任务。执行顺序为 **Spec → 设计与计划 → 验收检查 → 实现 → 同一检查复验与回归 → 逐项验收 → 授权交付**。验收检查的写法见 [workflow.md](skill/veriflow/references/workflow.md)。局部修复确认现有边界；跨模块改动明确职责与依赖方向；API 变化沿用权威契约来源，按模块归属同步消费者、类型、文档和测试。涉及状态或协议时补充适用的并发、失败、兼容与迁移语义。

实现完整性要求从本次约定入口追踪到可观察结果，识别未接入、固定成功等空实现。详细步骤及示例见 [design.md](skill/veriflow/references/design.md)。设计写入已有摘要或实现合同，交接模板和 Claude Code 编码、审查子代理沿同一组约束工作。指导文字采用动作、方法、执行条件与完成标准表达。

## 验证工具

仓库自检：

```bash
python3 tools/validate_repository.py
python3 -m unittest discover -s skill/veriflow/tests -v
python3 -m unittest tools/tests/test_validate_repository.py -v
```

运行一条检查并留下执行记录，再检查结构化任务记录：

```bash
python3 skill/veriflow/scripts/record_execution.py --output records/TASK-001/evidence/unit-tests.json --repo . --state records/TASK-001/task-state.json -- python3 -m unittest
python3 skill/veriflow/scripts/validate_task.py records/TASK-001/task-state.json --repo . --gate record
python3 skill/veriflow/scripts/validate_task.py records/TASK-001/task-state.json --repo . --gate acceptance
python3 skill/veriflow/scripts/validate_task.py records/TASK-001/task-state.json --repo . --gate local-commit
python3 skill/veriflow/scripts/validate_task.py records/TASK-001/task-state.json --repo . --gate push --target origin/feature-x
python3 skill/veriflow/scripts/validate_task.py records/TASK-001/task-state.json --repo . --gate action --action migrate --target db:staging
```

第一条命令会运行 `python3 -m unittest` 并写入证据文件；其余命令只读。检查运行期间若生成了未被忽略的文件（例如 `__pycache__/`），记录结果会是 `revision_changed` 并列出路径，把它们加入 `.gitignore` 后重跑。

`validate_task.py` 只读取文件和 Git 状态，由程序实际检查的内容：

- 字段、ID 引用、状态取值、证据文件存在性与 sha256；
- 执行记录是否自洽，记录内的 revision 是否等于当前内容（只刷新字段、不重跑检查会被发现）；
- 基线以来的改动路径和已提交路径是否都经过审查，他人无关改动（`foreign_paths`）是否与任务文件重叠；
- 授权来源、授权范围、已执行动作是否获授权；结果不明的动作和同一版本的重复动作会被阻断；
- 延后验证的指标是否有用户决策，强制与非退化指标在合并、部署及自定义动作前阻断；schema 1.3 的整体验收不能引用延期指标。

输出为 JSON，退出码 `0` 无错误、`1` 记录或门槛错误、`2` 运行错误；git 调用设有超时。主线程进一步核查需求、指标依据、测试覆盖、授权来源、远程 CI 和产品实际行为；模板占位检查不分析产品代码空实现。完整完成与部分验收的判定见 [metrics-and-evidence.md](skill/veriflow/references/metrics-and-evidence.md)。

## 记录格式版本

当前 `task-state.json` 格式为 `1.3`。校验器仍接受 `1.1`/`1.2` 并保留各自旧语义；旧记录不会被补写成新的 Spec 绑定。

相对 `1.2`，`1.3` 增加：

- `state.spec` 的版本、权威位置、来源、复用的 `discovery` 引用、条件、契约和未决项；`state.binding.receipt_paths` 是运行回执的唯一正式位置；
- 产品 revision 与 Spec 内容 digest 的组合绑定。完整 Spec、全部主任务和指标规范字段、契约文件字节哈希、交付物与外部输入声明均按精确位置进入摘要；运行状态和证据引用不进入摘要；
- 每个条件独立关联至少一个 `mandatory_gate`/`non_regression` 指标和具体交付文件。契约文件必须存在并按字节哈希；交付物可在实现前缺失，验收时再检查。

`deferred` 仅用于指标，保留 1.2 的“用户决定稍后验证”语义，整体验收不能延期，判定见 [metrics-and-evidence.md](skill/veriflow/references/metrics-and-evidence.md)；旧记录迁移须保留 raw 与 stale 原因，不能补造历史绑定或授权快照。

相对 `1.1`：

- `actions[]` 新增 `target` 与 `revision`，重复检查按版本进行，审查后的追加提交和推送可以通过；`in_progress`、`unknown` 的动作在核验前阻断；
- 授权可以带 `scope`，并可增加 `migrate` 等自定义动作，由 `--gate action` 检查；
- 执行记录自带运行前后的 revision；指标新增 `verification`（`execution` / `manual`）和 `deferred` 状态；
- `baseline.foreign_paths` 记录他人的无关改动，推送门槛检查已审查的提交内容；
- `delivery` 只保留 `local_validation`、`remote_ci`、`remote_ci_revision`，动作进度只记在 `actions`。

迁移步骤见 [records.md](skill/veriflow/references/records.md) 的“版本迁移”。

## 使用方式

- 在现有项目、测试框架与 CI 中采用本 skill 的设计、验证和交付流程。
- 根据用户授权创建会话、委派、隔离工作区及推进交付。
- 以用户指令判断授权，以检索、建议和检查结果支撑决策。
- 按任务影响选择记录与检查深度，用实际运行评估成本和效果。
- 自动化核查结构与状态，主线程审查产品结果。

## 许可证

本仓库采用 [Apache License 2.0](LICENSE)。再分发时需保留许可证文本并说明所做修改；提交到本仓库的贡献默认按同一许可证授权（许可证第 5 条）。
