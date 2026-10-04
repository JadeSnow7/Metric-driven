# ch05 首轮封存与去标签评审包装

你是独占本打包工作的 custom coder。主线程已确认两组正式进程终结后才会分派此任务。你不是唯一工作者，不回退其他人的文件。只负责本节指定封存、审查副本和证据，不改实现、不评分、不修复产品、不提交或推送。不要读取原个人.env。

输入源码分别为 /private/tmp/rein-ch05-pair-ready-20260914/a 与 b，原始进程记录 /private/tmp/rein-benchmark-executions/ch05/a 与 b。必须先检查各自 exit.json 与 events.jsonl 的终结状态，报告是首次final交付、明确阻塞还是进程中断。不能把作者缺文件叫资源中断。保存原始日志、final、prompt、启动/退出metadata、实际usage字段和适用工具/skill读取审计。只观察可验证的记录，不声称能证明未观察到的读取。

使用本仓库现有 tools/rein_experiment.py（先核对其真实参数）封存全部任务源码/正文/作者记录及共同输入，排除.git、node_modules、target/build/dist及.env秘密。保留文件模式。首轮载体和manifest放 records/REIN-CH05-16/experiments/ch05/first/arm-a、arm-b；也保留同样的临时安全副本，避免共享云目录读取故障损坏唯一载体。任何已有first路径先核查不得覆盖。对比共同起点：从 pre-ch05快照加三个实际task-inputs得到首轮输入，记录真实新增/修改/删除。用 git diff --no-index 做相邻补丁并验证在临时副本恢复到封存hash相等，不创建Git提交。

检查两臂的 task-inputs 与主线程 experiments/ch05/main-preflight/files-product-input-final.json 哈希是否保持一致；任何变化记录，不自动纠正首轮。记录两篇正文是否存在及实际修改文件清单。

去标签包只包含产品代码、测试、fixtures、正文、共同task-inputs及原写作参考。首次作者新增的records、工作总结、skill报告等不进评审包；这些仍完整保存在first载体。不要改源码/正文内的内容以美化结果；若源码本身暴露流程线索，记录限制。组别映射仅写在外部 experiments/ch05/review-mapping.json，不放评审目录，不给评审作者final或原始prompt。使用无语义代号 package-17 与 package-42。

为两名评审各建立独立工作副本，根目录 /private/tmp/rein-ch05-review-20260914/reviewer-1 和 reviewer-2，每个都含 package-17 与 package-42。同一个评审两包共用其私有Rust构建目录（包改动会重编），两个评审目标目录不同且位于副本外。依赖可以从原准备目录独立复制，不使用指向原Rein或正式首轮源码的可写链接。后续可以删除已停用的纯临时依赖/编译缓存节省空间，但先列出精确路径和无活动进程依据；不删除任何源码、首轮结果或证据。

提交包清单、hash/恢复校验、源码与正文范围、原始usage/时长提取、读取审计和两位评审的准确入口。不要提前修复缺陷，不改生产副本。遇到云目录I/O保留/tmp完整载体并明确records同步状态，不谎称已存全。

注意实际运行的环境偏离审计：部分执行者自行设置了源目录内的 `.cargo-target`。封存与评审包装排除这些实际编译产物，并记录路径及其与原指定环境的偏离；不要让默认工具遗漏排除后把编译缓存当源码。核查原始命令中是否查询或读取兄弟工作目录，区分只列路径、实际读取内容和修改；保留具体命令，不把目录隔离声明代替记录核查。不要向任何正式执行者补充建议。
