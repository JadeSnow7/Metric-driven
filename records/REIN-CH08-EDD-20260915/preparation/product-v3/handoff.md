# product-v3 交接

本次返工只物化共同产品规格、冻结资料和预算校准，未写 evaluator、CLI、Harness、正文或原书籍。v1/v2 与中断记录保留，不能作为本批基线。此前错误 calibration 已封存为 `rejected-calibration-v3.json`，不在共同 data 目录中。

## 交付路径

- 规格：`product-spec.md`
- 共同资料临时副本：`/private/tmp/rein-ch08-preparation-product-v3/data/`
- 归档资料：`product-v3/data/`
- 输入哈希：`data.sha256`、`manifest.sha256`、`evidence/artifact-sha256.txt`
- 实际校准命令：`evidence/commands.jsonl`

## 已核对数字

- 六份资料、四个任务、四策略默认 16 行
- 按 index 的真实 order、每条 rules 独立 system message 重新计算：task-01 3729、task-02 3714、task-03 3771、task-04 3693，均大于 2400
- task-03 的 doc-03 + doc-05、独立 rules system messages 与 question：1399（小于 2400）
- 任务 4 unknown=true 且 expectedFacts=[]

## 证据与边界

`evidence/commands.jsonl` 保存实际 argv、cwd、UTC 起止时间、退出码、stdout/stderr；原始 usage 不适用于本次静态资料准备，保持缺失。预算校准采用第 07 章普通消息公式 `sum(8+UTF8(role)+UTF8(content))`，不代表服务 token。fixture 是合成教材资料，不承诺当前软件已经具备这些能力。数字与主线程此前估计的 3735/3720/3777/3699、1405 存在差异，已保留本次独立计算结果，需主线程复核消息构造口径后再冻结。

主线程需审查并冻结后，交给另一新上下文实现 evaluator；本交付不启动正式 A/B/C。
