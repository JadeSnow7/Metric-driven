# 主线程审查：未接受

审查发生于正式三组启动前。本准备输出正常结束，318.92 秒；原始 usage 保存在 run/run.json，不作为正式组三组的结果。

实际源码发现：
- 默认真实入口会追加 --strategy None，toy 与真实入口不走同一参数路径。
- quality.all-required 把窗口合法漏失、变更真实事实后正确下降的质量判失败。
- budget0正确空messages也会被rules保留检查拒绝。
- 没有在同一评估suite中实际生成/运行budget0、重复metadata、缺文件输入；toy用mutant名称自行返回错误码，被测试当作检测“接受错误metadata”的证据，故障与系统反应不符。
- 只检查行数，不能识别等长替换造成的重复/缺失组合。
- toy用expectedFacts选择来源与字段，不能校准oracle隔离。
- output允许覆盖，记录缺少充分版本排除与timeout bytes处理。

因此3个unittest通过、449条字段检查通过不等于评估器已经有效。正式实验没有开始；改由有明确同一调用路径与动态输入合同的 evaluator-v4 继续，原版、提示和raw输出保留。
