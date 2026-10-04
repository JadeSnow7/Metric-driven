# 全仓库冻结缺口恢复：已核实的下一步

2026-09-14 11:18 UTC 主线程用 require_escalated 只读 curl -I --max-time15 确认 https://codeload.github.com/JadeSnow7/Metric-driven/tar.gz/1a10fca5d408004a354da5f61e6f449c09801f23 返回HTTP/2 200。先前DNS失败发生在受限网络，不能写成远程基线不存在。无需新凭据。空闲coder应使用同样安全升级下载此精确基线到/tmp，禁止clone/fetch/改.git，然后恢复390个原跟踪路径。基线commit/tree链及旧工具blob均已校验。

用最初已记录dirty路径区分原未修改与原手工稿：原未修改路径可由该精确基线恢复；原dirty8项中的skill文件使用冻结15文件，README需当前晚采集并注明时间；ROUND5的9份原未跟踪文件从当前或原备份读取。不得用HEAD覆盖dirty内容或把无法取得的原稿说成已冻结。保持初始status/current.patch及后续恢复/晚采集的来源区别，输出完整manifest并保留/tmp副本。

受测skill额外复核：完整15文件重新读取与/private/tmp/rein-benchmark-resources-20260914/skill现已逐个hash相等，见 experiments/ch05/main-preflight/skill-resource-recheck.json。此前一次false比较保留为异常历史，不能据此断言内容已变。full-input-archive/loose-object-diagnosis.json包含对象链，/tmp/validate.blob.gz是原工具可读压缩blob。
