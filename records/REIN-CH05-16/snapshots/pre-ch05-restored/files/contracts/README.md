# Shared contracts

`ts/` 与 `rust/` 在重叠能力范围内共享的合同：消息、工具调用、工具结果的形状，以及兼容边界与版本。

前置版本已定义并由两条 track 读取同一份 `fixtures/cases/prerequisites.json` 验收数据；它只提供模型 turn、工具调用和只读工具路由，不包含 Loop 控制。

按本任务生成的可恢复快照及合同变化记录定位合同版本，变化记录在 [MIGRATIONS.md](../MIGRATIONS.md)。
# ch05 前置合同

TypeScript 的 `ts/src/rein/contracts.ts` 与 Rust 的 `rust/src/rein/mod.rs` 共享四个可序列化概念：`Message` 表示对话消息，`ToolCall` 表示模型请求的工具动作，`ToolResult` 表示带 `ok` 与结构化错误的工具结果，`Turn` 把一轮消息、调用和结果成组保存。wire JSON 使用 camelCase（如 `toolCallId`、`toolCalls`、`toolResults`、`inputSchema`）；Rust 内部字段仍可使用 snake_case 并由 serde 映射。可选字段在 Rust 为 `None` 时省略，输入仍兼容缺失或 `null`，与 TS optional 对齐；`canonical_sample` 是两端共享的 canonical JSON 样例。`read_file` 与 `search_files` 只接受 workspace 内路径或关键词；工具错误码包括 `path_escape`、`path_invalid`、`read_failed`、`search_failed`、`workspace_invalid`、`arguments_invalid` 和 `unknown_tool`。TS 以 `ToolResult` 返回，Rust 也以 `ToolResult` 返回；解析与传输层错误则由 TS 抛出 `Error`、Rust 返回 `Result`。这不是对所有底层路径错误细节的隐藏承诺。

OpenAI 适配器使用现有配置和 transport，单次非流式调用，不自动重试；它序列化完整 messages/tools，并保留多个 `tool_calls` 及其 JSON arguments。Anthropic 前置适配器转换 system、text、tool_use、tool_result；回放输入是 Anthropic wire JSON，不是 `ModelTurn` 对象，按输入顺序消费，用尽后 TS 抛出 `Error('replay exhausted')`，Rust 返回 `code='replay_exhausted'`。Rust 的具体 HTTP 入口是 `rein::openai_complete`，通过 `rein::OpenAiHttp`（生产实现为 `ReqwestHttp`）发送请求；TS 入口是 `createOpenAIAdapter`。例如模型返回 `{"tool_calls":[{"id":"call-1","name":"read_file","arguments":{"path":"README.md"}}]}`，工具执行后追加 `{"role":"tool","toolCallId":"call-1","content":"..."}`，下一轮仍携带同一 id。这些 API 是 ch05 Agent Loop 的输入，不包含循环控制。
