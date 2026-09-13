# Evidence-Driven Development Skill

一个面向 Codex 的工程方法 skill：把模糊或复杂的软件开发请求整理成可交付链条，并用真实 diff、可复查证据、明确权限和停止条件约束执行。

它解决的不是“怎样写更多流程文档”，而是四个容易失真的位置：需求尚未支持实现决策、指标与任务错位、代理自报通过、以及恢复任务时重复产生副作用。

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

## 能力边界

- 不是项目管理平台、测试框架、CI 服务或发布系统。
- 不自动创建新会话、子代理、worktree、提交、远程仓库或部署。
- 不把搜索结果、代理建议或通过的 CI 当作用户授权。
- 不保证节省 token，也不要求每个小修复生成全套记录。
- 自动化检查只覆盖它实际读取到的结构和状态，不替代人类对产品结果的判断。

## 许可状态

本仓库尚未选择开放源代码许可。具体含义见 [LICENSE.md](LICENSE.md)。在权利人明确选择许可之前，不应把本仓库视为已获授权的开源项目。
