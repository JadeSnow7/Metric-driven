已完成第 08 章本地交付，未提交、推送或部署。

交付内容：

- Rust 四策略核心、真实 Rust→Node `read_file`：`rust/src/rein/context_methods.rs`
- Rust 示例与集成测试
- `ch08:compare` / `ch08:verify`
- 独立示例：`examples/ch08-context-methods/`
- 完整中文正文与导航同步：`docs/chapters/08.md`、`docs/index.md`、`docs/toc.md`
- 原始验证记录：`records/ch08/`

已通过：

- TypeScript typecheck
- ch08 四策略、16 行默认输出
- 零预算行为
- ch08 Rust 集成测试
- 独立示例
- 05/06/07 比较
- 文档构建与链接检查
- Rust fmt/check

失败/限制：

- 全量 TypeScript 与 Rust 测试中既有 HTTP/TCP 测试因当前环境 `listen EPERM` 失败，详见 `records/ch08/*tests*stderr.txt`。
- 未运行真实模型服务，符合合同要求。
- 第 09 章仍保持未实现状态。