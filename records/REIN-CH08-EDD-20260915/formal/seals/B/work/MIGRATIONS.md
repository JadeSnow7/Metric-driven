# Migrations

## ch05 loop contract（历史基线）

第05章新增可观察循环事件：`model_requested` 保存完整 `messages` 与 `tools`，`model_received` 保存模型消息与 `toolCallIds`，`tool_result` 保存原始 `call`、`toolCallId` 与结果；终态仍使用小写 snake_case 值。Rust 内部字段由 serde 映射为共享 camelCase wire。旧的 `runAgentLoop`/`run_agent_loop` 入口保持兼容。

工具 schema 现在明确声明 `read_file.path` 与 `search_files.needle` 为必需字符串。Rust 回放耗尽返回 `replay_exhausted`，不会 panic。真实入口必须显式 `--live`，最多四轮且不自动重试。

该历史基线：第05章的 TypeScript 与 Rust typed loop、只读工具路由、离线回放与受限真实入口处于本地实现核验中；Rust 的旧 `rein::run_agent_loop` 仍作为 OpenAI HTTP 兼容包装，核心实现位于 `rein::loop`。工程决策记录见 [DECISIONS.md](DECISIONS.md)。
## 混合路线后续任务（计划）

第 06 章混合运行时已有本地实现与测试材料，离线实验已核验：Rust core → Node `read_file` → 第二轮离线 fixture model；最终全站检查仍待维护者统一放行。第 13 章 journal 是后续交付物，不是当前流程的前置自循环；第 11 章的权限代理与隔离能力仍需按实际权限边界做独立验收。

以下项目描述交付物、依赖和验收条件；它们是路线计划，不表示当前已经实现。

| 任务 | 交付物 | 依赖 | 验收 |
| --- | --- | --- | --- |
| SDK 提炼 | 从实际调用抽出 TS SDK 接口 | core 调用稳定 | SDK 由真实调用驱动并保留 IDs/evidence |
| 08 context | 同一任务、同一预算下的四种上下文策略材料 | core 状态与消息快照 | 四策略输出可复算，并分别记录估算 token 与真实 token 的边界 |
| 09 validators | evidence binding 验证器 | 08 context | 按 task/call/targetVersion/rule 绑定证据；验证通过不等同任务成功 |
| 10 repair + unknown | 失败反馈、未知结果处理 | validators、断连结果 | 未知结果不自动重放，修复路径有明确终态 |
| 11 boundary | 参数、路径和信任边界；若需限制进程副作用，交付实际代理或隔离机制 | host 协议与工具权限 | 未授权路径和进程边界有真实失败证据；不把本轮 trusted Node 当作 sandbox |
| 12 approval baseline | patch approval 基线 | boundary、evidence | 补丁 hash 与文件基线绑定；基线变化使旧批准失效，拒绝状态不写入 |
| 13 persist recovery | 持久化、恢复和 unknown | approval、事件合同 | 交付 journal 后验证崩溃恢复不重放未知调用 |
| 14 bounded delegation | 受限委派合同 | recovery、权限边界 | 权限与预算不扩大；依赖满足、部分失败、取消传播和冲突均可验证 |
| 15 MCP/hooks | MCP stdio 正式协议与 hooks 兼容 | delegation、协议稳定 | 连接生命周期、取消和证据字段通过兼容测试 |
| 16 doc maintainer | 文档维护者流程与 12 个固定案例（命令过期、参数变化、相对链接失效、无须修改各 3 个） | 全部已实现能力 | 12 个案例均有可运行命令、结果和边界说明 |
