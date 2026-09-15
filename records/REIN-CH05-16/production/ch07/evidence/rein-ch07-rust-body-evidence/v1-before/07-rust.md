---
prev: { text: 06 循环控制, link: /chapters/06-rust.html }
next: { text: 08 上下文策略, link: /chapters/08-rust.html }
---

# 07 Rust：在循环中管理上下文

第 06 章解决的是“什么时候停止”。但即使循环没有触发 `max_turns`，历史也可能长到模型无法接受。把旧消息随意删掉会丢失规则、目标或最近的依据；把它们全发出去又可能超过预算。本章把四个对象分开：规则是每次发送都要带上的约束，当前目标是本次运行要完成的请求，完整历史是审计用的事实，发送上下文是本轮真正交给模型的消息副本。

本文使用 `chapter-snapshots/rein-ch07.tar.gz` 对应的 Rust 实现。恢复章节时应将归档解到新的临时目录，再从该书根运行命令；不要依赖 Git 标签。需要 Rust 2021 工具链和网络已缓存或可用的 Cargo 依赖。示例是确定性的离线适配器：它从发送给它的最新完整工具结果拼接答案，不代表真实模型能力，也不会现场读取 fixture 中路径为 `a`、`b` 的文件。

## 先准备共享案例

<a id="context-inputs"></a>

从书根复制公开案例到临时文件。这样可以改自己的输入，同时保留原始 fixture：

```bash
export REIN_CH07_CASE="$(mktemp -d)/ch07-context.json"
cp fixtures/cases/ch07-context.json "$REIN_CH07_CASE"
cargo run --quiet --manifest-path rust/Cargo.toml --example ch07_context -- "$REIN_CH07_CASE"
```

案例文件包含 `unit` 和多个 `cases`。每个 case 给出 `rules`、`goal`、完整 `history`、`budget` 和 `managed`。`history` 中的 assistant tool call 与 tool result 已经是输入事实；程序不会因为看到 `path: "a"` 就去现场打开文件。离线适配器检查它真正收到的消息，找到最新完整工具组的结果，再按声明 call 顺序用换行拼成答案。

输出最外层是 `unit: "estimated-bytes-v1"` 和 `cases`。其中 `unmanaged-overflow` 仍送出全部历史，适配器发现发送量超过 300 后返回 `model_error`；`managed-window` 在相同输入和预算下裁掉最旧组，保留规则、目标和最新工具组，得到 `final_answer`。`required-overflow` 的规则和目标本身放不下，因而没有模型请求。`multi-tool-boundary` 的旧工具组整体移除，最新组中的两个结果一起保留；`invalid-orphan` 与 `invalid-missing` 在发模型前以 `invalid_context_history` 结束。`unicode-content` 用中文和 emoji 检查 UTF-8 估算。

## 估算单位不是 token

<a id="budget-estimate"></a>

`estimated-bytes-v1` 是本地可复算的教学单位。它使用字符串的 UTF-8 字节长度，但把 JSON 数字固定估作 8；它不是 JSON 在线字节数，也不是服务 token。消息估算的实际函数是：

```rust
fn estimated_message(message: &Message) -> usize {
    8 + message.role.as_bytes().len()
        + message.content.as_bytes().len()
        + message.tool_call_id.as_ref().map_or(0, |id| id.as_bytes().len())
        + message.tool_calls.iter().map(|call| {
            8 + call.id.as_bytes().len()
                + call.name.as_bytes().len()
                + estimated_json(&call.arguments)
        }).sum::<usize>()
}
pub fn estimated_units(messages: &[Message]) -> usize {
    messages.iter().map(estimated_message).sum()
}
```

`estimated_json` 对 null、布尔、数字、字符串、数组和对象递归计数，并为分隔符加固定项。上下文事件的 `beforeUnits` 与 `afterUnits` 还包括注入的 system 规则，但不包括工具 schema、HTTP 包络或服务端实际计费。读者可以用案例的 `unit`、消息文本和规则复算结果，却不能把它换算成某个模型的 token 余量。

## 完整历史与发送副本

<a id="atomic-history"></a>

Rust 用拥有型 `Vec<Message>` 保存审计历史。`ContextConfig` 的 `history` 先复制，再追加当前 goal；每轮 `prepare_context` 从这份完整历史重新分组。一个有 tool call 的 assistant 消息和它后面全部对应的 tool result 是一个组，组 ID 按完整历史起点命名为 `g0`、`g1`……多调用组不能拆开。规则另生成 system 消息，不会被旧历史覆盖。

```rust
let context = options.context.clone();
let history_len = context.as_ref().map(|c| c.history.len()).unwrap_or(0);
let mut messages = context.as_ref().map(|c| c.history.clone()).unwrap_or_default();
messages.push(Message { role: "user".into(), content: prompt.into(), tool_call_id: None, tool_calls: vec![] });
```

`prepare_context` 只返回本轮发送的 `Vec<Message>`，然后将同一独立副本放进 `ModelRequested` 并传给 adapter；`LoopResult.messages` 仍是没有裁剪的完整审计历史。Rust 的 clone 和所有权让发送副本的修改不会回写审计数组。`Option` 表示 context 配置可能不存在，`Result` 则把非法历史和预算拒绝变成必须处理的路径。

## managed 与 unmanaged 的对照

<a id="managed-run"></a>

```bash
cargo run --quiet --manifest-path rust/Cargo.toml --example ch07_context -- "$REIN_CH07_CASE"
```

`managed: false` 不是关闭校验，而是只保留完整历史并记录 `context_prepared`；它不裁剪、不提前预算拒绝，所以离线 adapter 仍会因超过 300 返回 `model_error`。`managed: true` 先验证历史，计算必要组，再从最旧的非必要组开始整体删除，直到发送量不超过预算。当前目标组和最新工具组始终必要；它们本身超过预算时直接 `context_budget_exhausted`，请求数为 0。

运行结果中的 `sentMessages` 记录真正进入 adapter 的消息二维数组；`events` 里的 `context_prepared` 记录 `beforeUnits`、`afterUnits`、`requiredUnits`、`keptGroups` 和 `removedGroups`。这能检验管理发生在 loop 内，而不是只测一个未被调用的裁剪函数。

## 源码中的顺序和失败边界

`run_agent_loop_with_options` 先验证 `ContextConfig.budget` 和历史结构；非法角色、孤立 result、缺失 result、重复 call ID 或不相邻 result 都在第一次模型请求前返回 `invalid_context_history`。随后 `prepare_context` 计算规则、全部组与必要组：

```rust
let required_units = groups.iter()
    .filter(|group| required.contains(&group.id))
    .flat_map(|group| messages[group.start..group.end].iter())
    .map(estimated_message).sum::<usize>() + rules_units;
if required_units > config.budget {
    return Err(StopReason::ContextBudgetExhausted);
}
```

上面是实际判断核心；真实实现会在返回错误前写入完整的 `ContextRejected` 事件，事件字段包括 `turn`、`unit`、`mode`、`budget`、`beforeUnits` 和 `requiredUnits`。通过后才删除非必要旧组，并重新按原顺序构造发送数组。`context_rejected` 与最终 `stopped` 分开记录：前者说明哪条上下文规则拒绝了请求，后者说明循环停止原因。非法配置的 errorCode 是 `invalid_context_config`，但停止原因仍是 `invalid_context_history`。

Rust 的 `match`、`Option` 和 `Result` 提供编译期和控制流上的帮助，不能替代 JSON 解码、有限数字检查或历史关联检查。`serde` 的 `toolCallId` 映射只解决字段名，不证明结果属于正确的 assistant call。

## 失败实验

<a id="context-failure"></a>

为了只观察失败类型，可以在输出中筛选三个 case：

```bash
cargo run --quiet --manifest-path rust/Cargo.toml --example ch07_context -- "$REIN_CH07_CASE" > /tmp/rein-ch07-rust.json
node -e 'const x=require("/tmp/rein-ch07-rust.json"); for(const c of x.cases) if(c.result.reason!=="final_answer") console.log(c.id,c.result.reason,c.requests)'
```

预期 `unmanaged-overflow` 是 `model_error/1`，`required-overflow` 是 `context_budget_exhausted/0`，两个 invalid case 是 `invalid_context_history/0`。不要因为所有 CLI 命令退出 0 就认为这些业务 case 成功；必须读取 JSON 中的 `reason`、`requests` 和发送消息。

## 练习

<a id="practice-07-1"></a>

### 练习 07-1：改变最新事实

复制 case 文件后，把 `最新事实 A` 改为 `最新事实 A（已更正）`，保留 `managed-window` 的预算和 history 结构，再运行：

```bash
cargo run --quiet --manifest-path rust/Cargo.toml --example ch07_context -- "$REIN_CH07_CASE"
```

答案应随最新 tool content 变化；检查 `sentMessages` 中仍有完整最新工具组，且审计 `result.messages` 没有被物理裁剪。不要只改 `expected.answer`，因为 adapter 不读取 expected。

<a id="practice-07-2"></a>

### 练习 07-2：预算边界 239/238

在临时副本中把 managed case 的 `budget` 改为 239，再改为 238。实际快照数据下，239 应允许必要上下文并发出 1 次模型请求；238 应为 `context_budget_exhausted` 且请求数 0。观察 `requiredUnits` 与 `budget`，不要删除规则或最新工具组来“挤出”答案。

<a id="practice-07-3"></a>

### 练习 07-3：删除一个对应结果

在临时副本的 managed history 中删除一个 tool result，保留其 assistant call，再运行相同命令。预期 `invalid_context_history`、请求数 0，并在 `context_rejected` 的 error 中看到短码。修复配对后再运行，才能回到正常管理路径；这一步检查的是历史完整性，不是工具文件是否存在。

本章的 Rust 入口只覆盖当前快照的上下文管理；后续演进可能增加策略和停止原因，但不会改变本节对完整历史、发送副本和预算边界的区分。
