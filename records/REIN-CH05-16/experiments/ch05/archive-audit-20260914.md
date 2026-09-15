# ch05 当前档案完整性复查

独立只读审计 ch05_archive_audit 核对了以下当前内容，主线程保留本结果及早前亲自核对的hash证据：

- safe snapshots arm-a 122/122、arm-b 123/123 内容与mode符合各自manifest，无缺失/额外文件。
- records/experiments/ch05/first 两组同样符合manifest，manifest与safe逐字节一致。
- 每组execution的7份原始文件与/private/tmp/rein-benchmark-executions/ch05对应目录逐字节相等；events各101行有效JSON、1次turn.completed，final匹配最后完成的agent_message，exit0。它们证明首次执行档案完整，不证明产品合格。
- evidence/full-input-archive/experiments/ch05/reviews：reviewer-1 150、reviewer-2 145、main-review13，共308份内容/mode与对应/private/tmp原始证据相符。

相邻patch及历史恢复日志确实存在，但本次审计没有实际重新apply。主线程另发现旧pre快照files缺失，原first patch呈全文件新增形式，不能因此声称它从原114文件前置恢复正确；须保留旧件并补充基于精确恢复前置的新相邻补丁与实际恢复记录。

初始106与pre114恢复候选，主线程已分别以原patch内嵌09:46:02Z source_manifest和10:33:57Z pre manifest逐文件SHA及Git执行位核对，均0差异。当前proof：/private/tmp/rein-input-recovery-main-verification.json。候选中provenance元数据将与产品files分开放入新的归档；这是事后精确恢复，不倒称原目录一直完整。
