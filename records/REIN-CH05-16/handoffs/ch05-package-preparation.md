# 为第05章准备共同冻结输入

你是有界 custom coder/执行者，你不是唯一工作者。另一人正在 tools/rein_evaluate.py、tools/validate_repository.py 和 skill 仓库输入归档工作，禁止触碰。production 前置作者已完成，主线程亲自复跑类型检查、TS 7 项前置测试、Rust fmt 和 5 项前置测试通过。现在你独占本任务的 production（仅以下很小文档更正）、snapshots/pre-ch05、experiments/ch05/input-audit 和下述新临时目录。不要实现 Loop 或05正文，不修改手工稿或受测skill，不提交、标签、推送或额外创建代理。

1. contracts/README.md 两处很小的事实更正：删去“正式书版发布时固定 tag”承诺，改成按本任务可恢复快照及合同变化记录定位；回放耗尽说明 TS 抛 Error('replay exhausted')、Rust 返回 code='replay_exhausted'，不要把二者都说成返回同样错误码。其他源码及fixture不改，因此无需重新跑全部功能测试。
2. 用现有 tools/rein_experiment.py 从 production 生成完整快照至 records/REIN-CH05-16/snapshots/pre-ch05（先确认不存在，存在就核查而非覆盖）。保存其与原始 Rein 输入的相邻补丁：可临时放 old/new 文件树，通过 git diff --no-index -- old new 输出，记录 git apply -p2 的复跑方法。不能用已有原HEAD的git diff漏掉新增文件。保持文件模式，禁止记录.env与依赖/编译产物。
3. 从同一 pre-ch05 快照克隆两份到 `/private/tmp/rein-ch05-pair-20260914/a` 与 `/private/tmp/rein-ch05-pair-20260914/b`。复制 production 的 .git 历史（不要新提交），确认remotes为空；不能保留会写回原仓库的路径。依赖 node_modules 各自独立复制（可用支持的 COW copy），不要硬链接或指向原仓库的可写symlink；`.bin`内部相对symlink可保留。Rust共用只读cargo缓存，但为两臂记录不同的 CARGO_TARGET_DIR，均放自身目录外的私有临时路径，避免构建互相锁住。
4. 两个目录新增完全相同只读逻辑输入 `task-inputs/product-spec.md`、chapter-05.json（源为 evidence/specs），以及 ch05-product-clarifications.md（源为 handoffs）。不要复制评估器、oracle、主线程记录或skill到两份产品工作目录。删除 clone 工具生成的 `.rein-snapshot.json` 元数据（它不是原产品文件，来源映射留在外部审计）；保留本来产品的源码和写作参考。
5. 把原已冻结的15文件skill复制到独立资源目录 `/private/tmp/rein-benchmark-resources-20260914/skill`，逐个与 evidence/inputs/skill/tree/manifest.json 验证hash相同。不要安装到全局，不在a/b中建立skill自动发现路径。主线程稍后只向一个执行者明确提供该路径。
6. 在 experiments/ch05/input-audit 保存共同源码/输入完整路径hash清单、两目录除.git/node_modules外对应相等的验证、依赖版本/独立目录检查、Git HEAD/无remotes检查、适用AGENTS发现位置（全局 ~/.codex/AGENTS.md 及父路径，不读取认证配置）、受测skillhash核对、可恢复补丁测试。通过读取/执行原有公开命令确认两份目录准备成功即可，不启动任一正式执行代理。

完成后返回实际目录、hash核对及恢复验证结果；任何缺口写明。所有操作记录实际执行，不伪造完成。
