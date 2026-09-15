# 有界评估工具补正

你按现有 custom coder 角色执行。你不是唯一工作者，保留他人修改；另一名 coder 正在 work/production，禁止触碰。只修改 tools/rein_evaluate.py、tools/tests/test_rein_evaluate.py、tools/tests/test_rein_dataset.py、tools/validate_repository.py、chapter-16 的 specs/fixtures；可以向 evidence/evaluator-v4 保存证据。不要修改任何 skill 源码/模板，不提交、推送或创建子代理。旧 v3 作者已终结，写入所有权现归你。

主线程已读实际 v3，不再做泛化重构，只解决以下明确反例：

1. parameter-change-01 的 ArgumentParser() 默认允许缩写，因此旧 --timeout 5 仍成功。设 allow_abbrev=False；测试必须执行真实 parser.parse_args(['--timeout','5']) 断言失败、parse_args(['--timeout-seconds','5']) 断言成功，不能仅搜索源码名称。同理核对 parameter-change-02 参数真实有效。expired-command-01 已修 package.scripts.check，请保留。
2. broken-relative-link-01 的 expected.contains_any 仍锁定两种链接标签，`See [Guide](docs/guide.md).` 被误拒。用结构化 visible_link_target 断言代替完整 Markdown 子串；normalize ./ 和 URL 解码，对任意非空标签均接受同一存在的路径；全部实际可见相对链接仍需存在。用该实际 case（非自行构造 expected）证明 `See [Guide](docs/guide.md).` 与 `See [the guide](./docs/guide.md).` 都通过；原坏链接+HTML注释正确链接、仅HTML注释则失败。所有3个链接 case 更新为一致的结构化断言。
3. 对每个有修改案例，assertions_hold 要核对非目标文件未改变：与原始 case workspace 的完整文件清单/哈希比较，只豁免 index.input_fault.file。目标正文不可被删为仅命令/flag/注释；沿用案例的保留意图断言并对实际12例加上上述回归。对合法自然语言改写，机械意图检查有限，明确允许人工复核裁决；不要把少量词组规则称成完整语义理解。no_change 的全树相等仍需保留。
4. test_stats.executed 与 tests_run 应表示真正执行过的测试，忽略项在 skipped 单列：Cargo passed+failed，unittest Ran-skipped，passed 排除 failures/errors。Vitest 只能解析以 Tests 开始的汇总行，不能把 Test Files 也相加；真实例 `Test Files 2 passed (2)\nTests 8 passed | 1 skipped (9)` 应为 executed8/passed8/skipped1。pytest只解析最终汇总行，各顺序均可，例如 `1 failed, 2 passed, 3 skipped in 0.1s` 应 executed3/passed2/failed1/skipped3，不应读取逐行测试名。保留Cargo多harness相加。新增精确回归并修正全skip门槛：有执行且成功不因skipped比executed大而误拒，全skip仍失败。require_review 且技术无失败应为 undetermined，而非 failed，顶层聚合一致。
5. tools/validate_repository.py 目前扫描故意坏链 fixture 与嵌套冻结副本。新增明确范围排除，仅 REIN-CH05-16 的 work、evidence/inputs、evidence/specs/chapter-16 和后续 experiments/snapshots 中的嵌套产品副本，不排除整个 records 或 maintained skill 文档。可把链接检查范围定义为本仓库维护文档，说明生成载体为何另行验证。坏链接 fixture 应由专属数据集测试验证，不得改坏链接为好链接消除反例。根验证应能通过，真正本仓库文档坏链接仍应失败。

实际运行 tools/tests 全部、snapshot工具测试、skill测试、仓库验证器，保存 argv/stdout/stderr/exit 和最终源hash 至 evidence/evaluator-v4。请对每个上述具体反例给出真实结果，未完成就写未完成，不用通过的其他测试代替。
