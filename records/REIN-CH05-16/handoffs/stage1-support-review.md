# 阶段1与A.2草稿返修

草稿 /private/tmp/rein-stage1-support-draft；source evidence /private/tmp/rein-stage1-support-evidence。尚未回写产品。root已全文读完两页。

1. 两页使用 marker: README alpha / marker: NOTES beta，却声称 ch06 normal成功；真实ch06只搜索 marker: ch06，当前命令必失败。阶段1准备README.md+guide.md内容 marker: ch06 alpha/beta，同一内容兼容ch05 marker:搜索，并同步所有预期摘要。A.2也使用 marker: ch06 alpha。不能复用其他输入的raw当本页复现证据。
2. 阶段1给章节快照恢复链接和npm依赖安装前提，删除“限时免费”状态条。正文不需要内部完成声明。
3. A.2 TS LoopEvent代码删了字段和model_received，要明确是节选；JSON tool_result给完整实际call/result.toolCallId等必需字段，不伪造简化合同。
4. A.2加一个小TS switch与Rust match对LoopState完整分支范例，解释穷尽检查并给可执行练习。
5. 指定作者下一轮修订只写原草稿和evidence，不在06已冻结或07源码写入期间运行其未定源码。可从已验收06 portable解包独立副本，复用安装依赖以外的无污染临时配置，所有cargo设外部target。新运行准确记录argv/cwd/start/end/exit/stdout/stderr。root复核后由coder串行拷入当前树，不能改已冻结06包。


v2全文复核：marker输入已改正确，A2完整JSON/类型节选/状态函数改好。仍有一个预期文本错误：阶段1“多文件任务”调用ch05，答案前缀必须是“多文件摘要：marker: ch06 alpha | marker: ch06 beta”；当前误改成ch06的“完成：”。其余新raw待根阅读8命令actual业务结果后判断，不仅看exit0。恢复说明还应给[阅读材料2](/readings/02.html)链接，并写明在恢复书根npm ci（当前只写“准备npm依赖”）。A2演练可补具体文件/编译命令，已给函数不要声称实际编译过若没有raw。等待空槽再修正文并由指定coder拷入当前树，不改旧06快照。
