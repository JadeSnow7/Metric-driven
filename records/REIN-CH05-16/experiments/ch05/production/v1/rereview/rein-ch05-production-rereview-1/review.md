# 第05章生产复核（评审者1）

**本轮结论：仍不放行完整章节交付。** 动态多文件演示、工具schema、完整事件输入和受限真实入口的代码接线已修复；但测试覆盖声明、Rust回放耗尽说明、正文可跟做性与练习验收仍有明确未修复项。下表逐项对应首轮F1–F9，不涉及第06–16章。

产品：`/private/tmp/rein-production-20260914`。只读产品；临时探针、反例及原始记录均在 `/private/tmp/rein-ch05-production-rereview-1`。已完整阅读两篇中文正文，先读作者实际stdout/stderr与测试源码，再仅运行关键探针、示例及本地HTTP。没有重跑全仓测试；作者的“通过”与本评审亲自验证分开记录。未读取个人配置或凭据、未调用真实模型服务。

## F1–F9复核

| 首轮问题 | TS | Rust | 本次判断与证据 |
|---|---|---|---|
| F1 单文件/多文件演示与内容相关答案 | passed | passed | 现有single与默认模式均有实现。TS两模式亲跑；Rust默认亲跑、single读作者`rust-single-final.stdout`并核对相应源码。两边默认按搜索结果生成读取，答案来自工具结果 |
| F2 动态搜索→读取与两套工作区 | passed | passed | 原独立探针适配生产API，AZURE/OCHRE两目录、每目录两文件，模型第三次实际输入及内容相关答案通过。另直接让生产TS示例在两套目录运行，答案分别为AZURE/OCHRE实际内容；原固定README/先读后搜问题消失 |
| F3 Rust工具必需参数schema | passed | passed | Rust首个真实wire请求有path/needle properties、required与additionalProperties:false，和TS语义一致 |
| F4 完整事件输入 | passed | passed | 事件保留messages/tools、完整模型消息、call参数。相同ID读取同内容不同路径的旧碰撞反例已不成立，两次events能区分path |
| F5 交付测试完整覆盖 | failed | failed | TS5个、Rust2个循环测试的实际源码仍未覆盖正文/规格所列项目；见问题1。独立探针通过不替产品交付测试补数 |
| F6 REIN_*、显式live、≤4轮且无重试入口 | passed | passed | 用生产入口直接访问本地127.0.0.1：读文件后2次请求完成；连续调用4次停止；503只请求1次。见`live-loopback-results.json`。正文仍缺可复制的live运行命令，归入F7 |
| F7 完整可跟做中文教程 | failed | failed | 前置工程说明与两种演示已有改善；但TS顺读命令实际失败，两篇仍缺关键构造步骤和具体失败实验，且有与代码不符的承诺，见问题2–4 |
| F8 Rust耗尽与目录连续性 | failed | failed | 原Rust重复cd问题修好；TS新增目录连续性错误。Rust普通示例移除了Vec响应队列，因此原正常示例的remove(0)风险已消除，但它根本没有正文所述replay_exhausted分支；测试Replay仍可耗尽panic。见问题3 |
| F9 同号练习与验收 | failed | failed | 05-2两边现在都是missing后重读，已对齐；05-1 TS仍写错收到读取结果的轮次，05-3 Rust写错实际JSON停止原因，见问题4。章节号、5个显式锚点集合及练习编号本身相同 |

上述`failed`不表示整项毫无改善；具体已经修好的部分已在表内注明。没有`undetermined`阻塞项。真实外部模型调用为`not_run`，安装/全量测试不重复执行。

## 仍需修复的明确问题

### 1. 测试源码不支持正文的完整覆盖声明（F5）

位置：`ts/tests/loop.test.ts` 全部5个用例；`rust/tests/loop.rs` 全部2个用例；`docs/chapters/05.md:39`、`docs/chapters/05-rust.md:37`。

TS新增两工作区和抛错耗尽模拟是实际改善，但仍没有循环级错误参数、缺失文件反馈后重新读取成功、默认32次上限测试。已有unknown用例只让模型一直返回unknown直至显式maxTurns:2，没有验证失败消息驱动恢复。现有双工作区用例检查第三次输入是实际内容，这部分通过。

Rust仍只有固定同轮search/read正常用例和第一次请求立即Err用例；测试Replay忽略收到的body。没有两工作区、搜索结果驱动下一次读取、循环工具失败反馈、空回答、32次保护或实际回放耗尽的断言。新测试名`model_errors_and_replay_boundaries_are_structured`不包含耗尽操作。已有prerequisites合同测试不能替代这些循环测试。

复现依据：先读作者`ts-tests-elevated.stdout`（77/77）、`rust-tests-elevated.stdout`（库9、loop2、合同5）及`rust-loop-final-2.stdout`（2/2），再亲读测试体。作者原始通过结果为真，正文声称覆盖的范围仍不成立；这不是从测试数量或名称推断。

### 2. TS正文的失败测试命令在它自己的当前目录执行会失败（F7/F8）

位置：`docs/chapters/05.md:20`进入`ts`，后续`:36`执行`npm run test --workspace ts -- loop.test.ts`。

复现：从根目录按正文进入ts并运行两种示例后，执行上述原命令，cwd为`/private/tmp/rein-production-20260914/ts`。实际exit1，`npm error No workspaces found: --workspace=ts`。见`ts-doc-test.json`。这不是沙箱问题，读者尚未到测试就被命令位置阻断。

此外，两篇正文仍只有概念说明和现成入口运行，没有逐步构造ModelTurn/适配器、追加工具消息的关键代码与输入输出对照；失败实验让读者自行“改path”“移除响应”，没有提供与当前代码匹配的完整修改位置/可执行操作。Rust虽增加了Vec、Result、serde解释，但不足以让读者照着构造并理解本章完整循环。两文的live段落也没有写出已有可运行入口的命令与位置（TS实际为`npm run ch05:live -- --live <workspace> <prompt>`；Rust为example的`--live`）。这些判断来自实际跟做，不按字数判定。

### 3. Rust回放耗尽说明仍与产品不符，保留的测试Replay仍会panic（F8）

位置：`docs/chapters/05-rust.md:23`称回放耗尽返回`replay_exhausted`；`:37`让读者“将示例的第二轮响应移除”后得到`model_error`。`rust/examples/ch05_loop.rs:11–68`的Replay现在按计数和请求内容动态构造响应，没有响应Vec、没有可删除的第二项，也没有replay_exhausted返回分支。

保留的`rust/tests/loop.rs:16`仍执行`self.0.lock().unwrap().remove(0)`。我将这个Replay定义原样复制到临时反例，只给它一条search响应并让生产`run_agent_loop`运行2轮：第一次搜索真实完成，第二次取空队列，exit101，`removal index (is 0) should be < len (is 0)`，无结构化LoopResult。见`rust-replay-exhaustion.json`及`rust-probe/src/exhausted.rs`。

边界：没有声称当前正常示例仍会按原路径panic；该路径已通过改为动态模型消除。未修复的是“可复现的耗尽实验/结构化耗尽合同”，以及仍然不安全的交付测试回放器。普通适配器返回Err时循环会ModelError，独立探针已确认，不要求循环捕获任意Rust panic。

### 4. 练习验收仍有可直接核对的错误（F9）

TS `docs/chapters/05.md:49`写“第二次模型输入含两条对应的tool消息”。实际时序是：第一次请求→search；第二次请求只有1条搜索tool消息；第二轮执行两个read；**第三次**请求才有两条读取tool消息（另有前面的搜索结果）。生产默认事件和两工作区运行都清楚呈现这一点。证据：`ts-doc-demo.json`、`ts-demo-two-workspaces.json`中turn2/turn3的model_requested.messages。

Rust `docs/chapters/05-rust.md:51`写停止原因为`max_turns`、`empty_final`，但当前Serde输出为`MaxTurns`、`EmptyFinal`。独立Rust探针和本地HTTP4次上限实测如此。两边行为本身能停止，错误是精确输出验收未与当前语言合同一致。

两篇都让读者在默认工作区“新增两份”文档，但默认已有README/notes两份marker文件，示例均只取排序后的前两条命中。若新增文件排在后面，它们不会进入答案；正文至少要明确使用新的两文件目录、替换现有两份，或说明选择规则。此项为源码与练习起始状态直接推导，未再扩展运行新用例。

## 本次实际复跑证据

目录均为 `/private/tmp/rein-ch05-production-rereview-1/`。每个命令记录JSON保留argv、cwd、完整输出、exit与实际target；同名txt保留原始输出。Rust独立target为`/private/tmp/rein-production-rereview-build`，未与其他包共用旧crate缓存。

- `ts-independent.json` / `probe-ts.mts`：两工作区、真实结果回传、多调用顺序、三类工具失败、模型错误、空白最终、默认32轮、事件输入碰撞反例，全部通过。
- `rust-independent.json` / `rust-probe/src/main.rs`：两工作区、三轮真实搜索读取、同轮多读取、错误/空白/32轮、完整事件及schema，实际输出核对通过。
- `ts-doc-demo.json`、`ts-doc-single.json`、`rust-doc-demo.json`：按正文当前命令实际执行成功。Rustsingle本轮使用作者原始`rust-single-final.stdout`与当前源码交叉核对，未重复执行。
- `ts-demo-two-workspaces.json` / `demo-two-workspaces.mts`：直接运行生产TS示例，目录内容AZURE/OCHRE变化后答案也真实变化，读取结果位于第三次模型输入。
- `live-loopback-results.json`：生产TS/Rust入口各3场景；每场景均保留子进程argv/cwd/stdout/stderr/exit及服务端捕获请求body。success恰2次且实际内容回传；limit恰4次；503恰1次，无重试。JSON结果的failed与CLI exit0分开记录，不用exit0宣告运行成功。
- `live-sandbox.json`：初次本地监听PermissionError；`live-elevated.json`：限定127.0.0.1安全复跑通过。没有剩余环境阻塞。
- `ts-doc-test.json`：原正文当前目录测试命令失败。
- `rust-replay-exhaustion.json`：原交付测试Replay定义的耗尽反例exit101。

生产源码保持只读。本轮必要编译仅为独立Rust探针和实际入口，未再次全量编译/测试其他模块。没有把作者77/77或16个Rust通过用例当作整章验收，也没有把临时探针当作已交付的产品测试。
