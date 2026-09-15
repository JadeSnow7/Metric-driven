---
prev: { text: 05 让工具结果推动下一轮, link: /chapters/05-rust.html }
next: { text: 07 上下文与状态, link: /chapters/07-rust.html }
---

# 06 循环控制（Rust）

上一章的 Rust 循环已经把搜索和读取结果作为下一轮消息。现在的问题是生命周期：一个 Agent 继续产生工具调用时，谁决定它必须停下？本章在 Tokio 异步循环中分别控制模型回合、工具派发、重复动作、取消和整体截止时间。你会看到 Rust 的 future、`select!` 和原子信号怎样共同表达这个边界。

正文对应未来打包的 `rein-ch06.tar.gz` 文件树快照；它不是 Git 提交或标签。可先按[阅读材料 2](/readings/02.html)恢复快照，再在书根准备同一份绝对输入：

```bash
export REIN_CH06_DIR="$(mktemp -d)"
printf 'marker: ch06 alpha\n' > "$REIN_CH06_DIR/README.md"
printf 'marker: ch06 beta\n' > "$REIN_CH06_DIR/guide.md"
CARGO_TARGET_DIR=/private/tmp/rein-candidate03-build cargo build --manifest-path rust/Cargo.toml
```

## 先看正常的三回合

<a id="loop-entry"></a>

```bash
CARGO_TARGET_DIR=/private/tmp/rein-candidate03-build cargo run --manifest-path rust/Cargo.toml --example ch06_loop -- normal "$REIN_CH06_DIR"
```

回放适配器第一次返回搜索调用 `search-1`，循环读取两个文件；第二次返回 `read-1`、`read-2`，第三次以真实内容组成 `完成：marker: ch06 alpha | marker: ch06 beta`。JSON 中 `requests` 和 `settledRequests` 都是 3，说明示例等待结束后没有额外的迟到模型回合。把 README 改成另一个 marker 后重跑，最终答案随输入变化；这是工具消息推动下一轮的证据，而不是脚本直接打印固定答案。

ch05 的公共入口也仍可复跑：

```bash
CARGO_TARGET_DIR=/private/tmp/rein-candidate03-build cargo run --manifest-path rust/Cargo.toml --example ch05_loop -- workspace "$REIN_CH05_DIR" multi
```

`CARGO_TARGET_DIR` 只把构建产物放在实验目录，不写入正文或输入工作区。

## 两种预算在不同边界生效

<a id="budget-and-stop"></a>

```bash
CARGO_TARGET_DIR=/private/tmp/rein-candidate03-build cargo run --manifest-path rust/Cargo.toml --example ch06_loop -- budget "$REIN_CH06_DIR"
CARGO_TARGET_DIR=/private/tmp/rein-candidate03-build cargo run --manifest-path rust/Cargo.toml --example ch06_loop -- tool-zero "$REIN_CH06_DIR"
CARGO_TARGET_DIR=/private/tmp/rein-candidate03-build cargo run --manifest-path rust/Cargo.toml --example ch06_loop -- zero "$REIN_CH06_DIR"
```

`LoopOptions.max_turns` 统计进入模型适配器的回合，`max_tool_calls` 统计真正调用 `dispatch_readonly` 的次数。`budget` 的一次模型回合返回 `one`、`two`：`one` 产生 `ToolResult`，`two` 产生 `ActionSkipped { reason: ToolBudgetExhausted }`。`tool-zero` 的一次模型请求中两个调用都跳过。`zero` 的 `max_turns` 为 0，因此模型请求数为 0，停止原因为 `max_turns`。Rust 程序以退出码 0 输出这些业务失败状态，只说明 CLI 成功完成报告；不能把它当成任务成功。

每个真实工具结果都同时有 `tool_result` 事件和带 `toolCallId` 的 `tool` 消息。跳过动作没有工具结果，也没有未执行调用的消息，因此下一轮看不到虚构的输出。事件中的停止原因使用 snake_case；`toolCallId` 保持跨语言合同的 camelCase。

## 重复动作的身份不包含调用 ID

<a id="duplicate-action"></a>

```bash
CARGO_TARGET_DIR=/private/tmp/rein-candidate03-build cargo run --manifest-path rust/Cargo.toml --example ch06_loop -- duplicate "$REIN_CH06_DIR"
```

Rust 回放中的两个调用 ID 固定为 `duplicate-1` 与 `duplicate-2`。两次调用的动作都是 `read_file`，参数都是 README；`duplicate_limit: 1` 因而允许第一次，第二次被 `ActionSkipped`，最终 `DuplicateAction`。循环通过工具名和 `canonical_json` 拼接身份，`canonical_json` 对对象键递归排序，数组顺序不改变。调用 ID 仍用于把事件与消息对应起来，但不能让同一个语义动作通过改 ID 逃过阈值。

`duplicate_limit` 是允许同一身份实际派发的次数。它不等于模型可以返回多少次调用，也不负责判断读取内容是否正确。若参数中有数组，不能为了去重擅自排序，因为那会改变参数语义。

## 取消、future 和资源生命周期

<a id="cancellation"></a>

```bash
CARGO_TARGET_DIR=/private/tmp/rein-candidate03-build cargo run --manifest-path rust/Cargo.toml --example ch06_loop -- cancel-before "$REIN_CH06_DIR"
CARGO_TARGET_DIR=/private/tmp/rein-candidate03-build cargo run --manifest-path rust/Cargo.toml --example ch06_loop -- cancel "$REIN_CH06_DIR"
CARGO_TARGET_DIR=/private/tmp/rein-candidate03-build cargo run --manifest-path rust/Cargo.toml --example ch06_loop -- cancel-at-return "$REIN_CH06_DIR"
CARGO_TARGET_DIR=/private/tmp/rein-candidate03-build cargo run --manifest-path rust/Cargo.toml --example ch06_loop -- cancel-between-tools "$REIN_CH06_DIR"
```

`cancel-before` 在第一次模型请求前检查 `ControlSignal`，所以 `requests: 0`。`cancel` 的回放 future 等待 100ms，而另一个 Tokio 任务在 20ms 调用 `ControlSignal::cancel`；`await_control` 用 `tokio::select!` 观察 future 与取消/截止时间，返回 `cancelled`，迟到 future 被丢弃。`cancel-at-return` 在返回“迟到答案”之前设置标志，循环在收到结果后再次检查，因此答案不会进入 `LoopResult`。这只隔离本地结果；它没有撤回服务器已处理的网络请求。

`cancel-between-tools` 安装 `ToolObserver`，第一项 `one` 完成后 observer 调用 `cancel`。第一项的 `ToolResult` 和消息被保留，第二项 `two` 记录为 `ActionSkipped`。observer 是可信的本地观察点：它能看到已完成的调用和结果，并取消现有运行；它不能排队新的工具或修改工作区。Rust 的 `Arc<AtomicBool>` 让 signal 可克隆并在线程间观察，`Release/Acquire` 保证取消状态可见。

整体截止时间覆盖模型等待和同轮工具间隔：

```bash
CARGO_TARGET_DIR=/private/tmp/rein-candidate03-build cargo run --manifest-path rust/Cargo.toml --example ch06_loop -- timeout "$REIN_CH06_DIR"
```

示例传入 30ms 的 `timeout`，而模型 future 等待 100ms，结果为 `timeout`。这与模型适配器自己的 HTTP 请求超时属于不同层次；本地睡眠只是在可控条件下制造竞争，不能当作服务性能测量。

## 走读 Rust 核心

`ControlSignal` 是 `Arc<AtomicBool>` 的轻量句柄；`ModelAdapter::complete_controlled` 接收它，真实适配器可以把它继续传给传输层。`run_agent_loop_with_options` 在进入每轮、模型 future 返回后、每个工具调用前以及 observer 返回后调用 `control_reason`。`await_control` 在有 deadline 时同时观察剩余 `Duration`，所以 timeout 和 cancelled 能分别落到结构化 `StopReason`。

模型响应先产生 `ModelReceived`、再进入消息历史。工具循环随后按顺序检查预算、控制信号和重复身份；只有检查通过才递增 `tool_started`、同步调用 `dispatch_readonly`，写入 `ToolResult` 与工具消息，再调用 observer。剩余调用仅写 `ActionSkipped`。旧的 `run_agent_loop_with_adapter(..., max_turns)` 保留默认选项，因而 ch05 的公共调用仍兼容。

`Pin<Box<dyn Future<...> + Send>>` 允许不同适配器提供异步计算，`select!` 未选中的分支在取消时释放 future。若适配器自己启动外部进程，它仍必须在自己的 future 取消路径清理进程；本章离线回放没有子进程，不能据此声称外部资源清理已被全面验证。工具 schema 仍只是模型可见声明，真实路径限制在 `dispatch_readonly`。

## 练习

<a id="practice-06-1"></a>

### 练习 06-1：改变重复阈值

在快照的 `rust/examples/ch06_loop.rs` 中将 `duplicate_limit` 的 `1` 改为 `2`，运行 `duplicate`。预期第一次和第二次均有 `ToolResult`，第三次才有 `ActionSkipped` 与 `duplicate_action`；Rust 示例的调用 ID 是固定的 `duplicate-1`、`duplicate-2`，不要假设它与 TypeScript 的动态编号相同。恢复为 1 后只应启动一次工具。`max_turns` 为 3，不会先挡住该实验。

<a id="practice-06-2"></a>

### 练习 06-2：改变取消发生点

在 `rust/examples/ch06_loop.rs` 的取消等待处把 20ms 改为 0，再改为 50，运行 `cancel`。检查 `ModelRequested`、`ModelReceived`、`ToolResult`、最终 `reason` 和延迟后 `settledRequests`。0ms 更容易在模型返回前触发，50ms 则可能让 future 先返回；循环仍会在返回后检查 signal，因此答案只有在信号尚未设置时才有资格进入结果。不要只依据退出码判断业务完成。

<a id="practice-06-3"></a>

### 练习 06-3：同轮工具预算

在 `LoopOptions` 初始化处把 `budget` 的 `max_tool_calls` 从 1 改为 2，再运行 `budget`。两个调用都应有真实结果；改回 1 后第二个只能出现在 `ActionSkipped` 中，`messages` 不应出现它的 `toolCallId`。提高工具预算只扩大派发边界，不保证下一轮一定得到最终答案。

本章命令中的构建目录是临时验证路径；正文不依赖任何私有工作区路径。快照将在主线程审阅全文后由指定打包步骤生成。
