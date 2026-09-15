# 主线程方法核对（评分前保留）

## 固定评分器校准缺口

冻结规格「预算、错误和真实记录」明确工具字段继承 ch07 `estimated_units` 和 J(arguments)；冻结 evaluator.py:16 的 estimate 却只计算普通role/content。因此 CHECK_ESTIMATE 的失败需分开复核「工具字段差额」与「确实超过预算」，不可一概判产品错误。

冻结 evaluator.py:66 仅从 role=user 收集带来源的事实；共同规格要求精确来源前缀，并未禁止真实 role=tool，且混合读取结果使用 tool 是合法路径。因此该限制导致合法 tool claim 假失败。准备期正例只校准了纯文本消息，未覆盖真实工具字段/角色；5项及11预植错误通过不能证明覆盖完整。

原评分器和其原始输出不修改。独立补充检查在自己的版本中仅校正以上不符合冻结规格之处，经含真实工具字段/来源形状的正确和错误样本测试后统一用于三组裁决；不得据此补写首轮成绩或改产品。

## 评审构建缓存污染

第一评审起初跨产物共用 runner Cargo target。Slate stderr 中 `run_one, validate, Index, Row, Task, Tasks` 的 import 和第25行panic不属于Slate实际源码，显示输出来源不可靠。已暂停并恢复同一评审，要求每份产物专属target及完整检查后清理。原始污染结果与因output冲突未运行的尝试保留，均不计产品缺陷。该准备/评审失误与主线程干预计入评审成本，不归咎受测skill。
