# Veriflow

Veriflow 的产品职责是 **验证驱动的编排**：验收契约、任务拆解与依赖、跨 Agent 调度、验证、失败诊断与修复安排、证据组织及整体验收。

**当前 main 实现仍是 Evidence-Driven Development Skill 与只读记录校验器，没有独立编排引擎。** 产品边界与下文的契约候选描述后续实现方向，不把未来能力记为已经完成。

一个面向 Codex 的工程方法 skill：把模糊或复杂的软件开发请求整理成可交付链条，并用真实 diff、可复查证据、明确权限和停止条件约束执行。

它解决的不是“怎样写更多流程文档”，而是四个容易失真的位置：需求尚未支持实现决策、指标与任务错位、代理自报通过、以及恢复任务时重复产生副作用。

## 产品分工与实现状态

| 项目 | 拥有的职责 | 稳定交接的方向 |
| --- | --- | --- |
| Veriflow | AcceptanceContract、任务图、尝试分派、验证计划与结果、诊断/修复策略、证据包和人工审阅结论 | 通过 RuntimePort 提交一个有界尝试；聚合证据后决定工作流是否通过 |
| [Rein](https://github.com/JadeSnow7/Rein) | 单 Agent 的模型适配、上下文、工具循环、权限执行、局部预算、取消、恢复、事件和原始回执 | 执行已经分派的尝试；不替 Veriflow 计算任务依赖或整体验收 |
| [Web Studio](https://github.com/JadeSnow7/Web-Studio) | Web 工作空间、浏览器/终端、CDP、页面操作、截图/日志/状态观测、预览、调试与审阅界面 | 提供受信环境能力和原始观测；人工决定绑定当前候选版本返回 |

| 位置 | 已有能力与限制 |
| --- | --- |
| main：`skill/evidence-driven-development/` | 工程方法、模板、schema 1.1 记录与 `validate_task.py` 门槛；宿主或人负责实际执行与调度 |
| 未合并的 [PR #3](https://github.com/JadeSnow7/Veriflow/pull/3)，审查提交 `422f012` | `skill/veriflow/`、schema 1.3 的 Spec 绑定、执行记录器、整合辅助与 Claude Code 包装；不是 main 能力，也不是独立任务图调度器 |
| 本轮 [编排与验证契约候选](contracts/orchestration-v0.1.md) | 定义跨层职责、数据绑定与验收语义；没有新增调度器、会话创建器或 RuntimePort adapter |

本轮决定、在途 PR 的兼容处理和实施切片见 [DECISIONS.md](DECISIONS.md)。保留现有 skill 名称、路径、记录 schema 与 CLI，不为产品定位重命名或搬迁源码。

## 仓库结构

```text
skill/evidence-driven-development/
├── SKILL.md                         # 精简入口与强约束
├── agents/openai.yaml               # Codex 展示与默认调用信息
├── references/                      # 按需读取的详细流程
├── assets/templates/                # 可复制、可裁剪的任务与交接模板
├── scripts/validate_task.py         # 只读任务记录/门槛校验器
└── tests/test_scenarios.py          # 隔离临时仓库中的关键反例与放行路径
tools/validate_repository.py         # 仓库结构与内部链接检查（不属于 skill 本体）
.github/workflows/ci.yml             # 在 Python 3.11–3.13 上运行仓库已有检查
contracts/orchestration-v0.1.md      # 待实现的编排/验证契约，引用 Rein RuntimePort
DECISIONS.md                        # 当前产品边界、审查依据与实施切片
```

## 安装

Skill 本体是 `skill/evidence-driven-development/`，可独立复制或链接到 Codex 的 skills 目录：

```bash
mkdir -p "${CODEX_HOME:-$HOME/.codex}/skills"
cp -R skill/evidence-driven-development "${CODEX_HOME:-$HOME/.codex}/skills/evidence-driven-development"
```

开发时也可建立符号链接：

```bash
ln -s "$(pwd)/skill/evidence-driven-development" "${CODEX_HOME:-$HOME/.codex}/skills/evidence-driven-development"
```

若目标位置已存在，请先人工确认其身份；不要用上述命令覆盖已有 skill。

## 依赖

- 使用 skill：支持本地 skills 的 Codex 环境；无强制 MCP 或外部服务依赖。
- 运行校验器：Python 3.11+ 与 Git。
- 运行 CI：GitHub Actions 的 `checkout` 和 `setup-python`；仓库本身不会创建远程仓库或开启发布。

## 调用

显式调用示例：

```text
Use $evidence-driven-development to implement this feature and leave verifiable evidence.
```

中文示例：

```text
使用 $evidence-driven-development 接手这个已有任务，先核验当前状态，再完成实现与本地提交；不要推送。
```

自动发现保持开启。若任务简单且低风险，skill 应裁剪记录；复杂、跨会话、多人协作或具有外部副作用时，才使用完整任务状态与交接模板。

## 验证工具

仓库自检：

```bash
python3 tools/validate_repository.py
python3 -m unittest discover -s skill/evidence-driven-development/tests -v
```

检查一个结构化任务记录：

```bash
python3 skill/evidence-driven-development/scripts/validate_task.py records/TASK-001/task-state.json --repo . --gate record
python3 skill/evidence-driven-development/scripts/validate_task.py records/TASK-001/task-state.json --repo . --print-revision
python3 skill/evidence-driven-development/scripts/validate_task.py records/TASK-001/task-state.json --repo . --print-sha256 records/TASK-001/evidence/unit-tests.txt
python3 skill/evidence-driven-development/scripts/validate_task.py records/TASK-001/task-state.json --repo . --gate local-commit
```

`validate_task.py` 只读取文件和 Git 状态。它能检查字段、ID 引用、门槛状态、证据文件存在性与 sha256、证据是否仍绑定当前补丁、改动路径是否经过审查，以及授权与已执行动作的一致性。输出为 JSON，退出码 `0` 无错误、`1` 记录或门槛错误、`2` 运行错误。它不能证明需求真实、数字合理、测试覆盖充分、授权来源真实或产品已经成功；这些仍由主线程审查。

## 记录格式版本

当前 `task-state.json` 格式为 `1.1`。相对 `1.0`：

- 证据新增 `sha256`，从 `local-commit` 门槛起必填；
- revision token 改为内容指纹（`revision-v2`），暂存或提交改动不再使证据过期，也不受本地 diff 配置影响；
- `records/<TASK-ID>/evidence/` 不计入指纹，新增证据不会让已有证据失效。

`1.0` 记录的迁移步骤见 [records.md](skill/evidence-driven-development/references/records.md) 的 `task-state.json` 一节。

## 当前实现与产品边界

- Veriflow 面向开发任务的编排与验证，仍不做通用项目管理平台、测试框架、CI 服务或部署平台。
- 当前 skill 与校验脚本不自动创建新会话、子代理、worktree、提交、远程仓库或部署；已有委派/交接规则由宿主在用户授权范围内执行。此处是当前实现说明，不是对未来 orchestration adapter 的永久禁止。
- 后续调度器通过显式执行策略与能力协商调用 Rein/provider；跨 Agent 选择、全局预算、依赖和修复属于 Veriflow，单次执行控制属于 Rein。commit / push / merge / deploy 仍分别受用户已有授权与宿主权限约束。
- 不把搜索结果、代理建议或通过的 CI 当作用户授权。
- 不保证节省 token，也不要求每个小修复生成全套记录。
- 自动化检查只覆盖它实际读取到的结构和状态，不替代人类对产品结果的判断。
- 不直接操作 Rein 的 SQLite/会话状态，也不将 runtime 完成或局部 verifier 通过直接写成工作流通过。

## 许可证

本仓库采用 [Apache License 2.0](LICENSE)。再分发时需保留许可证文本并说明所做修改；提交到本仓库的贡献默认按同一许可证授权（许可证第 5 条）。
