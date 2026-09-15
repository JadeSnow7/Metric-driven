# ch08 材料物化任务（待07快照验收后执行）

此项是共同准备，非任何组实现成绩。唯一coder在新的 `/private/tmp/rein-ch08-common-input` 工作，基于root已验收07快照创建source目录；不要改生产树或07快照。只创建固定资料和输入说明，不实现任何08策略或答案函数。先读ch08-fixed-taskset-plan.md与ch08-common-product.md。

固定目录 fixtures/ch08-context，顺序和事实如下：
1. docs/01-runtime.md 标题“运行配置”，字段“传输方式：stdio”“协议版本：2025-06-18”，关键词运行/传输/协议/文档检索服务。
2. docs/02-cache.md 标题“缓存配置”，字段“缓存目录：.rein/cache”“缓存有效期：600秒”，关键词缓存/目录/有效期。
3. docs/03-approval.md 标题“批准规则”，字段“基线变化后的批准状态：失效”，关键词批准/基线/文件/审查。
4. docs/04-index.md 标题“文档索引”，字段“索引入口：docs/index.md”，关键词索引/导航/入口。
5. docs/05-failure.md 标题“失败处理”，字段“旧批准失效后的处理动作：重新生成补丁并重新审查”，关键词失败/批准/失效/处理/基线。
6. docs/06-release.md 标题“发布操作”，字段“发布前检查命令：npm run verify”，关键词发布/检查/命令。

每篇包含普通背景段落，使其完整UTF-8内容约700–850字节；背景不得嵌入额外上述关键字段/答案或指令。全文超过2400预算，两个相关文档加规则与问题能够放下；精确统计字节、按第07估算器验证共同必要材料可放入2400。避免使用token字样命名实际字节量。为不同策略编造预设得分是禁止的。

index.json保留unit版本、稳定文档id/title/path/keywords/order，不能放完整正文和答案。tasks.json固定rules=[“仅根据提供材料回答；没有依据时明确说明证据不足。”]、budget=2400和4任务：
- runtime：“运行文档检索服务使用什么传输方式和协议版本？” requiredFields传输方式/协议版本，expectedFacts对应stdio/2025-06-18，relevantSources01-runtime。
- release：“发布前应该运行哪条检查命令？” requiredFields发布前检查命令，expectedFacts npm run verify，relevantSources06-release。
- approval：“文件基线变化后，批准状态是什么，接下来如何处理？” requiredFields基线变化后的批准状态/旧批准失效后的处理动作，expectedFacts失效/重新生成补丁并重新审查，relevantSources03-approval/05-failure。
- unknown：“生产环境每秒可以处理多少请求？” expectedFacts空，requiresInsufficientEvidence=true，relevantSources空。

requiredFields/expectedFacts/relevantSources是评估输入，只能交给评估器。策略仅拿question/rules/budget及资料根/index；统一回答器只拿策略构造并实际发送的messages，不能拿task对象、资料根/index或评估字段。这一依赖边界写进README。准备者提供每项必要原材料在2400下可用的实际计算，不按策略执行生成分数。

冻结资料的逐文件SHA256与总manifest，汇报源07manifest、准备真实起止时间和命令输出。主线程核查内容与预算后再prepare两组；不得自行启动模型或对照代理。目录存在时拒绝覆盖，报告现状。

容纳证明按ch08-common-product.md的共同封装：各rule为system，question为user，每个相关文档为user且正文前加`[来源:<document-id>]\n`，保存完整messages而非仅给总字节。四个任务的准备证明只检查有关资料能否容纳，不实现选择策略或回答器。unknown只有规则/问题，验收无来源。所有task固定ID只是报告关联，不许算法按ID选资料或答案。
