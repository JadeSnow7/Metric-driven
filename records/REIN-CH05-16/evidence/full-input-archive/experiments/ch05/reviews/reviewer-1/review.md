# 第05章独立技术与教程评审（评审者1）

评审对象：`/private/tmp/rein-ch05-review-20260914/reviewer-1/package-17` 与 `package-42`。依据各包 `task-inputs/ch05-product-clarifications.md`、`chapter-05.json`、当前章适用的 `product-spec.md`，以及允许的第一章正文和写作参考。未读取组别映射、作者报告、skill、原执行日志、长期记忆或其他评审结论；未修改产品、测试或提交推送。

**两包的 TS/Rust 核心循环都能实际工作，但两包都尚未满足“完整第05章产品与中文教程”的共同交付标准。** 独立输入验证了真实多文件搜索、依据搜索结果再读取、实际结果回传、同轮顺序与 ID、结构化工具失败、模型错误、空回答和轮数保护。主要缺口在随正文交付的演示、教程可跟做程度、测试覆盖、Rust 工具参数声明与部分错误说明。以下不设总分，也不根据工作流记录格式评分。

证据目录：`/private/tmp/rein-ch05-review-evidence-1`。每个执行的 `*.json` 含原始 argv、cwd、UTC 开始时间、实际环境覆盖、完整输出和 exit code；同名 `*.txt` 为原始输出。终端显示裁剪不影响这些完整文件。`independent-check-summary.json` 为独立探针检查摘要；源码带行号副本、源码 SHA-256 和临时反例脚本也保留在该目录。

## 执行边界与环境问题

- `npm ci` 未重跑（`not_run`）：接收的两包 node 依赖已经独立准备好。实际执行了正文后续 typecheck、离线演示和测试命令。没有把依赖安装状态当作功能通过依据。
- 两包最初缺公共基线文件，导致 `p17-ts-doc-initial.json` 的 ENOENT 和 `p17-rust-doc-initial.json` 的 default-run 缺目标。收到完整封存内容补齐后恢复审查；这两项属于包装问题，不是产品缺陷。
- TS/Rust 的本地 HTTP 测试遇到沙箱 `listen EPERM` / `PermissionDenied`。已对对应 loopback 测试目标安全升级重跑并通过；没有据此认定实现失败。外部模型调用始终为 `not_run`，未读取个人配置、凭据或访问真实模型服务。
- 起初按分配使用同一 reviewer-1 target 串行跑两包，Cargo 曾让 package-42 编译诊断引用 package-17 的旧 API。检查当前源码与诊断不符，清除自己的 crate 缓存后消失；随后按基础设施修订改为 `targets/reviewer-1/package-17` 与 `package-42`，并重新验证。`p42-rust-tests.json` 的参数数量/枚举/Serialize 错误属于旧缓存污染，**不得计入产品缺陷**。
- 本报告不要求第06–16章的完整预算、权限、持久化恢复等能力。事件“可观察轨迹”与“只保存 events 即可恢复原请求”分开判断。

## 逐项规格结论

`passed` 为实际验证符合该行界定；`failed` 为明确不符合；`undetermined` 为现有材料不足；`not_run` 为未执行。核心行为与交付的示例/正文分别判定，避免评审者临时编写的模型探针替产品补齐交付物。

| 规格或行为 | 17 TS | 17 Rust | 42 TS | 42 Rust | 依据与边界 |
|---|---|---|---|---|---|
| tool-search-read：真实搜索并读取多个文件 | passed | passed | passed | passed | AZURE/OCHRE 两个独立目录，各两文件；先搜索，第二轮根据真实文件名生成两次读取 |
| continue-call：下一次模型输入含实际工具结果并产生内容相关回答 | passed | passed | passed | passed | 独立探针记录每次 complete/post 输入；第三轮答案确为各工作区的两份内容 |
| 同轮多调用按声明顺序，每个 ID 对应一个结果 | passed | passed | passed | passed | search → read-0/read-1；下一次输入中的工具 ID 顺序为 search, read-0, read-1 |
| 未知工具作为结构化失败回传 | passed | passed | passed | passed | no_such_tool → unknown_tool，下一轮可回答 |
| 参数错误作为结构化失败回传 | passed | passed | passed | passed | read_file(path:9) → arguments_invalid |
| 文件不存在作为结构化失败回传 | passed | passed | passed | passed | read_file(missing.md) → path_invalid，保留调用 ID |
| 模型返回错误后保留已有事件、无假答案 | passed | passed | passed | passed | 一次真实读文件后抛 Error/返回 Err；model_error/ModelError，answer 缺失 |
| 无工具且非空文本才正常完成；空白回复失败 | passed | passed | passed | passed | normal/空格换行各自验证 |
| 32次基本保护及可解释停止原因 | passed | passed | passed | passed | TS 不传 options 为32；Rust入口明确传32，连续工具调用恰32轮停止。Rust库本身要求调用方显式传上限 |
| events-state：事件可核查顺序、ID、结果和终止状态 | passed | passed | passed | passed | 独立探针 events 与 messages 逐项核对；17以 ok/reason 表示终态，42以 state/reason 表示 |
| 仅保存 events 后恢复原调用输入/每轮完整请求 | failed | failed | failed | failed | 同 ID 读两个同内容不同路径，events 完全相同；参数仍在完整 messages 中。42正文有明确超出能力的承诺，见 F4 |
| 前置消息/ToolResult、OpenAI非流式及Anthropic转换基本兼容 | passed | passed | passed | passed | 阅读并运行共享合同测试；实际OpenAI工具消息 ID与内容序列可用。不是对所有提供商的外部兼容验证 |
| Hello 离线与本地回环既有行为 | passed | passed | passed | passed | TS hello 18项及Rust现有本地服务相关用例通过；真实hello网络服务未调用 |
| 交付的Rust工具声明与TS必需参数语义一致 | passed | failed | passed | failed | 两个Rust示例均只声明 type:object；42循环自身也硬编码该空schema，见 F3 |
| 正文命令直接提供单文件读取演示 | failed | failed | passed | passed | 17仅一条固定搜索→读guide流程，无单独读取模式；42 single实际读取一个文件 |
| 正文命令直接提供多文件搜索→读取→总结演示 | failed | failed | failed | failed | 17仅guide一个文件；42固定只读README，TS还先读后搜；见 F1、F2 |
| 原交付测试覆盖全部明确必测项及两份临时工作区 | failed | failed | failed | failed | 17为4/3个循环测试；42为3/1个；具体缺口见 F5。评审探针通过不替代随产品交付测试 |
| 离线演示无需个人密钥 | passed | passed | passed | passed | 所有REIN_*继承值被移除后运行成功；示例源码未加载env文件 |
| 可直接运行的REIN_*真实冒烟入口，≤4次且无重试 | failed | failed | failed | failed | 只有建议/代码调用片段，没有完成配置、适配器和工作区组装的可运行入口，见 F6 |
| 真实服务冒烟 | not_run | not_run | not_run | not_run | 本次规格明确不调用 |
| 保留00–04、导航及任务外文件 | undetermined | undetermined | undetermined | undetermined | 本评审未获独立的修改前基线diff；不以两包互比推断原文件保持。评审自身未改产品源码 |

| 教程要求 | 17 TS | 17 Rust | 42 TS | 42 Rust | 跟做判断 |
|---|---|---|---|---|---|
| 中文解释为什么循环、ID如何配对、何时终止 | passed | passed | passed | passed | 已亲自读完四篇；这些概念有明确解释 |
| 说明如何接入本章最小前置工程，环境与目录可定位 | failed | failed | failed | failed | 基本运行目录可知，但未给前置文件职责/组装步骤；42 TS开篇还笼统写“前面已经有”，见 F7 |
| 正文所列主要离线命令可运行 | passed | passed | passed | failed | 补齐包装/隔离target后主要命令可用；42 Rust顺读至第4节重复cd rust失败，见 F8 |
| 示例具体输入/预期输出覆盖完整学习主线 | failed | failed | failed | failed | 可复现短演示输出，但没有可跟做的多文件依赖读取与总结；F1/F2 |
| 关键源码与语言知识足以跟着构造循环 | failed | failed | failed | failed | 函数名、事件名和箭头说明较充分，真正构造adapter、ModelTurn、消息追加及失败模型的过程未展开；F7 |
| 失败处理解释与可跟做实验正确 | failed | failed | failed | failed | 17仅要求改示例，未指导实际构造反馈驱动分支；42 TS只列状态和测试，Rust回放耗尽说明实测错误；F5/F7/F8 |
| 两篇章节号和显式锚点对应 | passed | passed | passed | passed | 17的3个显式id集合相同；42的6个集合相同，章节号均05 |
| 练习编号及行为验收对应 | passed | passed | failed | failed | 17均练习05且同missing/path_invalid任务；42均05-1～05-3，但05-2一边纠错重读、一边越界后结束，见F9 |
| 完整中文教程（综合以上实际跟做，不按字数） | failed | failed | failed | failed | 当前更接近运行/接口说明，尚未带读者完成本章规定的两种演示和失败实验 |

## 有位置和复现输入的缺陷

### F1 — package-17：演示未交付规定的两种场景，最终文本不依赖读取内容

位置：`ts/examples/ch05-loop.ts:8–17`，尤其 `:14`；`rust/src/bin/ch05_loop.rs:53–60`、`:72–99`；`docs/chapters/05.md:17–23`、`:48`；`05-rust.md:15–21`、`:39`。

触发/观察：按正文运行，两个实现仅创建一个 guide.md，没有单文件模式或多文件读取。TS第三轮是固定字符串。按练习改变文件内容，在证据目录复制示例、仅将写入文本改为 `# Loop\n工具结果：AZURE apples\n` 并修正临时副本的import定位后，读取事件已经是AZURE，answer仍为旧句“读取完成：工具结果会进入下一轮。”。Rust原样运行的answer为“读取完成：guide.md”，因为 `find(|m| m.role == "tool")` 取的是搜索结果，而非读取结果。

影响：循环库具备能力，但读者运行正文无法完成“单文件读取”和“多文件搜索后读取再总结”两种规定实验；演示中的总结不能展示工具观察如何影响后续决定。证据：`p17-ts-demo.json`、`p17-ts-demo-modified.json`、`p17-demo-ts-modified.mts`、`p17-rust-demo.json`。这不是工具输出写死：真实工具输出确实会变；缺陷是示例路由/最终回答未依赖该结果。

### F2 — package-42：所谓多文件演示固定只读取README，TS实际先读后搜

位置：`ts/examples/ch05-loop.ts:6–14`；`fixtures/cases/prerequisites.json` 的 `anthropic_response`；`rust/examples/ch05_loop.rs:25–30`；TS正文 `:3`、`:19`，Rust正文 `:18`。

触发/观察：直接运行默认命令，TS第一轮顺序为 read_file(README.md) → search_files，第二轮固定“已完成读取与搜索。”；Rust为同轮 search_files → read_file(README.md)，随后固定说明已读取，均没有依搜索结果决定下一次读取。用 `probe-demo-ts.mts` 给原TS入口提供两套真实目录，每套README.md/extra.md均含“前置”；搜索实际返回 `README.md\nextra.md`，extra.md从未读取。把AZURE换为OCHRE，读结果变化，最终文本仍固定。原源码始终只读，不修改产品。

影响：不能从正文获得要求的多文件搜索后读取再总结；两语言主演示也没有同样的操作顺序。循环本身没有乱序——它忠实执行了不同的回放声明。证据：`p42-ts-demo.json`、`p42-ts-demo-two-workspaces.json`、`probe-demo-ts.mts`、`p42-rust-demo.json`。

### F3 — Rust的工具声明未向模型说明必需参数

位置：package-42 `rust/src/rein/mod.rs:648–656`；package-17 `rust/src/bin/ch05_loop.rs:76–85`。对照两包 `ts/src/rein/loop.ts` 的 readonlyToolDefinitions。

触发/观察：读取package-42独立探针实际收到的首个OpenAI请求，search_files/read_file的 `parameters` 都只有 `{"type":"object"}`，没有 needle/path 的 properties 或 required。package-17示例传给LoopAdapter的两个定义同样如此。根据这份声明，空对象属于允许输入；实际dispatcher却要求needle/path字符串（错误参数探针已验证arguments_invalid分支）。TS向模型明确声明必需字段，Rust没有。

影响：Rust真实适配器不能从工具合同了解如何调用；回放硬编码知道正确字段，掩盖了缺口。package-42是循环库自身问题，package-17是交付示例/接入合同问题，不能泛化成其可注入tools的库拒绝正确schema。未据此声称某真实模型一定失败。证据：`p42-rust-independent.json` 的 `cases.AZURE.received[0].tools`、`p17-rust-independent-isolated.json` 对应字段及上述示例源码。

### F4 — events单独不足以恢复原请求，package-42正文却明确承诺可以

位置：package-42 `docs/chapters/05.md:54`，`ts/src/rein/loop.ts:7–11,43–54`；`rust/src/rein/mod.rs:589–609`。package-17同类限制位于TS LoopEvent及Rust `LoopEvent`，正文 `05.md:36` 对“重放”未说明边界。

触发/观察：在同目录创建same-a.txt和same-b.txt，内容都为 `identical`；两次运行分别以同一调用ID `read` 读取两个不同path，之后最终回复 `done`。四个实现的events逐字相同，但完整messages里的工具参数不同。42事件甚至未保留工具名，model_requested只有消息数量。

影响：保存JSON.stringify(events)无法重建原请求或识别读了哪个文件，42正文该句不能成立。完整LoopResult.messages仍有调用参数，足够辅助查看；事件顺序/ID/终态本身通过，不要求第13章持久化恢复。证据：四份独立探针的same-a/same-b或eventReplay字段，及 `independent-check-summary.json`。

### F5 — 交付测试没有覆盖共同说明明确要求的实验

package-17位置：`ts/tests/loop.test.ts:13–64`、`rust/src/rein/mod.rs:759–885`。TS循环测试虽4项通过，但搜索/读取只断言最终result.messages；Rust Replay的 `_messages` 被直接忽略，无法验证循环是否真的把结果传入下一次complete。Rust搜索/读取在同轮，未测试依据搜索结果再调用。两边均无两份不同临时工作区的对照。

package-42位置：`ts/tests/loop.test.ts:14–50`、`rust/tests/loop.rs:10–54`。TS确实检查下一次输入，但搜索和读取在同轮固定产生；Rust只交付一个正常用例，post丢弃请求body，未验证循环后续实际请求，也没有循环级模型错误、空回答和轮数保护测试。两边没有两份不同临时工作区的对照。共享prerequisites测试的手动两轮请求与dispatcher验证不能替代run_agent_loop失败路径与依赖回路测试。

复现：正文/测试命令分别得到17的TS4项、Rust loop_3项；42的TS3项、Rust loop1项。亲自读完这些测试体后作上述判定，并非根据数量推断质量。独立探针补充证明多数行为确实可用，但探针属于评审证据，不属于产品交付。影响：产品回归测试未满足明确规格，也容易遗漏F1/F2/F8。

### F6 — 两包只有“以后这样接”的描述，没有可运行的受限真实冒烟入口

位置：17 `docs/chapters/05.md:42`、`05-rust.md:27`；42 `docs/chapters/05.md:56`、`05-rust.md:49–55`；各包ch05示例与package scripts。

触发/观察：跟正文寻找用REIN_*运行ch05的命令，17要求读者自行包装adapter，42 Rust给出一次函数调用但http/config/workspace/prompt等均由读者另行构造。所交付ch05入口始终是离线回放，且上限为默认/显式32，没有现成的配置组装和≤4次入口。现有hello入口不执行Agent Loop。

影响：无法按交付命令开展后续单独真实冒烟；缺的是入口，不是要求本次联网。本次未加载真实凭据、未调用服务，也未用现有hello的maxRetries设置代替ch05入口验证。

### F7 — 四篇正文尚不能带读者完成规定教程

位置：17 `05.md:13–48`、`05-rust.md:13–39`；42 `05.md:8–72`、`05-rust.md:8–71`。

实际跟做情况：读者能运行一个现成程序并看简短结果，但关键段落只列函数/事件名与箭头；没有逐步展示如何构造一个ModelTurn、如何把多调用工具结果追加成下一轮请求、如何实现观察反馈后的下一次决定。Rust示例实际涉及trait返回Future、Pin/Box、借用/可变状态，正文未在其使用处解释；TS也没有把回放输入与实际历史对照展开。两语言都没有把最小前置工程接线明确列出，也没有完整的失败实验构造步骤。17练习要求改guide.md，但示例每次在未输出路径的临时目录写入并立即删除；想改内容必须自己找到和改源码字符串。42让读者“让示例使用新目录”，入口并无工作区参数或对应操作步骤。

影响：这些是完整教程所需的实践步骤缺失，不是字数、标题或文风偏好。已给予“为何循环/如何ID配对/正常终止的概念解释”通过；未把第一章草稿未完成部分当作允许本章省略的依据。F1/F2提供了正文主线无法复现的具体行为证据。

### F8 — package-42 Rust回放耗尽会panic；顺序跟做还会cd失败

位置：`rust/examples/ch05_loop.rs:18` 的 `remove(0)`；`docs/chapters/05-rust.md:49` 的“耗尽回放则错误进入ModelError”；同正文 `:11` 与 `:44` 的重复 `cd rust`。

触发/观察：按正文所述制造回放耗尽，在证据目录保留原示例副本，仅把responses截成第一条，并把fixture路径定位到原包。第一次工具调用成功后，第二次post从空Vec执行remove(0)，进程exit101，原始输出 `removal index (is 0) should be < len (is 0)`，没有LoopResult、Stopped事件或ModelError。原产品未改动。另在第1节进入rust后按第4节继续 `cd rust`，exit1：`No such file or directory`。

影响：读者照着失败路径提示操作，得到未处理崩溃且丢失输出，而不是教程承诺的结构化结果；命令段落也未保持操作目录连续性。证据：`p42-rust-demo-exhausted.json`、`p42-rust-probe/src/exhausted.rs`、`p42-rust-doc-second-cd.json`。正确返回Err的适配器已独立验证为ModelError，因此定位到交付Replay实现，未要求循环捕获任意Rust panic。

### F9 — package-42练习编号相同但验收语义不同，且搜索输出说明不准确

位置：TS `05.md:64,68`；Rust `05-rust.md:63,67`。

触发/观察：TS05-2要求缺文件path_invalid后再读正确文件，Rust05-2要求越界path_escape后直接最终回答；两者错误类别和成功后续动作不同。TS05-1要求修改README后“搜索output…反映新文本”，实际search_files输出的是命中文件名；在AZURE/OCHRE双目录实验中，文件名集合相同所以搜索输出完全相同，只有读取工具结果随内容改变。

影响：两语言无法用同一练习验收同一行为；读者按文字期待搜索直接给新正文会误判。证据：`p42-ts-demo-two-workspaces.json` 以及两篇原正文。

## 已运行检查及原始证据索引

所有路径均位于 `/private/tmp/rein-ch05-review-evidence-1/`。

| 范围 | 原始证据 | 实际结果 |
|---|---|---|
| 17 TS类型/全部测试 | p17-ts-typecheck.json；p17-ts-tests.json；p17-ts-transport-escalated.json | typecheck通过；全量71/76先通过，5项listen EPERM；对应transport8/8安全复跑通过 |
| 17 TS正文循环测试 | p17-ts-doc-loop-test.json | 4/4通过 |
| 42 TS类型/全部测试 | p42-ts-typecheck.json；p42-ts-tests.json；p42-ts-transport-escalated.json | typecheck通过；全量70/75先通过，5项listen EPERM；对应transport8/8安全复跑通过 |
| 17 Rust格式/库/合同 | p17-rust-fmt.json；p17-rust-lib-isolated.json；p17-rust-prerequisites.json；p17-rust-prerequisite-loopback-escalated.json | fmt通过；库12/12；合同4项沙箱通过及1项loopback复跑通过 |
| 17 Rust正文过滤测试 | p17-rust-doc-loop-tests.json | loop_实际3/3；其余目标0测试没有当作新通过用例 |
| 42 Rust格式/库/循环/合同 | p42-rust-fmt.json；p42-rust-lib-escalated.json；p42-rust-loop-test.json；p42-rust-prerequisites.json；p42-rust-prerequisite-loopback-escalated.json | fmt通过；库9/9；loop1/1；合同4项沙箱通过及1项loopback复跑通过 |
| 17 TS/Rust正常示例 | p17-ts-demo.json；p17-rust-demo.json | 进程成功；功能缺口F1 |
| 42 TS/Rust双模式 | p42-ts-demo.json；p42-ts-demo-single.json；p42-rust-demo.json；p42-rust-demo-single.json | 进程成功；默认模式缺口F2 |
| 17/42 TS独立行为探针 | p17-ts-independent.json；p42-ts-independent.json；probe-ts.mts | 两份工作区、正常/多调用/失败/保护通过；events原请求恢复反例成立 |
| 17/42 Rust独立行为探针 | p17-rust-independent-isolated.json；p42-rust-independent.json；p17-rust-probe/src/main.rs；p42-rust-probe/src/main.rs | 同上；42额外记录真实OpenAI wire请求；17记录LoopAdapter参数 |
| 示例内容变化/回放耗尽/目录连续性 | p17-ts-demo-modified.json；p42-ts-demo-two-workspaces.json；p42-rust-demo-exhausted.json；p42-rust-doc-second-cd.json | 分别对应F1/F2/F8/F9 |

`p17-rust-independent.json` 是评审探针自身首次编译的借用期错误，已仅修正证据目录中的探针并保留v2及隔离target复跑。它不属于产品缺陷。源码哈希文件覆盖本次读取的60/61个产品/规格/参考文件，结束前复核没有变化；它不冒充首轮修改前的产品基线。

最终交付判断：两包均应先补齐第05章演示与教程，再复验。核心循环已有经独立输入支持的能力，不需要凭本评审扩大到后续章节或重写全部前置工程。
