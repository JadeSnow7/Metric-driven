# 包装工具 v2 主线程反例与修复边界

v2 不接受，禁止正式实验使用。主线程亲跑4项作者测试通过，但独立反例输出 `/private/tmp/rein-benchmark-tool-v2-main-review.json` 明确显示以下问题。

## 先修 run

- `--skill` 只进入 metadata，不进入真实 stdin；fake CLI 收到的仍为 COMMON。两组因此没有实际差异。共同 prompt 与实际各组 prompt 分别保存/hash；skill 组按已冻结 ch05 协议追加读取冻结 SKILL.md 的指令，控制组不追加。真实 stdin 必须等于实际 prompt 文件。
- `-o final.md` 写入产品树；改成 run 输出目录下绝对 final 路径，完全避免污染 product manifest。fake CLI 要解析 -o 参数，不应硬编码 final.md 掩盖问题。
- Popen 失败、读取失败、取消/中断都必须留下 ended/exit/classification/error，不能只留下开始记录或引用未初始化 proc。terminal 只从成功解析的 JSON 事件中取，坏行原样保存，不能解析崩溃。
- 当前 selectors 后调用阻塞 readline，stderr 无换行时可卡住；使用逐块非阻塞读取或独立泵送线程，输出实时落盘并在异常时关闭/终止进程。
- 使用真实多行 coder.toml 与假 CLI 精确断言 developer 指令单独经 -c、stdin内容、CARGO_TARGET_DIR、外部final、usage、退出/失败分类与增量输出。不要启动真实模型。

## 再修 seal/树复制

- run.json 实际在外部，seal 却只检查 tree/run.json，未提供任何运行证明也能成功。增加显式 execution 参数，校验 workspace、起始 hash、正常终结/明确阻塞状态，保留原始日志并拒绝尚未结束/不匹配的来源。普通生产 snapshot 与正式 first seal 分开入口，不用绕过运行检查。
- 保存的 baseline.patch 使用已经删除的临时绝对路径；恢复测试却使用另改过路径的文本。交付的必须就是实际验证过的稳定相对路径 patch。明确读者恢复命令，并在全新目录应用交付文件，验证精确清单含新增/删除/模式/二进制内容；可用 Git binary patch，避免 diff -ruN 的能力缺口。
- symlink 虽在 manifest 有记录，tree_hashes 仍无条件索引 sha256 导致 KeyError。目录 symlink 被 is_dir 分支变成空目录。先判断链接，明确安全策略并保存其目标/模式，精确恢复；测试文件链接、目录链接和越界链接拒绝/记录策略。
- 遍历在进入依赖和缓存前剪枝，避免 rglob 先遍历数万 build 文件。排除环境配置包括根及子目录，不将基线秘密写入任何patch。保持 fixtures/manifest.json 等产品输入。

作者测试可按函数拆小，但要实际区分上述反例。当前两个执行槽位先用于 ch05；主线程之后另发 bounded followup，不要抢占或自行运行后章。
