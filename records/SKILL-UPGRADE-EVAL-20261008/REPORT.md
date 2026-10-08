# Veriflow Skill 升级对照实验报告

计划见 [PLAN.md](PLAN.md)。每组每个任务只有 2 个样本，以下都是"在已观察样本上"的观察，不是因果结论或普遍规律。

## 结论

- **产品结果**：没有观察到差异。8 次运行的隐藏检查全部 5/5。两个陷阱也都被两组识别：未接入的 stub（8/8 注册进 `plugins.cfg`）和合法的空操作 `sync`（8/8 保留）。题目对 Sonnet 5.5 偏容易，存在天花板效应，区分不出两组。
- **流程差异只出现在 L1 任务**：B 组 2/2 先写新测试，在原 stub 上运行（各 7 个失败），再实现；A 组 0/2，产品和测试在同一条命令里一起写，写完再运行。
- **L0 任务没有差异**：两组 4/4 都在修改前先运行测试复现缺陷，0/4 创建结构化记录。A 版 L0 文案写的是"直接实现并验证"，执行者仍然先复现了。
- **成本**：B 组 token 略高，L0 每次约多 1.0k，L1 约多 1.7k，与 B 版 SKILL.md 多出 1,812 字节（11,454 → 13,266）的方向一致。L1 耗时 B 组更长；L0 耗时两组互有高低。
- **Skill 实际被读取的范围**：8 次运行都只读了 `SKILL.md`，没有打开任何 references 文件。因此 B 组的行为变化只能来自 SKILL.md 正文；references 里的改动（workflow 第 4 步细则、L2 实现前证据记录、design.md 完整性细则）在 L0/L1 任务里没有被触及。

## 逐次结果（分析器 v3）

| run | 组 | 产品 Q | P1 修改前已运行 | P2 先写并运行新检查 | P3 结构化记录 | 读取的 Skill 文件 | subagent_tokens | tool_uses | duration_ms |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| D-A1 | A | 5/5 | Y | N | N | SKILL.md | 55041 | 5 | 24096 |
| D-A2 | A | 5/5 | Y | N | N | SKILL.md | 55370 | 6 | 46622 |
| D-B1 | B | 5/5 | Y | N | N | SKILL.md | 56196 | 6 | 26465 |
| D-B2 | B | 5/5 | Y | N | N | SKILL.md | 56061 | 5 | 25496 |
| T-A1 | A | 5/5 | Y | N | N | SKILL.md | 58812 | 8 | 39956 |
| T-A2 | A | 5/5 | Y | N | N | SKILL.md | 59076 | 7 | 37514 |
| T-B1 | B | 5/5 | Y | **Y** | N | SKILL.md | 60728 | 8 | 45939 |
| T-B2 | B | 5/5 | Y | **Y** | N | SKILL.md | 60494 | 7 | 47993 |

- L0（duration）任务的 P2 记为 N，是因为四次都在复现之后同时补测试和修复，现有失败用例本身就是检查。按 B 版规则，L0 不要求先写新检查，所以这不算违规。
- 成本字段取自子代理完成通知，原样记录：`tool_uses` 含最后的回报调用；`subagent_tokens` 的口径未说明是否包含初始上下文，不与其他口径相加。

## 人工核对

- **T-B1、T-B2**：第 4 步用 heredoc 写入 `tests/test_export.py`，同一条命令随后运行测试，输出 `Ran 11 tests ... FAILED (failures=7)`，T-B1 另有 `todo export` 返回 `usage ... exit=2`；第 5 步才写 `todo/commands/export.py`。
- **T-A1、T-A2**：分别在第 4 步和第 5 步，一条命令里同时写 `export.py`、`plugins.cfg`、`tests/test_export.py`，之后才运行测试。
- **D 组四次**：第 2 或第 3 步运行 `unittest`，看到 `60 != 90`，下一步才修改 `duration.py`。

## 评估方法修订（首轮结果均保留）

| 版本 | 问题 | 发现时间 | 处理 |
| --- | --- | --- | --- |
| grader v1 | todo 的 Q1 在临时目录删除后才检查文件，正确版本也判失败 | 运行前校准 | 修复后重新校准；失败记录见 `grader/calibration-result-v1-failed.txt` |
| analyzer v1 | 产品路径正则以 `$` 结尾，漏掉经由 Bash heredoc 或 Python 写入的修改 | D-A1 收尾时，结果与 diff 不符 | 保留 `runs/D-A1/process-v1.json` 和 `grader/analyze-v1.py` |
| analyzer v2 | heredoc 写入测试文件时，因测试代码里出现产品路径，被误判为修改产品；同一命令里"先写后运行"未计入 | 全部收尾后人工复核 T-B 自述与 P2 不符 | 保留每次运行的 `process-v2.json`、`summary-analyzer-v2.md` 和 `grader/analyze-v2.py` |
| analyzer v3 | 有重定向目标时只按目标文件分类；heredoc 之后的运行算作写入之后 | — | 对 8 次运行统一复评，并补充合成校准样本（`grader/calibration-process/result-v3.txt`） |

`harness/frozen.sha256` 中只有 `grader/analyze.py` 与冻结时不同，原因即上表的 v1 → v3。

## 偏离与限制

- **执行方式**：改为子代理执行，Skill 通过 Read 加载，不是原生的 `/veriflow` 加载。原因是 headless `claude -p` 认证失败，记录在 PLAN.md。
- **原始记录已脱敏**：子代理原始记录含会话附件（账户与环境信息），仓库里只保存 `transcript.redacted.jsonl`，只保留助手的工具调用与工具返回。脱敏前后分析结果逐项一致；脱敏脚本为 `harness/redact.py`。
- **限制只靠指令约束**：执行者被要求只修改工作目录内的文件。T-A1、T-B1、T-B2 在 `/tmp` 下建了临时目录用于手动验证，没有改动工作目录外的项目文件。
- **覆盖范围**：只有一个模型（Sonnet 5.5）、两个小任务，没有 L2 任务和子代理委派场景；题目对两组都没有难度。

## 对 Skill 维护的含义

1. 在 L1 任务上，B 版的"先写验收检查"确实改变了执行顺序，产品结果没有变差，成本小幅增加。这是本次唯一观察到的流程效果。
2. 实现完整性规则的价值在本实验中**未被证实**。A 版和模型本身就识别出了未接入的 stub。要检验这条规则，需要更隐蔽的陷阱或更弱的模型。
3. L0/L1 执行者只读 SKILL.md，所以影响这两档行为的规则必须写在 SKILL.md 里；references 里的改动只对显式读取它们的 L2 或复杂任务有意义。之前把规则正文收拢到 references、SKILL.md 只留一句加链接的做法，对 L0/L1 是否仍然有效，应在后续实验中专门观察。
4. 后续实验建议：
   - 加一个 L2 任务（跨会话恢复，或需要 `record_execution` 的任务）；
   - 加一组 Haiku 执行者；
   - 设计更隐蔽的空实现陷阱，例如吞掉错误后返回成功；
   - 每组至少 5 次。
