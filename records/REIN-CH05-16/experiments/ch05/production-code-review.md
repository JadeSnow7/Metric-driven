# ch05 candidate-03 代码离线审查

代码离线门槛：passed。完整章节仍待正文跟做修订、真实冒烟状态记录与章节快照；不能据此宣告全任务完成。

唯一当前候选：`/private/tmp/rein-production-candidate-03`。来源是经过主线程126文件清单核验和7个历史源码hash核验的事后重建v2，再加明确有界补正。旧 `/private/tmp/rein-production-20260914` 不再使用。

主线程直接核查了 TS/Rust loop、typed ModelAdapter/OpenAI wrapper、演示mode、两语言测试、共享fixture、比较入口及规范化字段。实际 Rust SearchReplay 从收到的搜索结果选择读取，再从第三次收到的两个真实文件内容形成答案；停止原因的wire值为snake_case。

作者完整原始检查证据位于 `/private/tmp/rein-candidate03-evidence`。主线程已读实际stdout和状态文件：TS79项通过，Rust9个lib+4个loop+5个prerequisite通过，fmt/typecheck/check通过。初次localhost监听EPERM失败保留，之后受限升级复跑通过，未将失败日志抹除。

主线程亲自复跑10个关键场景：TS/Rust各自multi、recovery、empty、exhausted、limit，输入为新建ORCHID/CEDAR专用目录。断言多文件真实内容进入第三次模型请求、缺失文件错误后恢复读取、空回答/回放错误/两轮上限的原因和请求次数，全部通过。原始命令、时间、退出码和完整输出为 `/private/tmp/rein-main-ch05-candidate03-checks/offline-key-scenarios.json`。

主线程亲自复跑 `npm run ch05:compare-all`：同一fixture的正常两文件与缺失后恢复两case，实际分别启动TS/Rust入口，完整规范化messages、每轮请求schema、调用参数/id、工具结果状态/错误码及停止事件相等，并符合共享expected。错误人类文本按失败call ID规范化，正常工具文本保持精确。

比较入口曾硬编码本机Cargo target，现已删除该硬编码，尊重调用环境；生产修复的误覆盖和不完整v1归档另见 production-incident.md，不混入首轮成绩。

真实冒烟已执行：两语言均一次模型派发、零工具调用，failed/model_error；TS报告OpenAI HTTP 400，Rust仅报告OpenAI HTTP request failed，Rust具体底层原因undetermined。usage=null；未重试。主线程读取了 smoke-report.json 与实际 stdout，证据位于 /private/tmp/rein-ch05-live-evidence。CLI exit 0不等于冒烟通过。正文由新的 ch05_final_text 做最终完整跟做校对；ch06尚未开始。
