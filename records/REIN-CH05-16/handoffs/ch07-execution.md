# ch07 上下文管理实施交接

仅在 ch06 代码、两正文和快照通过后执行。沿 candidate-03 同一演进树增加能力，禁止换基线或提前实现08四策略。按已有剩余产品澄清实施；以下冻结语义，内部接口可按语言习惯设计，但两语言行为一致。

先表示规则、当前目标、完整历史、待发送上下文四个对象。每轮模型实际收到管理后的上下文，完整历史保留供审计；不能仅写一个未被loop调用的裁剪工具。正常未配置上下文管理时维持05/06兼容行为。上下文事件记录裁剪前后估算量、保留与移除的完整历史组、估算单位及停止原因。估算是明确可复算的本地算法，不是服务token。

规则与当前目标始终保留。先计算必要内容；若它们已超过预算，返回明确 context_budget_exhausted 且模型不派发，不以静默删除目标换成功。预算裁剪以完整模型工具回合为单元：assistant声明的全部call及对应tool结果整体保留/整体删除；不得留下孤立tool result、悬空调用或半个多工具回合。最新尚需发送的工具结果组属于当轮必要内容，放不下就明确停止；不能删掉刚读取的依据然后声称回答有依据。输入历史不合法时明确报错并不派发。

示例从仓库根可运行，两语言同一个固定共享案例集；至少包含：不管理时发出超预算长历史而adapter拒绝；管理后在预算内保留规则/当前目标/最新完整工具组并成功回答；必要内容超预算不派发；完整多调用组在裁剪边界不会拆开；原始完整历史仍存在。实际适配器检查收到的消息与预算，答案依据保留消息产生而非scenario ID或预制成功值。输出比较应检验实际发送消息、组配对、估算量、保留/裁剪明细及停止原因，避免只比较reason。

正文两篇完整中文，规则/目标/历史各自用途先以失败实验说明，再边修改边解释实际代码；就近解释TS不可变数组与Rust所有权/借用如何避免误改审计历史。给出源码入口、命令、输入、预期、失败处理和可检验练习07-1到07-3。共享锚点置于相同概念和各自练习附近。不要把未写的00–04或阅读占位页作为前置能力。引用完成后实际保存的rein-ch07快照，不引用Git标签。

两名语言coder可按不相交文件所有权执行，共享fixture/比较脚本/package每个明确唯一写入者。两语言均完成本章针对性测试、完整现有测试与旧05/06比较回归，根审查原始证据和关键动态输入。正文可在代码稳定后单独作者完成；不以文件存在或字数代替教程验收。通过后使用已有chapter snapshot helper以已验收ch06/files为baseline封存，主线程独立解包、应用补丁、核对hash后才准备08配对输入。


## 2026-09-14 冻结的双语言数据约定

新增 ContextConfig：rules 为字符串数组，history 为既有 Message 的完整历史数组，budget 为非负安全整数；当前 goal 仍是 runAgentLoop 的 prompt 参数。启用时 messages 审计历史初始化为 history 的独立副本再追加当前 user goal；rules 是独立配置，发送时生成 system 消息，不能由历史内容覆盖。未配置时维持原初始化和05/06行为。历史只接受 user/assistant/tool；历史中的 system、未知role、非assistant声明calls、非tool声明toolCallId、空/重复call ID、孤立/缺失/重复结果以及不紧邻其声明的结果均 invalid_context_history，模型不派发。一个 assistant 的多call结果允许任意顺序，但必须每个恰好一份且连续组成完整组。toolCallId不可在不同历史组复用。

分组：无call的user或assistant各一组；有call的assistant与随后全部tool结果一组。稳定组 ID 使用完整审计历史中起始消息的零基索引 g0/g1/...。最新的完整工具组和当前goal组永久必需；每轮新形成工具组替换“最新组”，旧组才可以删除。保留的组维持完整历史原顺序。每轮重新从完整审计历史计算，上轮删去并非物理删除。规则不作为可裁剪组。

估算 unit 固定为 estimated-bytes-v1，这是可复算的教学预算，不是 wire 字节数，也不是服务 token。utf8(s) 为字符串原始 UTF-8 字节数。J(null)=4，J(bool)=4或5，J(number)=8（固定估算），J(string)=2+utf8(s)，J(array)=2+元素J之和+max(0,n-1)，J(object)=2+每键(2+utf8(key)+1+J(value))之和+max(0,n-1)。每条消息 M=8+utf8(role)+utf8(content)+可选toolCallId字节数+每个toolCall的(8+utf8(id)+utf8(name)+J(arguments))。一组消息E为各M之和，不含工具schema/HTTP包络；正文必须说明省略项和实际服务用量的区别。JSON 数字必须有限，budget 必须非负安全整数。两语言不依赖对象键序，中文与emoji用UTF-8字节计数。

管理流程：验证全部历史→计算所有组、beforeUnits和必要组→必要组+rules超过budget即 context_budget_exhausted 且不调用adapter→否则从最旧的非必要组起逐组移除，直到 afterUnits<=budget→记录 context_prepared 事件后记录实际 model_requested，并把同一独立快照交给adapter。失败事件 context_rejected 包含 reason；预算失败仍记录 beforeUnits/requiredUnits/budget/unit，非法历史 error 是稳定短码。事件 context_prepared 字段：turn, unit, budget, beforeUnits, afterUnits, requiredUnits, keptGroups, removedGroups, requiredGroups。LoopResult.messages 是不含注入规则的完整审计历史；model_requested.messages 是实际含rules的发送消息。

共享示例 CLI 为 ts/examples/ch07-context.ts [path-to-case.json]，Rust example ch07_context [path-to-case.json]。无路径时读取 fixtures/cases/ch07-context.json，其 schema={unit,cases:[{id,rules,goal,history,budget,managed,expected:{reason,requests}}]}；文件是公开行为样例，可在其副本修改工具结果内容并观察答案变化。两个语言实际离线adapter必须拒绝 E(messages)>budget；在收到完整最新工具组后从该组的 tool content 生成 answer（按声明call顺序以换行拼接），禁止读取expected或按id硬编码成功值。没有可用tool组时也可从当前goal内容回答，这只用于明确基础场景。输出每case为 {id,result,requests,sentMessages}，result使用原loop结果/事件合同；共享比较入口剔除未承诺的人类error文案后比较完整行为、实际发送消息、管理事件、历史保存、动态答案，不只比reason。

TS coder 独占 ts/**、fixtures/cases/ch07-context.json、scripts/ch07-compare.mjs、根package.json；Rust coder 独占 rust/**。根锁文件和导航本阶段无须变化；不要新增依赖。TS coder 先发布fixture，Rust可按上述schema开始实现并等待fixture就位进行最终验证。建议固定样例不少于 unmanaged-overflow / managed-window / required-overflow / multi-tool-boundary / invalid-orphan / invalid-missing / unicode-content。预算根据固定公开数据计算并写进fixture，在两语言验收前冻结。测试需覆盖loop实际接入；不能只单测独立裁剪函数。正文交由后续作者，两代码coder不要写正文。


实现前补充消除歧义：ContextConfig 增加可选 manage:boolean（默认true），仅用于公开的未管理对照。manage=false 仍校验历史、组织规则/goal并记录 context_prepared，但不裁剪也不做预算拒绝，完整上下文实际送给限制预算的adapter，由adapter抛错产生model_error。事件增加 mode:'managed'|'unmanaged'；未管理时 afterUnits=beforeUnits、removedGroups=[]，可能超过budget，这正是要展示的失败。manage=true 遵循上述必需组/预算流程。该开关不代替或预先实现08四策略。

CLI输出最外层固定 {unit:'estimated-bytes-v1',cases:[{id,result,requests,sentMessages}]}；sentMessages为每次真正进入adapter时收到的消息数组（二维）。requiredGroups/keptGroups/removedGroups按完整历史起点升序输出。rules系统消息顺序按原rules数组；当前goal的固定历史索引为输入history.length，即使新回合追加消息也不可误把别的user当成当前goal。上下文以独立clone传给adapter，adapter修改收到的消息不应修改完整审计历史与已记事件。


主线程复核后的最终 rejected JSON 约定：非法历史/配置输出 {type:'context_rejected',turn,reason:'invalid_context_history',unit:'estimated-bytes-v1',mode:'managed'|'unmanaged',errorCode:'invalid_context_history'|'invalid_context_config'}。预算拒绝输出 {type,turn,reason:'context_budget_exhausted',unit,mode,budget,beforeUnits,requiredUnits}，其余不适用字段省略，不填0或null。非法时 LoopResult.error 等于短码，预算时省略。beforeUnits 与 afterUnits 都覆盖注入规则，分别计算裁剪前全部候选消息和实际送出消息；无裁剪时二者相等。
