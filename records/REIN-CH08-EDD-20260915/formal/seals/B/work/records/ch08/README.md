# ch08 原始验收记录

本目录保存本次实际命令的 stdout、stderr 与退出码文件。`*.exit` 是对应命令的真实退出码；动态 `child_pid`、cwd、argv 和耗时由 `ch08-compare.stdout.json` 中的 `callRecords`/行字段保留。当前工作区受限环境禁止本地 TCP listen，因此既有 TS transport 与 Rust HTTP 测试失败，详见各测试 stderr；这不是 ch08 端到端失败。

已保存：TypeScript typecheck/测试、Rust ch08 集成测试、ch08 比较/验证、独立示例、文档构建/链接及 05/06/07 比较。
