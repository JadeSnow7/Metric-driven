# ch06 双语言正文交接

只有主线程宣布当前代码门槛通过才可开始；实现不可改。所有权仅 candidate-03/docs/chapters/06.md 与06-rust.md，其他正文/源码/导航/快照均不写。使用冻结skill及 references/writing.md。你并非唯一代理，不回滚他人改动。

读者已跟做ch05，只具备其实际交付的只读工具循环。全文围绕“能继续调用并不意味着应该无限继续”展开，解释模型次数、工具派发数、同义重复、外部取消和整体超时分别控制什么。不给只含命令表和功能清单的短稿；正文要使读者理解并能在自己的临时工作区复现每个机制。两种语言采用各自习惯解释异步、信号和生命周期；不是逐字翻译。

使用代码门槛通过后的实际源码与命令。默认离线入口从书根运行：npm run ch06:offline --workspace ts -- <mode> [absolute-workspace]；cargo run --manifest-path rust/Cargo.toml --example ch06_loop -- <mode> [absolute-workspace]。所有私有验证路径只能留在本任务records，不能写进正文。安装、根目录、Cargo清单、共享输入准备要足以独立跟做；TypeScript npm workspace可能切cwd，输入用由mktemp生成的绝对路径。明确本章阅读时点为携带的rein-ch06.tar.gz，首次恢复可引用阅读02方法但不要假称已建立Git标签。

实验顺序：
1. 默认normal，观察3次模型请求、search和2次真实读取，最终答案引用两份实际文件。创建自己的README.md/guide.md且含marker: ch06，改变内容后再次运行，核对答案变化。
2. budget / tool-zero / zero，逐步区分一个模型回合可以产生多工具、模型预算0与工具预算0，事件中实际执行/跳过有何区别。输出停止是业务控制状态，CLI退出成功不等于任务已完成。
3. duplicate，相同动作不同调用ID仍被拦截；给实际canonical函数片段和嵌套JSON顺序含义，定义duplicateLimit为容许派发次数。
4. cancel-before / cancel / cancel-at-return / cancel-between-tools，逐项说明何时检查、为什么已完成结果仍须记入历史、剩余调用为何仅记skipped而不伪造输出。TS signal穿透到fetch与非合作适配器迟到结果隔离，Rust select丢弃future和Arc<AtomicBool>、可信observer的用途解释准确。绝不声称撤回了服务器已处理的请求。
5. timeout，整体时间预算与请求自身超时的区别；解释本地离线延时只是控制实验，不是模型服务性能。

走读实际核心变更：LoopOptions/defaults、循环派发前/返回后检查、身份计数、raceControl或await_control、ToolObserver/onToolResult、最终stop事件。每段源码说明它解决的具体观测问题，必要类型定义就近解释，不无目的粘贴整文件。

练习06-1、06-2、06-3在两页一一对应，题目给具体可操作修改或模式切换、预期计数和检验方式。若要求改阈值，指出本章快照中真实变量及替换位置，确认maxTurns不会先挡住该实验。若预算提高后示例仍继续发工具，不得写成一定成功结束；按真实行为解释。练习可以直接运行已有反例，但答案不能只写“运行测试看结果”。

共享显式锚点：loop-entry、budget-and-stop、duplicate-action、cancellation、deadline、practice-06-1/2/3，各置于对应概念或练习附近，禁止堆在页首。章节编号保留。正文避免实验分组、skill得分、代理过程、通过项清单等本任务内部记录。

按正文实际执行命令和练习，输出证据放 /private/tmp/rein-ch06-body-evidence（自动记录argv/cwd/时间/exit/stdout/stderr）。用临时复制的本章源码/输入验证需改代码的练习，别改生产源；不运行真实服务。本章源码通过后不再随意扩大测试，作者负责跟做有效性而非重新跑所有旧单测。结束前自查正文与实际输出并运行文档build；不能仅凭字数/锚点检查声称全文验收。完成后停止写入交主线程审阅，再由指定packager封存06并继续07。
