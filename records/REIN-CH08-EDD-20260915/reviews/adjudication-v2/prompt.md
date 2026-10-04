实现一个非常窄的裁决辅助工具。仅写当前目录 supplemental_check.py、tests/test_supplemental.py、README.md，不修改其他文件。你不是唯一写入者，保留其他目录工作。不要读取任何正式三组产物或其他评审。

这是对冻结评分器的只读适配，绝不替换原评分结果。固定源 /private/tmp/rein-ch08-evaluator-frozen/evaluator.py，SHA256 6ed1a9d09fd40871b8e4e0bfed7cb2d2f64a4a3eb9f5ff762bb0566cda6fe86b。必须先校验此hash，再importlib导入这个真实模块，并复用其 check_row/STRATEGIES，不能另写缩水验证器。共同规格 /private/tmp/rein-ch08-common-20260915/product-spec.md；ch07估算权威实现 /private/tmp/rein-ch08-common-20260915/book/rust/src/rein/loop.rs 中 estimated_json/estimated_message。

仅纠正两处：
1 frozen.estimate 替换为ch07精确估算，包括tool_call_id(可能null，视为0)，tool_calls默认空，J(arguments)按Rust实现。普通role/content仍8+UTF8。参数数字8，true4/false5，nested数组对象和中文。
2 调用 frozen.check_row 前 deepcopy(row)，对 content 以 [来源: 开头的 role=tool 消息改副本role=user（这两个role UTF8长度都是4）；其余字段不改。这使冻结检查支持合法tool来源，同时保留其实际文件源绑定、quality精确、未知题、必需字段、预算上限、规则等所有检查。不能仅做字符串包含而跳过其他检查。

CLI --run 路径 --data 当前资料 --budget 2400或0。--run是实际执行记录JSON，必须exit_code0且timed_out非true，解析其stdout根对象，unit/serviceTokens符合，tasks/index读取--data（必须实际使用），严格核对行数与(taskId,strategy)集合等于当前四任务×四策略。逐行用以上适配后的 frozen.check_row(row,tasks,index,{'budget':budget},data)；失败捕获具体AssertionError check_id，保存/打印JSON含原run hash、当前data文件hash、冻结评分器hash、失败检查ID，wrapper非0。不要覆盖run/fixture，只输出stdout结果。校验前后原始run hash相同。

实际测试必须有真正完整的4任务×4策略正例，所有冻结check_row必需字段/规则/真实data源/oracle均有效，不能拿简化残缺行当正例。测试独立断言具体check_id，不能只assert nonzero。至少：普通消息正例；合法tool调用+tool结果正例且估算包含null和非null字段；手算常量验证J的中文/嵌套/数字；错误估算CHECK_ESTIMATE；无依据claim CHECK_CLAIM_GROUNDED（估算必须同步正确避免错因）；修改真实源为新值、messages和claim也新值但保留旧oracle且quality仍1，要命中CHECK_QUALITY_EXACT；把此quality改成实际正确值应通过；只改源但旧messages/claim不变命中CHECK_CLAIM_CURRENT_SOURCE；budget0 answer=null正例无崩溃；执行失败明确拒绝。先自己算好正例再植错误，每个错误只改要测的性质。不要读取或修改原冻结calibration代码，不安装依赖。

运行所有tests并保存原始stdout/stderr与退出码，最后报告实际检查数量、hash、限制；不夸大测试覆盖。不要提交推送。
