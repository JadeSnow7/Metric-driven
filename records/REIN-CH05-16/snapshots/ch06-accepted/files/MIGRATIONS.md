# Migrations

## ch05 loop contract

第05章新增可观察循环事件：`model_requested` 保存完整 `messages` 与 `tools`，`model_received` 保存模型消息与 `toolCallIds`，`tool_result` 保存原始 `call`、`toolCallId` 与结果；终态仍使用小写 snake_case 值。Rust 内部字段由 serde 映射为共享 camelCase wire。旧的 `runAgentLoop`/`run_agent_loop` 入口保持兼容。

工具 schema 现在明确声明 `read_file.path` 与 `search_files.needle` 为必需字符串。Rust 回放耗尽返回 `replay_exhausted`，不会 panic。真实入口必须显式 `--live`，最多四轮且不自动重试。

当前仓库状态：第05章提供 TypeScript 与 Rust 的 typed loop、只读工具路由、离线回放与受限真实入口；Rust 的旧 `rein::run_agent_loop` 仍作为 OpenAI HTTP 兼容包装，核心实现位于 `rein::loop`。工程决策记录见 [DECISIONS.md](DECISIONS.md)。
