# ch08 共同产品输入草案（待主线程冻结）

本草案只描述书籍实验产品，不包含 EDD 流程、skill 内容或历史缺陷答案。四种策略必须对同一份输入运行：`on-demand`（按需读取）、`window`（窗口裁剪）、`summary`（规则式摘要）、`retrieval`（按关键词检索）。摘要为离线规则式处理，结论仅证明给定本地资料上的确定性行为；上下文估算使用 `estimated-bytes-v1`，服务 token 保持空值。

## 数据 schema 建议

```json
{
  "unit": "estimated-bytes-v1",
  "budget": 2400,
  "documents": [{"id": "doc-01", "path": "docs/01-runtime.md", "title": "...", "keywords": ["..."], "order": 1}],
  "tasks": [{
    "id": "task-01",
    "question": "...",
    "rules": ["只根据已读取材料回答", "标出事实来源"],
    "expectedFacts": [{"field": "...", "value": "...", "source": "doc-01"}],
    "unknown": false,
    "budget": 2400
  }]
}
```

建议将索引与任务拆为 `index.json={unit,budget,documents}` 和 `tasks.json={tasks:[...]}`。索引的 document 只允许 id/path/title/keywords/order；资料正文单独位于 `data-root` 下，source 统一使用 docId，片段位置可由实现另报。固定 6 份文档、4 个任务；任务与策略笛卡尔积为 16 次。评估器最后才读取 `expectedFacts`/`unknown`，实现和正文不能按任务 ID 查预置答案。文档事实改动后，答案必须来自实际读取内容；保留旧 oracle 时质量下降是合法结果，不能自动改 oracle 掩盖读取失败。

## CLI envelope 建议

```text
npm run --silent ch08:compare -- [--data-root ABS] [--budget N] [--strategy on-demand|window|summary|retrieval]
```

输出根对象建议为：

```json
{
  "unit": "estimated-bytes-v1",
  "serviceTokens": null,
  "results": [{
    "taskId": "task-01",
    "strategy": "on-demand",
    "question": "...",
    "budget": 2400,
    "status": "completed",
    "messages": [],
    "estimatedUnits": 0,
    "selectedSources": [],
    "operations": [],
    "answer": {"rawAnswer": "...", "claims": [], "insufficientEvidence": false},
    "quality": null,
    "unsupportedClaims": [],
    "elapsedMs": null,
    "serviceTokens": null,
    "modelCalls": 1,
    "callRecords": []
  }]
}
```

预算无法容纳规则和问题时，结果必须是 `context_budget_exhausted`、`modelCalls: 0`、`answer: null` 且不读取文档；I/O 或宿主错误为 `error` 且 `answer: null`。非法 CLI 或 metadata 使用非零退出并给出明确错误。`callRecords` 由真实 `StdioExecutor.records` 产生，不能由策略名或任务 ID 填充。
