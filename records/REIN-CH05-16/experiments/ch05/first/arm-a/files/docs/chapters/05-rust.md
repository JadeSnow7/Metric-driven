---
prev: { text: 04 统一模型适配, link: /chapters/04.html }
next: { text: 06 预算、取消与超时 · 待撰写, link: /chapters/06.html }
---

# 05 核心 Agent Loop（Rust）

模型要求搜索和读取时，Rust 程序要执行工作区工具，把每个结果作为带原调用 ID 的 `tool` 消息放回历史，再继续请求。本章在前置消息合同、适配器和只读工具之上加入循环；预算、取消和超时留到第06章。

<span id="knowledge-loop"></span>
<span id="知识点-循环与工具结果配对"></span>

## 运行离线演示

```bash
cd rust
CARGO_TARGET_DIR=/tmp/rein-ch05-target cargo fmt -- --check
CARGO_TARGET_DIR=/tmp/rein-ch05-target cargo run --locked --offline --bin ch05_loop
```

示例临时创建 `guide.md`，离线模型依次请求 `search_files` 和 `read_file`。输出 JSON 应包含 `search-1`、`read-1`、工具结果以及 `completed`；文件内容由 `dispatch_readonly` 真实读取，不是回放硬编码。

## 实现和失败路径

`rust/src/rein/mod.rs` 的 `LoopAdapter` 只负责一次 `complete`。`run_agent_loop` 保存消息与 `LoopEvent`：先记录 `Model`，再按声明顺序执行工具并记录 `Tool`。工具成功消息使用真实文本，失败消息使用包含结构化错误的 JSON。没有工具且非空文本才是 `Completed`；空文本为 `EmptyFinal`，适配器错误为 `ModelError`，超过调用方给定轮数为 `MaxRounds`。

`tool_call_id` 是关联键，多个调用不会串线。消息历史供模型使用，事件序列供人和测试核查。真实接入可在 adapter 中包装已有 `openai_complete`，并显式使用 `REIN_BASE_URL`、`REIN_API_KEY`、`REIN_MODEL`；本示例不读密钥、不联网。

```bash
CARGO_TARGET_DIR=/tmp/rein-ch05-target cargo test --locked --offline loop_
```

本章测试验证真实文件内容、多调用顺序、未知工具失败、模型错误与空最终回答。

<span id="failure-paths"></span>

## 练习 05

让离线模型先读取不存在的 `missing.md`，再依据 `path_invalid` 回答；修改 `guide.md` 为自己的句子。验收：事件含失败调用 ID 和 `ok=false`，错误码为 `path_invalid`，最终停止原因仍为 `completed`，并且读取文本随文件内容变化。
