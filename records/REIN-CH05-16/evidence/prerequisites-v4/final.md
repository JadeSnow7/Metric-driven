已完成前置合同与共享样例补正。

主要改动：

- TS/Rust 均使用 fixture 中真实 Anthropic/OpenAI 响应。
- loopback 第二轮断言完整 `tool_calls`、ID 与真实文件输出。
- 补齐并共享畸形响应列表，严格校验类型、空值和数组结构。
- replay 保存深拷贝，补充两次请求历史测试。
- Rust `Option::None` 序列化省略，新增 canonical JSON 样例。
- 更新合同 README，明确错误码、TS `Error`/Rust `Result`、wire JSON 回放及 Rust HTTP 入口。

测试结果：

- TS typecheck：通过
- TS 全量测试：72/72 通过
- Rust fmt/check：通过
- Rust 全量测试：9 单元测试、5 prerequisites 测试、doc-tests 全部通过
- 未修改依赖或 Rust lock 内容

证据已保存：

本报告仅规范化链接以便可移植展示，不改变前置条件结论或原始证据。

- [ts-full-output.log](ts-full-output.log)
- [rust-full-output.log](rust-full-output.log)
- [verification-meta.txt](verification-meta.txt)

未提交、未推送，未触碰根目录 tools 或评估数据集。
