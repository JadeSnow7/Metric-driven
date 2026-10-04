已完成第 05 章交付。

改动包括：

- TS：新增 `runAgentLoop`、事件/状态/停止原因、工具定义及测试。
- Rust：新增对应循环 API、事件模型、离线示例与测试。
- 新增单文件读取及多文件搜索后读取演示，支持 `single` 参数。
- 完成 `docs/chapters/05.md` 与 `docs/chapters/05-rust.md`，包含机制、失败路径、运行命令和练习。
- 增加 `ch05:offline` package script。

验证结果：

- TS 类型检查通过。
- TS 本章及前置专项测试：10/10 通过。
- TS 排除本地监听测试后：67/67 通过。
- Rust `cargo fmt --check` 通过。
- Rust 本章循环测试通过。
- 两版离线演示均成功输出真实搜索结果、文件内容、工具 ID 配对及 `final_answer`。

限制：

- 完整 TS/Rust 测试中涉及本地 TCP 监听的既有测试受沙箱 `listen EPERM` 限制失败，非本章循环逻辑问题。
- 未提交、推送或调用真实模型服务。