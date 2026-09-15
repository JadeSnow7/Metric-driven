# 第 05 章独立技术与教程评审（二）

评审对象为 `/private/tmp/rein-ch05-review-20260914/reviewer-2/package-17` 与 `package-42`。未识别或猜测组别。只使用两包公共 task-inputs、相关源码/测试/fixtures/正文及第一章写作参考；没有查看作者报告、工作流记录、其他评审或长期记忆。产品文件未修改，没有补实现、删测试、提交或推送。

两包的核心循环均能实际搜索、读取、回传并继续模型调用；独立探针在每种语言的两套临时工作区上验证了这一点。但两包均未完整满足本章的演示、事件重放、随包测试和完整教程要求。package-42 另有 Rust 示例回放耗尽时直接 panic 的可复现错误。以下结论限定第 05 章，不要求后续章节的完整预算、取消、权限或持久化恢复。

## 判定与证据边界

`passed` 表示本次实际行为/人工阅读足以支持该项；`failed` 表示有具体不符合；`undetermined` 表示证据不足或环境仍阻塞；`not_run` 表示没有运行。独立探针通过不等于产品已交付相应教程或自测。

最初缺根配置和公共源码是包装环境问题，补齐后才开始下列正式运行，不计产品缺陷。Rust 最终结果只采用 `targets/reviewer-2/package-17` 与 `targets/reviewer-2/package-42` 各自独立 target 的日志；旧共享 target 日志保留但不用于最终结论。两包串行完成 Rust 验证。

每条正式命令的 cwd、argv、运行前相关 source SHA-256、退出码和原始输出分别保存在 `*.meta.json`、`*.stdout.txt`、`*.stderr.txt`。`command-index.json` 是命令索引。`independent-summary.json` 给出探针结果和最终文件不变检查。正式开始与结束比较了 package-17 的 78 个、package-42 的 79 个相关文件，变化均为 0。

离线命令移除了继承环境中的 `REIN_*`；没有读取个人配置或凭据，也没有请求真实服务。`npm ci` 为 `not_run`：评审副本已经准备好独立依赖，为保持提供的产品副本而未重复安装。类型检查、正文运行命令和测试均亲自执行。Rust 命令的 target 路径按评审隔离要求替换，其他行为参数与正文一致。

## 每种语言逐项判定

| 当前章规格/可观察行为 | 17 TS | 17 Rust | 42 TS | 42 Rust |
|---|---|---|---|---|
| 循环实际调用适配器，真实访问指定工作区 | passed | passed | passed | passed |
| 搜索结果驱动下一轮读取多个文件，再据读取结果回答（独立探针） | passed | passed | passed | passed |
| 同轮多调用按声明顺序执行，结果 ID 一一对应并进入后续请求 | passed | passed | passed | passed |
| 未知工具、参数类型错误、文件缺失/目录读取失败为结构化反馈 | passed | passed | passed | passed |
| 适配器按接口返回 Error/Err 后保存已有事件、无假答案 | passed | passed | passed | passed |
| 无工具且非空文本才正常完成；空白回复明确失败 | passed | passed | passed | passed |
| 32 次基本保护及明确停止原因 | passed | passed* | passed | passed* |
| 可显式限制为 4 次且循环不自动重试 | passed | passed | passed | passed |
| 终止状态与工具顺序可核查 | passed | passed | passed | passed |
| 事件记录足以重建实际调用/请求 | failed | failed | failed | failed |
| 既有 hello 与前置消息/工具合同兼容（离线测试范围） | passed | passed | passed | passed |
| 模型收到的工具参数声明与实际所需字段一致 | passed | failed** | passed | failed |
| 正文命令能运行单文件读取 | passed*** | passed*** | passed | passed |
| 提供多文件搜索后读取再总结的直接演示 | failed | failed | failed | failed |
| 随包循环测试检查下一轮实际模型输入含工具结果 | failed | failed | passed | failed |
| 随包测试覆盖两套不同临时工作区内容 | failed | failed | failed | failed |
| 随包循环测试覆盖全部指定正常/失败类别 | failed**** | failed**** | failed**** | failed |
| 离线运行不需要个人密钥或真实服务 | passed | passed | passed | passed |
| 提供复用 REIN_*、读者可直接使用的完整真实冒烟入口 | failed | failed | failed | failed |
| 真实服务冒烟 | not_run | not_run | not_run | not_run |

\* Rust 的两个演示显式传入 32；独立探针也确认传入 32/4 时恰好调用 32/4 次。Rust 公共函数要求必传轮数，没有另一个无参数默认配置 API；这里仅判定交付入口的基本保护，不声称存在未实现的默认配置 API。

\** package-17 Rust 的 `run_agent_loop` 允许调用方传工具定义；失败指交付示例中的定义，不指它拒绝正确的外部定义。

\*** package-17 的唯一演示在读取一个文件前额外搜索一次，确实能演示单文件读取；它没有另一个多文件演示。

\**** package-17 TS/Rust 有正常最终回复、真实文件、多调用、未知工具、模型失败、空回复和显式短上限的检查，但没有完整的“先搜索结果驱动下一次读取 + 下一次模型输入断言 + 两套工作区”测试链。package-42 TS 同轮同时请求搜索与读取，没有测试搜索结果再驱动读取，亦无两套工作区。此行判定整套要求未齐，不否定已有分项覆盖。

公共四项验收：`tool-search-read`、`continue-call`、`failure-stop` 在四个核心循环的独立探针上均为 `passed`；`events-state` 为 `failed`，因为顺序和终止虽可看见，事件缺少重建实际动作所需的信息。package-42 Rust 的交付演示另有回放异常失控问题（42-1）。

## 两篇正文跟做与人工阅读判定

已亲自通读四篇正文及第一章手工稿/风格提炼。没有用字数、关键词、文件存在或测试数量代替质量判断。

| 教程要求 | 17 TS | 17 Rust | 42 TS | 42 Rust |
|---|---|---|---|---|
| 解释为何要循环、调用与结果如何配对、何时结束 | passed | passed | passed | passed |
| 开篇明确说明最小前置工程如何接入及尚非前四章完整交付 | failed | failed | failed | failed |
| 环境/目录准备足以让目标读者自行开始 | failed | failed | failed | failed |
| 主演示命令可运行（已准备依赖，loopback 条件见下） | passed | passed | passed | passed |
| 正文声称的演示行为与实际输出一致 | passed | passed | failed | failed |
| 关键实现可由正文跟做并理解相应语言知识 | failed | failed | failed | failed |
| 失败说明准确，能按文中方式复现 | passed***** | passed***** | passed***** | failed |
| 共享章节号与显式锚点 | passed | passed | passed | passed |
| 同编号练习有任务和可观察验收 | passed | passed | passed | passed |
| TS/Rust 同编号练习的行为验收一致 | passed | passed | failed | failed |
| 完整中文教程总体交付 | failed | failed | failed | failed |

\***** 指文中给出的错误分类符合实现、独立探针已复现；不表示正文已经提供完整可复制的错误示例代码。package-42 Rust 除回放耗尽说明错误，第 4 节再次 `cd rust` 也会打断顺序跟做。

人工依据：package-17 两文主要由运行命令、接口名和状态列表组成；package-42 增加了编号步骤和消息流，但仍直接从导入的前置对象与运行现成示例开始。四篇均未给出环境版本/安装或明确前置接入步骤，也没有带读者构造模型回放、工具声明、循环调用和失败场景的关键源码片段。Rust 的 `LoopAdapter`/`OpenAiHttp`、异步返回类型及可变状态如何接起来没有在使用处解释。读者能运行现成程序，但仅按正文无法完成所要求的构建和实验路线。第一章参考中的场景—操作—解释方式只部分实现，不将其未完稿或排版错误作为目标。

## package-17 具体问题

### 17-1：随包演示未交付多文件流程，Rust 的“总结”只取搜索文件名

位置：`ts/examples/ch05-loop.ts:8–16`；`rust/src/bin/ch05_loop.rs:20–64`、`:72–99`；正文 `docs/chapters/05.md:23`、`05-rust.md:21`。

触发：分别执行正文的 `npm run ch05:offline --workspace ts` 与 `cargo run --locked --offline --bin ch05_loop`。两个示例都只生成 `guide.md`，读取路径预先写死；没有第二个文件或多文件入口。Rust 最后一轮使用 `messages.iter().find(|m| m.role == "tool")`，取到的是搜索结果。

观察：Rust 实际答案为 `读取完成：guide.md`，不是读取出的正文。TS 的最终答复固定为 `读取完成：工具结果会进入下一轮。`，没有读取后续请求中的实际结果。工具确实访问了文件，问题是交付的演示没有展示由搜索命中选择多个读取对象、再根据读取结果总结。

影响：无法按正文直接复现共同规格要求的多文件流程；Rust 还会把“拿到搜索文件名”教成“使用读取内容”。独立探针证明核心循环支持该流程，但探针不是随包演示。

复现证据：`p17-ts-demo.stdout.txt`、`p17-rust-isolated-demo.stdout.txt`；对应 `.meta.json` 保存完整命令与 cwd。

### 17-2：仅保存 events 不能重建实际调用

位置：`ts/src/rein/loop.ts:4–8`、`:43–56`；`rust/src/rein/mod.rs:584–604`、`:657–707`；正文 `05.md:36`。

触发：在相同工作区、相同调用 ID 下分别请求 `search_files({needle:"absent-query-A"})` 与 `search_files({needle:"absent-query-B"})`，两次搜索都没有命中，再最终返回 `done`。

观察：两次 `events` 完全相等，实际发送给模型的后续请求不同；事件记录了名称、ID、结果，却没有搜索参数或初始消息。Rust 使用 `event-A` / `event-B` 的等价输入也复现。`LoopResult.messages` 中有额外信息，但正文/演示所保存的事件不能独立做到声称的重放。

影响：不能核查究竟执行了哪个搜索请求，亦不能从事件恢复原始模型请求。这里要求的是当前章轨迹重建，不是第 13 章运行恢复。

复现证据：`p17-ts-independent.stdout.txt` 与 `p17-rust-isolated-independent.stdout.txt` 的 `event_only_reconstruction_counterexample`，均为 `events_equal: true`、`requests_equal: false`。

### 17-3：随包测试没有验证循环的后续请求与两套工作区

位置：`ts/tests/loop.test.ts:16–43`；`rust/src/rein/mod.rs:757–840`。

触发：运行正文指定循环测试并阅读断言。TS 4 个测试通过；Rust 3 个循环测试通过。TS 只查最终 `result.messages`，没有读取 `replayAdapter.receivedMessages`；Rust 的测试 Replay 明确忽略 `_messages`。两者都只用一套固定文本场景测试读取。

观察：这些断言能证明返回结果收集了文件内容，不能证明循环实际把它交给下一次模型调用。前置测试手动拼接两次模型请求，不替代对 `runAgentLoop` / `run_agent_loop` 的断言。独立探针实际补验成功，但交付测试要求仍未满足。

影响：将来循环忘记传历史或错误取快照时，现有测试仍可能通过；两工作区差异要求也未交付。

证据：`p17-ts-doc-test.stdout.txt`、`p17-rust-isolated-loop.stdout.txt` 及上述源码。

### 17-4：真实冒烟只给建议，Rust 示例参数声明缺少 path/needle

位置：`05.md:42`；`05-rust.md:27`；`rust/src/bin/ch05_loop.rs:76–85`；`ts/package.json`。

触发：按正文寻找可将 REIN_* 接入循环的可运行入口。只有 `ch05:offline`；TS 文字要求自行传 `createOpenAIAdapter`，Rust 文字要求自行包装 `openai_complete`，未给可执行入口/完整接线代码。Rust 演示传给模型的工具 schema 仅有 `{"type":"object"}`，没有 `path`、`needle` 或 required 字段。

观察：独立 Rust 桥接探针捕获到这两个不完整定义。按照该 schema 合法的 `read_file({path:42})` 仍会被实际 dispatcher 判为 `arguments_invalid`；TS 默认定义则公开了正确字段。核心 API 可限制 4 次，本次已验证；缺的是交付入口和正确的 Rust 示例声明。

影响：读者须自行实现未讲授的适配接线；模型无法从提供的参数合同获知正确必填输入。此处没有调用真实服务，也没有断言真实模型一定失败。

证据：`p17-rust-isolated-independent.stdout.txt` 的首轮 `requests[].tools` 与 `errors` 场景，及上述正文/脚本定义。

### 17-5：正文未构成完整可跟做教程

位置：`05.md:8–48`、`05-rust.md:8–39`。

触发：从两篇正文顺序跟做。可以运行现成示例，但直到练习仍没有环境准备、前置工程接入、创建回放模型/调用循环的代码步骤；“改 guide.md”的对象是运行中自动创建且清理的临时文件，正文也未指明应改示例中的写入值。真实入口进一步要求读者自行完成未展示的适配代码。

观察及影响：文章解释了 ID 和停止原因，却主要是工程概述与验收提示；难以让目标读者从本章材料学会构建或修改循环。应判“完整教程”未交付，不能因测试和命令成功宣布教程完成。不是按篇幅或字数扣分。

## package-42 具体问题

### 42-1：Rust 示例回放耗尽直接 panic，正文承诺的 ModelError 不会返回

位置：`rust/examples/ch05_loop.rs:11–19`；`docs/chapters/05-rust.md:49`。

触发：使用原文件中的 `Replay`（通过 `include!` 引入原示例，没有修改产品代码），只给一条 `no_such_tool` 工具响应、不给下一条响应，调用原 `run_agent_loop`，`max_turns=4`。

观察：第一次工具结果产生后，第二次模型调用在 `self.responses.lock().unwrap().remove(0)` 触发 panic：`removal index (is 0) should be < len (is 0)`，进程退出 101，没有返回 `LoopResult`、`ModelError` 或可保存的事件结果。正文却称“耗尽回放则错误进入 ModelError”。

影响：读者按失败实验耗尽回放时崩溃，失去本次结果与已有轨迹；示例自身不满足本章失败应明确结束和保存事件的要求。核心循环收到正常 `Err` 的情况另已通过，不能据此掩盖交付 Replay 的错误。

复现脚本：`rust-probe-42/src/bin/replay_exhaustion.rs`。原始证据：`p42-rust-replay-exhaustion.stdout.txt`、`.stderr.txt`、`.meta.json`。

### 42-2：默认演示不是多文件搜索后读取，TS 的实际执行顺序还与正文相反

位置：`ts/examples/ch05-loop.ts:6–15`；`fixtures/cases/prerequisites.json:4`；`rust/examples/ch05_loop.rs:25–45`；正文 `05.md:19`、`05-rust.md:18`。

触发：执行两文默认离线命令及 `single` 命令。

观察：fixture 工作区只有 `README.md`。TS 默认复用 Anthropic fixture，第一轮先 `read_file(README.md)`、再 `search_files(前置)`，随后直接返回固定 `已完成读取与搜索。`。Rust 第一轮同时声明 search 和固定 README 读取，再返回固定 `我找到了 README.md，并读取了真实内容。`。两者均没有“先看搜索结果，再据命中读多个文件”的模型轮次；TS 的顺序更直接与“多文件搜索后读取”相反。单文件模式真实读取正常，但 TS 单文件答案仍声称完成了搜索。

影响：读者无法从正文命令复现实验目标，两个语言示例的动作语义也不同。独立探针验证了核心循环可实现该能力，不代表示例已交付。

证据：`p42-ts-demo.stdout.txt`、`p42-ts-single.stdout.txt`、`p42-rust-isolated-demo.stdout.txt`、`p42-rust-isolated-single.stdout.txt`。

### 42-3：事件只有计数和 ID，无法按文中承诺重建请求

位置：`ts/src/rein/loop.ts:7–11`、`:39–52`；`rust/src/rein/mod.rs:587–608`；正文 `05.md:54`。

触发：相同调用 ID 分别搜索两个不同的不命中关键词，再返回同样最终文本。

观察：两次事件完全相同，实际后续请求不同。`model_requested` 仅记录 messageCount，`model_received` 仅记录 IDs/text，工具事件连工具名称和参数也不包含。正文称“保存 JSON.stringify(result.events) 后可重建每轮请求”不成立。Rust 整个 `LoopResult` 同时保留 messages 是有用的额外证据，但其 events 本身同样不够。

影响：保存正文指定的 events 后丢失实际输入，不能重建或独立核验调用。此缺口属于当前章可观察事件，不要求后续持久化恢复。

证据：`p42-ts-independent.stdout.txt`、`p42-rust-isolated-independent.stdout.txt` 的 `event_only_reconstruction_counterexample`。

### 42-4：Rust 循环发布的工具 schema 与执行合同不一致

位置：`rust/src/rein/mod.rs:643–649`，对照 `ts/src/rein/loop.ts:27–29` 及 Rust dispatcher `:539–555`。

触发：捕获原 `run_agent_loop` 发出的首轮 HTTP body；模型返回 `read_file({path:42})`。

观察：两个 Rust 工具 parameters 都只有 `{"type":"object"}`，而执行要求 `path`/`needle` 为字符串。输入在发布 schema 中合法，执行却返回 `arguments_invalid`。TS 同功能明确发布 properties 和 required。

影响：Rust 模型请求没有可用的参数说明，语言间对同一工具的声明合同不一致；离线 fixture 预知参数名掩盖了这一问题。没有将此推断成已实测的真实模型故障。

证据：`p42-rust-isolated-independent.stdout.txt` 中 `requests[0].tools` 与 `errors` 场景实际反馈；`p42-ts-independent.stdout.txt` 中对应声明。

### 42-5：交付 Rust 循环测试仅一个成功用例，未满足失败与后续请求检查要求

位置：`rust/tests/loop.rs:8–53`；`ts/tests/loop.test.ts:12–43`；正文 `05.md:48`、`05-rust.md:49`。

触发：运行 `cargo test --locked --offline --test loop` 并阅读测试，只有 1 个成功用例。Replay 的 `post` 忽略请求 body，只检查最终 result.messages；没有循环级模型失败、空最终、轮次上限或失败后继续测试。前置适配器测试不运行循环。

观察：TS 有 3 个用例且确实断言后续请求中的工具内容，这点通过；但其搜索/读取同轮预先决定，只有一套数据。两种语言均未交付两套不同临时工作区验证。

影响：正文测试说明不足以支撑所需行为覆盖，Rust 示例的耗尽 panic 也因此没有被发现。本次独立探针确认接口返回 Err 时循环正常失败，仍不能替产品补交测试。

证据：`p42-rust-isolated-loop.stdout.txt`（1/1）；`p42-ts-tests.stdout.txt`（循环 3 个）；上述源码。

### 42-6：顺序跟做、练习合同与真实入口仍有缺项

位置：`05-rust.md:11`、`:44`、`:49–55`、`:65–71`；`05.md:3`、`:56`、`:62–72`。

触发及观察：按 Rust 第 1 节已进入 rust，继续第 4 节又 `cd rust`，退出 1 并显示 `no such file or directory: rust`。练习 05-2 的 TS 要求不存在路径 → 下一轮读取正确路径、验收 `path_invalid`；Rust 则要求越界路径 → 直接最终回答、验收 `path_escape`，不是同一失败恢复行为。两端编号和锚点虽然匹配，行为合同不匹配。

真实入口只给“传适配器/换 ReqwestHttp”及引用未定义变量的一行调用，没有可执行的 REIN_* 加载、HTTP 构造、workspace/prompt 接线代码或命令。4 次限制在 API 上可行，独立已验证；真实服务未运行。

影响：顺序跟做中断；相同编号练习不能互相对照验收；读者仍需自行补写入口。另四篇共有的前置接入、环境和关键源码讲解缺项适用于此包，两文尚未达到完整教程要求。

证据：`p42-rust-doc-cd.stderr.txt`/`.meta.json`；`document-structure.json` 仅用于对照锚点和命令，质量判断依据完整正文阅读。

## 已执行的验证与原始日志

所有文件都在 `/private/tmp/rein-ch05-review-evidence-2/`。下表只摘要，原始退出码与输出不被覆盖。

| 运行 | 原始结果 | 日志前缀 |
|---|---|---|
| 两包 TS typecheck | 各退出 0 | `p17-ts-typecheck`、`p42-ts-typecheck` |
| 17 TS 正文循环测试 | 4/4，通过 | `p17-ts-doc-test` |
| 17 TS 完整测试 | 71/76；5 个 loopback listen EPERM | `p17-ts-tests` |
| 42 TS 完整测试 | 70/75；5 个 loopback listen EPERM | `p42-ts-tests` |
| 两包 TS transport 定向升级复跑 | 各 8/8，通过 | `p17-ts-transport-elevated`、`p42-ts-transport-elevated` |
| 两包 Rust fmt | 退出 0 | `p17-rust-fmt`、`p42-rust-fmt` |
| 17 Rust 完整测试，独立 target | lib 7/12；5 个 loopback 权限失败，之后未继续 | `p17-rust-isolated-tests` |
| 17 Rust lib 定向升级复跑 | 12/12，通过 | `p17-rust-isolated-local-elevated` |
| 17 Rust prerequisites 升级复跑 | 5/5，通过 | `p17-rust-isolated-prerequisites-elevated` |
| 17 Rust 正文 loop_ | 3/3；其他 target 的 0 测试不算证据 | `p17-rust-isolated-loop` |
| 42 Rust 完整测试，独立 target | lib 4/9；5 个 loopback 权限失败，之后未继续 | `p42-rust-isolated-tests` |
| 42 Rust lib 定向升级复跑 | 9/9，通过 | `p42-rust-isolated-local-elevated` |
| 42 Rust prerequisites | 4/5；1 个 loopback 权限失败 | `p42-rust-isolated-prerequisites` |
| 42 Rust prerequisites 单测试升级复跑 | 1/1，通过 | `p42-rust-isolated-prerequisites-elevated` |
| 42 Rust loop 测试 | 1/1，通过 | `p42-rust-isolated-loop` |
| 17 两端演示、42 两端默认/single 演示 | 全部退出 0，具体行为缺口见上 | 对应 `*-demo`、`*-single` |
| 四套独立核心探针 | 全部退出 0；每套包含两工作区、真实模型后续请求和失败路径 | `p17-ts-independent`、`p42-ts-independent`、`p17-rust-isolated-independent`、`p42-rust-isolated-independent` |
| 42 Rust 原 Replay 耗尽反例 | 退出 101、原示例第 18 行 panic | `p42-rust-replay-exhaustion` |

loopback 相关权限失败均在限定测试的升级复跑中通过，所以不计为实现失败；最终没有仍因监听权限而未确定的核心项目。没有把分次测试结果伪称成一次完整套件通过。

## 独立探针如何排除固定答案

`probe-ts.mts` 与两个 `rust-probe-*/src/main.rs` 用离线 transport/OpenAiHttp 记录真实发送 body，再调用产品的真实适配器及循环。package-17 Rust 因未交付 LoopAdapter 的 OpenAI 包装，探针仅用一层转发桥调用原 `openai_complete`，未重写或替换产品循环/工具。

工作区 A 为 `a.txt = marker: 蓝色 17`、`nested/b.txt = marker: 山海 31`；工作区 B 为 `changed.txt = marker: 金色 29`、`other.md = marker: 风声 47`。第二次模型响应必须从实际 search tool message 解析文件名并创建两个读取调用；第三次响应必须从实际 read tool messages 拼出答案。四个实现都返回对应的新内容，原请求和结果完整保留。

失败输入依次为未知工具、`read_file({path:42})`、`read_file({path:"missing.md"})`、读取目录 `.`；下一次模型请求分别收到 `unknown_tool`、`arguments_invalid`、`path_invalid`、`read_failed`，ID 顺序保持。另在已经读取文件之后令模型错误，检查已有事件仍在且无答案；空白最终文本无答案；连续工具调用恰在 32/4 次结束。

事件反例保存了两个真实请求不同、事件相同的完整对象，未要求程序重启恢复。`replay_exhaustion.rs` 通过 include! 调用交付示例的原 Replay，反例没有把副本修改后的实现冒充产品。

本报告不提供加权总分，不以作者工作流记录格式评分。最终结论是两包均需要补齐当前章交付后再接受；已有核心能力的通过证据可保留，具体修改应针对以上可复现缺口。
