# ch07 正文交付约束

在代码门槛通过后开始写作；两篇正文分别为 docs/chapters/07.md 与 07-rust.md。正文面向读者，流程记录、返工次数、评审状态不写进书。

共同锚点依语义放在对应节：context-inputs、budget-estimate、atomic-history、managed-run、context-failure、practice-07-1、practice-07-2、practice-07-3。练习编号均 07-1/2/3。

从 ch06 只能限制循环次数但不能使长历史放进模型预算的问题进入。完整解释规则、当前目标、完整审计历史、实际发送上下文四者的位置。展示本章真实配置与调用，不把预置历史演示误说成现场发生的文件读取；说明循环测试确有多轮实际读取覆盖新工具组替换。每条模型调用及全部结果组成不可拆组，必要组是当前目标和最新完整工具组，旧组按顺序裁剪。

主要实验使用 fixtures/cases/ch07-context.json：未管理和已管理共享同一输入及300预算，原644单位，必要239，管理后239，移除g0、保留g1和g4。未管理适配器确实检查收到上下文并报错，管理后从最新工具结果形成回答。解释这是公开确定性离线适配器，未测真实模型能力。estimated-bytes-v1 是自定义UTF-8估算单位，不是JSON线上字节数，更不是服务token；消息结构与数字固定8的规则要可复算，完整公式可以引用实际函数。

至少逐步执行共享案例、源码对照、失败诊断和三项练习：07-1在临时fixtures副本更改最新事实，输出相应变化；07-2将管理案例预算设239成功、238必要上下文超限且零模型请求；07-3删除调用对应结果，校验失败且零模型请求。读者获得完整创建临时副本命令（可用仓库已有Node，无需Python），文件名和CLI位置准确；不要覆盖冻结fixtures。两语言命令分别使用 npm run --silent ch07:context --workspace ts -- /absolute/cases.json 与 cargo run --quiet --manifest-path rust/Cargo.toml --example ch07_context -- /absolute/cases.json。cargo测试/运行设置外部目标目录用于作者验证，不强求读者同样目录。

从仓库根执行，说明先npm ci、Rust工具链前提，链接阅读材料2恢复rein-ch07.tar.gz后使用该章代码。快照链接待真实生成后由封存代理整合，作者不能声称当前已存在或引用Git标签。

失败解释包括 invalid_context_history、context_budget_exhausted、未管理时model_error；非法配置以invalid_context_history停止而errorCode=invalid_context_config，不引入另一种停止原因。规则和目标无法放下时停止而非删除。保留ch05/06停止控制行为。

语言知识就近解释：TS readonly不等于深复制及structuredClone边界；Rust所有权、Vec克隆、Option与Result。给实际源码路径和相关函数，不罗列无解释的完整文件。作者实际运行自己展示的实验、保存argv/cwd/start/end/exit/stdout/stderr及全文hash，最后build文档。一个步骤失败需保留失败原始证据并修复；不要把退出零当作业务成功，读取JSON停止原因/请求数。
