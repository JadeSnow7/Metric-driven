---
prev:
  text: 04 统一模型适配
  link: /chapters/04.html
next:
  text: 06 预算、取消与超时 · 待撰写
  link: /chapters/06.html
---

# 05 核心 Agent Loop（Rust）

一次 `chat` 只能得到一次回答。只要模型要求搜索和读取，程序就必须保留 assistant 的工具调用，把工作区中的真实结果作为 `tool` 消息放回历史，再发起下一轮。本章在已有 Rust 消息合同、OpenAI/Anthropic 转换和只读工具之上加入这个循环；预算、取消、超时与重复检测留到第06章。

<span id="knowledge-loop"></span>
<span id="知识点-循环与工具结果配对"></span>

## 准备并运行离线示例

在仓库根目录执行：

```bash
cd rust
CARGO_TARGET_DIR=/tmp/rein-ch05-target cargo fmt -- --check
CARGO_TARGET_DIR=/tmp/rein-ch05-target cargo run --locked --offline --bin ch05_loop
```

示例临时创建 `guide.md`，离线模型依次请求 `search_files`、`read_file`，最后把真实读取文本组成回答。输出是 JSON，能找到 `"type":"tool"`、`search-1`、`read-1` 和 `"reason":"completed"`。因此它不依赖 key，也不是把搜索结果写在模型回放里：`dispatch_readonly` 读取的是示例刚写入的文件。

## Rust 中的循环边界

`rust/src/rein/mod.rs` 的 `LoopAdapter` trait 只约定一次 `complete`，具体适配器可以是 `openai_complete` 的包装，也可以是测试回放。`run_agent_loop` 自己负责状态：

1. 复制初始 `Message`，记录 `Started`。
2. 调用 adapter，记录 `Model`，并把 assistant 消息追加到历史。
3. 没有工具调用时，非空文本产生 `Completed`；空文本产生 `EmptyFinal`。
4. 有工具调用时按声明顺序调用 `dispatch_readonly`，为每个结果追加 `role: "tool"`，并记录 `Tool`。
5. 模型错误产生 `ModelError`；超过默认调用方传入的轮数产生 `MaxRounds`。

工具结果始终带原始 `tool_call_id`。成功结果的消息内容是文件或搜索文本；失败结果则是包含结构化错误的 JSON。这样后续模型请求会同时携带 assistant 的调用列表和逐一匹配的工具结果，多个调用不会串线。

## 测试和失败处理

```bash
CARGO_TARGET_DIR=/tmp/rein-ch05-target cargo test --locked --offline
```

已有前置测试检查合同与只读工具，本章的循环行为也由 `run_agent_loop` 的数据结构保证：未知工具、参数错误和读取失败仍是 `ToolResult { ok: false, error: ... }`，不是成功字符串。adapter 返回 `Err` 时已经发生的事件保留在 `LoopResult` 中，且 `ok` 为 `false`。只有无工具、非空文本才是正常最终回答。

真实模型接入时，可以实现 `LoopAdapter`，在 `complete` 内调用已有 `openai_complete`；生产入口应显式使用 `REIN_BASE_URL`、`REIN_API_KEY`、`REIN_MODEL`，并把轮次限制设为不超过 4。本次示例不会读取个人配置或请求网络。

<span id="failure-paths"></span>

## 事件为什么值得保存

`LoopEvent` 是可序列化的运行轨迹：它保存轮次、工具调用 ID、工具名称、工具结果和停止原因。只看退出码无法区分“模型正常回答”和“模型失败后程序提前结束”；看事件则能确认每一次调用和结果的对应关系。消息历史是给模型的输入，事件序列是给人和测试的证据，两者用途不同。

<span id="exercise-05"></span>

## 练习 05

任务：复制 `rust/src/bin/ch05_loop.rs` 的离线模型，增加一个先读取 `missing.md`、再根据失败结果回答的回合，并把 `guide.md` 内容换成自己的句子。

可观察验收：运行同一条 `cargo run --locked --offline --bin ch05_loop` 命令时，JSON 事件包含失败工具调用的 ID，`result.ok` 为 `false` 且错误码为 `path_invalid`，最终停止原因为 `completed`；换文件内容后，读取事件中的文本也必须变化。
