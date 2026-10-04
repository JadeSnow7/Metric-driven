# 工作日志

## EVENT-001：现场恢复与委派就绪

- 来源：当前用户请求；仓库内无新增适用 AGENTS.md，遵循用户提供的全局路由。
- 主线程读取入口、全部指定参考、模板、脚本与测试相关实现及六份近期材料。历史报告仅作调查入口。
- 原目录 git status 超时，逐文件快照到临时隔离目录；HEAD/分支与限定路径 status/diff 成功。未把超时当成干净状态。
- Spec VF-SPEC-1 及其冻结副本先于实现委派建立，coder 独占指定源码/测试/文档路径，主线程独占 Spec 与本轮共享记录。
- 基线验证：skill 60 项、仓库校验 12 项通过。主线程用冻结基线实际构造反例，确认本轮缺陷仍存在。
- 方法偏差：首次提取基线 tar 使用 Python 3.9 不支持的 filter 参数，退出 1；改为逐成员验证路径/类型后提取自有 git archive，未改变原仓库。
- 原始材料：baseline-manifest.json、source-git-probes.json、baseline-tests.txt、baseline-repository-tests.txt、baseline-counterexamples.json。

## EVENT-002：设计补充

- 主线程读实际控制流，发现后续交付 gate 也把历史前置动作与当前授权混用，已通知 coder 同边界修复。
- 记录器 after 阶段应重读 state，避免运行中修改 Spec/分类而仍使用旧内存状态；纳入 SC-03 原定义的版本绑定验证，不降低标准。

## EVENT-003：支持关系反例与验证环境

- 主线程在冻结基线中只把 EVD-001.supports 改成 MET-002，保留 MET-001 对它的引用；acceptance 返回 0。这是 SC-01 对应条件关联的当前缺陷，已交 coder 增补独立回归，见 baseline-support-counterexample.json。
- 隔离目录默认 python3 是 3.9.6，原工作目录默认是 3.14.6；明确选择已核实的 Python 3.11.15 复跑。冻结基线 60 项在 3.11 通过；原始 record_execution 输出见 baseline-python311.json。
- 文档更新分配第二个 coder，互斥所有权已发给双方；工具 coder 继续独占脚本/测试/schema 参考，文档 coder 负责入口/流程/委派/写作/Claude 定义及非 JSON 模板。主线程保留 Spec 与本轮报告。

## EVENT-004：退回首版与缩小实现边界

- 文档首版实际 diff 暴露模板路径误解：三个模板误写在 skill 根目录，真实 templates 未更新；流程步骤也存在重复。主线程已退回同一文档 coder 修正，仅处理其本轮产物。
- 工具 coder 长时间未返回独立可运行结果，部分草稿仍存在 Spec hash 未进入摘要等问题。主线程停止其写入，保存 interrupted-draft 下两份源码文本及完整差异，不把草稿算作完成。
- 新 fresh-context coder 接管更小 SC-01/02 边界，仅在基线 1.2 上修历史证据/fixture，随后再独立实现版本绑定和授权。前任草稿的两个脚本允许从隔离 HEAD 恢复，原工作区及既有内容不变。

## EVENT-005：分边界审查结果

- 主线程读取并复跑授权模块9项回归通过；首次反例发现类型崩溃、重复scope矛盾和无效日期，修复后保留各次证据。模块尚待与任务gate集成，不等于SC-04整体通过。
- 授权coder曾覆盖execution-v2.json中的失败结果；主线程此前已读到该原文，独立保存在tool-observed-v2-failure.json并注明这是工具观察的保存副本而非新运行。后续使用新文件名。首次execution-log.json为回报转录，不作原始通道证据。
- 历史证据主线程真实CLI反例：新current加旧stale放行、只用stale拒绝、篡改旧原件拒绝。外部fixture未声明时在执行前拒绝，完整声明时recorder和record gate通过。
- 追加反例发现ignored symlink fixture在命令中改指向其他输入而recorder仍passed。已交当前脚本owner修复并补回归，SC-02尚未完整通过。
- 流程文档v3实际读回确认主要纠正已落盘，原始subprocess检查记录存在。前两个文档版本的问题与失败说明保留；完整schema文档仍依赖后续工具结果。
- 1.3 Spec绑定/验收和授权gate集成由fresh-context coder独占脚本与schema文档；另一个coder仅补历史证据测试，不再写这些脚本。

## 2026-09-16T10:07:00Z — EVENT-006

Spec VF-SPEC-1 未变。主线程继续实际 diff 审查，发现 fixture 测试仍使用共享临时父目录；实现者已改为独立 root/repo 与 root/external，并连续运行两次 5 项测试通过，原始 stderr 与计时留存。流程文档 v4 已恢复既有来源/结果拆分/Git 超时语义并加入复杂验证校准；仍在做最后一致性修正。Spec 绑定工具尚在实施，未视为完成。

skill-creator 快速检查首次因 Python 3.11 缺 PyYAML 未执行成功；临时目录安装 PyYAML 6.0.3 后实际复跑通过（skill-frontmatter-check-v2.json）。未修改系统依赖或已安装 skill。该检查只证明入口格式，不证明行为。

## 2026-09-16T10:15:00Z — EVENT-007

Spec VF-SPEC-1 未变。主线程拒绝了 Spec 绑定初稿的完成声明：实际新增测试仍为 3 个辅助函数检查，原 E2E 脚本只记录命令并用不完整 state 调用 record，没有验收、恢复或动作闭环。该稿与日志留存于 evidence/spec-coder/，不作为 SC-07 通过依据。改为互斥所有权：规范模型/模板/参考文档一位 coder，CLI 场景回归另一位 coder，脚本修正待测试反馈后继续。主线程已编写独立实际端到端验证脚本 evidence/primary_e2e.py，尚未运行。

回写前源文件预检完成 43 项；唯一漂移是 tools/.DS_Store（Finder 元数据），不在本轮允许回写路径中，保留源现状。其余基线内容一致。该预检不能替代最终回写时的逐文件检查。

## EVENT-008 最终审查与验证

主线程读取实际代码/文档 diff，复跑最终 85 项工具测试、12 项仓库测试及静态检查，原始结果见 final-checks-3；最终 E2E、23 次反例门槛、fixture 和 6 次授权链门槛均通过。两次冻结行为观察产物已独立核验；过程不可观察项与最终补修版本差异如实保留。Spec 初始基线项数笔误更正为实际清单 43 项，不改冻结 Spec。回写待执行。

## EVENT-009 原目录回写与读回

integrate_boundary.py 按源 HEAD、目标 HEAD、允许路径、逐文件源/目标哈希预检后回写 278 个文件；全部读回匹配。27 个产品/skill 文件更新，其余为本轮记录。原有 tools 两处修改保持基线字节，原目录 HEAD 未变化。最终报告与回执采用增量清单再次同步；未执行安装、原仓库提交、推送、合并或发布。

EVENT-010：原目录回写后全仓库静态扫描 30 秒超时；限定 diff 检查通过。保留为原目录扫描未完成，不以隔离通过冒充原目录运行通过。
