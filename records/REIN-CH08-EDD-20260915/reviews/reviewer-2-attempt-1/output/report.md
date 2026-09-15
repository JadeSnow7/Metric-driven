# ch08 独立产品评审

评审顺序：Slate → Larch → Quartz。评审依据为冻结 `product-spec.md`、产品自身源码/正文/fixtures、claims，以及冻结 evaluator（SHA256 `6ed1a9d09fd40871b8e4e0bfed7cb2d2f64a4a3eb9f5ff762bb0566cda6fe86b`）。没有读取其他评审者、正式实现过程或组别映射。原始命令记录均在各产品的 `output/*/checks/*/run.json`，其中包含 argv、cwd、时间、退出码、超时、输出和源码 hash。

## 结论矩阵

| 产物 | 完整性 | 功能/回归 | 架构 | 正文复现 |
|---|---|---|---|---|
| Slate | FAIL | FAIL | FAIL | UNVERIFIED |
| Larch | FAIL | FAIL | FAIL | UNVERIFIED |
| Quartz | FAIL | FAIL | FAIL | UNVERIFIED |

## Slate

### 完整性：FAIL

存在完整中文正文、Rust `context_methods`、`rust/examples/ch08_context.rs`、独立示例目录、fixtures、根 compare/verify 脚本和 8 个锚点（正文 `docs/chapters/08.md:1-69`；入口 `rust/examples/ch08_context.rs:1-...`；导航 `docs/toc.md:114-116`）。typecheck、独立示例、docs build 和 05/06/07 compare 均有成功原始记录：`output/Slate/checks/typecheck/run.json`、`example-final/run.json`、`docs-build-final/run.json`、`ch05-final/run.json`、`ch06-final/run.json`、`ch07-final/run.json`。

冻结 evaluator 有效运行失败于 `CHECK_CLAIM_GROUNDED`：`output/Slate/checks/evaluator-final/run.json`。另有因预创建 evaluator 输出目录导致的工具拒绝记录，不能计为产品失败：`output/Slate/checks/evaluator/run.json`、`evaluator-2/run.json`、`evaluator-rerun-1/run.json`。

### 功能/回归：FAIL

ch08 默认 16 行和零预算命令退出 0：`ch08-compare-final/run.json`、`ch08-zero-final/run.json`；verify 退出 0：`ch08-verify-final/run.json`。Rust `check` 和 fmt 通过：`cargo-check/run.json`、`fmt/run.json`。Rust 全测退出 101，TS 全测为 95 passed/5 failed；失败原因是当前沙箱 `listen EPERM`，应视为环境阻塞而非产品失败：`cargo-test-2/run.json`、`ts-test/run.json`。hybrid normal 通过，cancel/crash 均真实退出非零并返回空 answer 事件：`hybrid-normal-final/run.json`、`hybrid-cancel-final/run.json`、`hybrid-crash-final/run.json`。

源码显示 `task-04` 的 quality 被直接设为 `Some(1.0)`（`rust/src/rein/context_methods.rs:364-366`），不符合“未知题 claims 为空且 evidence insufficient、质量按实际必需事实计算”的合同。窗口裁剪只删除 tool message，未证明按最近完整段落 suffix（同文件 `342-349`）。

### 架构：FAIL

Rust core 确实调用 `read_file` 并从 StdioExecutor 取 records（`rust/src/rein/context_methods.rs:305-319`），Node 领域工具边界和真实 callRecords 有证据；但 evaluator 的 claim-grounded 失败、硬编码未知题质量，以及完整错误/异常矩阵未全部通过，不能判为架构满足规格。正文关于证据驱动的声明（`docs/chapters/08.md:23-27`）与源码质量计算不一致。

### 正文复现：UNVERIFIED

正文的入口、零预算命令和三项练习位于 `docs/chapters/08.md:7-67`，包含绝对路径/参数/预期字段；静态核对通过。已实际跟做独立入口，未逐项执行正文三个练习的数据副本、事实改写、检索词改写及根 docs link checker；因此不把它们标为通过。浏览器 GUI 验收未执行，仅做静态导航核对。

## Larch

### 完整性：FAIL

正文、Rust 模块、根脚本、fixtures 和 8 个锚点存在（正文 `docs/chapters/08.md:1-66`；Rust `rust/src/rein/context_methods.rs:1-295`；导航 `docs/toc.md:114-116`）。但独立示例实际运行失败：`output/Larch/checks/example-2/run.json`，README 声明的真实入口不可加载；不能以目录/文本存在替代入口可运行。

冻结 evaluator 有效运行失败于 `CHECK_ESTIMATE`：`output/Larch/checks/evaluator-1/run.json`。

### 功能/回归：FAIL

ch08 compare、零预算、verify、05/06/07 compare、typecheck、fmt、cargo check、docs build 均退出 0：`output/Larch/checks/ch08-compare-1/run.json`、`ch08-zero-1/run.json`、`verify-2/run.json`、`ch05-2/run.json`、`ch06-2/run.json`、`ch07-2/run.json`、`typecheck-1/run.json`、`fmt-2/run.json`、`check-2/run.json`、`build-2/run.json`。Rust 全测退出 101：`test-2/run.json`；网络监听失败部分属于环境阻塞。

源码的错误路径在读取失败时 `break`，随后仍构造 `status: completed`、`answer: Some`、`model_calls: 1`（`rust/src/rein/context_methods.rs:240-271`），违反缺文件/宿主错误必须是 error 行且不得派发回答器。其 claims 已自报 window 和错误路径未完善，与实际缺陷吻合。

### 架构：FAIL

Larch 的 summary 确实从真实输出提取事实行并加入 `[来源:...]`（`rust/src/rein/context_methods.rs:220-239`），但成功错误折叠和 evaluator 的 estimate 失败表明预算/错误终态契约不可靠。独立入口失败还说明公开 Rust→Node 组合路径未形成可复现产品边界。

### 正文复现：UNVERIFIED

正文包含入口、绝对路径示例、三练习和所有 8 锚点（`docs/chapters/08.md:5-66`）；已运行根 compare/verify/zero，但未实际执行三份独立数据副本练习和正文链接检查。GUI 未执行，导航仅静态核对。

## Quartz

### 完整性：FAIL

正文、Rust 模块、独立示例目录、根脚本、README/MIGRATIONS 和 8 个锚点均存在（正文 `docs/chapters/08.md:1-73`；导航 `docs/toc.md:114-116`）。独立示例实际运行失败：`output/Quartz/checks/example-1/run.json`。冻结 evaluator 有效运行失败于 `CHECK_ESTIMATE`：`output/Quartz/checks/evaluator-1/run.json`。

### 功能/回归：FAIL

ch08 compare/zero/verify、05/06/07 compare、typecheck、fmt、cargo check、docs build 均退出 0：`output/Quartz/checks/compare-2/run.json`、`zero-2/run.json`、`verify-2/run.json`、`ch05-2/run.json`、`ch06-2/run.json`、`ch07-2/run.json`、`typecheck-1/run.json`、`fmt-2/run.json`、`check-1/run.json`、`build-1/run.json`。Rust 全测和网络异常路径没有完整成功证据；hybrid normal/cancel/crash 的独立 run 目录因磁盘/批次中断未全部留下有效记录，故为未验证，不推断通过。

源码错误终态结构虽返回 `status: error`（`rust/src/rein/context_methods.rs:282-300`），但窗口裁剪实现是按 assistant/tool 对删除（`315-325`），不是按最近完整段落 suffix；质量和 estimate 的冻结 evaluator 仍失败。正文声称严格裁剪（`docs/chapters/08.md:25`）与实现不一致。

### 架构：FAIL

Quartz 的 Rust→Node 边界和真实 executor records 在源码中存在，摘要也保留来源前缀；但 evaluator estimate 失败、窗口语义不符、独立入口不可运行，意味着 Rust authority/预算/公开混合入口尚未满足共同规格。README 中“已完成离线实验”的状态不能抵消实际失败记录。

### 正文复现：UNVERIFIED

正文包含 8 锚点和三项练习（`docs/chapters/08.md:5-73`），入口/zero/compare 已执行；三项练习命令含副本和改写步骤但尚未逐项按读者起点实际执行，docs link checker 与浏览器 GUI 也未执行。静态导航范围已核对，不能冒充完整站点验收。

## 共同限制与证据边界

- 每份产物的 run_check 过程均显式绑定其自己的 `CARGO_TARGET_DIR`、`CARGO_INCREMENTAL=0`、dev/test debug=0；已完成产物的 target 在切换产物前清理。
- 由于沙箱禁止 localhost `listen`，TS/Rust 网络测试未能通过；没有收到可用的 `require_escalated` 重跑权限，因此按环境阻塞记录，未称产品测试失败。
- 没有修改任何 products 源码或冻结 fixtures，没有提交、推送或部署。
- 未提供任何精确总分；本报告只给四轴状态和实际证据目录。
