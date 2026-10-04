# 受测 skill 改进候选（未修改本批受测版本）

此文件是生产与评审观察，不是已经验证有效的 skill 修改。本轮冻结资源保持不变。后续若修改，必须另起批次，不能将改后版本混入当前四对实验。

## ch05 首轮后的观察

- 两组可复用核心循环都通过了独立行为检查，但两组正文与交付演示均有明确缺陷；没有证据据此宣称 skill 节省成本或改善整章结果。正式裁决见 `experiments/ch05/adjudication.md`。
- treatment 可观察命令记录读取了 SKILL.md，没有观察到其 reading/writing 引用中的 writing 文档读取。只能表述为日志观察，不能证明代理不可见的所有上下文内容。候选：入口如何将正文交付要求可靠地路由到写作指导，需另行测试。
- “通过测试”与“覆盖了正文全部主张”被混淆。首轮与生产 v1 的测试确实有通过输出，但实际测试体未验证全部声明行为。候选：每项可观察主张与当前版本具体证据的对应检查，而不是以总通过数作完整性替代。
- 正文的命令、工作目录、输出枚举与模型请求轮次出现直接不一致。候选：跟做验收应按正文命令顺序和初始状态执行，并核对预期输出；不能仅构建站点或运行入口一次。
- 生产修复 v1 用动态离线适配器消除了正常演示中的耗尽路径，却保留了过时的耗尽教程和不安全测试回放器。候选：修复必须检查旧解释/旧测试假设是否仍成立，不能只验证新正常路径。
- 工具制作也发生“功能清单存在，但实际合同未落实”的情况，例如多行角色解析、真实 final 保存和补丁恢复。它属于准备/生产工具成本，不算 ch05 两组产品分；候选：使用能区分错误实现的校准样例。

## 推断边界

这里只能作本项目当前配对条件下的探索性观察。共同规划本身已包含明确产品要求，比较的是执行阶段额外加载 skill 的增量。准备、评审、生产返工成本单列；没有样本量或随机化支持总体因果结论。没有对缺少 EDD 专用记录格式的 control 产品扣分。

## ch06 生产返工观察（不属于正式配对）

- 只比较停止原因的跨语言检查曾放过不同模型轮次/工具参数；升级为结构化结果后又因fixture缺字段与对象键顺序直接失败。候选：评估器不仅需要已知错误样例，也应先用正确的完整共享合同校准。此项仅说明这次工具实现/审查经历，不证明skill相对另一组的效果。
- “同步抛错清理”与“同步取消后抛错”不是同一测试路径。主线程后者探针实际返回cancelled后仍因未处理Promise拒绝导致Node exit1；原始证据在 /private/tmp/rein-ch06-main-review-v3/sync-abort-throw.json。候选：按取消/异常组合的实际状态转换选小量有区分力的回归，避免凭单项测试名称推定组合也通过。


## Production ch07 and support tutorial observations

- Multi-message history validation skipped tool result fields when advancing the iteration index; fixes initially covered only the reported role. Require a complete shape check for every consumed message and cross-language behavior probes. This is production rework evidence, not a controlled paired skill effect.
- Rust `cargo test loop` filtered by test name and ran one wire test; `cargo test --test loop` is the intended complete integration target. Inspect test count and identities rather than exit alone.
- A2 author tested a separately handwritten DemoState example while final prose retained LoopState names. Tutorial extraction must use exact final Markdown code and retain positive and negative compiler outcomes.
