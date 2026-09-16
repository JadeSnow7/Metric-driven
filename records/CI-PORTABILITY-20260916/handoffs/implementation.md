# CI 修复实现合同

所有者 coder。你不是唯一执行者，不要撤销他人修改。共享 task-state、task-summary、work-log 和 skill-observations 仅主线程写入。读取 skill/veriflow/SKILL.md；不修改 skill/**。

可写：task-state 中 IT-001 的八个路径，以及本任务 evidence/coder/（原始报告备份 .txt、SHA、链接映射、测试原始输出和回报）。不提交推送。

先核对全部七报告/十八链接，再实现。六个可编辑报告在修改前保存原始 bytes 和 sha256，声明是仅规范化链接的可移植展示报告；能映射到已跟踪同源证据的改为相对链接，不能映射的保留原始路径代码文本并明确 local-only / not committed。不能用其他实验同名文件替代。

封存路径 records/REIN-CH08-EDD-20260915/formal/seals/C/run/final.md 不修改、不重算封存哈希。校验器仅对这一精确文件增加历史归档分类（与现有封存 work 排除一致），不可扩大到整个 evidence 或 run 目录；在 evidence/coder/portable-evidence-index.md 维护它到原文、现有同源 work/records/ch08/evidence 的相对链接，测试相邻未归档 run 文档仍受校验。

校验本地链接时拒绝 POSIX 绝对路径及 Windows 盘符/UNC 本机路径；拒绝解析后逃逸仓库（含符号链接）；保留已有 HTTP/HTTPS/mailto/sandbox、片段和代码示例行为。在同一纯函数中实现可测试判断，仓库入口调用该函数。

区分性测试必须包含实际存在的绝对文件（普通及尖括号）、相对有效/缺失、../ 越界、符号链接越界、外部 URL、片段、代码文本。禁止改变断言使错误变成通过。保持现有 workflow 矩阵与规则。

先跑 tools/tests/test_validate_repository.py，检查维护文档整体；用 record_execution.py --repo --state 保存本任务 evidence/coder/ 下的记录。必要的编译缓存设到仓库外。最终立即回报结果、文件清单、验证与原始证据、文档同步、下一依赖及 skill 候选问题。主线程另跑完整 workflow 和干净快照。
