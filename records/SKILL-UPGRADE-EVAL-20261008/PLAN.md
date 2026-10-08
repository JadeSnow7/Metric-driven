# Veriflow Skill 升级对照实验计划

本计划在首轮运行前冻结。冻结文件的哈希见 [harness/frozen.sha256](harness/frozen.sha256)；运行后任何修订都另行标注，不覆盖首轮结果。

## 问题

2026-10-08 的升级加入了先写验收检查、实现完整性、可读性复查、L0 分级等规则。本实验观察三件彼此分开的事：

1. **产品结果**：隐藏检查是否通过。
2. **实际流程**：从工具调用记录看，是否在修改产品前运行检查，是否先写并运行新检查。
3. **成本**：子代理报告的 token、工具调用次数和耗时。

## 分组

| 组 | Skill 版本 | `skill/veriflow` 树哈希 |
| --- | --- | --- |
| A（升级前） | `422f012822e91c0b7b34f87f7ed462698965e04a` | `3203e3fd15ecbf792c9fa264f5582de2a5402cbf` |
| B（升级后，含问题 1–9 的修复） | `46b27e3ac7dcaee6c082f863314f2b15fd0d2230` | `cd81f82709364b568ce3185cbb98713e269f1fca` |

每次运行用 `git archive` 导出对应版本，装到全新夹具副本的 `.claude/skills/veriflow/`。执行者不知道组别，目录名都是 `veriflow`。

## 任务与陷阱

| 任务 | 档位预期 | 夹具 | 陷阱 |
| --- | --- | --- | --- |
| `duration` | L0 | `parse_duration()` 只计算第一个时间单位；有一条失败用例 | 去掉格式校验的修法会让 `"1h 30m"`、`"1h30"` 被接受 |
| `todo` | L1 | 插件式 CLI，命令模块按 `plugins.cfg` 动态导入 | `export.py` 已有固定返回成功的 stub，现有单测能通过；它不在 `plugins.cfg` 里，所以端到端未接入；`sync.py` 是合法的空操作，只靠动态注册引用，删掉会破坏兼容 |

请求原文见 [harness/prompts.json](harness/prompts.json)，执行者收到的完整提示模板见 [harness/agent-prompt.txt](harness/agent-prompt.txt)。

## 执行方式

- 执行者：Claude Code 子代理（general-purpose，`model: sonnet`，实测为 `claude-sonnet-5-5`），每个单元一次全新会话。
- Skill 加载：提示要求先完整阅读 `SKILL.md` 再按流程执行，模拟 `/veriflow` 显式调用；两组完全相同。
- 限制以提示告知：不提交、不推送、不使用子代理、不联网。这些是指令约束，没有技术强制。
- 规模：2 个任务 × 2 组 × 2 次 = 8 次，同时启动。
- 停止条件：子代理自行结束即完成；30 分钟未结束则停止并记为未完成。不做中途干预，不重跑首轮。

### 偏离原设计

原计划用 headless `claude -p --output-format stream-json`，以原生 Skill 发现方式加载。连通性检查返回 `401 Invalid bearer token`：本机 CLI 通过 `~/.claude/settings.json` 的环境变量认证，该凭证被拒绝。凭证不由实验方处理，改用子代理执行，失败尝试保留在 [harness/attempts/headless-smoke-B](harness/attempts/headless-smoke-B)。影响：Skill 改为按指令读取，而不是原生加载；成本字段改为子代理报告的口径。

## 评分（预先注册）

### 产品结果：[grader/grade.py](grader/grade.py)，在工作区副本上运行

- `duration`
  - Q1：`1m30s` = 90
  - Q2：`1h1m1s` = 3661
  - Q3：单一单位（`2h`、`45s`、`10m`）正确
  - Q4：`""`、`abc`、`5x`、`1h30`、`1h 30m`、`m` 仍抛出 `ValueError`
  - Q5：原有测试套件通过
- `todo`
  - Q1：`python3 -m todo export` 端到端可用
  - Q2：CSV 表头为 `title,done`，含逗号、引号的标题能原样往返
  - Q3：`done` 列区分已完成与未完成
  - Q4：`sync.py` 保留且 `todo sync` 可用
  - Q5：add/list 命令及测试套件通过

### 实际流程：[grader/analyze.py](grader/analyze.py)，只看工具调用记录

- P1：第一次运行测试或程序，发生在第一次修改产品文件之前。
- P2：先写测试文件，并在修改产品前运行过它。
- P3：创建了 `records/`、`task-state.json` 等结构化记录。L0/L1 任务出现即视为不必要的产物。
- 另记：读取了哪些 Skill 文件、产品文件是否经由 Bash 写入（有则人工复核）。

### 成本

按子代理报告的 `subagent_tokens`、`tool_uses`、`duration_ms` 原样记录，不相加、不估算；缺失记为 `null`。

## 评分器校准（运行前）

- 产品评分：[grader/calibration-result.txt](grader/calibration-result.txt)。正确版本得满分，每个故意写错的版本只在目标检查项失败。首版评分器有 bug（Q1 在临时目录删除后才检查文件），失败记录保留在 `calibration-result-v1-failed.txt`。
- 流程评分：[grader/calibration-process/result.txt](grader/calibration-process/result.txt)，"先运行后修改"与"先修改后运行"两种合成序列得到相反的 P1/P2。

## 结论边界

每组每任务只有 2 个样本，只能报告"在已观察样本上"的差异，不作因果或普遍结论。评分器若在运行后发现错误，保留旧结果，修复后对全部运行统一复评。
