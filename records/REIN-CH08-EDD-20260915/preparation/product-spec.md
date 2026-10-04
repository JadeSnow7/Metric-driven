# ch08 共同产品规格（实验输入）

本章在第 07 章的上下文预算基础上，实现四种上下文方法：按需读取、窗口裁剪、摘要和检索。四种策略必须接收相同的文档索引、任务问题、规则和 2400 单位预算；策略差异只能发生在候选材料的选择与构造。Rust `context_methods` 是唯一的策略与预算权威，复用 M1 `StdioExecutor` 启动真实 Node `read_file` 宿主。TypeScript 只提供领域工具和宿主，不复制 Harness。独立进程不是安全沙箱。

## 输入

输入拆为 `index.json` 与 `tasks.json`。索引只描述文档元数据，不包含事实答案；正文文件位于 `data-root` 下，路径由索引相对该根目录解析。

```json
// index.json
{"unit":"estimated-bytes-v1","budget":2400,"documents":[
  {"id":"doc-01","path":"docs/runtime.md","title":"运行时","keywords":["状态","生命周期"],"order":1}
]}
// tasks.json
{"tasks":[{"id":"task-01","question":"传输方式和恢复动作是什么？","rules":["只根据已读取材料回答","每个事实必须带来源"],"expectedFacts":[{"field":"传输方式","value":"JSON Lines","source":"doc-01"}],"unknown":false,"budget":2400}]}
```

本批固定 6 份文档、4 个任务，四策略各运行同一任务集。`expectedFacts` 只供最后评估器使用，实现不可读取它，也不可按 task ID 返回答案。`unknown` 是问题无证据时的 oracle 标记；实现只有在 answer 没有 claims 且明确证据不足时才可报告 unknown。

## 四种策略

按需读取先使用 `index.json` 的 title/keywords 与问题匹配，再通过真实 Node `read_file` 读取选中的文档；未选中的文件不得读取。窗口裁剪按 `order` 读取完整文档，构造按顺序排列的完整片段 suffix，预算不足时从最早完整片段开始裁剪，不能拆开片段、规则或问题。摘要读取候选文档后，只提取包含明确字段和值的事实行，丢弃背景段落，并在消息中标明来源；摘要是确定性的离线规则式处理，不证明模型摘要质量。检索读取候选文档并按问题词与 keywords 的匹配数排序，输出匹配片段及 docId；同分按 order 稳定排序。

四种策略最后都把构造好的 messages 交给同一个离线回答器。回答器只能依据 messages 中实际存在的字段和值生成 `rawAnswer` 与 claims，不得读取 oracle、任务 ID、原始文档或 expectedFacts。答案来自 facts 的内容变化；修改文档事实后，输出必须变化。

## 统一 CLI 与输出

```text
npm run --silent ch08:compare -- [--data-root ABS] [--budget N] [--strategy on-demand|window|summary|retrieval]
```

输出必须是：

```json
{"unit":"estimated-bytes-v1","serviceTokens":null,"results":[
 {"taskId":"task-01","strategy":"on-demand","question":"...","budget":2400,
  "status":"completed","messages":[],"estimatedUnits":0,"selectedSources":[],"operations":[],
  "answer":{"rawAnswer":"...","claims":[{"field":"...","value":"...","source":"doc-01"}],"insufficientEvidence":false},
  "quality":null,"unsupportedClaims":[],"elapsedMs":null,"serviceTokens":null,"modelCalls":1,"callRecords":[]}
]}
```

`estimatedUnits` 使用第 07 章 `estimated-bytes-v1`：每条消息为 `8 + utf8(role) + utf8(content) + toolCallId + Σ(8 + utf8(id) + utf8(name) + J(arguments))`，数组和对象的 `J` 规则沿用第 07 章；不是服务 token。`serviceTokens` 缺失时保持 null，不能估算。`callRecords` 必须来自真实 `StdioExecutor.records`。

预算无法放下 rules/question 时，`status=context_budget_exhausted`、`modelCalls=0`、`answer=null`，且 operations 为空，不读取文档、不启动宿主、不调用回答器。预算为 0 同样不做 I/O。缺失文档、越界路径、非法 metadata、宿主异常或读取失败为 `status=error`、`answer=null`，不伪造成功。非法 CLI 参数以非零退出和明确错误结束。正常完成不等于证据充分；证据不足可以合法完成，但必须有空 claims 和 `insufficientEvidence=true`。

## 验收与正文跟做

公开检查运行 TS 全测、Rust fmt/check/test、05–07 compare、ch08 compare、真实 Node 读取、Rust→Node 异常、独立 example 和文档构建/链接。ch08 正文必须解释相同输入下四种选择的可观察 messages、selectedSources、estimatedUnits、modelCalls 和 callRecords；必须区分估算单位与服务 token，并说明离线回答器范围。

正文提供三个独立练习：修改一个事实并观察答案与 claim 变化；把 budget 减到规则/问题放不下并观察零 I/O；修改 query 词并观察 retrieval selectedSources 改变。每个练习使用临时副本和绝对 `data-root`，不覆盖冻结输入；命令、参数、预期字段和失败原因必须完整可复制。

异常覆盖：越界路径不能读出 data-root；缺失/重复文档 ID 和非法 order 不能静默接受；缺 rules/question 不能派发；预算 0 不能产生 model call；宿主错误、断连、错误身份和无效响应必须保留实际 callRecords 与错误状态。独立评审仍需实际跟做正文并核对真实进程反应；自动评估器不能替代这一点。
