# 生产修复副本覆盖事件

状态：正在恢复。此事件发生在首轮两组封存和裁决之后，属于生产返工，不覆盖首轮成绩。原 Rein 尚未回写。

主线程从实际工具记录核查，ch05_code_repair_v2 在 2026-09-14T11:53:28Z 将旧 `records/REIN-CH05-16/work/production` 误当作当前生产来源，归档并删除/替换 `/private/tmp/rein-production-20260914`。11:53 的归档不是当前 ch05 生产 v1；SHA256SUMS 只包含42个产品文件，关键章节和运行时目录为空。此前交接已明确旧目录仅为前置备份，不得作为 ch05 完成状态。

该代理在 12:06:29Z 又用这一不完整归档删除/替换生产根，12:07:29Z 改为从首轮 diff-b/new 再次替换，丢失刚完成的 v2 内容。主线程观察目录空缺后暂停两名代理写入并中断它们，要求只读回报。正文代理只执行过 npm ci（DNS失败并清理依赖）及05.md写入，没有执行根目录删除/替换。

相关实际工具 call_id：call_cJREAqRGvIchlADcbCCcUKev、call_YNJzFZ2oWs7IPUeZ8MIYPslc、call_dxZLzzp1Y6teZPHdCii4UESQ。来源为当前任务子代理19:52:10的实际工具日志，不以事后自述替代这些记录。

主线程随后逐字节重新核验 `/private/tmp/rein-ch05-seal-safe-20260914/snapshots/arm-a` 的122文件和 arm-b 的123文件，全部SHA256匹配原manifest，证据 `/private/tmp/rein-first-incident-recheck.json`。原 Agent-Learning git status 仍为既有手工稿/站点改动，没有本任务ch05源码回写。

恢复使用新代理和全新目录 `/private/tmp/rein-ch05-trace-recovery-20260914`，从完整first-b与v1/v2实际源码写入记录重建。禁止盲跑含删除和错误复制的历史shell。重建副本明确标识为事后恢复；v2已记录的7文件hash作为精确核验，缺失项如实保留。旧不完整归档和错误证据保持原样，不能用新内容补成“原封存”。

旧写入代理不再负责生产源码。后续每次章节基线必须由主线程验证完整清单，新的作者只在明确的新副本增量修改，禁止替换整个已有生产根。此事件不归因于skill的确定效果，不与成对首轮产品分混计。

## 追加：前置归档内容缺口

2026-09-14 12:58 UTC 附近复查时，snapshots/pre-ch05/files只有空目录，114项manifest仍在；evidence/inputs/rein/tree/files亦为空且其manifest缺失。当前原因undetermined，不能将其直接归因于之前生产根覆盖。原始pre-ch05.patch嵌入初始106文件source_manifest；按历史hash的恢复由 ch05_trace_recovery 执行。刚生成的snapshots/pre-ch05-portable和snapshots/ch05以空baseline包装，均未获验收，不得成为下一章起点。受测skill399项主线程重新核验全部匹配，15项资源存在；原Rein未回写。
