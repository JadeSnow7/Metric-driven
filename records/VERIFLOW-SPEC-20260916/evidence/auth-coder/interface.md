# IT-03 授权快照接口

`skill/veriflow/scripts/authorization_snapshot.py` 提供两个纯函数：

- `capture_snapshot(state, authorization_action, target, revision) -> dict`：读取当前授权与来源，要求状态为 `authorized`，来源为 `accepted` 的 `user_requirement` 或 `user_feedback`，并验证目标落在 scope（空 scope 表示不限制）。返回 schema version `1`、真实 UTC `captured_at`、动作/目标/revision、完整 authorization/source 副本，以及 `content_sha256`。
- `audit_snapshot(snapshot, action_record) -> list[dict]`：只依据历史快照和动作记录检查类型、时间、状态、来源、scope、action/target/revision 和规范 JSON SHA-256。`snapshot is None` 返回 `AUTH_SNAPSHOT_UNKNOWN`，不会用当前 state 补历史授权。

动作记录预期至少有 `authorization_action`、`target`、`revision`；集成字段名为 `authorization_snapshot`。CLI 只从 `--state` 读取 JSON 并把快照输出 stdout，不执行动作。摘要是完整性校验，不是用户签名；来源真实性仍由主线程核实。
