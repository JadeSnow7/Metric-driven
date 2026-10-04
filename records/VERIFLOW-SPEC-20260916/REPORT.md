# Veriflow Spec-first 修复交付报告

仓库内实现与文档已完成，最终版本的静态检查、85 项工具测试、12 项仓库测试和隔离端到端运行通过。已按清单回写原目录并逐文件读回核验。权威目标为 [VF-SPEC-1](SPEC.md)，逐项裁决见 [acceptance.json](acceptance.json)。机械通过不替代主线程语义审查。

## 问题、修改与效果

| 对象 | 已确认问题与最终行为 | 证据 |
|---|---|---|
| 历史证据 | stale 记录不再因当前输入消失或变化阻断历史审计；原件摘要、结果和失效原因保留。当前强制条件仍需新证据，篡改旧原件仍被拒绝 | evidence/primary-fixtures-final、primary-adversarial-final、primary-e2e-final |
| 输入身份 | recorder 与 validator 共用外部 fixture 精确允许清单；规范路径、身份、哈希、复现说明必须完整。未声明输入和路径别名在执行前拒绝 | evidence/primary-fixtures-final；test_evidence_history.py |
| 产品、规范与回执 | schema 1.3 单独绑定 Spec 规范内容、引用契约字节和产品输入；仅修改版本标签不能保住旧证据。声明的运行回执可追加；作为交付物的正文、示例、运行产物即使位于元数据目录也纳入绑定及完成检查 | evidence/primary-adversarial-final、primary-e2e-final；test_spec_binding.py |
| 授权 | 已完成动作保留执行时授权快照和目标版本；撤销约束新动作，不追溯改写历史。缺失历史快照保持未知，阻断后续副作用门槛。重复、范围、结果不明检查保留 | evidence/primary-temporal-final-2、primary-adversarial-final、primary-e2e-final |
| 工作流 | 用户意图先形成 Spec，再进入设计、实现和逐项验收；主线程维护契约，coder 不降低成功条件。委派前确认就绪，报告前核对每项交付物与证据。入口、参考、模板、示例和 Claude Code 定义同步 | evidence/final-review.patch；references/workflow.md、records.md |

采用保守的小模型：产品指纹与任务规范摘要，显式回执分类；不引入细粒度依赖图。已有 OpenAPI、公开类型与协议继续作为对应接口权威来源，任务 Spec 引用它们。L0 用几句目标、约束和验收，无须建文件；L1 可复用摘要；L2 使用稳定条目和内容绑定。设计理由见 [design-decisions.md](design-decisions.md)。

## 实际验证

| 层次 | 结果与边界 | 原始记录 |
|---|---|---|
| 既有基线 | 先执行既有 60 项工具测试与 12 项仓库检查；独立反例揭示原覆盖缺口 | evidence 下 baseline 与 counterexample 记录 |
| 静态与格式 | 仓库检查、Python 编译、skill 格式、git diff --check 均通过 | evidence/final-checks-3/*.json |
| 工具回归 | 85 项通过，包含旧格式兼容、新 Spec、历史证据、外部 fixture、授权快照；12 项仓库适配测试通过 | evidence/final-checks-3/skill-tests.json、repository-tests.json |
| 实际端到端 | 新临时 Git 仓库运行 26 条命令，完成记录、状态重载恢复、验收、Spec 改变后重验、实际本地动作、结果不明核验和撤销后阻止新动作 | evidence/primary-e2e-final |
| 校准反例 | 23 次门槛检查以及 fixture 正负对照通过；最后另以 6 次完整门槛验证历史 commit/push/merge 授权与当前授权分离 | evidence/primary-adversarial-final、primary-fixtures-final、primary-temporal-final-2 |
| 独立行为样本 | 两个新上下文 coder 样本完成，主线程读回产物并复跑；详见下段限制 | evidence/behavior-run |

最终验证记录包含实际 argv、cwd、时间、退出码和 stdout/stderr。final-checks-3 的运行前后输入哈希一致。端到端仅操作隔离本地资源；授权链中的 push、merge 与远程 CI 回执明确为模拟状态，只有临时仓库的 Git commit 实际执行，未访问生产服务。

检查过程中失败没有删除：外部路径误分类、回执路径被错误要求产品审查、历史前序动作仍依赖当前授权等反例和中间失败保留；最终版本均有对应复验。子任务的一份早期失败日志被覆盖后，主线程依据此前工具读回内容另存为带来源说明的转录，不将其冒充原始进程日志；最终结论使用主线程实际运行记录。证据目录说明区分了草稿、转录与最终结果。

## 行为观察及未验证项

冻结 skill 后使用 gpt-5.6-luna / medium 的 coder，两个样本各运行一次，输入只提供用户请求、必要材料与工作边界，不提供评分答案；停止条件为一次最终回复或 12 分钟。冻结清单、归档、输入、环境与产物已保存。

轻量样本只修复 README 标题，正文保持不变且没有建立额外记录文件。教程样本交付 README、程序、示例输入和运行结果；主线程实跑正常输入、空文件、缺参、缺失文件均符合请求。执行者报告进行了验收，但没有独立保存执行者原始过程日志；Spec 形成时机、维护过程与执行者主动验收过程仍属未验证，不能由最终产物倒推。两个样本没有显示遗漏交付物，但不足以证明普遍避免提前结束或扩大结论。

行为冻结发生在最后的历史授权链补修之前。该补修已通过最终工具回归与实际门槛反例，未重跑行为样本；不将样本结果扩展至该代码改动。没有对照组、速度/成本统计或普遍质量结论。[后续实验建议](follow-up-experiment.md) 列出 27 次 A/B/C 运行的上限预算，尚未启动。

本轮工具实跑环境为 macOS / Python 3.11.15。未运行 Linux、其他 Python 版本矩阵、真实 Claude Code 会话或生产服务；Claude Code 仅完成定义与仓库适配静态校验。授权快照是可审计内容摘要，不是用户密码学签名；主线程仍须核实授权来源。

## 兼容、现场与动作状态

schema 1.1/1.2 继续走既有兼容路径，并明确旧格式没有新 Spec 内容绑定；1.2 不降格为 1.1。迁移至 1.3 需补齐真实任务契约并实际重新验证，不能刷新旧记录外层字段冒充重跑，不能自动补造历史授权。具体字段与命令见 skill/veriflow/references/records.md。

原始工作区 HEAD 为 fd7f0a618720e7682621207d4df28411327004ef。基线采用现场逐文件快照，不以历史提交替代当前字节。SPEC.md 初始调查写“42 项”，实际清单为 43 项；此处纠正统计笔误，保留已冻结的 Spec 字节。全目录 Git status 超时，限定路径查询成功；tools 两处已有改动保留。预检仅发现 tools/.DS_Store 后续变化，不纳入本轮回写。

本轮没有更新已安装 skill，没有在原工作区提交、推送、合并或发布。历史封存实验与只读 Web Studio 文件未修改。

## 交付回执

第一轮按源版本、原目录 HEAD、允许路径、源哈希和目标基线完成 278 个文件回写，逐文件读回哈希全部一致；其中 27 个为入口、skill、工具、测试及同步文档，其余为本轮新增记录。原 tools 两处已有修改逐文件核对保持原字节，原目录 HEAD 未变化。实际清单、调用回执和读回结果见 evidence/integration-manifest-1.json、integration-execution-1.json、integration-readback-1.json。报告与验收回执随后按第一轮已写入哈希再次增量同步，见 evidence/integration-final-receipt.json。

Spec 满足情况：SC-01 至 SC-07、SC-09 满足本轮实现与验证范围；SC-08 已完成有限行为观察，过程观察不足仍单独列为未验证。记录完整性：最终原始结果、输入哈希、失败与限制保留。交付动作状态：仓库内文件已更新，安装、原仓库提交、推送、合并、部署均未执行。

回写后原目录的限定路径 git diff --check 通过；全仓库 tools/validate_repository.py 在 30 秒后超时，未判定通过或失败（该目录此前也发生全目录读取阻塞）。对应检查在隔离副本已通过，回写字节经哈希确认一致；原目录全仓库扫描仍为未完成项。原始观察见 evidence/target-verification.json。
