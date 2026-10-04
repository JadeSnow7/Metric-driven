已完成第08章本地交付，未提交、推送或部署。

交付内容：

- Rust `context_methods` 四策略与真实 Rust→Node 文件读取。
- `ch08:compare`、`ch08:verify` 脚本及 package scripts。
- 独立示例 `examples/ch08-context-methods/`。
- 中文正文、三项练习、导航、README/MIGRATIONS 状态同步。
- ch08 Rust 专项测试。
- 原始证据：[records/ch08/evidence]( /private/tmp/rein-ch08-formal-20260915/C/book/records/ch08/evidence )

验证结果：

- Rust fmt/check：通过。
- ch08 Rust tests：2 passed。
- TypeScript typecheck：通过。
- ch08 默认比较：16 行通过。
- ch08 verify、独立示例、零预算、真实 Node 宿主、文档构建：通过。
- 全量 Rust/TS 测试：受沙箱禁止 localhost `listen EPERM` 影响，5 个 Rust 与5 个 TS 网络测试失败。
- 第05/06/07比较与完整异常覆盖未全部重新执行。

未完成项：全量测试中的 localhost 监听失败属于当前环境限制；第09章仍按要求保持未实现。