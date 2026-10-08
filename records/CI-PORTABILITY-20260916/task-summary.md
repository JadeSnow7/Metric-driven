# CI 链接可移植性修复

当前基线 `fd7f0a6`，PR #3 分支 `feat/skill-entry-round-2`。两次 workflow（35058210153、35058474421）的六个 job 均在链接校验失败：每个 job 18 个坏链，涉及 7 个 final.md；Python 编译步骤被跳过。本机校验通过说明本机路径存在掩盖了不可移植链接。

执行合同见 [实现交接](handoffs/implementation.md)。修复先保留原文与哈希；已封存 C 组报告保持逐字节不变，精确按历史归档分类，并提供相对链接索引。其余六个报告仅规范化展示链接，不能修改历史结果。

验收：存在于本机的绝对链接必须失败，仓库内相对链接通过，越界/坏链失败；保持原有代码示例和外部链接语义；本地完整 workflow、干净快照、主线程区分性检查通过后，核验新提交对应的远程矩阵。

当前：实现与主线程审查已完成；干净目录完整 workflow 通过（60 场景测试、12 仓库测试），区分性检查与原件保留检查通过。修复已提交推送为 `a4e841f`；push 与 pull_request 两次 workflow 的 Python 3.11/3.12/3.13 共六个 job 全部通过。修复提交推送到现有 PR；不合并、不删除大型证据目录。现有未跟踪产物保持不动。终端阶段可以开始。

[状态](task-state.json) · [日志](work-log.md) · [skill 问题记录](skill-observations.md)

交付工作区：`/private/tmp/veriflow-ci-delivery-20260916`。原目录云盘 Git 对象出现 dataless/mmap 错误；八文件按已审查 SHA 迁移，内容指纹一致。原工作区与 foreign 产物保持不动。

远程回执：[最终 CI 检查](evidence/remote-ci-final.json)。本机当前交付回执写回在任务记录中；原工作区 Git HEAD 尚未因云盘故障而重置，不将其称为干净工作区。
