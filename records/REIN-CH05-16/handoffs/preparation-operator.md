# 准备工具收尾与输入归档

你是 custom coder。你不是唯一工作者，保留其他作者修改。production 正由另一个 coder 补正，禁止读取或改动 production。你独占 tools/rein_evaluate.py、tools/tests/test_rein_evaluate.py、tools/validate_repository.py 及必要的对应测试；可在 records/REIN-CH05-16/evidence/preparation-operator 和 evidence/inputs/skill-repository 新建材料。不改受测 skill、不改其他既有记录、不提交/推送，不开额外代理。evaluator-v4 作者已终结。

请仅完成三个明确任务，不泛化重构：

1. v4 的 Cargo 统计仍是 `executed=passed + failed + skipped`。实际 `3 passed;0 failed;2 ignored` 加 `5 passed;0 failed;1 ignored` 应 executed=8、passed=8、failed=0、skipped=3。修正该分支并用此非零 ignored 回归；已有其他 runner 统计和21项测试保留。
2. is_maintained_document 当前 `if "experiments" in parts or "snapshots" in parts` 排除全仓库任意同名路径，超过指定范围。限制为当前任务 `records/REIN-CH05-16/experiments` 和 `records/REIN-CH05-16/snapshots`。维护文档中的代码示例不应当作实际链接，可以去除 fenced code 和 inline code 后再扫描链接；保留真实维护文档坏链检查，不通过整个 records 排除来规避。必要时保留明确生成证据路径排除，但记录理由。至少测试 skill/references/experiments/example.md 仍在维护范围，而本任务 snapshots/x.md 不在。
3. 原来的输入冻结保存了整个 Rein，但 skill 只保存 skill/evidence-driven-development 目录15文件，仓库层级则仅有 HEAD、初始 current.patch 与 status.txt。补齐整个 skill 仓库输入载体，同时不把本任务后续新增工具和records混入初始工作区。方法：以 evidence/inputs/skill/source-head.txt 指向的本地 Git 对象建立临时副本，应用同目录初始 current.patch，纳入初始 status.txt 所列的未跟踪原有 records/ROUND-5-WRITING（现在仍在原目录，不能改它）。保存完整文件清单/hash及可恢复文件树到 evidence/inputs/skill-repository/tree。可以调用现有 tools/rein_experiment.py，Git历史只复制到临时工作目录且移除remotes，不做提交/标签。禁止读取或归档 .env/认证配置等秘密。核对重建后的15个skill文件与原冻结skill manifest完全相同。归档说明必须区分初始HEAD/patch恢复与未跟踪目录本次较晚采集，若无法证明后者与最初时刻一致就明确写不能证明，不伪造初始hash或时间。原始15文件与初始patch/status一律不覆盖。

跑 tools/tests、snapshot测试和仓库校验，保存真实命令、stdout/stderr/exit、源码hash、归档还原核对结果和任何限制到 preparation-operator。最后回复精确实际状态。
