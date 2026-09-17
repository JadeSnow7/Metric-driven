已完成 production 副本双语言前置工程，未 commit/tag/push，未触碰正文或外部评估器。

主要完成：

- Rust 增加真实 `ReqwestHttp`，支持 base URL/API key/model、timeout、无应用级重试。
- TS/Rust 完整处理 OpenAI/Anthropic text、system、tool_use、tool_result。
- 增加严格畸形响应校验、统一 replay、真实工具 dispatch 和调用 ID 绑定。
- 加强 workspace canonicalize、目录拒绝、symlink escape、防跟随 symlink 的稳定搜索。
- 两端测试均读取共享 fixture，并覆盖多工具、多轮工具结果、坏参数、未知工具、非法路径、symlink escape、replay 耗尽。
- 同步 [contracts/README.md](</Users/huaodong/Documents/evidence-driven-development/records/REIN-CH05-16/work/production/contracts/README.md>)。

验证通过：

- `npm run typecheck`
- `npm test`：7 个文件，70 tests passed
- `cargo fmt --manifest-path rust/Cargo.toml -- --check`
- `cargo check --locked --offline`
- `cargo test --locked --offline`：9 个 unit + 4 个 prerequisites passed
- Rust loopback 测试捕获两次具体 Reqwest 请求，并验证第二轮 assistant `tool_calls` 与两个 `tool_call_id`

完整 stdout/stderr、exit code、测试清单和 SHA-256 已保存至：

[RESULT.md](</Users/huaodong/Documents/evidence-driven-development/records/REIN-CH05-16/evidence/prerequisites-v3/RESULT.md)

未验证真实外网 OpenAI 请求；本任务仅验证本地 loopback HTTP，不读取密钥。