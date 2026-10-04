# ch06 修复冻结合同（生产返工 v3，非正式配对实验）

上一轮尚未通过，v2 先封存后方可继续写入。生产根唯一为 /private/tmp/rein-production-candidate-03。受测 skill 不变。正文待代码门槛通过后交给独立作者。TS 与 Rust 作者分别只写自己的语言目录；TS 作者另唯一拥有本章 fixture 和比较脚本，Rust 作者只读取。均不得覆盖根目录，不安装/重装现有依赖，不碰其他章节正文、快照、锁文件、导航或原 Rein 工作区。

## 共同场景及预期

示例命令保持 ch06:offline 与 ch06_loop，mode 为首参数，未知 mode 必须失败。共同输出为 {mode, requests, settledRequests, result}；requests 由 adapter 真正开始次数计数，settledRequests 在停止后的观察间隔再次读取，必须与 requests 相同。result 为真实核心 loop 结果，不填预制成功事件。工具派发和结果须来自真实只读工具。工具完成后的可信观察回调可用于确定性取消，不赋予新工具能力；保留现有 API 的默认兼容性。

| mode | 模型次数 | 实际工具调用 ID（顺序） | 跳过 ID | 停止原因 |
|---|---:|---|---|---|
| normal | 3 | search-1, read-1, read-2 | 无 | final_answer |
| budget | 1 | one | two | tool_budget_exhausted |
| duplicate | 2 | duplicate-1 | duplicate-2 | duplicate_action |
| zero | 0 | 无 | 无 | max_turns |
| tool-zero | 1 | 无 | one, two | tool_budget_exhausted |
| cancel-before | 0 | 无 | 无 | cancelled |
| cancel | 1 | 无 | 无 | cancelled |
| cancel-at-return | 1 | 无 | 无 | cancelled |
| cancel-between-tools | 1 | one | two | cancelled |
| timeout | 1 | 无 | 无 | timeout |

normal 的输入：README.md 内容为 `marker: ch06 alpha\n`，guide.md 内容为 `marker: ch06 beta\n`。首轮 search_files({needle:"marker: ch06"})，次轮分别 read_file README.md 与 guide.md，第三轮从两条实际读结果产生答案 `完成：marker: ch06 alpha | marker: ch06 beta`，禁止固定答案。可选第二参数为已有 workspace 的绝对路径，normal 用实际输入运行，默认才创建上述样例；这供正文展示改变输入改变答案。

budget/tool-zero/cancel-between-tools 首轮均返回 one=read_file README.md, two=read_file guide.md。budget=1，tool-zero=0，取消场景在 first tool_result 的可信观察回调中取消，第二个工具不得开始。duplicate 每轮仅返回一次 read_file README.md，阈值1（容许一次）。zero 指模型预算0。cancel-before 在运行前取消。cancel 为模型等待中取消：adapter 开始时安排取消，适配器保持至少100ms才有迟到响应；约20ms取消、停止后再观察至少120ms以证实迟到结果不会追加事件、answer或新动作。cancel-at-return 在 adapter 返回最终文本前同步取消，循环必须拒绝这份结果。timeout 为相同延迟模型，整体30ms截止且同样观察迟到响应。调度必须给合理余量，不使用1ms竞赛。

比较器必须逐场景核对 fixture 中的预期 reason、state、模型次数、实际工具次数、调用 ID/名称/参数与顺序、跳过顺序和原因、answer（失败时无），并比较两语言规范化输出；不能仅比较相同错误值，不能忽略未知/遗漏场景。可忽略环境绝对路径与计时值。CARGO_TARGET_DIR 只继承外部环境，禁止在产品脚本或正文硬编码本机路径。TS writer 将本表变为 fixtures/cases/ch06-control.json，并将实际比较结果保存为原始证据；在 Rust 就绪前只做单语言预期检查，不宣称跨语言通过。

## 库行为与针对性验证

保留 ch05 基本工具循环；预算检查作用于派发而非结果输出，外部取消/整体截止在模型返回、工具之间、最后一轮结束仍需检查。相同工具身份采用递归排序 JSON，覆盖嵌套/键顺序以及不同 call ID。工具预算0仍允许一次模型请求，模型预算0不派发模型。取消和超时后的迟到响应不得变成成功或继续动作。TS raceControl 所有路径包括同步 throw / 已取消均清理监听器和 timer；外部 signal 传至真实 fetch。用受控 fetch 测试接收 signal 并在取消时 reject 的实际路径，禁止仅检查参数相等。Rust 通过 drop future 停止等待，测试 Drop guard 或显式可取消适配器观察；不得称已撤销服务器处理。

每个作者负责本语言 meaningful 单元/集成测试，至少覆盖本表各关键分支与嵌套重复、同轮工具间取消、取消与最后响应竞争、旧 ch05 回归。已有 localhost 测试若 sandbox EPERM，可安全提升只读执行权限运行原测试；不删测、不降断言。根审查将复核源码与原始证据。记录精确命令、cwd、开始结束、exit、stdout/stderr 与本次文件 hash，缺失历史信息保持缺失。
