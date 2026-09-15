# 主线程验收：混合架构 M1

## 当前结论

M1 已通过主线程代码审查、隔离集成树离线复跑及原项目回写后检查。`/Users/huaodong/workspace/Agent-Learning` 已接收 81 个任务路径，零冲突。主线程独立 readback 结果见 `postwrite-integrity.json`，回写命令和原项目构建/完整集成输出见 `../transfer/postwrite/`。

Rust 保留既有 loop、消息历史和预算控制，以 `ToolExecutor` 边界调用真实 Node 子进程。TS 宿主复用早期只读工具，不加载历史 TS loop。模型由离线 FixtureModel 提供；正常结果经过真实文件读取和证据采纳后进入第二次模型调用，最终回答含实际 marker 内容。

主线程直接检查了身份关联、持久帧缓冲、取消确认、严格终态、EOF/退出条件、实际 wait/reap、路径规范化、版本重读和无自动重放路径。原先按返回枚举推断进程事实、取消时丢弃半帧、弱取消分支及不完整故障注入均经历了修复；原始失败记录保留，不作为通过证据。

## 已复跑的检查

- `npm run typecheck`：通过。
- `npm test`：100 项通过。初次受沙箱回环监听限制的 5 项测试随后在允许本机监听的环境完整复跑通过；没有线上模型调用。
- `node --import tsx --test docs/.vitepress/theme/sourceVersionState.test.ts`：5 项通过。
- `cargo test --locked --manifest-path rust/Cargo.toml`：39 项通过，含 12 项跨进程测试。完整命令、时间、退出码、源码哈希与原始 stdout/stderr 在本目录 `rust-full.*`。
- 五个 CLI 的独立复跑在 `scenarios-v2/`：normal 为 exit 0 / final_answer / 两次模型调用；invalid、crash、disconnect-after-effect 为 exit 1 / outcome_unknown / 一次模型调用；cancel 为 exit 1 / cancelled / 一次模型调用。每种场景均观察到单条实际派发并回收的调用记录。
- `scenarios-v2/ledger.txt` 保留故障宿主写入的单行副作用。它证明该次运行未自动重放，不证明持久化 exactly-once。

本目录第一版 `scenarios.json` 保留主线程复现的 crash 故障注入缺失；后续修复了测试宿主缺失的退出分支，再完成 v2 全部场景，未修改运行时以迎合错误测试。

回写后 `npm run hybrid:verify` 在原项目再次通过 TypeScript 类型检查、100 项 TS 测试、Rust 格式/编译/39 项测试和正常 CLI。主线程另外运行了原项目的真实导航测试命令，5 项通过，完整结果为 `nav-original.json`。`transfer/postwrite/commands.json` 中名为 nav5 的历史记录实际 argv 是 TS 全量测试；按 argv 解释该记录，不将其冒充导航测试。

## 文档与保留边界

作者第 01 章在本次任务中的受保护哈希为 `e07a2850ab31ca132fed9214256ccd746776bddfca2e48458fb25515ff8ea32d`。原库 124 个冻结文件在回写准备时均无漂移，既有 dirty 状态属于作者基线。D9 追加新决定并保留 D1–D8。第 04 章只增加边界区分与主线衔接，05–07 的历史 TS 材料、原有 fixtures、练习与快照保留。

主线程实际导航验证见上级目录 `navigation-review-02.md`：第 01 章与阅读 0 的真实双版本切换保留共有锚点；05–07 不伪造语言对；主线经过 06 Rust core、06 Plugin 再到 07 Rust core。

最终状态与前后页衔接已在浏览器再次核对，见 `navigation-review-03.md`；回写后构建与链接检查通过。临时验收浏览器页面及 4175 端口开发服务已关闭。

## 未实现与未验证

SDK 提炼、通用领域验证器、修改批准、持久 journal、恢复、委派、MCP/Hooks 和 08–16 的后续正文仍属于迁移计划。当前首方 Node 进程是受信任进程，不是操作系统沙箱。内存调用记录不是恢复日志。

真实模型服务、线上 CI、GitHub Pages 发布未在本次 M1 中运行。没有提交、标签、推送或部署。本次迁移及返工不是原双语言 skill 配对实验；旧实验保留，新路线后续实验需要重新冻结输入，不能据此声称 skill 的因果提升或节省比例。token 数据未取得，保留为空。
