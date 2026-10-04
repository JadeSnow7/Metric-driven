# ch08 补查报告

本补查不修改首轮报告、产品源码或冻结 fixtures。所有新增命令证据在 `output/followup/{Slate,Larch,Quartz}/checks/`，正文 shell 原文在 `output/followup/extracted/README.md`。

## 正文练习与入口

- Slate：三项练习实际执行成功。练习一的 `messages`/`rawAnswer` 使用改写后的 `Unix socket`；练习二全部为 `context_budget_exhausted` 且无 operations/model call；练习三实际产生 retrieval 结果，可核对 selectedSources/score。证据：`checks/practice1|2|3/run.json`。README 的真实 `node examples/ch08-context-methods/run.mjs` 通过：`checks/readme/run.json`。
- Larch：练习二、三成功；练习一因磁盘耗尽未能保存 run_check 结果，不能判通过。README 命令先因外层 `$PWD` 展开偏差产生旧失败记录，随后在产品根等价绝对路径下复跑成功：`checks/readme-correct-root/run.json`。此前错误的 `run.mjs` 路径不作为入口证据。链接检查通过（2198 checked、0 failures）。
- Quartz：练习一、二、三均有成功 run_check 记录；README 的真实 `entry.mjs` 通过；链接检查通过（2198 checked、0 failures）。

正文自身问题：Slate 的绝对路径练习一/三需读者先复制资料；Slate budget0 使用 `/绝对路径/...` 占位符。Quartz 练习二/三同样使用占位符，且练习三正文命令未在命令块中包含实际 query 改写步骤。Larch 的 shell 块自包含 `mktemp/cp/sed`，但把结果检查留给读者。

## 混合与故障

Larch normal 通过，cancel/crash 均退出 1 且输出 answer null 与事件；Quartz normal 通过，cancel/crash 均退出 1 且输出 answer null 与事件。Slate 补查阶段因重建 target 后磁盘耗尽，normal/cancel/crash 的 run_check 均退出 101，不能当作产品故障结论；首轮已有 normal 通过、cancel/crash 非零记录。真实 records/pid/reaped 字段保留在各 run JSON 的 stdout 中，未用 passed 字段替代。

链接检查均为真实 `node scripts/check-book-links.mjs`，不是仅检查退出码。

## 元数据与网络补查

路径越界在 Slate 补查中实际退出 2；重复 doc ID 和其余产物的元数据命令因磁盘耗尽未能保存完整证据。重复 task ID 的一次尝试并不满足规格的重复 index ID 检查，故不计为通过。提权网络测试调用已发起，但 run_check 在创建证据目录前再次遇到 `ENOSPC`，没有产生有效测试记录；这属于资源阻塞，不称为权限拒绝，也不称产品测试失败。

## 更新后的判断

补查没有改变首轮四轴结论：三份均仍是完整性 FAIL、功能/回归 FAIL、架构 FAIL、正文复现 UNVERIFIED。补查新增了 Slate/Quartz 的练习和入口正面证据、Larch 正确入口失败证据，以及三份真实链接检查证据；未验证项和磁盘限制均明确保留。
