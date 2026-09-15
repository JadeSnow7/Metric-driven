已完成并验证：

- 新增 Rust `context_methods` 与 `ch08_context` 示例入口
- 新增 `ch08:compare`、`ch08:verify`
- 新增独立示例 `examples/ch08-context-methods`
- 完成第08章中文正文、练习与锚点
- 更新目录与 VitePress 导航
- 保存 `records/ch08` 原始输出与退出码
- `ch08:verify` 通过：16 行结果、零预算、真实 Rust→Node、独立示例
- TS typecheck、Rust fmt、文档构建通过

失败/限制：

- TS 全量测试与 Rust 全量测试因环境禁止监听 `127.0.0.1`，出现 `EPERM`
- 尚未运行 05/06/07 比较验收
- `window` 当前仍是简化实现，未完成严格的完整片段裁剪
- 缺失文件等运行时错误路径仍需进一步完善为严格 `error` 行
- README/MIGRATIONS 状态同步未完成

未提交、未打标签、未推送、未部署。