# Rein ch05–16 当前状态

整体仍在进行。唯一生产树为 `/private/tmp/rein-production-candidate-03`；原 `/Users/huaodong/workspace/Agent-Learning` 尚未回写。没有提交、标签、推送或发布。主线程负责方案与审查，代码、正文、工具、归档与最终回写由 custom coder 执行。

- ch05、ch06 已通过各自离线整章门槛，共4篇完整正文。ch05 snapshot127文件，ch06 snapshot132文件；主线程均实际解包、从相邻基线应用Git binary patch并核对全部hash/执行位。有效路径为 `snapshots/ch05-accepted`、`snapshots/ch06-accepted`，pre基线为 `snapshots/pre-ch05-restored`；旧无效包保留但不使用。
- ch06代码14项hash与完整TS88、Rust21原始测试已核对，十控制场景、动态0/1/3/数字文件名、missing工作区、05回归和同步abort+throw反例通过。两正文v3、8共享锚点与build通过。393份最终raw源/归档hash已逐项复核，另有277份历史返工证据和reading02三份证据已核对。`production/ch06/*-gate.json` 是实际门槛。原snapshot helper退出raw缺失，主线程独立恢复验证作为验收依据；随后只读进程审计未见命令行helper活进程。原06源码的一条observer注释不准确，06正文已解释无沙箱保证，07演进代码正修正文注释，旧hash不篡改。
- ch07 代码门槛已通过并记录13项源码/配置hash（production/ch07/code-gate.json）。最终TS96/96与typecheck通过；Rust完整27/27后又以真正 --test loop 跑13/13；root fmt、05/06比较、固定七案例、独立10行计量和额外动态/非法输入通过。此前NaN/畸形结果/空toolCallId/重复ID/空工具名/unsafe-budget差异与过滤错测试已保留证据并修复。两篇完整正文终稿已审查通过：TS d000737...、Rust7921f54...，root最终build与8共有锚点通过。CLI空文本fallback不一致已修正并验证empty_final，最终代码hash更新。单一coder正在封存07快照/patch和归档全部raw；root恢复验证尚待完成。
- 阶段汇总1 docs/milestones/02.md 与A.2 docs/appendices/a2.md 已写入产品并通过正文验收。v2八项06快照运行与v5从最终Markdown提取的正/负编译输出已被root读取；最终A2 hash88e9715...，阶段1e40f81...。232份归档源/目标hash及mode已逐项复核无差异（production/support-stage1-a2）。历史v4书稿仍留错枚举名尽管作者声称通过，已明确纠正后再验收。reading02已随06交付。后续A1/A3–5、阶段2/3仍待对应章节。
- ch08尚未物化或执行。共同产品/数据准备/执行三份handoff已制定：07验收快照后，冻结6文档、4问和2400估算预算，逐策略真实构造并同回答器评估，禁止按策略/任务ID查预置答案。随后两组全新无历史custom coder CLI，一组额外加载冻结skill。准备时间单列，首轮同时封存后再去标签两人评审。
- ch05正式首轮两组都已封存并完成两名独立去标签评审及root裁决：核心观察行为passed，完整章节交付均failed，属于正常结束的遗漏。`experiments/ch05/adjudication.md/json` 保留依据；05 live每语言一次均在首次模型调用失败，TS HTTP400，Rust具体传输原因undetermined，工具0、usage null，未重试。08/12/14配对、12/16 live及07正文、08–16后续整章工作仍待完成。
- 后续实验工具的13项测试已由root实际重跑，12份工具归档hash全部核对。后续双方统一新增skip-git-repo-check与显式workspace-write，05当时两组有.git；差异与未验证真实无.git运行的限制已记录。原评估器known-good/预植缺陷检查及23项主线程准备验证保留在早期记录。

输入历史限制必须保留：初始106份Rein及114份pre基线原files目录后来为空，原因未知；已依据原hash从安全首轮、原Rein和原补丁精确事后恢复，root106/106和114/114核对无差异。399份skill全仓库归档及15份受测资源已核验；README/ROUND5是明确标注的晚采集，不宣称同初始时点。受测skill本轮不修改。

05生产副本曾被前任coder覆盖，旧v1档案不完整、v2元数据曾手写；已从真实工具写入记录事后重建两份126文件版本，并核对7个历史源码hash。原Rein与正式两组未被该事件改动。仅使用candidate03，详见 `experiments/ch05/production-incident.md`，不得恢复使用旧 `/private/tmp/rein-production-20260914`。

首轮review实际归档位置是 `evidence/full-input-archive/experiments/ch05/reviews`；05安全副本为 `/private/tmp/rein-ch05-seal-safe-20260914`。control误写共同父目录的3文件单列，不计正式交付；隔离偏离和单次配对限制不作因果推广。最终仍须逐章正文复现、统一验证全部独立例子、站点导航/语言切换/锚点、原库三方回写及受影响集成复验。
