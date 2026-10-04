# 06 循环控制（Rust）

TypeScript 版本暴露了一个问题：32 轮上限只是最后一道栅栏。Rust 版本使用同一份消息和事件合同，在 `rein::loop` 中加入工具预算、规范化重复检测、取消信号和整体截止时间。示例使用 Tokio 的真实异步等待，数据来自运行时创建的临时文件。

<a id="loop-entry"></a>
## loop-entry：运行正常任务

从仓库根目录执行：

```bash
CARGO_TARGET_DIR=/private/tmp/rein-candidate03-build cargo run --manifest-path rust/Cargo.toml --example ch06_loop -- normal
```

结果包含一次 `read_file` 工具结果和最终 `完成`。工具读取示例创建的 `README.md`，没有预写答案分支替代读取。上一章入口仍可执行：

```bash
CARGO_TARGET_DIR=/private/tmp/rein-candidate03-build cargo run --manifest-path rust/Cargo.toml --example ch05_loop -- workspace ./fixtures/workspaces/prerequisites multi
```

<a id="budget-and-stop"></a>
## budget-and-stop：模型预算与工具预算

```bash
CARGO_TARGET_DIR=/private/tmp/rein-candidate03-build cargo run --manifest-path rust/Cargo.toml --example ch06_loop -- budget
CARGO_TARGET_DIR=/private/tmp/rein-candidate03-build cargo run --manifest-path rust/Cargo.toml --example ch06_loop -- zero
```

`LoopOptions.max_turns` 统计已进入适配器的模型请求，`max_tool_calls` 统计已调用只读分派器的工具。`budget` 返回 `tool_budget_exhausted`，第二个同轮调用产生 `action_skipped`；`zero` 不调用模型，返回 `max_turns`。事件停止原因使用 snake_case，`callId` 等字段保持跨语言合同的 camelCase。

<a id="search-read"></a>
## search-read：重复身份

```bash
CARGO_TARGET_DIR=/private/tmp/rein-candidate03-build cargo run --manifest-path rust/Cargo.toml --example ch06_loop -- duplicate
```

重复身份由工具名和 `canonical_json` 组成。对象键排序后再比较，所以不同调用 ID 仍是同一个动作。`duplicate_limit: 1` 允许一次真实派发，下一次记录跳过并停止。数组顺序保留，因为它是参数语义的一部分。

<a id="cancellation"></a>
## cancellation：信号、异步边界和资源生命周期

```bash
CARGO_TARGET_DIR=/private/tmp/rein-candidate03-build cargo run --manifest-path rust/Cargo.toml --example ch06_loop -- cancel
CARGO_TARGET_DIR=/private/tmp/rein-candidate03-build cargo run --manifest-path rust/Cargo.toml --example ch06_loop -- timeout
```

`ControlSignal` 是可克隆的原子取消标志。`ModelAdapter::complete` 收到它，可以在自己的传输层向下传递；循环同时用 `tokio::select!` 观察模型 future 和控制观察 future。适配器不支持取消时，select 会丢弃迟到结果，后续不会把它加入消息，也不会派发工具。截止时间由 `Instant` 计算，覆盖模型等待和同轮调用之间的间隔。

Rust 的 future 只有被 poll 才能推进，`select!` 取消未选中的分支会释放 future。已启动的外部进程若由适配器创建，适配器仍需在 future 的取消路径清理它；本章回放没有子进程。

## 机制走读

`run_agent_loop_with_options` 在每轮请求前调用 `control_reason`，并将 `&ControlSignal` 传入 `complete`。模型返回后，循环先记录 `ModelReceived`，再逐个检查工具预算、取消/截止时间和重复计数。超出的调用只写 `ActionSkipped`，不会写 `ToolResult` 或 tool message。旧的 `run_agent_loop_with_adapter(..., max_turns)` 保留默认选项，因此 ch05 公共入口兼容。

工具 schema 是发给模型的声明，真实路径检查在 `dispatch_readonly`；`additionalProperties: false` 不是运行时 JSON 验证器。`Pin<Box<dyn Future...>>` 让适配器返回异步计算；`Send` 约束保证 future 可在线程池移动，取消语义仍由 signal 和 future 生命周期共同完成。

## 练习

<a id="practice-06-1"></a>
### 练习 06-1：改变重复阈值

在 `rust/examples/ch06_loop.rs` 将 `duplicate_limit` 从 1 改为 2。运行 `duplicate`，应先得到两次 `tool_result`，第三次得到 `ActionSkipped`；改回 1 后只应启动一次工具。

<a id="practice-06-2"></a>
### 练习 06-2：改变取消时机

把示例中的 5 毫秒等待改为 0 和 50，再运行 `cancel`。观察 `ModelRequested`、`ToolResult` 和最终 `reason`；等待输出后一小段时间，计数不应增长。

<a id="practice-06-3"></a>
### 练习 06-3：同轮多调用的预算

把 `max_tool_calls` 改为 2 后运行 `budget`，两个调用应各有结果；恢复为 1，第二个调用只能出现在 `ActionSkipped` 中。检查 `messages`，不应有未执行调用的 `toolCallId`。

本章快照会在主线程验收后归档。`CARGO_TARGET_DIR` 是实验专用构建目录。
