# 05 核心 Agent Loop（Rust）

Rust 版本复用 `rein::Message`、`ToolCall`、`ToolResult` 与 `OpenAiHttp`。新增循环在 `rust/src/rein/mod.rs`，把模型适配器、只读工作区工具和事件轨迹接在一起。

<span id="ch05-loop"></span>
<span id="message-tool-pairing"></span>

## 1、运行离线程序

```bash
cd rust
cargo fmt --check
cargo test --locked --offline
cargo run --locked --offline --example ch05_loop
cargo run --locked --offline --example ch05_loop -- single
```

`ch05_loop` 中的 `Replay` 实现 `OpenAiHttp`，两段 OpenAI wire JSON 只替代模型响应；工作区仍是 `../fixtures/workspaces/prerequisites`。不带参数是搜索后读取，附加 `single` 是单文件读取；工具都访问真实文件。输出包含请求、工具结果、下一轮响应和停止事件，末尾应为 `Completed` / `FinalAnswer`。

<span id="tool-loop-mechanism"></span>

## 2、消息如何驱动下一轮

`run_agent_loop` 每轮调用 `openai_complete`，把返回的 assistant message 放入 history，再按 `Vec` 声明顺序调用 `dispatch_readonly`，建立 `role: "tool"` 消息：

```text
assistant.tool_calls[0] → tool.tool_call_id == calls[0].id
assistant.tool_calls[1] → tool.tool_call_id == calls[1].id
```

成功 content 是文件或搜索文本；失败 content 是含 `ok: false` 和结构化错误的 JSON。所有消息进入下一次请求，模型才能根据事实继续行动。不能只取 `first()`，本例用两个调用验证顺序与配对。

<span id="event-replay"></span>

## 3、事件与停止

`LoopEvent` 是 serde 可序列化枚举，记录请求轮次、模型调用 id、工具结果和停止事件；`LoopResult` 同时保留 messages。无调用且非空文本才是 `Completed / FinalAnswer`；空文本是 `Failed / EmptyFinal`，适配器错误是 `Failed / ModelError`，达到 `max_turns` 是 `Failed / MaxTurns`。本章传入 32；预算、取消和超时属于第 06 章。

<span id="failure-paths"></span>

## 4、测试与真实入口

```bash
cd rust
cargo fmt --check
cargo test --locked --offline
```

共享合同测试覆盖 wire 解析、多调用和真实 fixture 工具。把示例的工具名换成 `no_such_tool` 可看到 `unknown_tool`；把最终 content 改为空可看到 `EmptyFinal`；耗尽回放则错误进入 `ModelError`。真实服务中可将 `Replay` 换成 `ReqwestHttp`，调用：

```rust
let result = run_agent_loop(&http, &base_url, &key, &model, &workspace, prompt, 4).await;
```

本章不读取个人环境、不发网络请求；真实冒烟应最多 4 次且不自动重试。

<span id="exercises"></span>

## 5、练习

### 练习 05-1：另一份工作区

写两份不同文本并修改 `Workspace.root`。验收：搜索和 tool result 随文件变化，不是固定 fixture 文本。

### 练习 05-2：失败后继续

第一轮请求 `../outside`，第二轮返回最终文本。验收：结果为 `ok: false`、`path_escape`，id 一致，第二轮仍可成功。

### 练习 05-3：停止原因

分别制造空文本、HTTP 错误、连续工具调用且 `max_turns=2`。验收原因为 `EmptyFinal`、`ModelError`、`MaxTurns`，三者 `answer` 都是 `None`。

两端现在共享章节编号、锚点和练习语义，具备下一章控制策略的循环边界。
