# 运行时修复的当前门槛

旧 runtime coder 只拥有 `rust/tests/stdio_host.rs` 和测试证据的写权限，不再修改 runtime 源码。原因：多次交接仅编译，关键测试未写；最后取消修改将 started 校验注释掉，并把等待 terminal 时观察到的取消直接强杀后返回 Cancelled，未取得可信取消结果。

下一位源码 coder 应以测试为门槛完整修复该模块，不在有缺陷的分支上继续叠加状态。保持现有公共兼容入口。

## 必须保持的不变量

1. 仍是实际 Rust loop → ToolExecutor → Node TS host → tool message → 下一次模型调用。示例模型必须读取匹配 callId 的真实内容并据此回答，不因存在任意 tool 消息就宣称读取成功。
2. core 先检查预算、允许工具、参数及 canonical 工作区边界。固定只读策略不授予 Node 操作系统沙箱。任务标识每个运行固定，请求及会话标识每次唯一。
3. 版本和所有标识逐条验证。成功仅 output+evidence；工具失败仅 error；取消没有这些字段。证据检查 task/call/path/rule/targetVersion，且采用前重新确认当前 canonical 目标的 SHA256 和真实 UTF8 内容。
4. ready、started、terminal、EOF 是有状态的协议。开始之前退出为 not_dispatched；请求可能已送达后任何无法确认的结局为 outcome_unknown。任何重复、畸形或多余响应都不能被当作干净 EOF。
5. 同一 loop 的取消和 deadline 在工具等待期间持续生效。core 发出 cancel 后等待有界终态，只有完整关联的取消终态、干净输出和子进程已回收才可报告已确认取消；否则为未知。取消不等于副作用回滚。
6. 不要在每次 poll 时丢弃正在组装的部分帧。可使用独立有界读取任务与消息队列，或在同一个状态循环内保留 pending read；整行大小在扩容前受限。stderr 可继承，不留下未消费的管道。
7. 所有读写、grace、EOF 等待和进程退出均有界；显式 kill/wait 清理，kill_on_drop 只作兜底。若超时或强杀，保留原未知结局，不能因强杀成功而变为 Cancelled。
8. Rust 持有内存调用记录，至少包含 call/request/task、是否实际派发、终态、原因及 child PID/回收结果。事件或调用记录让故障可以审查；此记录不冒充持久 journal。
9. outcome_unknown 直接停止 loop，不产生普通 tool_failure 供模型自动尝试下一次；没有自动重启、重试或恢复重放。

## 实际测试

以 `rust/tests/stdio_host.rs` 驱动真实 Node 进程。正常唯一文件 marker 必须进入第二次模型输入与答案；异常仅一次模型调用且没有答案。故障宿主位于 `ts/tests/fixtures/hybrid-fault-host.ts`，生产宿主位于 `ts/src/hybrid-host.ts`。

必须覆盖：坏 JSON、错误版本/标识、同一终态冲突字段、重复终态；延后于实际 started 的取消、忽略取消；ready 前崩溃、invoke 后退出；临时 ledger 写入并关闭后断连，只有一条记录且结果未知；证据绑定错误和目标变化。用同内容的正常 fixture 作正对照，避免错误用例仅因输出不匹配而失败。还要检查预算 0、路径越界/符号链接、超长无换行响应与终态后挂起。

CLI 提供读者可直接运行的 normal、invalid、cancel、crash、disconnect-after-effect 场景。输出使用 serde 的稳定 snake_case 状态及真实计数，不以命令行场景名直接决定结果。故障 CLI 在专用临时目录运行，不修改作者文件。

测试数据不依赖真实模型或用户凭据。全部必要离线门槛通过后，再同步 06-plugin 正文、审查差异、有限路径回写并在原工作区重测。
