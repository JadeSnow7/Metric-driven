# 工作日志

- EVENT-001 2026-09-14T09:44:50Z：用户批准完整实施方案。核查两仓库HEAD与dirty状态；启动bootstrap和evaluation_tools，限定互斥写入路径。原始目录尚未修改。

- EVENT-002 2026-09-14T09:55:21.845192+00:00：主线程核查Rein106/skill15个冻结文件均与源文件一致；复跑工具测试。评估器首版空命令与伪计数假通过已保存复现并退回，修正版7项自检已复跑。前置工具协议与fixture事实源仍待补齐，不启动对照。

- EVENT-003 2026-09-14：独立评审与主线程确认准备版本仍存在语义 oracle 假通过、数据事实不符、Cargo 多 harness 计数问题；前置版本缺 Rust 具体 HTTP 实现与足够共享样例验证。原始评审保存在 evidence/preparation-review，前两版运行日志保留。两个互斥范围的 coder 正执行 v3 补正，尚未验收。

- EVENT-004 2026-09-14：内置代理新建/恢复反复触发数量限制，无法保证正式对照所需的全新上下文。读取本机 coder.toml 并核对官方非交互执行文档，准备 v3 改用相同角色配置的临时 Codex CLI。正式协议在任何章节试验开始前同步改为同一 CLI 入口；此变更只影响调度方式。所有实现仍委派，主线程未写产品源码。ch05–16 尚未开始，原 Rein 未回写。

- EVENT-005 2026-09-14：前置 v4 的完整输出为 TS 72 tests、Rust 9 unit+5 prerequisites 通过；主线程亲自复跑 TS 类型检查、7个前置测试、Rust格式和5个前置测试，全部通过，原始输出与前后源码hash保存在 evidence/main-review/prerequisites-v4。评估器最终23项测试已复跑；非零ignored的Cargo探针结果 executed8/passed8/failed0/skipped3。此处仅为前置及工具验收。

- EVENT-006 2026-09-14：打包时发现 Documents 下部分 Git 文件标记 SF_DATALESS。主线程以只读方式核查并恢复读取；原始 Agent-Learning/.git 518文件无占位且HEAD仍匹配，后续打包改用该本地历史来源。停止受阻的首个打包CLI，结果保存为准备中断（evidence/ch05-packaging），不计章节成绩。新的有界打包交给可再次调用的原生coder，另一个coder补齐整个skill仓库文件树。正式成对执行仍按既定相同CLI入口，不混用启动方式。

## EVENT-007 2026-09-14T10:58:49.479591+00:00

主线程复核ch05共同输入发现误放准备指令，保存错误版本并统一更正，重新确认117文件完全一致后启动正式a/b CLI coder。前置与评估器主线程检查通过；完整skill仓库归档仍不完整。实现进程/日志见 /private/tmp/rein-benchmark-executions/ch05，待两臂结束封存及去标签审查。

## EVENT-008 2026-09-14T11:08:37.525469+00:00

ch05两臂turn.completed/exit0。a墙钟571.294秒，b546.989秒；usage原字段完整保留，不用总输入token掩盖cached字段。首轮封存交bootstrap，未评分未修复。全仓库冻结缺口交归档coder独立继续，作用域不重叠。

## EVENT-009 2026-09-14T11:33:08.941062+00:00

两名独立评审完成。主线程核对实际diff、原始探针/错误、亲自复跑TS并裁决分歧，ch05两组核心行为passed，完整章节交付failed；详细裁决已封存 experiments/ch05/adjudication.md。批准另建skill生产修复副本；未进入ch06。原始测试环境故障单列，不计产品。

## EVENT-010 2026-09-14T11:37:47.102276+00:00

全仓库归档399路径由coder完成；主线程全文SHA256回读无差异，并用远程精确基线tar重建390文件Git tree ac803ca5e39d6e0c59e7f708c92ddd26028d93c7完全匹配。README/ROUND5晚采集限制不抹去。ch05首轮裁决已保存，生产修复正在新的/tmp目录执行；后章未开工。

## EVENT-011 2026-09-14

生产 v1 独立复核与主线程源码审查完成，完整章节仍 failed。真实入口本地 HTTP 行为通过，但测试、正文、共享 wire、模块拆分仍有明确遗漏。代码修复 v2 交 ch05_code_repair_v2；先封存 v1。基准包装工具首版也经主线程审查退回：role 多行解析/指令层级、Git 复制、执行日志、恢复验证和双包评审均需修复，禁止用于 ch08。

## EVENT-012 2026-09-14T12:10Z

生产副本被代码代理错误根目录替换，v1归档实际来自旧前置且不完整，v2无完整副本。主线程停止写入、核查实际工具记录，首轮122/123文件hash全匹配，原Rein未回写。独立coder从first-b与实际工具源码记录在新目录事后重建，7个v2已记录hash作为核验。详细原因、call_id及恢复边界见 experiments/ch05/production-incident.md。包装工具run模块另交原工具作者分项修复，禁止正式使用未通过版本。

## EVENT-013 — ch05代码离线通过，真实冒烟失败

主线程已核查真实10个关键离线场景与两项完整跨语言规范化比较；TS79和Rust9+4+5原始输出已核对，当前源码停止修改。真实冒烟按语言各一次且没有重试：TS HTTP 400，Rust request failed，均首轮失败且0工具调用，usage null。正文最终整段校对委派新代理 ch05_final_text；尚未形成通过的章节快照，ch06未开始。

## EVENT-014 — 正文通过，前置快照目录缺失

最终两正文已全文审查、原始multi/single和6mode结果核对，共有5锚点一致；最终docs build实际exit0，原始记录 /private/tmp/rein-main-ch05-candidate03-checks/docs-build-final.json。归档代理发现原pre-ch05/files为空，但manifest仍声明114项；主线程复查初始Rein/tree/files亦空、manifest缺失，尚未确定消失原因。新生成pre-ch05-portable和ch05误用了空baseline，明确无效且保留。主线程按114既有hash找到110项在safe first-a、2项在原Rein，剩contracts/README与rust/src/rein/mod.rs交coder从原始补丁/日志精确恢复。原pre-ch05.patch嵌入完整初始106 source_manifest，可用于初始输入恢复。skill全仓库399项当前重验0问题，首轮安全副本/评审归档另交只读审计。原Rein未回写，ch06未开始。

## EVENT-015 — ch05冻结版本验收通过，启动ch06

主线程再次核验恢复106/114历史hash，实际恢复pre/ch05 tar和114→127 Git binary patch，所有文件与当前冻结产品一致。ch05-accepted manifest SHA b0b8fd29880fa92f74af8a65b8db04c1fc5ac52bf5401872ddcfa32e8b624f50。源码/两正文/离线门槛通过，live失败单列；最终全书演进树回归未运行。ch06_implementation负责同一candidate03的06源码、共享样例、测试、两正文；ch05_trace_recovery独立修复首轮相邻补丁包装说明与恢复README，不碰运行时代码。原Rein未回写。

## EVENT-016 — ch06控制代码通过，正文待审查

ch06 v1/v2未满足正常三轮、多工具顺序、取消和比较器门槛；v2封存18文件，主线程核对与当前源hash相等。v1源快照未保存，不以当前文件冒充；旧null时间保留。v3改为TS与Rust两名coder分文件写入，主线程探针发现同步abort后throw导致未处理Promise拒绝；新回归与v4修复后同一探针exit0。原始失败与修复证据均保留。

当前主线程审阅14项源码diff/hash，亲自运行十场景共享fixture/双语言比较、0/1/3/数字文件名动态输入、missing workspace、ch05回归全部通过，TS88与Rust21测试原始输出已核对。code-gate.json绑定源码hash与证据。ch06_body_author现负责两完整中文正文，ch06_archive归档返工/reading02原始材料；全文与章节快照仍未验收，ch07未开始。此章为生产工作，返工不混入四对正式首轮成绩。reading02已补全快照恢复说明并通过hash失败反例，随后续快照携带。
