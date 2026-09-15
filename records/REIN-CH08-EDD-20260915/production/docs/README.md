# CH08 production docs handoff

- 目标：交付第 08 章完整中文教程、三项独立可复制练习及 08 导航状态。
- 来源/base：生产副本 `/private/tmp/rein-ch08-production-20260915/book`，基线 `1dfa82b9d90196c2294f61914d2017449e5548e3`。
- 文档 owner：production docs coder；源码 owner：`/root/skill_update`。双方不得并行写同一文件。
- 允许出口：`docs/chapters/08.md`、`docs/toc.md`、`docs/index.md`、`docs/.vitepress/config.mts`、`README.md`、`MIGRATIONS.md`，以及本目录和 `/private/tmp/rein-ch08-production-20260915/evidence-docs/**`。
- 当前产物：`docs/chapters/08.md` 已扩展为完整教程，含锚点 `methods-entry`、`fixed-dataset`、`four-methods`、`compare-results`、`method-failure`、`practice-08-1`、`practice-08-2`、`practice-08-3`；已同步 v2 的普通 user 来源消息、paragraph window、retrieval operation 字段；练习各自创建绝对临时目录并完整复制 fixture。
- 文档事实来源：`/private/tmp/rein-ch08-common-20260915/product-spec.md`、生产 fixture `fixtures/ch08-context/**`；风格只参考原书 `03.md` 前 47 行和 `04.md` 前 18 行。
- 已验证：VitePress build、book links（2198 项无失败）和文档 diff check 通过；导航已拆为 05–07 对照、08 混合正文、09–16 规划。
- 未完成：仍未运行 cargo、ch08 compare、三练习、正文命令提取器；不能把当前文稿报告为验收完成。
- 下一依赖：测试 coder 释放 cargo 执行权后，读取实际 16 行输出，修正文档中与输出不一致的预期，并用统一 `CARGO_TARGET_DIR` 从最终 Markdown 提取后以 `bash -euo pipefail` 执行全部命令。
