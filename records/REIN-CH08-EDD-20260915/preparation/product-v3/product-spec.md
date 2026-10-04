# ch08 共同产品规格 v3

本章承接第 07 章的预算与完整历史，围绕同一份六文档、四任务资料运行四种上下文方法：`on-demand`、`window`、`summary`、`retrieval`。这是面向读者的混合系统产品规格，不包含实验分组或 skill 流程。未来实现只有一个 Rust `context_methods` 模块，负责方法选择、预算和证据采纳；通过既有 `StdioExecutor` 启动真实 Node `read_file` 宿主。TypeScript 只承担领域文件工具，不复制 Harness，也不扩展 M1 协议。独立进程只是进程边界，不是安全沙箱。

允许产品改动严格限于：`rust/src/rein/context_methods.rs`、`rust/src/rein/mod.rs` 的接入行、`rust/examples/ch08_context.rs`、`rust/tests/ch08_context.rs`、`scripts/ch08-compare.mjs`、`scripts/ch08-verify.mjs`、`examples/ch08-context-methods/**`、`docs/chapters/08.md`、ch08 导航所需的 `docs/toc.md`、`docs/index.md`、`docs/.vitepress/config.mts`、README/MIGRATIONS 的 ch08 状态，以及 package.json 的必要脚本。`ts/src/hybrid-host.ts` 只有兼容性确有必要时可改；`docs/chapters/01.md`、05–07 源码/正文及作者 dirty 成果必须保留。`fixtures/ch08-context/**` 是冻结只读输入，不能由实现者修改。

## 固定输入与入口

`data/index.json` 只有 `unit`、`budget` 和 document 的 `id/path/title/keywords/order`；事实只存在六份 Markdown。`data/tasks.json` 包含四个任务，每题规则相同、budget 为 2400。任务视图交给实现时只含 question、rules、budget；expectedFacts 和 unknown 只由完成后的 evaluator 读取。任务一要求早期文档的传输方式与协议版本，任务二要求最新发布文档的检查命令，任务三跨批准与失败文档询问文件基线变化后的批准状态与处理动作，任务四询问资料未给出的生产吞吐量并标记 unknown。每条 rules 元素都必须成为独立的 system message，事实片段必须使用精确前缀 `[来源:docId]\n`。

统一入口：`npm run --silent ch08:compare -- [--data-root ABS] [--budget N] [--strategy on-demand|window|summary|retrieval]`。默认输出 16 行，即 4 任务 × 4 方法；指定 strategy 可只输出一列。输出根对象为 `{unit,serviceTokens:null,results}`。每行必须有 `taskId,strategy,question,budget,status,messages,estimatedUnits,selectedSources,operations,answer,quality,unsupportedClaims,elapsedMs,serviceTokens:null,modelCalls,callRecords`。answer 为 `{rawAnswer,claims:[{field,value,source}],insufficientEvidence}`；成功 status 必须精确为 `completed`，成功调用一次离线回答器，modelCalls 为真实 1。quality 是正确且在 messages 中存在来源依据的必需事实数除以必需事实总数，范围 0..1；没有相关 claims 时 `insufficientEvidence=true`，部分事实有据但不全时用 quality 表示。unknown 仅在明确证据不足且 claims 为空时为 1，否则为 0。没有事实的行仍成功但 evidence insufficient。

## 四种方法与共同回答器

on-demand 先以 index 的 title/keywords 选择文档，然后才通过 Node 读取选中文件；未选文件不得产生 read 操作。window 按 order 读取，保留最近完整段落 suffix，裁剪只删最早完整片段，不按 query 改变顺序，rules/question 永不裁剪。summary 从真实读取资料提取 `字段：值` 事实行，丢弃背景自然段并保留来源；这是规则式离线摘要，不能据此声称 LLM 摘要能力。retrieval 按 query 分词、关键词和正文段落相关度评分，稳定排序并记录 score 与片段；它不是 task ID 查表。

最终离线 answer 只接收最终 messages。它从 question 的通用同义词识别字段，再从带 `[来源:docId]` 的实际消息内容取值；映射可以识别字段同义词，不能把整道题或 taskId 映射到事实值。事实行修改后，只要该事实进入 messages，rawAnswer 与 claim 必须使用新值，即使旧 oracle 的 quality 因而下降。窗口裁掉事实时，证据不足是合法结果。claims 必须在所称 source message 中有对应事实；无依据 claims 进入 unsupportedClaims。

## 预算、错误和真实记录

沿用第 07 章 `estimated-bytes-v1`：普通消息估算为 `8 + UTF8(role) + UTF8(content)`，工具字段按既有 `estimated_units` 的 `J(arguments)` 规则继承。`estimatedUnits` 必须等于实际 messages 估算，不是服务 token；serviceTokens 始终 null；elapsedMs 只覆盖本地构造、离线回答和评分的单调时钟。

rules/question 放不下（含 budget 0）时，返回 `context_budget_exhausted`、answer null、messages/operations/callRecords 空、estimatedUnits 0、modelCalls 0、quality null，不做文档 I/O 或模型派发。预算须为非负安全整数。index/doc/task ID 唯一，order 唯一明确，path 必须是 data-root 内相对路径。CLI 非法参数或 metadata（重复 ID/order、非法 path 等）必须以非零退出和明确错误结束，不能折叠成普通结果行。运行时缺失文档、path escape、Node 宿主错误或无效响应返回 `error` 行、answer null、modelCalls 0，并保留真实失败 records。实现可在自己的 `records/ch08/**` 保存证据，不得引入新依赖。真实 callRecords 来自 StdioExecutor，已派发记录必须含 child_pid、dispatched、reaped、exit_code、terminal；不得根据策略名伪造。

## 读者可复现的公开检查

正文从第 07 章的历史过长问题进入，展示同一数据下四方法如何改变 messages、selectedSources、operations、estimatedUnits、quality 与 callRecords，明确离线范围与真实服务 token 的缺失。正文必须有锚点 `methods-entry`、`fixed-dataset`、`four-methods`、`compare-results`、`method-failure`、`practice-08-1`、`practice-08-2`、`practice-08-3`，且不依赖先读附录。

三项独立练习都复制临时资料而不改冻结 data：练习一修改早期文档真实传输方式并保留旧 oracle，执行 `--data-root ABS` 后核对 messages、rawAnswer 和 quality；练习二用 `--budget 0`，核对 `context_budget_exhausted`、modelCalls 0、operations 空；练习三改 retrieval query 词，核对 selectedSources、scores 和证据遗漏。每项命令必须给绝对路径、完整参数、预期字段和结论。

公开验收覆盖 TS typecheck/全部 tests、Rust fmt/check/test、05/06/07 compare、ch08 16 行、真实 Rust→Node、异常路径、独立 example、从最终 Markdown 抽取命令并执行、三练习、docs build/link/navigation。根 `ch08:verify` 必须执行独立 `examples/ch08-context-methods/README.md` 所述真实混合入口与自有演示输入；该目录必须包含 README、输入和入口。真实模型服务不运行；文档与退出码只证明离线合同和本地行为。
