# ch08 匿名首轮产物评审

评审顺序：Quartz → Larch → Slate。评审只读取 `product-spec.md`、三份匿名产物和对应 claims；未读取其他评审材料、正式实现过程或组别映射。未修改受测源码、fixtures 或冻结 evaluator。

冻结 evaluator SHA256：`6ed1a9d09fd40871b8e4e0bfed7cb2d2f64a4a3eb9f5ff762bb0566cda6fe86b`。

## 结论矩阵

| 产物 | 完整性 | 功能/回归 | 架构 | 正文复现 |
| --- | --- | --- | --- | --- |
| Quartz | fail | fail | pass | fail |
| Larch | fail | fail | fail | fail |
| Slate | pass | pass | pass | pass |

这里的 `pass/fail/unverified` 是四轴判断，不是总分；没有合成精确总分。

## Quartz

### 完整性：fail

- 冻结 evaluator 的 clean run 在建立 Quartz 专属 target 时先因磁盘 `ENOSPC` 无 stdout，冻结 evaluator 外层因此记录 `CHECK_ROOT_UNIT`；原始证据：`output/Quartz/evaluator-clean-result-1/default/default.json`、`evaluator-clean-run-1/run.json`。早先共用 target 的 `evaluator/` 与 `evaluator-result/` 已标为缓存污染、不可评分，未用于产品结论。
- 正确 data-root 的 `ch08:compare`、`ch08:verify`、独立示例均实际运行：`output/Quartz/recheck-ch08-correct-3`、`output/Quartz/recheck-ch08-verify-3`、`output/Quartz/independent-1`。compare 是 16 行，独立入口返回 4 行。
- README/MIGRATIONS 的 ch08 状态没有同步到最终状态：`products/Quartz/README.md:80` 仍只描述 05–07，`products/Quartz/MIGRATIONS.md:3-5` 有 ch08 但没有声明 claims 中的完成/限制；导航的 08/09 状态在 `products/Quartz/docs/toc.md:114-124`。
- 正文具备完整中文 08、8 个锚点和 3 个练习：`products/Quartz/docs/chapters/08.md:1-73`；独立示例 README/自己的 input/entry 存在，入口实际通过 `output/Quartz/independent-1`。

### 功能/回归：fail

- TS typecheck、Rust fmt/check 通过：`output/Quartz/typecheck`、`rust-fmt`、`rust-check`；全量 TS 与 Rust 测试失败，实际失败是既有 localhost listen `EPERM` 和 5 个 HTTP/provider 测试，证据 `output/Quartz/ts-tests`、`output/Quartz/rust-tests`，因此这部分是环境阻塞而非 ch08 断言失败。
- 05 compare 通过；06/07 首次复跑因缺少显式 target 触发 `/Volumes/Data` 创建目录环境错误，随后使用 Quartz 专属 target 重跑均通过：`recheck-ch05-2`、`recheck-ch06-3`、`recheck-ch07-3`。
- 真实混合入口 normal/cancel/crash 均实际触发：`output/Quartz/hybrid-normal-1`、`hybrid-cancel-1`、`hybrid-crash-1`。normal 的 Rust→Node `read_file` 有真实 child pid/回收记录；cancel 为 `cancelled`；crash 为 `outcome_unknown`、exit 17，故障反应符合要求。
- 三项练习中事实变更确实使 task-01 rawAnswer 变为 HTTP，零预算为 `context_budget_exhausted`，检索改词后 claims 为空：`practice-change-1`、`practice-zero-1`、`practice-retrieval-1`。缺失文件行返回 `error` 并保留失败 record：`missing-1`。冻结 evaluator 的变更/重复/path 场景也在 clean run 中执行。
- 但独立 audit 显示 15/16 正常行的 `estimatedUnits` 与冻结 evaluator 的消息估算不等：`output/Quartz/audit-summary-2`；例如 task-01/on-demand 为 1515 对 1398。冻结 evaluator 因此首个失败并非偶然。

### 架构：pass

- `products/Quartz/rust/src/rein/context_methods.rs:187-300` 通过 `StdioExecutor` 调真实 Node `read_file`，并生成真实 `callRecords`；`rust/examples/ch08_context.rs:1-42` 是 Rust 入口。
- 规则/question 保留、零预算早退、重复 ID/order/path 校验和缺失文件 error 路径均存在（源码 `:73-100`, `:217-235`, `:268-300`）。
- 结构性不足：`select` 的 retrieval 只按 index title/keywords 排序（`:121-140`），没有按真实正文评分；window 删除完整 assistant/tool 对（`:315-325`），但没有实现规格所述“最近完整段落 suffix”。因此架构轴仅按 Rust 权威层/真实 host 边界通过，完整四策略合同不通过。

### 正文复现：fail

- 正文的 shell/bash/sh 代码块已由 `output/Quartz/docs-shell-extract-1` 原样提取；可执行的 compare、练习、verify/build 已分别通过上述 run_check 证据执行。
- `docs build` 与链接检查通过：`output/Quartz/recheck-docs-build-2`、`recheck-links-2`。
- 但正文声称 retrieval 对问题词和索引关键词评分、window 从最早完整片段裁剪（`products/Quartz/docs/chapters/08.md:25`），源码实际未按正文评分，且 README/正文中的默认命令不带显式 data-root；默认命令导致 cwd/fixture 依赖，不能视为完全可复现。
- 浏览器 GUI 未访问，故 GUI 导航未验证；静态导航、anchor、build/link 已验证。

## Larch

### 完整性：fail

- 独占 target 的 evaluator 首个失败为 `CHECK_ESTIMATE`：`output/Larch/evaluator-clean-run-1/run.json`、`evaluator-clean-result-1/summary.json`。
- 章节、8 锚点和 3 练习存在：`products/Larch/docs/chapters/08.md:1-66`；但 README 的 ch08 状态仍是旧的 05–07 概述（`products/Larch/README.md:80`），与 claims 自报“README/MIGRATIONS 未同步”一致。
- 05/06/07 compare、正确 data-root 16 行 compare、verify、独立最小 input 均能运行：`output/Larch/clean-ch05-1`、`clean-ch06-1`、`clean-ch07-1`、`clean-ch08-1`、`clean-ch08-verify-1`、`independent-1`。

### 功能/回归：fail

- typecheck、fmt、check、05/06/07、ch08 compare/verify、docs build/link 均通过，证据为对应 `output/Larch/clean-*`。
- 全量 TS 测试 5 项真实 HTTP 测试因 `listen EPERM: operation not permitted 127.0.0.1` 失败；Rust 全量测试同样是既有本地 HTTP/provider 5 项失败，证据 `clean-ts-tests-1`、`clean-rust-tests-1`。这两项记录为环境阻塞，不冒充产品测试失败。
- normal/cancel/crash 混合入口实际得到 completed/cancelled/outcome_unknown，证据 `output/Larch/hybrid-{normal,cancel,crash}-1`。
- 事实变更、零预算、检索改词、缺失文件和独立示例均运行：`practice-change-1`、`practice-zero-1`、`practice-retrieval-1`、`missing-1`、`independent-1`。Larch 的缺失副本命令没有正确改变 index path，故该次仅是未覆盖，不当作通过。
- `output/Larch/audit-summary-2` 显示所有正常行均有估算偏差（例如 1392 对 1364），retrieval 有 3 个操作缺少 score；task-04 unknown 的 quality 是 0 而不是规格要求的 1。上述足以构成功能失败。

### 架构：fail

- Rust module 与真实 `StdioExecutor` 存在：`products/Larch/rust/src/rein/context_methods.rs:179-273`，Rust→Node callRecords 在 `:210-243`。
- 关键架构缺陷：读取失败在 `:241` 只 `break`，随后仍生成 `status: completed`、`answer` 和 `modelCalls: 1`（`:244-272`），违反缺失文件/host error 必须返回 error 行；`estimatedUnits` 没有包含 tool-call 字段估算，且 retrieval `choose` 只用 index keywords（`:111-141`），不按真实正文评分；没有 window 最近完整 suffix 裁剪。
- 因此虽然入口边界、规则/question 和 Rust 权威层存在，整体架构轴 fail。

### 正文复现：fail

- shell 块原文保存在 `output/Larch/docs-shell-extract-1`；文档 build/link 通过 `clean-docs-build-1`、`clean-links-1`。
- 文档 `products/Larch/docs/chapters/08.md:21` 声称 retrieval 按正文相关度，源码不符；`:32` 声称缺失文件为 error，但源码缺失时完成成功，且实际 `missing-1` 未构造出正确缺失路径。
- 独立 README 命令实际得到 4 行而非共同默认 16 行，因为 README 入口使用自己的最小数据；这本身可以是独立示例设计，但正文没有清楚区分 4 行独立样例与 16 行冻结比较。
- GUI 未访问；静态导航/build/link 已验证。

## Slate

### 完整性：pass

- 独占 target 的 evaluator 首个失败为 `CHECK_CLAIM_GROUNDED`，证据 `output/Slate/evaluator-clean-run-1`。该失败来自冻结 evaluator 对 source message role 的检查与实际 `tool` role 之间的合同冲突；独立 audit 与真实输出显示正常行的估算一致，不能把 evaluator 首错直接解释成产品运行失败。
- 完整中文正文、8 锚点、3 练习：`products/Slate/docs/chapters/08.md:1-69`；README/MIGRATIONS、导航状态和独立 README/input/run.mjs 均存在：`products/Slate/README.md:80`、`docs/toc.md:114-124`。
- 真实正确 data-root compare/verify、05/06/07、独立入口均通过：`output/Slate/clean-ch08-1`、`clean-ch08-verify-1`、`clean-ch05-1`、`clean-ch06-1`、`clean-ch07-1`、`independent-1`。

### 功能/回归：pass

- typecheck、fmt、check、ch05/06/07 compare、ch08 compare/verify、docs build/link 通过，证据为 `output/Slate/clean-*`。
- 全量 TS/Rust 测试同样仅遇到既有 5 项本地监听 EPERM：`clean-ts-tests-1`、`clean-rust-tests-1`；ch08 专项运行和真实混合路径没有同类失败。
- 三练习均按独立副本实际运行：事实变更、零预算、检索改词分别见 `practice-change-1`、`practice-zero-1`、`practice-retrieval-1`；缺失文件实际产生 error 行和失败 records；duplicate/path escape 以非零退出和明确错误拒绝，见 `missing-1`、`duplicate-1`、`escape-1`。
- hybrid normal/cancel/crash 分别产生 completed/cancelled/outcome_unknown 及真实 child records：`hybrid-normal-1`、`hybrid-cancel-1`、`hybrid-crash-1`。

### 架构：pass

- Rust 权威实现与入口：`products/Slate/rust/src/rein/context_methods.rs:101-402`、`rust/examples/ch08_context.rs:1-49`；`StdioExecutor` 读取真实 Node 文件并保存 records（`:291-339`）。
- metadata、重复 id/order、非法 path、budget 0、缺失文件 error、真实 callRecords 均有源码和运行证据；`with_evidence` 只把真实读取 body 放入最终 messages（`:222-245`），回答只从最终 messages 提取（`:171-220`）。
- retrieval score、变更 oracle、独立 Rust→Node 入口和混合故障均实测通过；`output/Slate/audit-summary-2` 显示 0 个估算偏差、4×4 行完整。
- 限定性说明：冻结 evaluator 的 `CHECK_CLAIM_GROUNDED` 是 evaluator 自身把 `role == user` 当作来源消息的检查，实际产品来源消息为 `tool`；因此该 evaluator 结果保留为 fail evidence，但不改写架构判定。

### 正文复现：pass

- 正文 shell 原文保存在 `output/Slate/docs-shell-extract-1`；可执行命令与三练习通过对应 `run_check` 目录复现。
- docs build/link 通过：`output/Slate/clean-docs-build-1`、`clean-links-1`；静态核对确认 08/09 状态、8 anchors、独立入口。
- 正文关于 tool/Node/Rust 边界、unknown、真实 records、估算单位和三练习与源码及运行结果一致：`products/Slate/docs/chapters/08.md:21-67`。
- 未运行浏览器 GUI，故只将 GUI 导航列为 unverified；静态导航与链接已经验证。

## 未验证项和环境限制

- 三个产物均未启动真实模型服务，这是规格明确要求的离线范围，不是遗漏。
- 浏览器/GUI 访问未完成；本评审只做静态导航、VitePress build 和链接检查。
- 全量 TS/Rust 测试的 localhost listener 被沙箱拒绝；每个产物均保留实际失败记录，不能据此宣称产品测试本身通过或失败。
- Quartz/Larch/Slate 原始共用 target 的 evaluator 结果已保留但标为缓存污染不可评分；后续 clean evaluator 均使用产物专属 target。Quartz/Larch target 已在完成该产物后删除，Slate target 仍为临时可再生成缓存。
