已完成第05章交付。

改动包括：

- TypeScript：新增 `runAgentLoop`、事件记录、工具失败反馈、轮次保护、回放适配器。
- Rust：新增 `run_agent_loop`、`LoopAdapter`、事件与停止原因、离线二进制入口。
- 新增 TS/Rust 循环测试与离线演示。
- 完成 `docs/chapters/05.md`、`docs/chapters/05-rust.md`。
- 新增 `ts` 的 `ch05:offline` 脚本。

验证结果：

- TS 类型检查通过。
- TS 第05章测试：4/4 通过。
- Rust 格式检查通过。
- Rust 第05章测试：3/3 通过。
- TS、Rust 离线演示均成功输出真实搜索、读取结果及事件序列。
- 完整 TS/Rust 测试受当前沙箱禁止本地监听端口影响，既有 HTTP transport 测试出现 `listen EPERM`；非本章逻辑失败。