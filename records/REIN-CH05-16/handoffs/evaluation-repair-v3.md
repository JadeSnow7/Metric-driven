# 评估准备最终补正

你是有界源码实现coder。你不是唯一工作者，不要还原他人改动。只可修改tools/rein_evaluate.py、tools/tests/test_rein_evaluate.py、tools/tests/test_rein_dataset.py、records/REIN-CH05-16/evidence/specs/chapter-16/**和chapter-16-cases.json。原作者已停止；另一个作者正在work/production实现前置，禁止触碰。可以在evidence/evaluator-v3/写原始证据。不要改skill或原Agent-Learning，不提交或推送。

先读现有源码和本任务范围内的fixture。主线程已经反复发现完成声明与实际文件不符，这次必须实际修改并复跑全部具体反例，不以旧自检通过替代。完成以下三项：

1. 数据事实：expired-command-01的README/oracle要求npm run check，但package.json仍只有rein-check；逐例核对全部12个workspace事实。当前脚本要真实可执行，CLI参数名称要来自argparse或机器schema而非随意常量。所有正例候选必须能从输入workspace源码得出，不能依靠expected推导产品行为。
2. 语义oracle：assertions_hold目前仍只是contains/contains_any。改为解析可见Markdown（HTML注释不能使可见错误通过），命令normalize npm test与npm run test，链接normalize相对路径且检查可见链接确实全部有效，原旧变量用token边界检查。保留正常原意，不能删全文只留命令/flag过线；其余非文稿接口文件必须保持。至少实际证明：合法npm run test与[the guide](./docs/guide.md)通过；仅命令/flag、原坏链接加HTML注释正确链接、原API_URL加注释REIN_BASE_URL均拒绝。不要把能机械检查这些案例说成理解所有中文语义。
3. 评估计数：当前test_count仍max多个harness，tests_run因此错误，虽然test_stats部分sum；按runner一致计算executed/passed/failed/skipped，Cargo多个结果累计且ignored为skipped，unittest的Ran减skip、fail/error不能计passed。全部skip/0tests不得通过。保留timeout bytes解码输出和manual unreviewed=undetermined。针对真实unittest skipped/失败/成功及Cargo多harness文本做回归，计数解析与有效test runner绑定分开解释。

验证：运行所有评估器、数据集及新增反例测试，保存实际stdout/stderr/exit和本次源文件hash到evidence/evaluator-v3/；保留以前证据。最终返回明确的实际修改、原始命令和结果、仍需人工审查的边界。禁止新建额外子代理，当前并发预算已由主线程管理。
