# Veriflow 实验反馈升级

已完成六份 skill 文档的升级及主线程审查。已安装目录是指向本仓库的软链接，当前文件同步可见。原有脚本、测试和 schema 没有修改；未在原仓库提交、推送、合并或部署。

## 改了什么

| 改进 | 实验依据 | 落点 |
|---|---|---|
| 校验输入确实到达目标路径，识别空集合断言与包装层替代真实链路的误判 | CH08 评审与生产修复中的验证方法缺陷 | metrics-and-evidence.md；入口只保留短规则 |
| 检查异常残余误入库，以及后续合法记录是否独立保留 | ROUND-7 S4 隐藏检查 | 通用证据参考与两个紧凑场景示例 |
| 区分最终产物、二手转录、原始过程；区分主动执行、主线程补做和自动行为 | Spec-first 两个行为样本缺过程日志 | delegation-and-handoffs.md、writing.md |
| 先校准评分器，再比较；首轮封存、修复和统一复评分开；未知成本不填补、不重复合计 | CH08 首轮均未完成、评分误判与成本限制 | 新增按需读取的 experiments.md |
| 从最终文档执行关键命令，保持初始状态与失败可见性 | CH08 中间稿/最终稿、普通/严格执行的差异 | writing.md |

本次保持 L0 轻量流程；实验细节按需加载，没有新增记录配额、固定实验次数或工具门槛。来源映射见 [source-map.md](evidence/source-map.md)，历史来源字节见 [source-hashes.json](evidence/source-hashes.json)。这些历史观察支持修订方向，不作为新版效果证明。

## 验证结果

- **冻结与范围**：升级前29文件快照与基线哈希保留；最终30文件逐一读回全部一致。实际变更为5份现有文档及1份新增参考。见 [差异](evidence/final-candidate.patch)、[候选哈希](evidence/final-candidate-hashes.json)、[读回](evidence/final-readback.json)。其余24份原文件字节保持不变。
- **格式与静态**：skill-creator quick_validate通过；隔离副本的结构、本地链接与Claude Code定义检查通过；12项仓库校验测试通过。主线程读过原始输出及退出码，三项记录绑定同一产品/Spec内容，运行前后未变化。见 [格式](evidence/checks/skill-format.json)、[结构](evidence/checks/repository-check.json)、[12项测试](evidence/checks/repository-tests.json)。coder初次格式检查缺少yaml，主线程使用本机已有含PyYAML环境完成检查，没有修改全局依赖。
- **有限行为观察**：一个无父会话历史的独立评估包含三个子任务。标题只修正拼写；实验判断没有把未完成的较短耗时称为提速，没有把后续修复回填首轮；导入残余被判失败，未派发的崩溃测试被判未确定。见 [协议与限制](evidence/behavior/protocol.md)、[实际报告](evidence/behavior/reviewer-report.md)。评估者还指出夹具中的跨行CSV本身语法合法，异常定义须由产品契约明确，避免把业务拒绝策略写成通用CSV规则。
- **主线程区分性复核**：亲自比对README全部字节，检查标准CSV完整解析与提供的数据库残余差异，确认空错误集合上的all返回True但派发数为0。见 [原始执行记录](evidence/checks/primary-behavior-check.json)。这不是复跑真实导入器或worker。

本次未修改工具代码，因此没有扩大为整套工具行为回归；未复跑历史A/B/C、真实Claude会话、跨平台矩阵或生产服务。一个显式加载的合成场景评估不能证明自动发现、主动过程执行或普遍速度/质量收益；评估者内部时序未完整采集，报告与主线程原始复核记录分别标注。

## 原目录与记录边界

HEAD读取成功：331db211b2b7e0ca88dd92df2ebb54a89b699b79。完整/限定git status及原目录revision查询超时；限定目录跟踪/未跟踪枚举和文件字节快照可读。原目录record/acceptance门槛未判定，task-state中的结构化验证保持未确定，不能把隔离副本的revision改写成原目录证据。见 [基线](evidence/baseline.json)、[限定查询](evidence/scoped-git.json)、[revision查询转录](evidence/original-revision-check.json)。文档升级和上述限定验证已完成；记录门槛的环境限制不被写成通过。

测试在临时副本运行，临时Git提交仅用于验证基线，没有更改原仓库Git历史。可用 [受测副本归档](evidence/validated-workspace.tar.gz) 复核文件；归档中的旧revision绑定对应当时临时仓库，新解压位置重新执行时应建立自己的真实基线，不能沿用旧token。

复跑范围检查，在含PyYAML的Python环境运行（以下操作只做本地检查）：

```bash
python3 /Users/huaodong/.codex/skills/.system/skill-creator/scripts/quick_validate.py skill/veriflow
PYTHONDONTWRITEBYTECODE=1 python3 tools/validate_repository.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tools/tests -p test_validate_repository.py -v
```

原目录全仓扫描可能继续受同步文件读取影响；本次结构检查通过的是不含历史records的临时副本。最终交付按文件哈希对应，未声称原目录全量扫描成功。
