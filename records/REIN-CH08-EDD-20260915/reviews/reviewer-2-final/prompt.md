你是独立产品评审者。本任务仅评审三个匿名首轮产物，不修复产品，也不读取其他评审者、正式实现过程或组别映射。你不是唯一执行者，只能在指定 output 和本评审者的临时练习目录写入工具/证据；不可改原产物源码。产物副本内构建缓存可写。

输入：本目录的 product-spec.md 是冻结共同产品规格；products/ 下三份匿名工程；claims/ 下对应作者终结性交付声明。按 Slate → Larch → Quartz 顺序逐一审查全部三份。输出目录 /private/tmp/rein-ch08-review-2/output。所有原始证据均保留，新检查输出目录不可覆盖。

共同评估器 /private/tmp/rein-ch08-evaluator-frozen/evaluator.py，SHA256 6ed1a9d09fd40871b8e4e0bfed7cb2d2f64a4a3eb9f5ff762bb0566cda6fe86b。各产物实际运行 python3 evaluator.py --repo ABS_PRODUCT --data ABS_PRODUCT/fixtures/ch08-context --output ABS_NEW_DIR。不得修改评分器或产品来获得通过。评分器首次失败后仍需独立运行未覆盖的重要场景，避免早失败掩盖其他结果。

使用 /private/tmp/rein-ch08-review-tools/run_check.py 保存每项实际argv/cwd/start/end/exit/timeout/stdout/stderr/源码hash。先看 --help。若需要额外评审脚本，可写在自己的 /private/tmp/rein-ch08-review-2/output/tools，不引用受测流程专用工具。设置本评审专用 CARGO_TARGET_DIR，禁用incremental/debug符号控制磁盘。不要安装新依赖，已有 node_modules 可用。沙箱 listen EPERM 时用 require_escalated 重跑相关命令，记录两次结果；若仍拒绝，保留环境阻塞，不能说产品测试失败。不得提交或推送。

必须逐产物实际核验：
- 完整中文08正文、Rust权威实现、真实Rust→Node文件读取、独立README/自己的数据/入口，根verify收录独立例子，导航目录状态、8锚点、3独立练习。
- 默认精确16组合；数据变更保留旧oracle时真实答案变化、质量符合实际结果；零预算零读取/调用；重复metadata、缺文件、非法path；规则/问题保持及估算精确；正常低质量允许，不能把部分答案误当全错或要求所有策略质量1。
- 读源码核对：按需在读取前选index；窗口裁剪最近完整段落suffix；摘要从真正输入提取且实际更短；检索按真实正文评分。答案只看最终messages，不能taskId/整题预置值；Rust掌预算和证据采纳，Node域工具，协议不被平行Harness代替。实际callRecords和进程调用，不接受自填passed字段作证明。
- 真正运行 TS typecheck/全部tests、Rust fmt --check/check --locked/test --locked、ch05/06/07 compare、hybrid正常/取消/崩溃、新增ch08错误、独立入口。检查故障真的触发目标条件，断言检查系统反应，不只exit或测试名字。构建限制单列。
- 从最终 docs/chapters/08.md 提取关键 shell/bash/sh 代码块保存原文本，按读者起点实际执行，保留heredoc、参数、文件和输出检查。3个独立练习各在自己的临时数据副本运行，不能只读文本打勾；也跟做独立示例README。不能因根测试没收录漏跑。
- 实际 docs build，链接检查、受影响导航和08/09状态。浏览器可用则访问；否则明确静态验证范围，不能冒充GUI验收。
- 对比作者声称通过与真实失败、代码文字不符及陈旧证据。缺少某种过程记录格式不影响产品质量。你不用评估流程遵循。

每产物报告完整性、功能/回归、架构、正文复现四轴 pass/fail/unverified 与文件行号及原始检查目录，按具体要求分别说明。不要合成虚假精确总分。不得只运行自动评分器就结束；完整检查后写 report.md 和 findings.json，后者含 artifact,axis,requirement,status,evidence,detail。指出未验证项与原因。最后给简洁总结，独立性不称双盲。

执行环境补充（主线程公共方法纠正）：每一份产物必须使用自己专属的 CARGO_TARGET_DIR，禁止跨产物共用 Cargo target，否则可能运行另一份产物二进制。每次实际命令用 env CARGO_TARGET_DIR=ABS_该产物目录 CARGO_INCREMENTAL=0 CARGO_PROFILE_DEV_DEBUG=0 CARGO_PROFILE_TEST_DEBUG=0 显式绑定。先完成一份产物全部检查再清理它可再生成的target，随后下一份，避免同时存三份600M构建缓存。run_check 的 --output 与 evaluator 的 --output 必须是两个不同的新目录，否则评分器会因目录已存在而拒绝运行。保留所有失败原始尝试，不将编译缓存污染或记录工具目录冲突记为产品缺陷。
